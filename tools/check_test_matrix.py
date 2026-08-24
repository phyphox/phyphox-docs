#!/usr/bin/env python3
"""Check test-matrix.yml against the app repositories' test tags.

    python3 tools/check_test_matrix.py

The matrix (test-matrix.yml, repository root) lists every cross-platform
test; app tests carry their row id as a tag comment ("phyphox-test: <id>").
This tool verifies the two stay in step:

  * the matrix itself is well-formed (unique kebab-case ids, known tiers,
    platforms, statuses);
  * every tag found in an app repo names a matrix row (typo guard) - a
    violation FAILS;
  * every `active` row is tagged in each platform repo it names - a missing
    tag FAILS, because an implemented test that disappears is a regression;
  * `planned` rows are reported as information: which platforms already
    carry the tag, and which rows are ready to be flipped to active.

App repos are looked for next to this repository (../phyphox-android,
../phyphox-ios), the same convention as the shipped-collection check; a
missing checkout skips that repo's checks silently (CI checks out
phyphox-docs alone).

Exit status 1 on any failure; tools/hooks.py runs this as part of
`mkdocs build --strict`.
"""

import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX = os.path.join(ROOT, "test-matrix.yml")

TAG_RE = re.compile(r"phyphox-test:\s*([a-z0-9-]+)")
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TIERS = {"T0", "T1", "T2", "T3"}
PLATFORMS = {"android", "ios"}
STATUSES = {"planned", "active"}
# App test sources carry the tag as a code comment; rows driven by a
# host-side tool (the T1 drivers in phyphox-docs) carry it as a
# `# phyphox-test: <id>` comment in the repo's CI workflow instead, so
# workflow YAML is scanned too.
SOURCE_EXT = {".java", ".kt", ".swift", ".yml", ".yaml"}

REPOS = {
    "android": os.path.normpath(os.path.join(ROOT, "..", "phyphox-android")),
    "ios": os.path.normpath(os.path.join(ROOT, "..", "phyphox-ios")),
}


def load_matrix():
    with open(MATRIX, encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    rows = doc.get("tests") or []
    problems = []
    seen = set()
    for i, row in enumerate(rows):
        where = f"test-matrix.yml row {i + 1} ({row.get('id', '?')})"
        rid = row.get("id")
        if not rid or not ID_RE.match(str(rid)):
            problems.append(f"{where}: id must be kebab-case")
        elif rid in seen:
            problems.append(f"{where}: duplicate id")
        seen.add(rid)
        if row.get("tier") not in TIERS:
            problems.append(f"{where}: tier must be one of {sorted(TIERS)}")
        plats = row.get("platforms")
        if (not isinstance(plats, list) or not plats
                or not set(plats) <= PLATFORMS):
            problems.append(f"{where}: platforms must be a non-empty subset "
                            f"of {sorted(PLATFORMS)}")
        if row.get("status") not in STATUSES:
            problems.append(f"{where}: status must be one of "
                            f"{sorted(STATUSES)}")
        for field in ("area", "description"):
            if not row.get(field):
                problems.append(f"{where}: missing {field}")
    return rows, problems


def scan_tags(repo_root):
    """{tag id: [relative file paths]} across the repo's source files."""
    tags = {}
    for dirpath, dirnames, filenames in os.walk(repo_root):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "build", "Pods", ".gradle")]
        for fn in filenames:
            if os.path.splitext(fn)[1] not in SOURCE_EXT:
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            for m in TAG_RE.finditer(text):
                tags.setdefault(m.group(1), []).append(
                    os.path.relpath(path, repo_root))
    return tags


def check(verbose=True):
    """Returns a list of failures; prints informational lines if verbose."""
    rows, problems = load_matrix()
    by_id = {r.get("id"): r for r in rows}

    found = {}
    for platform, repo in REPOS.items():
        if not os.path.isdir(repo):
            continue
        found[platform] = scan_tags(repo)

    for platform, tags in found.items():
        for tag, files in sorted(tags.items()):
            if tag not in by_id:
                problems.append(
                    f"{platform}: tag 'phyphox-test: {tag}' "
                    f"({files[0]}) names no row in test-matrix.yml")

    ready = []
    for row in rows:
        rid = row.get("id")
        for platform in row.get("platforms") or []:
            if platform not in found:
                continue  # checkout absent - skipped silently
            present = rid in found[platform]
            if row.get("status") == "active" and not present:
                problems.append(
                    f"{platform}: active test '{rid}' has no "
                    f"'phyphox-test: {rid}' tag - an implemented test "
                    f"disappeared, or the row was activated too early")
        if row.get("status") == "planned" and found:
            covered = [p for p in row.get("platforms") or []
                       if p in found and rid in found[p]]
            missing = [p for p in row.get("platforms") or []
                       if p in found and rid not in found[p]]
            if covered and not missing:
                ready.append(rid)
            elif covered and verbose:
                print(f"test-matrix: planned '{rid}' implemented on "
                      f"{', '.join(covered)}, waiting for "
                      f"{', '.join(missing)}")
    if ready and verbose:
        print(f"test-matrix: ready to flip to active: {', '.join(ready)}")
    return problems


def main():
    problems = check()
    if problems:
        print("test matrix check failed:", file=sys.stderr)
        for p in problems:
            print(f"  {p}", file=sys.stderr)
        return 1
    print("test matrix OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
