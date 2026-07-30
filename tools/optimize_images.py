#!/usr/bin/env python3
"""Shrink oversized images in docs/assets.

Several images came off the wiki straight from a camera - one is 5260 px wide and
4.5 MB, displayed inline at a few hundred pixels. Git keeps every byte forever, so
they are worth shrinking once rather than carrying at full size indefinitely.

Rules, deliberately conservative:

* Only raster images are touched. PDFs, videos, .phyphox files and sketches are
  left alone - they are content, not illustrations.
* Anything longer than MAX_EDGE on its long side is scaled down to it. 1600 px is
  well above what any page displays.
* JPEG data is re-encoded as JPEG (lossy, quality 82). PNG data is re-encoded as
  PNG (lossless, maximum compression, metadata stripped) so screenshots, diagrams
  and line art keep their crisp edges and any alpha channel.
* A file is only replaced if the saving is worth it. PNG re-encoding is lossless,
  so any saving above MIN_SAVING counts. Re-encoding a JPEG that is *not* being
  resized costs a generation of quality, so that needs MIN_SAVING_LOSSY before it
  is considered - no point trading visible artefacts for ten kilobytes. Both
  thresholds also keep the script idempotent: a second run changes nothing.

File names are left exactly as they are, including the three wiki uploads named
.png that actually contain JPEG data. Renaming them would decouple docs/assets
from the links tools/migrate_wiki.py generates, for a purely cosmetic gain;
browsers sniff the content type regardless.

Requires ImageMagick. Usage:

    python3 tools/optimize_images.py [--dry-run]
"""

import argparse
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "docs", "assets")

MAX_EDGE = 1600
JPEG_QUALITY = 82
MIN_SAVING = 0.10
MIN_SAVING_LOSSY = 0.30


def mime(path):
    return subprocess.run(["file", "-b", "--mime-type", path],
                          capture_output=True, text=True).stdout.strip()


def dimensions(path):
    out = subprocess.run(["identify", "-format", "%w %h", path],
                         capture_output=True, text=True).stdout.split()
    return (int(out[0]), int(out[1])) if len(out) == 2 else (0, 0)


def human(n):
    return f"{n / 1024:.0f} KB" if n < 1024 * 1024 else f"{n / 1024 / 1024:.1f} MB"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    before = after = 0
    changed = []

    for name in sorted(os.listdir(ASSETS)):
        path = os.path.join(ASSETS, name)
        if not os.path.isfile(path):
            continue

        kind = mime(path)
        if kind not in ("image/jpeg", "image/png"):
            before += os.path.getsize(path)
            after += os.path.getsize(path)
            continue

        size = os.path.getsize(path)
        before += size
        w, h = dimensions(path)

        with tempfile.TemporaryDirectory() as tmp:
            suffix = ".jpg" if kind == "image/jpeg" else ".png"
            out = os.path.join(tmp, "out" + suffix)

            cmd = ["convert", path, "-strip"]
            if max(w, h) > MAX_EDGE:
                cmd += ["-resize", f"{MAX_EDGE}x{MAX_EDGE}>"]
            if kind == "image/jpeg":
                cmd += ["-quality", str(JPEG_QUALITY)]
            else:
                cmd += ["-define", "png:compression-level=9"]
            cmd.append(out)

            subprocess.run(cmd, check=True, capture_output=True)
            new_size = os.path.getsize(out)

            resized = max(w, h) > MAX_EDGE
            threshold = (MIN_SAVING if resized or kind == "image/png"
                         else MIN_SAVING_LOSSY)
            if new_size >= size * (1 - threshold):
                after += size
                continue

            nw, nh = dimensions(out)
            changed.append((name, w, h, size, nw, nh, new_size))
            after += new_size
            if not args.dry_run:
                shutil.copy2(out, path)

    for name, w, h, s, nw, nh, ns in changed:
        note = f"{w}x{h} -> {nw}x{nh}" if (w, h) != (nw, nh) else f"{w}x{h}"
        print(f"  {name:40} {note:20} {human(s):>9} -> {human(ns):>9}")

    verb = "would save" if args.dry_run else "saved"
    print(f"\n{len(changed)} files changed, {verb} "
          f"{human(before - after)} ({human(before)} -> {human(after)})")


if __name__ == "__main__":
    main()
