"""MkDocs hooks for phyphox-docs.

Wired up via `hooks:` in mkdocs.yml - no plugin packaging needed.

Responsibilities:

1. Expand `{{inconsistency:<id>}}` markers into an admonition warning the reader
   that the implementations disagree here.
2. Generate the "Known inconsistencies" page from inconsistencies.yml so the
   to-do list can never drift from the inline warnings.
3. Fail the build on a marker referencing an unknown id, so a renamed entry
   cannot silently leave a page with a dangling warning.
4. Apply the same check to the `x-phyphox-inconsistency` keys in the OpenAPI
   description, so the spec and the to-do list cannot drift either.
"""

import os
import re

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "inconsistencies.yml")
LIST_PAGE = "reference/known-inconsistencies.md"
OPENAPI = os.path.join(ROOT, "docs", "remote-interface", "openapi.yaml")

MARKER = re.compile(r"\{\{inconsistency:([a-z0-9-]+)\}\}")

STATUS_LABEL = {
    "open": ("warning", "Implementations disagree - canonical behaviour not yet decided"),
    "decided": ("warning", "Implementations disagree - this is a known bug"),
    "fixed": ("info", "Recently corrected"),
}

IMPL_LABEL = {
    "android": "Android",
    "ios": "iOS",
    "editor": "Blockly editor",
    "arduino": "Arduino library",
    "micropython": "MicroPython library",
    "wiki": "Old wiki",
}

_entries = None


def _load():
    global _entries
    if _entries is None:
        with open(SOURCE) as f:
            data = yaml.safe_load(f) or []
        _entries = {e["id"]: e for e in data}
    return _entries


def _indent(text, prefix="    "):
    return "\n".join(prefix + line if line.strip() else line
                     for line in text.strip().split("\n"))


def _admonition(entry, link_prefix=""):
    kind, heading = STATUS_LABEL.get(entry.get("status", "open"),
                                    STATUS_LABEL["open"])
    body = [entry["summary"].strip()]

    if entry.get("status") == "open":
        body.append("**This is a bug.** Which behaviour is correct has not been "
                    "decided yet, so do not rely on either until it is resolved.")
    elif entry.get("canonical"):
        body.append(f"**Correct behaviour:** {entry['canonical'].strip()}\n\n"
                    "The implementations that disagree will be corrected; treat "
                    "this as a bug, not as a platform difference to code around.")

    rows = entry.get("affects") or {}
    if rows:
        table = ["| Implementation | Current behaviour |", "|---|---|"]
        for impl, behaviour in rows.items():
            cell = " ".join(behaviour.split())
            table.append(f"| {IMPL_LABEL.get(impl, impl)} | {cell} |")
        body.append("\n".join(table))

    if entry.get("issue"):
        body.append(f"[Tracking issue]({entry['issue']})")

    body.append(f"See [all known inconsistencies]({link_prefix}"
                f"{LIST_PAGE}).")

    return (f'!!! {kind} "{heading}: {entry["title"]}"\n\n'
            + _indent("\n\n".join(body)) + "\n")


def _walk_extension(node, path=""):
    """Yield (json-pointer-ish path, id) for every x-phyphox-inconsistency."""
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "x-phyphox-inconsistency":
                for ref in (value if isinstance(value, list) else [value]):
                    yield path, ref
            else:
                yield from _walk_extension(value, f"{path}/{key}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _walk_extension(item, f"{path}[{i}]")


def on_config(config, **kwargs):
    """Check the OpenAPI description against inconsistencies.yml before building.

    The spec marks the operations where the implementations disagree; without
    this check a renamed or deleted entry would leave the spec pointing at
    nothing, and nobody reads a YAML file closely enough to notice.
    """
    if not os.path.exists(OPENAPI):
        return config

    entries = _load()
    with open(OPENAPI) as f:
        spec = yaml.safe_load(f)

    # An invalid spec means a wrong reference page, so fail the docs build on it
    # rather than shipping whatever Swagger UI makes of a broken document.
    try:
        from openapi_spec_validator import validate as _validate_openapi
    except ImportError:
        raise ValueError(
            "openapi-spec-validator is not installed, so openapi.yaml cannot be "
            "checked. Install requirements.txt.")
    _validate_openapi(spec)

    unknown = [(where, ref) for where, ref in _walk_extension(spec)
               if ref not in entries]
    if unknown:
        raise ValueError(
            "openapi.yaml references unknown inconsistency ids:\n"
            + "\n".join(f"  {where}: {ref}" for where, ref in unknown)
            + f"\nKnown ids: {', '.join(sorted(entries))}")

    referenced = {ref for _, ref in _walk_extension(spec)}
    global _api_referenced
    _api_referenced = referenced
    return config


_api_referenced = set()


def on_page_markdown(markdown, page, config, files, **kwargs):
    entries = _load()
    src = page.file.src_uri

    depth = src.count("/")
    link_prefix = "../" * depth if depth else ""

    if src == LIST_PAGE:
        return markdown + "\n" + _render_list()

    def expand(m):
        key = m.group(1)
        if key not in entries:
            raise ValueError(
                f"{src}: {{{{inconsistency:{key}}}}} refers to an id that is not "
                f"in inconsistencies.yml. Known ids: {', '.join(sorted(entries))}")
        return _admonition(entries[key], link_prefix)

    return MARKER.sub(expand, markdown)


def _render_list():
    entries = _load()
    if not entries:
        return ("Nothing is currently recorded. That is unlikely to mean the "
                "implementations agree - see the note above.\n")

    by_status = {"open": [], "decided": [], "fixed": []}
    for e in entries.values():
        by_status.setdefault(e.get("status", "open"), []).append(e)

    out = []
    headings = [
        ("open", "Undecided",
         "The implementations disagree and the canonical behaviour has not been "
         "chosen yet. Do not rely on any of these."),
        ("decided", "Decided, not yet fixed",
         "The correct behaviour is settled. The implementations that disagree "
         "are buggy and will be corrected."),
        ("fixed", "Fixed",
         "Corrected in all implementations. Listed until the release carrying "
         "the fix has shipped everywhere."),
    ]
    for status, heading, blurb in headings:
        items = by_status.get(status) or []
        if not items:
            continue
        out.append(f"## {heading}\n\n{blurb}\n")
        for e in sorted(items, key=lambda x: (x.get("area", ""), x["id"])):
            out.append(f"### {e['title']}\n")
            out.append(f"`{e['id']}` &middot; {e.get('area', 'unspecified')}\n")
            out.append(e["summary"].strip() + "\n")
            if e.get("canonical"):
                out.append(f"**Correct behaviour:** {e['canonical'].strip()}\n")
            rows = e.get("affects") or {}
            if rows:
                out.append("| Implementation | Current behaviour |")
                out.append("|---|---|")
                for impl, behaviour in rows.items():
                    out.append(f"| {IMPL_LABEL.get(impl, impl)} | "
                               f"{' '.join(behaviour.split())} |")
                out.append("")
            if e.get("issue"):
                out.append(f"[Tracking issue]({e['issue']})\n")
    return "\n".join(out)
