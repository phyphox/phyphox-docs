#!/usr/bin/env python3
"""Cross-check spec/*.yml against what the documentation describes.

    python3 tools/spec_vs_docs.py

The prose is not authoritative - it has already been caught documenting an
attribute name no implementation accepts - so a mismatch is not an error. It is a
prompt to look again, and it catches the one failure the parsers cannot: a
construct that exists, is documented, and was simply not noticed while reading
the source. Three such gaps in the views block were found by hand before this
existed.

The docs are mined two ways, both deliberately crude:

  * XML skeletons in code fences, which give element names and, from
    `attr="..."` pairs, their attributes. This is the strong signal - authors
    write the skeleton to show the full surface.
  * Definition-list terms, which name attributes but not which element they
    belong to, so they are only checked as a flat set per page.

Findings are reported per direction. "In the docs, not in the spec" is the one
that matters; the reverse usually means the docs are behind, which is worth
knowing but is not a modelling error.
"""

import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = os.path.join(ROOT, "spec")
DOCS = os.path.join(ROOT, "docs", "file-format")

# spec file -> documentation pages describing the same block
PAIRS = {
    "input.yml": ["input.md", "bluetooth-low-energy.md"],
    "views.yml": ["views.md"],
}

# Placeholders and unrelated elements that appear inside the skeletons.
IGNORE_ELEMENTS = {"phyphox", "views", "data-containers", "container", "input",
                   "output", "analysis", "export", "set", "data", "translations",
                   "translation", "string", "network", "connection", "send",
                   "receive", "events", "event", "title", "category", "icon",
                   "description", "link", "color", "state-title"}
IGNORE_ATTRS = {"version"}

# Some documentation pages describe more than one block - bluetooth-low-energy.md
# covers the bluetooth element of the input block AND of the output block. Until
# every block is modelled, constructs belonging to an unmodelled one look like
# gaps. List them here and delete the entry when that block is modelled.
# Attributes the spec models that the documentation deliberately does not
# describe. Keeping them listed means the "undocumented" report stays actionable
# instead of becoming noise everyone skims past.
EXPECTED_UNDOCUMENTED = {
    # superseded draft of the spectroscopy feature, to be removed - see
    # graph-output-data-picker
    "calibrationMode", "calibrationParameter",
    # the docs describe the colour scale generically as mapColor[n]
    "mapColor8", "mapColor9",
    # TODO: document when the bluetooth block is modelled. Implemented by both
    # apps; the decimal separator for the string conversion.
    "decimalPoint",
}

OTHER_BLOCK = {
    # <input char="..." conversion="...">: the bluetooth element of <output>,
    # which writes to a device. Belongs to output.yml, not yet written.
    ("bluetooth-low-energy.md", "input"): {"char", "conversion"},
}

FENCE = re.compile(r"```(?:xml)?\n(.*?)```", re.S)
TAG = re.compile(r"<([a-zA-Z][\w\-]*)((?:\s+[\w\-]+\s*=\s*\"[^\"]*\")*)")
ATTR = re.compile(r"([\w\-]+)\s*=\s*\"[^\"]*\"")
DEF_TERM = re.compile(r"^([A-Za-z_][\w\-]*)\s*$")


def from_docs(page):
    """(elements -> attributes) from XML skeletons, plus all definition terms."""
    md = open(os.path.join(DOCS, page), encoding="utf-8").read()
    elements = {}
    for fence in FENCE.findall(md):
        for m in TAG.finditer(fence):
            name = m.group(1)
            attrs = set(ATTR.findall(m.group(2) or ""))
            elements.setdefault(name, set()).update(attrs - IGNORE_ATTRS)

    lines = md.split("\n")
    terms = {m.group(1) for i, ln in enumerate(lines[:-1])
             if (m := DEF_TERM.match(ln)) and lines[i + 1].startswith(":")}

    # Anything named anywhere on the page counts as documented for the "is this
    # mentioned at all" direction. Deliberately generous: several BLE conversion
    # attributes are described in tables and prose rather than definition lists,
    # and flagging those as undocumented buries the ones that really are.
    mentioned = set(re.findall(r"[A-Za-z_][\w\-]*", md))
    return elements, terms | mentioned


def from_spec(fn):
    doc = yaml.safe_load(open(os.path.join(SPEC, fn), encoding="utf-8"))
    elements = {}
    for el in doc.get("elements") or []:
        attrs = {a["name"] for a in (el.get("attributes") or [])}
        # `outputs:` describes the child <output> element of input modules,
        # including the attribute that names the component.
        outputs = el.get("outputs")
        if outputs:
            elements.setdefault("output", set())
            if outputs.get("attribute"):
                elements["output"].add(outputs["attribute"])
        elements.setdefault(el["name"], set()).update(attrs)
    return elements


def main():
    total = 0
    for fn, pages in sorted(PAIRS.items()):
        spec = from_spec(fn)
        documented = set()
        for page in pages:
            doc_els, doc_terms = from_docs(page)
            print(f"\n=== {fn}  vs  {page} " + "=" * (46 - len(fn) - len(page)))

            missing_el = sorted(set(doc_els) - set(spec) - IGNORE_ELEMENTS)
            if missing_el:
                total += len(missing_el)
                print("  ELEMENTS in the docs but not the spec — look again:")
                for e in missing_el:
                    print(f"     <{e}>")

            for el in sorted(set(doc_els) & set(spec)):
                gap = sorted(doc_els[el] - spec[el]
                             - OTHER_BLOCK.get((page, el), set()))
                if gap:
                    total += len(gap)
                    print(f"  ATTRIBUTES on <{el}> in the docs but not the spec:")
                    for a in gap:
                        print(f"     {a}")

            documented.update(doc_terms)
            documented.update(a for v in doc_els.values() for a in v)

        # Only meaningful once every page describing this block has been read -
        # an attribute documented on one page and absent from another is not
        # undocumented.
        spec_attrs = {a for v in spec.values() for a in v}
        undocumented = sorted(spec_attrs - documented - EXPECTED_UNDOCUMENTED)
        if undocumented:
            print(f"  in {fn} but documented on none of its pages:")
            for a in undocumented:
                print(f"     {a}")

    print(f"\n{total} thing(s) documented but not modelled." if total else
          "\nNothing documented is missing from the spec.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
