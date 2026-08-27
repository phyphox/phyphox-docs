# Debug stimulus for the BLE bench

`bleDebug.ino` is `randomNumbers` with the library's own debug channel switched
on. Same stimulus as the scenario — `random(0, 100)` every 50 ms — plus:

- `Serial.begin()` and `PhyphoxBLE::begin(&Serial)`, which the library declares
  "for debug purpose" and which enable its `onConnect` / descriptor-write /
  `device disconnected` prints;
- a two-second heartbeat printing what the **stack** holds: the server's
  connected count and the 0x2902 descriptor on the data characteristic — the two
  things `BLECharacteristic::notify()` itself checks before sending. The
  library's `currentConnections` and `isSubscribed` are printed beside them, for
  comparison only.

That distinction is the whole point of the sketch, and it was nearly got wrong
here. The library's flags are its own bookkeeping, not the link's state:
`isSubscribed` is never cleared on disconnect, and `write()` notifies
unconditionally without consulting either flag, so `writes=1212 subscribed=1`
says nothing whatever about whether a packet left the board. Measured between
two cycles:

    [beat] t=83s writes=1662 connected=0 cccd=0x0000  (library says connections=0 subscribed=1)

Nothing connected, notifications disabled, and the library still claiming a
subscription. Read the CCCD, not the flag.

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
seconds, throughout the failure:

    [beat] t=53s writes=1048 connected=1 cccd=0x0100  (library says connections=1 subscribed=1)

`connected=1` is the server's connected count and `cccd=0x0100` is the client
configuration descriptor with notifications enabled — precisely the two guards
`notify()` applies, so every write was going out on the air. Meanwhile the app
displayed "The Bluetooth device is not connected. Experiment can not be
started." and its buffers stayed empty.

The link was up, the subscription was in place at the stack level, and the
peripheral was transmitting. Only the app's belief about it was wrong.
