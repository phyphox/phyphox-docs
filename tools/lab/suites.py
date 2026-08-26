"""The T2 suites the lab driver runs per device.

Each suite returns a JSON-able dict {passed, findings, details}. Suites
carry their test-matrix tags here (the checker scans this repo's tools/
for T2 rows - one driver serves both platforms):

# phyphox-test: device-sensors
# phyphox-test: device-audio
# phyphox-test: device-experiments
# phyphox-test: device-languages
"""

import json
import math
import os
import re
import subprocess
import sys
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lab.device import api, wait_api

ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", ".."))
TOOLS = os.path.join(ROOT, "tools")

# canonical plausibility windows per sensor kind (area H of the test plan)
PLAUSIBLE = {
    "magnitude9.81": (9.31, 10.31),   # |accel| at rest
    "near0": (-0.1, 0.1),             # gyro at rest (per axis window)
    "earthfield": (15.0, 75.0),       # |B| in uT
    "pressure": (300.0, 1100.0),      # hPa
    "positive": (1e-9, float("inf")),
}


def _get_buffers(base, names):
    q = "&".join(f"{n}=full" for n in names)
    status, body = api(base, "/get?" + q, timeout=20)
    if status != 200:
        return None
    try:
        return {n: [v for v in (b.get("buffer") or [])]
                for n, b in json.loads(body).get("buffer", {}).items()}
    except Exception:
        return None


def _finite(vs):
    return [v for v in vs if isinstance(v, (int, float))
            and math.isfinite(v)]


def run_sensor_suite(dev, manifest, args):
    """Per manifest sensor: launch its experiment, run, check liveness,
    plausibility and achieved rate. A sensor the manifest excludes is
    skipped; the app's graceful sensor-missing path is covered by the
    experiments suite loading everything.

    Liveness and rate FAIL; the value-plausibility windows only WARN
    (maintainer, 2026-08-26): a lab phone routinely sits on a screw or
    holds a stale magnetometer calibration, and no plausible phyphox bug
    changes sensor values while keeping the rate right - so a window
    violation is bench information, not a red suite."""
    findings, warnings, details = [], [], {}
    for name, spec in (manifest.get("sensors") or {}).items():
        det = {"sensor": name}
        details[name] = det
        if not dev.launch(spec["experiment"]):
            findings.append(f"{name}: launch failed")
            continue
        if wait_api(dev.base, args.api_wait) is None:
            findings.append(f"{name}: remote API not reachable")
            continue
        api(dev.base, "/control?cmd=start")
        time.sleep(spec.get("seconds", 8))
        api(dev.base, "/control?cmd=stop")
        bufs = _get_buffers(dev.base, spec["value_buffers"]
                            + ([spec["time_buffer"]] if spec.get("time_buffer") else []))
        if bufs is None:
            findings.append(f"{name}: /get failed")
            continue
        values = [_finite(bufs.get(b) or []) for b in spec["value_buffers"]]
        if any(not v for v in values):
            findings.append(f"{name}: no data in "
                            + ",".join(b for b, v in zip(spec["value_buffers"], values) if not v))
            continue
        det["samples"] = len(values[0])
        kind = spec.get("plausibility")
        if kind == "magnitude9.81":
            mags = [math.sqrt(sum(axis[i] ** 2 for axis in values))
                    for i in range(min(len(v) for v in values))]
            mean = sum(mags) / len(mags)
            det["mean_magnitude"] = round(mean, 3)
            lo, hi = PLAUSIBLE[kind]
            if not lo <= mean <= hi:
                warnings.append(f"{name}: |mean| {mean:.2f} outside {lo}..{hi}"
                                " (bench or calibration, not failed)")
        elif kind in PLAUSIBLE:
            lo, hi = PLAUSIBLE[kind]
            if kind == "earthfield":
                mags = [math.sqrt(sum(axis[i] ** 2 for axis in values))
                        for i in range(min(len(v) for v in values))]
                mean = sum(mags) / len(mags)
            else:
                allv = [v for vs in values for v in vs]
                mean = sum(allv) / len(allv)
            det["mean"] = round(mean, 3)
            if not lo <= mean <= hi:
                warnings.append(f"{name}: mean {mean:.2f} outside {lo}..{hi}"
                                " (bench or calibration, not failed)")
        tb = spec.get("time_buffer")
        if tb and spec.get("rate"):
            ts = _finite(bufs.get(tb) or [])
            if len(ts) > 4 and ts[-1] > ts[0]:
                rate = (len(ts) - 1) / (ts[-1] - ts[0])
                det["achieved_rate"] = round(rate, 1)
                expect, tol = spec["rate"]["expect"], spec["rate"].get("tol", 0.3)
                if abs(rate - expect) > expect * tol:
                    findings.append(f"{name}: rate {rate:.0f} vs expected "
                                    f"{expect} (tol {tol:.0%})")
    if manifest.get("gps"):
        # indoors: graceful no-fix only - launch, run, no crash
        if dev.launch(manifest["gps"]["experiment"]):
            if wait_api(dev.base, args.api_wait) is not None:
                api(dev.base, "/control?cmd=start")
                time.sleep(5)
                api(dev.base, "/control?cmd=stop")
                if wait_api(dev.base, args.api_wait) is None:
                    findings.append("gps: app stopped answering (no-fix path)")
                else:
                    details["gps"] = {"graceful": True}
            else:
                findings.append("gps: remote API not reachable")
    return {"passed": not findings, "findings": findings, "details": details}


def run_audio_suite(dev, args):
    """fixtures/audio/loopback.phyphox: speaker to microphone, dominant
    frequency must be the played 1 kHz (corrected by the achieved rate),
    magnitude above the floor."""
    findings, det = [], {}
    dev.set_media_volume_max()
    # the fixture is not a bundled asset: run.py serves the phyphox-docs
    # fixtures over http and the device opens it through the normal
    # phyphox:// route (adb reverse makes the host reachable at
    # 127.0.0.1 on Android; an iOS device uses the host's LAN address)
    url = (f"phyphox://{dev.fixture_host()}:{args.fixture_port}"
           f"/audio/loopback.phyphox")
    if not dev.open_url(url):
        return {"passed": False,
                "findings": ["could not open the loopback fixture"],
                "details": det}
    if wait_api(dev.base, args.api_wait) is None:
        return {"passed": False,
                "findings": ["remote API not reachable after loading the fixture"],
                "details": det}
    api(dev.base, "/control?cmd=start")
    time.sleep(6)
    api(dev.base, "/control?cmd=stop")
    bufs = _get_buffers(dev.base, ["peakfreq", "level", "achievedrate"])
    if not bufs or not _finite(bufs.get("peakfreq") or []):
        return {"passed": False, "findings": ["no analysis result"],
                "details": det}
    peak = _finite(bufs["peakfreq"])[-1]
    level = _finite(bufs.get("level") or [0])[-1]
    ach = _finite(bufs.get("achievedrate") or [48000])
    achieved = ach[-1] if ach else 48000.0
    expected = 1000.0 * 48000.0 / achieved if achieved else 1000.0
    det.update({"peak": peak, "level": level, "achieved_rate": achieved,
                "expected_peak": round(expected, 1)})
    if abs(peak - expected) > 75:
        findings.append(f"peak {peak:.0f} Hz, expected ~{expected:.0f}")
    if level < args.audio_floor:
        findings.append(f"level {level:.4f} below floor {args.audio_floor}")
    return {"passed": not findings, "findings": findings, "details": det}


def run_experiments_suite(dev, args):
    """The full shipped matrix: shell out to t1_experiments.py, which
    already knows launches, exports and verdicts."""
    out = os.path.join(args.out_dir,
                       f"experiments-{dev.platform}-{dev.serial if hasattr(dev, 'serial') else dev.udid}.json")
    cmd = [sys.executable, os.path.join(TOOLS, "t1_experiments.py"),
           "--platform", dev.platform,
           "--serial", getattr(dev, "serial", None) or dev.udid,
           "--port", str(dev.port), "--seconds", str(args.seconds),
           "--require-rows", "--out", out]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
    findings = []
    if r.returncode != 0:
        findings = [ln.strip() for ln in r.stdout.splitlines()
                    if ln.strip().startswith("!")] or ["experiments run failed"]
    return {"passed": r.returncode == 0, "findings": findings,
            "details": {"results_file": out}}


# --- languages: the T2 release check against BUILT ARTIFACTS -------------

# aapt dump badging reports BCP-47-ish spellings, not the resource
# qualifiers: the default (English) resources appear as '--_--', Chinese
# as zh-CN/zh-TW. Verified against a real debug APK 2026-08-26.
ANDROID_LOCALE_MAP = {"--_--": "en", "zh-CN": "zh-Hans", "zh-TW": "zh-Hant",
                      "zh-rCN": "zh-Hans", "zh-rTW": "zh-Hant",
                      "b+sr+Latn": "sr-Latn"}
IOS_LOCALE_MAP = {"zh_Hans": "zh-Hans", "zh_Hant": "zh-Hant",
                  "sr_Latn": "sr-Latn"}


def _canonical():
    import yaml
    with open(os.path.join(ROOT, "languages.yml")) as f:
        doc = yaml.safe_load(f)
    langs = set(doc.get("languages") or [])
    per_platform = {"android": set(langs), "ios": set(langs)}
    for exc in doc.get("exceptions") or []:
        for p in exc.get("platforms") or []:
            per_platform[p].add(exc["code"])
    return per_platform


def apk_locales(apk_path, aapt="aapt"):
    try:
        r = subprocess.run([aapt, "dump", "badging", apk_path],
                           capture_output=True, text=True, timeout=120)
    except FileNotFoundError:
        raise ToolMissing(f"aapt not found ({aapt!r}) - name the full "
                          f"build-tools path in lab.yml (aapt:)")
    m = re.search(r"locales:((?:\s+'[^']+')+)", r.stdout)
    if not m:
        return None
    out = set()
    for loc in re.findall(r"'([^']+)'", m.group(1)):
        out.add(ANDROID_LOCALE_MAP.get(loc, loc))
    return out


def ipa_locales(ipa_path):
    """The APP BUNDLE's own .lproj set from an .ipa (or a zipped .app /
    .xcarchive) - the set the App Store derives supported languages from
    and the set Bundle.main.localizations reports in the T0 row. Nested
    bundles are deliberately excluded: phyphox.app/Settings.bundle
    carries a larger translation set (40 lproj folders, 18 languages the
    app does not enable) that belongs to the Weblate workflow - the
    translation lives on a branch of the same repo - so it is there on
    purpose and is not what this check is about; matching anywhere in
    the archive over-counted exactly those (found on the first MacBook
    run, 2026-08-26)."""
    out = set()
    with zipfile.ZipFile(ipa_path) as z:
        for entry in z.namelist():
            m = re.match(r"(?:Payload/)?[^/]+\.app/([A-Za-z0-9_\-]+)\.lproj/",
                         entry)
            if m and m.group(1) != "Base":
                out.add(IOS_LOCALE_MAP.get(m.group(1), m.group(1)))
    return out or None


class ToolMissing(Exception):
    pass


def run_languages_suite(platform, artifact, aapt="aapt"):
    """FAILS on canonical-list mismatch - the T2 semantics. A missing
    tool or artifact SKIPS with a notice (passed: None) instead of
    aborting the run: one misconfigured lab.yml line must not kill the
    device suites that were fine."""
    if not os.path.exists(artifact):
        return {"passed": None,
                "skipped": f"artifact not found: {artifact}", "details": {}}
    try:
        got = (apk_locales(artifact, aapt) if platform == "android"
               else ipa_locales(artifact))
    except ToolMissing as e:
        return {"passed": None, "skipped": str(e), "details": {}}
    canonical = _canonical()[platform]
    if got is None:
        return {"passed": False,
                "findings": [f"could not read the locale set from {artifact}"],
                "details": {}}
    missing, extra = sorted(canonical - got), sorted(got - canonical)
    findings = []
    if missing:
        findings.append(f"missing from the artifact: {', '.join(missing)}")
    if extra:
        findings.append(f"in the artifact but not canonical: {', '.join(extra)}"
                        " (a testing locale left in a release build?)")
    return {"passed": not findings, "findings": findings,
            "details": {"artifact": artifact, "locales": sorted(got)}}
