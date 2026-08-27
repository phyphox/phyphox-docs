# Staged BLE captures

Experiment XML taken off a phone that received it from a board
(`tools/lab/run.py --suites ble --capture-ble-xml`), held here because the
spec check flags it and where it belongs is a decision, not a default.

`corpus/valid/` means two things at once: the file validates against
`spec/`, and both apps load it. A library capture can fail the first while
passing the second, and dropping one into `corpus/valid/` anyway would
break the docs build on the next commit.

What is here now, and why:

- `arduino-getSensorDataFromSmartphone.phyphox`
- `arduino-getSystemAndEventTime.phyphox`

Both carry `facor="1"` on their `<value>` view elements — a typo for
`factor`, emitted by the library itself (`phyphox-arduino`
`src/view_elements/value.cpp:58` and, identically, `phyphox-micropython`
`phyphoxBLE/experiment.py:575`). It is harmless: the value written is the
attribute's own default, and both parsers ignore unknown attributes, so
nothing misbehaves. But it is real output that released apps must keep
loading, which is precisely what `corpus/invalid/` with `parser: accepts`
records.

Moving them there is a classification decision and the maintainer's call —
and it is worth making after the libraries are next touched, since a fixed
library would make these captures clean and put them in `corpus/valid/`
instead.

## The same example emits different XML on different boards

Found 2026-08-28, and it is why captures carry the board in their name.

`arduino/connectionParameter` captured from the ESP32 contains

    <value label="myLabel" facor="1">
      <input>CH1</input>
    </value>

and the same example captured from the Nano 33 BLE does not. The library builds
its default experiment per board: `src/boards/phyphoxBLE_ESP32.cpp:289` adds a
`Value` element to the view, `src/boards/phyphoxBLE_NRF52.cpp` adds only the
graph. So the Nano's XML is spec-clean while the ESP32's carries the `facor`
typo, purely because only one of them emits the element that has it.

Two consequences. A capture is only meaningful with its board recorded, which
is now in the filename. And a fixture that "changed" between runs may simply
have come from the other board — two files were withdrawn from the corpus over
exactly that before the naming was fixed.
