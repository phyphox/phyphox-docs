# Testing a phyphox release

What has to pass before a phyphox release ships, in the order it runs. The tests themselves are
listed in [`test-matrix.yml`](test-matrix.yml) — one row per test, tagged in both app repositories
and checked mechanically by `tools/check_test_matrix.py`. This file is the procedure around them.

| Tier | When | Where | Budget |
|------|------|-------|--------|
| T0 | every commit and PR | JVM and simulator unit tests, no emulator boot | < 5 min |
| T1 | pushes to development, release branches, manual dispatch | emulator / simulator, scripted | 1–2 h, parallel |
| T2 | before a release, and after changes that touch what it covers | the device lab over USB | 2–3 h |
| T3 | at the release | a human, with the phone in hand | < 30 min per platform |

T0 and T1 run in CI in the app repositories and need nothing from anybody. What follows is T2 and
T3, which need hardware and a person.

## Before starting

- Both app repos on the revision you intend to ship, **built and installed on every lab device**.
  The lab checks what it found and says so in the report, but it will not install anything: a
  suite that quietly built its own subject would not be testing the release.
- `lab.yml` present on each host (copy `tools/lab/lab.yml.example`), naming that host's devices,
  its boards, and the release artifacts for the languages check.
- Phones in developer mode and unlocked. On iOS, the system permission prompts have to be accepted
  by hand once per install — no automation can dismiss them.
- The bench free: the lab takes an advisory lock (`.bench-lock-<hostname>` in the working root) and
  a second run refuses to start.

## T2 — the device lab

One command per host. Boards and firmware come from `lab.yml`, so this is the whole invocation:

```bash
python3 tools/lab/run.py --config lab.yml --host linuxbox --release --out lab-results
python3 tools/lab/run.py --config lab.yml --host macbook  --release --out lab-results
```

Each host runs every suite it has the hardware for — sensors, audio, experiments, the BLE bench
where a board is configured, and the languages gate where the host names a release artifact — and
writes `<host>.json`. The two hosts can run at the same time; they hold separate locks and, with a
board each, separate benches.

Then merge:

```bash
python3 tools/lab/run.py --merge lab-results
```

`merged.md` is the report to read, and it ends with the T3 checklist generated from the matrix.

### Reading the report

- **A finding fails the release.** It is a thing the app did that it should not have.
- **A warning is information.** A sensor outside its plausibility window is usually the bench —
  a phone lying on a screw, a stale magnetometer calibration. A languages difference on a
  development build is expected. Neither blocks a release; both are worth a glance.
- **The retry counts are the number to watch**, and they are the reason a green run still deserves
  a look. Both apps retry a refused BLE connection and a lost transfer internally, so a scenario
  passes whether the app got through first time or on its last permitted attempt. `app_retries`
  carries operations, retries and how many exhausted their budget. A count that climbs release over
  release is hardware or a library getting worse, long before it turns a run red.

## T3 — by hand

The checklist is at the end of `merged.md`, generated from the `manual: true` rows in
`test-matrix.yml` so it cannot drift from the matrix. Seven steps, once per platform, none of them
covered by anything above: a real GPS fix outdoors, a QR scan off paper, a phone call during an
audio experiment, a Bluetooth device nobody wrote for this test, an accessibility spot check, the
store screenshots, and the permission dialogs on a factory-fresh OS.

They are in the matrix rather than in a document of their own for the same reason as everything
else: one list, reviewed like code, so a step cannot quietly disappear.

## When something fails

Not every red run is the app, and on this bench most of them were not. Before reporting a finding
against either app:

- **BLE**: run `tools/lab/board_check.py` first. It talks to the board from the host's own
  Bluetooth adapter and does what the app does — pulls the experiment, checks its CRC, counts data.
  A clean 8/8 there against a phone that fails puts the fault in the app; the same failure from a
  neutral central puts it in the board or the library.
- **A phone that has been driven all day** can stop completing BLE connections while still
  completing transfers, which reads exactly like a regression. Every report carries `uptime_h` per
  device for that reason. Reboot and re-run before believing it.
- **Evidence is on disk**: `lab-results/evidence/` holds a screenshot at the moment of failure and
  the full instrumentation output of a failed connect, both named by device.

`tools/lab/README.md` is the long version — what each suite covers, what the bench needs, and the
failure modes that have cost time before.
