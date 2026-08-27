# Debug stimulus for the BLE bench

`bleDebug.ino` is `randomNumbers` with the library's own debug channel switched
on. Same stimulus as the scenario — `random(0, 100)` every 50 ms — plus:

- `Serial.begin()` and `PhyphoxBLE::begin(&Serial)`, which the library declares
  "for debug purpose" and which enable its `onConnect` / descriptor-write /
  `device disconnected` prints;
- a two-second heartbeat printing `writes`, `PhyphoxBLE::currentConnections` and
  `PhyphoxBLE::isSubscribed`, so the board's own belief about the link can be
  read off while the phone is being driven.

The suite flashes examples **unmodified**; this is not part of a run. It exists
because "no data arrived" is a statement about the phone, and answering it needs
the other end of the link to say what it thinks is happening.

Build it against the library checkout without touching it:

    arduino-cli compile --fqbn esp32:esp32:esp32:PartitionScheme=huge_app \
        --build-property compiler.cpp.extra_flags=-DDEBUG \
        --library ../phyphox-arduino  fixtures/ble/debug

**`-DDEBUG` does not compile as the library stands.** `PhyphoxBLE::begin` calls
`printer->begin(115200)` on a `Print*`, which has no `begin`
(`src/boards/phyphoxBLE_ESP32.cpp`, in `begin(Print*)`), so the whole debug path
fails to build. Deleting that one line makes it compile — the sketch opens the
port itself. That is a library defect for a library session; note it, do not fix
it in passing, and revert any local patch before leaving the checkout.

## What it established (2026-08-27, Pixel 3 + ESP32-D0WDQ6)

On a cycle where the phone collected nothing, the board reported, every two
seconds, throughout:

    [beat] t=61s writes=1212 connections=1 subscribed=1

Connected, subscribed, and still writing at 20 Hz — while the app displayed "The
Bluetooth device is not connected. Experiment can not be started." The link was
never down; only the app's belief about it was.
