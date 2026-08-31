#!/usr/bin/env python3
"""Repair the black graph margins an Android emulator produces.

A phyphox graph draws into a TextureView. On a real phone the area around the
plot - where the axis labels sit - shows the app's background; on the emulator
it comes out pure black, while the plot interior is correct. Measured
2026-08-31 and confirmed by the maintainer as emulator-only: phones have
rendered it correctly for years.

It is not the software rasteriser (`-gpu swiftshader_indirect` and `-gpu host`
give identical pixels) and it is not what the app's code says should happen -
`PlotRenderer.drawFrame` clears the whole surface to an opaque background with
the scissor test disabled, and `GraphView` paints no background at all. The
likely explanation, and the maintainer's own, is that those margins are in fact
transparent and the emulator composites transparency over the view behind it as
black instead of showing it. Unproven, and it does not change the repair.

**This compensates for the capture environment; it does not retouch the app.**
The distinction is the whole justification, so keep it narrow:

* only pixels that are EXACTLY black are touched - a graph legitimately draws
  curves, grid lines, labels and a background, none of which is #000000;
* only inside the `graph_frame` rectangles that `uiautomator dump` reports, so
  the camera preview (also a TextureView, and legitimately full of black) is
  never touched;
* the replacement colour is read off the page beside each frame rather than
  hardcoded, so it follows the app's theme instead of asserting one.

If a future app version renders these margins correctly on the emulator too,
this becomes a no-op and should be deleted rather than kept "just in case".

    fix_emulator_graphs.py shot.png ui.xml [-o out.png]
"""

import argparse
import re
import sys
from collections import Counter

FRAME_ID = "de.rwth_aachen.phyphox:id/graph_frame"
BLACK = (0, 0, 0)


def graph_frames(dump_xml):
    """The graph blocks' rectangles, from a uiautomator dump."""
    pattern = (r'resource-id="' + re.escape(FRAME_ID)
               + r'"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"')
    return [tuple(map(int, m.groups()))
            for m in re.finditer(pattern, dump_xml)]


def page_color(im, rect, margin=12):
    """The app background beside a frame - the colour the margins should be.

    Sampled rather than hardcoded: the app has a light theme too, and a
    screenshot run should not have to be told which one it is looking at.
    """
    l, t, r, b = rect
    w, h = im.size
    votes = Counter()
    for y in range(t, b, 8):
        for x in (l - margin, r + margin):
            if 0 <= x < w and 0 <= y < h:
                votes[im.getpixel((x, y))] += 1
    if not votes:
        raise ValueError("no page pixels beside the graph frame to sample")
    return votes.most_common(1)[0][0]


def repair(im, frames):
    """Returns (image, pixels repaired). The image is modified in place."""
    px = im.load()
    fixed = 0
    for rect in frames:
        bg = page_color(im, rect)
        if bg == BLACK:
            raise ValueError(
                "the page beside a graph is itself black - refusing to guess "
                "what these margins should be")
        l, t, r, b = rect
        for y in range(max(t, 0), min(b, im.size[1])):
            for x in range(max(l, 0), min(r, im.size[0])):
                if px[x, y] == BLACK:
                    px[x, y] = bg
                    fixed += 1
    return im, fixed


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("shot")
    ap.add_argument("dump", help="uiautomator dump of the same screen")
    ap.add_argument("-o", "--out", help="default: overwrite the shot")
    args = ap.parse_args()

    from PIL import Image
    im = Image.open(args.shot).convert("RGB")
    with open(args.dump, encoding="utf-8", errors="replace") as f:
        frames = graph_frames(f.read())
    if not frames:
        print(f"{args.shot}: no graph on this screen, nothing to repair")
        return
    im, fixed = repair(im, frames)
    out = args.out or args.shot
    im.save(out)
    total = im.size[0] * im.size[1]
    print(f"{out}: {len(frames)} graph frame(s), {fixed} px repaired "
          f"({100.0 * fixed / total:.1f}% of the screen)")


if __name__ == "__main__":
    main()
