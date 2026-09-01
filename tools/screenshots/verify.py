#!/usr/bin/env python3
"""Check a captured screenshot set before it goes anywhere.

    verify.py <dir> --form-factor phone

`<dir>` is a capture output tree, `<locale>/images/<kind>Screenshots/*.png`.

This exists because the same sweep was written by hand three times during the
Android work and mis-tuned twice - thresholds picked for a phone flagged 67 of
138 tablet plates, every one of them a false positive. Each rule below carries
the reason for its threshold, so the next person tightening one can tell what it
was protecting against.

What it does NOT do is judge whether a screenshot is *good*. It catches files
that are broken or obviously wrong; a plate on the wrong tab, or a graph with
unfortunate data, still needs eyes.
"""

import argparse
import os
import sys
from collections import Counter

SIZES = {"phone": (1080, 1920),
         "sevenInch": (1200, 1920),
         "tenInch": (1600, 2560)}

# Scenes whose plates legitimately contain pure black, and why:
#   tone-generator   light theme - black text on white
#   audio-spectrum   the dark end of the map's colour scale
#   main             the "Contribute to phyphox" icons are black on white, and
#                    the tablet layouts show them where a phone crops them off
BLACK_IS_FINE = {"tone-generator", "audio-spectrum", "main"}

# A plate that is almost one colour has failed to render. The threshold has to
# clear the emptiest legitimate plate: on a 7-inch tablet `strobe` reaches 0.95
# background, because the layout is wider than its content. 0.97 leaves room
# without admitting a blank screen.
BLANK = 0.97


def check(path, form_factor):
    from PIL import Image
    scene = os.path.basename(path)[3:-4]
    out = []
    try:
        im = Image.open(path)
        im.load()                      # a truncated file raises here, not on open
        im = im.convert("RGB")
    except Exception as e:
        return [f"unreadable ({e.__class__.__name__})"]

    want = SIZES[form_factor]
    if im.size != want:
        out.append(f"{im.size[0]}x{im.size[1]}, expected {want[0]}x{want[1]}")

    step = max(im.width // 100, 1)
    c = Counter(im.getpixel((x, y))
                for y in range(150, im.height - 20, step)
                for x in range(0, im.width, step))
    total = sum(c.values())
    top, n = c.most_common(1)[0]
    if n / total > BLANK:
        out.append(f"looks blank: {n / total:.0%} is one colour {top}")

    light = sum(top) > 200
    if light != (scene == "tone-generator"):
        out.append(f"wrong theme: {'light' if light else 'dark'}")

    if scene not in BLACK_IS_FINE and c.get((0, 0, 0)):
        out.append(f"{c[(0, 0, 0)]} pure-black samples - the graph margins used "
                   f"to render like this before the app painted them itself")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("directory")
    ap.add_argument("--form-factor", required=True, choices=sorted(SIZES))
    args = ap.parse_args()

    kind = args.form_factor + "Screenshots"
    files = []
    for locale in sorted(os.listdir(args.directory)):
        d = os.path.join(args.directory, locale, "images", kind)
        if os.path.isdir(d):
            files += [os.path.join(d, f) for f in sorted(os.listdir(d))
                      if f.endswith(".png")]
    if not files:
        sys.exit(f"no {kind} under {args.directory}")

    problems = 0
    for f in files:
        for msg in check(f, args.form_factor):
            print(f"  {os.path.relpath(f, args.directory)}: {msg}")
            problems += 1
    locales = len({f.split(os.sep)[-4] for f in files})
    print(f"{len(files)} images, {locales} locales, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
