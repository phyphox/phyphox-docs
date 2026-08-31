#!/usr/bin/env python3
"""Build the experiment file a store screenshot is taken of.

The screenshots must show the experiments the app actually ships, on a device
that is NOT running the remote interface - its banner would be in every one of
them (../STORE-RELEASE-PLAN.md, section 4). So the recorded measurement cannot
be pushed in with /set; it is baked into a copy of the shipped file as
container `init` values, and the host serves that copy over HTTP.

The copy is generated from the current shipped file on every run and is build
output, never committed. What keeps it from becoming a parallel universe of
experiment files is check(): it re-reads the result and fails unless the ONLY
differences from the shipped file are `init` attributes on containers the scene
names, plus - when --reorder-views is used - the order of the <view> elements.
Anything else is a bug in this script, and the run stops.

    compose.py --scene accelerometer --collection <dir> --out build/

`--collection` is a checkout of phyphox-experiments, i.e.
phyphox-android/app/src/main/assets/experiments or phyphox-ios/phyphox-experiments.
Use the one from the branch being released, which is the whole point: a
translation or an edit that landed on development shows up in the screenshots
without anyone remembering to refresh anything.

Views are named by label rather than index, because an index silently points at
a different view when one is inserted and a label does not. resolve_view()
turns the label into the index the app's -phyphoxView / debug.phyphox.view seam
takes, and raises if no view carries it.
"""

import argparse
import copy
import json
import os
import sys

from lxml import etree

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     "..", ".."))
SCENES = os.path.join(ROOT, "screenshots", "scenes.yml")
DATA = os.path.join(ROOT, "screenshots", "data")


def load_scenes(path=SCENES):
    import yaml
    with open(path, encoding="utf-8") as f:
        return {s["id"]: s for s in (yaml.safe_load(f) or {}).get("scenes", [])}


def _containers(tree):
    """Every <container> by name, namespace-agnostically."""
    out = {}
    for el in tree.iter():
        # iter() also yields comments and processing instructions, whose .tag
        # is a callable rather than a name
        if not isinstance(el.tag, str) or etree.QName(el).localname != "container":
            continue
        name = (el.text or "").strip()
        if name:
            out[name] = el
    return out


def _views(tree):
    """The <view> elements under <views>, in document order."""
    out = []
    for el in tree.iter():
        if not isinstance(el.tag, str) or etree.QName(el).localname != "view":
            continue
        parent = el.getparent()
        if parent is not None and isinstance(parent.tag, str) \
                and etree.QName(parent).localname == "views":
            out.append(el)
    return out


def resolve_view(tree, label):
    """The index of the view carrying `label`, for the app's view seam."""
    views = _views(tree)
    for i, v in enumerate(views):
        if v.get("label") == label:
            return i
    raise ValueError(
        f"no view labelled {label!r} - the file has "
        f"{[v.get('label') for v in views]}. Either the experiment was "
        f"changed or scenes.yml is out of date; do not guess an index.")


def format_init(values):
    """A float list the way the format wants it: comma-separated, with the
    lexical spellings for the non-finite values a buffer may hold.

    /get writes null for every non-finite value, so a recording round-trips
    through this without the caller having to think about NaN.
    """
    out = []
    for v in values:
        if v is None:
            out.append("NaN")
        elif isinstance(v, str):
            out.append(v)
        elif v != v:
            out.append("NaN")
        elif v == float("inf"):
            out.append("Infinity")
        elif v == float("-inf"):
            out.append("-Infinity")
        else:
            out.append(repr(float(v)) if v % 1 else str(int(v)))
    return ",".join(out)


def scene_values(scene, data_dir=DATA):
    """The container -> values mapping a scene injects, from its recording
    and its literal init block."""
    values = {}
    if scene.get("data"):
        path = os.path.join(data_dir, scene["data"])
        with open(path, encoding="utf-8") as f:
            recorded = json.load(f)
        buffers = recorded.get("buffers", recorded)
        if not isinstance(buffers, dict):
            raise ValueError(f"{path}: expected /get's shape, "
                             f"{{'buffers': {{name: [...]}}}}")
        values.update(buffers)
    values.update(scene.get("init") or {})
    return values


def compose(scene, collection, reorder_views=False, data_dir=DATA):
    """Return (bytes of the composed file, view index, list of touched names)."""
    path = os.path.join(collection, scene["experiment"])
    parser = etree.XMLParser(remove_blank_text=False)
    tree = etree.parse(path, parser)
    root = tree.getroot()

    view = resolve_view(root, scene["view"])

    values = scene_values(scene, data_dir)
    containers = _containers(root)
    missing = sorted(set(values) - set(containers))
    if missing:
        raise ValueError(
            f"{scene['id']}: {scene['experiment']} has no container(s) "
            f"{', '.join(missing)}. The experiment changed, or the recording "
            f"is stale - re-record rather than editing this by hand.")
    for name, vals in values.items():
        containers[name].set("init", format_init(vals))

    if reorder_views and view != 0:
        views = _views(root)
        parent = views[0].getparent()
        wanted = views[view]
        parent.remove(wanted)
        parent.insert(list(parent).index(views[0]), wanted)
        view = 0

    return (etree.tostring(root, encoding="utf-8", xml_declaration=True),
            view, sorted(values))


def check(original_path, composed, touched, reordered):
    """Fail unless the only differences are the init attributes we set.

    Both trees are normalised by dropping `init` from every container the scene
    touched (and, when views were reordered, by sorting the views by label)
    and then compared as canonical XML. What that leaves is a genuine
    difference in structure, text or any other attribute - i.e. a bug here.
    """
    def normalise(tree):
        t = copy.deepcopy(tree)
        for name, el in _containers(t).items():
            if name in touched and "init" in el.attrib:
                del el.attrib["init"]
        if reordered:
            views = _views(t)
            if views:
                parent = views[0].getparent()
                for v in sorted(views, key=lambda v: v.get("label") or ""):
                    parent.remove(v)
                    parent.append(v)
        return etree.tostring(t, method="c14n2", strip_text=True)

    before = normalise(etree.parse(original_path).getroot())
    after = normalise(etree.fromstring(composed))
    if before != after:
        raise ValueError(
            "the composed file differs from the shipped one by more than the "
            "init values this scene sets. That is a bug in compose.py - the "
            "screenshots are supposed to show the shipped experiment.")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--scene", required=True)
    ap.add_argument("--collection", required=True,
                    help="a phyphox-experiments checkout")
    ap.add_argument("--out", default="build")
    ap.add_argument("--reorder-views", action="store_true",
                    help="put the wanted view first instead of relying on the "
                         "app's view seam - for builds that predate it")
    args = ap.parse_args()

    scenes = load_scenes()
    if args.scene not in scenes:
        sys.exit(f"unknown scene {args.scene!r}; scenes.yml has "
                 f"{', '.join(scenes)}")
    scene = scenes[args.scene]
    if scene.get("kind") == "collection":
        sys.exit(f"{args.scene} is the collection screen - it has no "
                 f"experiment file to compose")

    composed, view, touched = compose(scene, args.collection,
                                      args.reorder_views)
    check(os.path.join(args.collection, scene["experiment"]), composed,
          touched, args.reorder_views)

    os.makedirs(args.out, exist_ok=True)
    out = os.path.join(args.out, f"{args.scene}.phyphox")
    with open(out, "wb") as f:
        f.write(composed)
    print(f"{out}: view {view} ({scene['view']}), "
          f"{len(touched)} container(s) set"
          + (f" - {', '.join(touched)}" if touched else ""))


if __name__ == "__main__":
    main()
