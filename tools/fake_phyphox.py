#!/usr/bin/env python3
"""Stand-in servers that reproduce the two apps' quirks, for testing the test.

    python3 tools/fake_phyphox.py            # android on :8111, ios on :8112
    python3 tools/contract_test.py --android http://127.0.0.1:8111 \
                                   --ios     http://127.0.0.1:8112

contract_test.py needs two phones, which makes it awkward to know whether the
script itself works. This serves just enough of each platform's behaviour -
including the divergences recorded in inconsistencies.yml - for the script to be
exercised without hardware.

**This is a fixture for testing contract_test.py, not a model of phyphox.** It is
not authoritative about anything, it is not kept in step with the apps, and a
disagreement between this file and an app is always this file being wrong. When
contract_test.py grows a probe, teach this fixture only as much as that probe
needs.
"""

import json
import math
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlparse

CRC32 = "1a2b3c4d"
BUFFERS = [{"name": "accX", "size": 200}, {"name": "t", "size": 200}]
SAMPLES = [0.1, 0.25, -0.4]


class Base(BaseHTTPRequestHandler):
    platform = None

    def log_message(self, *a):
        pass

    # ------------------------------------------------------------- plumbing
    def send_json(self, obj, status=200, cors=False):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_blob(self, data, ctype, status=200, cors=False):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_empty(self, status, cors=False):
        self.send_response(status)
        if cors:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qsl(u.query, keep_blank_values=True)
        handler = getattr(self, "h_" + u.path.strip("/").replace(".", "_") or "h_root", None)
        if handler is None:
            self.send_empty(404, self.cors)
            return
        handler(dict(q), q)

    # -------------------------------------------------------- shared payloads
    def config(self):
        return {
            "crc32": CRC32,
            "title": "Fixture", "localTitle": "Fixture",
            "category": "Test", "localCategory": "Test",
            "buffers": list(BUFFERS),
            "inputs": [{"source": "accelerometer",
                        "outputs": [{"x": "accX"}, {"t": "t"}]}],
            "export": [{"set": "Data", "sources": [
                {"label": "Acceleration x", "buffer": "accX"},
                {"label": "Time", "buffer": "t"}]}],
        }

    def status(self):
        return {"session": "abc123", "measuring": True,
                "timedRun": False, "countDown": 0}

    def meta_common(self):
        return {k: "" for k in (
            "version", "build", "fileFormat", "deviceModel", "deviceBrand",
            "deviceBoard", "deviceManufacturer", "deviceBaseOS",
            "deviceCodename", "deviceRelease", "depthFrontSensor",
            "depthFrontResolution", "depthFrontRate", "depthBackSensor",
            "depthBackResolution", "depthBackRate")}

    def h_time(self, q, pairs):
        self.send_json([{"event": "START", "experimentTime": 0.0,
                         "systemTime": 1.7e9}], cors=self.cors)

    def h_config(self, q, pairs):
        self.send_json(self.config(), cors=self.cors)


class Android(Base):
    platform = "android"
    cors = True

    def h_meta(self, q, pairs):
        j = self.meta_common()
        j["camera2api"] = ""
        j["camera2apiFull"] = ""
        j["sensors"] = {"accelerometer": {k: "" for k in (
            "name", "vendor", "range", "resolution", "minDelay", "maxDelay",
            "power", "version")}}
        self.send_json(j, cors=True)

    def h_get(self, q, pairs):
        out = {}
        for name, value in pairs:
            match = next((b for b in BUFFERS if b["name"] == name), None)
            if match is None:
                continue                      # unknown buffers are skipped
            if value == "":
                out[name] = {"size": match["size"], "updateMode": "single",
                             "buffer": [SAMPLES[-1]]}
            elif value == "full":
                out[name] = {"size": match["size"], "updateMode": "full",
                             "buffer": list(SAMPLES)}
            else:
                threshold = value.split("|", 1)[0]
                try:
                    float(threshold)
                except ValueError:
                    self.send_empty(400, True)   # bad threshold -> 400 (get-unknown-reference-buffer, fixed)
                    return
                ref = value.split("|", 1)[1] if "|" in value else name
                if not any(b["name"] == ref for b in BUFFERS):
                    self.send_empty(400, True)   # unknown reference -> 400 (get-unknown-reference-buffer, fixed)
                    return
                out[name] = {"size": match["size"], "updateMode": "partial",
                             "buffer": list(SAMPLES)}
        self.send_json({"buffer": out, "status": self.status()}, cors=True)

    def h_control(self, q, pairs):
        cmd = q.get("cmd")
        if cmd in ("start", "stop", "clear"):
            self.send_json({"result": True}, cors=True)
        elif cmd == "set":
            name, value = q.get("buffer"), q.get("value")
            if name is None or value is None:
                self.send_json({"result": False}, cors=True); return
            try:
                v = float(value)
            except ValueError:
                self.send_json({"result": False}, cors=True); return
            if not math.isfinite(v):
                self.send_json({"result": False}, cors=True); return  # rejects NaN and infinity (control-set-infinity, fixed)
            if not any(b["name"] == name for b in BUFFERS):
                self.send_json({"result": False}, cors=True); return  # unknown buffer -> false (control-set-unknown-buffer, fixed)
            self.send_json({"result": True}, cors=True)
        elif cmd == "trigger":
            self.send_json({"result": False}, cors=True)  # out-of-range index -> false, not a crash (control-trigger-out-of-range; Android side fixed, iOS still answers true)
        else:
            self.send_json({"result": False}, cors=True)

    def h_export(self, q, pairs):
        fmt = q.get("format")
        if fmt is None:
            self.send_json({"error": "Invalid format."}, cors=True)   # missing format -> error object, not a crash (export-invalid-format; Android side fixed)
            return
        try:
            i = int(fmt)
        except ValueError:
            self.send_json({"error": "Invalid format."}, cors=True)
            return
        if not 0 <= i <= 5:
            self.send_json({"error": "Format out of range."}, cors=True)
            return
        self.send_blob(b"fixture", "text/csv", cors=True)

    def h_res(self, q, pairs):
        if not q.get("src"):
            self.send_json({"error": "Unknown file."}, cors=True)
            return
        if q["src"] == "hue.png":
            self.send_blob(b"\x89PNG", "application/octet-stream", cors=True)
            return
        self.send_json({"error": "Unknown file."}, cors=True)


class IOS(Base):
    platform = "ios"
    cors = False

    def h_meta(self, q, pairs):
        self.send_json(self.meta_common())      # no sensors, no camera2api

    def h_get(self, q, pairs):
        if not pairs:
            self.send_empty(400)                # rejects an empty query
            return
        out = {}
        for name, value in pairs:
            match = next((b for b in BUFFERS if b["name"] == name), None)
            if match is None:
                continue
            if value == "":
                out[name] = {"size": match["size"], "updateMode": "single",
                             "buffer": [SAMPLES[-1]]}
            elif value == "full":
                out[name] = {"size": match["size"], "updateMode": "full",
                             "buffer": list(SAMPLES)}
            else:
                if "|" in value:
                    ref = value.split("|", 1)[1]
                    if not any(b["name"] == ref for b in BUFFERS):
                        self.send_empty(400)
                        return
                out[name] = {"size": match["size"], "updateMode": "partial",
                             "buffer": list(SAMPLES)}
        self.send_json({"buffer": out, "status": self.status()})

    def h_control(self, q, pairs):
        cmd = q.get("cmd")
        if cmd in ("start", "stop", "clear"):
            self.send_json({"result": True})    # clearGroup params ignored
        elif cmd == "set":
            name, value = q.get("buffer"), q.get("value")
            if name is None or value is None \
                    or not any(b["name"] == name for b in BUFFERS):
                self.send_json({"result": False}); return
            try:
                v = float(value)
            except ValueError:
                self.send_json({"result": False}); return
            self.send_json({"result": math.isfinite(v)})   # rejects infinity
        elif cmd == "trigger":
            self.send_json({"result": True})    # bounds-checked, silent no-op
        else:
            self.send_json({"result": False})

    def h_export(self, q, pairs):
        fmt = q.get("format")
        if fmt is None:
            self.send_json({"error": "Format out of range"})
            return
        try:
            i = int(fmt)
        except ValueError:
            i = 0
        if not 0 <= i <= 5:
            # The app traps here. A crashed app answers nothing at all, which is
            # what a client sees, so the fixture closes the connection.
            self.close_connection = True
            return
        self.send_blob(b"fixture", "text/csv")

    def h_res(self, q, pairs):
        if not q.get("src"):
            self.send_json({"error": "No file requested."})
            return
        self.send_json({"error": "Unknown file."})


def serve(cls, port):
    srv = ThreadingHTTPServer(("127.0.0.1", port), cls)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    a_port = int(sys.argv[1]) if len(sys.argv) > 1 else 8111
    i_port = int(sys.argv[2]) if len(sys.argv) > 2 else 8112
    serve(Android, a_port)
    serve(IOS, i_port)
    print(f"android fixture on http://127.0.0.1:{a_port}")
    print(f"ios     fixture on http://127.0.0.1:{i_port}")
    print("Ctrl-C to stop.")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
