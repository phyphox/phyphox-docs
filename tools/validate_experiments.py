#!/usr/bin/env python3
"""Validate real .phyphox files against spec/*.yml.

    python3 tools/validate_experiments.py <directory-of-phyphox-files> [...]

The specification was written by reading two parsers - the process that has been
wrong repeatedly, and wrong specifically about defaults, requiredness and which
values are allowed. This runs it over real experiment files, which is the
cheapest available test of several hundred assertions at once.

**A finding is not automatically a bug in the file.** Every mismatch means either
the file is wrong or the spec is, and the second is at least as likely. The point
is to have the list.

Two of the decisions already taken need exactly this check before they can ship:
making iOS validate output components can stop a file loading that loads today,
and removing camera/threshold and edit/editable wants a search of the collection
first. Both are reported here.

What is checked, in order of how much it can be trusted:

  * element names, against the children the spec models for each parent;
  * attribute names, against the attributes the spec models for that element;
  * enumerated values, against the allowed set (case-insensitively, per the
    enum-case-insensitive rule);
  * analysis module slots: whether `as` is present where the spec says it is
    required, whether counts fall within min/max, and whether type="value" or
    type="empty" is used on a slot that allows it;
  * input module output components, the same way.
"""

import argparse
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET


def normalize_namespace(root):
    """Reproduce the apps' namespace handling.

    Android takes the ROOT element's namespace - none, or a default xmlns like
    http://phyphox.org/xml - as the document's namespace, and skips tags from
    any other namespace entirely (editor annotations, most commonly). Both
    apps also ignore namespaced attributes such as editor:uuid. Without this,
    every namespaced file in the wild reports as one big parse failure.
    """
    ns = root.tag[1:root.tag.index("}")] if root.tag.startswith("{") else ""
    prefix = "{" + ns + "}" if ns else ""

    def walk(node):
        for a in [a for a in node.attrib if a.startswith("{")]:
            del node.attrib[a]
        kept = []
        for c in node:
            if isinstance(c.tag, str) and c.tag.startswith(prefix) and (
                    prefix or not c.tag.startswith("{")):
                c.tag = c.tag[len(prefix):]
                walk(c)
                kept.append(c)
        node[:] = kept

    if prefix:
        root.tag = root.tag[len(prefix):]
    walk(root)
    return root

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "spec")

import generate_validators as _gv
NUMBER_LEX = {
    "integer": re.compile(_gv.INT_LEX),
    "float": re.compile(_gv.FLOAT_LEX),
    "float-list": re.compile(_gv.FLOAT_LIST_LEX),
}


def load_spec():
    elements, common, slots, components = {}, {}, {}, {}
    for fn in sorted(os.listdir(SPEC)):
        if not fn.endswith(".yml") or fn == "rules.yml":
            continue
        doc = yaml.safe_load(open(os.path.join(SPEC, fn), encoding="utf-8")) or {}
        for group, items in (doc.get("common") or {}).items():
            key = ("input" if "input" in group else
                   "output" if "output" in group else
                   "module" if "module" in group else
                   "view" if "view" in group else None)
            if key:
                common.setdefault(key, {})
                for i in items or []:
                    common[key][i["name"]] = i
        for el in doc.get("elements") or []:
            key = (el.get("parent"), el["name"])
            entry = elements.setdefault(key, {"attrs": {}, "children": set(),
                                              "patterns": []})
            for a in el.get("attributes") or []:
                if a.get("name_pattern"):
                    # dynamically numbered names like mapColorN: any attribute
                    # matching the pattern is this one
                    entry["patterns"].append((re.compile(a["name_pattern"]), a))
                else:
                    entry["attrs"][a["name"]] = a
            entry["children"] |= set(el.get("children") or [])
            # The element-level constraints the published validators are
            # generated from. They were read by generate_validators only,
            # so a file whose sole defect was one of these validated
            # cleanly here while the RELAX NG and Schematron rejected it -
            # two consumers of one spec disagreeing, which is the thing
            # this spec exists to prevent. Found 2026-08-29, when 13
            # corpus candidates could not be filed because of it.
            for field in ("required", "content_required"):
                if el.get(field):
                    entry[field] = el[field]
            entry["unique_attrs"] = [a["name"] for a in el.get("attributes") or []
                                     if a.get("unique_among_siblings")]
            entry["bounds"] = {a["name"]: a["exclusive_minimum"]
                               for a in el.get("attributes") or []
                               if "exclusive_minimum" in a}
            o = el.get("outputs")
            if isinstance(o, dict):
                entry["children"].add("output")
                components[key] = o
            elif isinstance(o, list):
                slots.setdefault(key, {})["output"] = o
                entry["children"].add("output")
            if isinstance(el.get("inputs"), list):
                slots.setdefault(key, {})["input"] = el["inputs"]
                entry["children"].add("input")
    return elements, common, slots, components


class Report:
    def __init__(self):
        self.items = collections.defaultdict(list)   # kind -> [(file, detail)]

    def add(self, kind, path, detail):
        self.items[kind].append((path, detail))


def check_required_children(node, parent_name, spec, rep, path, fname):
    """What the spec says a parent cannot be without.

    `required: base-locale` is the softer form: the element must exist for
    the experiment's base language, which a translation block for that
    language may supply instead - light.phyphox in the shipped collection
    has no root <title> and takes it from <translation locale="en">.
    """
    for (parent, name), entry in spec.items():
        if parent != parent_name or not entry.get("required"):
            continue
        if node.find(name) is not None:
            continue
        if entry["required"] == "base-locale":
            base = node.get("locale") or "en"
            if any(t.get("locale") == base and t.find(name) is not None
                   for t in node.findall("translations/translation")):
                continue
            rep.add("missing required element", fname,
                    f"{path}<{parent_name}>: no <{name}> for the base "
                    f"language ({base})")
        else:
            rep.add("missing required element", fname,
                    f"{path}<{parent_name}>: no <{name}>")


def check_unique_children(node, spec, rep, path, fname):
    """Attributes the spec marks unique among siblings - a link label is
    the key its translation is matched on, so two links cannot share one.
    Checked from the parent because ElementTree nodes cannot see upwards.
    """
    for child in node:
        entry = spec.get((node.tag, child.tag))
        for an in (entry or {}).get("unique_attrs") or []:
            mine = child.get(an)
            if mine is None:
                continue
            same = [c for c in node
                    if c.tag == child.tag and c.get(an) == mine]
            if len(same) > 1 and same[0] is child:
                rep.add("duplicate attribute value", fname,
                        f"{path}<{node.tag}>/<{child.tag}>: {an}=\"{mine}\" "
                        f"appears {len(same)} times among its siblings")


def check_element(node, parent_name, spec, common, slots, components, rep, path, fname):
    key = (parent_name, node.tag)
    entry = spec.get(key)
    if entry is None:
        if node.tag in ("input", "output") and any(
                k[1] == parent_name for k in list(slots) + list(components)):
            entry = {"attrs": {}, "children": set(), "patterns": []}   # described by common: + slots
        else:
            rep.add("unknown element", fname,
                    f"{path}: <{node.tag}> not modelled under <{parent_name}>")
            return

    known = dict(entry["attrs"])
    if node.tag in ("input", "output") and parent_name:
        known.update(common.get(node.tag, {}))
    # every analysis module accepts the shared module attributes
    if parent_name == "analysis":
        known.update(common.get("module", {}))
    # every view element accepts the shared label/visibility attributes
    if parent_name == "view":
        known.update(common.get("view", {}))
    ckey = next((k for k in components if k[1] == parent_name), None)
    if node.tag == "output" and ckey:
        c = components[ckey]
        if c.get("attribute"):
            known.setdefault(c["attribute"], {"name": c["attribute"]})

    if entry.get("content_required") and not (node.text or "").strip():
        rep.add("empty element", fname,
                f"{path}<{node.tag}>: needs a value, and is empty")
    for an, lo in (entry.get("bounds") or {}).items():
        raw = node.get(an)
        if raw is None:
            continue
        try:
            if float(raw) <= lo:
                rep.add("value out of range", fname,
                        f"{path}<{node.tag}>: {an}=\"{raw}\" must be "
                        f"greater than {lo}")
        except ValueError:
            pass          # a non-numeric value is the numeric check's business

    for attr, value in node.attrib.items():
        spec_a = known.get(attr)
        if spec_a is None:
            spec_a = next((a for rx, a in entry.get("patterns") or []
                           if rx.fullmatch(attr)), None)
        if spec_a is None:
            rep.add("unknown attribute", fname, f"{path}<{node.tag}>: {attr}=\"{value}\"")
            continue
        allowed = spec_a.get("values")
        if allowed and value.lower() not in {str(v).lower() for v in allowed}:
            rep.add("bad enum value", fname,
                    f"{path}<{node.tag}> {attr}=\"{value}\" not in {allowed}")
        # numeric and boolean syntax, per the number-invalid-value rule
        # (decided 2026-08-24) and the boolean extension of
        # enum-invalid-value. The lexes come from generate_validators so
        # this checker and the published grammar cannot disagree.
        kind = spec_a.get("type")
        if kind == "boolean" and value.lower() not in ("true", "false"):
            rep.add("bad boolean value", fname,
                    f"{path}<{node.tag}> {attr}=\"{value}\"")
        elif kind in NUMBER_LEX and not NUMBER_LEX[kind].fullmatch(value):
            rep.add("bad numeric value", fname,
                    f"{path}<{node.tag}> {attr}=\"{value}\" is not "
                    + ("a comma-separated list of numbers"
                       if kind == "float-list" else f"a valid {kind}"))

    # required attributes must be present (found missing 2026-08-24: the
    # generated RELAX NG checked this while nothing here did)
    for aname, a in entry.get("attrs", {}).items():
        if a.get("required") and aname not in node.attrib:
            rep.add("missing required attribute", fname,
                    f"{path}<{node.tag}>: {aname}")

    # Both parsers hard-require credentials for the TLS MQTT services
    # ("password must be set for the mqtts/json service" - NetworkService
    # setup on Android, the network handler on iOS), found 2026-08-24 when a
    # credential-less corpus fixture failed to load on Android. The spec
    # cannot express conditional requiredness, so it lives here.
    if node.tag == "connection":
        service = (node.get("service") or "").lower()
        if service.startswith("mqtts"):
            for cred in ("username", "password"):
                if not node.get(cred):
                    rep.add("missing mqtts credential", fname,
                            f"{path}<connection service=\"{service}\">: "
                            f"{cred} is required for TLS MQTT")

    # The graph element's dataset pairing (decided 2026-08-20, amended the
    # same day; see docs/file-format/views/graph.md and spec/views.yml): with
    # exactly as many x as y inputs they pair 1-on-1 in order; with fewer x
    # than y, each y uses the most recent preceding x (or an index axis) and
    # any x no y uses - trailing or shadowed - is an error. Several shipped
    # Bluetooth experiments rely on the equal-count y-then-x form, which is
    # why this is validated here rather than assumed.
    if node.tag == "graph":
        seq = [(c.get("axis") or "").lower() for c in node
               if c.tag.split("}")[-1] == "input"]
        seq = [a for a in seq if a in ("x", "y")]
        nx, ny = seq.count("x"), seq.count("y")
        if nx != ny:
            used, last = set(), None
            for k, a in enumerate(seq):
                if a == "x":
                    last = k
                elif last is not None:
                    used.add(last)
            xpos = 0
            for k, a in enumerate(seq):
                if a == "x":
                    xpos += 1
                    if k not in used:
                        rep.add("unused graph x input", fname,
                                f"{path}<graph>: x input {xpos} of {nx} is "
                                f"used by no y input ({ny} y inputs)")

    check_unique_children(node, spec, rep, path, fname)
    for child in node:
        check_element(child, node.tag, spec, common, slots, components, rep,
                      f"{path}<{node.tag}>/", fname)


ROOT_ONCE = ("title", "state-title", "category", "icon", "color",
             "description")


def check_root_once(root, rep, fname):
    """The root's metadata children may appear at most once (rule
    duplicate-metadata-last-wins in spec/rules.yml): apps tolerate a legacy
    duplicate - the last occurrence wins - but nothing may write one, so a
    duplicate is an authoring error."""
    counts = collections.Counter(ch.tag for ch in root)
    for tag in ROOT_ONCE:
        if counts[tag] > 1:
            rep.add("duplicate metadata element", fname,
                    f"<phyphox>: {tag} appears {counts[tag]} times")


def check_slots(node, slots, components, rep, fname):
    """Analysis module slots and input-module output components."""
    for module, kinds in ((n.tag, slots.get(n.tag)) for n in node.iter() if n.tag in slots):
        pass  # handled below per occurrence

    def owner(d, tag, parent_tag):
        return d.get((parent_tag, tag))

    for grandparent in node.iter():
      for parent in grandparent:
        skey = (grandparent.tag, parent.tag)
        # analysis module slots
        if skey in slots:
            for kind, defs in slots[skey].items():
                bydef = {d["name"]: d for d in defs}
                seen = collections.Counter()
                for child in parent:
                    if child.tag != kind:
                        continue
                    as_name = child.get("as")
                    if as_name is None:
                        # is any slot willing to take an unnamed tag?
                        if not any(not d.get("as_required", True) for d in defs):
                            rep.add("missing required as", fname,
                                    f"<{parent.tag}>/<{kind}> has no as attribute; "
                                    f"every slot requires one ({sorted(bydef)})")
                        continue
                    d = bydef.get(as_name)
                    if d is None:
                        rep.add("unknown slot", fname,
                                f"<{parent.tag}>/<{kind} as=\"{as_name}\"> not a slot of "
                                f"this module ({sorted(bydef)})")
                        continue
                    seen[as_name] += 1
                    t = child.get("type")
                    if t == "value" and d.get("allows_value") is False:
                        rep.add("type not allowed", fname,
                                f"<{parent.tag}>/<{kind} as=\"{as_name}\" type=\"value\"> "
                                f"but the slot does not allow a literal value")
                    if t == "empty" and d.get("allows_empty") is False:
                        rep.add("type not allowed", fname,
                                f"<{parent.tag}>/<{kind} as=\"{as_name}\" type=\"empty\"> "
                                f"but the slot does not allow the empty type")
                for name, d in bydef.items():
                    mx = d.get("max")
                    if isinstance(mx, int) and seen[name] > mx:
                        rep.add("too many", fname,
                                f"<{parent.tag}>/<{kind} as=\"{name}\"> appears {seen[name]} "
                                f"times, maximum {mx}")

        # input module output components
        if skey in components:
            c = components[skey]
            attr = c.get("attribute", "component")
            names = {x["name"] for x in c["components"]}
            required = {x["name"] for x in c["components"] if x.get("required")}
            seen = collections.Counter()
            for child in parent:
                if child.tag != "output":
                    continue
                comp = child.get(attr)
                if comp is None:
                    if c.get("required_component"):
                        rep.add("missing component", fname,
                                f"<{parent.tag}>/<output> has no {attr} attribute "
                                f"(one of {sorted(names)})")
                    else:
                        # unnamed outputs fill the declared slots in order
                        for x in c["components"]:
                            if seen[x["name"]] == 0:
                                seen[x["name"]] += 1
                                break
                    continue
                if comp not in names:
                    rep.add("unknown component", fname,
                            f"<{parent.tag}>/<output {attr}=\"{comp}\"> not a component of "
                            f"this input ({sorted(names)})")
                seen[comp] += 1
            for r in required - set(seen):
                rep.add("missing component", fname,
                        f"<{parent.tag}> requires an output with {attr}=\"{r}\"")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+", help="directories holding .phyphox files")
    ap.add_argument("--detail", action="store_true", help="list every occurrence")
    args = ap.parse_args()

    spec, common, slots, components = load_spec()
    rep = Report()
    files = 0
    unparsed = []

    for d in args.dirs:
        for dirpath, _, names in os.walk(d):
            for n in sorted(names):
                if not n.endswith(".phyphox"):
                    continue
                p = os.path.join(dirpath, n)
                try:
                    root = normalize_namespace(ET.parse(p).getroot())
                except ET.ParseError as e:
                    unparsed.append((n, str(e)))
                    continue
                files += 1
                for child in root:
                    check_element(child, "phyphox", spec, common, slots, components,
                                  rep, "", n)
                for attr, value in root.attrib.items():
                    a = spec.get((None, "phyphox"), {"attrs": {}})["attrs"].get(attr)
                    if a is None:
                        rep.add("unknown attribute", n, f"<phyphox>: {attr}=\"{value}\"")
                check_slots(root, slots, components, rep, n)
                check_root_once(root, rep, n)
                check_required_children(root, "phyphox", spec, rep, "", n)
                check_unique_children(root, spec, rep, "", n)

    print(f"{files} experiment file(s) validated"
          + (f", {len(unparsed)} unparsable" if unparsed else ""))
    for n, e in unparsed:
        print(f"   ! {n}: {e}")

    if not rep.items:
        print("\nNothing to report: every file matches the specification.")
        return 1 if unparsed else 0

    print()
    for kind in sorted(rep.items, key=lambda k: -len(rep.items[k])):
        entries = rep.items[kind]
        by_detail = collections.Counter(d for _, d in entries)
        print(f"{kind.upper()} - {len(entries)} occurrence(s) in "
              f"{len({f for f, _ in entries})} file(s)")
        for detail, count in by_detail.most_common(None if args.detail else 8):
            where = sorted({f for f, d in entries if d == detail})
            shown = ", ".join(where[:3]) + (f" +{len(where)-3} more" if len(where) > 3 else "")
            print(f"   [{count:3d}] {detail}")
            print(f"         {shown}")
        if not args.detail and len(by_detail) > 8:
            print(f"   ... and {len(by_detail) - 8} more distinct message(s); use --detail")
        print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
