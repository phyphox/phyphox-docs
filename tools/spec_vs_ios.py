#!/usr/bin/env python3
"""Check spec/*.yml against the attributes iOS's handlers declare.

    python3 tools/spec_vs_ios.py [path-to-phyphox-ios]

iOS states its accepted surface unusually plainly: every element handler carries
an `enum Attribute` listing exactly what it reads, and registers its children by
name. Walking that from the root element gives an independent inventory of the
format to diff the spec against - one that does not depend on my having read the
right lines.

It found a real structural error on its first run: <input> under <tone> and
<noise> in the audio output, which the spec had modelled only under <audio>.

Three traps this has to avoid, all of which produced false findings before being
handled:

  * **Class bodies must be brace-matched.** A regex ending at the first `\\n}`
    runs past the end of a class and picks up the next one's attributes. That
    reported `experimentTime` on <events> (it belongs to <start>/<pause>) and
    `stride` on a bluetooth output (it belongs to a neighbouring sensor handler).
  * **Class names are not unique.** OutputElementHandler.swift declares its own
    private AudioElementHandler and BluetoothElementHandler, with the same names
    as the input block's. Keys are therefore file-qualified.
  * **childHandlers maps names to variables, not classes.** They have to be
    resolved through the `let x = SomeHandler()` bindings in the same class.

Anything iOS declares but never reads is listed in DECLARED_BUT_UNREAD rather
than modelled: it is in the source, but it is not part of the format.
"""

import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "spec")
DEFAULT_IOS = os.path.join(os.path.dirname(ROOT), "phyphox-ios")

# (parent, child) -> attributes iOS declares in its Attribute enum and never
# reads. Checked by hand; each is dead code rather than part of the format.
DECLARED_BUT_UNREAD = {
    ("bluetooth", "output"): {"stride"},
    ("dropdown", "map"): {"replacement"},
    ("tone", "input"): {"clear"},
    ("noise", "input"): {"clear"},
    ("input", "bluetooth"): {"mtu"},          # honoured on Android, ignored here
    ("phyphox", "events"): {"experimentTime", "systemTime"},  # copy of its child's enum
    ("phyphox", "link"): {"translation"},     # declared only to reject it with a clear
                                              # error: allowed on translation/link only
}

# Elements iOS reaches through a computed childHandler rather than a literal
# switch, so the walk cannot see them. Checked by hand instead.
#   events/start, events/pause  - accepted via TimeMappingEvent(rawValue:)
#   analysis/<module>           - any name, dispatched by ExperimentAnalysisFactory


def class_bodies(src):
    """Yield (class_name, body) with bodies delimited by brace matching."""
    for m in re.finditer(r'class (\w+)\s*:[^{]*\{', src):
        depth, i = 1, m.end()
        while i < len(src) and depth:
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
            i += 1
        yield m.group(1), src[m.end():i - 1]


def scan(ios_root):
    handlers_dir = os.path.join(ios_root, "phyphox-iOS", "phyphox",
                                "Experiments", "Serialization", "Handlers")
    handlers = {}
    for dirpath, _, files in os.walk(handlers_dir):
        for fn in files:
            if not fn.endswith(".swift"):
                continue
            src = open(os.path.join(dirpath, fn), encoding="utf-8").read()
            for cls, body in class_bodies(src):
                attrs = []
                for em in re.finditer(r'enum Attribute[^{]*\{(.*?)\n\s*\}', body, re.S):
                    for c in re.finditer(r'case (\w+)(?:\s*=\s*"([^"]+)")?', em.group(1)):
                        attrs.append(c.group(2) or c.group(1))
                binding = dict(re.findall(
                    r'(?:let|var) (\w+)\s*(?::\s*\w+)?\s*=\s*(\w+ElementHandler)\(\)', body))
                kids = {}
                ch = re.search(r'childHandlers\s*=\s*\[(.*?)\]', body, re.S)
                if ch:
                    for name, var in re.findall(r'"([\w\-]+)"\s*:\s*(\w+)', ch.group(1)):
                        kids[name] = (fn, binding.get(var, var))
                for cm in re.finditer(r'case "([\w\-]+)":\s*\n?\s*handler = (\w+)', body):
                    kids[cm.group(1)] = (fn, binding.get(cm.group(2), cm.group(2)))
                handlers[f"{fn}::{cls}"] = {"attrs": sorted(set(attrs)), "children": kids}
    return handlers


def walk(handlers):
    def resolve(hint, cls):
        if f"{hint}::{cls}" in handlers:
            return f"{hint}::{cls}"
        return next((k for k in handlers if k.endswith(f"::{cls}")), None)

    root = "PhyphoxElementHandler.swift::PhyphoxElementHandler"
    pairs, frontier, seen = {}, [("phyphox", root)], set()
    while frontier:
        pname, pkey = frontier.pop()
        if (pname, pkey) in seen:
            continue
        seen.add((pname, pkey))
        for cname, (fn, ccls) in (handlers.get(pkey, {}).get("children") or {}).items():
            ckey = resolve(fn, ccls)
            if ckey:
                pairs[(pname, cname)] = ckey
                frontier.append((cname, ckey))
    return pairs


def spec_attributes():
    out = {}
    patterns = {}
    for fn in sorted(os.listdir(SPEC)):
        if not fn.endswith(".yml") or fn == "rules.yml":
            continue
        doc = yaml.safe_load(open(os.path.join(SPEC, fn), encoding="utf-8")) or {}
        common = {}
        for group, items in (doc.get("common") or {}).items():
            key = ("input" if "input" in group else
                   "output" if "output" in group else
                   "view" if "view" in group else None)
            if key:
                common[key] = {i["name"] for i in items or []}
        for el in doc.get("elements") or []:
            key = (el.get("parent"), el["name"])
            out[key] = out.get(key, set()) | {a["name"] for a in (el.get("attributes") or [])}
            for a in el.get("attributes") or []:
                if a.get("name_pattern"):
                    patterns.setdefault(key, []).append(re.compile(a["name_pattern"]))
            outputs = el.get("outputs")
            if isinstance(outputs, dict) and outputs.get("attribute"):
                k2 = (el["name"], "output")
                out[k2] = out.get(k2, set()) | {outputs["attribute"]}
        for el in doc.get("elements") or []:
            for child in el.get("children") or []:
                if child in common:
                    k2 = (el["name"], child)
                    out[k2] = out.get(k2, set()) | common[child]
            # a "view" common group applies to every child of the view element
            if el["name"] == "view" and "view" in common:
                for child in el.get("children") or []:
                    k2 = ("view", child)
                    out[k2] = out.get(k2, set()) | common["view"]
    return out, patterns


def main():
    ios_root = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IOS
    if not os.path.isdir(ios_root):
        print(f"phyphox-ios not found at {ios_root} - pass its path as an argument.")
        return 0

    handlers = scan(ios_root)
    pairs = walk(handlers)
    spec, spec_patterns = spec_attributes()

    problems = []
    for (pname, cname), key in sorted(pairs.items()):
        declared = set(handlers.get(key, {}).get("attrs") or [])
        declared -= DECLARED_BUT_UNREAD.get((pname, cname), set())
        modelled = spec.get((pname, cname))
        if modelled is None:
            if declared:
                problems.append(f"{pname}/{cname}: not modelled at all "
                                f"(iOS declares {sorted(declared)})")
        else:
            gap = sorted(a for a in declared - modelled
                         if not any(rx.fullmatch(a)
                                    for rx in spec_patterns.get((pname, cname), [])))
            if gap:
                problems.append(f"{pname}/{cname}: iOS declares {gap}, spec does not")

    print(f"{len(pairs)} parent/child pairs reachable from <phyphox> in the iOS handlers")
    if problems:
        print()
        for p in problems:
            print(f"  {p}")
        print(f"\n{len(problems)} gap(s).")
        return 1
    print("No attribute iOS declares is missing from the spec.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
