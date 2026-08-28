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
        if a second board is attached, leave it advertising something
        with a different name, so the scan has to discriminate - a room
        with exactly one BLE device is not the room these run in
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

Status (2026-08-28, ESP32-D0WDQ6): the whole chain runs unattended on
Android - flash, transfer, load, hold, measure, release - and all ten
scenarios have been measured on the Pixel 3. Baselines are recorded
against 1.2.0.

The two old phones run it too since the Android session fixed the connect
test below API 28, but the first three-phone pass was NOT green: eight
scenarios failed at connect across the Nexus 5X and the Galaxy A3 (and
one on the Pixel 3), and the one case whose log survived was the 90 s
experiment-transfer timeout the README describes. Whether that is the
old stacks, the single board serving three centrals in turn, or the app
is unknown - the reporting that would have said was only fixed
afterwards. Do not read a green Pixel 3 as a green suite.

The bench is one board as of that date: the Nano 33 BLE stopped accepting
uploads from anything and was retired, and the maintainer scoped this
suite to the ESP32 rather than replacing it (scenarios.yml says why).
Per-board machinery below is kept deliberately - the library-side test
that will cover many boards on one phone is the natural home for it - but
nothing here currently exercises two boards, so the scan runs without a
distractor and each run says so.

The iOS half has never touched hardware. Its connect path
(-phyphoxBleConnect) is implemented in the app and unit-tested there, but
the branch below that drives it was written blind, exactly as the Android
branch was before its bring-up found four defects in this file. Expect
the same. Note also that this suite cannot be split across hosts: the
boards travel to whichever machine drives the phones (tools/lab/README).
"""

import glob
import json
import os
import re
import shlex
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
        for attempt in (1, 2):
            live = resolve_arduino_port(fqbn, port)
            # No props here: `upload` does not take --build-property and
            # answers a usage dump if given one. It uploads what `compile`
            # just built, so the properties are already baked in.
            r = sh(["arduino-cli", "upload", "-p", live, "--fqbn", fqbn,
                    sketch], timeout=300)
            if r.returncode == 0:
                return True, ("flashed" if live == port
                              else f"flashed (on {live}, not {port})")
            # One retry. Two failures to beat: a board caught
            # mid-re-enumeration (absent for a second, then back), and a
            # Nano stuck in an unreachable bootloader, which on this bench
            # only a re-plug clears. Try the software version of the
            # re-plug before giving up - it touches this device alone, so
            # a board sharing the hub is not disturbed.
            if attempt == 1:
                time.sleep(5)
                rok, rmsg = usb_reset(live)
                print(f"   {'reset and retrying' if rok else 'no reset'}: "
                      f"{rmsg}", flush=True)
        out = (r.stderr or r.stdout) or ""
        if "No device found" in out:
            # Same tool error, two opposite causes, and the difference is
            # visible in the USB product id: 0x805a is the sketch running,
            # 0x005a is the bootloader. Telling a maintainer to double-tap
            # a board that is ALREADY in its bootloader wastes their time
            # and is exactly what this message did once.
            if _usb_pid(live) == "005a":
                return False, (
                    f"{board} is in its bootloader (usb 2341:005a) and "
                    f"bossac cannot reach it on {live}. UNPLUG IT AND PLUG "
                    f"IT BACK IN - measured 2026-08-27/28, that is the only "
                    f"thing that recovers it: a flash or two works after a "
                    f"replug and then one leaves it here again. Reset "
                    f"presses do not help, waiting does not, and neither "
                    f"does a USB reset - it is the marginal USB path, so "
                    f"try another cable or a root port first")
            return False, (f"{board} did not enter its bootloader: the port "
                           f"({live}) is there but the 1200 bps touch got no "
                           f"answer, so the sketch on it is not servicing "
                           f"USB. Unplug and replug the board; a double-tap "
                           f"on reset frees the sketch but has not been "
                           f"enough on its own")
        return False, f"upload failed: {out[-300:]}"

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


def advertisers(name, timeout=10.0):
    """Addresses currently advertising exactly `name`, or None if this
    host cannot scan.

    The suite picks a board BY NAME, so two boards answering to one name
    makes every result meaningless - the phone may take either, and a
    scenario that fails proves nothing about the app. It is not a
    hypothetical: five of the seven Arduino examples advertise the
    library default, and on 2026-08-27 a stale sketch left "phyphox
    device" on both bench boards for an afternoon while the suite
    measured a ~45% failure rate that was never the app's.
    """
    try:
        import asyncio
        from bleak import BleakScanner
    except ImportError:
        return None
    try:
        found = asyncio.run(BleakScanner.discover(timeout=timeout))
    except Exception:
        return None
    return [d.address for d in found if (d.name or "") == name]


def usb_reset(port):
    """Re-enumerate the board behind a serial port, without touching
    anything else on the bus. Returns (ok, message).

    Written for the bench Nano 33 BLE (retired 2026-08-28), which took
    about one upload per physical re-plug, and there is no software
    equivalent of pulling the cable:
    USBDEVFS_RESET makes the kernel reset and re-probe that ONE device -
    the hub, and the ESP32 sharing it, are untouched - but it does not
    remove VBUS, so the board's own chip is not power-cycled. Whether
    that is enough is an empirical question; when it is not, the message
    still asks for the cable.

    Needs write access to the device node, which is root's by default:

        SUBSYSTEM=="usb", ATTRS{idVendor}=="2341", MODE="0664", GROUP="plugdev"
    """
    import fcntl
    node = _usb_node(port)
    if node is None:
        return False, f"no USB device node found behind {port}"
    try:
        fd = os.open(node, os.O_WRONLY)
    except PermissionError:
        return False, (f"{node} is not writable, so the board cannot be reset "
                       f"from here - see usb_reset() for the one-line udev "
                       f"rule that grants it")
    except OSError as e:
        return False, f"{node}: {e}"
    try:
        fcntl.ioctl(fd, ord("U") << 8 | 20, 0)     # USBDEVFS_RESET
    except OSError as e:
        return False, f"reset ioctl on {node} failed: {e}"
    finally:
        os.close(fd)
    time.sleep(3)                                  # let it come back
    return True, f"reset {node}"


def _usb_node(port):
    """/dev/bus/usb/BBB/DDD for the device behind a tty, via sysfs."""
    name = os.path.basename(port)
    try:
        link = os.path.realpath(f"/sys/class/tty/{name}/device")
    except OSError:
        return None
    # .../usb3/3-2/3-2.2/3-2.2.2/3-2.2.2:1.0/tty/ttyACM0 - walk up to the
    # first directory that carries busnum/devnum, which is the device
    # itself rather than one of its interfaces.
    while link and link != "/":
        bus = os.path.join(link, "busnum")
        dev = os.path.join(link, "devnum")
        if os.path.exists(bus) and os.path.exists(dev):
            try:
                with open(bus) as f:
                    b = int(f.read().strip())
                with open(dev) as f:
                    d = int(f.read().strip())
            except (OSError, ValueError):
                return None
            return f"/dev/bus/usb/{b:03d}/{d:03d}"
        link = os.path.dirname(link)
    return None


def _usb_pid(port):
    """The USB product id behind a serial port, lowercase and unprefixed,
    or None. It is what distinguishes an Arduino running its sketch from
    the same board sitting in its bootloader."""
    r = sh(["arduino-cli", "board", "list", "--format", "json"], timeout=60)
    if r.returncode != 0:
        return None
    try:
        doc = json.loads(r.stdout or "{}")
    except ValueError:
        return None
    for entry in doc.get("detected_ports") or []:
        p = entry.get("port") or {}
        if p.get("address") == port:
            pid = ((p.get("properties") or {}).get("pid") or "")
            return pid.lower().replace("0x", "") or None
    return None


def resolve_arduino_port(fqbn, configured):
    """Where that board actually is right now, not where lab.yml said.

    An Arduino board re-enumerates on every upload (1200 bps touch into
    the bootloader and back), and it does not reliably come back on the
    node it left: a full pass on 2026-08-27 failed EVERY distractor flash
    with
    "No device found on ttyACM1" while the board sat there working, and
    it was on ttyACM1 again by the time the run ended. So ask arduino-cli,
    which identifies boards by USB id and reports the FQBN per port, and
    fall back to what was configured when it cannot say (the ESP32's
    CP2102 is a generic bridge and matches no board).
    """
    r = sh(["arduino-cli", "board", "list", "--format", "json"], timeout=60)
    if r.returncode != 0:
        return configured
    try:
        doc = json.loads(r.stdout or "{}")
    except ValueError:
        return configured
    base = fqbn.split(":")[:3]
    for entry in doc.get("detected_ports") or []:
        for board in entry.get("matching_boards") or []:
            if (board.get("fqbn") or "").split(":")[:3] == base:
                return (entry.get("port") or {}).get("address") or configured
    return configured


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

RELEASE_PROP = "debug.phyphox.labRelease"
# What BleCompatConnectTest logs once it is parked and the phone is the
# host's to drive. Matching on the app's own line rather than on a
# timeout is what makes the handover exact.
HOLD_TAG = "phyphoxBleCompat"
HOLD_LINE = "holding the app open"


def _await_hold(dev, timeout):
    """True once the connect test says it is holding the app for us."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        r = sh(dev.adb + ["logcat", "-d", "-s", HOLD_TAG], timeout=30)
        if HOLD_LINE in (r.stdout or ""):
            return True
        time.sleep(1)
    return False
ANDROID_PACKAGE = "de.rwth_aachen.phyphox"
# Where Android leaves the experiment a device just sent it.
TRANSFER_FILE = "files/temp_bt/bt.phyphox"


def connect_phone(dev, scenario, args):
    """Run the platform's scan-and-connect test on the phone. The UI flow
    (scan, pick the device, accept its experiment) has no remote-API
    equivalent, so it lives as a small instrumented test in the app repo;
    everything after it is asserted from here.

    On Android the test has to be left RUNNING while the host measures.
    Instrumentation is hosted in the app's own process, so the app dies
    the moment `am instrument` returns - measured on the Pixel 3: the
    remote API answered 200 at 33 s and was gone at 36 s, three seconds
    later, with the process. So the run is started in the background and
    released afterwards through debug.phyphox.labRelease, which the test
    polls (see release_phone). iOS needs none of this: -phyphoxBleConnect
    is the app launching itself, and it stays up on its own.

    Returns (ok, message, handle) - the handle is passed back to
    release_phone, and is None where there is nothing to release.
    """
    name = scenario.get("device_name") or ""
    if dev.platform == "android":
        # Start from nothing on the phone. Both of these were learned from
        # one bad full pass: a previous scenario's app instance survived a
        # killed instrumentation and kept answering the API, so every
        # later scenario "connected" to a phone still holding the wrong
        # experiment - and the leftover transfer file was captured four
        # times under four different names.
        sh(dev.adb + ["shell", "am", "force-stop", ANDROID_PACKAGE])
        sh(dev.adb + ["shell", "run-as", ANDROID_PACKAGE,
                      "rm", "-f", TRANSFER_FILE])
        sh(dev.adb + ["shell", "setprop", RELEASE_PROP, "0"])
        # Cleared so the hold line found below is THIS run's, not the
        # previous scenario's.
        sh(dev.adb + ["logcat", "-c"])
        proc = subprocess.Popen(
            dev.adb + ["shell", "am", "instrument", "-w",
                       "-e", "class",
                       "de.rwth_aachen.phyphox.BleCompatConnectTest",
                       # Quoted: adb joins argv into ONE shell command, so
                       # a name with a space ("phyphox device", "My
                       # Device") becomes two arguments and am instrument
                       # answers with a usage dump instead of running.
                       "-e", "bleDevice", shlex.quote(name),
                       "-e", "holdForHost", "true",
                       "de.rwth_aachen.phyphox.test/"
                       "androidx.test.runner.AndroidJUnitRunner"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        # Wait for the test to say it is HOLDING, not merely for the API.
        # The remote server comes up the moment the experiment loads,
        # which is while the test is still asserting - and one of those
        # assertions is that nothing is measuring, so a host that starts
        # at the API fails the test it is waiting on. The Android session
        # hit this three runs out of four (2026-08-27) before either of
        # us worked out it was the host doing it.
        if not _await_hold(dev, args.connect_timeout):
            proc.kill()
            sh(dev.adb + ["shell", "am", "force-stop", ANDROID_PACKAGE])
            out = proc.communicate()[0] or ""
            if "ClassNotFoundException" in out:
                # Not a launch failure, however much it looks like one:
                # the app never starts because the instrumentation cannot
                # find the test class. The phone simply has an older
                # androidTest APK - the app APK and the test APK are
                # installed separately and a device that missed the last
                # `installRegularDebugAndroidTest` fails exactly here.
                return False, (
                    f"the androidTest APK on this device is stale - it has "
                    f"no BleCompatConnectTest. Install it: ANDROID_SERIAL="
                    f"{getattr(dev, 'serial', '<serial>')} ./gradlew "
                    f"installRegularDebug installRegularDebugAndroidTest"
                ), None
            # The FIRST exception WITH THE LINES UNDER IT, not the last
            # 300 characters and not one line: an instrumentation failure
            # prints the cause at the top and JUnit's summary at the
            # bottom, so a tail shows the summary; and JUnit's own header
            # is "Error in <test>:" with the throwable on the NEXT line,
            # so one line is just that header. The three-phone run on
            # 2026-08-28 reported eight failures as "Error in
            # theDeviceOffersItsExperimentAndItLoads(...):" and nothing
            # else, which is why the whole output is now kept as well.
            lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
            at = next((i for i, ln in enumerate(lines)
                       if "Exception" in ln or "Error" in ln), None)
            first = " | ".join(lines[at:at + 3])[:400] if at is not None else ""
            try:
                log = evidence_path(
                    dev, args,
                    f"{scenario['library']}-{scenario['example']}"
                    f"-connect-failed.txt")
                with open(log, "w") as f:
                    f.write(out)
                first += f" [full output: {os.path.relpath(log, ROOT)}]"
            except OSError:
                pass
            return False, ("the connect test never reached its hold: "
                           + (first or out[-300:])), None
        if wait_api(dev.base, args.connect_timeout) is None:
            proc.kill()
            # Killing the local adb does NOT stop the instrumentation on
            # the phone; without this it keeps the app alive and the next
            # scenario talks to it.
            sh(dev.adb + ["shell", "am", "force-stop", ANDROID_PACKAGE])
            out = (proc.communicate()[0] or "")[-300:]
            return False, ("the phone did not reach a loaded experiment "
                           "within the connect timeout: " + out), None
        return True, "connected", proc
    r = sh(["xcrun", "devicectl", "device", "process", "launch",
            "--terminate-existing", "--device", dev.udid, "--",
            "de.rwth-aachen.physics.phyphox",
            "-phyphoxBleConnect", name, "-phyphoxRemote",
            "-phyphoxRemotePort", "80", "-phyphoxAutoConfirm"],
           timeout=args.connect_timeout)
    return r.returncode == 0, (r.stderr or r.stdout or "")[-300:], None


def release_phone(dev, handle, args):
    """Let the held instrumentation run finish, and report what it said.

    The test's assertions - that the experiment parsed, that it was left
    unstarted - are only reported when it returns, so this is where an
    Android connect actually passes or fails. A test that hangs past the
    timeout is killed rather than left holding the phone.
    """
    if handle is None:
        return True, ""
    sh(dev.adb + ["shell", "setprop", RELEASE_PROP, "1"])
    try:
        out = handle.communicate(timeout=args.connect_timeout)[0] or ""
    except subprocess.TimeoutExpired:
        handle.kill()
        out = handle.communicate()[0] or ""
        return False, ("the connect test did not finish after being "
                       "released - is it polling " + RELEASE_PROP + "? "
                       + out[-200:])
    finally:
        sh(dev.adb + ["shell", "setprop", RELEASE_PROP, "0"])
    ok = handle.returncode == 0 and "FAILURES" not in out
    return ok, out[-300:]


# -------------------------------------------------------------- assertions

def read_serial(port, seconds, baud=115200, until=None, trigger=None):
    """Whatever the board printed in a window - the assertion channel for
    the phone -> board direction, which has no phone-side evidence.

    `until` is checked as lines come in and ends the read early, so the
    window can be generous enough to cover a slow link (see
    await_live_link) without every scenario paying for it.

    `trigger` is run once the port is OPEN, and that ordering is the whole
    point: the event-driven sketches print their burst the instant the
    experiment starts or stops, so a reader opened afterwards catches the
    tail of one line and concludes the board said nothing. Opening first
    means whatever the board says during the trigger is already in the
    buffer.
    """
    try:
        import serial
    except ImportError:
        return None, "pyserial is not installed"
    try:
        with serial.Serial(port, baud, timeout=0.5) as s:
            if trigger is not None:
                trigger()
            deadline = time.time() + seconds
            out = []
            while time.time() < deadline:
                line = s.readline()
                if line:
                    out.append(line.decode("utf-8", "replace").strip())
                    if until and until(out):
                        break
        return out, None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _screenshot(dev, scenario, args, board=None):
    """Keep the screen when a start produced nothing.

    The phone usually knows exactly what went wrong and says so in a
    dialog - "The Bluetooth device is not connected. Experiment can not
    be started." - while /control?cmd=start still answers {"result":
    true}, so the host's own view is only ever "no data". A picture
    settles in one look what the logs took an afternoon to not settle,
    and it does not depend on matching a translated string.
    """
    if dev.platform != "android":
        return None
    try:
        path = evidence_path(dev, args,
                             f"{scenario['library']}-{scenario['example']}"
                             + (f"-{board}" if board else "") + "-nodata.png")
        with open(path, "wb") as f:
            r = subprocess.run(dev.adb + ["exec-out", "screencap", "-p"],
                               stdout=f, timeout=30)
        return path if r.returncode == 0 and os.path.getsize(path) else None
    except (OSError, subprocess.SubprocessError):
        return None


def evidence_path(dev, args, name):
    """lab-results/evidence/<phone>-<name>, created on demand.

    The phone belongs in the name: three phones run the same scenario
    against the same board, and without it the last one to fail
    overwrites the evidence of the first - which is what the file
    lab-results/evidence/ held after the 2026-08-28 three-phone run.
    """
    out = os.path.join(getattr(args, "out_dir", "lab-results"), "evidence")
    os.makedirs(out, exist_ok=True)
    who = re.sub(r"[^A-Za-z0-9_.-]", "_",
                 getattr(dev, "serial", None) or getattr(dev, "udid", "phone"))
    return os.path.join(out, f"{who}-{name}")


def _start_for_real(dev, args, tries=8, gap=1.0):
    """Start the experiment and confirm it actually started.

    `/control?cmd=start` answers {"result": true} for a start the app
    refused - it is documented as "whether the command was accepted" -
    so the answer that matters is status.measuring in the next /get.
    """
    for attempt in range(tries):
        api(dev.base, "/control?cmd=start")
        status, body = api(dev.base, "/get?", timeout=20)
        if status == 200:
            try:
                if json.loads(body).get("status", {}).get("measuring"):
                    if attempt:
                        print(f"   the start took {attempt + 1} attempt(s) - "
                              f"the app refuses one until every bluetooth "
                              f"block of the experiment is connected",
                              flush=True)
                    return True
            except ValueError:
                pass
        time.sleep(gap)
    return False


def await_live_link(dev, buffers, args):
    """Start the experiment and wait until the board's data arrives.
    Returns (live, seconds waited).

    Two things have to be waited for, and only one of them used to be.

    A start issued the moment /config answers is REFUSED, and answers
    {"result": true} while refusing. The remote server comes up when the
    experiment loads, but every Arduino and MicroPython configuration
    describes its board with two <bluetooth> blocks, and the app connects
    them sequentially on a background thread: the second is up about
    1.6 s later (+1.61, +1.67, +1.69, +1.61 measured by the Android
    session on 2026-08-27), and startAllIO refuses a start until it is.
    Starting immediately failed 11 of 12 cycles; starting 2 s later
    delivered 12/12, 6/6 and 4/4. My earlier "45% of starts fail" report
    was this, jittering across the window edge because the host's polling
    is not synchronised to it.

    So the start is confirmed rather than assumed: /get carries
    status.measuring, which is false after a refused start and true after
    an accepted one, and the start is repeated until it takes. That is a
    handshake against a documented field rather than a sleep tuned to one
    phone.

    The second wait is the board's first value, which is worth keeping
    separately: how long a link takes to deliver is exactly where BLE
    stacks differ, so it is recorded per phone.
    """
    q = "&".join(b + "=full" for b in buffers)
    started = time.time()
    if not _start_for_real(dev, args):
        return False, round(time.time() - started, 1)
    while time.time() - started < args.link_timeout:
        status, body = api(dev.base, "/get?" + q, timeout=20)
        if status == 200:
            try:
                data = json.loads(body).get("buffer", {})
            except ValueError:
                data = {}
            if any(v is not None for b in data.values()
                   for v in (b.get("buffer") or [])):
                return True, round(time.time() - started, 1)
        time.sleep(1)
    return False, round(time.time() - started, 1)


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
        wanted = scenario["expect"].get("contains_any") or []
        trigger = scenario["expect"].get("trigger")
        # Confirmed starts here too: a refused one answers {"result":
        # true} and measures nothing, which reads as a silent board.
        def fire():
            if trigger == "start_stop":
                det["started"] = _start_for_real(dev, args)
                time.sleep(2)
                api(dev.base, "/control?cmd=stop")
            elif isinstance(trigger, dict) and "set" in trigger:
                det["started"] = _start_for_real(dev, args)
                spec = trigger["set"]
                api(dev.base, f"/control?cmd=set&buffer={spec['buffer']}"
                              f"&value={spec['value']}")
                det["triggered"] = f"{spec['buffer']}={spec['value']}"
            else:
                det["started"] = _start_for_real(dev, args)

        # Generous window, ended as soon as the board says what we are
        # waiting for: the link is not live the moment the API answers
        # (see await_live_link), and here there are no buffers to watch
        # for that - the evidence IS the board's output.
        lines, err = read_serial(
            board_port, args.serial_window + args.link_timeout,
            until=(lambda ls: any(w in "\n".join(ls) for w in wanted))
            if wanted else None,
            trigger=fire)
        api(dev.base, "/control?cmd=stop")
        if det.get("started") is False:
            return ["the app refused to start the experiment - "
                    "status.measuring stayed false"], det
        if err:
            return [f"could not read the board's serial output: {err}"], det
        det["serial_lines"] = lines[-10:]
        # Matched against the joined output, not line by line: a
        # readline() that starts mid-line splits "New Interval:  300.0"
        # into "New Inter" + "val:  300.0" and a per-line match then fails
        # against a board that said exactly the right thing.
        joined = "\n".join(lines)
        if wanted and not any(w in joined for w in wanted):
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
    live, waited = await_live_link(dev, buffers, args)
    det["time_to_data_s"] = waited
    if not live:
        shot = _screenshot(dev, scenario, args,
                           getattr(args, "_board", None))
        if shot:
            det["evidence"] = shot
        return [f"no data arrived from the board within {args.link_timeout:.0f}"
                f" s of starting"
                + (f" - screen at that moment: {shot}" if shot else "")], det
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

    # kind == structure: what the reference release produced, in every
    # respect that a rerun can legitimately reproduce.
    #
    # NOT the values. Every scenario in this class emits a stimulus that
    # cannot repeat: CreateExperiment writes random(0,100) and its square,
    # multigraph writes millis()-derived sine and cosine, MicroPython's
    # createExperiment writes random numbers too. Comparing recorded
    # values against a rerun would fail every time and mean nothing when
    # it passed. What a release must preserve, and what a rerun can hold
    # it to, is the shape: the same experiment title, the same buffers,
    # and data still arriving in the same ones.
    if baseline is None:
        findings.append("no baseline recorded for this scenario - run with "
                        "--record-ble-baseline against the reference release "
                        "first, so 'the previous version worked' is a "
                        "measured fact")
        return findings, det
    if baseline.get("title") and det.get("title") != baseline["title"]:
        findings.append(f"experiment title is {det.get('title')!r}, the "
                        f"baseline recorded {baseline['title']!r}")
    was, now = set(baseline.get("buffer_names") or []), set(buffers)
    if was and was != now:
        gone, new = sorted(was - now), sorted(now - was)
        findings.append(
            "the experiment's buffers changed since the baseline"
            + (f" - gone: {', '.join(gone)}" if gone else "")
            + (f" - new: {', '.join(new)}" if new else ""))
    for name, count in (baseline.get("counts") or {}).items():
        if count and not got.get(name):
            findings.append(f"buffer {name} carried {count} value(s) on the "
                            f"reference release and none now")
    det["baseline"] = {"app": (baseline.get("app") or {}).get("version"),
                       "recorded": baseline.get("recorded")}
    return findings, det


# ------------------------------------------------------------ XML capture

CAPTURE_DIR = os.path.join(ROOT, "corpus", "valid", "ble-libraries")
# Where a capture waits when it cannot go straight into corpus/valid.
CAPTURE_STAGING = os.path.join(ROOT, "fixtures", "ble", "captured")
MACISH = re.compile(r"\b[0-9A-Fa-f]{2}(:[0-9A-Fa-f]{2}){5}\b")


def spec_findings(path):
    """What tools/validate_experiments.py says about one file.

    corpus/valid means "validates cleanly AND both apps load it", and a
    capture cannot be assumed to do the first: the libraries emit
    `facor="1"` for `factor` on every <value> element (Arduino
    src/view_elements/value.cpp:58, MicroPython phyphoxBLE/
    experiment.py:575 - the same typo, copied). The apps ignore unknown
    attributes and load it fine, so that belongs in corpus/invalid with
    `parser: accepts`, which is a classification decision and therefore
    the maintainer's. A flagged capture is staged instead of filed, and
    the run says so - dropping it into corpus/valid would break the docs
    build on the next commit.
    """
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    try:
        import validate_experiments as ve
    except ImportError as e:
        return [f"could not run the spec check: {e}"]
    import xml.etree.ElementTree as ET
    spec, common, slots, components = ve.load_spec()
    rep = ve.Report()
    name = os.path.basename(path)
    root = ve.normalize_namespace(ET.parse(path).getroot())
    for child in root:
        ve.check_element(child, "phyphox", spec, common, slots, components,
                         rep, "", name)
    for attr, value in root.attrib.items():
        if spec.get((None, "phyphox"), {"attrs": {}})["attrs"].get(attr) is None:
            rep.add("unknown attribute", name, f'<phyphox>: {attr}="{value}"')
    ve.check_slots(root, slots, components, rep, name)
    ve.check_root_once(root, rep, name)
    return [f"{kind}: {where}"
            for kind, entries in rep.items.items()
            for _fn, where in entries][:5]


def capture_xml(dev, scenario, board=None):
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
    r = sh(dev.adb + ["shell", "run-as", ANDROID_PACKAGE,
                      "cat", TRANSFER_FILE], timeout=30)
    if r.returncode != 0 or not (r.stdout or "").lstrip().startswith("<"):
        return None, ("no transferred experiment on the phone - "
                      f"{(r.stderr or r.stdout or '')[-120:]}")
    xml = r.stdout
    # Prove it came from THIS board. connect_phone deletes the file first,
    # so a leftover should be impossible - but a bad full pass on
    # 2026-08-27 wrote one stale file into the corpus under four different
    # scenario names, and a fixture that silently describes the wrong
    # device is worse than no fixture.
    wanted = scenario.get("device_name")
    m = re.search(r'<bluetooth\b[^>]*\bname="([^"]*)"', xml)
    if wanted and m and m.group(1) != wanted:
        return None, (f"the transferred experiment names {m.group(1)!r}, not "
                      f"{wanted!r} - this is not that board's file")
    # The corpus is public. Nothing seen so far carries one - the
    # libraries identify their device by name - but a captured file is
    # not hand-written, so check rather than trust.
    if MACISH.search(xml):
        return None, ("the capture contains something MAC-shaped; sanitize "
                      "it by hand before it goes into the public corpus")
    stem = (f"{scenario['library']}-{scenario['example']}"
            + (f"-{board}" if board and board != scenario["boards"][0] else "")
            + ".phyphox")
    # Write first, then judge: the spec check needs a file, and where the
    # file belongs depends on what it says.
    os.makedirs(CAPTURE_STAGING, exist_ok=True)
    staged = os.path.join(CAPTURE_STAGING, stem)
    with open(staged, "w", encoding="utf-8") as f:
        f.write(xml)
    findings = spec_findings(staged)
    if findings:
        return staged, ("staged, NOT filed - the spec check flags it ("
                        + "; ".join(findings) + "). If the apps load it "
                        "anyway it belongs in corpus/invalid with "
                        "`parser: accepts`, which is a call to make by "
                        "hand")

    os.makedirs(CAPTURE_DIR, exist_ok=True)
    path = os.path.join(CAPTURE_DIR, stem)
    old = None
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            old = f.read()
    os.remove(staged)
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

    if len(boards) < 2:
        # A standing property of the bench, not a per-scenario incident,
        # so it is said once rather than ten times: with one board there
        # is nothing else in the air, and a scan that finds the only
        # device in the room has not been asked to discriminate. The
        # suite is scoped to one board on purpose (scenarios.yml says
        # why) - this is what keeps that in front of whoever reads a
        # green report, instead of only in a file nobody rereads.
        for r in results.values():
            r["warnings"].append(
                "one board on the bench, so every scan ran without a "
                "distractor: nothing else was advertising, and picking "
                "the right device out of one device proves less than it "
                "looks")

    off = [s for s in cfg["scenarios"] if s.get("disabled")]
    if off:
        # A disabled scenario is coverage the suite does not have, and a
        # green report must say so - the same reason a missing board is
        # reported below. Deleting the block would have hidden it; the
        # key is one line to remove when the reason is gone.
        for r in results.values():
            r["warnings"].append(
                "disabled in scenarios.yml, so this pass did not cover "
                + "; ".join(f"{d['library']}/{d['example']} "
                            f"({d['disabled']})" for d in off))

    scenarios = [s for s in order_scenarios(cfg["scenarios"])
                 if not s.get("disabled") and set(s["boards"]) & set(boards)]
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
               if not s.get("disabled")
               and not set(s["boards"]) & set(boards)]
    if skipped:
        # Never silently: a suite that covers less than the file says is
        # exactly what a green report must not hide.
        for r in results.values():
            r["warnings"].append(
                f"{len(skipped)} scenario(s) skipped, no board attached "
                f"for them: {', '.join(sorted(set(skipped)))}")

    flashed = {}                      # board -> the name it advertises now
    holds = {}                        # board -> (library, example) on it
    failures = {}                     # board -> consecutive flash failures
    dead_boards = {}                  # board -> why it was given up on
    flashes = 0

    def put(sc, board, why):
        """Flash unless that board already holds exactly this example -
        it does happen, because a distractor is often the next scenario's
        target."""
        nonlocal flashes
        key = (sc["library"], sc["example"])
        if holds.get(board) == key:
            return True, "already on the board"
        # A board that cannot be flashed twice will not be flashable the
        # eight other times this pass asks either: a wedged board needs a
        # finger on its reset button, or its cable pulled. Give up on it
        # once, with one message, instead of spending 35 s per attempt
        # rediscovering it.
        if board in dead_boards:
            return False, dead_boards[board]
        print(f"   {why}: {sc['example']} -> {board}", flush=True)
        ok, msg = flash(sc, board, cfg, args)
        if ok:
            flashes += 1
            holds[board] = key
            flashed[board] = sc.get("device_name")
            failures.pop(board, None)     # consecutive, not cumulative
        else:
            failures[board] = failures.get(board, 0) + 1
            if failures[board] >= 2:
                dead_boards[board] = (
                    f"{board} is out of this run after {failures[board]} "
                    f"failed flashes: {msg}")
                print(f"   !! {dead_boards[board]}", flush=True)
        return ok, msg

    from lab import bench
    for scenario in scenarios:
        # Checked per scenario, because losing the bench mid-run does not
        # announce itself: the phone simply starts behaving oddly - props
        # cleared, forwards removed, the connect test killed - and the
        # results read as an intermittent BLE fault. Ask, and stop.
        if not bench.owns():
            for r in results.values():
                r["passed"] = False
                r["findings"].append(
                    "the bench lock was taken over mid-run, so everything "
                    "measured from here would be of a phone someone else "
                    "is using - stopping. Nothing above this point is "
                    "necessarily trustworthy either")
            return results
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
            if idle and not any(flashed.get(b) not in (None, target_name)
                                for b in idle):
                # Only when a second board IS attached and could not be
                # put to work: that is an incident and belongs to the
                # scenario. A one-board bench is reported once, above.
                for r in results.values():
                    r["warnings"].append(
                        f"{label}: no second board advertising a name "
                        f"differing from {target_name!r}, so the scan ran "
                        f"without a distractor")

            # Prove the name identifies ONE board before any phone is
            # asked to pick by it. A duplicate here invalidates the
            # scenario outright rather than producing a plausible-looking
            # failure, so it fails loudly and does not measure.
            seen = advertisers(target_name)
            if seen is None:
                for r in results.values():
                    r["warnings"].append(
                        f"{label}: could not check for duplicate advertisers "
                        f"(no bleak on this host), so a same-named board "
                        f"would go unnoticed")
            elif len(seen) > 1:
                for r in results.values():
                    r["passed"] = False
                    r["findings"].append(
                        f"{label}: {len(seen)} boards advertise "
                        f"{target_name!r} ({', '.join(seen)}) - the phone "
                        f"picks by name, so nothing measured here would mean "
                        f"anything. Reflash or unpower the other one")
                continue
            elif not seen:
                for r in results.values():
                    r["warnings"].append(
                        f"{label}: this host's scan saw nothing advertising "
                        f"{target_name!r} just before the phone was asked to "
                        f"find it")

            baseline = load_baseline(scenario)
            for dev_id, entry, dev in _phones_for(scenario, devices):
                print(f"   {dev_id}: connecting to "
                      f"{scenario.get('device_name')!r}", flush=True)
                ok, msg, handle = connect_phone(dev, scenario, args)
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
                try:
                    args._board = board
                    findings, det = assert_scenario(dev, scenario, baseline,
                                                    args, boards[board])
                    if getattr(args, "capture_ble_xml", False):
                        path, note = capture_xml(dev, scenario, board)
                        det["capture"] = (os.path.relpath(path, ROOT)
                                          + ": " + note if path else note)
                finally:
                    # Always release, including on an exception: a held
                    # test owns the phone until it is let go.
                    rok, rmsg = release_phone(dev, handle, args)
                if not rok:
                    findings.append(f"the connect test reported: {rmsg}")
                results[dev_id]["scenarios"][entry_key] = det
                # A scenario that only passed after a restart is a pass
                # with something to say; it goes in the report where the
                # per-phone pattern is visible, which is what makes a BLE
                # race worth reporting at all.
                results[dev_id]["warnings"] += [f"{entry_key}: {w}"
                                                for w in det.get("warnings", [])]
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

    The wait is for the REMOTE API, not for a keypress: switching remote
    access on is the operator's last step and is precisely what makes the
    phone answer, so the tool needs no terminal of its own and the
    operator needs no second action to say "done".
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

    if len(boards) < 2:
        # A standing property of the bench, not a per-scenario incident,
        # so it is said once rather than ten times: with one board there
        # is nothing else in the air, and a scan that finds the only
        # device in the room has not been asked to discriminate. The
        # suite is scoped to one board on purpose (scenarios.yml says
        # why) - this is what keeps that in front of whoever reads a
        # green report, instead of only in a file nobody rereads.
        for r in results.values():
            r["warnings"].append(
                "one board on the bench, so every scan ran without a "
                "distractor: nothing else was advertising, and picking "
                "the right device out of one device proves less than it "
                "looks")

    scenarios = [s for s in order_scenarios(cfg["scenarios"])
                 if not s.get("disabled") and set(s["boards"]) & set(boards)]
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
        # The operator's own actions ARE the signal, so nothing is read
        # from stdin: switching remote access on is the last step, and it
        # is exactly what makes the API answer. Waiting for that instead
        # of for a keypress means this runs the same way whether a person
        # is at a terminal or driving it from somewhere else.
        print(f"   On {dev_id}, by hand:\n"
              f"     1. add an experiment for a Bluetooth device and pick "
              f"{name!r}\n"
              f"     2. let it load, then switch remote access on from the "
              f"menu\n"
              f"   waiting up to {args.record_wait:.0f} s for the phone to "
              f"start serving...", flush=True)

        if wait_api(dev.base, args.record_wait) is None:
            print("   !! nothing served within the wait - skipping this one. "
                  "Remote access not switched on, a different network, or "
                  "the experiment did not load")
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
