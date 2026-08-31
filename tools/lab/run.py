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


class _QuietFixtureHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler narrates every request to stderr, which
    buries the run's own output - and it is not only one line per
    fixture fetch: a phone that tries https against the port produces a
    "Bad request version" wall of binary. The lab prints what the suites
    find; the fixture server is plumbing."""

    def log_message(self, *args):
        pass


# Colour only when a person is watching: every pass is also run with its
# output redirected to a file, and escape codes in a report someone reads
# a day later are worse than no colour at all.
_TTY = sys.stdout.isatty()
GREEN, RED, OFF = ("\033[32m", "\033[31m", "\033[0m") if _TTY else ("", "", "")


def verdict(passed):
    return f"{GREEN}ok{OFF}" if passed else f"{RED}FAIL{OFF}"


def serve_fixtures(port):
    handler = functools.partial(_QuietFixtureHandler, directory=FIXTURES)
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


def _t3_checklist(platforms):
    """The human checklist, generated from test-matrix.yml rather than
    written out here.

    The automated tiers stop at what a machine can reach: no runner takes
    a phone outdoors for a satellite fix, holds a printed QR code in front
    of a camera, or turns VoiceOver on. Those steps are rows like any
    other - listed, versioned and reviewed - and this puts them at the end
    of the report a person is already reading to decide whether to ship,
    which is the only moment they will be done.
    """
    matrix = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..",
        "test-matrix.yml"))
    try:
        import yaml
        with open(matrix, encoding="utf-8") as f:
            rows = (yaml.safe_load(f) or {}).get("tests") or []
    except Exception as e:
        return [f"_(could not read the T3 checklist from test-matrix.yml: "
                f"{e})_"]
    todo = [r for r in rows
            if r.get("manual") and r.get("status") == "active"
            and (not platforms or set(r.get("platforms") or []) & platforms)]
    if not todo:
        return []
    out = ["", "## T3 - by hand, once per platform", "",
           "Budget 30 minutes each. Nothing below is covered by anything "
           "above it.", ""]
    for row in todo:
        who = "/".join(sorted(row.get("platforms") or []))
        text = " ".join((row.get("description") or "").split())
        out.append(f"- [ ] **{row['id']}** ({who}) - {text}")
    return out


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
                det = r.get("details") or {}
                n = len(det.get("locales") or [])
                if det.get("release", True):
                    lines.append(f"- languages[{platform}]: ok ({n} locales, "
                                 f"matching the canonical list)")
                else:
                    # never claim a match for a test build: it carries the
                    # testing-only locales by design, and saying "26 match"
                    # against a canonical list of 22 was simply false
                    lines.append(f"- languages[{platform}]: ok, not a release "
                                 f"artifact ({n} locales; differences below "
                                 f"are information)")
                for w in r.get("warnings") or []:
                    total["warn"] += 1
                    lines.append(f"    - ~ {w}")
            else:
                lines.append(f"- languages[{platform}]: FAIL")
                for f in r.get("findings") or []:
                    lines.append(f"    - !! {f}")
                for w in r.get("warnings") or []:
                    total["warn"] += 1
                    lines.append(f"    - ~ {w}")
        lines.append("")
    lines.append(f"**{total['ok']} suite(s) passed, {total['fail']} failed, "
                 f"{total['warn']} warning(s).** A warning is something to "
                 f"know, not something that failed: a sensor reading outside "
                 f"its plausibility window (bench conditions, calibration) "
                 f"or a language difference in an artifact that is not a "
                 f"release candidate - see tools/lab/README.md.")
    seen = {p for data in (merged.get("hosts") or {}).values()
            for p in (data.get("platforms") or [])}
    lines += _t3_checklist(seen)
    return "\n".join(lines) + "\n"


class _ThreadTee:
    """stdout that keeps each worker thread's output apart.

    contextlib.redirect_stdout swaps sys.stdout for the whole PROCESS,
    so with several suites running at once the workers clobbered each
    other's redirect and swallowed the main thread's prints - which is
    why a parallel run stopped showing results at all. This routes a
    thread with a registered buffer into it and everyone else through to
    the real stdout."""

    def __init__(self, real):
        self._real = real
        self._buffers = {}

    def register(self, buf):
        self._buffers[threading.get_ident()] = buf

    def unregister(self):
        self._buffers.pop(threading.get_ident(), None)

    def write(self, data):
        buf = self._buffers.get(threading.get_ident())
        (buf or self._real).write(data)

    def flush(self):
        self._real.flush()

    def __getattr__(self, name):
        return getattr(self._real, name)


_TEE = None


def _one_suite(suite, dev_id, dev, args):
    """One suite on one device, capturing whatever it prints so parallel
    devices cannot interleave their output mid-line."""
    import io
    buf = io.StringIO()
    r = None
    if _TEE is not None:
        _TEE.register(buf)
    try:
        if suite == "sensors":
            manifest_path = os.path.join(HERE, "devices", f"{dev_id}.yml")
            if not os.path.exists(manifest_path):
                r = {"passed": False,
                     "findings": [f"no manifest devices/{dev_id}.yml - run "
                                  f"--record-manifest first"]}
            else:
                with open(manifest_path) as f:
                    manifest = yaml.safe_load(f)
                r = suites.run_sensor_suite(dev, manifest, args)
        elif suite == "audio":
            r = suites.run_audio_suite(dev, args)
        elif suite == "experiments":
            r = suites.run_experiments_suite(dev, args)
    finally:
        if _TEE is not None:
            _TEE.unregister()
    return r, [ln for ln in buf.getvalue().splitlines() if ln.strip()]


def _run_suite(suite, devices, args, jobs):
    """Yields (dev_id, entry, result, captured lines) per device as
    each finishes, run
    sequentially or across a small thread pool. The suites are I/O-bound
    - HTTP against a phone, a subprocess per device - so threads fit, and
    an exception on one device becomes that device's finding instead of
    ending the run."""
    if jobs <= 1:
        for dev_id, entry, dev in devices:
            print(f"== {suite} @ {dev_id} ({entry['platform']})", flush=True)
            r, captured = _one_suite(suite, dev_id, dev, args)
            for line in captured:
                print(f"   {line}")
            yield dev_id, entry, r, []
        return

    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(_one_suite, suite, dev_id, dev, args):
                   (dev_id, entry) for dev_id, entry, dev in devices}
        # as_completed, not submission order: a device reports the moment
        # IT finishes. Collecting in order meant the whole pool went
        # silent until the slowest device was done, which on a parallel
        # experiments sweep is most of an hour of nothing (2026-08-27).
        for fut in as_completed(futures):
            dev_id, entry = futures[fut]
            try:
                r, captured = fut.result()
            except Exception as e:
                r = {"passed": False,
                     "findings": [f"{type(e).__name__}: {e}"]}
                captured = []
            results.append((dev_id, entry, r, captured))
            yield dev_id, entry, r, captured
    return


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
    ap.add_argument("--board-port", action="append", default=[],
                    metavar="BOARD=PORT",
                    help="serial port per lab board for the ble suite, e.g. "
                         "--board-port esp32=/dev/ttyUSB0")
    ap.add_argument("--micropython-firmware", metavar="BIN",
                    help="ble suite: the ESP32 MicroPython firmware image. "
                         "The Arduino scenarios overwrite the whole flash, "
                         "so the suite reflashes it before the MicroPython "
                         "ones - only when the board is not already running "
                         "MicroPython")
    ap.add_argument("--connect-timeout", type=float, default=180.0,
                    help="ble suite: seconds for the phone's scan-and-connect "
                         "test")
    ap.add_argument("--link-timeout", type=float, default=45.0,
                    help="ble suite: seconds to wait for the board's data to "
                         "start arriving after the experiment loads. The "
                         "remote API answers before the BLE link is ready to "
                         "measure, so the suite proves the link instead of "
                         "trusting it and reports how long it took")
    ap.add_argument("--serial-window", type=float, default=8.0,
                    help="ble suite: seconds of board serial output to read "
                         "for the phone-to-board scenarios")
    ap.add_argument("--suites", default=None,
                    help="languages runs only when the host entry names "
                         "artifacts; ble needs --board-port and is not in "
                         "the default set because it wants the bench")
    ap.add_argument("--force-bench", action="store_true",
                    help="take the bench lock even though another run holds "
                         "it. Only when you know that run is gone")
    ap.add_argument("--record-ble-baseline", action="store_true",
                    help="ble suite: record what each board produces on the "
                         "REFERENCE release (normally the current store "
                         "build), so 'the previous version worked' is "
                         "measured. Interactive: that build predates the "
                         "automation seam, so a human connects the phone "
                         "and switches remote access on for each scenario. "
                         "Pass one --devices id")
    ap.add_argument("--record-wait", type=float, default=240.0,
                    help="--record-ble-baseline: seconds to wait per scenario "
                         "for the operator to connect the phone and switch "
                         "remote access on. The API answering IS the signal; "
                         "nothing is read from stdin")
    ap.add_argument("--ble-scenario", metavar="[LIB/]EXAMPLE",
                    help="ble suite: run only this scenario (bring-up and "
                         "debugging - the report is marked as narrowed)")
    ap.add_argument("--capture-ble-xml", action="store_true",
                    help="ble suite: freeze the XML each board serves into "
                         "corpus/valid/ble-libraries/ (the T0 half). "
                         "Deliberate and reviewed, like the baselines - it "
                         "rewrites corpus files, so run it when you mean to "
                         "and read the diff")
    ap.add_argument("--seconds", type=float, default=10.0)
    ap.add_argument("--api-wait", type=float, default=15.0)
    ap.add_argument("--audio-floor", type=float, default=1.0)
    ap.add_argument("--fixture-port", type=int, default=8113)
    ap.add_argument("--jobs", type=int, default=1,
                    help="devices to run in parallel per suite (audio is "
                         "always serial - the phones share a room). This is "
                         "for the long experiments sweep; N phones at once "
                         "also draw N times the USB power")
    ap.add_argument("--start-delay", type=float, default=3.0,
                    help="seconds to wait after an experiment loads before "
                         "starting it (default 3). Neither app starts one "
                         "whose bluetooth blocks have not connected yet")
    ap.add_argument("--ble-attempts", type=int, default=2,
                    help="how many times a ble scenario may be tried on one "
                         "phone before it counts as failed (default 2). "
                         "Passing on a later attempt is a pass with a "
                         "warning naming what failed first, and the attempt "
                         "count is in the report; flash failures, duplicate "
                         "advertisers and missing tools are never retried")
    ap.add_argument("--out", dest="out_dir", default="lab-results")
    ap.add_argument("--release", action="store_true",
                    help="run everything this host can: every suite it has "
                         "the hardware for, boards and firmware taken from "
                         "lab.yml. What is left afterwards - the other host, "
                         "the merge, the T3 checklist - is printed at the end")
    ap.add_argument("--record-manifest", metavar="DEVICE_ID")
    ap.add_argument("--merge", metavar="DIR")
    args = ap.parse_args()
    args.board_ports = dict(
        kv.split("=", 1) for kv in args.board_port if "=" in kv)

    if args.merge:
        merged = {"hosts": {}}
        failures = 0
        for fn in sorted(os.listdir(args.merge)):
            # skip the per-device files AND this tool's own output, or a
            # second merge folds the previous report in as a host
            if (fn.endswith(".json") and not fn.startswith("experiments-")
                    and fn != "merged.json"):
                with open(os.path.join(args.merge, fn)) as f:
                    host = json.load(f)
                # Keyed on the host the file RECORDS, not on its name: one
                # host may write several files (a release build for most
                # suites, a debug build for ble), and they belong in one
                # section. Older files named <host>.json merge the same
                # way.
                name = host.get("host") or fn[:-5]
                into = merged["hosts"].setdefault(
                    name, {"host": name, "devices": {}})
                for key, value in host.items():
                    if key in ("host", "devices"):
                        continue
                    if key == "languages":
                        into.setdefault("languages", {}).update(value or {})
                    elif key == "platforms":
                        into["platforms"] = sorted(
                            set(into.get("platforms") or []) | set(value or []))
                    else:
                        into[key] = value
                for dev_id, suites_ran in (host.get("devices") or {}).items():
                    target = into["devices"].setdefault(dev_id, {})
                    for suite, result in (suites_ran or {}).items():
                        if suite in target:
                            # Two files claiming the same suite on the same
                            # device: say so rather than silently keeping
                            # one, because which is current cannot be known
                            # from here.
                            print(f"!! {name}/{dev_id}: {suite} appears in "
                                  f"more than one report; keeping the later "
                                  f"file ({fn})")
                        target[suite] = result
                for dev in host.get("devices", {}).values():
                    if not dev:
                        failures += 1      # recorded nothing: not a pass
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
    # Boards belong in lab.yml with the rest of the host's hardware. They
    # were command-line only, which meant a release run had to remember a
    # serial port and a firmware path - exactly the kind of thing that is
    # got wrong at the end of a long day.
    for key, dest in (("boards", "board_ports"),
                      ("micropython_firmware", "micropython_firmware")):
        if host_cfg.get(key) and not getattr(args, dest):
            setattr(args, dest, host_cfg[key])
    if args.release and args.suites:
        # An explicit list wins: the flag exists to save typing the usual
        # set and to print what is still outstanding, not to overrule a
        # deliberate choice. Running the release build without ble - it
        # needs the instrumentation APK, which a store-signed build cannot
        # host - is exactly that choice.
        print(f"== release run on {args.host}: {args.suites} (as given)",
              flush=True)
    elif args.release:
        # Everything the host has the hardware for. ble only when a board
        # is actually configured, languages only when artifacts are named
        # (it skips itself otherwise) - a release run should not fail for
        # want of something this host was never meant to cover.
        # NOT `suites`: that name is the imported module, and shadowing it
        # here made the languages gate call a list.
        wanted_suites = ["sensors", "audio", "experiments"]
        if args.board_ports:
            wanted_suites.append("ble")
        args.suites = ",".join(wanted_suites)
        print(f"== release run on {args.host}: {args.suites}"
              + (" (+ languages)" if host_cfg.get("artifacts") else ""),
              flush=True)
        # A release run that quietly leaves out a whole suite is the thing
        # a release run must not do. Both of these are legitimate for a
        # host that was never meant to cover them - and both are far more
        # often a lab.yml that predates the entry.
        if not args.board_ports:
            print("   !! no boards for this host, so the ble suite is NOT "
                  "part of this run. Add them to lab.yml:\n"
                  "        boards:\n"
                  "          esp32: /dev/ttyUSB0\n"
                  "        micropython_firmware: /path/to/ESP32_GENERIC-<v>.bin\n"
                  "      (or pass --board-port, and see tools/lab/lab.yml.example)",
                  flush=True)
        elif not args.micropython_firmware:
            print("   !! a board is configured but no MicroPython firmware, so "
                  "the MicroPython scenarios will fail as soon as an Arduino "
                  "upload has overwritten it. Add micropython_firmware to "
                  "lab.yml.", flush=True)
        if not host_cfg.get("artifacts"):
            print("   !! no artifacts for this host, so the languages gate is "
                  "NOT part of this run - see lab.yml.example.", flush=True)
    if args.suites is None:
        args.suites = "sensors,audio,experiments"
    os.makedirs(args.out_dir, exist_ok=True)
    wanted = {d for d in args.devices.split(",") if d}

    global _TEE
    if _TEE is None:
        _TEE = _ThreadTee(sys.stdout)
        sys.stdout = _TEE

    # The phones and the boards are shared with whoever else is working in
    # this folder. See lab/bench.py for the afternoon that bought this.
    from lab import bench
    ok, msg = bench.acquire(f"lab/run.py --host {args.host}",
                            force=args.force_bench)
    print(f"   {msg}")
    if not ok:
        return 1

    srv = serve_fixtures(args.fixture_port)
    report = {"host": args.host, "devices": {}}
    baseline_rc = 0
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
        if args.record_ble_baseline:
            # Operator-assisted and interactive, so it is a mode of its
            # own rather than a suite: the reference release predates the
            # automation seam and cannot be driven.
            from lab import ble
            baseline_rc = ble.record_baselines(devices, args)
        elif args.record_manifest:
            for dev_id, entry, dev in devices:
                if args.record_manifest == dev_id:
                    record_manifest(dev, dev_id, args)
        else:
          for suite in args.suites.split(","):
            # The ble suite runs the loop the other way round - one flash,
            # then every phone in that scenario's scope - so it owns its
            # orchestration and only hands back the per-device results.
            if suite == "ble":
                from lab import ble
                try:
                    per_device = ble.run_suite(devices, args)
                except Exception as e:
                    # A crashed suite must still produce a report. The
                    # write happens at the end of this function, so an
                    # exception used to take the whole run's evidence with
                    # it: on 2026-08-28 a MacBook pass reached its eighth
                    # scenario, raised on a missing mpremote, and left
                    # nothing at all - not even the seven scenarios that
                    # had already run against the phone, which were the
                    # ones worth reading.
                    import traceback
                    traceback.print_exc()
                    per_device = {
                        dev_id: {"passed": False, "warnings": [],
                                 "findings": [f"the ble suite crashed: "
                                              f"{type(e).__name__}: {e}"]}
                        for dev_id, _entry, _dev in devices}
                for dev_id, r in per_device.items():
                    report["devices"][dev_id]["ble"] = r
                    state = verdict(r.get("passed"))
                    print(f"\n== ble @ {dev_id}: {state}"
                          + "".join(f"\n      ! {x}"
                                    for x in r.get("findings", []))
                          + "".join(f"\n      ~ {x}"
                                    for x in r.get("warnings", [])))
                continue
            # Devices are independent - own serial, own forwarded port,
            # own app instance - so a suite can run on all of them at
            # once, which is what matters for `experiments`: four devices
            # in sequence is a multi-hour run, in parallel it is one
            # device's worth. AUDIO IS THE EXCEPTION and is forced
            # serial: the phones share a room, so one device's tone would
            # land in another's microphone. --jobs 1 (the default) keeps
            # everything sequential; raise it deliberately, and mind that
            # N phones at once also draw N times the USB power.
            # audio shares a room, ble shares the radio and a flashing
            # cycle - both are serial whatever --jobs says
            jobs = 1 if suite in ("audio", "ble") else max(1, args.jobs)
            if jobs > 1:
                print(f"== {suite}: {len(devices)} device(s), "
                      f"{jobs} at a time")
            for dev_id, entry, r, captured in _run_suite(suite, devices,
                                                         args, jobs):
                if jobs > 1:
                    print(f"== {suite} @ {dev_id} ({entry['platform']})")
                if r is None:
                    continue
                report["devices"][dev_id][suite] = r
                state = verdict(r.get("passed"))
                print(f"\n   {state}"
                      + ("".join(f"\n      ! {x}" for x in r.get("findings", [])))
                      + ("".join(f"\n      ~ {x}" for x in r.get("warnings", []))))
                for line in captured:
                    print(f"      {line}")
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
                     else verdict(r["passed"]))
            print(f"\n   languages[{platform}]: {state}"
                  + ("".join(f"\n      ! {x}" for x in r.get("findings", [])))
                  + ("".join(f"\n      ~ {x}" for x in r.get("warnings", []))))
    finally:
        for _dev_id, _entry, dev in devices:
            dev.cleanup()
        srv.shutdown()
        bench.release()
    # The platforms this host actually drove, so a merged report can print
    # the T3 checklist for what was tested rather than for everything.
    report["platforms"] = sorted({e["platform"] for _i, e, _d in devices})

    if args.record_ble_baseline:
        # same reasoning as the manifest below: recording is not a run
        print("baselines recorded; no run report written")
        return baseline_rc
    if args.record_manifest:
        # recording a manifest is not a test run - writing a report full
        # of empty device entries only invites reading it as a green run
        print("manifest recorded; no run report written")
        return 0
    # The suites are in the NAME so that two runs of one host do not
    # overwrite each other - the release build cannot carry the ble suite
    # (it needs the instrumentation APK, which a store-signed build cannot
    # host), so running that suite separately against a debug build is a
    # normal thing to do rather than a special case. The merge keys on the
    # host recorded INSIDE the file, so the two land in one section.
    out = os.path.join(
        args.out_dir,
        f"{args.host}-{'+'.join(s for s in args.suites.split(',') if s)}.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=1)
    bad = sum(1 for d in report["devices"].values()
              for s in d.values() if s.get("passed") is False)
    bad += sum(1 for r in (report.get("languages") or {}).values()
               if r.get("passed") is False)
    # a device that recorded NO suite result is not a pass: an empty
    # report used to exit 0 and merge as green, which is the worst
    # possible failure mode for a run someone reads to decide whether to
    # ship (found 2026-08-27 in a report whose device entries were all
    # empty)
    empty = [d for d, suites in report["devices"].items() if not suites]
    if empty:
        print(f"\n!! no suite result recorded for: {', '.join(sorted(empty))}"
              f" - check --suites")
        bad += len(empty)
    print(f"\n{bad} failing suite(s) -> {out}")
    if args.release:
        # A release is not finished when this host is: the other host has
        # to run, the reports have to be merged, and the merge is what
        # prints the checklist a person still has to work through. Said
        # here because this is where somebody stops reading.
        others = [h for h in (cfg.get("hosts") or {}) if h != args.host]
        print("\nStill to do for this release:")
        if others:
            print(f"  - the same on {', '.join(sorted(others))}, writing "
                  f"into the same --out directory")
        print(f"  - python3 tools/lab/run.py --merge {args.out_dir}"
              f"   (merged.md carries the T3 checklist)")
        print("  - the T3 steps by hand, once per platform")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
