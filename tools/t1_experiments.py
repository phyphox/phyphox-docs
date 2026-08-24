#!/usr/bin/env python3
"""T1 experiments-end-to-end driver (area K, tier T1).

For every shipped experiment: open it via phyphox://asset=..., start it,
let it run, stop it, download every export format and validate the files
against the experiment's export block, record which buffers filled - no
crash, no hang. Runs host-side against an emulator (or a device) with the
remote API as the bus.

    python3 tools/t1_experiments.py --platform android [--serial S]
        [--emulator] [--seconds 10] [--port 8080] [--subset raw/]
        [--out results.json] [--collection PATH]

Preconditions:
  - The app must serve the remote API for launched experiments. The
    driver flips the remote-enable switch itself (decided 2026-08-25):
    Android `adb shell setprop debug.phyphox.remote 1` (cleared again at
    the end of the run), iOS the `-phyphoxRemote` launch argument. On a
    build without the switch it polls and reports a per-experiment
    "remote API not reachable" finding instead of hanging.
  - Android: adb in PATH, the device/emulator connected; the driver sets
    up `adb forward tcp:<port> tcp:8080` itself. With --emulator it
    injects sensor values through the emulator console (adb emu) so the
    real sensor pipeline produces data.
  - iOS (macOS host only): the app installed on a booted simulator;
    launches use `xcrun simctl launch <udid> <bundle> -phyphoxUrl ...`.

Experiments under bluetooth/ are skipped by default: headless, they stop
at the device-scan dialog; their data plane is covered by the BLE lab
(area J) and their parsing by the corpus. --include-bluetooth launches
them anyway (load-phase smoke only, nothing is started).

Results: one JSON object per experiment (loaded, started, buffers that
filled, export findings per format, errors), written to --out and
summarized on stdout. Exit 1 if any experiment crashed the app, failed
to load, or produced an invalid export file.
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_export

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEFAULT_COLLECTION = os.path.join(
    ROOT, "..", "phyphox-android", "app", "src", "main", "assets", "experiments")
ANDROID_BUNDLE = "de.rwth_aachen.phyphox"
IOS_BUNDLE = "de.rwth-aachen.physics.phyphox"
FORMATS = range(6)

# Emulator console sensors the injection loop wiggles, with a base vector.
EMULATOR_SENSORS = {
    "acceleration": (0.3, 0.2, 9.81),
    "gyroscope": (0.1, -0.1, 0.05),
    "magnetic-field": (22.0, 5.8, -43.1),
    "pressure": (1013.25,),
    "light": (400.0,),
    "proximity": (5.0,),
    "humidity": (45.0,),
    "temperature": (23.5,),
}


def sh(cmd, timeout=30):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def api(base, path, timeout=5):
    try:
        with urllib.request.urlopen(base + path, timeout=timeout) as r:
            body = r.read()
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()


def wait_api(base, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        status, _ = api(base, "/config", timeout=2)
        if status == 200:
            return True
        time.sleep(0.5)
    return False


class Android:
    def __init__(self, serial, port):
        self.adb = ["adb"] + (["-s", serial] if serial else [])
        self.port = port
        sh(self.adb + ["forward", f"tcp:{port}", "tcp:8080"])
        # the remote-enable switch: a debug.* property is writable only by
        # the shell UID, so this is the host-controlled counterpart of the
        # iOS launch argument. Sticky until reboot - cleanup() clears it.
        sh(self.adb + ["shell", "setprop", "debug.phyphox.remote", "1"])

    def cleanup(self):
        sh(self.adb + ["shell", "setprop", "debug.phyphox.remote", "''"])

    def launch(self, asset_path):
        url = "phyphox://asset=" + urllib.parse.quote(asset_path, safe="")
        r = sh(self.adb + ["shell", "am", "start", "-W", "-a",
                           "android.intent.action.VIEW", "-d", url])
        return r.returncode == 0 and "Error" not in r.stdout

    def stop_app(self):
        sh(self.adb + ["shell", "am", "force-stop", ANDROID_BUNDLE])

    def inject(self, t):
        # wiggle every sensor slightly around its base so buffers move
        for name, base_v in EMULATOR_SENSORS.items():
            vals = [f"{v + 0.05 * ((t + i) % 3):g}" for i, v in enumerate(base_v)]
            sh(self.adb + ["emu", "sensor", "set", name, ":".join(vals)],
               timeout=5)


class IOS:
    def __init__(self, udid, port):
        self.udid = udid or "booted"
        self.port = port

    def launch(self, asset_path):
        url = "phyphox://asset=" + urllib.parse.quote(asset_path, safe="")
        r = sh(["xcrun", "simctl", "launch", self.udid, IOS_BUNDLE,
                "-phyphoxUrl", url, "-phyphoxRemote"])
        return r.returncode == 0

    def cleanup(self):
        pass

    def stop_app(self):
        sh(["xcrun", "simctl", "terminate", self.udid, IOS_BUNDLE])

    def inject(self, t):
        pass  # the iOS simulator cannot inject sensors (recorded platform difference)


def run_experiment(dev, base, rel, path, args):
    result = {"experiment": rel, "loaded": False, "remote": False,
              "started": False, "filled": [], "exports": {}, "errors": []}
    if not dev.launch(rel):
        result["errors"].append("launch failed")
        return result
    result["loaded"] = True

    if not wait_api(base, args.api_wait):
        result["errors"].append("remote API not reachable (is remote access "
                                "enabled for launched experiments?)")
        return result
    result["remote"] = True

    status, body = api(base, "/config")
    try:
        config = json.loads(body)
    except Exception:
        result["errors"].append("/config unparsable")
        return result
    buffers = [b["name"] for b in config.get("buffers", [])]

    status, _ = api(base, "/control?cmd=start")
    result["started"] = status == 200
    t0 = time.time()
    while time.time() - t0 < args.seconds:
        if args.emulator:
            dev.inject(int(time.time() - t0))
        time.sleep(1.0)
    api(base, "/control?cmd=stop")

    if buffers:
        q = "&".join(urllib.parse.quote(b) + "=full" for b in buffers)
        status, body = api(base, "/get?" + q, timeout=20)
        if status == 200:
            try:
                got = json.loads(body).get("buffer", {})
                result["filled"] = sorted(
                    n for n, v in got.items() if v.get("buffer"))
            except Exception:
                result["errors"].append("/get unparsable")

    sets = validate_export.export_sets(path)
    if sets:
        for fmt in FORMATS:
            status, body = api(base, f"/export?format={fmt}", timeout=30)
            if status != 200:
                result["exports"][fmt] = [f"status {status}"]
                continue
            problems = validate_export.validate(
                body, sets, fmt, require_rows=args.require_rows)
            result["exports"][fmt] = problems

    # the app must still be alive
    if not wait_api(base, 5):
        result["errors"].append("app stopped answering after the run")
    return result


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--platform", required=True, choices=["android", "ios"])
    ap.add_argument("--serial", help="adb serial / simulator udid")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--collection", default=DEFAULT_COLLECTION,
                    help="phyphox-experiments checkout (default: the "
                         "Android sibling's submodule)")
    ap.add_argument("--subset", default="",
                    help="only experiments whose path starts with this")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--api-wait", type=float, default=15.0)
    ap.add_argument("--emulator", action="store_true",
                    help="inject sensor values via the emulator console")
    ap.add_argument("--require-rows", action="store_true",
                    help="an export set without rows is a finding")
    ap.add_argument("--include-bluetooth", action="store_true")
    ap.add_argument("--out", default="t1-results.json")
    args = ap.parse_args()

    collection = os.path.normpath(args.collection)
    experiments = []
    for dirpath, dirs, names in os.walk(collection):
        dirs[:] = [d for d in dirs if d not in (".git", "res")]
        for n in sorted(names):
            if n.endswith(".phyphox"):
                rel = os.path.relpath(os.path.join(dirpath, n), collection)
                if args.subset and not rel.startswith(args.subset):
                    continue
                if rel.startswith("bluetooth") and not args.include_bluetooth:
                    continue
                experiments.append(rel)
    if not experiments:
        sys.exit(f"no experiments under {collection}")

    if args.platform == "android":
        dev = Android(args.serial, args.port)
    else:
        dev = IOS(args.serial, args.port)
    base = f"http://127.0.0.1:{args.port}"

    results, hard_failures = [], 0
    try:
        run_all(dev, base, collection, experiments, args, results)
    finally:
        dev.cleanup()
    hard_failures = sum(
        1 for r in results
        if r["errors"] or not r["loaded"]
        or any(p for p in r["exports"].values()))

    with open(args.out, "w") as f:
        json.dump({"platform": args.platform, "results": results}, f, indent=1)
    print(f"\n{len(results)} experiment(s), {hard_failures} with findings "
          f"-> {args.out}")
    return 1 if hard_failures else 0


def run_all(dev, base, collection, experiments, args, results):
    for rel in experiments:
        print(f"== {rel}")
        r = run_experiment(dev, base, rel, os.path.join(collection, rel), args)
        results.append(r)
        bad_exports = {f: p for f, p in r["exports"].items() if p}
        if r["errors"] or not r["loaded"] or bad_exports:
            for e in r["errors"]:
                print(f"   ! {e}")
            for f, p in bad_exports.items():
                print(f"   ! export format {f}: {'; '.join(p)}")
        else:
            print(f"   ok - {len(r['filled'])} buffer(s) filled")


if __name__ == "__main__":
    sys.exit(main())
