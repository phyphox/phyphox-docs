#!/usr/bin/env python3
"""Validate an exported data file against its experiment's export block.

The export area of the test strategy: an experiment's export must yield a
file that parses, holds one table per export set, carries the set's data
names as column headers, and (where the source produced data) rows of
values. This tool checks exactly that, host-side - the T1/T2 drivers pull
the file via GET /export and call validate() per format.

Formats, by the remote API's fixed index (docs/remote-interface/
openapi.yaml, /export):

    0  Excel .xlsx           one worksheet per set
    1  CSV comma, point      a zip with one .csv per set, always - this
    2  CSV tab, point        endpoint runs the experiment's full export
    3  CSV semicolon, point  (Android getType(false), iOS singleSet:
    4  CSV tab, comma        false) and answers application/zip. A BARE
    5  CSV semicolon, comma  .csv is what the graph view's own export
                             produces, and it does not come through
                             /export at all (maintainer, 2026-08-30).

Usage:
    validate_export.py exported.file --phyphox experiment.phyphox \\
        --format 1 [--require-rows]

Exit 0 when the file matches, 1 with a finding list otherwise.
"""

import argparse
import io
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

CSV_SEP = {1: ",", 2: "\t", 3: ";", 4: "\t", 5: ";"}


def export_sets(phyphox_path):
    """[(set name, [column names], [source buffer names])] from the
    experiment's export block. The buffer names let a driver decide per
    set whether data rows can be expected on the current target (a set
    whose source buffers never filled - no microphone on an emulator, no
    GPS fix - is validated structurally but not required to have rows)."""
    root = ET.parse(phyphox_path).getroot()
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"
    sets = []
    for exp in root.iter(f"{ns}export"):
        for st in exp.findall(f"{ns}set"):
            datas = st.findall(f"{ns}data")
            names = [d.get("name") for d in datas]
            buffers = [(d.text or "").strip() for d in datas]
            sets.append((st.get("name"), names, buffers))
    return sets


def _norm(s):
    """Set names become file/sheet names with platform-specific
    sanitizing - compare on the alphanumeric skeleton, case-folded."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())


def _xlsx_tables(data):
    """{sheet name: (headers, row count)} from an .xlsx file."""
    z = zipfile.ZipFile(io.BytesIO(data))
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    relmap = {rel.get("Id"): rel.get("Target")
              for rel in rels.iter("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")}
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in sst.findall("m:si", ns):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t")))
    tables = {}
    for sheet in wb.find("m:sheets", ns):
        name = sheet.get("name")
        target = relmap[sheet.get(f"{{{ns['r']}}}id")]
        if not target.startswith("xl/"):
            target = "xl/" + target.lstrip("/")
        ws = ET.fromstring(z.read(target))
        rows = ws.findall(".//m:row", ns)
        headers = []
        if rows:
            for c in rows[0].findall("m:c", ns):
                v = c.find("m:v", ns)
                is_ = c.find("m:is", ns)
                if is_ is not None:     # inline string (t="inlineStr")
                    headers.append("".join(
                        t.text or "" for t in is_.iter(f"{{{ns['m']}}}t")))
                elif v is None:
                    headers.append("")
                elif c.get("t") == "s":
                    headers.append(shared[int(v.text)])
                else:
                    headers.append(v.text)
        tables[name] = (headers, max(0, len(rows) - 1))
    return tables


def _csv_tables(data, sep, single_set_name=None):
    """{name: (headers, row count)} from the zip of CSVs /export returns.

    A bare .csv raises rather than being accepted: /export never produces
    one, so receiving it means the response came from somewhere else or a
    single-set export stopped zipping. Taking it silently - which this did
    until 2026-08-30, on an assumption nobody had measured - validated
    that one file against the single set it was told to expect and
    reported a clean export.
    """
    if data[:4] == b"PK\x03\x04":
        z = zipfile.ZipFile(io.BytesIO(data))
        out = {}
        for entry in z.namelist():
            if entry.endswith("/"):
                continue
            # the archive also carries metadata files under meta/; keyed
            # by basename they would shadow an export set of the same
            # name ("Time" in sonar - found by the Android T1 run)
            if "meta" in entry.split("/")[:-1]:
                continue
            name = entry.rsplit("/", 1)[-1]
            name = name[:-4] if name.lower().endswith(".csv") else name
            out[name] = _one_csv(z.read(entry), sep)
        return out
    raise ValueError(
        "a bare .csv, where this endpoint always returns a zip with one "
        "file per export set - a bare file is what the graph view's own "
        "export produces")


def _one_csv(data, sep):
    lines = [ln for ln in data.decode("utf-8", "replace").splitlines()
             if ln.strip()]
    if not lines:
        return ([], 0)
    headers = [h.strip().strip('"') for h in lines[0].split(sep)]
    return (headers, len(lines) - 1)


def validate(data, sets, fmt, require_rows=False, require_rows_for=None):
    """Return a list of findings (empty = the export matches).

    require_rows_for: optional set of set names - with require_rows on,
    only those sets must have data rows (the driver passes the sets whose
    source buffers actually filled on this target; the metadata sheets in
    xlsx are ignored either way). None means every set."""
    problems = []
    try:
        if fmt == 0:
            tables = _xlsx_tables(data)
        else:
            tables = _csv_tables(data, CSV_SEP[fmt],
                                 sets[0][0] if len(sets) == 1 else None)
    except Exception as e:
        return [f"file does not parse as format {fmt}: "
                f"{type(e).__name__}: {e}"]
    bynorm = {_norm(k): (k, v) for k, v in tables.items()}
    for entry in sets:
        set_name, columns = entry[0], entry[1]
        hit = bynorm.get(_norm(set_name))
        if hit is None:
            problems.append(f"set {set_name!r}: no table (have: "
                            f"{', '.join(sorted(tables)) or 'none'})")
            continue
        headers, rows = hit[1]
        if [_norm(h) for h in headers[:len(columns)]] != [_norm(c) for c in columns]:
            problems.append(f"set {set_name!r}: headers {headers!r} do not "
                            f"match the export block's {columns!r}")
        need_rows = require_rows and (require_rows_for is None
                                      or set_name in require_rows_for)
        if need_rows and rows < 1:
            problems.append(f"set {set_name!r}: no data rows")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("exported", help="the downloaded export file")
    ap.add_argument("--phyphox", required=True,
                    help="the experiment the export came from")
    ap.add_argument("--format", type=int, required=True, choices=range(6),
                    help="the format index it was requested with")
    ap.add_argument("--require-rows", action="store_true",
                    help="fail on a set without data rows")
    args = ap.parse_args()
    sets = export_sets(args.phyphox)
    if not sets:
        print("experiment has no export block - nothing to validate")
        return 0
    with open(args.exported, "rb") as f:
        data = f.read()
    problems = validate(data, sets, args.format, args.require_rows)
    for p in problems:
        print(f"  ! {p}")
    if not problems:
        print(f"export matches: {len(sets)} set(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
