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
  2026-08-26; iOS still salvages the rest - `container-traversal-entry`
  - so its test pins the old behavior until it conforms).
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
  answer). A test opening it as a local file must assert the REFUSAL;
  iOS still accepts it from any route (`partial-zip-intake-scope`).

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
