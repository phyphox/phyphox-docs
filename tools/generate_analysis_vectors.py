#!/usr/bin/env python3
"""Generate the analysis golden-vector artifacts from their case files.

corpus/analysis/cases/<module>.yml is the human-authored source: per case
the buffers (with init values - the real parser is the injection path), the
module's input/output tags, its attributes, how many analysis cycles to run
and the expected buffer contents afterwards. This script derives, per case:

    corpus/analysis/vectors/<module>/<case>.phyphox        the runnable file
    corpus/analysis/vectors/<module>/<case>.expected.json  what the app
                                                           runners compare

Both are committed; the docs build regenerates them and fails on drift
(tools/hooks.py, _check_analysis_vectors), so the YAML stays the single
source of truth without the runners needing a YAML parser or this script.

Everything here is deterministic templating - no numerics. Expected values
are authored into the case files (computed with tools/analysis_reference.py
where the module is tractable, pinned from the audit rulings or platform
runs where it is not; the `expected_source` field records which).

Run with --check to verify the committed artifacts match (what the build
does); without it, artifacts are (re)written.
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CASES_DIR = os.path.join(ROOT, "corpus", "analysis", "cases")
VECTORS_DIR = os.path.join(ROOT, "corpus", "analysis", "vectors")
SPEC_ANALYSIS = os.path.join(ROOT, "spec", "analysis.yml")

# Attributes whose use raises the file format version above the module's own
# `since`. keep/append are the 1.17 spellings of clear=; cycles arrived in 1.10.
ATTR_SINCE = {"keep": "1.17", "append": "1.17", "cycles": "1.10"}

DEFAULT_TOL = {"rel": 1e-6, "abs": 1e-9}


def _ver(s):
    a, b = str(s).split(".")
    return (int(a), int(b))


def load_spec_modules():
    with open(SPEC_ANALYSIS) as f:
        spec = yaml.safe_load(f)
    modules = {}
    analysis_attrs = {}
    for el in spec.get("elements") or []:
        if el.get("parent") == "analysis":
            modules[el["name"]] = {
                "since": el.get("since") or spec.get("since") or "1.0",
                "attrs": {a["name"]: a.get("since") or el.get("since")
                          or spec.get("since") or "1.0"
                          for a in el.get("attributes") or []},
            }
        elif el.get("name") == "analysis":
            analysis_attrs = {a["name"]: a.get("since") or "1.0"
                              for a in el.get("attributes") or []}
    return modules, analysis_attrs


def case_modules(module, case):
    """A case is one module by default; execution-semantics cases may chain
    several via a `modules:` list (each entry: module, attributes, inputs,
    outputs), emitted in order."""
    if case.get("modules"):
        return case["modules"]
    if not module:
        raise ValueError("case without modules: needs a file-level module")
    return [{"module": module, "attributes": case.get("attributes"),
             "inputs": case.get("inputs"), "outputs": case.get("outputs")}]


def fmt_number(v):
    """Format a number the way the file format reads it back exactly."""
    if isinstance(v, str):
        # normalize to the format's lexical spellings ("inf" is NOT valid
        # in the file format - number-invalid-value allows only NaN,
        # Infinity and -Infinity, case-insensitively)
        s = v.strip().lower()
        if s == "nan":
            return "NaN"
        if s in ("inf", "infinity", "+inf", "+infinity"):
            return "Infinity"
        if s in ("-inf", "-infinity"):
            return "-Infinity"
        return v
    if isinstance(v, bool):
        raise ValueError("booleans are not buffer values")
    if isinstance(v, int):
        return str(v)
    if math.isnan(v):
        return "NaN"
    if math.isinf(v):
        return "Infinity" if v > 0 else "-Infinity"
    return repr(v)


def norm_expect_value(v):
    """Normalize an expected value for the JSON file: numbers stay numbers,
    the non-finite spellings become canonical lowercase strings."""
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("nan",):
            return "nan"
        if s in ("inf", "infinity", "+inf", "+infinity"):
            return "inf"
        if s in ("-inf", "-infinity"):
            return "-inf"
        raise ValueError(f"expected value {v!r} is neither a number nor nan/inf/-inf")
    if isinstance(v, bool):
        raise ValueError("booleans are not buffer values")
    if isinstance(v, float) and math.isnan(v):
        return "nan"
    if isinstance(v, float) and math.isinf(v):
        return "inf" if v > 0 else "-inf"
    return v


def _as_name(v):
    """YAML reads `as: true` as a boolean - map it back to the slot name."""
    if isinstance(v, bool):
        return "true" if v else "false"
    return xml_escape(v)


def xml_escape(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def case_version(module, case, modules, analysis_attrs):
    versions = []
    for mod in case_modules(module, case):
        name = mod["module"]
        if name not in modules:
            raise ValueError(f"{case['name']}: no analysis module {name} in the spec")
        m = modules[name]
        versions.append(m["since"])
        for aname in (mod.get("attributes") or {}):
            if aname == "cycles":
                versions.append(ATTR_SINCE["cycles"])
            elif aname in m["attrs"]:
                versions.append(m["attrs"][aname])
            else:
                raise ValueError(f"{name}/{case['name']}: attribute {aname} not in spec")
        for tag in (mod.get("inputs") or []) + (mod.get("outputs") or []):
            for k in tag:
                if k in ATTR_SINCE:
                    versions.append(ATTR_SINCE[k])
    for aname in (case.get("analysis_attributes") or {}):
        if aname not in analysis_attrs:
            raise ValueError(f"{case['name']}: analysis attribute {aname} not in spec")
        versions.append(analysis_attrs[aname])
    if case.get("version"):
        versions.append(case["version"])
    return max(versions, key=_ver)


def emit_phyphox(module, case, modules, analysis_attrs):
    version = case_version(module, case, modules, analysis_attrs)
    stem = module or "execution"
    lines = []
    a = lines.append

    def attr_str(attrs):
        return "".join(
            f' {k}="{xml_escape(v).lower() if isinstance(v, bool) else xml_escape(v)}"'
            for k, v in (attrs or {}).items())

    a(f'<phyphox xmlns="http://phyphox.org/xml" version="{version}" locale="en">')
    a(f"    <title>golden vector: {xml_escape(stem)}/{xml_escape(case['name'])}</title>")
    a("    <category>Analysis golden vectors</category>")
    a(f"    <description>Generated from corpus/analysis/cases/{stem}.yml - do not edit.</description>")
    a("    <data-containers>")
    for name, spec in (case.get("buffers") or {}).items():
        spec = spec or {}
        attrs = f' size="{int(spec.get("size", 1))}"'
        init = spec.get("init")
        if init:
            attrs += f' init="{",".join(fmt_number(v) for v in init)}"'
        if spec.get("static"):
            attrs += ' static="true"'
        a(f"        <container{attrs}>{xml_escape(name)}</container>")
    a("    </data-containers>")
    a(f"    <analysis{attr_str(case.get('analysis_attributes'))}>")
    for mod in case_modules(module, case):
        a(f"        <{mod['module']}{attr_str(mod.get('attributes'))}>")
        for tag in mod.get("inputs") or []:
            attrs = ""
            if "as" in tag:
                attrs += f' as="{_as_name(tag["as"])}"'
            if tag.get("keep"):
                attrs += ' keep="true"'
            if tag.get("empty"):
                a(f'            <input{attrs} type="empty" />')
            elif "value" in tag:
                a(f'            <input{attrs} type="value">{fmt_number(tag["value"])}</input>')
            else:
                a(f'            <input{attrs}>{xml_escape(tag["buffer"])}</input>')
        for tag in mod.get("outputs") or []:
            attrs = ""
            if "as" in tag:
                attrs += f' as="{_as_name(tag["as"])}"'
            if tag.get("append"):
                attrs += ' append="true"'
            a(f'            <output{attrs}>{xml_escape(tag["buffer"])}</output>')
        a(f"        </{mod['module']}>")
    a("    </analysis>")
    # The real loading path requires at least one view with a label and at
    # least one element on both platforms (found by the Android runner,
    # 2026-08-24); a separator (since 1.0) is the cheapest element that
    # reads no buffer.
    a("    <views>")
    a('        <view label="golden vector">')
    a("            <separator />")
    a("        </view>")
    a("    </views>")
    a("</phyphox>")
    return "\n".join(lines) + "\n"


def emit_expected(module, case):
    cycles = int(case.get("cycles", 1))
    buffers = set(case.get("buffers") or {})

    def norm_buffer_expect(spec):
        if isinstance(spec, list):
            spec = {"values": spec}
        out = {"values": [norm_expect_value(v) for v in spec["values"]]}
        for k in ("rel", "abs"):
            if k in spec:
                out[k] = spec[k]
        return out

    def norm_stage(stage, after_cycle):
        for b in stage:
            if b not in buffers:
                raise ValueError(f"{module}/{case['name']}: expected buffer "
                                 f"{b} is not declared")
        return {"after_cycle": after_cycle,
                "buffers": {b: norm_buffer_expect(v) for b, v in stage.items()}}

    if "expect_per_cycle" in case:
        stages = [norm_stage(s, i + 1)
                  for i, s in enumerate(case["expect_per_cycle"])]
        if len(stages) != cycles:
            raise ValueError(f"{module}/{case['name']}: expect_per_cycle has "
                             f"{len(stages)} entries for cycles: {cycles}")
    else:
        stages = [norm_stage(case["expect"], cycles)]

    doc = {
        "module": module,
        "case": case["name"],
        "cycles": cycles,
        "default_tolerance": DEFAULT_TOL.copy(),
        "expect": stages,
    }
    if case.get("tolerance"):
        doc["default_tolerance"].update(case["tolerance"])
    if case.get("expected_source"):
        doc["expected_source"] = case["expected_source"]
    return json.dumps(doc, indent=1, sort_keys=True) + "\n"


def generate(check=False):
    modules, analysis_attrs = load_spec_modules()
    problems = []
    wanted = {}

    for fn in sorted(os.listdir(CASES_DIR)) if os.path.isdir(CASES_DIR) else []:
        if not fn.endswith(".yml"):
            continue
        with open(os.path.join(CASES_DIR, fn)) as f:
            doc = yaml.safe_load(f)
        module = doc.get("module")
        stem = os.path.splitext(fn)[0]
        if module is None:
            # a file of multi-module execution-semantics cases; every case
            # must carry its own modules: list
            if any(not c.get("modules") for c in doc.get("cases") or []):
                problems.append(f"{fn}: no module field, so every case "
                                f"needs a modules list")
                continue
        elif module != stem:
            problems.append(f"{fn}: module field must match the file name")
            continue
        elif module not in modules:
            problems.append(f"{fn}: no analysis module {module} in the spec")
            continue
        names = set()
        for case in doc.get("cases") or []:
            if case["name"] in names:
                problems.append(f"{stem}: duplicate case name {case['name']}")
                continue
            names.add(case["name"])
            base = os.path.join(stem, case["name"])
            try:
                wanted[base + ".phyphox"] = emit_phyphox(module, case, modules,
                                                         analysis_attrs)
                wanted[base + ".expected.json"] = emit_expected(stem, case)
            except (ValueError, KeyError) as e:
                problems.append(f"{stem}/{case.get('name', '?')}: {e}")

    existing = {}
    if os.path.isdir(VECTORS_DIR):
        for dirpath, _, names in os.walk(VECTORS_DIR):
            for n in names:
                p = os.path.join(dirpath, n)
                existing[os.path.relpath(p, VECTORS_DIR)] = p

    if check:
        for rel, content in sorted(wanted.items()):
            p = os.path.join(VECTORS_DIR, rel)
            if rel not in existing:
                problems.append(f"vectors/{rel} is missing - run "
                                f"tools/generate_analysis_vectors.py")
            else:
                with open(p) as f:
                    if f.read() != content:
                        problems.append(f"vectors/{rel} is stale - run "
                                        f"tools/generate_analysis_vectors.py")
        for rel in sorted(set(existing) - set(wanted)):
            problems.append(f"vectors/{rel} has no case - delete it or add the case")
        return problems

    for rel, content in sorted(wanted.items()):
        p = os.path.join(VECTORS_DIR, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(content)
    for rel in sorted(set(existing) - set(wanted)):
        os.remove(existing[rel])
        print(f"removed stale vectors/{rel}")
    print(f"{len(wanted) // 2} case(s) generated into corpus/analysis/vectors/")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="verify committed artifacts instead of writing them")
    args = ap.parse_args()
    problems = generate(check=args.check)
    for p in problems:
        print(f"  ! {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
