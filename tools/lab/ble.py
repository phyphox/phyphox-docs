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
advertise the experiment service at a time.

UNVERIFIED: written without boards attached. Every path that touches
arduino-cli, mpremote or a serial port is untested until the first real
run; report what needed fixing rather than working around it.
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
        r = sh(["arduino-cli", "compile", "--fqbn", fqbn, sketch], timeout=600)
        if r.returncode != 0:
            return False, f"compile failed: {(r.stderr or r.stdout)[-300:]}"
        r = sh(["arduino-cli", "upload", "-p", port, "--fqbn", fqbn, sketch],
               timeout=300)
        if r.returncode != 0:
            return False, f"upload failed: {(r.stderr or r.stdout)[-300:]}"
        return True, "flashed"

    # MicroPython: the firmware is flashed once by hand; the run copies the
    # library and the example over with mpremote and soft-resets.
    src = os.path.join(repo, lib["examples"], scenario["example"] + ".py")
    if not os.path.exists(src):
        return False, f"example not found: {src}"
    pkg = os.path.join(repo, "phyphoxBLE")
    r = sh(["mpremote", "connect", port, "fs", "cp", "-r", pkg, ":"],
           timeout=300)
    if r.returncode != 0:
        return False, f"copying the library failed: {(r.stderr or '')[-200:]}"
    r = sh(["mpremote", "connect", port, "fs", "cp", src, ":main.py"],
           timeout=120)
    if r.returncode != 0:
        return False, f"copying the example failed: {(r.stderr or '')[-200:]}"
    sh(["mpremote", "connect", port, "reset"], timeout=60)
    return True, "copied and reset"


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
