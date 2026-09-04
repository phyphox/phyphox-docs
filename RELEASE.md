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
  **its boards and the MicroPython firmware**, and the release artifacts for the languages check.
  An older `lab.yml` predating the `boards:` entry is the common case, and a release run without it
  silently has no BLE suite — so the run says so rather than leaving you to notice:

      boards:
        esp32: /dev/ttyUSB0
      micropython_firmware: /path/to/ESP32_GENERIC-<version>.bin

  `--board-port esp32=… --micropython-firmware …` still override, for a board that has moved.
- Phones in developer mode and unlocked. On iOS, the system permission prompts have to be accepted
  by hand once per install — no automation can dismiss them.
- The bench free: the lab takes an advisory lock (`.bench-lock-<hostname>` in the working root) and
  a second run refuses to start.

## T2 — the device lab

**Empty the results directory first.** The merge folds in every report it finds there, and it has
no way to tell one release's results from the last one's — a stale file is merged in silence and
reported as part of this run. That is the worst failure mode this report has: green, and partly
about a build that is no longer the candidate.

```bash
rm -rf lab-results        # or use a fresh directory per release
```

A report is named `<host>-<suites>.json`, and the merge keys on the host recorded inside it, so
several runs of one host land in one section rather than overwriting each other. If two of them
claim the same suite on the same device, the merge says so instead of quietly picking one.

Then one command per host. Boards and firmware come from `lab.yml`, so this is the whole
invocation:

```bash
python3 tools/lab/run.py --config lab.yml --host linuxbox --release --out lab-results
python3 tools/lab/run.py --config lab.yml --host macbook  --release --out lab-results
```

### Running the BLE suite separately

The BLE suite needs the instrumentation APK, which a store-signed build cannot host, so a release
candidate usually runs everything else and takes BLE separately against a build you signed
yourself. Give the suites explicitly and they win — `--release` only fills the list in when you did
not:

```bash
# the release candidate, everything except BLE (the languages gate still runs:
# it is driven by the host's artifacts entry, not by --suites)
python3 tools/lab/run.py --config lab.yml --host linuxbox \
    --suites sensors,audio,experiments --release --out lab-results

# then, with the debug build and its androidTest APK installed
python3 tools/lab/run.py --config lab.yml --host linuxbox \
    --suites ble --release --out lab-results
```

Both write into the same directory — `linuxbox-sensors+audio+experiments.json` and
`linuxbox-ble.json` — and the merge combines them into one `linuxbox` section. Note the report
records what was installed at the time, so the two halves honestly show the two builds.

### Narrowing a run

Both flags take effect on top of `--release`, and both mark nothing in the report — a narrowed run
looks like a complete one, so use them while working, not for the release itself:

- `--platform ios` (or `android`) runs only that platform's devices on a host that has both. The
  MacBook can drive iPhones and Android phones, so this is how its two halves are split — or how
  you re-run just the iOS side after a fix.
- `--devices iphone-14-pro,ipad-pro` names devices explicitly. Without it, a run takes every device
  `lab.yml` assigns to the host, which is what a release wants.

The exception is the BLE suite, which is deliberately not per-device: it flashes a board and then
walks it past every phone in each scenario's scope, so narrowing by platform narrows which phones
it visits, not what it flashes.

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
`test-matrix.yml` so it cannot drift from the matrix. Five steps, once per platform, none of them
covered by anything above: a real GPS fix outdoors, a QR scan off paper and off a screen, a
Bluetooth device nobody wrote for this test, an accessibility spot check, and the permission
dialogs on a factory-fresh OS. Two further rows are marked optional and are listed separately -
they are the store listing update, not tests.

They are in the matrix rather than in a document of their own for the same reason as everything
else: one list, reviewed like code, so a step cannot quietly disappear.

The QR step has its material published with the documentation: the five codes on
<https://phyphox.org/docs/transferring-experiments/> are generated from two example experiments by
`tools/generate_qr.py` and verified on every docs build, so the step is "print that page, or put it
on a second screen, and scan" rather than "make yourself some QR codes first". The two link codes
resolve against the published site, so a release tested before the site is pushed will find them
pointing at whatever is live.

A step that cannot actually be carried out does not belong here - it reads as if someone were
watching when nobody is. That is why a phone call during an audio experiment is not in the list:
almost none of the lab phones have a mobile subscription, so audio interruption relies on user
reports and on colleagues testing on their own phones.

The two store rows are **optional**, and the checklist prints them in their own group below the
five: they are release preparation rather than tests, and most releases do not need them. Leaving
them unticked is a normal outcome. What they involve is the next section.

## The store release

Everything a release puts in front of a user that is not the app itself: the screenshots, the store
texts and the release notes. It is **one command per platform**, and each asks once before anything
reaches a store.

    cd phyphox-android              # on the Linux machine
    tools/store_release.py

    cd phyphox-ios                  # on the Mac, from the screenshot virtualenv
    ~/.venvs/phyphox-screenshots/bin/python tools/store_release.py

Budget about three hours: the capture is nearly all of it, and the emulators need the machine to
themselves. **Uploading is not releasing** — the run stops at "uploaded", and the listing goes live
with the app release, which is a manual act in each console.

Not all of it is needed every time. The screenshots have to be retaken when the app's appearance
changed enough that they no longer show the current app, or a scene was added or reworked in
`screenshots/scenes.yml`; the texts when `phyphox-translation` changed or a language gained a
translation. The run notices plates that are already there and offers to keep them, so a release
that only needs new release notes is the same command answered differently.

Everything is generated. The screenshots come from the **shipped experiment files**, with starting
values injected from measurements recorded on a real phone, so they show the real app rather than a
mock-up; the texts are read on the fly from `phyphox-translation`'s store PO files. **That
repository is only ever read from, never written to.** And the scenes are composed from the
experiment collection **in the working tree**, so check the repository out at the revision you are
shipping before starting; there is deliberately no `--ref`.

### Release notes — one source for all three channels

Both stores and F-Droid show the same release notes, and there is **one copy of them**: F-Droid's
changelogs in the Android repository,

    phyphox-android/fastlane/metadata/android/<lang>/changelogs/<versionCode>.txt

That file is version controlled, shows up in a diff and needs no credentials to read, which is why
it is the reference rather than either console. It also carries the state of the step: **if there
is no file for the current `versionCode`, the notes for this version have not been written yet**,
and the run asks for them — first thing, while the emulators are still cold, so the rest can run
unattended.

Only **English and German** are written by hand; every other store language shows the **English**
text. Release notes change with every release and a translation round would hold the release up for
weeks — unlike the store description, which goes through Weblate and changes about once a year.
Notes that already exist are never edited by either script; change those in the files.

Whichever platform asks for the texts writes them into `phyphox-android` — including the iOS run,
from the Mac. **Commit and push that**, or F-Droid will build the release without notes.

`phyphox-android/tools/changelog.py` is the one implementation of all of this and the iOS script
imports it across the working root; nothing about the release notes is written down twice.

### Android — Google Play and F-Droid

One metadata tree serves both: Play gets it over the API, F-Droid reads it out of the git
repository. `tools/store_release.py` runs, in this order:

1. **Preflight** — the sibling checkouts, the Python modules, the three AVDs and the Play
   credentials, all before three hours of capturing rather than after.
2. **Release notes**, asked for if this `versionCode` has none.
3. **Screenshots**, all three form factors from **one** build: `regularRelease` is assembled and
   signed once and photographed three times, so a listing cannot end up showing two builds.
4. **The mechanical check** over every plate. It catches broken and blank captures, not ugly ones —
   a plate on the wrong tab or a graph with unfortunate data still needs eyes.
5. **The F-Droid half into the metadata tree**: the listing text for every language that has a
   directory there — title, short and full description, prepared exactly as Play gets them, trimmed
   short description included, so the two stores never say different things — and the six English
   phone plates. No other images are committed: the stores upload over their APIs and never look at
   git, so the other locales' plates would be binary weight for nothing, and F-Droid falls back to
   English. A language with a translation but no directory is reported, not created; adding one to
   F-Droid is your decision.
6. **A rehearsal** — text and images into a Play edit, validated server-side, edit thrown away.
7. **The question.** Everything before it is local or discarded. Yes runs the same upload with
   `--commit`, which for this app **also submits it for review** — Play refuses
   `changesNotSentForReview`, so that cannot be deferred. Managed publishing is what keeps the
   reviewed listing away from users until you release it.
8. **The release-notes block** for the Play Console, printed last so it is on the screen when you
   go there. Play has no API path for it here: a release is created in the console when the bundle
   is rolled out, which is a different act from updating the store entry. Paste it under
   Release → Production → Edit release → Release notes.

**The run never touches git.** It ends by saying what is waiting there — the changelogs, the
listing text and the English plates — and when that is committed and pushed is your call.

Authentication is the maintainer's own Google account through a Desktop OAuth client, not a service
account - see `STORE-RELEASE-PLAN.md` §8.1 for the one-time setup.

### iOS — the App Store

The same shape, with the same numbering, so the two runs read alike. `tools/store_release.py`
runs, in this order:

1. **Preflight** — the sibling checkouts (`phyphox-android` among them, for the release notes),
   the Python modules, `simctl`, a fastlane that knows both screenshot sizes, and the API key in
   the login keychain — all before an hour or two of capturing rather than after.
2. **Release notes**, asked for if this version has none, through the shared module in
   `phyphox-android` — so the iOS run writes into that repository too.
3. **Screenshots**, both form factors from **one** build: the Release configuration is built once
   and photographed on the iPhone and the iPad simulator, which the capture creates itself.
4. **The mechanical check** over every plate, the same `verify.py` as on Android; its pure-black
   rule is Android-only, because on iOS pure black is ordinary (dark theme, the camera scene).
5. *(Nothing. The App Store is API-only, so unlike F-Droid nothing of this is committed.)*
6. **The rehearsal.** There is **no server-side one**: App Store Connect has no draft edit that
   can be validated and discarded, so this is the live listing downloaded and compared field by
   field, and the store's screenshots read back against the plates. `subtitle` and `keywords`
   are maintained by hand in App Store Connect and the metadata tree deliberately contains no
   files for them — deliver sets only fields it finds a file for, and an empty file would blank
   them.
7. **The question.** Yes runs the listing upload and then the release-notes upload for the draft
   version — two deliver runs, because the release-notes tree holds nothing but
   `release_notes.txt` so that it cannot drag the listing along. deliver renders an HTML preview
   of each and waits for a yes of its own, so the answer is given three times in all; that is
   deliver's review step, not a bug. Uploading is not releasing: both go live when the version is
   released in App Store Connect, with the build from Xcode.
8. **What is left**, which is the release notes waiting in `phyphox-android`'s git.

Authentication is an App Store Connect **individual** API key restricted to phyphox (§8.2). Team
keys cannot be app-restricted.

### Doing it in pieces

The driver only orders the underlying tools; each keeps its own options, and those are what a
rehearsal or a repair uses.

    tools/store_release.py --skip-capture      # reuse the plates already taken
    tools/store_release.py --no-publish        # stop after the rehearsal
    tools/store_release.py --languages en,de --scenes accelerometer,strobe

    tools/store_screenshots.py --avd phyphox-shot-7in --form-factor sevenInch --apk <apk>
    ../phyphox-docs/tools/screenshots/verify.py ../screenshots/android --form-factor phone
    tools/play_upload.py --text                # rehearsal only; also writes the F-Droid text
    tools/play_upload.py --image-types phoneScreenshots --commit
    tools/play_upload.py --release-notes       # just the block to paste

Narrow a re-upload with `--image-types`: uploading a type *replaces* every image of it, so a full
run would churn images that are already on the store, or mid-review, for nothing.

And on the Mac, likewise:

    tools/store_release.py --skip-capture      # reuse the plates already taken
    tools/store_release.py --no-upload         # stop after the checks
    tools/store_release.py --languages en,de --scenes accelerometer,strobe

    tools/store_screenshots.py --form-factor iphone --build
    tools/store_screenshots.py --form-factor ipad   --app <what --build produced>
    ../phyphox-docs/tools/screenshots/verify.py ../screenshots/ios --form-factor iphone
    tools/appstore_upload.py --diff              # what would change, against the live listing
    tools/appstore_upload.py --verify-screenshots
    tools/appstore_upload.py --upload            # deliver renders a preview and waits for a yes
    tools/appstore_upload.py --release-notes --upload   # the draft's notes, nothing else

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
