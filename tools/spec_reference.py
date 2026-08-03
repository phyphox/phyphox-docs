#!/usr/bin/env python3
"""Render reference sections for the file format from spec/*.yml.

    python3 tools/spec_reference.py output/audio/audio      # print one element
    python3 tools/spec_reference.py --list                  # every key

This is the generating half of phase 3. The spec was written to be checked
against the parsers; this turns it into the part of the documentation that
states facts - which attributes exist, what type each takes, what it defaults
to, from which file format version, and where the implementations disagree.

**The prose stays hand-written.** A page keeps its narrative, its worked
examples and everything the spec does not know, and marks the places where the
reference belongs:

    {{spec:output/audio/audio}}

`tools/hooks.py` expands that during the build. Nothing is generated into the
repository - the Markdown sources keep the marker, so there is no generated file
anyone can edit by mistake and no second copy to keep in step.

Three things this buys beyond removing duplication:

  * **Divergences surface where they are relevant.** Fourteen file-format
    entries were recorded in inconsistencies.yml and not one of them appeared on
    a file-format page - the mechanism existed, the markers were never placed by
    hand. An attribute whose `agreement:` is `divergent` now carries its warning
    wherever it is documented, automatically.
  * **Version notes stop being copied.** `since:` in the spec plus the release
    table on the version-history page gives "since file format 1.16 (phyphox
    1.1.12)" with a working link, in one voice, everywhere.
  * **Skeletons match the spec.** The hand-written camera skeleton named a
    component `apertue` and omitted two others; nobody had reason to notice.

Marker syntax
-------------

    {{spec:BLOCK/PARENT/NAME}}          skeleton, attributes, slots, warnings
    {{spec:BLOCK/PARENT/NAME|xml}}      the XML skeleton alone
    {{spec:BLOCK/PARENT/NAME|attributes}}
    {{spec:BLOCK/PARENT/NAME|slots}}    input/output slots or components alone
    {{spec:BLOCK/NAME}}                 a root element, which has no parent

BLOCK is the spec file (`input`, `views`, `analysis`, ...). PARENT and NAME are
the element's `parent:` and `name:`. All three are needed because neither pair
identifies an element on its own: `<audio>` exists under both `<input>` and
`<output>` and means different things, and `<config>` under `<bluetooth>` is
modelled once per block. Keying elements by name alone, or by parent and name,
is a mistake this project has made repeatedly - hence the full triple.

An attribute marked `undocumented: intentionally` is modelled but never
rendered - `appleBan` is the case it exists for.
"""

import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_DIR = os.path.join(ROOT, "spec")
VERSION_TABLE = os.path.join(ROOT, "docs", "reference", "version-history",
                             "index.md")
INCONSISTENCIES = os.path.join(ROOT, "inconsistencies.yml")
LIST_PAGE = "reference/known-inconsistencies.md"

# {{spec:BLOCK/PARENT/NAME}}, or {{spec:BLOCK/NAME}} for a root element, which
# has no parent - <phyphox> is the only one.
MARKER = re.compile(r"\{\{spec:([a-zA-Z0-9_\-]+)/(?:([a-zA-Z0-9_\-]+)/)?"
                    r"([a-zA-Z0-9_\-]+)(?:\|([a-z]+))?\}\}")

# Placeholder shown for an attribute value in a generated skeleton.
PLACEHOLDER = {
    "integer": "INTEGER",
    "float": "FLOAT",
    "boolean": "BOOLEAN",
    "string": "STRING",
    "color": "COLOR",
}


class Spec:
    """Every modelled element, keyed by (block, parent, name)."""

    def __init__(self):
        self.blocks = {}
        self.elements = {}
        self.common = {}          # block -> group -> [attribute]
        self.releases = _releases()
        self.inconsistencies = _inconsistencies()

        for fn in sorted(os.listdir(SPEC_DIR)):
            if not fn.endswith(".yml") or fn == "rules.yml":
                continue
            with open(os.path.join(SPEC_DIR, fn), encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            block = doc.get("block") or fn[:-4]
            self.blocks[block] = doc
            self.common[block] = doc.get("common") or {}
            for el in doc.get("elements") or []:
                key = (block, el.get("parent"), el["name"])
                if key in self.elements:
                    raise ValueError(f"spec: {key} is modelled twice")
                self.elements[key] = el

    def get(self, block, parent, name):
        try:
            return self.elements[(block, parent, name)]
        except KeyError:
            near = sorted("/".join(str(p) for p in k)
                          for k in self.elements if k[2] == name)
            raise KeyError(
                f"no element {block}/{parent}/{name} in the spec. "
                + (f"Elements named {name}: {', '.join(near)}" if near
                   else f"Nothing named {name} is modelled."))

    # -- shared attributes ------------------------------------------------
    def shared_for(self, block, element, child):
        """Attributes every `<input>`/`<output>` of a block accepts.

        The analysis block states them once under `common:` rather than on each
        of its 54 modules; the audio output does the same for its generators.
        """
        groups = self.common.get(block) or {}
        for group, items in groups.items():
            if child == "input" and "input" in group:
                return items or []
            if child == "output" and "output" in group:
                return items or []
        return []


def _releases():
    """file format version -> (phyphox release, page) from the release table.

    The overview table on the version-history page is the only machine-readable
    statement of which release first carried a file format version, and the
    prose has always quoted the pair together ("file format 1.16 (phyphox
    1.1.12)"). Reading it here keeps the generated notes saying the same thing
    as the hand-written ones, with a link that the build checks.
    """
    out = {}
    if not os.path.exists(VERSION_TABLE):
        return out
    row = re.compile(r"^\|\s*\[([\d.]+)\]\(([^)]+)\)\s*\|[^|]*\|\s*\(?([\d.]+)\)?\s*\|")
    with open(VERSION_TABLE, encoding="utf-8") as f:
        for line in f:
            m = row.match(line.strip())
            if m:
                release, page, fmt = m.groups()
                out.setdefault(fmt, (release, page))
    return out


def _inconsistencies():
    if not os.path.exists(INCONSISTENCIES):
        return {}
    with open(INCONSISTENCIES, encoding="utf-8") as f:
        return {e["id"]: e for e in (yaml.safe_load(f) or [])}


# ---------------------------------------------------------------- helpers --

def _slug(text):
    """The anchor python-markdown's toc extension gives a heading."""
    try:
        from markdown.extensions.toc import slugify_unicode
        return slugify_unicode(text, "-")
    except ImportError:
        text = re.sub(r"[^\w\s-]", "", text).strip().lower()
        return re.sub(r"[-\s]+", "-", text)


def _sentence(text):
    """Collapse a folded YAML scalar back to flowing text."""
    return " ".join((text or "").split())


def _text(entry):
    """What the documentation shows for an attribute, slot or component.

    `summary:` is the one-line statement the spec was written with, and it
    stays that: short enough to scan a whole block in one screen, and what a
    generated index or a validator message wants. `description:` is the full
    documentation text, moved across from the hand-written pages, which is
    usually several sentences and sometimes several paragraphs. Where both
    exist the longer one is what a reader gets.
    """
    text = entry.get("description") or entry.get("summary") or ""
    # A description written as a literal block may hold several paragraphs.
    # Inside a definition-list item every line after the first has to be
    # indented to stay part of it.
    paragraphs = [_sentence(p) for p in re.split(r"\n\s*\n", text) if p.strip()]
    return "\n\n    ".join(paragraphs)


def _code_list(values):
    return ", ".join(f"`{v}`" for v in values)


def _version_note(version, spec, prefix="", capitalise=True):
    """"since file format 1.16 (phyphox 1.1.12)", with a link to the release."""
    if not version or str(version) == "1.0":
        return ""
    rel = spec.releases.get(str(version))
    note = f"since file format {version}"
    if rel:
        release, page = rel
        note += f" ([phyphox {release}]({prefix}reference/version-history/{page}))"
    return note[0].upper() + note[1:] if capitalise else note


class PageState:
    """Per-page bookkeeping.

    An inconsistency is rendered in full the first time a page needs it and
    referred to by link afterwards. `input-invalid-enum-handling` is reached by
    eleven attributes; eleven copies of the same admonition on one page would
    be worse than not warning at all.
    """

    def __init__(self, link_prefix=""):
        self.link_prefix = link_prefix
        self.seen = set()


# ------------------------------------------------------------- attributes --

def _meta_line(attr, spec, link_prefix):
    """The second definition line: requiredness, type, values, default, since."""
    bits = ["*required*" if attr.get("required") else "*optional*"]

    kind = attr.get("type")
    unit = f" in {attr['unit']}" if attr.get("unit") else ""
    if kind == "enum" and attr.get("values"):
        bits.append("one of " + _code_list(attr["values"]) + unit)
    elif kind and kind != "string":
        bits.append(kind + unit)
    elif unit:
        bits.append(unit.strip())

    default = attr.get("default")
    if isinstance(default, list):
        # Version-dependent defaults, most recent first. This is the reason the
        # format needs a spec rather than a grammar.
        parts = []
        for entry in default:
            value = _render_value(entry.get("value"))
            if entry.get("since"):
                parts.append(f"{value} from file format {entry['since']}")
            else:
                parts.append(f"{value} below that")
        bits.append("default: " + ", ".join(parts))
    elif default is not None:
        bits.append(f"default: {_render_value(default)}")

    if attr.get("since"):
        bits.append(_version_note(attr["since"], spec, link_prefix,
                                  capitalise=False))
    if attr.get("translatable"):
        bits.append("translatable")

    platforms = attr.get("platforms") or []
    if attr.get("agreement") == "platform" and platforms:
        names = {"android": "Android", "ios": "iOS"}
        bits.append("**" + " and ".join(names.get(p, p) for p in platforms)
                    + " only**")

    return ":   " + ", ".join(b for b in bits if b)


def _render_value(value):
    if value is None:
        return "none"
    if isinstance(value, bool):
        return f"`{str(value).lower()}`"
    if value == "":
        return "empty"
    # Some defaults are described rather than stated - "the length of the
    # input". Setting those in code voice suggests they are a literal.
    if isinstance(value, str) and " " in value:
        return value
    return f"`{value}`"


def _attribute(attr, spec, state):
    lines = [attr["name"], ":   " + _text(attr)]

    if attr.get("deprecated"):
        superseded = attr.get("superseded_by")
        note = "*Deprecated.*"
        if superseded:
            target = (f"`{superseded}`" if re.fullmatch(r"[\w.]+", superseded)
                      else superseded)
            note += f" Use {target} instead."
        lines.append(":   " + note)

    # `note:` is deliberately not rendered. It holds what was found while
    # reading the two parsers - source citations, why a divergence is not one,
    # what to search for next time - which is the spec's working record and not
    # something a reader of the documentation has any use for. Reader-facing
    # detail goes in `remark:`, which exists so the distinction has to be made
    # on purpose rather than by whoever happens to be writing the note.
    if attr.get("remark"):
        lines.append(":   " + _sentence(attr["remark"]))

    # An enumerated attribute whose values need explaining carries them in
    # `value_notes:`, rendered as a nested definition list - the shape the
    # hand-written pages already used for aeStrategy and the audio parameters.
    notes = attr.get("value_notes") or {}
    if notes:
        nested = []
        for value in (attr.get("values") or list(notes)):
            if value in notes:
                nested.append(f"    {value}\n    :   " + _sentence(notes[value]))
        if nested:
            lines.append("\n" + "\n\n".join(nested) + "\n")

    lines.append(_meta_line(attr, spec, state.link_prefix))

    ref = attr.get("inconsistency")
    if ref:
        lines.append(":   " + _divergence_pointer(ref, spec, state))
    return "\n".join(lines)


def _divergence_pointer(ref, spec, state):
    entry = spec.inconsistencies.get(ref)
    if entry is None:
        raise ValueError(f"spec references unknown inconsistency {ref}")
    anchor = _slug(entry["title"])
    link = f"{state.link_prefix}{LIST_PAGE}#{anchor}"
    return (f"⚠ The implementations disagree here - see "
            f"[{entry['title']}]({link}).")


def render_attributes(element, spec, state):
    # `undocumented: intentionally` keeps an attribute out of the documentation
    # while the spec still models it. appleBan is the case it exists for: iOS
    # reads it, so a specification of the format has to record it, and it is
    # App Store housekeeping that no experiment author should be reaching for.
    attrs = [a for a in (element.get("attributes") or [])
             if not a.get("undocumented")]
    if not attrs:
        return ""
    return "\n\n".join(_attribute(a, spec, state) for a in attrs)


# ----------------------------------------------------- slots & components --

def _count(slot):
    lo, hi = slot.get("min", 0), slot.get("max")
    if hi in (None, "unlimited", 0):
        return "at least one" if lo else "any number"
    if lo == hi:
        return "exactly one" if hi == 1 else f"exactly {hi}"
    if lo == 0:
        return "optional" if hi == 1 else f"up to {hi}"
    return f"{lo} to {hi}"


def render_slots(element, spec, state, block):
    """`<input>`/`<output>` children: analysis slots or input components."""
    out = []

    components = element.get("outputs")
    if isinstance(components, dict):
        out.append(_components(element, components, spec, state))
        components = None

    for kind in ("inputs", "outputs"):
        slots = element.get(kind)
        if not isinstance(slots, list) or not slots:
            continue
        label = "input" if kind == "inputs" else "output"
        rows = ["| `as` | Count | `as` required | Literal value |",
                "|---|---|---|---|"]
        repeats, footnotes = [], []
        for slot in slots:
            if slot.get("remark"):
                footnotes.append(f"`{slot['name']}`\n:   "
                                 + _sentence(slot["remark"]))
            if slot.get("inconsistency"):
                footnotes.append(f"`{slot['name']}`\n:   " + _divergence_pointer(
                    slot["inconsistency"], spec, state))
            value = ("n/a" if kind == "outputs"
                     else ("allowed" if slot.get("allows_value") else "no"))
            if slot.get("allows_empty"):
                value += ", `type=\"empty\"` allowed"
            count = _count(slot)
            if slot.get("default") is not None:
                count += f", defaults to {_render_value(slot['default'])}"
            rows.append(f"| `{slot['name']}` | {count} | "
                        f"{'yes' if slot.get('as_required', True) else 'no'} | "
                        f"{value} |")
            if slot.get("repeat_offset"):
                repeats.append(slot["name"])
        out.append(f"**{label.capitalize()}s**\n\n" + "\n".join(rows))
        if footnotes:
            out.append("\n\n".join(footnotes))
        if repeats:
            out.append("The slots " + _code_list(repeats) + " form a repeating "
                       "group: a further set of tags in the same order adds "
                       "another one.")

    if out and element.get("parent") == "analysis":
        shared_in = spec.shared_for(block, element, "input")
        shared_out = spec.shared_for(block, element, "output")
        if shared_in or shared_out:
            out.append("Every `<input>` and `<output>` additionally accepts the "
                       "attributes common to all analysis modules.")
    return "\n\n".join(out)


def _components(element, mapping, spec, state):
    """The `<output component="...">` children of an input module."""
    attribute = mapping.get("attribute", "component")
    lines = [f"**Outputs**", "", "Each `<output>` names the data container "
             f"receiving one component, selected with `{attribute}`."
             + ("" if mapping.get("required_component")
                else f" A tag without `{attribute}` fills the first component.")]

    for comp in mapping.get("components") or []:
        entry = [comp["name"], ":   " + _text(comp)]
        bits = []
        if comp.get("required"):
            bits.append("*required*")
        if comp.get("since"):
            bits.append(_version_note(comp["since"], spec, state.link_prefix,
                                      capitalise=False))
        if bits:
            entry.append(":   " + ", ".join(bits))
        if comp.get("deprecated"):
            note = "*Deprecated.*"
            if comp.get("superseded_by"):
                note += f" Superseded by {comp['superseded_by']}."
            entry.append(":   " + note)
        if comp.get("platforms"):
            names = {"android": "Android", "ios": "iOS"}
            entry.append(":   **Only "
                         + " and ".join(names.get(p, p) for p in comp["platforms"])
                         + "** accepts this component.")
        lines.append("")
        lines.append("\n".join(entry))

    ref = mapping.get("inconsistency")
    if ref:
        lines.append("")
        lines.append(_divergence_pointer(ref, spec, state))
    return "\n".join(lines)


# ---------------------------------------------------------------- skeleton --

def _attr_placeholder(attr):
    if attr.get("type") == "enum" and attr.get("values"):
        joined = "/".join(str(v) for v in attr["values"])
        # Spelling the choices out in the skeleton is the useful thing to do
        # when there are two or three of them and unreadable when there are six.
        if len(joined) <= 24:
            return joined
        return "STRING"
    return PLACEHOLDER.get(attr.get("type"), "STRING")


def _open_tag(name, attrs, width=78):
    """`<graph a="..." b="...">`, wrapped and aligned when it gets long.

    The graph element takes 53 attributes. On one line that is a 1,400-character
    skeleton nobody can read, and it is the element people most need a skeleton
    for.
    """
    pairs = [f'{a["name"]}="{_attr_placeholder(a)}"' for a in attrs
             if not a.get("deprecated") and not a.get("undocumented")]
    if not pairs:
        return f"<{name}>"
    indent = " " * (len(name) + 2)
    lines, current = [], f"<{name}"
    for pair in pairs:
        if len(current) + 1 + len(pair) > width and current.strip() != f"<{name}":
            lines.append(current)
            current = indent + pair
        else:
            current += " " + pair
    lines.append(current + ">")
    return "\n".join(lines)


def render_skeleton(element, spec, block, max_children=12):
    name = element["name"]
    open_tag = _open_tag(name, element.get("attributes") or [])

    body = []
    mapping = element.get("outputs")
    if isinstance(mapping, dict):
        attribute = mapping.get("attribute", "component")
        for comp in (mapping.get("components") or [])[:max_children]:
            body.append(f'    <output {attribute}="{comp["name"]}">BUFFER</output>')
    else:
        for kind, tag in (("inputs", "input"), ("outputs", "output")):
            slots = element.get(kind)
            if not isinstance(slots, list):
                continue
            for slot in slots[:max_children]:
                body.append(f'    <{tag} as="{slot["name"]}">BUFFER</{tag}>')

    for child in element.get("children") or []:
        if child in ("input", "output") and (
                element.get("inputs") or element.get("outputs")):
            continue
        sub = spec.elements.get((block, name, child))
        if sub is None:
            body.append(f"    <{child}>...</{child}>")
            continue
        inner = "TEXT" if sub.get("text") else ""
        if sub.get("children") or isinstance(sub.get("outputs"), (dict, list)):
            inner = inner or "..."
        # Spelling out every child's attributes is right for <audio>, with
        # three children, and useless for <view>, with twelve - the whole
        # views block would arrive as one 60-line skeleton. Past a handful of
        # children the skeleton's job is to show what may appear, and each
        # child has its own reference section anyway.
        if len(element.get("children") or []) > 3:
            body.append(f"    <{child} />" if not inner
                        else f"    <{child}>{inner}</{child}>")
            continue
        tag = _open_tag(child, sub.get("attributes") or [], width=74)
        body.extend(f"    {line}" for line in tag.split("\n")[:-1])
        body.append(f'    {tag.split(chr(10))[-1]}{inner}</{child}>')

    text = "TEXT" if element.get("text") else ""
    if not body:
        return f"```xml\n{open_tag}{text}</{name}>\n```"
    return "```xml\n" + "\n".join([open_tag] + body + [f"</{name}>"]) + "\n```"


# ------------------------------------------------------------------ render --

def render_element(block, parent, name, spec, state, mode=None):
    element = spec.get(block, parent, name)
    parts = []

    if mode in (None, "xml"):
        parts.append(render_skeleton(element, spec, block))
    if mode == "xml":
        return "\n\n".join(parts)

    if mode is None:
        note = _version_note(element.get("since"), spec, state.link_prefix)
        if note:
            parts.append(f"*{note}.*")
        if element.get("text"):
            parts.append("**Text content:** " + _sentence(element["text"]))
        if element.get("remark"):
            parts.append(_sentence(element["remark"]))

    if mode in (None, "attributes"):
        attrs = render_attributes(element, spec, state)
        if attrs:
            parts.append("**Attributes**\n\n" + attrs)
        elif mode == "attributes":
            parts.append("This element takes no attributes.")

    if mode in (None, "slots"):
        slots = render_slots(element, spec, state, block)
        if slots:
            parts.append(slots)

    if mode is None:
        parts.extend(_element_warnings(element, spec, state))

    return "\n\n".join(p for p in parts if p)


def _element_warnings(element, spec, state):
    """Full admonitions for divergences this element is the first to reach."""
    holders = [element] + list(element.get("attributes") or [])
    if isinstance(element.get("outputs"), dict):
        holders.append(element["outputs"])
    if isinstance(element.get("slot_constraints"), dict):
        holders.append(element["slot_constraints"])
    for key in ("inputs", "outputs"):
        if isinstance(element.get(key), list):
            holders += [s for s in element[key] if isinstance(s, dict)]

    refs = []
    for holder in holders:
        ref = holder.get("inconsistency")
        if ref and ref not in refs:
            refs.append(ref)

    out = []
    for ref in refs:
        if ref in state.seen:
            continue
        state.seen.add(ref)
        out.append("{{inconsistency:" + ref + "}}")
    return out


def expand(markdown, spec, state):
    """Replace every {{spec:...}} marker in a page."""
    def one(m):
        block, parent, name, mode = m.groups()
        return render_element(block, parent, name, spec, state, mode)
    return MARKER.sub(one, markdown)


def main():
    spec = Spec()
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--list":
        for key in sorted(spec.elements,
                          key=lambda k: tuple(str(p) for p in k)):
            print("/".join(str(p) for p in key))
        return 0
    state = PageState("../")
    for arg in args:
        mode = None
        if "|" in arg:
            arg, mode = arg.split("|", 1)
        parts = arg.split("/")
        block, name = parts[0], parts[-1]
        parent = parts[1] if len(parts) == 3 else None
        print(render_element(block, parent, name, spec, state, mode))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
