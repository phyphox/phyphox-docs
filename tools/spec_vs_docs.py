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
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# spec file -> documentation pages describing the same block
PAIRS = {
    "input.yml": ["input.md", "bluetooth-low-energy.md"],
    "views.yml": ["views.md"],
    "network.yml": ["network-connections.md"],
    "root.yml": ["index.md"],
    "output.yml": ["output.md", "bluetooth-low-energy.md"],
    "analysis.yml": ["analysis/index.md", "analysis/basic-math.md",
                     "analysis/trigonometric-functions.md", "analysis/statistics.md",
                     "analysis/advanced-math.md", "analysis/buffer-operations.md",
                     "analysis/data-generation.md", "analysis/logic.md",
                     "analysis/other.md", "analysis/formula-node.md"],
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
    # Root attributes neither page describes. isLink is in the version history
    # for 1.1.9 and is implemented on both, so it wants documenting; appleBan is
    # iOS-only App Store housekeeping and arguably should not be.
    "isLink", "appleBan",
}

OTHER_BLOCK = {}

FENCE = re.compile(r"```(?:xml)?\n(.*?)```", re.S)
TAG = re.compile(r"<([a-zA-Z][\w\-]*)((?:\s+[\w\-]+\s*=\s*\"[^\"]*\")*)")
ATTR = re.compile(r"([\w\-]+)\s*=\s*\"[^\"]*\"")
DEF_TERM = re.compile(r"^([A-Za-z_][\w\-]*)\s*$")


_spec_cache = None


def _rendered(page):
    """The page as the build sees it, with {{spec:...}} markers expanded.

    Once a page draws its reference section from the spec, its Markdown source
    no longer names the attributes - so comparing the source would report every
    generated attribute as undocumented, and would stop checking the parts of
    the page that are still hand-written. Expanding first keeps this check
    meaningful during the conversion, when a page is half generated.

    What it can no longer be is an independent opinion: generated text agrees
    with the spec by construction. Its remaining job is the unconverted prose,
    which is where the omissions it has caught all came from.
    """
    global _spec_cache
    md = open(os.path.join(DOCS, page), encoding="utf-8").read()
    if "{{spec:" not in md:
        return md
    import spec_reference
    if _spec_cache is None:
        _spec_cache = spec_reference.Spec()
    depth = page.count("/") + 1
    return spec_reference.expand(
        md, _spec_cache, spec_reference.PageState("../" * depth))


def from_docs(page):
    """(elements -> attributes) from XML skeletons, plus all definition terms."""
    md = _rendered(page)
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
    for group, items in (doc.get("common") or {}).items():
        key = "input" if "input" in group else ("output" if "output" in group else "_common")
        elements.setdefault(key, set()).update(i["name"] for i in items or [])
    for el in doc.get("elements") or []:
        attrs = {a["name"] for a in (el.get("attributes") or [])}
        # `outputs:` describes the child <output> element of input modules,
        # including the attribute that names the component.
        outputs = el.get("outputs")
        if isinstance(outputs, dict):
            elements.setdefault("output", set())
            if outputs.get("attribute"):
                elements["output"].add(outputs["attribute"])
        elif outputs:                       # analysis modules: a list of slots
            elements.setdefault("output", set())
        if el.get("inputs"):
            elements.setdefault("input", set())
        elements.setdefault(el["name"], set()).update(attrs)
    return elements


def main():
    total = 0
    # A documentation page can describe more than one block - bluetooth-low-energy.md
    # covers the bluetooth element of both input and output - so a page is
    # compared against the union of the specs that claim it, not against each in
    # turn. Comparing individually reports each block's constructs as missing
    # from the other.
    pages_to_specs = {}
    for fn, pages in PAIRS.items():
        for page in pages:
            pages_to_specs.setdefault(page, []).append(fn)

    for page, fns in sorted(pages_to_specs.items()):
        spec = {}
        for fn in fns:
            for el, attrs in from_spec(fn).items():
                spec.setdefault(el, set()).update(attrs)
        documented = set()
        for _ in (page,):
            doc_els, doc_terms = from_docs(page)
            label = "+".join(fns)
            print(f"\n=== {label}  vs  {page} " + "=" * max(4, 46 - len(label) - len(page)))

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
        if undocumented and len(PAIRS.get(fns[0], [])) == 1:
            print(f"  in {'+'.join(fns)} but not named on {page}:")
            for a in undocumented:
                print(f"     {a}")

    print(f"\n{total} thing(s) documented but not modelled." if total else
          "\nNothing documented is missing from the spec.")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
