#!/usr/bin/env python3
"""Record the measurement a store screenshot shows, from a real phone.

The screenshots are taken on emulators, because those are the only places the
exact store resolutions exist - but an emulator has nothing to measure. So the
data comes from a phone, once, and is replayed for as long as the experiment
does not change shape.

    record.py --scene accelerometer --base http://127.0.0.1:8080

`--base` is a running phyphox instance with remote access on, i.e. what the lab
driver already sets up (`debug.phyphox.remote` / `-phyphoxRemote`, plus an adb
port forward). The banner that remote access draws does not matter here: this
phone is never photographed.

The result is written to screenshots/data/<scene>.json in /get's own shape,
`{"buffers": {name: [...]}}`, which is also /set's shape - the two are
deliberately the same so a recording round-trips. compose.py then writes those
numbers into the shipped experiment as container `init` values.

Recording is not part of a release run. It happens when a scene is created, or
when the experiment it uses changes enough that the old numbers no longer fit,
and the result is reviewed like any other fixture before it is committed.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose  # noqa: E402

DATA = compose.DATA


def get(base, path, timeout=10):
    with urllib.request.urlopen(base.rstrip("/") + path, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def buffer_names(scene):
    """Which containers this scene wants recorded.

    Explicit rather than "everything /get offers": a screenshot needs the few
    buffers its view reads, and dragging a whole experiment's state along would
    make the fixture unreviewable and the init strings enormous.
    """
    names = scene.get("record")
    if names:
        return list(names)
    raise ValueError(
        f"{scene['id']}: scenes.yml names no buffers to record. Add a "
        f"`record:` list - the containers the scene's view reads.")


def fetch(base, names, timeout=10):
    """One /get for all of them. `null` comes back for every non-finite value,
    which is exactly what compose.format_init writes as NaN."""
    query = "&".join(f"{urllib.parse.quote(n)}=full" for n in names)
    data = get(base, "/get?" + query, timeout)
    buffers = data.get("buffer") or {}
    out = {}
    for n in names:
        entry = buffers.get(n)
        if entry is None:
            raise ValueError(
                f"the experiment has no buffer {n!r} - /get returned "
                f"{sorted(buffers)}. Either the wrong experiment is open or "
                f"scenes.yml is stale.")
        out[n] = entry.get("buffer", [])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scene", required=True)
    ap.add_argument("--base", required=True,
                    help="a running phyphox with remote access, "
                         "e.g. http://127.0.0.1:8080")
    ap.add_argument("--measure", type=float, default=0.0,
                    help="start the experiment, run it this many seconds, stop "
                         "it, then read. Omit to read whatever is on screen, "
                         "which is what you want after measuring by hand.")
    ap.add_argument("--out-dir", default=DATA)
    args = ap.parse_args()

    scenes = compose.load_scenes()
    if args.scene not in scenes:
        sys.exit(f"unknown scene {args.scene!r}; scenes.yml has "
                 f"{', '.join(scenes)}")
    scene = scenes[args.scene]
    if not scene.get("data"):
        sys.exit(f"{args.scene} carries no recording - it is set up from "
                 f"literal init values in scenes.yml")

    try:
        names = buffer_names(scene)
        if args.measure:
            get(args.base, "/control?cmd=start")
            time.sleep(args.measure)
            get(args.base, "/control?cmd=stop")
            time.sleep(0.5)
        buffers = fetch(args.base, names)
    except (urllib.error.URLError, OSError) as e:
        sys.exit(f"cannot reach {args.base}: {e}. Is remote access on and the "
                 f"port forwarded?")
    except ValueError as e:
        sys.exit(str(e))

    empty = [n for n, v in buffers.items() if not v]
    if empty:
        sys.exit(f"nothing recorded in {', '.join(empty)} - the experiment was "
                 f"probably never started. Refusing to write an empty fixture.")

    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, scene["data"])
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"buffers": buffers}, f, indent=1)
        f.write("\n")
    print(f"{out}: " + ", ".join(f"{n} ({len(v)})" for n, v in buffers.items()))
    print("Look at the screenshot it produces before committing this - a "
          "recording is a picture, not a measurement.")


if __name__ == "__main__":
    main()
