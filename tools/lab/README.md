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

## The ble suite follows the boards; it does not split

Every other suite is split-host: each machine drives its own phones and the
merge combines the reports. The ble suite cannot be, because flashing and
phone-driving are one loop — a board is flashed, then every phone in that
scenario's scope connects to it before the next flash. The boards are USB
devices on one machine at a time, so **the board travels to whichever host
drives the phones**, and an iOS pass means physically moving the ESP32 to
the MacBook.

What that host then needs, beyond the Xcode tooling the other suites use:
`arduino-cli` with the `esp32:esp32` core, `mpremote`, `esptool`, an ESP32
MicroPython image, and `pyserial` plus `bleak` in its venv. `board_check.py` additionally needs Bluetooth
permission for the terminal it runs from on macOS, which the OS asks for
once.

Baselines do not need re-recording per platform: what they pin is the
experiment the BOARD serves — its title and buffers — so an iOS pass
compares against the same `fixtures/ble/baselines/` files recorded on
Android. A platform that disagrees there is a finding, not a reason for a
second set of files.

**The first iOS pass ran 2026-08-28**, and that held: iPhone 14 Pro on
iOS 26.6 against the ESP32, `--ble-scenario arduino/randomNumbers`, the
board tagged `phyphox device M1`. The experiment the board serves
transferred, loaded and ran at 19.9 Hz on both channels, agreeing with
the Android-recorded baseline down to the title and the buffer names —
one set of files, as this section claims. Getting there took an app fix
rather than a driver fix: `-phyphoxBleConnect` matched the requested name
against `peripheral.name`, CoreBluetooth's cached name for the device,
because the scan never handed the advertised one to the delegate — which
the per-flash bench tags make stale by construction, so the seam had
never once taken a board (phyphox-ios `b43ae390`). Worth knowing the next
time a phone scans past a board that is plainly on the air: on iOS, check
the device log for `-phyphoxBleConnect: skipping a device advertising as
…`, which names all three names it compared.

## One session at a time

The phones and the boards are shared with whoever else is working in this
folder, and a run takes an advisory lock before touching them:
`.bench-lock-<hostname>` in the working root, naming who holds it, since
when and with which pid. A second run on that machine refuses to start
and says who has it; `--force-bench` overrides, and a lock whose process
is gone is taken over automatically.

**Per host, not one shared file.** The working root syncs between the
Linux machine and the MacBook, and the two benches are different phones
and different boards, so neither should ever wait for the other - and
with the bench tags on advertised names they are meant to run at the same
time. The first version knew that when reading a lock but not when
writing one: both hosts wrote a single `.bench-lock`, so the second run
to start overwrote the first one's entry, and the first then found a lock
that was not its own and stopped itself mid-pass believing someone had
taken its phones. That is exactly what happened on 2026-08-28, two
scenarios into a full pass, when the MacBook began a run. One file each
also means the two machines never write the same file, which matters when
what is between them is a sync client.

This is not bureaucracy. On 2026-08-27 a full ble pass and an Android
session ran at once: the pass held a connection to each board in turn (a
BLE peripheral stops advertising while connected) and drove the shared
Pixel 3, so the other session saw a dead bench and an experiment that
started measuring by itself a second after loading. Both were the other
session. If you are about to touch the hardware by hand, look at that
file first.

## Host prerequisites for the ble suite

Only the BLE suite needs more than adb/Xcode: `arduino-cli` and `mpremote`
on PATH, `esptool` (either the v4 `esptool.py` or the v5 `esptool`), an
ESP32 MicroPython image passed as `--micropython-firmware`, and the
`pyserial` module in the venv the driver runs from. **The suite checks
for these before it flashes anything** and stops with the tool's name if
one is missing - a host that was never set up looks nothing like a board
fault, but discovered per scenario it arrives as two failed flashes and a
board declared dead. On the MacBook on 2026-08-28 a missing `mpremote`
was worse still: the run raised on the first MicroPython scenario, and
the operator watched an idle phone until the run ended before seeing why
- and because the report is written only at the end, the seven scenarios
that HAD already run against the phone were lost with it. A crashing
suite now still produces a report, with the exception as its finding. pyserial is deliberately NOT in requirements.txt: the docs build and app CI install
that file and never open a serial port. It is needed only for the three
scenarios where the data goes phone -> board and the board's own printout
is the evidence.

**ModemManager must be kept off the boards.** The ESP32's CP2102 is not an
ACM device and is not affected, so this matters only once a board with a
native USB stack is on the bench again (see the scope note below) - but the
rule costs nothing and the failure it prevents is unreadable. ModemManager
probes every new ACM device with AT commands, and that left the Nano 33
BLE's bootloader unresponsive: the port opens, a SAM-BA `V#` returns
nothing, and `bossac` reports "No device found on ttyACM0" against a
bootloader that is demonstrably there. It is a race, so uploads work until
they suddenly do not. `journalctl -u ModemManager` shows the claim - "port
ttyACM0 released by device .../3-2.2.2" each time the board re-enumerates.
Fix it once, as root:

    # /etc/udev/rules.d/99-arduino-no-modemmanager.rules
    SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ENV{ID_MM_DEVICE_IGNORE}="1"
    SUBSYSTEM=="tty", ATTRS{idVendor}=="2a03", ENV{ID_MM_DEVICE_IGNORE}="1"

    sudo udevadm control --reload-rules

`sudo systemctl stop ModemManager` works for one session if you would rather
not add a rule.

## One board on the bench, and why that is the plan

`scenarios.yml` names the ESP32 and nothing else. The bench Nano 33 BLE
stopped accepting uploads on 2026-08-28 - not from this driver, not from
the Arduino IDE, not from a second PC - and the maintainer retired it
rather than replacing it, because the split it forced is the right one:

- **this suite is a RELEASE gate**: does the app still talk to boards?
  One board answers that, across every phone in the lab.
- **the library gets its own tests**, with many boards and a single
  phone, living with `phyphox-arduino` and built when that library is
  next worked on.

The driver keeps its per-board machinery - the library test is where it
will be wanted, and it degrades to one board correctly. Adding a board
back is one line under `flash.fqbn` plus the board's name in the
scenarios that should run on it.

Two things are genuinely lost meanwhile, and both are reported rather
than papered over. **The scan runs with no distractor**: with one board
there is nothing else in the air, so finding the right device out of one
device proves less than it looks, and every run says so once in its
warnings. And **NRF52 coverage is gone**: the Arduino library emits
different XML per board (`fixtures/ble/captured/README.md`), so the
ESP32's output is not evidence about anyone's Nano. The two Nano captures
already in `corpus/valid/ble-libraries/` stay - they are real library
output that both parsers must keep loading, and the board they came from
being off this desk does not change that.

### Retired-board notes, kept for the library test

The Nano was awkward long before it died, and the next USB-native board
will be too. `usb_reset()` in `ble.py` issues `USBDEVFS_RESET` on one
board's device node - deliberately device-scoped, never hub-wide, because
cutting a hub takes out whatever another session is using. It needs write
access to the node:

    # /etc/udev/rules.d/99-arduino-usbreset.rules
    SUBSYSTEM=="usb", ATTRS{idVendor}=="2341", MODE="0664", GROUP="plugdev"

It clears a board caught mid-re-enumeration and was measured NOT to clear
a stuck bootloader: the device comes back and is still mute, so removing
VBUS is what that state needs and a reset cannot do it. Measured
2026-08-27: after a re-plug one or two uploads succeed, then one leaves
the board in its bootloader (`2341:005a`), and from there nothing
recovers it - not a reset press, not a double-tap, not waiting, not
`bossac` by hand, not a USB reset. The kernel logged marginal USB around
these resets (`device descriptor read/64, error -32`), which is why a
cable or hub is the first thing to suspect on the next board. A root port
instead of the shared 1a86 hub helped and did not cure it.

The driver drops a board after two failed flashes and carries on with any
others; `arduino-cli` needs each bench board's core installed once, which
is now just

    arduino-cli core install esp32:esp32

A board added without its core fails at compile with "Plattform '...'
nicht gefunden", which is a host that was never set up rather than
anything about the board.

Two ESP32 build settings are carried in `scenarios.yml` rather than left
to the default FQBN, both found by compiling every example during bring-up:
`PartitionScheme=huge_app` (three examples overflow the default 1.2 MB app
partition) and `-DLED_BUILTIN=2` for `getDataFromSmartphone` (the generic
esp32 board defines no `LED_BUILTIN`, and the variants that do offer no
partition option). Both are board configuration. The sketches themselves
are flashed unmodified and must stay that way — a modified example is no
longer the thing users have.

`tools/lab/board_check.py` needs `bleak` in the same venv (again lab-only,
again not in requirements.txt). It connects to a board from THIS machine's
Bluetooth adapter, pulls the experiment and then counts data
notifications, several times over. It asks for the experiment the way the
app does - subscribe to `cddf0002`, then write `0x01` to `cddf0003` where
the device offers it - because **a peripheral may want either, and which
one is a property of that implementation**. Subscribing is the original
trigger and still the default; the control characteristic came later
(maintainer, 2026-08-28) for stacks that offered no callback on
subscription. It does not split by library: inside phyphox-arduino the
ESP32 and NRF52 transfer on the subscription (`phyphoxBLE_ESP32.cpp`,
`onSubscribe` -> `startTask`) while the NINA-B31, Nano 33 IoT and STM32
carry a control characteristic (`phyphoxBLE_NanoIOT.cpp`,
`controlCharacteristicWritten`), and phyphox-micropython waits for the
write (`phyphoxBLE.py`, `_IRQ_GATTS_WRITE`). Both apps do both and say so
in a comment (`BluetoothExperimentLoader.kt`, `BluetoothScan.swift`);
nothing in the documentation does, which is worth fixing whenever the BLE
protocol is specified. Written against the subscription alone, this tool
reported a healthy MicroPython board as 0/8 eight times in a row.
Run it before reporting any BLE fault against either app: it is the control
that says whether the board is doing its job, and it settled today's
question in five minutes after a lot of peripheral-side guesswork did not.
An 8/8 there against a phone that fails half its connects puts the fault on
the phone; a board that starves here was never the app's fault at all.

Do not judge a board by what the Arduino library reports about itself.
`PhyphoxBLE::isSubscribed` is never cleared on disconnect, `write()`
notifies without consulting it, and the 0x2902 descriptor keeps its last
value after every client is gone - the board will happily print
`connected=0 cccd=0x0100`. Only `getConnectedCount()` and the descriptor
WRITE CALLBACKS are current; everything else is bookkeeping, and it misled
this session twice before the maintainer called it.

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
  through the per-device dispatch. A full pass is ten flashes for the ten
  scenarios on the one bench board. Where a second board is attached the
  idle one is kept advertising a DIFFERENT name so the scan has to
  discriminate; the single-board bench cannot, and every run says so once
  in its warnings.

  Two flags for it: `--ble-scenario [lib/]example` narrows a run to one
  scenario for bring-up (the report is marked as narrowed, so it cannot
  be mistaken for a pass), and `--capture-ble-xml` freezes the XML each
  board serves into `corpus/valid/ble-libraries/` - the T0 half. That one
  rewrites corpus files, so use it when you mean to and read the diff.

  **The Android connect test is held open while the host measures.**
  Instrumentation runs in the app's own process, so the app dies the
  moment `am instrument` returns - on the Pixel 3 the remote API answered
  at 33 s and was gone at 36 s with the process. The driver therefore
  starts the run in the background, waits for the test to say it is
  holding, measures, and then sets `debug.phyphox.labRelease` to `1`; the
  test polls that property and returns, and its own assertions are
  collected afterwards. iOS needs none of it - `-phyphoxBleConnect` is
  the app launching itself and it stays up.

  Waiting for the HOLD rather than for the API matters more than it
  looks. The remote server comes up when the experiment loads, which is
  while the test is still asserting - and one of its assertions is that
  nothing is measuring. A host that starts there fails the test it is
  waiting on, the test throws before reaching its hold, and the app dies
  with it; what the host then sees is a phone serving nothing, which
  reads exactly like a BLE fault. Two sessions chased that as an app bug
  for an afternoon. The handshake is the app's own log line
  (`phyphoxBleCompat: holding the app open`).

  **Two findings came out of the first three-phone passes on
  2026-08-28**, and neither was where it first looked.

  The experiment transfer failed about one connect in four - 12 of 44
  attempts across two passes, moving between phones from one pass to the
  next, so not an Android version, a library, a scenario or a board.
  `board_check.py` cleared the board half of it (8/8 transfers from a
  neutral central against the same flash, 1.6-4.0 s each, minutes after
  the app had timed out at 90 s) and the Android session fixed the app
  half. **It is better, not gone: 1 of 38 connects after the fix.** A
  full pass is 19 connects, so about a third of passes come out green at
  that rate - which is why it went back to them (`Android-TODO.md`)
  rather than being written off as flake. A gate that is red two runs in
  three gets ignored.

  The other was `micropython/getDataFromSmartphone`, which is now
  **disabled in `scenarios.yml`** on the maintainer's call: the example's
  own main loop never yields to the MicroPython scheduler, which degrades
  BLE until the older phones cannot connect. `MicroPython-TODO.md` in the
  working root has the write-up, including two traps that hide it -
  `print()` yields, so instrumenting the loop fixes the bug while you
  look at it, and `mpremote eval` soft-resets the board. A disabled
  scenario is warned about once per run rather than removed, because
  missing coverage that a green report does not mention is the thing this
  lab exists to prevent; re-enabling is deleting the `disabled:` key.

  A connect failure leaves the whole instrumentation output in
  `lab-results/evidence/<phone>-<library>-<example>-connect-failed.txt`.
  Read that first: before it existed, failures were reported as JUnit's
  header line with the exception thrown away, which is how "the old
  phones are broken" survived a whole morning as a theory.

  **Every flash gets a bench tag.** The board advertises its scenario's
  name with a short host letter and this run's flash number appended -
  `phyphox device L1`, `My Device M11` - written into a copy of the
  example before it is built (`rename_source`; the library checkouts are
  never touched). The count restarts every run, so `L1` always means the
  first flash of the pass in front of you.

  Three reasons, all the maintainer's (2026-08-28): a run's progress is
  readable from across the room, since the name in a scan list says which
  flash is on the board; a board still advertising an earlier scenario
  cannot be mistaken for the current one, which is what the
  duplicate-advertiser check exists to catch; and the Linux machine and
  the MacBook can run the suite at the same time with an ESP32 each,
  because `L` and `M` never collide. The name is the one part of a sketch that identifies a
  device rather than exercising the app, so tagging it cannot hide an app
  defect. The real risk is a name too long for an advertising payload, so
  the tag is short and `rename_source` refuses to flash past 26
  characters.

  Two things it is checked against rather than trusted with: there must
  be exactly one `start()` call to rewrite, and where an example names
  itself that name must match `scenarios.yml` - a silent miss would flash
  an untagged board and leave the phone hunting for a name nothing is
  advertising, which reads exactly like a BLE fault. The tag is also
  stripped back out of captured XML before it is written as a corpus
  fixture; left in, every run would rewrite those files with a new number.

  **A failed scenario is retried, and the attempt count is reported**
  (`--ble-attempts`, default 2). Passing on a later attempt is a PASS
  with a warning naming what failed first; failing every attempt is a
  finding, as before. The maintainer's call, 2026-08-28, and the same
  reasoning as the sensors suite's warn-only plausibility windows: a
  green pass has to be REACHABLE or the gate gets waved through, and a
  19-connect pass against a 2.6% per-connect transfer flake comes out
  green about a third of the time.

  It hides nothing. Each scenario carries `attempts` in the report, each
  device carries `retries`, and the run's last line names the total, so a
  number that starts climbing is visible long before it becomes a red
  pass. Watch that number rather than the colour: two retries in a pass
  is the bench; five is a regression that has not gone red yet.

  What is NOT retried, because none of it is transient: a board that will
  not flash, a name nothing advertises, two boards under one name, a
  missing tool, a capture the spec rejects. Those fail the run outright.

  **Start a release pass from rebooted phones.** A phone that has been
  driven all day stops completing BLE data connections while still
  completing transfers, which looks exactly like an app regression in the
  code that runs between the two. On 2026-08-28 the Nexus 5X failed all
  five of its scenarios that way - experiment loads, then "Es besteht
  keine Verbindung zu dem Bluetooth Gerät" - hours after a build touching
  that very path had landed. It failed again on a narrowed re-run, and
  passed after a reboot; its whole scope then passed. The other two
  phones were green throughout the same pass, so it was neither the board
  nor the build.

  The driver does NOT reboot for you. It would add minutes per phone to
  every run, and it would have hidden this instead of teaching it. What
  it does is record `uptime_h` per phone in the ble result, so the number
  that explains a failure like this is already in the report when someone
  reads it.

  **Baselines are recorded by hand, and cannot be otherwise.** The point
  of a baseline is that the PREVIOUS release worked, so it has to come
  from that release - which predates everything the driver uses to steer
  a phone. Android v1.2.0 has no `debug.phyphox.remote`; an
  instrumentation test must be signed with the same key as the app it
  drives, which a Play-signed build rules out; and `-phyphoxBleConnect`
  is likewise newer than the released iOS binary. What the released app
  does have is remote access as an ordinary user feature. So
  `--record-ble-baseline` flashes each board, waits while an operator
  connects the phone and switches remote access on, and then measures and
  writes `fixtures/ble/baselines/` itself. Ten scenarios, ten pauses,
  once per reference release.
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
  written on the Linux machine and were unverified until 2026-08-28, when
  the first MacBook run drove a phone (iPhone 14 Pro, iOS 26.6, the ble
  suite): both worked as written and the driver needed no fixing — what
  was broken was on the app side, see the ble section. The other iOS
  suites — sensors, audio, experiments — still have not run on hardware
  here, so treat their iOS paths as unverified.
- The suites carry the phyphox-test tags in suites.py - one driver
  serves both platforms, so the matrix checker accepts tags from this
  repository for the T2 rows.
