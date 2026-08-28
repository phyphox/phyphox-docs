"""Is the BOARD reliable, judged by a central that is not phyphox?

    .venv/bin/python tools/lab/board_check.py [--name "phyphox device"]
                                              [--cycles 8]

Run this BEFORE reporting a BLE fault against either app.

Repeats the same shape the app does - discover, connect, pull the
experiment over cddf0002 and CHECK it (its declared length, the CRC32 in
its header, and that the stream is one clean run of 20-byte packets),
subscribe to the data characteristic, receive - from this machine's own
BlueZ adapter. If a neutral central gets through
every cycle where the app gets through half, the board is doing its job
and the fault is in the phone. If this starves too, the board is the
problem and our Bluetooth code is owed an apology.

The experiment transfer is here because that is where the suite actually
flakes: on 2026-08-28 twelve of forty-four connects across three phones
failed with "the experiment the device offers did not load within 90 s",
and a control that only counted data notifications could not say anything
about it.

A peripheral can be asked for its experiment in either of two ways, and
assuming one of them makes this tool report a perfectly healthy board as
0/8 (it did, once, before the mistake was caught):

- SUBSCRIBING to cddf0002 is the original trigger and still the default.
- WRITING 0x01 to the experiment control characteristic cddf0003 is a
  later addition (maintainer, 2026-08-28), for peripherals whose BLE
  stack offered no callback on subscription.

Which one a device wants is a property of that implementation, not of the
library it belongs to: inside phyphox-arduino the ESP32 and the NRF52
transfer on the subscription (phyphoxBLE_ESP32.cpp, onSubscribe ->
startTask) while the NINA-B31, the Nano 33 IoT and the STM32 carry a
control characteristic (phyphoxBLE_NanoIOT.cpp,
controlCharacteristicWritten), and phyphox-micropython waits for the
write (phyphoxBLE.py, the _IRQ_GATTS_WRITE branch). Expect either from
anything.

So this does what the app does, which covers both: subscribe, then write
0x01 to cddf0003 if the device offers it (BluetoothExperimentLoader.kt:
"If the control characteristic is present, the device expects us to
initiate the transfer by writing 1"; BluetoothScan.swift says the same).
The board then notifies a 20-byte header - b"phyphox", a big-endian
length, a big-endian checksum - followed by 20-byte chunks of XML, 10 ms
apart, so adding up what arrives is the rest of it.
"""
import asyncio, sys, time, zlib
from bleak import BleakScanner, BleakClient

import argparse

EXP_CHAR = "cddf0002-30f7-4671-8b43-5e40ba53514a"
CTRL_CHAR = "cddf0003-30f7-4671-8b43-5e40ba53514a"
DATA_CHAR = "cddf1002-30f7-4671-8b43-5e40ba53514a"
MAGIC = b"phyphox"

_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--name", default="phyphox device",
                 help="what the board advertises as")
_ap.add_argument("--cycles", type=int, default=8)
_ap.add_argument("--transfer-timeout", type=float, default=30.0,
                 help="how long to wait for the experiment (the app's own "
                      "test waits 90 s, but a board that is going to answer "
                      "answers in seconds)")
_args = _ap.parse_args()
NAME, CYCLES = _args.name, _args.cycles


async def experiment(client, timeout):
    """(declared, received, note). Subscribe to cddf0002 and add up what
    the board sends, which is the transfer the phones time out on."""
    chunks = []
    done = asyncio.Event()
    state = {"declared": None, "crc": None, "oddities": []}

    def on_chunk(_c, data):
        if state["declared"] is None:
            if data[:7] != MAGIC:
                # Not the header we know: keep it, report it, judge later.
                state["declared"] = -1
                chunks.append(bytes(data))
                return
            state["declared"] = int.from_bytes(data[7:11], "big")
            state["crc"] = int.from_bytes(data[11:15], "big")
            return
        # What the app instruments for as well (BluetoothScan.swift): a
        # stream that is not one clean run of 20-byte packets. A second
        # header means the board started the transfer over mid-stream, a
        # short packet anywhere but at the end means one went missing or
        # was split. Both leave the byte count looking right while the
        # payload is wrong, which is why counting bytes is not enough.
        at = sum(len(c) for c in chunks)
        if len(data) == 20 and data[:7] == MAGIC:
            state["oddities"].append(f"a second header at byte {at}")
        elif (len(data) != 20 and state["declared"] > 0
                and at + len(data) < state["declared"]):
            state["oddities"].append(f"a {len(data)}-byte packet at byte {at}")
        chunks.append(bytes(data))
        if state["declared"] > 0 and sum(len(c) for c in chunks) >= state["declared"]:
            done.set()

    await client.start_notify(EXP_CHAR, on_chunk)
    # The app's own order: subscribe first, then ask. A MicroPython board
    # sends nothing until this write arrives; an Arduino board has
    # already started and does not mind it.
    has_ctrl = client.services.get_characteristic(CTRL_CHAR) is not None
    if has_ctrl:
        try:
            await client.write_gatt_char(CTRL_CHAR, b"\x01", response=True)
        except Exception as e:
            return None, 0, f"could not write 0x01 to cddf0003: {e}"
    try:
        await asyncio.wait_for(done.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        pass
    finally:
        try:
            await client.stop_notify(EXP_CHAR)
            if has_ctrl:
                await client.write_gatt_char(CTRL_CHAR, b"\x00",
                                             response=True)
        except Exception:
            pass
    got = sum(len(c) for c in chunks)
    if state["declared"] is None:
        return None, 0, ("nothing on cddf0002 after subscribing"
                         + ("" if has_ctrl else
                            " (and this device offers no cddf0003 to ask "
                            "through)"))
    if state["declared"] == -1:
        return None, got, "first notification was not a phyphox header"
    body = b"".join(chunks)
    if got < state["declared"]:
        return state["declared"], got, "INCOMPLETE"
    # The CRC32 from the header, checked the way both apps check it.
    # Without this a corrupted stream still counts up to the declared
    # length and this tool calls it ok - useless as the control for the
    # stream problem iOS is chasing.
    payload = body[:state["declared"]]
    crc = zlib.crc32(payload) & 0xFFFFFFFF
    note = []
    if crc != state["crc"]:
        note.append(f"CRC MISMATCH (header {state['crc']:#010x}, "
                    f"payload {crc:#010x})")
    if b"<phyphox" not in payload:
        note.append("no <phyphox> in it")
    note += state["oddities"]
    return state["declared"], got, "; ".join(note) if note else "ok"


async def one(cycle):
    dev = await BleakScanner.find_device_by_name(NAME, timeout=15.0)
    if dev is None:
        return None, "not advertising"
    got = []
    try:
        async with BleakClient(dev) as client:
            t0 = time.monotonic()
            declared, received, note = await experiment(
                client, _args.transfer_timeout)
            took = time.monotonic() - t0
            xfer = (f"experiment {received}/{declared} bytes in {took:.1f} s"
                    f" - {note}" if declared else
                    f"experiment: {note} (after {took:.1f} s)")
            await client.start_notify(DATA_CHAR, lambda _c, d: got.append(d))
            await asyncio.sleep(5.0)
            await client.stop_notify(DATA_CHAR)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    return (len(got), xfer, note == "ok"), None


async def main():
    ok = transfers = 0
    for cycle in range(1, CYCLES + 1):
        r, err = await one(cycle)
        if err:
            print(f"  cycle {cycle}: FAILED - {err}", flush=True)
        else:
            n, xfer, xok = r
            ok += n > 0
            transfers += xok
            print(f"  cycle {cycle}: {xfer}; then {n} notifications in 5 s "
                  f"({n/5:.0f} Hz)", flush=True)
        await asyncio.sleep(2)
    print(f"\n{transfers}/{CYCLES} experiment transfers completed, "
          f"{ok}/{CYCLES} cycles received data - from a non-phyphox central")

asyncio.run(main())
