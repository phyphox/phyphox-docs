"""Is the BOARD reliable, judged by a central that is not phyphox?

    .venv/bin/python tools/lab/board_check.py [--name "phyphox device"]
                                              [--cycles 8]

Run this BEFORE reporting a BLE fault against either app.

Repeats the same shape the app does - discover, connect, subscribe to the
data characteristic, receive - from this machine's own BlueZ adapter. If a
neutral central gets data on every cycle where the app gets it on half,
the board is doing its job and the fault is in the phone. If this starves
too, the board is the problem and our Bluetooth code is owed an apology.
"""
import asyncio, sys
from bleak import BleakScanner, BleakClient

import argparse

DATA_CHAR = "cddf1002-30f7-4671-8b43-5e40ba53514a"

_ap = argparse.ArgumentParser(description=__doc__)
_ap.add_argument("--name", default="phyphox device",
                 help="what the board advertises as")
_ap.add_argument("--cycles", type=int, default=8)
_args = _ap.parse_args()
NAME, CYCLES = _args.name, _args.cycles

async def one(cycle):
    dev = await BleakScanner.find_device_by_name(NAME, timeout=15.0)
    if dev is None:
        return None, "not advertising"
    got = []
    try:
        async with BleakClient(dev) as client:
            await client.start_notify(DATA_CHAR, lambda _c, d: got.append(d))
            await asyncio.sleep(5.0)
            await client.stop_notify(DATA_CHAR)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    return len(got), None

async def main():
    ok = 0
    for cycle in range(1, CYCLES + 1):
        n, err = await one(cycle)
        if err:
            print(f"  cycle {cycle}: FAILED - {err}", flush=True)
        else:
            ok += n > 0
            print(f"  cycle {cycle}: {n} notifications in 5 s "
                  f"({n/5:.0f} Hz)", flush=True)
        await asyncio.sleep(2)
    print(f"\n{ok}/{CYCLES} cycles received data from a non-phyphox central")

asyncio.run(main())
