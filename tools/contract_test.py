#!/usr/bin/env python3
"""Run the same requests against a running Android and iOS phyphox and diff them.

    python3 tools/contract_test.py --android http://192.168.0.10:8080 \
                                   --ios     http://192.168.0.11

Both phones must have remote access enabled and be running **the same
experiment**, which the script checks via the crc32 in /config before it starts.

What it checks
--------------

1. Every response validates against the schema in docs/remote-interface/openapi.yaml.
   OpenAPI 3.1 schemas are JSON Schema, so the spec is used directly - this is the
   point of writing the spec first.

2. The two phones agree in *shape*: same keys, same types, same enum choices. It
   deliberately does not compare values. Two phones cannot produce the same
   measurements, device names or timestamps, and a test that expected them to
   would be useless. What must match is the contract.

3. Divergences already recorded in inconsistencies.yml are reported but do not
   fail the run. A divergence that is *not* recorded fails it. That is the whole
   point: the implementations are known to disagree in many places, and this
   script exists to catch the next one, not to re-report the backlog.

By default only read-only endpoints are used. Pass --allow-control to include
start/stop/set/trigger, which change the state of the experiment, and
--allow-clear to include clearing, which destroys measured data.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENAPI = os.path.join(ROOT, "docs", "remote-interface", "openapi.yaml")
INCONSISTENCIES = os.path.join(ROOT, "inconsistencies.yml")

TIMEOUT = 10


# --------------------------------------------------------------------- probes

class Probe:
    """One request, run identically against both phones."""

    def __init__(self, name, path, params=None, schema=None, expect_json=True,
                 relates_to=(), destructive=False, clears=False):
        self.name = name
        self.path = path
        self.params = params or {}
        self.schema = schema          # $ref name under components/schemas
        self.expect_json = expect_json
        self.relates_to = tuple(relates_to)   # inconsistency ids
        self.destructive = destructive
        self.clears = clears

    def url(self, base):
        q = urllib.parse.urlencode(self.params)
        return f"{base.rstrip('/')}{self.path}" + (f"?{q}" if q else "")


def build_probes(buffer_name):
    """The probe set. `buffer_name` comes from the running experiment's /config."""
    b = buffer_name
    probes = [
        Probe("config", "/config", schema="Config"),
        Probe("meta", "/meta", schema="Meta", relates_to=["meta-sensors"]),
        Probe("time", "/time"),

        Probe("get.single", "/get", {b: ""}, schema="GetResponse"),
        Probe("get.full", "/get", {b: "full"}, schema="GetResponse"),
        Probe("get.threshold", "/get", {b: "0"}, schema="GetResponse"),
        Probe("get.threshold.ref", "/get", {b: f"0|{b}"}, schema="GetResponse"),
        Probe("get.unknown.buffer", "/get", {"nosuchbuffer___": ""},
              schema="GetResponse"),

        # Edge cases that the two are known to handle differently. They are here
        # so the recorded entries stay honest, and so a *change* in behaviour -
        # someone fixing one side - shows up immediately.
        Probe("get.no.parameters", "/get",
              relates_to=["get-no-parameters"]),
        Probe("get.unknown.reference", "/get", {b: "0|nosuchbuffer___"},
              relates_to=["get-unknown-reference-buffer"]),
        Probe("export.bad.format", "/export", {"format": "99"},
              expect_json=False, relates_to=["export-invalid-format"]),
        Probe("export.missing.format", "/export",
              expect_json=False, relates_to=["export-invalid-format"]),
        Probe("res.missing.src", "/res",
              relates_to=["res-fallback"]),
        Probe("res.unknown.src", "/res", {"src": "nosuchfile___.png"},
              relates_to=["res-fallback"]),
        # hue.png is bundled with the app rather than with the experiment, so
        # this is the request that shows the fallback divergence.
        Probe("res.bundled.fallback", "/res", {"src": "hue.png"},
              expect_json=False, relates_to=["res-fallback"]),

        Probe("control.bad.command", "/control", {"cmd": "nosuchcommand___"},
              schema="ControlResult"),
        Probe("control.no.command", "/control", schema="ControlResult"),
    ]

    control = [
        Probe("control.set", "/control", {"cmd": "set", "buffer": b, "value": "1"},
              schema="ControlResult", destructive=True),
        Probe("control.set.unknown.buffer", "/control",
              {"cmd": "set", "buffer": "nosuchbuffer___", "value": "1"},
              schema="ControlResult", destructive=True,
              relates_to=["control-set-unknown-buffer"]),
        Probe("control.set.infinity", "/control",
              {"cmd": "set", "buffer": b, "value": "Infinity"},
              schema="ControlResult", destructive=True,
              relates_to=["control-set-infinity"]),
        Probe("control.set.nan", "/control",
              {"cmd": "set", "buffer": b, "value": "NaN"},
              schema="ControlResult", destructive=True),
        Probe("control.trigger.out.of.range", "/control",
              {"cmd": "trigger", "element": "99999"},
              schema="ControlResult", destructive=True,
              relates_to=["control-trigger-out-of-range"]),
    ]

    clearing = [
        Probe("control.clear.groups", "/control",
              {"cmd": "clear", "clearGroup1": "nosuchgroup___"},
              schema="ControlResult", destructive=True, clears=True,
              relates_to=["control-clear-groups"]),
    ]
    return probes, control, clearing


# ----------------------------------------------------------------- requesting

def fetch(url):
    """Return a dict describing the response, never raising for HTTP errors."""
    req = urllib.request.Request(url, headers={"Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            body = r.read()
            return {
                "status": r.status,
                "content_type": (r.headers.get("Content-Type") or "").split(";")[0].strip(),
                "cors": r.headers.get("Access-Control-Allow-Origin"),
                "body": body,
            }
    except urllib.error.HTTPError as e:
        body = e.read()
        return {
            "status": e.code,
            "content_type": (e.headers.get("Content-Type") or "").split(";")[0].strip(),
            "cors": e.headers.get("Access-Control-Allow-Origin"),
            "body": body,
        }
    except Exception as e:                      # timeout, refused, reset
        return {"status": None, "content_type": None, "cors": None,
                "body": b"", "transport_error": f"{type(e).__name__}: {e}"}


# -------------------------------------------------------------------- shaping

# Enum-like strings whose choice is part of the contract, so they are compared
# as values rather than collapsed to "<string>".
ENUMS = {"full", "partial", "single", "none", "START", "PAUSE", "CLEAR"}

# Paths whose value legitimately differs between two phones. Everything else is
# compared as far as its type allows - in particular booleans are compared by
# value, because "result": true vs false is the whole answer of /control and
# collapsing it to "<bool>" would hide the divergence this script looks for.
VOLATILE = {
    "status.session",
    "status.measuring",
    "status.timedRun",
    "status.countDown",
}


def shape(value, path=""):
    """A structural signature: keys, types, enum choices and booleans."""
    if path in VOLATILE:
        return f"<volatile {type(value).__name__}>"
    if isinstance(value, dict):
        return {k: shape(v, f"{path}.{k}" if path else k)
                for k, v in sorted(value.items())}
    if isinstance(value, list):
        # Collapse to the set of distinct element shapes, so a different number
        # of samples is not reported as a difference.
        seen = []
        for item in value:
            s = shape(item, path)
            if s not in seen:
                seen.append(s)
        return {"<array of>": sorted(seen, key=repr)}
    if isinstance(value, bool):
        return f"<bool {str(value).lower()}>"
    if isinstance(value, (int, float)):
        return "<number>"
    if value is None:
        return "<null>"
    if isinstance(value, str):
        return value if value in ENUMS else "<string>"
    return f"<{type(value).__name__}>"


def flatten(node, prefix=""):
    """Shape -> sorted list of "path: type" lines, for a readable diff."""
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            out.extend(flatten(v, f"{prefix}.{k}" if prefix else k))
    else:
        out.append(f"{prefix or '.'}: {node}")
    return sorted(out)


# ------------------------------------------------------------------ the run

def load_spec():
    with open(OPENAPI) as f:
        return yaml.safe_load(f)


def load_known_ids():
    with open(INCONSISTENCIES) as f:
        return {e["id"] for e in (yaml.safe_load(f) or [])}


def validator_for(spec, schema_name):
    from jsonschema import Draft202012Validator
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012

    # The spec is registered under its own URI so that "$ref" resolves into it
    # rather than into the one-line wrapper schema below.
    base = "urn:phyphox-remote-api"
    resource = Resource(contents=spec, specification=DRAFT202012)
    registry = Registry().with_resource(base, resource)
    return Draft202012Validator(
        {"$ref": f"{base}#/components/schemas/{schema_name}"},
        registry=registry)


def pick_buffer(base):
    """A buffer name from the running experiment, preferring an exported one."""
    r = fetch(f"{base.rstrip('/')}/config")
    if r["status"] != 200:
        return None, None
    cfg = json.loads(r["body"])
    for s in cfg.get("export") or []:
        for src in s.get("sources") or []:
            if src.get("buffer"):
                return src["buffer"], cfg.get("crc32")
    buffers = cfg.get("buffers") or []
    return (buffers[0]["name"] if buffers else None), cfg.get("crc32")


def run(args):
    spec = load_spec()
    known = load_known_ids()
    targets = {"android": args.android, "ios": args.ios}
    targets = {k: v for k, v in targets.items() if v}
    if len(targets) < 2:
        print("Need both --android and --ios to diff. With one, only schema "
              "validation runs.\n")

    # Same experiment on both, or the comparison is meaningless.
    buffer_name, crc = None, {}
    for name, base in targets.items():
        b, c = pick_buffer(base)
        if b is None:
            sys.exit(f"{name}: could not read /config from {base}. Is remote "
                     f"access enabled and an experiment loaded?")
        crc[name] = c
        buffer_name = buffer_name or b
    if len(set(crc.values())) > 1:
        sys.exit("The phones are running different experiments (crc32 "
                 + ", ".join(f"{k}={v}" for k, v in crc.items())
                 + "). Load the same experiment on both.")
    print(f"experiment crc32 {next(iter(crc.values()))}, probing buffer "
          f"{buffer_name!r}\n")

    probes, control, clearing = build_probes(buffer_name)
    if args.allow_control:
        probes += control
    if args.allow_clear:
        probes += clearing

    failures, expected_diffs = [], []
    cors_seen = {name: set() for name in targets}

    for probe in probes:
        results = {}
        for name, base in targets.items():
            r = fetch(probe.url(base))
            if r.get("transport_error"):
                # Not automatically a failure: an app that traps on a bad request
                # answers nothing at all, and that is exactly what
                # export-invalid-format describes. Let it take part in the diff.
                results[name] = {"status": None, "content_type": None,
                                 "shape": f"<no response: {r['transport_error']}>"}
                continue

            cors_seen[name].add(bool(r["cors"]))
            parsed = None
            if r["content_type"] == "application/json" or probe.expect_json:
                try:
                    parsed = json.loads(r["body"])
                except Exception:
                    parsed = None

            # Schema check, where the spec says what to expect.
            if probe.schema and parsed is not None and r["status"] == 200:
                v = validator_for(spec, probe.schema)
                for err in sorted(v.iter_errors(parsed), key=lambda e: e.path):
                    failures.append(
                        f"{probe.name} [{name}]: schema {probe.schema}: "
                        f"{'/'.join(str(p) for p in err.path) or '<root>'}: "
                        f"{err.message}")

            results[name] = {
                "status": r["status"],
                "content_type": r["content_type"],
                "shape": shape(parsed) if parsed is not None else "<non-json>",
            }

        if len(targets) < 2:
            continue

        a, i = results["android"], results["ios"]
        diffs = []
        if a["status"] != i["status"]:
            diffs.append(f"status: android={a['status']} ios={i['status']}")
        if a["content_type"] != i["content_type"]:
            diffs.append(f"content-type: android={a['content_type']} "
                         f"ios={i['content_type']}")
        if a["shape"] != i["shape"]:
            only_a = set(flatten(a["shape"])) - set(flatten(i["shape"]))
            only_i = set(flatten(i["shape"])) - set(flatten(a["shape"]))
            for line in sorted(only_a):
                diffs.append(f"android only: {line}")
            for line in sorted(only_i):
                diffs.append(f"ios only:     {line}")

        if not diffs:
            continue
        unknown_refs = [r for r in probe.relates_to if r not in known]
        if unknown_refs:
            failures.append(f"{probe.name}: relates_to names ids missing from "
                            f"inconsistencies.yml: {', '.join(unknown_refs)}")
        if probe.relates_to:
            expected_diffs.append((probe, diffs))
        else:
            failures.append(f"{probe.name}: UNRECORDED divergence\n    "
                            + "\n    ".join(diffs))

    # CORS is a property of the whole server, not of one endpoint, so it is
    # checked once here instead of being repeated on every probe. A platform
    # that is inconsistent with *itself* is a separate, unrecorded problem.
    for name, values in cors_seen.items():
        if len(values) > 1:
            failures.append(f"{name}: sends the CORS header on some endpoints "
                            f"and not others - that is not a platform "
                            f"difference, it is a bug in {name}.")
    if len(targets) == 2 and all(len(v) == 1 for v in cors_seen.values()):
        a_cors = next(iter(cors_seen["android"]))
        i_cors = next(iter(cors_seen["ios"]))
        if a_cors != i_cors:
            expected_diffs.append((
                Probe("server.cors", "/", relates_to=["cors-header"]),
                [f"Access-Control-Allow-Origin: android={a_cors} ios={i_cors}"]))

    # --------------------------------------------------------------- report
    if expected_diffs:
        print("Known divergences, already recorded in inconsistencies.yml:\n")
        for probe, diffs in expected_diffs:
            print(f"  {probe.name}  ({', '.join(probe.relates_to)})")
            for d in diffs:
                print(f"      {d}")
        print()

    if failures:
        print("FAILURES:\n")
        for f in failures:
            print(f"  {f}")
        print(f"\n{len(failures)} problem(s). An unrecorded divergence is either "
              f"a new bug or a divergence nobody has written down yet - add an "
              f"entry to inconsistencies.yml and reference it from the probe.")
        return 1

    print(f"OK - {len(probes)} probes, no unrecorded divergences.")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--android", help="base URL, e.g. http://192.168.0.10:8080")
    p.add_argument("--ios", help="base URL, e.g. http://192.168.0.11")
    p.add_argument("--allow-control", action="store_true",
                   help="also probe start/stop/set/trigger (changes experiment state)")
    p.add_argument("--allow-clear", action="store_true",
                   help="also probe cmd=clear (DESTROYS measured data)")
    args = p.parse_args()
    if not args.android and not args.ios:
        p.error("give at least one of --android / --ios")
    sys.exit(run(args))


if __name__ == "__main__":
    main()
