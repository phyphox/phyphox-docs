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

Two things learned from the first run against real phones:

* **Start and stop a measurement on both devices first.** Buffer contents and the
  /time event list are state, not contract; an empty buffer next to a full one is
  tolerated, but a device that has never measured makes several probes
  uninformative.
* **Run --allow-control last, and clear afterwards.** control.set.infinity leaves
  a non-finite value in a buffer on Android, which then shows up as a null in
  every later /get and looks like a fresh divergence.
"""

import argparse
import json
import re
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
                 relates_to=(), destructive=False, clears=False, keep_values=()):
        self.name = name
        self.path = path
        self.params = params or {}
        self.schema = schema          # $ref name under components/schemas
        self.expect_json = expect_json
        self.relates_to = tuple(relates_to)   # inconsistency ids
        self.destructive = destructive
        self.clears = clears
        # Paths whose literal string value is part of what this probe compares.
        # Normally strings collapse to "<string>", because device names and
        # titles differ legitimately - but where an entry is *about* the wording
        # (res-fallback is), the wording has to be visible.
        self.keep_values = frozenset(keep_values)

    def url(self, base):
        q = urllib.parse.urlencode(self.params)
        return f"{base.rstrip('/')}{self.path}" + (f"?{q}" if q else "")


def build_probes(buffer_name, resource_name=None):
    """The probe set.

    `buffer_name` comes from /config; `resource_name` from the generated
    interface. Load an experiment with an image view element to exercise /res
    properly - with none, those probes only cover the refusal paths.
    """
    b = buffer_name
    probes = [
        Probe("config", "/config", schema="Config"),
        Probe("meta", "/meta", schema="Meta",
              relates_to=["meta-sensors", "meta-missing-value-representation"]),
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
              relates_to=["get-unknown-reference-buffer", "cors-error-paths"]),
        Probe("export.bad.format", "/export", {"format": "99"},
              expect_json=False, relates_to=["export-invalid-format"]),
        Probe("export.missing.format", "/export",
              expect_json=False,
              relates_to=["export-invalid-format", "cors-error-paths"]),
        Probe("res.missing.src", "/res",
              relates_to=["res-fallback"], keep_values=["error"]),
        Probe("res.unknown.src", "/res", {"src": "nosuchfile___.png"},
              relates_to=["res-fallback"], keep_values=["error"]),

        Probe("control.bad.command", "/control", {"cmd": "nosuchcommand___"},
              schema="ControlResult"),
        Probe("control.no.command", "/control", schema="ControlResult"),
    ]

    if resource_name:
        probes.insert(
            len(probes) - 2,
            Probe("res.existing", "/res", {"src": resource_name},
                  expect_json=False, relates_to=["res-content-type"]))

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


def shape(value, path="", keep=frozenset()):
    """A structural signature: keys, types, enum choices and booleans."""
    if path in VOLATILE:
        return f"<volatile {type(value).__name__}>"
    if path in keep:
        return repr(value)
    if isinstance(value, dict):
        return {k: shape(v, f"{path}.{k}" if path else k, keep)
                for k, v in sorted(value.items())}
    if isinstance(value, list):
        # Collapse to the set of distinct element shapes, so a different number
        # of samples is not reported as a difference.
        seen = []
        for item in value:
            s = shape(item, path, keep)
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


def diff_shapes(a, b, path=""):
    """Differences between two shapes, ignoring what is merely state.

    An **empty array is treated as compatible with any array.** Two phones are
    never in the same measurement state - one may have been started and the other
    not - and an empty buffer or an empty event list says nothing about the
    contract, only that nothing has happened yet. Comparing them as different
    shapes buried the real findings under five spurious failures on the first run
    against real devices.
    """
    here = path or "."
    if isinstance(a, dict) and isinstance(b, dict):
        if "<array of>" in a and "<array of>" in b:
            ea, eb = a["<array of>"], b["<array of>"]
            if not ea or not eb:          # no data on one side: nothing to compare
                return []
            out = []
            for extra in sorted(set(map(repr, ea)) - set(map(repr, eb))):
                out.append(f"android only: {here}[]: {extra}")
            for extra in sorted(set(map(repr, eb)) - set(map(repr, ea))):
                out.append(f"ios only:     {here}[]: {extra}")
            return out
        out = []
        for k in sorted(set(a) | set(b)):
            sub = f"{path}.{k}" if path else k
            if k not in b:
                out += [f"android only: {ln}" for ln in flatten(a[k], sub)]
            elif k not in a:
                out += [f"ios only:     {ln}" for ln in flatten(b[k], sub)]
            else:
                out += diff_shapes(a[k], b[k], sub)
        return out
    if a != b:
        return [f"{here}: android={a} ios={b}"]
    return []


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


def pick_resource(base):
    """A resource name the running experiment actually references.

    /config does not list resources - there is no <resource> element in the
    format, both apps derive the list from the view elements that name a file -
    so the only way to find one from outside is to read the generated interface,
    which links each image as res?src=NAME.
    """
    r = fetch(f"{base.rstrip('/')}/")
    if r["status"] != 200:
        return None
    names = re.findall(rb"res\?src=([^\"'\\ >]+)", r["body"])
    return names[0].decode() if names else None


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
    resource_name = None
    for base in targets.values():
        resource_name = resource_name or pick_resource(base)
    print(f"experiment crc32 {next(iter(crc.values()))}, probing buffer "
          f"{buffer_name!r}"
          + (f", resource {resource_name!r}" if resource_name
             else ", no image resource in this experiment")
          + "\n")

    probes, control, clearing = build_probes(buffer_name, resource_name)
    if args.allow_control:
        probes += control
    if args.allow_clear:
        probes += clearing

    skip = {n.strip() for n in args.skip.split(",") if n.strip()}
    unknown_skips = skip - {p.name for p in probes}
    if unknown_skips:
        sys.exit(f"--skip names no such probe: {', '.join(sorted(unknown_skips))}")
    if skip:
        probes = [p for p in probes if p.name not in skip]
        print(f"skipping: {', '.join(sorted(skip))}\n")

    failures, expected_diffs = [], []
    cors_seen = {name: set() for name in targets}
    # A probe can kill the app it is aimed at - export-invalid-format does
    # exactly that on iOS. Once a target has stopped answering, every later
    # probe against it "diverges", which buries the one real finding under a
    # page of noise. So notice it and stop.
    died_after = {}

    for probe in probes:
        if died_after:
            break
        results = {}
        for name, base in targets.items():
            r = fetch(probe.url(base))
            if r.get("transport_error"):
                if name not in died_after:
                    died_after[name] = probe.name
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
                "shape": (shape(parsed, "", probe.keep_values)
                          if parsed is not None else "<non-json>"),
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
        diffs += diff_shapes(a["shape"], i["shape"])

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
            expected_diffs.append((
                Probe(f"server.cors.{name}", "/", relates_to=["cors-error-paths"]),
                [f"{name} sends the CORS header on some endpoints and not others"]))
    if len(targets) == 2:
        # "ever sends it" rather than "always sends it", so a platform that is
        # internally inconsistent (see cors-error-paths) is still compared with
        # the other one.
        a_cors = any(cors_seen["android"])
        i_cors = any(cors_seen["ios"])
        if a_cors != i_cors:
            expected_diffs.append((
                Probe("server.cors", "/", relates_to=["cors-header"]),
                [f"Access-Control-Allow-Origin: android={a_cors} ios={i_cors}"]))

    # A recorded divergence that no probe can see any more has probably been
    # fixed on one side, and the entry is now lying to readers. Reported as a
    # note rather than a failure: some probes cannot observe their divergence
    # through a shape diff alone, so absence here is a prompt to check, not
    # proof. This is the signal that someone fixed a bug and forgot the docs.
    probed_ids = {i for p in probes for i in p.relates_to}
    if len(targets) == 2:
        probed_ids.add("cors-header")   # checked above, not by a probe
    seen_ids = {i for p, _ in expected_diffs for i in p.relates_to}
    resolved = sorted(probed_ids - seen_ids)

    # --------------------------------------------------------------- report
    if died_after:
        for name, probe_name in died_after.items():
            print(f"*** {name} stopped answering during probe '{probe_name}'.\n")
            print(f"    The app has most likely crashed - phyphox serves this API\n"
                  f"    in-process, so a trap takes the whole app down and the\n"
                  f"    socket with it.\n")
            print(f"    Restart phyphox on the {name} device, then re-run with\n"
                  f"      --skip {probe_name}\n"
                  f"    to get through the remaining probes.\n")
        print("    Probing stopped here; results below cover only what ran.\n")

    if resolved:
        print("Recorded divergences that did NOT show up in this run:\n")
        for i in resolved:
            print(f"  {i}")
        print("\n  If one of these was fixed, update its entry in "
              "inconsistencies.yml (status: fixed) and the spec along with it.\n")

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
    p.add_argument("--skip", default="",
                   help="comma-separated probe names to leave out, e.g. after one "
                        "of them has been found to crash an app")
    args = p.parse_args()
    if not args.android and not args.ios:
        p.error("give at least one of --android / --ios")
    sys.exit(run(args))


if __name__ == "__main__":
    main()
