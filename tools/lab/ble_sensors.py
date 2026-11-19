"""The ble-sensors suite: the shipped Bluetooth experiments for our own
sensors, phyphox:m and phyphox:mini, run end to end on every lab phone.

# phyphox-test: ble-shipped-sensors

The board bench (ble.py) checks that the app still talks to devices
other people program; the experiments suite opens every shipped
experiment but stops Bluetooth ones at the scan dialog. Between the two,
nothing ran the experiments the app ships for the sensors we sell. This
does: each experiment in fixtures/ble/sensors.yml is opened from the
app's own collection (phyphox://asset=), the app connects to the first
device its own <bluetooth> filter matches, and the host starts it over
the remote API, measures, and checks what the views would show.

The one thing an unattended run cannot do is pick the device in the
scan dialog. The bleAutoConnect switch does it - debug.phyphox.bleAutoConnect
on Android, -phyphoxBleAutoConnect on iOS - by treating every
<bluetooth> block as autoConnect="true", which both apps already
implement. ANY matching unit is taken, on purpose (maintainer
2026-11-19): the units are swapped and renamed in workshops, and every
phyphox:m is a valid subject. Both switches are release-safe, so this
suite runs against the release candidate, not the debug build the board
bench needs.

Per device and serial, like the board bench: the phones share one radio
neighbourhood, and a sensor serves one phone at a time - the app is
stopped after every experiment so the next one finds it advertising
again.

Verdicts follow the sensors suite (maintainer 2026-11-19): no connection,
no data, or data that stopped arriving FAILS; a value outside its
plausibility window only WARNS.
"""

import glob
import json
import math
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lab.device import api, wait_api   # noqa: E402

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
FIXTURE = os.path.join(ROOT, "fixtures", "ble", "sensors.yml")
# The collection the fixture is checked against. The phone runs its own
# bundled copy; this is only for the drift check and the device filters,
# so the Android checkout serves for both platforms (the bluetooth/
# folders are identical in both submodules - say so if they ever differ).
COLLECTION = os.path.normpath(os.path.join(
    ROOT, "..", "phyphox-android", "app", "src", "main", "assets", "experiments"))

DEFAULT_SECONDS = 16


# The other shipped collection checkout. The two submodules can point at
# different commits, so the docs build checks each one it finds.
IOS_COLLECTION = os.path.normpath(os.path.join(
    ROOT, "..", "phyphox-ios", "phyphox-experiments"))

# Names our sensors advertise, in the shapes seen on the bench: bare, with
# a unit number, and with the trailing newline the mini sends. Used only to
# ask "would this shipped experiment take one of ours?".
OUR_NAMES = ["phyphox:m", "phyphox:m 131", "phyphox:mini", "phyphox:mini A48\n"]


def load_fixture(full=False):
    with open(FIXTURE, encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    return doc if full else doc["experiments"]


def ours(path):
    """Whether a shipped experiment is one for our own sensors: its
    <bluetooth> filter would take a phyphox:m or phyphox:mini, or its file
    is named like one (a filter by service UUID alone would not show in
    the name test)."""
    if os.path.basename(path).startswith("phyphox_m"):
        return True
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return False
    for bt in root.iter("bluetooth"):
        name, regex = bt.get("name"), bt.get("nameRegex")
        if (name or regex) and any(matches(n, name, regex) for n in OUR_NAMES):
            return True
    return False


def coverage_findings(collection=COLLECTION):
    """Every shipped experiment for our sensors must be in the fixture,
    either run (`experiments`) or deliberately left out (`excluded`, with a
    reason) - and nothing may be listed that is no longer shipped. The
    fixture is a hand-written list, and a hand-written list goes stale
    silently: a new experiment would simply never be tested, and two
    files merged into one would fail as "not in the collection" only at
    the next release run. Run by the suite AND by the docs build, so a
    collection change is noticed when the submodule is bumped, not on
    release day."""
    doc = load_fixture(full=True)
    listed = {e["file"] for e in doc.get("experiments") or []}
    excluded = {e["file"] for e in doc.get("excluded") or []}
    out = []
    for e in doc.get("excluded") or []:
        if not (e.get("reason") or "").strip():
            out.append(f"{e['file']}: excluded without a reason")
    for f in sorted(listed & excluded):
        out.append(f"{f}: both run and excluded")
    if not os.path.isdir(collection):
        return out
    shipped = set()
    for path in sorted(glob.glob(os.path.join(collection, "**", "*.phyphox"),
                                 recursive=True)):
        rel = os.path.relpath(path, collection).replace(os.sep, "/")
        if ours(path):
            shipped.add(rel)
    for f in sorted(shipped - listed - excluded):
        out.append(f"{f}: shipped for phyphox:m/mini but not in "
                   f"fixtures/ble/sensors.yml - add it to `experiments`, or "
                   f"to `excluded` with the reason")
    for f in sorted((listed | excluded) - shipped):
        out.append(f"{f}: in fixtures/ble/sensors.yml but no longer shipped "
                   f"(removed, renamed or merged) - update the fixture")
    return out


def _filters(path):
    """The device-matching criteria of an experiment's first <bluetooth>
    block that carries any - (name, nameRegex) - the same test the app
    applies, so the host scan can say whether anything it would take is
    on the air."""
    root = ET.parse(path).getroot()
    for bt in root.iter("bluetooth"):
        name, regex = bt.get("name"), bt.get("nameRegex")
        if name or regex:
            return name, regex
    return None, None


def matches(advertised, name, regex):
    """docs/file-format: name is a substring test, nameRegex must match
    the whole name (surrounding whitespace stripped), both must hold when
    both are given."""
    if not advertised:
        return False
    adv = advertised.strip()
    if name and name not in adv:
        return False
    if regex:
        try:
            if not re.fullmatch(regex, adv):
                return False
        except re.error:
            return False
    return bool(name or regex)


def fixture_findings(experiments, collection=COLLECTION):
    """Every buffer the fixture names must be a container of the shipped
    file, and the file must exist. An experiment reworked in the
    collection otherwise turns into "no data in temperature" on every
    phone, which reads as an app or sensor fault and is this file."""
    out = []
    for e in experiments:
        path = os.path.join(collection, e["file"])
        if not os.path.exists(path):
            out.append(f"{e['file']}: not in the collection any more - "
                       f"update fixtures/ble/sensors.yml")
            continue
        root = ET.parse(path).getroot()
        have = {(c.text or "").strip() for c in root.iter("container")}
        named = list(e.get("time") or []) + list(e.get("values") or [])
        for c in e.get("checks") or []:
            for kind, spec in c.items():
                head = spec[0]
                named += head if isinstance(head, list) else [head]
        missing = sorted({b for b in named if b not in have})
        if missing:
            out.append(f"{e['file']}: no buffer {', '.join(missing)} in the "
                       f"shipped file - update fixtures/ble/sensors.yml")
    return out


_UNSCANNED = object()
_SCAN = _UNSCANNED


def host_scan(seconds=12.0):
    """Advertised names seen from the host's own adapter, or None when the
    host cannot scan (no bleak, no adapter, no Bluetooth permission for the
    terminal on macOS). Once per run: a sensor that is off is off for every
    phone, and finding out per experiment would cost a connect timeout
    each - 17 of them per phone."""
    global _SCAN
    if _SCAN is not _UNSCANNED:
        return _SCAN
    try:
        import asyncio
        from bleak import BleakScanner

        async def scan():
            found = await BleakScanner.discover(timeout=seconds,
                                                return_adv=True)
            return {adv.local_name or d.name
                    for d, adv in found.values() if adv.local_name or d.name}
        _SCAN = asyncio.run(scan())
    except Exception as e:
        print(f"   ~ host scan not possible ({type(e).__name__}: {e}); "
              f"every experiment will try to connect", flush=True)
        _SCAN = None
    return _SCAN


def _get(base, names):
    q = "&".join(f"{n}=full" for n in names)
    status, body = api(base, "/get?" + q, timeout=20)
    if status != 200:
        return None
    try:
        return {n: list(b.get("buffer") or [])
                for n, b in json.loads(body).get("buffer", {}).items()}
    except Exception:
        return None


def _finite(vs):
    return [v for v in vs if isinstance(v, (int, float)) and math.isfinite(v)]


def _start_when_connected(base, timeout, first_delay=8.0, interval=4.0):
    """Both apps refuse to start an experiment whose <bluetooth> blocks
    have not connected, and answer {"result": false} until they have. So
    asking repeatedly is the connect wait here - unlike the board bench,
    where the device is found by the test and the start is asked once.
    Returns the seconds it took, or None.

    Not too eagerly, though: every refused start is also shown to the
    user. On Android it is a dialog ("no connection to the Bluetooth
    device, the experiment cannot be started ... retry"), which stays on
    screen over the measurement that then starts fine - harmless to the
    data, but on the first smoke run (Pixel 9 Pro, 2026-11-19) it was all
    the operator could see and read as a failed connection.

    Why the connect is slow: stop_app force-stops the previous app, which
    drops the link without a disconnect, so the sensor only notices after
    its link supervision timeout (about 4 s) and only then advertises
    again. Measured on the second smoke run: the connect came 4-7 s after
    the API answered, every one of 14 experiments. So the first ask waits
    first_delay (--sensor-start-delay, 8 s) and a normal connect raises no
    dialog at all. A slower one still may - stop_app clears it afterwards."""
    t0 = time.time()
    time.sleep(first_delay)
    while time.time() - t0 < timeout:
        status, body = api(base, "/control?cmd=start", timeout=5)
        try:
            started = status == 200 and json.loads(body).get("result") is True
        except (ValueError, TypeError, AttributeError):
            started = False
        if started:
            return time.time() - t0
        time.sleep(interval)
    return None

def check_values(e, bufs):
    """(findings, warnings, details) for one experiment's final read."""
    findings, warnings, det = [], [], {}
    for b in e.get("values") or []:
        if not _finite(bufs.get(b) or []):
            findings.append(f"no data in {b}")
    if findings:
        return findings, warnings, det

    def mean(vs):
        vs = _finite(vs)
        return sum(vs) / len(vs) if vs else float("nan")

    for c in e.get("checks") or []:
        if "range" in c:
            b, lo, hi = c["range"]
            m = mean(bufs.get(b) or [])
            det[f"mean_{b}"] = round(m, 3)
            if not lo <= m <= hi:
                warnings.append(f"{b} mean {m:.4g} outside {lo}..{hi} "
                                f"(bench, not failed)")
        elif "magnitude" in c:
            axes, lo, hi = c["magnitude"]
            cols = [_finite(bufs.get(a) or []) for a in axes]
            n = min(len(v) for v in cols)
            if n:
                m = sum(math.sqrt(sum(col[i] ** 2 for col in cols))
                        for i in range(n)) / n
                det["mean_magnitude_" + axes[0]] = round(m, 3)
                if not lo <= m <= hi:
                    warnings.append(f"|{','.join(axes)}| mean {m:.4g} outside "
                                    f"{lo}..{hi} (bench, not failed)")
        elif "near0" in c:
            axes, tol = c["near0"]
            for a in axes:
                m = mean(bufs.get(a) or [])
                if not abs(m) <= tol:
                    warnings.append(f"{a} mean {m:.4g} not within ±{tol} at "
                                    f"rest (bench, not failed)")
    return findings, warnings, det


def run_one(dev, e, args):
    """One experiment on one phone: (findings, warnings, details)."""
    det = {}
    seconds = e.get("seconds", DEFAULT_SECONDS)
    if not dev.launch(e["file"], ble_auto_connect=True):
        return [f"launch failed: {getattr(dev, 'last_error', '')}".strip()], [], det
    try:
        if wait_api(dev.base, args.api_wait) is None:
            return ["remote API not reachable"], [], det
        took = _start_when_connected(dev.base, args.sensor_connect_timeout,
                                     first_delay=getattr(args, "sensor_start_delay", 8.0))
        if took is None:
            seen = ("a matching sensor was on the air (host scan), so the "
                    "app did not take it" if _SCAN not in (None, _UNSCANNED)
                    else "the host could not scan, so the sensor may simply "
                    "be off")
            return [f"never connected and started within "
                    f"{args.sensor_connect_timeout:.0f} s - {seen}. Does this "
                    f"build carry the bleAutoConnect switch?"], [], det
        det["connect_s"] = round(took, 1)
        time_bufs = list(e.get("time") or [])
        names = time_bufs + [b for b in (e.get("values") or [])
                             if b not in time_bufs]
        for c in e.get("checks") or []:
            for spec in c.values():
                head = spec[0]
                names += [b for b in (head if isinstance(head, list) else [head])
                          if b not in names]
        time.sleep(seconds / 2)
        mid = _get(dev.base, time_bufs) or {}
        time.sleep(seconds / 2)
        bufs = _get(dev.base, names)
        api(dev.base, "/control?cmd=stop")
        if bufs is None:
            return ["/get failed after the measurement"], [], det
        findings = []
        for tb in time_bufs:
            end = _finite(bufs.get(tb) or [])
            half = _finite(mid.get(tb) or [])
            if not end:
                findings.append(f"no data in {tb}")
            elif half and not end[-1] > half[-1]:
                findings.append(f"{tb} stopped moving after the first half "
                                f"({half[-1]:.3f} -> {end[-1]:.3f}): data "
                                f"stopped arriving")
            elif not half:
                findings.append(f"{tb} was still empty after {seconds / 2:.0f} s")
        first = _finite(bufs.get(time_bufs[0]) or []) if time_bufs else []
        if len(first) > 4 and first[-1] > first[0]:
            rate = (len(first) - 1) / (first[-1] - first[0])
            det["achieved_rate"] = round(rate, 2)
            det["samples"] = len(first)
            if e.get("rate"):
                expect, tol = e["rate"]["expect"], e["rate"].get("tol", 0.3)
                if abs(rate - expect) > expect * tol:
                    findings.append(f"rate {rate:.4g} Hz vs expected {expect} "
                                    f"(tol {tol:.0%})")
        f2, warnings, d2 = check_values(e, bufs)
        det.update(d2)
        return findings + f2, warnings, det
    finally:
        # The sensor serves one phone at a time: release it for the next
        # experiment and the next phone (see IOSDevice.stop_app).
        dev.stop_app()


def run_suite(dev, platform, args):
    """Every fixture experiment for this platform and this bench, on one
    phone. Returns the {passed, findings, warnings, details} every suite
    returns."""
    experiments = load_fixture()
    findings, warnings, details = [], [], {}
    bench = set(getattr(args, "ble_sensors", None) or [])
    drift = coverage_findings() + fixture_findings(experiments)
    if drift:
        # The fixture no longer describes the collection: every result
        # below would be about the wrong buffers.
        return {"passed": False, "findings": drift, "warnings": [],
                "details": {}}
    seen = host_scan()
    for e in experiments:
        key = os.path.basename(e["file"])[:-len(".phyphox")]
        if e.get("platforms") and platform not in e["platforms"]:
            continue
        if bench and e["device"] not in bench:
            warnings.append(f"{key}: skipped, no {e['device']} on this bench "
                            f"(ble_sensors in lab.yml)")
            continue
        if seen is not None:
            name, regex = _filters(os.path.join(COLLECTION, e["file"]))
            if not any(matches(n, name, regex) for n in seen):
                findings.append(
                    f"{key}: nothing matching its filter "
                    f"({'name ' + repr(name) if name else ''}"
                    f"{' ' if name and regex else ''}"
                    f"{'nameRegex ' + repr(regex) if regex else ''}) "
                    f"advertised near the host - is the {e['device']} "
                    f"switched on and charged?")
                continue
        print(f"   {key}", flush=True)
        f, w, d = run_one(dev, e, args)
        details[key] = d
        # One line per experiment as it finishes: a ten-minute suite whose
        # verdicts only appear at the end cannot be watched.
        rate = (f", {d['achieved_rate']:g} Hz" if "achieved_rate" in d else "")
        print(f"      {'FAIL' if f else 'ok'}{rate}"
              + (f" (connected after {d['connect_s']:g} s)"
                 if "connect_s" in d else "")
              + "".join(f"\n        ! {x}" for x in f)
              + "".join(f"\n        ~ {x}" for x in w), flush=True)
        findings += [f"{key}: {x}" for x in f]
        warnings += [f"{key}: {x}" for x in w]
    return {"passed": not findings, "findings": findings,
            "warnings": warnings, "details": details}
