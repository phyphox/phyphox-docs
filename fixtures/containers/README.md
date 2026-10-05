# Container fixtures

The `.phyphox` container forms are contract (see the ecosystem notes:
zip archives with several experiments, bundled `res/` images, and the
headerless partial zip that QR codes and BLE transfers carry) - and
until 2026-08-26 none of them was pinned by any test. These fixtures,
built deterministically from `src/` by `tools/make_containers.py` and
content-verified on every docs build, feed two matrix rows:

## `containers-load` (T0)

Through the platform's REAL intake route (the intent/URL/file handlers,
not a lenient unzip):

- `two-experiments.zip` - unpacks to exactly the two experiments; the
  chooser path offers both; each loads.
- `with-resource.zip` - the experiment loads and its resource is
  available to the image element.
- `traversal.zip` - the whole archive is REFUSED: an entry pointing
  outside the extraction directory is evidence of tampering, so nothing
  is extracted and nothing opens, not even the legitimate entry (ruled
  2026-08-26).
- `partial.bin` - the headerless STORED-plus-descriptor form is
  detected by its trailing PK\x07\x08 signature, rebuilt into a zip and
  loads as container-a. This is the QR/BLE delivery path. Stored, not
  deflated: both apps synthesize a local header with compression
  method 0, so a deflated payload loads nowhere - the fixture carried
  one until 2026-08-26 and both app suites had to hand-build their own
  payload; with the corrected fixture they can consume it directly.
  The form is accepted ONLY from the QR scanner and the Bluetooth
  transfer (ruled 2026-08-26 - those are the low-bandwidth paths that
  justify it; elsewhere a file nobody can inspect or edit is the wrong
  answer), so a test opening it as a local file asserts the REFUSAL.

## `saved-state-load` (T0)

`saved-state.zip` is the saved-state container of `docs/saved-states.md`
(phyphox 1.3.0), built from `src/saved-state.phyphox` with the data in
`STATE_DATA` of `tools/make_containers.py`. Through the real intake route
it must restore the state, not open the plain experiment:

- the list shows it under "Saved states" as "Fixture state" (from
  `meta/state.csv`), the experiment's own title as the subtitle;
- `t` holds 0, 0.5, 1, 1.5 and `x` holds 1, NaN, -2.5, +Infinity (binary
  values survive, which the legacy text form could not promise);
- `calibration` holds 9.81 and is marked filled, so the analysis of a
  static buffer does not run again;
- `empty` is empty although its file exists; `max x (m/s²)` holds 7, the
  state replacing its `init="1,2,3"`, located through `data/index.csv`
  since its name is no entry name;
- the time reference has START at experiment time 0 / system time
  1759650000.000 s and PAUSE at 1.5 / 1759650001.500 s;
- the image element gets `res/pic.png`.

The same row keeps `corpus/generated/events-state.phyphox` loading as a
legacy state (title from `state-title`, events from the block, data from
`init`), and asserts that a container whose `data/index.csv` count does
not match the file size is refused.

## `saved-state-write` (T0)

Writing the state of a running experiment and reading it back through the
same code yields the same buffers, static flags, time reference and title;
the written container has the entry set and the CSV dialect of the docs
page (comma, dot, quoted strings, LF), `experiment.phyphox` byte-identical
to the source, and only the referenced resources under `res/`. Saving the
state of a legacy state copies its experiment file as is, `state-title`,
`events` and `init` data included.

## `save-to-collection` (T1)

The save flow the auto-confirm switch deliberately declines, driven by
UI automation (Espresso / XCUITest) accepting the offer:

- open `with-resource.zip` externally, ACCEPT saving to the collection;
- the collection gains the entry; the resource is extracted into the
  per-experiment folder named by the hex CRC32 of the experiment file;
- reopening the saved entry from the collection works and the image
  element has its image;
- open `two-experiments.zip`, save BOTH via the picker; both appear and
  reopen.

Deleting the saved entries at the end keeps the test hermetic.
