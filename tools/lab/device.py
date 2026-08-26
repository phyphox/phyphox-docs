"""Device handles for the lab driver (run.py).

AndroidDevice drives a phone over adb by serial: port forward, the two
debug.phyphox.* switches, asset launches, media volume for the audio
loopback. IOSDevice drives an iPhone/iPad from a macOS host via devicectl
(launch with the -phyphox* arguments) and a user-provided port forward
(iproxy or pymobiledevice3 usbmux forward - started by run.py when the
lab.yml entry names a local port). The iOS paths were written on the
Linux machine and are UNVERIFIED until the first MacBook run - anything
that needed fixing there is a finding for the docs session.
"""

import subprocess
import sys
import time
import urllib.parse
import urllib.request

ANDROID_BUNDLE = "de.rwth_aachen.phyphox"
IOS_BUNDLE = "de.rwth-aachen.physics.phyphox"


def sh(cmd, timeout=30):
    """One visible retry on timeout, then a failed stand-in (the
    t1_experiments convention - a wedged tool fails one step, not the
    run)."""
    for attempt in (1, 2):
        try:
            r = subprocess.run(cmd, capture_output=True, text=True,
                               timeout=timeout)
            if attempt == 2:
                print(f"   ~ retried after a timeout: {' '.join(cmd[:4])} ...")
            return r
        except subprocess.TimeoutExpired:
            if attempt == 2:
                print(f"   ~ command timed out twice: {' '.join(cmd[:4])} ...")

    class T:
        returncode, stdout, stderr = -1, "", "timed out"
    return T()


def api(base, path, timeout=5):
    try:
        with urllib.request.urlopen(base + path, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e).encode()


def wait_api(base, seconds, probe_timeout=2):
    t0 = time.time()
    while time.time() - t0 < seconds:
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


class AndroidDevice:
    platform = "android"

    def __init__(self, serial, port):
        self.serial, self.port = serial, port
        self.base = f"http://127.0.0.1:{port}"
        self.adb = ["adb", "-s", serial]

    def prepare(self, fixture_port=None):
        _claim_host_port(self.adb, self.port)
        if fixture_port:
            # the phone reaches the host's fixture server at 127.0.0.1
            sh(self.adb + ["reverse", f"tcp:{fixture_port}",
                           f"tcp:{fixture_port}"])
        for prop in ("remote", "autoConfirm"):
            sh(self.adb + ["shell", "setprop", f"debug.phyphox.{prop}", "1"])
        for perm in ("RECORD_AUDIO", "CAMERA", "ACCESS_FINE_LOCATION",
                     "ACCESS_COARSE_LOCATION"):
            sh(self.adb + ["shell", "pm", "grant", ANDROID_BUNDLE,
                           f"android.permission.{perm}"])

    def cleanup(self):
        for prop in ("remote", "autoConfirm"):
            sh(self.adb + ["shell", "setprop", f"debug.phyphox.{prop}", "''"])

    def launch(self, asset_path):
        self.stop_app()
        url = "phyphox://asset=" + urllib.parse.quote(asset_path, safe="")
        r = sh(self.adb + ["shell", "am", "start", "-W", "-a",
                           "android.intent.action.VIEW", "-d", url])
        return r.returncode == 0 and "Error" not in r.stdout

    def stop_app(self):
        sh(self.adb + ["shell", "am", "force-stop", ANDROID_BUNDLE])

    def fixture_host(self):
        return "127.0.0.1"  # via adb reverse

    def open_url(self, phyphox_url):
        """Open a phyphox:// URL (e.g. a fixture served by run.py)."""
        self.stop_app()
        r = sh(self.adb + ["shell", "am", "start", "-W", "-a",
                           "android.intent.action.VIEW", "-d", phyphox_url])
        return r.returncode == 0 and "Error" not in r.stdout

    def set_media_volume_max(self):
        sh(self.adb + ["shell", "cmd", "media_session", "volume",
                       "--stream", "3", "--set", "15"])
        sh(self.adb + ["shell", "media", "volume", "--stream", "3",
                       "--set", "15"])


class IOSDevice:
    platform = "ios"

    def __init__(self, udid, port):
        self.udid, self.port = udid, port
        self.base = f"http://127.0.0.1:{port}"
        self._forward = None

    def prepare(self, fixture_port=None):
        self.fixture_port = fixture_port
        # forward local port -> device port 80 (the app's server on
        # hardware). Invoked as a MODULE: a pip-installed console script
        # not being on PATH is the normal state on macOS, and a missing
        # binary in a background Popen would only surface later as an
        # unreachable port (found on the first MacBook run, 2026-08-26).
        try:
            import pymobiledevice3  # noqa: F401 - presence check only
        except ImportError:
            raise SystemExit(
                "pymobiledevice3 is not installed for this Python "
                f"({sys.executable}) - pip install pymobiledevice3")
        self._forward = subprocess.Popen(
            [sys.executable, "-m", "pymobiledevice3", "usbmux", "forward",
             str(self.port), "80", "--serial", self.udid],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    def cleanup(self):
        if self._forward:
            self._forward.terminate()

    def launch(self, asset_path):
        url = "phyphox://asset=" + urllib.parse.quote(asset_path, safe="")
        return self._launch_args(["-phyphoxUrl", url])

    def _launch_args(self, extra):
        args = extra + ["-phyphoxRemote", "-phyphoxRemotePort", "80",
                        "-phyphoxAutoConfirm"]
        # the "--" keeps devicectl from parsing the app's dash-prefixed
        # arguments as its own options (first hardware attempt failed on
        # every launch; simctl passes trailing args, devicectl does not)
        r = sh(["xcrun", "devicectl", "device", "process", "launch",
                "--terminate-existing", "--device", self.udid, "--",
                IOS_BUNDLE] + args, timeout=60)
        self.last_error = (r.stderr or r.stdout or "").strip()[-300:]
        if r.returncode == 0:
            return True
        if "device was not found" in self.last_error:
            # devicectl is CoreDevice, which only speaks to iOS 17+ - the
            # iPhone 8 tops out at iOS 16 and is in the lab precisely to
            # be old. Legacy path via pymobiledevice3's instruments
            # tunnel; needs developer mode and, on iOS <17, a mounted
            # developer disk image (python3 -m pymobiledevice3 mounter
            # auto-mount). UNVERIFIED until it records a skeleton - a
            # failure lands in the skeleton with this stderr.
            # NB: the developer/dvt subcommands select the device with
            # --udid, unlike usbmux's --serial (the captured error listed
            # the valid options)
            r = sh([sys.executable, "-m", "pymobiledevice3", "developer",
                    "dvt", "launch", "--udid", self.udid,
                    " ".join([IOS_BUNDLE] + args)], timeout=90)
            self.last_error = (r.stderr or r.stdout or "").strip()[-300:]
            return r.returncode == 0
        return False

    def stop_app(self):
        pass  # --terminate-existing on launch

    def fixture_host(self):
        # an iOS device reaches the host over the LAN; run.py passes the
        # host address from lab.yml (host_ip)
        return getattr(self, "host_ip", None) or "HOST-IP-UNSET"

    def open_url(self, phyphox_url):
        return self._launch_args(["-phyphoxUrl", phyphox_url])

    def set_media_volume_max(self):
        pass  # no CLI path; the unlock-once checklist sets the volume
