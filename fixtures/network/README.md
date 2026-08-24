# Network fixtures

Runtime fixtures for the network-connection tests (test-matrix rows
`network-http` and `network-mqtt`, tier T1): a deterministic local server
plus one experiment per behavior under test. Unlike the conformance
corpus, these files are *run*, not only parsed — but they are spec-valid
and the docs build validates them like corpus files, so they cannot drift
from the format.

## The pieces

- `tools/network_fixture.py` — the HTTP side: `/data` serves a counting
  sequence, `/collect` echoes sends back flat, plus the error endpoints
  (`/malformed`, `/empty`, `/http500`, `/timeout`). See its docstring.
  Binds all interfaces; `/reset` restarts the counters between tests.
- mosquitto for MQTT (`mosquitto.conf` here): plain listener on 1883,
  anonymous access — a test broker, never expose it beyond the test
  host. For the TLS (`mqtts/...`) variants, generate a throwaway CA and
  server certificate with openssl and add a TLS listener on 8883; that
  setup lands together with the mqtts fixtures (not written yet).
- One `.phyphox` per behavior, placeholders instead of a host:
  every file carries `FIXTURE-HOST` and `FIXTURE-PORT` in its connection
  address.

## The runner contract

- **Substitution.** The runner replaces `FIXTURE-HOST`/`FIXTURE-PORT` in
  the raw file bytes before handing them to the real loading path — the
  Android emulator reaches the host at `10.0.2.2`, the iOS simulator at
  `127.0.0.1`. Nothing else about loading is special.
- **Reset, load, start.** Call `/reset` on the fixture, load the
  experiment, start it (the remote API is the bus), let it poll for a
  defined time, stop, then assert buffer contents via `/get`:
    - `http-get-receive`: `seq` holds the consecutive integers 1..k for
      some k ≥ 1 (no gaps, no duplicates), `value` holds n/2 pairwise.
    - `http-get-send-roundtrip`: `back` holds 42.5 — the send went out
      and came back; `seq` proves how many round trips happened.
    - `http-post-roundtrip`: `back` holds the pattern 1, 2.5, 3 repeated
      per poll — the array send path.
    - `http-error-malformed`, `http-error-down`: the app keeps running
      and answering the remote API; `never` stays empty. No crash and no
      hang IS the assertion.
    - `mqtt-json-roundtrip`: with the broker up, `back` holds 7.25 —
      publish and subscribe through a real broker in one loop.
- Timing is not asserted beyond "at least one poll happened" — intervals
  are best-effort on both platforms.
