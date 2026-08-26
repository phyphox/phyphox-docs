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
- `traversal.zip` - the `../evil.phyphox` entry is REJECTED and nothing
  is written outside the extraction directory; the legitimate entry
  still works. This is a security pin (Android's ZipIntentHandler
  guard; iOS must match).
- `partial.bin` - the headerless deflate-plus-descriptor form is
  detected by its trailing PK\x07\x08 signature, rebuilt into a zip and
  loads as container-a. This is the QR/BLE delivery path.

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
