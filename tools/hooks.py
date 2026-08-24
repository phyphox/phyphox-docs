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
5. Fail the build if the generated site would make a visitor's browser fetch
   anything from a third party.
"""

import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
SOURCE = os.path.join(ROOT, "inconsistencies.yml")
LIST_PAGE = "reference/known-inconsistencies.md"
OPENAPI = os.path.join(ROOT, "docs", "remote-interface", "openapi.yaml")
SPEC_DIR = os.path.join(ROOT, "spec")

MARKER = re.compile(r"\{\{inconsistency:([a-z0-9-]+)\}\}")

# There is deliberately no "fixed" status: an entry whose divergence has been
# corrected everywhere is deleted, markers and spec references with it. Readers
# learn about corrected behaviour from the release changelog; a lingering
# "recently corrected" note only clutters the documentation.
STATUS_LABEL = {
    "open": ("warning", "Implementations disagree - canonical behaviour not yet decided"),
    "decided": ("warning", "Implementations disagree - this is a known bug"),
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


def _ensure_path():
    """Make the sibling modules importable, and keep them importable.

    MkDocs loads a hooks file by path with its own directory temporarily on
    sys.path, and takes that entry away again once the module is imported. A
    module-level insert guarded by "if not already there" therefore does
    nothing - the directory is there at that moment and gone by the time a hook
    actually runs. Ensuring it at each entry point is what survives that.
    """
    if TOOLS not in sys.path:
        sys.path.append(TOOLS)


def _load():
    global _entries
    if _entries is None:
        with open(SOURCE) as f:
            data = yaml.safe_load(f) or []
        bad = [e["id"] for e in data if e.get("status") not in STATUS_LABEL]
        if bad:
            raise ValueError(
                "inconsistencies.yml: entries with a status that is not "
                f"open/decided: {', '.join(bad)}. A corrected divergence is "
                "deleted, not marked fixed - remove the entry along with its "
                "markers and spec references.")
        _entries = {e["id"]: e for e in data}
    return _entries


def _indent(text, prefix="    "):
    return "\n".join(prefix + line if line.strip() else line
                     for line in text.strip().split("\n"))


def _admonition(entry, link_prefix=""):
    kind, heading = STATUS_LABEL.get(entry.get("status", "open"),
                                    STATUS_LABEL["open"])
    if entry.get("permanent"):
        # A decided entry can be marked permanent: the difference is the
        # intended contract (platform limitation or deliberate design), so the
        # bug wording would be wrong - it will never be "fixed".
        kind, heading = "info", "The platforms differ here by design"
    body = [entry["summary"].strip()]

    if entry.get("status") == "open":
        body.append("**This is a bug.** Which behaviour is correct has not been "
                    "decided yet, so do not rely on either until it is resolved.")
    elif entry.get("permanent"):
        body.append(f"**The contract:** {entry['canonical'].strip()}\n\n"
                    "This difference is permanent and documented - account for "
                    "it when writing portable experiments.")
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

    if entry.get("verified"):
        body.append("*Observed on real devices: "
                    + " ".join(entry["verified"].split()) + "*")

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

    _check_spec(entries)
    _check_spec_against_docs()
    _check_colors()
    _check_corpus()
    _check_validators()
    _check_conversion_values()
    _check_test_matrix()
    return config


def _check_conversion_values():
    """The four bluetooth conversion attributes inline the vocabulary that
    spec/output.yml records under `conversions:` (established name by name
    from both parsers). Inlining is what lets every tool - the validator,
    the grammar, the rendered reference - see the values without a cross-
    file indirection; this check is what makes the duplication safe."""
    with open(os.path.join(SPEC_DIR, "output.yml")) as f:
        out = yaml.safe_load(f)
    with open(os.path.join(SPEC_DIR, "input.yml")) as f:
        inp = yaml.safe_load(f)
    conv = out.get("conversions") or {}
    vocab = {}
    for key in ("input", "output", "config"):
        sec = conv.get(key) or {}
        vocab[key] = set(sec.get("functions") or []) | {
            e["name"] for e in sec.get("extra") or []}

    def attr_values(doc, parent, name):
        for el in doc.get("elements") or []:
            if el.get("parent") == parent and el.get("name") == name:
                for a in el.get("attributes") or []:
                    if a["name"] == "conversion":
                        return set(a.get("values") or [])
        return set()

    expect = [
        ("input.yml bluetooth/output", attr_values(inp, "bluetooth", "output"),
         vocab["input"]),
        ("input.yml bluetooth/config", attr_values(inp, "bluetooth", "config"),
         vocab["config"]),
        ("output.yml bluetooth/input", attr_values(out, "bluetooth", "input"),
         vocab["output"]),
        ("output.yml bluetooth/config", attr_values(out, "bluetooth", "config"),
         vocab["config"]),
    ]
    problems = []
    for where, got, want in expect:
        if got != want:
            missing = sorted(want - got)
            extra = sorted(got - want)
            problems.append(f"{where}: conversion values drifted from the "
                            f"conversions section (missing {missing}, "
                            f"extra {extra})")
    if problems:
        raise ValueError("conversion vocabularies out of step:\n"
                         + "\n".join(f"  {p}" for p in problems))


def _check_test_matrix():
    """Keep test-matrix.yml and the app test suites in step.

    The matrix is the parity mechanism for cross-platform testing; see
    tools/check_test_matrix.py for the rules. Like the shipped-collection check, the app-repo comparisons run
    only when the checkouts sit next to this repository.
    """
    if not os.path.exists(os.path.join(ROOT, "test-matrix.yml")):
        return
    _ensure_path()
    import check_test_matrix
    problems = check_test_matrix.check()
    if problems:
        raise ValueError("test matrix is out of step:\n"
                         + "\n".join(f"  {p}" for p in problems))


def _check_spec_against_docs():
    """Fail if the documentation describes something the spec does not model.

    The prose is not authoritative, but it is a third pair of eyes: every gap it
    found in the views block was a real omission. Only this direction fails the
    build - "in the spec, not in the docs" is usually the docs being behind.
    """
    import io
    import contextlib
    _ensure_path()
    try:
        import spec_vs_docs
    except ImportError:
        return

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = spec_vs_docs.main()
    if rc:
        raise ValueError("the documentation describes constructs the spec does "
                         "not model:\n" + buf.getvalue())


def _check_colors():
    """Keep the colour table on the Colors page in step with spec/root.yml.

    The page table is hand-written because of its swatch markup, so nothing
    would notice a colour added or changed on one side only. The spec is the
    source; the page must list exactly the same names and hex values.
    """
    spec_path = os.path.join(SPEC_DIR, "root.yml")
    page_path = os.path.join(ROOT, "docs", "file-format", "colors.md")
    if not (os.path.exists(spec_path) and os.path.exists(page_path)):
        return
    with open(spec_path) as f:
        doc = yaml.safe_load(f) or {}
    spec_colors = {c["name"]: str(c["hex"])
                   for c in (doc.get("colors") or {}).get("names") or []}
    if not spec_colors:
        return
    page_colors = dict(re.findall(r"^\| `([a-z]+)` \| `([0-9a-f]{6})` \|",
                                  open(page_path).read(), re.M))
    problems = []
    for name in sorted(set(spec_colors) | set(page_colors)):
        s, p = spec_colors.get(name), page_colors.get(name)
        if s != p:
            problems.append(f"{name}: spec says {s}, the Colors page says {p}")
    if problems:
        raise ValueError("the colour table on the Colors page is out of step "
                         "with spec/root.yml:\n"
                         + "\n".join(f"  {p}" for p in problems))


def _check_corpus():
    """Fail the build if the corpus and the spec drift apart.

    Three checks, so the corpus keeps holding the parser surface still:

    * corpus/valid and corpus/generated must validate cleanly, and so must
      the example experiment files shipped with the documentation itself
      (docs/assets/examples);
    * the shipped experiment collection must too - checked only when the
      Android checkout sits next to this repository, as it does on the
      development machines, and skipped silently otherwise (CI checks out
      phyphox-docs alone). A failure here may also mean the experiments
      submodule is on an old commit, not that the spec is wrong;
    * every file in corpus/invalid must still produce the findings recorded
      in corpus/invalid/expected.yml. An invalid file going clean means the
      spec silently started accepting its defect.
    """
    corpus = os.path.join(ROOT, "corpus")
    if not os.path.isdir(corpus):
        return
    _ensure_path()
    import io
    import contextlib
    import xml.etree.ElementTree as ET
    import validate_experiments as ve

    clean_dirs = [os.path.join(corpus, d) for d in ("valid", "generated")
                  if os.path.isdir(os.path.join(corpus, d))]
    doc_examples = os.path.join(ROOT, "docs", "assets", "examples")
    if os.path.isdir(doc_examples):
        clean_dirs.append(doc_examples)
    shipped = os.path.normpath(os.path.join(
        ROOT, "..", "phyphox-android", "app", "src", "main", "assets",
        "experiments"))
    if os.path.isdir(shipped):
        clean_dirs.append(shipped)

    argv = sys.argv
    buf = io.StringIO()
    try:
        sys.argv = ["validate_experiments.py"] + clean_dirs
        with contextlib.redirect_stdout(buf):
            rc = ve.main()
    finally:
        sys.argv = argv
    if rc:
        raise ValueError(
            "corpus, docs examples or the shipped experiment collection no "
            "longer match spec/:\n" + buf.getvalue())

    invalid = os.path.join(corpus, "invalid")
    if not os.path.isdir(invalid):
        return
    with open(os.path.join(invalid, "expected.yml")) as f:
        expected = yaml.safe_load(f) or {}
    spec, common, slots, components = ve.load_spec()
    problems = []
    names = sorted(n for n in os.listdir(invalid) if n.endswith(".phyphox"))
    for extra in set(expected) - set(names):
        problems.append(f"expected.yml lists {extra}, which does not exist")
    for n, entry in expected.items():
        # each entry carries the validator findings AND the app-parser
        # behavior (rejects/accepts) the app test suites assert - see the
        # header of expected.yml and the unknown-attribute-ignored rule
        if (not isinstance(entry, dict)
                or entry.get("parser") not in ("rejects", "accepts")
                or not isinstance(entry.get("findings"), list)):
            problems.append(f"{n}: expected.yml entry needs parser: "
                            f"rejects|accepts and a findings list")
    for n in names:
        if n not in expected:
            problems.append(f"{n} has no entry in expected.yml")
            continue
        root = ve.normalize_namespace(
            ET.parse(os.path.join(invalid, n)).getroot())
        rep = ve.Report()
        for child in root:
            ve.check_element(child, "phyphox", spec, common, slots, components,
                             rep, "phyphox", n)
        # the slot/component pass is separate from the element walk in
        # validate_experiments.main - without it, an expected finding like an
        # unknown camera component can never be matched here (gap found
        # 2026-08-24 when exactly that expectation failed)
        ve.check_slots(root, slots, components, rep, n)
        details = [f"{kind}: {d}" for kind, lst in rep.items.items()
                   for _, d in lst]
        if not details:
            problems.append(f"{n} validates cleanly - the spec now accepts "
                            f"its documented defect")
            continue
        for sub in (expected[n] or {}).get("findings") or []:
            if not any(sub in d for d in details):
                problems.append(f"{n}: expected finding '{sub}' not produced; "
                                f"got: {'; '.join(sorted(set(details))[:3])}")
    if problems:
        raise ValueError("corpus/invalid is out of step:\n"
                         + "\n".join(f"  {p}" for p in problems))


# Invalid fixtures whose defect only validate_experiments can see (none at
# the moment). A file listed here is excused from the "every invalid fixture
# must fail the published validators" assertion below.
VALIDATOR_BLIND = set()


def _check_validators():
    """Regenerate the published RELAX NG / Schematron and prove them.

    tools/generate_validators.py derives docs/assets/validators/ from spec/
    on every build (write-if-changed, so mkdocs serve does not loop). The
    artifacts are then held to the same standard as the spec itself:

    * every file that must load - corpus/valid, corpus/generated, the docs'
      own example files, and the shipped collection when its checkout is
      present - passes the RELAX NG and produces no Schematron error
      (role="warning" asserts, the version gates, are advice and do not
      fail);
    * every corpus/invalid fixture fails at least one of the two, unless
      VALIDATOR_BLIND lists it as only detectable by validate_experiments.
    """
    corpus = os.path.join(ROOT, "corpus")
    if not os.path.isdir(corpus):
        return
    _ensure_path()
    import generate_validators as gv
    from lxml import etree
    from lxml.isoschematron import Schematron

    out_dir, _ = gv.generate()
    # the compact-syntax artifact is never executed by this build, so parse
    # it with an independent RNC parser or a syntax error would ship silently
    import rnc2rng
    rnc2rng.load(os.path.join(out_dir, "phyphox.rnc"))
    rng = etree.RelaxNG(etree.parse(os.path.join(out_dir, "phyphox.rng")))
    sch = Schematron(etree.parse(os.path.join(out_dir, "phyphox.sch")),
                     store_report=True)
    svrl = "{http://purl.oclc.org/dsdl/svrl}failed-assert"

    def sch_errors(tree):
        sch.validate(tree)
        return [fa.findtext("{http://purl.oclc.org/dsdl/svrl}text").strip()
                for fa in sch.validation_report.iter(svrl)
                if fa.get("role") != "warning"]

    clean_dirs = [os.path.join(corpus, d) for d in ("valid", "generated")
                  if os.path.isdir(os.path.join(corpus, d))]
    doc_examples = os.path.join(ROOT, "docs", "assets", "examples")
    if os.path.isdir(doc_examples):
        clean_dirs.append(doc_examples)
    shipped = os.path.normpath(os.path.join(
        ROOT, "..", "phyphox-android", "app", "src", "main", "assets",
        "experiments"))
    if os.path.isdir(shipped):
        clean_dirs.append(shipped)

    problems = []
    for d in clean_dirs:
        for dirpath, _dirs, files in os.walk(d):
            for fn in sorted(files):
                if not fn.endswith(".phyphox"):
                    continue
                path = os.path.join(dirpath, fn)
                rel = os.path.relpath(path, ROOT)
                tree = etree.parse(path)
                if not rng.validate(tree):
                    problems.append(
                        f"{rel}: {rng.error_log[0].message}"
                        if len(rng.error_log) else f"{rel}: RELAX NG rejects")
                for msg in sch_errors(tree)[:2]:
                    problems.append(f"{rel}: schematron: {msg[:120]}")
    if problems:
        raise ValueError(
            "the generated validators reject files that must load:\n"
            + "\n".join(f"  {p}" for p in problems[:20]))

    invalid = os.path.join(corpus, "invalid")
    if os.path.isdir(invalid):
        missed = []
        for fn in sorted(os.listdir(invalid)):
            if not fn.endswith(".phyphox") or fn in VALIDATOR_BLIND:
                continue
            try:
                tree = etree.parse(os.path.join(invalid, fn))
            except etree.XMLSyntaxError:
                continue  # not well-formed fails every validator trivially
            if rng.validate(tree) and not sch_errors(tree):
                missed.append(fn)
        if missed:
            raise ValueError(
                "corpus/invalid fixtures pass the generated validators - "
                "either the grammar lost a check or the fixture belongs in "
                "VALIDATOR_BLIND:\n"
                + "\n".join(f"  {m}" for m in missed))


def _check_spec(entries):
    """Keep spec/ and inconsistencies.yml in step.

    The format spec references divergences by id and the rules reference them
    back; without this a renamed entry would leave either pointing at nothing,
    and nobody reads three YAML files side by side often enough to notice.
    """
    if not os.path.isdir(SPEC_DIR):
        return

    problems = []
    # A block's root element is modelled in its own file, so <phyphox> naming
    # `input` or `analysis` as a child is satisfied across files.
    block_roots = set()
    for fn in sorted(os.listdir(SPEC_DIR)):
        if fn.endswith(".yml") and fn != "rules.yml":
            with open(os.path.join(SPEC_DIR, fn)) as f:
                doc = yaml.safe_load(f) or {}
            for e in doc.get("elements") or []:
                if e.get("parent") == "phyphox":
                    block_roots.add(e["name"])
    rules_path = os.path.join(SPEC_DIR, "rules.yml")
    rule_ids = set()
    if os.path.exists(rules_path):
        with open(rules_path) as f:
            doc = yaml.safe_load(f) or {}
        for rule in doc.get("rules") or []:
            rule_ids.add(rule["id"])
            ref = rule.get("inconsistency")
            if ref and ref not in entries:
                problems.append(f"rules.yml: rule {rule['id']} names unknown "
                                f"inconsistency {ref}")
            elif ref and entries[ref].get("status") != "decided":
                problems.append(
                    f"rules.yml: rule {rule['id']} states settled behaviour but "
                    f"{ref} is status '{entries[ref].get('status')}' - a rule may "
                    f"only exist once the divergence has been decided")
        for q in doc.get("open_questions") or []:
            ref = q.get("inconsistency")
            if ref and ref not in entries:
                problems.append(f"rules.yml: open question names unknown "
                                f"inconsistency {ref}")

    for fn in sorted(os.listdir(SPEC_DIR)):
        if not fn.endswith(".yml") or fn == "rules.yml":
            continue
        with open(os.path.join(SPEC_DIR, fn)) as f:
            doc = yaml.safe_load(f) or {}
        elements = doc.get("elements") or []

        # Child elements must actually be modelled. Declaring `children: [...]`
        # and stopping there is how the graph data picker and the button's
        # trigger tag went missing - the name was written down, the element
        # behind it never was, and nothing complained.
        modelled = {(e.get("parent"), e["name"]) for e in elements}
        # YAML 1.1 turns bare true/false/yes/no/on/off/null into non-strings.
        # The `if` module has slots literally named "true" and "false", which
        # were silently parsed as booleans until a validator tripped over them.
        for element in elements:
            for key in ("inputs", "outputs"):
                for slot in (element.get(key) or []):
                    if isinstance(slot, dict) and not isinstance(slot.get("name"), str):
                        problems.append(
                            f"{fn}: {element['name']}/{key} has a slot named "
                            f"{slot.get('name')!r}, which YAML did not read as a "
                            f"string - quote it")
            for attr in element.get("attributes") or []:
                if not isinstance(attr.get("name"), str):
                    problems.append(f"{fn}: {element['name']} has an attribute named "
                                    f"{attr.get('name')!r} - quote it")

        # An attribute cannot predate the element it belongs to. This is what
        # exposed aeFPSTarget being documented as file format 1.3 when the camera
        # element itself arrived in 1.17 - a copy-paste error in the prose that
        # had been sitting there unnoticed.
        def _ver(v):
            try:
                return tuple(int(x) for x in str(v).split("."))
            except ValueError:
                return None

        for element in elements:
            ev = _ver(element.get("since"))
            for attr in element.get("attributes") or []:
                av = _ver(attr.get("since"))
                if ev and av and av < ev:
                    problems.append(
                        f"{fn}: {element['name']}/{attr['name']} is marked since "
                        f"{attr['since']} but its element only exists from "
                        f"{element['since']}")

        for element in elements:
            for child in element.get("children") or []:
                if (element["name"], child) in modelled:
                    continue
                # Some elements describe a child once with a key rather than as
                # a separate element: input modules list their components under
                # `outputs:`, and analysis modules list their slots under
                # `inputs:`/`outputs:` with the shared attributes in `common:`.
                if child == "output" and element.get("outputs"):
                    continue
                if child == "input" and element.get("inputs"):
                    continue
                if element["name"] == "phyphox" and child in block_roots:
                    continue
                problems.append(f"{fn}: {element['name']} declares child "
                                f"'{child}' but no such element is modelled")
            parent = element.get("parent")
            if parent:
                owner = next((e for e in elements if e["name"] == parent), None)
                if owner is not None and element["name"] not in (owner.get("children") or []):
                    problems.append(f"{fn}: {parent}/{element['name']} is modelled "
                                    f"but not listed in {parent}'s children")

        # attributes shared by every module of a block live under `common:`
        for group, items in (doc.get("common") or {}).items():
            for h in items or []:
                where = f"{fn}: common/{group}/{h.get('name')}"
                ref = h.get("inconsistency")
                if h.get("agreement") in ("divergent", "undecided") and not ref:
                    problems.append(f"{where}: agreement '{h['agreement']}' "
                                    f"requires an inconsistency id")
                if ref and ref not in entries:
                    problems.append(f"{where}: unknown inconsistency {ref}")
                for r in h.get("rules") or []:
                    if r not in rule_ids:
                        problems.append(f"{where}: unknown rule {r}")

        for element in elements:
            holders = list(element.get("attributes") or [])
            # Input modules describe their component set as a mapping under
            # `outputs:`; analysis modules use the same key for a plain list of
            # slot names, which carries no agreement of its own.
            if isinstance(element.get("outputs"), dict):
                holders.append(element["outputs"])
            if isinstance(element.get("slot_constraints"), dict):
                holders.append(element["slot_constraints"])
            # individual analysis slots may carry their own agreement
            for key in ("inputs", "outputs"):
                if isinstance(element.get(key), list):
                    holders += [x for x in element[key]
                                if isinstance(x, dict) and x.get("agreement")]
            for h in holders:
                where = f"{fn}: {element['name']}/{h.get('name', '<outputs>')}"
                ref = h.get("inconsistency")
                if h.get("agreement") in ("divergent", "undecided") and not ref:
                    problems.append(f"{where}: agreement '{h['agreement']}' "
                                    f"requires an inconsistency id")
                if ref and ref not in entries:
                    problems.append(f"{where}: unknown inconsistency {ref}")
                for r in h.get("rules") or []:
                    if r not in rule_ids:
                        problems.append(f"{where}: unknown rule {r}")

    if problems:
        raise ValueError("spec/ is out of step with inconsistencies.yml:\n"
                         + "\n".join(f"  {p}" for p in problems))


_api_referenced = set()
_spec = None


def _expand_spec(markdown, link_prefix, src):
    """Expand {{spec:BLOCK/PARENT/NAME}} markers from spec/*.yml."""
    global _spec
    _ensure_path()
    import spec_reference

    if "{{spec:" not in markdown:
        return markdown
    if _spec is None:
        _spec = spec_reference.Spec()
    state = spec_reference.PageState(link_prefix)
    # a marker the author already placed by hand counts as this page's one
    # full admonition for that entry - the spec-driven emission must not
    # render a second copy further down
    state.seen.update(re.findall(r"\{\{inconsistency:([a-z0-9-]+)\}\}",
                                 markdown))
    try:
        out = spec_reference.expand(markdown, _spec, state)
    except KeyError as e:
        raise ValueError(f"{src}: {e.args[0]}")
    if "{{spec:" in out:
        stray = re.findall(r"\{\{spec:[^}]*\}\}", out)
        raise ValueError(
            f"{src}: malformed reference marker(s) {stray}. The form is "
            f"{{{{spec:BLOCK/PARENT/NAME}}}}, optionally with |xml, "
            f"|attributes or |slots.")
    return out


def on_page_markdown(markdown, page, config, files, **kwargs):
    entries = _load()
    src = page.file.src_uri

    depth = src.count("/")
    link_prefix = "../" * depth if depth else ""

    if src == LIST_PAGE:
        return markdown + "\n" + _render_list()

    # Reference sections are generated from spec/. This runs first because the
    # generated text emits {{inconsistency:...}} markers of its own, which the
    # substitution below then expands - that is how a divergence recorded in
    # the spec reaches the page it belongs on without anyone placing a marker.
    markdown = _expand_spec(markdown, link_prefix, src)

    def expand(m):
        key = m.group(1)
        if key not in entries:
            raise ValueError(
                f"{src}: {{{{inconsistency:{key}}}}} refers to an id that is not "
                f"in inconsistencies.yml. Known ids: {', '.join(sorted(entries))}")
        return _admonition(entries[key], link_prefix)

    return MARKER.sub(expand, markdown)


# --------------------------------------------------- since-badge relocation --

# An element-level "added in x.y" badge (class phyphox-since-element, emitted
# by spec_reference._since_badge) belongs beside the section heading, not down
# in the generated block - beside the attribute list it wrongly suggests the
# attributes were added later. The headings are hand-written markdown and the
# badges are generated, so the two only meet here, after both have been
# rendered to HTML. Relocating at this stage cannot change heading ids, page
# anchors or the nav: those are all derived from the markdown before
# on_page_content runs.

_BADGE_P = re.compile(
    r'<p>((?:<a|<span)[^>]*class="[^"]*phyphox-since-element[^"]*"[^>]*>'
    r'.*?(?:</a>|</span>))</p>')
_HEADING_CLOSE = re.compile(r"</h[1-6]>")


def on_page_content(html, page, config, files, **kwargs):
    while True:
        m = _BADGE_P.search(html)
        if m is None:
            return html
        badge = m.group(1).replace(" phyphox-since-element", "")
        closes = [c for c in _HEADING_CLOSE.finditer(html, 0, m.start())]
        target = closes[-1] if closes else None
        # Only the first badge after a heading moves into it: a second one in
        # the same section documents a child element, and hoisting it would
        # pin the wrong version to the heading. It stays where it is (still
        # floated right), just without the relocation marker.
        if target is None or "phyphox-since" in html[html.rfind("<h", 0, target.start()):target.start()]:
            html = html[:m.start()] + "<p>" + badge + "</p>" + html[m.end():]
            continue
        html = (html[:target.start()] + badge + html[target.start():m.start()]
                + html[m.end():])


def _render_list():
    entries = _load()
    if not entries:
        return ("Nothing is currently recorded. That is unlikely to mean the "
                "implementations agree - see the note above.\n")

    by_status = {"open": [], "decided": [], "permanent": []}
    for e in entries.values():
        key = e.get("status", "open")
        if key == "decided" and e.get("permanent"):
            key = "permanent"
        by_status.setdefault(key, []).append(e)

    out = []
    headings = [
        ("open", "Undecided",
         "The implementations disagree and the canonical behaviour has not been "
         "chosen yet. Do not rely on any of these."),
        ("decided", "Decided, not yet fixed",
         "The correct behaviour is settled. The implementations that disagree "
         "are buggy and will be corrected."),
        ("permanent", "Permanent platform differences",
         "These differences are the intended contract - a platform limitation "
         "or a deliberate design choice. They will not be reconciled; account "
         "for them when writing portable experiments."),
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
            if e.get("verified"):
                out.append("*Observed on real devices: "
                           + " ".join(e["verified"].split()) + "*\n")
            if e.get("issue"):
                out.append(f"[Tracking issue]({e['issue']})\n")
    return "\n".join(out)


# --------------------------------------------------------------------------
# No third-party requests
# --------------------------------------------------------------------------
#
# Visitors must be able to read this site without their browser contacting
# anyone but the host serving it. That is easy to lose by accident: Material
# pulls Roboto from fonts.googleapis.com unless `font: false` is set, mounts a
# component that calls api.github.com when repo_url is present, and Swagger UI
# ships a validator badge that posts the spec URL to validator.swagger.io. All
# three are switched off - this check is what stops them coming back unnoticed
# on the next dependency bump.
#
# Only *automatic* fetches count. Ordinary hyperlinks are fine; a visitor
# choosing to follow one is not the site phoning home.

_RESOURCE_TAG = re.compile(
    r"<(link|script|img|iframe|source|video|audio|embed|object)\b([^>]*)>", re.I)
_URL_ATTR = re.compile(r"(?:src|href|data)\s*=\s*[\"']([^\"']+)[\"']", re.I)
_REL_ATTR = re.compile(r"rel\s*=\s*[\"']([^\"']+)[\"']", re.I)
_CSS_URL = re.compile(r"(?:url\(\s*[\"']?|@import\s+[\"'])(https?:)?//([^)\"'\s]+)")

# rel values that describe a relationship without fetching anything.
_NON_FETCHING_RELS = {"canonical", "alternate", "author", "license", "me",
                      "nofollow", "noopener", "noreferrer"}


def _is_absolute(url):
    return url.startswith(("http://", "https://", "//"))


def on_post_build(config, **kwargs):
    site_dir = config["site_dir"]
    offenders = []

    for root, _, files in os.walk(site_dir):
        for fn in files:
            path = os.path.join(root, fn)
            rel_path = os.path.relpath(path, site_dir)
            if fn.endswith((".html", ".htm")):
                with open(path, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                for m in _RESOURCE_TAG.finditer(text):
                    tag, attrs = m.group(1).lower(), m.group(2)
                    url = _URL_ATTR.search(attrs)
                    if not url or not _is_absolute(url.group(1)):
                        continue
                    rel = _REL_ATTR.search(attrs)
                    rels = set((rel.group(1) if rel else "").lower().split())
                    if rels & _NON_FETCHING_RELS:
                        continue
                    offenders.append(f"{rel_path}: <{tag}> {url.group(1)}")
            elif fn.endswith(".css"):
                with open(path, encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                for m in _CSS_URL.finditer(text):
                    offenders.append(f"{rel_path}: css url() //{m.group(2)}")

    if offenders:
        shown = "\n".join(f"  {o}" for o in sorted(set(offenders))[:20])
        more = len(set(offenders)) - 20
        raise ValueError(
            "The built site would make visitors' browsers fetch from a third "
            "party:\n" + shown
            + (f"\n  ... and {more} more" if more > 0 else "")
            + "\n\nEverything the site needs must be served from the site "
              "itself. See the 'No third-party requests' note in tools/hooks.py.")
