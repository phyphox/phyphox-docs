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
    up `adb forward tcp:<port> tcp:8080` itself and pre-grants the
    runtime permissions an unattended run cannot confirm (RECORD_AUDIO,
    CAMERA, fine/coarse location) - without them every audio, camera,
    GPS and depth experiment hangs in the permission dialog and reports
    "remote API not reachable". With --emulator it injects sensor values
    through the emulator console (adb emu) so the real sensor pipeline
    produces data.
  - iOS (macOS host only): the app installed on a booted simulator;
    launches use `xcrun simctl launch <udid> <bundle> -phyphoxUrl ...`.

Experiments under bluetooth/ are skipped by default: headless, they stop
at the device-scan dialog; their data plane is covered by the BLE lab
(area J) and their parsing by the corpus. --include-bluetooth launches
them anyway (load-phase smoke only, nothing is started).

With --require-rows, a set whose source buffers never filled on this
target (no microphone samples on an emulator, no GPS fix indoors,
event-based sensors without events) is validated structurally but not
required to carry rows - such sets are recorded per experiment under
"no_stimulus_sets" instead of failing the run.

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
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_export   # noqa: E402 - after the path insert

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


class _Timeout:
    """Failed-command stand-in for a call that timed out: a wedged
    simulator or adb degrades into one failed step instead of an escaped
    TimeoutExpired killing the whole sweep (seen on iOS CI: a stop_app
    hanging >30 s on a simulator that normally answers in 0.4 s)."""
    returncode = -1
    stdout = ""
    stderr = "timed out"


def sh(cmd, timeout=30):
    """One retry on timeout: a 30 s hang on launch or terminate is a
    simulator/adb hiccup, not a property of the experiment (measured
    healthy duration 0.2-0.4 s) - the retry costs nothing when things
    work and removes the one failure mode that has turned this workflow
    red without an app defect behind it. The ~ retried note keeps the
    hiccup visible even when the retry succeeds."""
    for attempt in (1, 2):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout)
            if attempt == 2:
                print(f"   ~ retried after a timeout: "
                      f"{' '.join(cmd[:4])} ...")
            return r
        except subprocess.TimeoutExpired:
            if attempt == 1:
                continue
            print(f"   ~ command timed out twice ({timeout}s each): "
                  f"{' '.join(cmd[:4])} ...")
            return _Timeout()


def api(base, path, timeout=5):
    try:
        with urllib.request.urlopen(base + path, timeout=timeout) as r:
            body = r.read()
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()


def wait_api(base, seconds, probe_timeout=2):
    """Seconds until /config answered, or None. The elapsed time is a
    datum: a late answer distinguishes a slow host from an experiment the
    app declined."""
    t0 = time.time()
    deadline = t0 + seconds
    while time.time() < deadline:
        status, _ = api(base, "/config", timeout=probe_timeout)
        if status == 200:
            return time.time() - t0
        time.sleep(0.5)
    return None



def _claim_host_port(adb_serial_cmd, port):
    """Evict any existing forward of this HOST port before binding it:
    adb does not rebind a port owned by another device, so a stale
    forward silently routes the driver to the wrong phone (cost a lab
    run: host 8080 still pointed at the Pixel 3 while the Pixel 9 Pro
    was being tested)."""
    r = sh(["adb", "forward", "--list"])
    for line in (r.stdout or "").splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1] == f"tcp:{port}":
            sh(["adb", "-s", parts[0], "forward", "--remove", f"tcp:{port}"])
    sh(adb_serial_cmd + ["forward", f"tcp:{port}", "tcp:8080"])


class Android:
    def __init__(self, serial, port):
        self.adb = ["adb"] + (["-s", serial] if serial else [])
        self.port = port
        _claim_host_port(self.adb, port)
        # runtime permissions an unattended run cannot confirm; failures
        # are ignored (a permission not declared cannot be granted)
        for perm in ("RECORD_AUDIO", "CAMERA", "ACCESS_FINE_LOCATION",
                     "ACCESS_COARSE_LOCATION"):
            sh(self.adb + ["shell", "pm", "grant", ANDROID_BUNDLE,
                           f"android.permission.{perm}"])
        # the remote-enable switch: a debug.* property is writable only by
        # the shell UID, so this is the host-controlled counterpart of the
        # iOS launch argument. Sticky until reboot - cleanup() clears it.
        sh(self.adb + ["shell", "setprop", "debug.phyphox.remote", "1"])
        # ...and the auto-confirm switch, or a network experiment's privacy
        # notice sits modally over the sweep (sensordb in the shipped
        # collection has a <network> block) - the iOS branch passes
        # -phyphoxAutoConfirm on every launch
        sh(self.adb + ["shell", "setprop", "debug.phyphox.autoConfirm", "1"])

    def cleanup(self):
        sh(self.adb + ["shell", "setprop", "debug.phyphox.remote", "''"])
        sh(self.adb + ["shell", "setprop", "debug.phyphox.autoConfirm", "''"])

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
    """Simulator by default (what CI drives); --ios-target device switches
    to devicectl for real hardware, where the app serves port 80 and the
    host-side forward is set up by the caller (the lab driver's
    IOSDevice.prepare) rather than here."""

    def __init__(self, udid, port, target="simulator"):
        self.udid = udid or "booted"
        self.port = port
        self.target = target
        self._hw = None
        if target == "device":
            # hardware launching lives in tools/lab/device.py, which
            # already handles devicectl AND the pymobiledevice3 dvt
            # fallback for iOS 16 devices that CoreDevice cannot see
            # (the iPhone 8). Delegate rather than duplicate it - the
            # first duplicate cost the whole iPhone 8 sweep. prepare()
            # is NOT called: the caller owns the port forward.
            from lab.device import IOSDevice
            self._hw = IOSDevice(udid, port)

    def launch(self, asset_path):
        url = "phyphox://asset=" + urllib.parse.quote(asset_path, safe="")
        # --terminate-running-process: simctl launch onto a running app does
        # not deliver new arguments (found by the iOS session 2026-08-25) -
        # the app would keep the previous experiment and this driver would
        # report a false ok. -phyphoxRemotePort keeps the served port and
        # the driver's base URL in step; -phyphoxAutoConfirm accepts the
        # dialogs a headless run cannot tap (network privacy).
        if self._hw is not None:
            return self._hw.launch(asset_path)
        r = sh(["xcrun", "simctl", "launch", "--terminate-running-process",
                self.udid, IOS_BUNDLE,
                "-phyphoxUrl", url, "-phyphoxRemote",
                "-phyphoxRemotePort", str(self.port),
                "-phyphoxAutoConfirm"])
        return r.returncode == 0

    def cleanup(self):
        pass

    def stop_app(self):
        if self.target == "device":
            return          # --terminate-existing on launch
        sh(["xcrun", "simctl", "terminate", self.udid, IOS_BUNDLE])

    def inject(self, t):
        pass  # the iOS simulator cannot inject sensors (recorded platform difference)


def is_link_entry(path):
    """True for a collection entry with isLink=true - not a runnable
    experiment but a redirect (opening it launches the browser), so the
    sweep skips it."""
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return False
    return (root.get("isLink") or "").strip().lower() == "true"


_SAVED = []


def _save_artifact(args, rel, fmt, body, limit=8):
    """Write a failing export next to --out, capped so a systematically
    broken run cannot fill the disk."""
    if len(_SAVED) >= limit:
        return None
    out_dir = os.path.dirname(os.path.abspath(args.out)) or "."
    stem = rel.replace("/", "_").replace(".phyphox", "")
    ext = "xlsx" if fmt == 0 else "zip"
    path = os.path.join(out_dir, f"failed-export-{stem}-fmt{fmt}.{ext}")
    try:
        with open(path, "wb") as f:
            f.write(body)
    except OSError:
        return None
    _SAVED.append(path)
    return path


def uses_audio_input(path):
    """True if the experiment records audio - the iOS simulator's
    AVAudioEngine input can abort the whole app (AudioToolbox RPC
    timeout), so these are skipped there instead of launched."""
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return False
    ns = root.tag.split("}")[0] + "}" if root.tag.startswith("{") else ""
    for inp in root.findall(f"{ns}input"):
        for child in inp:
            if child.tag == f"{ns}audio":
                return True
    return False


def run_experiment(dev, base, rel, path, args):
    result = {"experiment": rel, "loaded": False, "remote": False,
              "started": False, "filled": [], "exports": {}, "errors": []}
    # Every step below is individually bounded, but their sum was not:
    # one pathological experiment (doppler on the Galaxy A3, whose
    # buffer-reading requests stall) held a whole sweep open long after
    # the other devices had finished, 2026-08-27. A sweep must end; the
    # budget turns such a stall into a reported finding on that one
    # experiment instead of an open-ended wait.
    budget_ends = time.time() + args.experiment_budget
    if is_link_entry(path):
        result["skipped"] = "link entry (isLink), not a runnable experiment"
        return result
    if (args.platform == "ios" and args.ios_target == "simulator"
            and uses_audio_input(path)):
        # simulator only: its AVAudioEngine input can abort the app. On
        # real hardware the microphone works and these experiments are
        # exactly the ones worth running (the lab skipped 11 of 40 for
        # this reason until 2026-08-26)
        result["skipped"] = "audio input aborts the app on the simulator"
        return result
    # a fresh app per experiment: on Android a stacked Experiment activity
    # keeps holding the remote port (the next one either fails to bind or
    # falls back to another port while the forward still points at the
    # old one - found by the Android T1 run). iOS is NOT force-stopped
    # here: launch --terminate-running-process already does it, and the
    # redundant simctl terminate was seen hanging >30 s on a wedged
    # simulator.
    if args.platform == "android":
        dev.stop_app()
    if not dev.launch(rel):
        result["errors"].append("launch failed")
        return result
    result["loaded"] = True

    elapsed = wait_api(base, args.api_wait)
    if elapsed is None:
        # a second, more patient window separates "the app declined this
        # experiment" from "the host was too slow this time" - without it
        # a loadable experiment on a loaded host silently shrinks the
        # covered subset (observed on sensordb, which normally answers
        # 1.1 s after launch)
        elapsed = wait_api(base, args.api_wait, probe_timeout=10)
        if elapsed is not None:
            elapsed += args.api_wait
    if elapsed is None:
        # The app declines an experiment the target cannot run ("sensor
        # not available") and returns to the collection, so no API comes
        # up. That is scoping, not failure - on EITHER platform: the iOS
        # simulator lacks most sensors, and a phone without depth
        # hardware declines depth.phyphox just the same (Pixel 9 Pro,
        # found by the lab 2026-08-26). It is only indistinguishable
        # from a broken remote switch in the abstract - run_all() has
        # the evidence and reclassifies afterwards, so this verdict is
        # provisional.
        result["not_loadable"] = True
        return result
    if elapsed > args.api_wait:
        result["slow_api"] = round(elapsed, 1)
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
        # WITHOUT "=full": the single-value form answers with each
        # buffer's last value, which is all this check needs (a buffer
        # that produced data has a non-null last value). Asking for the
        # full contents of every buffer moves megabytes for an audio
        # experiment and simply never completed on the Galaxy A3
        # (doppler: no answer in 60 s, while /config answered in 20 ms)
        # - the value of knowing WHICH buffers filled does not justify
        # downloading all of them. Caveat: a buffer holding only NaN
        # reads as not filled, since /get sends non-finite values as
        # null; that only ever relaxes an export row requirement.
        q = "&".join(urllib.parse.quote(b) + "=" for b in buffers)
        status, body = api(base, "/get?" + q, timeout=30)
        if status == 200:
            try:
                got = json.loads(body).get("buffer", {})
                result["filled"] = sorted(
                    n for n, v in got.items()
                    if any(x is not None for x in (v.get("buffer") or [])))
            except Exception:
                result["errors"].append("/get unparsable")
        else:
            result["errors"].append(
                f"/get did not answer (status {status}) - the device may be "
                f"too slow for this experiment's data volume")

    sets = validate_export.export_sets(path)
    if sets:
        # rows are only required of sets whose source buffers actually
        # filled on this target; the rest lack real-world stimulus here
        filled = set(result["filled"])
        rows_for = {name for name, _cols, bufs in sets
                    if any(b in filled for b in bufs)}
        result["no_stimulus_sets"] = sorted(
            name for name, _cols, _bufs in sets if name not in rows_for)
        for fmt in FORMATS:
            if time.time() > budget_ends:
                result["errors"].append(
                    f"over the {args.experiment_budget:.0f}s budget for one "
                    f"experiment - formats {fmt}..5 not tried")
                break
            status, body = api(base, f"/export?format={fmt}",
                               timeout=args.export_timeout)
            if status != 200:
                result["exports"][fmt] = [
                    f"no export: status {status}"
                    + (f" (no answer within {args.export_timeout:.0f}s - "
                       f"raise --export-timeout if this device is simply "
                       f"slow)" if status is None else "")]
                continue
            problems = validate_export.validate(
                body, sets, fmt, require_rows=args.require_rows,
                require_rows_for=rows_for)
            result["exports"][fmt] = problems
            if problems:
                # keep the evidence: an export finding is otherwise a
                # sentence with no file behind it, and the interesting
                # ones are the odd formats out (an iPad reported one
                # empty set in format 2 while the other five were fine -
                # unreproducible on Android, and unexaminable without
                # the bytes)
                saved = _save_artifact(args, rel, fmt, body)
                if saved:
                    result.setdefault("saved_exports", {})[fmt] = saved
                result["exports"][fmt] = problems + [
                    f"({len(body)} bytes"
                    + (f", saved as {os.path.basename(saved)}" if saved else "")
                    + ")"]

    # the app must still be alive (same patience as the startup wait - a
    # loaded emulator can take a while after six export downloads)
    if not wait_api(base, args.api_wait):
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
    ap.add_argument("--experiment-budget", type=float, default=300.0,
                    help="seconds one experiment may take before the driver "
                         "gives up and moves on, reporting the overrun - a "
                         "sweep has to end even when a device stalls")
    ap.add_argument("--export-timeout", type=float, default=30.0,
                    help="seconds to wait for one export. 30 is already "
                         "generous: the heaviest shipped experiment exports "
                         "a few hundred rows, which even the oldest lab "
                         "phone writes in well under a second, so a longer "
                         "wait buys nothing and only hides a stall")
    ap.add_argument("--emulator", action="store_true",
                    help="inject sensor values via the emulator console")
    ap.add_argument("--require-rows", action="store_true",
                    help="an export set without rows is a finding")
    ap.add_argument("--include-bluetooth", action="store_true")
    ap.add_argument("--ios-target", choices=["simulator", "device"],
                    default="simulator",
                    help="iOS only: simulator (simctl, the CI default) or "
                         "device (devicectl; the caller provides the port "
                         "forward)")
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
        dev = IOS(args.serial, args.port, args.ios_target)
    base = f"http://127.0.0.1:{args.port}"

    results, hard_failures = [], 0
    try:
        run_all(dev, base, collection, experiments, args, results)
    finally:
        dev.cleanup()

    # Provisional not-loadable verdicts, judged with the whole run as
    # evidence: if NOTHING reached the remote API, the switch or the
    # forward is broken and every one of them is a real failure; if some
    # experiments did, the app simply declined the others.
    if not any(r.get("remote") for r in results):
        for r in results:
            if r.pop("not_loadable", None):
                r["errors"].append(
                    "remote API not reachable, and no experiment on this "
                    "target reached it - remote-enable switch or port "
                    "forward broken?")
    hard_failures = sum(
        1 for r in results
        if not r.get("skipped") and not r.get("not_loadable")
        and (r["errors"] or not r["loaded"]
             or any(p for p in r["exports"].values())))

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
        if r.get("skipped"):
            print(f"   - skipped: {r['skipped']}")
            continue
        if r.get("not_loadable"):
            print("   - not loadable on this target (the app declined it - "
                  "hardware or simulator lacks what it needs)")
            continue
        if r.get("slow_api"):
            print(f"   ~ remote API answered late ({r['slow_api']} s) - "
                  f"kept in the run")
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
