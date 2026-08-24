#!/usr/bin/env python3
"""Deterministic HTTP fixture for the network-connection tests (area G).

Serves the endpoints the fixture experiments in fixtures/network/ talk to.
Everything is flat JSON (the receive id addresses a top-level key) and
fully deterministic, so a test can assert exact buffer contents through
the remote API after a known number of polls.

Endpoints:
    /data       GET: {"seq": n, "value": n/2} - n counts requests to this
                endpoint, starting at 1. The poll counter IS the fixture:
                a connection with interval=X that ran for Y seconds must
                hold the consecutive sequence 1..k.
    /collect    GET or POST: records the request and echoes it back flat:
                query parameters (GET) or the JSON body's top-level values
                (POST) are returned under their own keys, plus
                {"result": true, "seq": n}. Send-and-receive-back in one
                round trip, so a test validates the SEND path purely
                through the app's own buffers.
    /malformed  GET: 200 with a text/plain body that is not JSON.
    /empty      GET: 200 with an empty body.
    /http500    GET: 500 with a JSON error body.
    /timeout    GET: accepts the connection, never answers (30 s sleep).
    /reset      GET: resets all counters, answers {"result": true}.

Run: python3 tools/network_fixture.py [port]   (default 8113)

MQTT is not served here: the mqtt fixture experiments need a broker -
see fixtures/network/README.md for the mosquitto setup.
"""

import json
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlparse

LOCK = threading.Lock()
COUNTERS = {}


def bump(key):
    with LOCK:
        COUNTERS[key] = COUNTERS.get(key, 0) + 1
        return COUNTERS[key]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _route(self, body_pairs):
        path = urlparse(self.path).path
        if path == "/data":
            n = bump("data")
            self._json({"seq": n, "value": n / 2})
        elif path == "/collect":
            n = bump("collect")
            echo = {"result": True, "seq": n}
            for k, v in parse_qsl(urlparse(self.path).query):
                echo.setdefault(k, _num(v))
            for k, v in (body_pairs or {}).items():
                echo.setdefault(k, v)
            self._json(echo)
        elif path == "/malformed":
            body = b"this is not json {"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/empty":
            self.send_response(200)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif path == "/http500":
            self._json({"result": False, "error": "deliberate"}, 500)
        elif path == "/timeout":
            time.sleep(30)
        elif path == "/reset":
            with LOCK:
                COUNTERS.clear()
            self._json({"result": True})
        else:
            self._json({"result": False, "error": "unknown path"}, 404)

    def do_GET(self):
        self._route(None)

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        pairs = {}
        try:
            doc = json.loads(raw)
            if isinstance(doc, dict):
                # flatten one level: {"v": 3} stays, {"v": [1,2]} keeps the
                # array (phyphox sends buffers as arrays)
                pairs = doc
        except Exception:
            pass
        self._route(pairs)


def _num(s):
    try:
        return float(s)
    except ValueError:
        return s


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8113
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"network fixture on port {port} (all interfaces - emulators "
          f"reach the host at 10.0.2.2, simulators at 127.0.0.1)")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
