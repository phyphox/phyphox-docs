"""The BLE compatibility suite (T2, release-gated).

# phyphox-test: ble-compat-arduino
# phyphox-test: ble-compat-micropython

What is under test is the phyphox APP: a release must not break Arduino
or MicroPython projects that worked with the previous one. The library
examples are flashed unmodified as stimulus, and anything unusual about
what they emit is the compatibility surface, not a defect.

Shape of a run (fixtures/ble/scenarios.yml holds the data):

    for each scenario, for each board it names:
        flash the board with the example, unmodified
        leave the OTHER board advertising something with a different
        name, so the scan has to discriminate - a room with exactly one
        BLE device is not the room these run in
        for each phone in the scenario's scope:
            run the platform's little scan-and-connect test on the phone
            (the UI flow has no remote-API equivalent), then assert from
            the host: buffer values or range and cadence over the remote
            API, or the board's serial output where the direction is
            phone -> board

Serial throughout: flashing is the outer loop, and only one board may
advertise the experiment service at a time. That inverts the other
suites' loop, which is per device, and is why this one owns its own
orchestration (run_suite below) instead of going through run.py's
per-device dispatch: a flash takes a minute and must be amortised across
every phone in the scenario's scope, not repeated per phone.

Bring-up status (2026-08-27, Pixel 3 + ESP32-D0WDQ6 + Nano 33 BLE): the
flashing paths, the MicroPython reflash, the serial reader and the whole
host-side half are exercised and working. The phone-side connect step is
blocked on an Android bug - the collection's add-experiment sub-FABs are
drawn but never made visible, so nothing that reads the accessibility
tree can find them - and is verified only by driving it manually.
"""

import glob
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lab.device import api, sh, wait_api

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SCENARIOS = os.path.join(ROOT, "fixtures", "ble", "scenarios.yml")
BASELINES = os.path.join(ROOT, "fixtures", "ble", "baselines")


def load_scenarios():
    import yaml
    with open(SCENARIOS) as f:
        return yaml.safe_load(f)


def baseline_path(scenario):
    return os.path.join(BASELINES,
                        f"{scenario['library']}-{scenario['example']}.json")


def load_baseline(scenario):
    p = baseline_path(scenario)
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return json.load(f)


# ------------------------------------------------------------------ flashing

def flash(scenario, board, cfg, args):
    """Flash one example onto one board. Returns (ok, message)."""
    lib = cfg["libraries"][scenario["library"]]
    repo = os.path.normpath(os.path.join(ROOT, "..",
                                         os.path.basename(lib["repository"])))
    port = args.board_ports.get(board)
    if not port:
        return False, f"no serial port configured for board {board}"

    if scenario["library"] == "arduino":
        sketch = os.path.join(repo, lib["examples"], scenario["example"])
        if not os.path.isdir(sketch):
            return False, f"example not found: {sketch}"
        fqbn = lib["flash"]["fqbn"].get(board)
        if not fqbn:
            return False, f"no fqbn for board {board}"
        # Board configuration, never sketch edits: an example is stimulus
        # and is flashed as it is. See scenarios.yml for why each of these
        # exists.
        props = []
        for k, v in (scenario.get("build_properties") or {}).get(
                board, {}).items():
            props += ["--build-property", f"{k}={v}"]
        r = sh(["arduino-cli", "compile", "--fqbn", fqbn] + props + [sketch],
               timeout=600)
        if r.returncode != 0:
            return False, f"compile failed: {(r.stderr or r.stdout)[-300:]}"
        r = sh(["arduino-cli", "upload", "-p", port, "--fqbn", fqbn] + props
               + [sketch], timeout=300)
        if r.returncode != 0:
            return False, f"upload failed: {(r.stderr or r.stdout)[-300:]}"
        return True, "flashed"

    # MicroPython: the ESP32 is shared with the Arduino scenarios, whose
    # uploads overwrite the whole flash, so the firmware cannot be a
    # one-time manual step - the suite puts it back whenever the board is
    # not currently running MicroPython.
    ok, msg = ensure_micropython(board, port, args)
    if not ok:
        return False, msg
    src = os.path.join(repo, lib["examples"], scenario["example"] + ".py")
    if not os.path.exists(src):
        return False, f"example not found: {src}"
    # Relative source, run from the library checkout, because mpremote
    # recreates the SOURCE PATH on the board: an absolute one lands the
    # package at /home/.../phyphox-micropython/phyphoxBLE, where the
    # example's `import phyphoxBLE` cannot see it. The board then boots
    # into an ImportError and advertises nothing, which shows up as a
    # scan timeout on the phone and looks like a BLE problem.
    r = sh(["mpremote", "connect", port, "fs", "cp", "-r", "phyphoxBLE", ":"],
           timeout=300, cwd=repo)
    if r.returncode != 0:
        return False, f"copying the library failed: {(r.stderr or '')[-200:]}"
    r = sh(["mpremote", "connect", port, "fs", "cp", src, ":main.py"],
           timeout=120)
    if r.returncode != 0:
        return False, f"copying the example failed: {(r.stderr or '')[-200:]}"
    sh(["mpremote", "connect", port, "reset"], timeout=60)
    return True, "copied and reset"


def _esptool():
    """esptool ships as `esptool` (v5) or `esptool.py` (v4) - accept both."""
    import shutil
    for name in ("esptool", "esptool.py"):
        if shutil.which(name):
            return name
    return None


def running_micropython(port):
    """Ask the board rather than remembering: a probe survives a killed
    run, a reboot and a previous session, so the firmware is reflashed
    only when it actually has to be."""
    # short and unretried: mpremote does not fail fast against a board
    # running something else, it simply waits, so the first attempt IS
    # the answer (the default retry turned a 30 s probe into 60 s)
    r = sh(["mpremote", "connect", port, "eval", "1+1"], timeout=8,
           retries=0)
    return r.returncode == 0 and "2" in (r.stdout or "")


def ensure_micropython(board, port, args):
    """Flash the MicroPython firmware unless the board already runs it."""
    if running_micropython(port):
        return True, "already running MicroPython"
    firmware = args.micropython_firmware
    if not firmware:
        return False, ("the board is not running MicroPython and no "
                       "firmware was given - pass --micropython-firmware "
                       "<esp32 .bin> (the Arduino scenarios overwrite the "
                       "whole flash, so it has to be put back here)")
    if not os.path.exists(firmware):
        return False, f"MicroPython firmware not found: {firmware}"
    tool = _esptool()
    if tool is None:
        return False, "esptool is not installed"
    r = sh([tool, "--chip", "esp32", "--port", port, "erase_flash"],
           timeout=300)
    if r.returncode != 0:
        return False, f"erase_flash failed: {(r.stderr or r.stdout)[-200:]}"
    r = sh([tool, "--chip", "esp32", "--port", port, "--baud", "460800",
            "write_flash", "-z", "0x1000", firmware], timeout=600)
    if r.returncode != 0:
        return False, f"write_flash failed: {(r.stderr or r.stdout)[-200:]}"
    time.sleep(3)                      # let it boot before mpremote talks
    if not running_micropython(port):
        return False, "flashed the firmware but the board does not answer "\
                      "as MicroPython"
    return True, f"flashed {os.path.basename(firmware)}"


def order_scenarios(scenarios):
    """Arduino scenarios first, then MicroPython. Each transition between
    the two costs a full firmware flash on the shared ESP32, so the run
    crosses that line once instead of ten times."""
    return sorted(scenarios, key=lambda s: s["library"] != "arduino")


def pick_distractor(scenario, cfg, boards_available):
    """A scenario for the idle board whose advertised name DIFFERS from
    the one under test - the maintainer's point: the real world does not
    stop advertising other devices while we test one."""
    name = scenario.get("device_name")
    for other in cfg["scenarios"]:
        if other is scenario:
            continue
        if other.get("device_name") in (None, name):
            continue
        if not set(other["boards"]) & set(boards_available):
            continue
        return other
    return None


# ------------------------------------------------------- the phone-side step

def connect_phone(dev, scenario, args):
    """Run the platform's scan-and-connect test on the phone. The UI flow
    (scan, pick the device, accept its experiment) has no remote-API
    equivalent, so it lives as a small instrumented test in the app repo;
    everything after it is asserted from here."""
    name = scenario.get("device_name") or ""
    if dev.platform == "android":
        r = sh(dev.adb + ["shell", "am", "instrument", "-w",
                          "-e", "class",
                          "de.rwth_aachen.phyphox.BleCompatConnectTest",
                          "-e", "bleDevice", name,
                          "de.rwth_aachen.phyphox.test/"
                          "androidx.test.runner.AndroidJUnitRunner"],
               timeout=args.connect_timeout)
        ok = r.returncode == 0 and "FAILURES" not in (r.stdout or "")
        return ok, (r.stdout or r.stderr or "")[-300:]
    r = sh(["xcrun", "devicectl", "device", "process", "launch",
            "--terminate-existing", "--device", dev.udid, "--",
            "de.rwth-aachen.physics.phyphox",
            "-phyphoxBleConnect", name, "-phyphoxRemote",
            "-phyphoxRemotePort", "80", "-phyphoxAutoConfirm"],
           timeout=args.connect_timeout)
    return r.returncode == 0, (r.stderr or r.stdout or "")[-300:]


# -------------------------------------------------------------- assertions

def read_serial(port, seconds, baud=115200):
    """Whatever the board printed in a window - the assertion channel for
    the phone -> board direction, which has no phone-side evidence."""
    try:
        import serial
    except ImportError:
        return None, "pyserial is not installed"
    try:
        with serial.Serial(port, baud, timeout=0.5) as s:
            deadline = time.time() + seconds
            out = []
            while time.time() < deadline:
                line = s.readline()
                if line:
                    out.append(line.decode("utf-8", "replace").strip())
        return out, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def assert_scenario(dev, scenario, baseline, args, board_port):
    """Host-side assertions once the phone holds the experiment."""
    findings, det = [], {}
    kind = scenario["expect"]["kind"]

    if wait_api(dev.base, args.api_wait) is None:
        return ["the phone did not serve the remote API after connecting - "
                "is the remote-enable seam covering BLE-delivered "
                "experiments?"], det

    status, body = api(dev.base, "/config")
    try:
        config = json.loads(body)
    except Exception:
        return ["/config unparsable after connecting"], det
    buffers = [b["name"] for b in config.get("buffers", [])]
    det["buffers"] = buffers
    det["title"] = config.get("title")

    if kind == "board_serial":
        if scenario["expect"].get("trigger") == "start_stop":
            api(dev.base, "/control?cmd=start")
            time.sleep(2)
            api(dev.base, "/control?cmd=stop")
        else:
            api(dev.base, "/control?cmd=start")
        lines, err = read_serial(board_port, args.serial_window)
        api(dev.base, "/control?cmd=stop")
        if err:
            return [f"could not read the board's serial output: {err}"], det
        det["serial_lines"] = lines[-10:]
        wanted = scenario["expect"].get("contains_any") or []
        if wanted and not any(w in ln for ln in lines for w in wanted):
            findings.append(
                f"nothing matching {wanted} in the board's output - the "
                f"phone->board direction did not arrive")
        return findings, det

    # Clear first: `start` resumes rather than restarts, so whatever is
    # already in the buffers counts into the window - measured during
    # bring-up as a doubled rate when the same phone was measured twice.
    # Neither app auto-starts a BLE-delivered experiment (iOS confirmed
    # 2026-08-27: startExperiment has exactly two callers, the toolbar
    # button and cmd=start), so this is about repeat runs, not about a
    # phone that was already measuring. One request, and a rerun against
    # an already-loaded phone then means the same as a fresh one.
    api(dev.base, "/control?cmd=clear")
    api(dev.base, "/control?cmd=start")
    time.sleep(args.seconds)
    api(dev.base, "/control?cmd=stop")
    q = "&".join(b + "=full" for b in buffers)
    status, body = api(dev.base, "/get?" + q, timeout=30)
    if status != 200:
        return [f"/get after the run answered {status}"], det
    got = {n: [v for v in (b.get("buffer") or []) if v is not None]
           for n, b in json.loads(body).get("buffer", {}).items()}
    det["counts"] = {n: len(v) for n, v in got.items()}

    if kind == "range_rate":
        e = scenario["expect"]
        values = max(got.values(), key=len) if got else []
        if not values:
            return ["no data arrived from the board"], det
        out_of_range = [v for v in values if not e["min"] <= v <= e["max"]]
        if out_of_range:
            findings.append(f"{len(out_of_range)} value(s) outside "
                            f"[{e['min']}, {e['max']}], e.g. {out_of_range[0]}")
        rate = len(values) / args.seconds
        det["rate_hz"] = round(rate, 1)
        lo = e["rate_hz"] * (1 - e["rate_tolerance"])
        hi = e["rate_hz"] * (1 + e["rate_tolerance"])
        if not lo <= rate <= hi:
            findings.append(f"{rate:.1f} values/s, expected about "
                            f"{e['rate_hz']} (tolerance "
                            f"{e['rate_tolerance']:.0%})")
        return findings, det

    if kind == "connection":
        if not any(got.values()):
            findings.append("no data arrived with the sketch's connection "
                            "parameters")
        return findings, det

    # kind == exact
    if baseline is None:
        findings.append("no baseline recorded for this scenario - run with "
                        "--record-ble-baseline against the STORE RELEASE "
                        "first, so 'the previous version worked' is a "
                        "measured fact")
        return findings, det
    for name, expected in (baseline.get("buffers") or {}).items():
        actual = got.get(name)
        if actual is None:
            findings.append(f"buffer {name} is gone")
        elif actual[:len(expected)] != expected:
            findings.append(f"buffer {name} differs from the baseline: "
                            f"{actual[:3]} vs {expected[:3]}")
    if baseline.get("title") and det.get("title") != baseline["title"]:
        findings.append(f"experiment title is {det.get('title')!r}, the "
                        f"baseline recorded {baseline['title']!r}")
    return findings, det


# ------------------------------------------------------------ XML capture

CAPTURE_DIR = os.path.join(ROOT, "corpus", "valid", "ble-libraries")
MACISH = re.compile(r"\b[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}\b")


def capture_xml(dev, scenario):
    """Pull the experiment the board just served, for the T0 half.

    The libraries generate their XML on the microcontroller, so the only
    way to freeze it is to take it off a phone that received it. Android
    keeps the transfer at files/temp_bt/bt.phyphox and a debug build lets
    run-as read it; iOS has no equivalent that does not need a developer
    container dump - which does not matter, because the file comes from
    the BOARD. One platform capturing it is enough.

    Frozen under corpus/valid/ble-libraries/, so both app test suites
    parse it on every commit (T0) and a parser regression against
    library-generated XML is caught without hardware.
    """
    if dev.platform != "android":
        return None, "capture runs on Android only (the file is the board's)"
    r = sh(dev.adb + ["shell", "run-as", "de.rwth_aachen.phyphox",
                      "cat", "files/temp_bt/bt.phyphox"], timeout=30)
    if r.returncode != 0 or not (r.stdout or "").lstrip().startswith("<"):
        return None, ("no transferred experiment on the phone - "
                      f"{(r.stderr or r.stdout or '')[-120:]}")
    xml = r.stdout
    # The corpus is public. Nothing seen so far carries one - the
    # libraries identify their device by name - but a captured file is
    # not hand-written, so check rather than trust.
    if MACISH.search(xml):
        return None, ("the capture contains something MAC-shaped; sanitize "
                      "it by hand before it goes into the public corpus")
    os.makedirs(CAPTURE_DIR, exist_ok=True)
    path = os.path.join(
        CAPTURE_DIR, f"{scenario['library']}-{scenario['example']}.phyphox")
    old = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            old = f.read()
    if old == xml:
        return path, "unchanged"
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    return path, ("recorded" if old is None else
                  "CHANGED - review the diff before committing it")


# --------------------------------------------------------- orchestration

def _phones_for(scenario, devices):
    """`phones: all` is every device; `newest` is the newest per platform.

    Newest means the device marked `newest: true` in lab.yml, and failing
    that the first of its platform in the host's device list - which is
    how the lists happen to be written. The distinction exists because
    Android's BLE behaviour varies by version and manufacturer, so the
    four scenarios that exercise different parts of the implementation
    are worth every phone and the rest are not.
    """
    if scenario.get("phones") != "newest":
        return devices
    picked, seen = [], set()
    for dev_id, entry, dev in devices:
        if entry.get("newest"):
            picked.append((dev_id, entry, dev))
            seen.add(entry["platform"])
    for dev_id, entry, dev in devices:
        if entry["platform"] not in seen:
            picked.append((dev_id, entry, dev))
            seen.add(entry["platform"])
    return picked


def run_suite(devices, args):
    """Every scenario across every phone in its scope. Returns
    {device id: result} in the shape run.py reports."""
    cfg = load_scenarios()
    boards = dict(getattr(args, "board_ports", {}) or {})
    results = {dev_id: {"passed": True, "findings": [], "warnings": [],
                        "scenarios": {}}
               for dev_id, _entry, _dev in devices}
    if not boards:
        for r in results.values():
            r["passed"] = False
            r["findings"].append(
                "no --board-port given, so there is no board to talk to")
        return results

    scenarios = [s for s in order_scenarios(cfg["scenarios"])
                 if set(s["boards"]) & set(boards)]
    only = getattr(args, "ble_scenario", None)
    if only:
        # Bring-up and debugging: one scenario instead of an hour. A run
        # narrowed this way says so in every device's warnings, so a
        # report from one cannot be mistaken for a pass of the suite.
        scenarios = [s for s in scenarios
                     if only in (s["example"],
                                 f"{s['library']}/{s['example']}")]
        if not scenarios:
            for r in results.values():
                r["passed"] = False
                r["findings"].append(f"--ble-scenario {only!r} matches "
                                     f"nothing in scenarios.yml")
            return results
        for r in results.values():
            r["warnings"].append(
                f"narrowed to --ble-scenario {only!r}: this is not a pass "
                f"of the suite")
    skipped = [s["example"] for s in cfg["scenarios"]
               if not set(s["boards"]) & set(boards)]
    if skipped:
        # Never silently: a suite that covers less than the file says is
        # exactly what a green report must not hide.
        for r in results.values():
            r["warnings"].append(
                f"{len(skipped)} scenario(s) skipped, no board attached "
                f"for them: {', '.join(sorted(set(skipped)))}")

    flashed = {}                      # board -> the name it advertises now
    holds = {}                        # board -> (library, example) on it
    flashes = 0

    def put(sc, board, why):
        """Flash unless that board already holds exactly this example -
        it does happen, because a distractor is often the next scenario's
        target."""
        nonlocal flashes
        key = (sc["library"], sc["example"])
        if holds.get(board) == key:
            return True, "already on the board"
        print(f"   {why}: {sc['example']} -> {board}", flush=True)
        ok, msg = flash(sc, board, cfg, args)
        if ok:
            flashes += 1
            holds[board] = key
            flashed[board] = sc.get("device_name")
        return ok, msg

    for scenario in scenarios:
        for board in [b for b in scenario["boards"] if b in boards]:
            label = f"{scenario['library']}/{scenario['example']}@{board}"
            ok, msg = put(scenario, board, "flashing")
            if not ok:
                for r in results.values():
                    r["passed"] = False
                    r["findings"].append(f"{label}: {msg}")
                continue

            # The idle board keeps advertising under a DIFFERENT name, so
            # the scan has to discriminate. WHICH example it runs does not
            # matter - only that the name differs - so whatever it already
            # holds is kept unless it would collide with the target. Left
            # to "flash the scenario pick_distractor chose", the two boards
            # swap roles every scenario and the run spends 22 flashes on
            # 10 scenarios; a flash is about a minute, so this is most of
            # an hour.
            idle = [b for b in boards if b != board]
            target_name = scenario.get("device_name")
            for other in idle:
                if flashed.get(other) and flashed[other] != target_name:
                    continue
                distractor = pick_distractor(scenario, cfg, [other])
                if not distractor:
                    continue
                dok, dmsg = put(distractor, other, "distractor")
                if not dok:
                    for r in results.values():
                        r["warnings"].append(
                            f"{label}: the distractor board could not "
                            f"be flashed ({dmsg}) - the scan ran "
                            f"against fewer devices than intended")
            if not any(flashed.get(b) not in (None, target_name)
                       for b in idle):
                # Worth saying out loud: the scan then had nothing to
                # discriminate against, so a pass proves less than it looks.
                for r in results.values():
                    r["warnings"].append(
                        f"{label}: no second board advertising a name "
                        f"differing from {target_name!r}, so the scan ran "
                        f"without a distractor")

            baseline = load_baseline(scenario)
            for dev_id, entry, dev in _phones_for(scenario, devices):
                print(f"   {dev_id}: connecting to "
                      f"{scenario.get('device_name')!r}", flush=True)
                ok, msg = connect_phone(dev, scenario, args)
                entry_key = f"{scenario['library']}/{scenario['example']}"
                if board != scenario["boards"][0]:
                    entry_key += f"@{board}"
                if not ok:
                    results[dev_id]["passed"] = False
                    results[dev_id]["findings"].append(
                        f"{entry_key}: the phone did not connect - {msg}")
                    results[dev_id]["scenarios"][entry_key] = {
                        "connected": False}
                    continue
                findings, det = assert_scenario(dev, scenario, baseline,
                                                args, boards[board])
                if getattr(args, "capture_ble_xml", False):
                    path, note = capture_xml(dev, scenario)
                    det["capture"] = (os.path.relpath(path, ROOT) + ": " + note
                                      if path else note)
                results[dev_id]["scenarios"][entry_key] = det
                if findings:
                    results[dev_id]["passed"] = False
                    results[dev_id]["findings"] += [f"{entry_key}: {f}"
                                                    for f in findings]
    print(f"-- ble: {flashes} flash(es) for {len(scenarios)} scenario(s)",
          flush=True)
    for r in results.values():
        r["flashes"] = flashes
    return results


# --------------------------------------------------------- baselines

def record_baselines(devices, args):
    """Record what each board produces on the app version being used as
    the reference - normally the CURRENT STORE RELEASE, so that "the
    previous version worked" is measured rather than assumed.

    This one is operator-assisted on purpose, because the released app
    cannot be driven the way a development build can:

      * the automation seam is newer than the release (v1.2.0 has no
        debug.phyphox.remote), so remote access has to be switched on by
        hand - it is an ordinary user-facing feature, two taps in the
        menu;
      * an instrumentation test must be signed with the same key as the
        app under test, and a Play-signed build cannot host ours, so the
        scan-and-connect step cannot run either;
      * on iOS the same holds - -phyphoxBleConnect does not exist in the
        released binary.

    So the tool flashes, waits for a human to connect the phone and turn
    remote access on, and then does the measuring and the writing itself.
    Ten scenarios is ten pauses; this happens once per reference release,
    not per run.
    """
    import datetime
    cfg = load_scenarios()
    boards = dict(getattr(args, "board_ports", {}) or {})
    if not boards:
        print("!! no --board-port given, so there is no board to record from")
        return 1
    if len(devices) != 1:
        print("!! record one phone at a time: pass --devices <id> naming the "
              "phone that runs the reference release")
        return 1
    dev_id, _entry, dev = devices[0]

    scenarios = [s for s in order_scenarios(cfg["scenarios"])
                 if set(s["boards"]) & set(boards)]
    only = getattr(args, "ble_scenario", None)
    if only:
        scenarios = [s for s in scenarios
                     if only in (s["example"],
                                 f"{s['library']}/{s['example']}")]
    if not scenarios:
        print("!! nothing to record")
        return 1

    os.makedirs(BASELINES, exist_ok=True)
    written, failed = [], []
    for scenario in scenarios:
        board = next(b for b in scenario["boards"] if b in boards)
        name = scenario.get("device_name")
        label = f"{scenario['library']}/{scenario['example']}"
        print(f"\n== {label} on {board}", flush=True)
        ok, msg = flash(scenario, board, cfg, args)
        if not ok:
            print(f"   !! {msg}")
            failed.append(f"{label}: {msg}")
            continue
        print(f"   On {dev_id}, by hand:\n"
              f"     1. add an experiment for a Bluetooth device and pick "
              f"{name!r}\n"
              f"     2. let it load, then switch remote access on from the "
              f"menu\n"
              f"   Enter to record, or 's' to skip this scenario: ", end="",
              flush=True)
        try:
            if (input().strip().lower() or "") == "s":
                failed.append(f"{label}: skipped by the operator")
                continue
        except EOFError:
            print("\n!! not an interactive terminal - this mode needs one")
            return 1

        if wait_api(dev.base, args.api_wait) is None:
            print("   !! the phone is not serving the remote API - is remote "
                  "access on, and on this network?")
            failed.append(f"{label}: no remote API")
            continue
        meta = {}
        status, body = api(dev.base, "/meta")
        if status == 200:
            try:
                meta = json.loads(body)
            except Exception:
                pass
        status, body = api(dev.base, "/config")
        config = json.loads(body) if status == 200 else {}
        buffers = [b["name"] for b in config.get("buffers", [])]
        api(dev.base, "/control?cmd=clear")
        api(dev.base, "/control?cmd=start")
        time.sleep(args.seconds)
        api(dev.base, "/control?cmd=stop")
        q = "&".join(b + "=full" for b in buffers)
        status, body = api(dev.base, "/get?" + q, timeout=30)
        if status != 200:
            print(f"   !! /get answered {status}")
            failed.append(f"{label}: /get {status}")
            continue
        got = {n: [v for v in (b.get("buffer") or []) if v is not None]
               for n, b in json.loads(body).get("buffer", {}).items()}
        baseline = {
            "recorded": datetime.date.today().isoformat(),
            "device": dev_id,
            "app": {"version": meta.get("version"),
                    "build": meta.get("build"),
                    "fileFormat": meta.get("fileFormat")},
            "seconds": args.seconds,
            "title": config.get("title"),
            "buffer_names": buffers,
            "counts": {n: len(v) for n, v in got.items()},
            # Only the head of each buffer: a baseline is a fingerprint of
            # what the board produces, not a recording of a measurement,
            # and a full run would put thousands of random numbers into a
            # reviewed file.
            "buffers": {n: v[:20] for n, v in got.items() if v},
        }
        path = baseline_path(scenario)
        with open(path, "w") as f:
            json.dump(baseline, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"   recorded {os.path.relpath(path, ROOT)} "
              f"(app {baseline['app']['version']}, "
              f"{sum(baseline['counts'].values())} values)")
        written.append(label)

    print(f"\n{len(written)} baseline(s) written"
          + (f", {len(failed)} not: " + "; ".join(failed) if failed else ""))
    return 1 if failed else 0
