# The device lab (T2)

Host-side driver for the hardware tier: the full experiment matrix,
per-device sensor plausibility, the audio loopback and the release
language check, on the seven lab phones - split-host capable, one entry
point, JSON per host, merged report.

    cp lab.yml.example lab.yml       # local: serials, host address, artifacts
    python3 tools/lab/run.py --config tools/lab/lab.yml --host macbook \
        --out /home/dicon/phyphox/lab-results
    python3 tools/lab/run.py --merge /home/dicon/phyphox/lab-results

**Both hosts must write into the SAME directory** for the merge to see
them - the working root syncs between the machines, so a path inside it
works for both. `--merge` writes `merged.json` (everything) and
`merged.md` (the readable summary: one line per device and suite,
findings collapsed by repetition, the language gate last) and exits
non-zero if any suite failed.

The split: the MacBook can run everything; or the Linux machine runs the
Android devices (`--host linuxbox`) while the MacBook runs iOS - each
writes `<host>.json` into the shared results directory and `--merge`
combines them.

`--jobs N` runs a suite on N devices at once. The devices are
independent (own serial, own forwarded port, own app), so this is
mostly free time: the `experiments` sweep across four phones takes one
phone's worth instead of four. **Audio is always serial regardless of
`--jobs`** - the phones share a room and one device's tone would land in
another's microphone. Two things to weigh before raising it: N phones
running camera and audio experiments at once draw N times the USB power
(the lab has already seen a battery lose against its charger), and a
parallel suite's per-device output is collected and printed when that
device finishes rather than streamed. Phones stay in developer mode and are unlocked once per
run; media volume for the audio suite is set automatically on Android
and by hand on iOS (part of the unlock-once ritual). Android devices
are held awake for the run (`svc power stayon usb`, with the screen
dimmed to its minimum because staying awake means staying lit - the old
phones already lose against USB power) and both settings are restored
afterwards; iOS devices stay awake on USB by themselves.

iOS hardware additionally needs its system permission prompts confirmed
BY HAND once per app install - there is no simctl privacy on a real
device, devicectl offers nothing, and -phyphoxAutoConfirm deliberately
touches no system dialog. The first record run raises Motion & Fitness
and Location, the first audio run Microphone, the first experiments
sweep Camera; tap them as they come and every later run is dialog-free
until the app is reinstalled. (Android needs none of this: the driver
pre-grants via pm grant.)

## Host prerequisites for the ble suite

Only the BLE suite needs more than adb/Xcode: `arduino-cli` and `mpremote`
on PATH, `esptool` (either the v4 `esptool.py` or the v5 `esptool`), an
ESP32 MicroPython image passed as `--micropython-firmware`, and the
`pyserial` module in the venv the driver runs from. pyserial is
deliberately NOT in requirements.txt: the docs build and app CI install
that file and never open a serial port. It is needed only for the three
scenarios where the data goes phone -> board and the board's own printout
is the evidence.

`arduino-cli` needs the cores for the bench boards installed once:

    arduino-cli core install esp32:esp32
    arduino-cli core install arduino:mbed_nano

Without the second one every `nano33ble` scenario fails at compile with
"Plattform 'arduino:mbed_nano' nicht gefunden", which is a host that was
never set up rather than anything about the board.

Two ESP32 build settings are carried in `scenarios.yml` rather than left
to the default FQBN, both found by compiling every example during bring-up:
`PartitionScheme=huge_app` (three examples overflow the default 1.2 MB app
partition) and `-DLED_BUILTIN=2` for `getDataFromSmartphone` (the generic
esp32 board defines no `LED_BUILTIN`, and the variants that do offer no
partition option). Both are board configuration. The sketches themselves
are flashed unmodified and must stay that way — a modified example is no
longer the thing users have.

One mpremote trap, met during bring-up and worked around in `ble.py`:
`mpremote fs cp -r <dir> :` recreates the SOURCE PATH on the board, so an
absolute path puts the library at `/home/.../phyphoxBLE` instead of
`/phyphoxBLE`. The example then boots into an ImportError and the board
advertises nothing, which looks exactly like a BLE fault from the phone
side. The driver therefore copies a relative path with `cwd` set to the
library checkout. If you ever debug a board that flashed cleanly but does
not appear in the scan, check `mpremote connect <port> fs ls` first.

## Suites and their matrix rows

- `sensors` (`device-sensors`): per-device manifest driven - liveness,
  plausibility (|accel| at rest, gyro near zero, earth-field magnitude,
  pressure range, light positive), achieved rate vs expectation, and the
  graceful GPS no-fix path indoors. A real fix is T3. Liveness and rate
  FAIL; the plausibility windows only WARN (maintainer, 2026-08-26): a
  lab phone routinely sits on a screw or carries a stale magnetometer
  calibration - a figure-eight fixed the A3's 176 uT - and no plausible
  phyphox bug changes the values while keeping the rate right. The
  warnings stay in the report as bench information.
- `audio` (`device-audio`): fixtures/audio/loopback.phyphox - speaker to
  microphone, FFT peak at the played 1 kHz (corrected by the achieved
  rate), level above the floor. The fixture is served from this checkout
  over http (adb reverse on Android, the host's LAN address for iOS).
- `experiments` (`device-experiments`): the full shipped matrix through
  tools/t1_experiments.py per device - open, run, stop, all six export
  formats validated. Bluetooth experiments stay load-phase only (their
  data plane is the phase-6 board lab).
- `ble` (`ble-compat-arduino`, `ble-compat-micropython`): the board bench,
  and the one suite that inverts the loop - it flashes a board, then runs
  every phone in that scenario's scope against it, because a flash costs
  about a minute and repeating it per phone would waste most of the run.
  It is therefore not in the default `--suites`, needs `--board-port` per
  board, and owns its orchestration (`ble.run_suite`) rather than going
  through the per-device dispatch. A full pass with both boards attached
  is 21 flashes for the ten scenarios; the idle board is kept advertising
  a DIFFERENT name throughout so the scan has to discriminate, and a run
  that ends up without one says so in its warnings.

  Two flags for it: `--ble-scenario [lib/]example` narrows a run to one
  scenario for bring-up (the report is marked as narrowed, so it cannot
  be mistaken for a pass), and `--capture-ble-xml` freezes the XML each
  board serves into `corpus/valid/ble-libraries/` - the T0 half. That one
  rewrites corpus files, so use it when you mean to and read the diff.
- `languages` (`device-languages`): runs when the host entry names built
  artifacts - the apk's `aapt dump badging` locales / the ipa's .lproj
  set against languages.yml. This is the release gate that makes a
  forgotten testing locale or missing language impossible; mismatch
  FAILS. Put each artifact on a host that can read it: the `.ipa` needs
  nothing, the `.apk` needs aapt from the Android SDK, which a MacBook
  driving only iPhones does not have (it skips with a notice instead of
  failing the run). aapt is discovered in the usual SDK locations, so
  the Android host normally needs no `aapt:` entry.

  A bare path means a RELEASE candidate and a mismatch fails. For a
  development build write `{path: ..., release: false}`: the comparison
  still runs and its result is reported as a warning, but it does not
  fail the run - a test build legitimately carries the testing-only
  locales, and a check that is red by design every run teaches everyone
  to ignore red. Point the entry at a release artifact (or drop the
  flag) and the gate has its teeth back.

## Per-device sensor manifests

`devices/<id>.yml`, committed - the expected truth per lab phone. First
time on a device:

    python3 tools/lab/run.py --config lab.yml --host X --record-manifest pixel-9-pro

writes `devices/pixel-9-pro.skeleton.yml` with the observed buffer names
per core experiment and the /meta sensor list (Android). Hand-finish it:
which sensors this device HAS, per sensor the experiment, value/time
buffer names, a plausibility kind (magnitude9.81, near0, earthfield,
pressure, positive) and the expected rate. A sensor absent from the
manifest is not tested on that device - the older phones are in the lab
precisely because their sensor sets differ.

## Honesty notes

- The iOS device paths (devicectl launch, pymobiledevice3 forward) were
  written on the Linux machine and are UNVERIFIED until the first
  MacBook run; whatever needed fixing is a finding for the docs session.
- The suites carry the phyphox-test tags in suites.py - one driver
  serves both platforms, so the matrix checker accepts tags from this
  repository for the T2 rows.
