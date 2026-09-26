#!/usr/bin/env python3
"""Build the demo experiments the view-element screenshots are taken of.

The documentation of every view element opens with one screenshot of a typical
use. Each scene below is a small experiment with a single view holding just that
element, so a capture needs no navigation and can be cropped to the view's
content. Measurement data is baked in as container `init` values, the same way
the store screenshots avoid the remote interface's banner - the experiment is
never started.

This file is the platform-independent half: it writes the experiments (a bare
.phyphox, or a zip container when a scene needs images) into build/. The capture
lives in the app repositories (phyphox-android/tools/docs_screenshots.py) and
writes docs/assets/screenshots/views/<id>-light.png and <id>-dark.png (.jpg for
the camera preview), which the
pages show with Material's #only-light / #only-dark switch.

    views.py --out build/docs-views          # every scene
    views.py --list                          # the scene ids
"""

import argparse
import io
import json
import math
import os
import zipfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
VERSION = "1.21"


def series(values, digits=4):
    return ",".join(f"{v:.{digits}g}" for v in values)


def oscillation(n=240, t_end=12.0):
    t = [t_end * i / (n - 1) for i in range(n)]
    x = [0.12 * math.exp(-0.18 * ti) * math.cos(2 * math.pi * 0.62 * ti) for ti in t]
    return t, x


def acceleration(n=160, t_end=8.0):
    t = [t_end * i / (n - 1) for i in range(n)]
    ax = [0.8 * math.sin(1.3 * ti) + 0.05 * math.sin(17 * ti) for ti in t]
    ay = [0.4 * math.cos(0.9 * ti) + 0.04 * math.sin(23 * ti) for ti in t]
    az = [9.81 + 0.3 * math.sin(2.1 * ti) + 0.05 * math.cos(19 * ti) for ti in t]
    a = [math.sqrt(x * x + y * y + z * z) for x, y, z in zip(ax, ay, az)]
    return t, ax, ay, az, a


def histogram():
    """Bar edges 0..10 and counts; the last count only closes the last bar."""
    edges = list(range(11))
    counts = [2, 5, 11, 19, 26, 24, 17, 9, 4, 1, 0]
    return edges, counts


def ranking():
    """hbars: y are the bar edges, x the lengths."""
    y = [0, 1, 2, 3, 4, 5]
    x = [9.78, 9.81, 9.79, 9.83, 9.80, 0]
    return x, y


def spectrum(n=301):
    """A line spectrum over sensor pixels, three peaks on a weak background."""
    px = [600 * i / (n - 1) for i in range(n)]
    peaks = [(180, 0.55, 9), (310, 1.0, 7), (470, 0.7, 11)]
    y = [0.04 + 0.02 * math.sin(p / 37) + sum(a * math.exp(-((p - c) / w) ** 2 / 2)
                                              for c, a, w in peaks) for p in px]
    return px, y


def spectrogram(cols=120, rows=60):
    """A rising whistle and its first harmonic over time, as x/y/z for a map."""
    f, t, z = [], [], []
    for r in range(rows):
        ti = 4.0 * r / (rows - 1)
        f0 = 400 + 180 * ti
        for c in range(cols):
            fi = 2000.0 * c / (cols - 1)
            v = (0.02 + math.exp(-((fi - f0) / 60) ** 2)
                 + 0.35 * math.exp(-((fi - 2 * f0) / 80) ** 2))
            f.append(fi)
            t.append(ti)
            z.append(v)
    return f, t, z


def fit_data():
    """Noisy measurements of a falling object and the fitted parabola."""
    tm = [0.05 * i for i in range(13)]
    noise = [0.012, -0.018, 0.006, 0.021, -0.009, -0.015, 0.017, -0.004, 0.011,
             -0.02, 0.008, 0.014, -0.011]
    ym = [1.8 - 0.5 * 9.81 * ti * ti + e for ti, e in zip(tm, noise)]
    tf = [0.6 * i / 59 for i in range(60)]
    yf = [1.8 - 0.5 * 9.81 * ti * ti for ti in tf]
    return tm, ym, tf, yf


# ---------------------------------------------------------------------------
# Images for the scenes that need them. Drawn here rather than committed, so
# the fixtures stay text. Colours work on the light and the dark background.

ORANGE = (255, 126, 34, 255)
GREY = (128, 128, 128, 255)


def _canvas(w, h):
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _png(img):
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


def pendulum_png():
    """A pendulum sketch: suspension, string at an angle, bob, dashed rest line."""
    w, h = 800, 520
    img, d = _canvas(w, h)
    cx, top = w // 2, 60
    d.rectangle([cx - 160, top - 24, cx + 160, top], fill=GREY)
    for i in range(-160, 160, 24):
        d.line([cx + i, top - 24, cx + i + 24, top - 48], fill=GREY, width=4)
    length = 380
    for y in range(top, top + length + 40, 28):
        d.line([cx, y, cx, y + 14], fill=GREY, width=4)
    phi = math.radians(28)
    bx, by = cx + length * math.sin(phi), top + length * math.cos(phi)
    d.line([cx, top, bx, by], fill=ORANGE, width=8)
    d.arc([cx - 150, top - 150, cx + 150, top + 150], 90 - 28, 90, fill=ORANGE, width=6)
    d.ellipse([bx - 44, by - 44, bx + 44, by + 44], fill=ORANGE)
    return _png(img)


def gauge_face_png():
    """Semicircular scale from -135 deg to +135 deg with ticks every 10 %."""
    s = 800
    img, d = _canvas(s, s)
    c, r = s / 2, s * 0.44
    # 0 % at -135 deg (lower left) to 100 % at +135 deg, measured from "up", clockwise
    d.arc([c - r, c - r, c + r, c + r], 135, 405, fill=GREY, width=16)
    d.arc([c - r, c - r, c + r, c + r], 351, 405, fill=ORANGE, width=16)
    for i in range(11):
        a = math.radians(-135 + 27 * i)
        inner = r - (60 if i % 5 == 0 else 36)
        d.line([c + inner * math.sin(a), c - inner * math.cos(a),
                c + (r - 8) * math.sin(a), c - (r - 8) * math.cos(a)],
               fill=GREY, width=10 if i % 5 == 0 else 6)
    d.ellipse([c - 26, c - 26, c + 26, c + 26], fill=GREY)
    return _png(img)


def gauge_needle_png():
    """The needle, same canvas as the face, pointing up from the centre."""
    s = 800
    img, d = _canvas(s, s)
    c = s / 2
    d.polygon([(c - 12, c), (c + 12, c), (c + 3, c - s * 0.36), (c - 3, c - s * 0.36)],
              fill=ORANGE)
    d.ellipse([c - 18, c - 18, c + 18, c + 18], fill=ORANGE)
    return _png(img)


# ---------------------------------------------------------------------------
# The scenes. `containers` maps a container name to its init values (a list,
# or None for an empty one), `view` is the content of the single <view>,
# `resources` names the images a zip container carries. `input` is extra XML
# for the <input> block. `orientation` "landscape" rotates the device for the
# capture, for the one element whose point is what it does with a wide screen.
# `interaction` "picker" makes the capture maximize the graph, enter pick mode
# and tap the point at `pick_at` (fractions of the maximized graph's frame,
# from its top left), so the picture shows the pick popup with the outputs.
# `format` "jpg" is for the camera preview, a photograph that PNG stores at
# ten times the size; everything else is flat UI and stays a lossless PNG.

def scenes():
    t, x = oscillation()
    ta, ax, ay, az, a = acceleration()
    edges, counts = histogram()
    hx, hy = ranking()
    px, spec = spectrum()
    mf, mt, mz = spectrogram()
    tm, ym, tf, yf = fit_data()
    return [
        dict(id="info", page="basics", view="""
<info label="Place the phone flat on the table, start the measurement and give the table a gentle knock. The recording stops automatically after five seconds." />
"""),
        dict(id="separator", page="basics", view="""
<info label="Setup" />
<separator height="0.1" color="ff7e22" />
<info label="Place the phone flat on the table." />
<separator height="1" />
<info label="Measurement" />
<separator height="0.1" color="ff7e22" />
<info label="Start the measurement and knock on the table." />
"""),
        dict(id="value", page="basics",
             containers={"f": [0.6214], "T": [1.6093], "A": [0.1184]}, view="""
<value label="Frequency" unit="Hz" precision="3"><input>f</input></value>
<value label="Period" unit="s" precision="3"><input>T</input></value>
<value label="Amplitude" unit="cm" precision="1" factor="100"><input>A</input></value>
"""),
        dict(id="image", page="basics", resources={"pendulum.png": pendulum_png},
             view="""
<info label="Deflect the pendulum by about 30° and let it swing." />
<image src="pendulum.png" scale="0.7" />
"""),
        dict(id="graph", page="graph", containers={"t": t, "x": x}, view="""
<graph label="Position" labelX="t" unitX="s" labelY="x" unitY="m" partialUpdate="true">
    <input axis="x">t</input>
    <input axis="y">x</input>
</graph>
"""),
        dict(id="graph-bars", page="graph", containers={
                "edges": edges, "counts": counts, "hx": hx, "hy": hy}, view="""
<graph label="Histogram" labelX="Period" unitX="s" labelY="Count" style="vbars" lineWidth="0.8">
    <input axis="x">edges</input>
    <input axis="y">counts</input>
</graph>
<graph label="Measured g per group" labelX="g" unitX="m/s²" labelY="Group" style="hbars" lineWidth="0.6" minX="9.7" scaleMinX="fixed">
    <input axis="x">hx</input>
    <input axis="y">hy</input>
</graph>
"""),
        dict(id="graph-map", page="graph",
             containers={"fmap": mf, "tmap": mt, "zmap": mz}, view="""
<graph label="Spectrogram" labelX="f" unitX="Hz" labelY="t" unitY="s" labelZ="Amplitude" unitZ="a.u." aspectRatio="1.3" style="map" mapWidth="120">
    <input axis="x">fmap</input>
    <input axis="y">tmap</input>
    <input axis="z">zmap</input>
</graph>
"""),
        dict(id="graph-multiple", page="graph",
             containers={"tm": tm, "ym": ym, "tf": tf, "yf": yf}, view="""
<graph label="Free fall" labelX="t" unitX="s" labelY="h" unitY="m">
    <input axis="x" style="dots" lineWidth="3">tm</input>
    <input axis="y">ym</input>
    <input axis="x" color="white">tf</input>
    <input axis="y">yf</input>
</graph>
"""),
        dict(id="graph-picker", page="graph", interaction="picker", pick_at=[0.39, 0.44],
             containers={"px": px, "spec": spec, "cal_x1": None, "cal_lambda1": None,
                         "cal_x2": None, "cal_lambda2": None}, view="""
<graph label="Spectrum" labelX="Pixel" labelY="Intensity" unitY="a.u." pickLabel="Calibrate">
    <input axis="x">px</input>
    <input axis="y">spec</input>
    <output axis="x" label="Calibration point 1">cal_x1</output>
    <output axis="xcal" label="Assigned wavelength in nm">cal_lambda1</output>
    <output axis="x" label="Calibration point 2">cal_x2</output>
    <output axis="xcal" label="Assigned wavelength in nm">cal_lambda2</output>
</graph>
"""),
        dict(id="edit", page="user-input", containers={"m": None, "l": None}, view="""
<edit label="Mass" unit="g" default="250" signed="false"><output>m</output></edit>
<edit label="Length" unit="cm" default="42.5" signed="false"><output>l</output></edit>
"""),
        dict(id="button", page="user-input", containers={"t": None, "x": None}, view="""
<info label="Clears the recorded positions without stopping the measurement." />
<button label="Clear positions">
    <input type="empty" />
    <output>t</output>
    <input type="empty" />
    <output>x</output>
</button>
"""),
        dict(id="toggle", page="user-input", containers={"cont": None, "filt": None}, view="""
<toggle label="Continuous measurement" default="1"><output>cont</output></toggle>
<toggle label="Low-pass filter" default="0"><output>filt</output></toggle>
"""),
        dict(id="slider", page="user-input", containers={"f": None}, view="""
<slider label="Frequency" minValue="100" maxValue="1000" stepSize="10" default="440" precision="0" showValue="true"><output>f</output></slider>
"""),
        dict(id="dropdown", page="user-input", containers={"w": None}, view="""
<dropdown label="Waveform" default="1">
    <output>w</output>
    <map value="0">Sine</map>
    <map value="1">Square</map>
    <map value="2">Sawtooth</map>
</dropdown>
"""),
        dict(id="camera-gui", page="preview", format="jpg",
             containers={"h": None, "t": None},
             input="""
<camera auto_exposure="true" feature="photometric" x1="0.4" x2="0.6" y1="0.4" y2="0.6">
    <output component="hue">h</output>
    <output component="t">t</output>
</camera>
""", view="""
<camera-gui label="Preview" exposure_adjustment_level="3" />
"""),
        dict(id="vertical", page="groups",
             containers={"t": t, "x": x, "f": [0.6214], "T": [1.6093], "A": [0.1184]},
             view="""
<horizontal spacing="0.5">
    <graph label="Position" labelX="t" unitX="s" labelY="x" unitY="m" aspectRatio="1.5" weight="3">
        <input axis="x">t</input>
        <input axis="y">x</input>
    </graph>
    <vertical weight="2" spacing="0.5">
        <value label="f" unit="Hz" precision="3" verticalLayout="true"><input>f</input></value>
        <value label="T" unit="s" precision="3" verticalLayout="true"><input>T</input></value>
        <value label="A" unit="cm" precision="1" factor="100" verticalLayout="true"><input>A</input></value>
    </vertical>
</horizontal>
"""),
        dict(id="horizontal", page="groups", containers={"run": None, "count": None},
             view="""
<info label="Three buttons next to each other:" />
<horizontal spacing="0.5">
    <button label="Start"><input type="value">1</input><output>run</output></button>
    <button label="Stop"><input type="value">0</input><output>run</output></button>
    <button label="Reset"><input type="value">0</input><output>count</output></button>
</horizontal>
"""),
        dict(id="grid", page="groups", orientation="landscape",
             containers={"t": ta, "ax": ax, "ay": ay, "az": az, "a": a}, view="""
<grid maxWidth="1" maxWidthUnit="screen">
    <graph label="x" labelX="t" unitX="s" labelY="x" unitY="m/s²" aspectRatio="3"><input axis="x">t</input><input axis="y">ax</input></graph>
    <graph label="y" labelX="t" unitX="s" labelY="y" unitY="m/s²" aspectRatio="3"><input axis="x">t</input><input axis="y">ay</input></graph>
    <graph label="z" labelX="t" unitX="s" labelY="z" unitY="m/s²" aspectRatio="3"><input axis="x">t</input><input axis="y">az</input></graph>
    <graph label="abs" labelX="t" unitX="s" labelY="a" unitY="m/s²" aspectRatio="3"><input axis="x">t</input><input axis="y">a</input></graph>
</grid>
"""),
        dict(id="stack", page="groups", containers={"percent": [72]},
             resources={"gauge-face.png": gauge_face_png,
                        "gauge-needle.png": gauge_needle_png}, view="""
<stack>
    <image src="gauge-face.png" scale="0.8" />
    <transform>
        <input as="rotate" min="0" max="100" mapMin="-2.35" mapMax="2.35" clamp="true">percent</input>
        <image src="gauge-needle.png" scale="0.8" />
    </transform>
    <value label="" unit="%" size="2" precision="0" align="center"><input>percent</input></value>
</stack>
"""),
    ]


def experiment(scene):
    containers = scene.get("containers", {})
    lines = []
    for name, init in containers.items():
        size = 0
        attr = f' init="{series(init)}"' if init else ""
        lines.append(f'    <container size="{size}"{attr}>{name}</container>')
    view = "\n".join("        " + l if l else l
                     for l in scene["view"].strip("\n").splitlines())
    title = scene["id"]
    inp = scene.get("input", "").strip("\n")
    return f"""<phyphox version="{VERSION}" locale="en">
<title>{title}</title>
<category>Documentation</category>
<description>Screenshot scene for the {title} view element of the phyphox documentation.</description>
<data-containers>
{chr(10).join(lines)}
</data-containers>
<input>
{inp}
</input>
<views>
    <view label="{title}">
{view}
    </view>
</views>
<export />
</phyphox>
"""


def write(scene, out):
    xml = experiment(scene).encode("utf-8")
    res = scene.get("resources")
    if not res:
        path = os.path.join(out, scene["id"] + ".phyphox")
        with open(path, "wb") as f:
            f.write(xml)
        return path
    path = os.path.join(out, scene["id"] + ".zip")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(scene["id"] + ".phyphox", xml)
        for name, draw in res.items():
            z.writestr("res/" + name, draw())
    return path


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join(ROOT, "build", "docs-views"))
    ap.add_argument("--scenes", help="comma separated ids (default: all)")
    ap.add_argument("--list", action="store_true",
                    help="print the scenes as JSON (id, page, file, orientation, format)")
    args = ap.parse_args()
    all_scenes = scenes()
    wanted = args.scenes.split(",") if args.scenes else None
    chosen = [s for s in all_scenes if not wanted or s["id"] in wanted]
    os.makedirs(args.out, exist_ok=True)
    listing = []
    for s in chosen:
        path = write(s, args.out)
        listing.append(dict(id=s["id"], page=s["page"], file=os.path.basename(path),
                            orientation=s.get("orientation", "portrait"),
                            format=s.get("format", "png"),
                            interaction=s.get("interaction"),
                            pick_at=s.get("pick_at")))
    if args.list:
        print(json.dumps(listing, indent=1))
    else:
        for l in listing:
            print(f"  {l['file']}")


if __name__ == "__main__":
    main()
