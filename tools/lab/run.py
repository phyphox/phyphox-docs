#!/usr/bin/env python3
"""The device-lab driver (T2). One entry point, split-host capable.

    python3 tools/lab/run.py --config lab.yml --host linuxbox
        [--platform android] [--devices pixel-9-pro,pixel-3]
        [--suites sensors,audio,experiments,languages]
        [--out results/] [--record-manifest pixel-9-pro]

    python3 tools/lab/run.py --merge results/   # combine host JSONs

lab.yml (local, never committed - lab.yml.example is the template)
assigns devices to named hosts. Each invocation runs its host's share
and writes <host>.json into --out; the MacBook can run the full set, or
the Linux machine runs the Android devices while the MacBook covers iOS
- the merge step combines the per-host files into one report.

Preconditions per the test plan: phones in developer mode, unlocked once
per run, media volume audible for the audio suite (set automatically on
Android, by hand on iOS), the debug builds installed. The iOS device
paths are UNVERIFIED until the first MacBook run.

--record-manifest launches each core sensor experiment on the named
device and writes tools/lab/devices/<id>.skeleton.yml with the observed
buffer names and /meta sensor list, to be hand-finished into the
committed per-device manifest (expected sensors, plausibility kinds,
rates).
"""

import argparse
import functools
import http.server
import json
import os
import socketserver
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import yaml
from lab import suites
from lab.device import AndroidDevice, IOSDevice, api, wait_api

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
FIXTURES = os.path.join(ROOT, "fixtures")

# the record-mode probe set per platform: iOS has no ambient light API
# (recorded platform difference - the light row is Android-only), and
# probing it there raises a sensor-not-available dialog that blocks the
# run while the API behind it still answers, so the skeleton would
# happily record a sensor the device cannot serve.
CORE_EXPERIMENTS = {
    "android": ["accelerometer.phyphox", "gyroscope.phyphox",
                "magnetometer.phyphox", "pressure.phyphox",
                "light.phyphox", "gps.phyphox"],
    "ios": ["accelerometer.phyphox", "gyroscope.phyphox",
            "magnetometer.phyphox", "pressure.phyphox", "gps.phyphox"],
}


class _FixtureServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    def server_bind(self):
        socketserver.TCPServer.server_bind(self)   # skip the FQDN lookup
        self.server_name, self.server_port = "localhost", self.server_address[1]


def serve_fixtures(port):
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=FIXTURES)
    srv = _FixtureServer(("0.0.0.0", port), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _resolve_artifact(path, config_path):
    if os.path.isabs(path):
        return path
    bases = [os.getcwd(),
             os.path.dirname(os.path.abspath(config_path)),
             ROOT, os.path.dirname(ROOT)]
    for base in bases:
        candidate = os.path.normpath(os.path.join(base, path))
        if os.path.exists(candidate):
            return candidate
    return os.path.normpath(os.path.join(bases[0], path))


def _summarize(merged):
    """The merged run as something a human reads: one line per device and
    suite, findings and warnings underneath, the language gate last. The
    JSON keeps everything; this is what tells you whether to ship."""
    lines = ["# Device lab run", ""]
    total = {"ok": 0, "fail": 0, "warn": 0}
    for host, data in sorted(merged.get("hosts", {}).items()):
        lines.append(f"## {host}")
        for dev_id, suites in sorted((data.get("devices") or {}).items()):
            if not suites:
                lines.append(f"- **{dev_id}**: no suite ran")
                continue
            states = []
            for name, r in sorted(suites.items()):
                ok = r.get("passed")
                states.append(f"{name} {'ok' if ok else 'FAIL'}")
                total["ok" if ok else "fail"] += 1
            lines.append(f"- **{dev_id}**: " + ", ".join(states))
            for name, r in sorted(suites.items()):
                # collapse repeats: a sweep that fails the same way for
                # every experiment must not bury the run in 39 identical
                # lines (the report is read by a human deciding whether
                # to ship)
                for mark, key in (("!!", "findings"), ("~", "warnings")):
                    seen = {}
                    for item in r.get(key) or []:
                        text = str(item).lstrip("! ").strip()
                        seen[text] = seen.get(text, 0) + 1
                        if key == "warnings":
                            total["warn"] += 1
                    for text, n in seen.items():
                        lines.append(f"    - {mark} {name}: {text}"
                                     + (f"  (x{n})" if n > 1 else ""))
        for platform, r in sorted((data.get("languages") or {}).items()):
            if r.get("skipped"):
                lines.append(f"- languages[{platform}]: skipped "
                             f"({r['skipped']})")
            elif r.get("passed"):
                n = len((r.get("details") or {}).get("locales") or [])
                lines.append(f"- languages[{platform}]: ok ({n} locales "
                             f"match the canonical list)")
            else:
                lines.append(f"- languages[{platform}]: FAIL")
                for f in r.get("findings") or []:
                    lines.append(f"    - !! {f}")
        lines.append("")
    lines.append(f"**{total['ok']} suite(s) passed, {total['fail']} failed, "
                 f"{total['warn']} warning(s).** Warnings are bench "
                 f"conditions (sensor plausibility), never failures - see "
                 f"tools/lab/README.md.")
    return "\n".join(lines) + "\n"


def make_device(entry, host_cfg):
    if entry["platform"] == "android":
        return AndroidDevice(entry["serial"], entry.get("port", 8080))
    dev = IOSDevice(entry["serial"], entry.get("port", 8081))
    dev.host_ip = host_cfg.get("host_ip")
    return dev


def record_manifest(dev, dev_id, args):
    skeleton = {"device": dev_id, "recorded": "hand-finish this file into "
                "devices/" + dev_id + ".yml - see README"}
    exps = {}
    status, body = None, b""  # /meta is read once an experiment serves the API
    print("   watch the device: a sensor-not-available dialog blocks the "
          "run silently while the API behind it still answers - if one "
          "appears, that sensor does not belong in this device's manifest")
    for asset in CORE_EXPERIMENTS[dev.platform]:
        if not dev.launch(asset):
            exps[asset] = ("launch failed: "
                           + (getattr(dev, "last_error", "") or "no stderr"))
            continue
        if wait_api(dev.base, args.api_wait) is None:
            exps[asset] = "no remote API (sensor missing on this device?)"
            continue
        st, cfg = api(dev.base, "/config")
        try:
            exps[asset] = [b["name"] for b in json.loads(cfg).get("buffers", [])]
        except Exception:
            exps[asset] = "unparsable /config"
        if status != 200:
            status, body = api(dev.base, "/meta")
    skeleton["experiments"] = exps
    if status == 200:
        try:
            skeleton["meta_sensors"] = sorted(
                json.loads(body).get("sensors", {}).keys())
        except Exception:
            pass
    out = os.path.join(HERE, "devices", f"{dev_id}.skeleton.yml")
    with open(out, "w") as f:
        yaml.safe_dump(skeleton, f, sort_keys=False)
    print(f"wrote {out}")


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=os.path.join(HERE, "lab.yml"))
    ap.add_argument("--host", help="which lab.yml host this machine is")
    ap.add_argument("--platform", choices=["android", "ios"])
    ap.add_argument("--devices", default="",
                    help="comma-separated device ids (default: all of this host)")
    ap.add_argument("--suites", default="sensors,audio,experiments",
                    help="languages runs only when the host entry names artifacts")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--api-wait", type=float, default=15.0)
    ap.add_argument("--audio-floor", type=float, default=1.0)
    ap.add_argument("--fixture-port", type=int, default=8113)
    ap.add_argument("--out", dest="out_dir", default="lab-results")
    ap.add_argument("--record-manifest", metavar="DEVICE_ID")
    ap.add_argument("--merge", metavar="DIR")
    args = ap.parse_args()

    if args.merge:
        merged = {"hosts": {}}
        failures = 0
        for fn in sorted(os.listdir(args.merge)):
            if fn.endswith(".json") and not fn.startswith("experiments-"):
                with open(os.path.join(args.merge, fn)) as f:
                    host = json.load(f)
                merged["hosts"][fn[:-5]] = host
                for dev in host.get("devices", {}).values():
                    for suite in dev.values():
                        if isinstance(suite, dict) and suite.get("passed") is False:
                            failures += 1
        merged["failed_suites"] = failures
        out = os.path.join(args.merge, "merged.json")
        with open(out, "w") as f:
            json.dump(merged, f, indent=1)
        report = _summarize(merged)
        report_path = os.path.join(args.merge, "merged.md")
        with open(report_path, "w") as f:
            f.write(report)
        print(report)
        print(f"{failures} failing suite(s) -> {out}, {report_path}")
        return 1 if failures else 0

    with open(args.config) as f:
        cfg = yaml.safe_load(f)
    if not args.host or args.host not in (cfg.get("hosts") or {}):
        sys.exit("give --host, one of: " + ", ".join(cfg.get("hosts") or {}))
    host_cfg = cfg["hosts"][args.host]
    os.makedirs(args.out_dir, exist_ok=True)
    wanted = {d for d in args.devices.split(",") if d}

    srv = serve_fixtures(args.fixture_port)
    report = {"host": args.host, "devices": {}}
    # SUITE-MAJOR order: every device runs the sensors suite before any
    # device starts the next suite, so the first-run dialogs of a suite
    # (local network, microphone, camera) cluster at its start and the
    # operator can leave once a suite's first pass is through, instead
    # of supervising every device separately (maintainer, 2026-08-26)
    devices = []
    for dev_id, entry in (host_cfg.get("devices") or {}).items():
        if wanted and dev_id not in wanted:
            continue
        if args.platform and entry["platform"] != args.platform:
            continue
        dev = make_device(entry, host_cfg)
        dev.prepare(fixture_port=args.fixture_port)
        devices.append((dev_id, entry, dev))
        report["devices"][dev_id] = {}
    try:
        if args.record_manifest:
            for dev_id, entry, dev in devices:
                if args.record_manifest == dev_id:
                    record_manifest(dev, dev_id, args)
        else:
          for suite in args.suites.split(","):
            for dev_id, entry, dev in devices:
                print(f"== {suite} @ {dev_id} ({entry['platform']})")
                r = None
                if suite == "sensors":
                    manifest_path = os.path.join(HERE, "devices",
                                                 f"{dev_id}.yml")
                    if not os.path.exists(manifest_path):
                        r = {"passed": False,
                             "findings": [f"no manifest devices/{dev_id}.yml"
                                          f" - run --record-manifest first"]}
                    else:
                        with open(manifest_path) as f:
                            manifest = yaml.safe_load(f)
                        r = suites.run_sensor_suite(dev, manifest, args)
                elif suite == "audio":
                    r = suites.run_audio_suite(dev, args)
                elif suite == "experiments":
                    r = suites.run_experiments_suite(dev, args)
                if r is None:
                    continue
                report["devices"][dev_id][suite] = r
                state = "ok" if r.get("passed") else "FAIL"
                print(f"   {state}"
                      + ("".join(f"\n      ! {x}" for x in r.get("findings", [])))
                      + ("".join(f"\n      ~ {x}" for x in r.get("warnings", []))))
        art = host_cfg.get("artifacts") or {}
        # a relative artifact path is tried against the obvious bases -
        # where the command was run, the lab.yml's own directory, the
        # phyphox-docs root and the working root above it - so one synced
        # config works from either host without anyone having to know
        # which directory the driver happened to start in
        # an entry is either a bare path (a release candidate: a mismatch
        # FAILS) or {path: ..., release: false} for a development build,
        # where the comparison is reported but does not fail the run
        art = {p: (v if isinstance(v, dict) else {"path": v})
               for p, v in art.items()}
        for platform, spec in art.items():
            path = _resolve_artifact(spec["path"], args.config)
            r = suites.run_languages_suite(
                platform, path, aapt=host_cfg.get("aapt", "aapt"),
                release=spec.get("release", True))
            report.setdefault("languages", {})[platform] = r
            state = ("skipped: " + r["skipped"] if r.get("skipped")
                     else "ok" if r["passed"] else "FAIL")
            print(f"   languages[{platform}]: {state}"
                  + ("".join(f"\n      ! {x}" for x in r.get("findings", [])))
                  + ("".join(f"\n      ~ {x}" for x in r.get("warnings", []))))
    finally:
        for _dev_id, _entry, dev in devices:
            dev.cleanup()
        srv.shutdown()

    out = os.path.join(args.out_dir, f"{args.host}.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=1)
    bad = sum(1 for d in report["devices"].values()
              for s in d.values() if s.get("passed") is False)
    bad += sum(1 for r in (report.get("languages") or {}).values()
               if r.get("passed") is False)
    print(f"\n{bad} failing suite(s) -> {out}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
