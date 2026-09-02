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
         "tenInch": (1600, 2560),
         "iphone": (1320, 2868),
         "ipad": (2064, 2752)}

# The two capture trees are shaped differently, and so are the file names:
#   Android  <locale>/images/<kind>Screenshots/01-main.png
#   iOS      <locale>/iphone-01-main.png
# Apple wants exactly two sizes and scales everything else down from them, so
# there is no per-form-factor directory on that side.
IOS = {"iphone", "ipad"}

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


def scene_of(path, form_factor):
    """The scene id, from either naming scheme. `01-main.png` -> `main`."""
    name = os.path.basename(path)[:-len(".png")]
    if form_factor in IOS:
        name = name[len(form_factor) + 1:]
    return name[3:]                            # past the "NN-" display order


def check(path, form_factor):
    from PIL import Image
    scene = scene_of(path, form_factor)
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

    # ANDROID ONLY. This rule is about the emulator: gfxstream copied the
    # surface with the scissor test still enabled, so everything outside the
    # plot came back as whatever was in the buffer, usually black. A simulator
    # has no such path, and on iOS pure black is ordinary - the dark theme uses
    # it, and the camera scene photographs a dark room. Applied there it flags
    # 63 of 126 iPhone plates and every iPad camera-luminance plate, all of
    # them correct captures (measured 2026-09-02 over the current tree).
    if (form_factor not in IOS and scene not in BLACK_IS_FINE
            and c.get((0, 0, 0))):
        out.append(f"{c[(0, 0, 0)]} pure-black samples - the graph margins used "
                   f"to render like this before the app painted them itself")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("directory")
    ap.add_argument("--form-factor", required=True, choices=sorted(SIZES))
    args = ap.parse_args()

    files, locales = [], set()
    for locale in sorted(os.listdir(args.directory)):
        if args.form_factor in IOS:
            d = os.path.join(args.directory, locale)
            names = [f for f in sorted(os.listdir(d))
                     if f.startswith(args.form_factor + "-")
                     and f.endswith(".png")] if os.path.isdir(d) else []
        else:
            d = os.path.join(args.directory, locale, "images",
                             args.form_factor + "Screenshots")
            names = [f for f in sorted(os.listdir(d))
                     if f.endswith(".png")] if os.path.isdir(d) else []
        if names:
            locales.add(locale)
            files += [os.path.join(d, f) for f in names]
    if not files:
        sys.exit(f"no {args.form_factor} plates under {args.directory}")

    problems = 0
    for f in files:
        for msg in check(f, args.form_factor):
            print(f"  {os.path.relpath(f, args.directory)}: {msg}")
            problems += 1
    print(f"{len(files)} images, {len(locales)} locales, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
