# Staged BLE captures

Empty, and meant to stay that way most of the time.

`tools/lab/ble.py --capture-ble-xml` writes an experiment here when the spec check flags it, rather
than into the corpus, because `corpus/valid/` means two things at once: the file validates against
`spec/`, and both apps load it. A library capture can fail the first while passing the second, and
dropping one into `corpus/valid/` anyway breaks the docs build on the next commit.

The eight that waited here were filed on 2026-08-29 as `corpus/invalid/ble-lib-*.phyphox` with
`parser: accepts` — real library output that the apps must keep loading, which is exactly what that
combination records. See `corpus/invalid/expected.yml` for why they stay there even after the
libraries are fixed.

So a file appearing here means a capture found something new. Read `spec_findings()`'s output on it,
decide whether the spec is wrong or the library is, and file it accordingly.

## The same example emits different XML on different boards

Found 2026-08-28, and it is why captures carry the board in their name.

`arduino/connectionParameter` captured from the ESP32 contains

    <value label="myLabel" facor="1">
      <input>CH1</input>
    </value>

and the same example captured from the Nano 33 BLE does not. The library builds its default
experiment per board: `src/boards/phyphoxBLE_ESP32.cpp:289` adds a `Value` element to the view,
`src/boards/phyphoxBLE_NRF52.cpp` adds only the graph. So the Nano's XML is spec-clean while the
ESP32's carries the `facor` typo, purely because only one of them emits the element that has it.

Two consequences. A capture is only meaningful with its board recorded, which is now in the
filename. And a fixture that "changed" between runs may simply have come from the other board — two
files were withdrawn from the corpus over exactly that before the naming was fixed.
