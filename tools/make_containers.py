#!/usr/bin/env python3
"""Build the container fixtures (fixtures/containers/) from their src/.

The apps accept more than bare XML - the container forms are contract
(see ../CLAUDE.md, "Containers"): a zip of several experiments, a zip
bundling res/ images that saving must extract into the per-experiment
CRC32 folder, and the headerless partial zip that QR codes and BLE
transfers carry. This script builds each form deterministically:

    two-experiments.zip   container-a + container-b
    with-resource.zip     with-resource.phyphox + res/pic.png
    traversal.zip         a normal entry plus ../evil.phyphox - the
                          handlers must REJECT the traversal entry (a
                          security pin; Android's ZipIntentHandler guard)
    partial.bin           container-a as a single STORED entry with
                          a trailing data descriptor (PK\\x07\\x08 + crc +
                          sizes), no local file header, no central
                          directory - the QR/BLE form both apps rebuild a
                          zip around. STORED, not deflated: both apps
                          synthesize a local header with compression
                          method 0 and the editor's offlineQrCode.ts
                          writes STORE, so a deflated payload loads
                          nowhere (this fixture had it wrong until
                          2026-08-26)

tools/hooks.py verifies the built artifacts against src/ content-wise on
every docs build (byte-exact zip reproducibility across zlib builds is
not guaranteed, content equality is what matters).
"""

import os
import struct
import sys
import zipfile
import zlib

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CDIR = os.path.join(ROOT, "fixtures", "containers")
SRC = os.path.join(CDIR, "src")

FIXED_DATE = (1980, 1, 1, 0, 0, 0)


def make_png():
    """2x2 opaque RGB PNG (red, green / blue, white) - same pixels as the
    imagedecode golden vector."""
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0)
    raw = (b"\x00" + bytes([255, 0, 0, 0, 255, 0])
           + b"\x00" + bytes([0, 0, 255, 255, 255, 255]))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def zwrite(zf, arcname, data):
    info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    zf.writestr(info, data)


def read_src(name):
    with open(os.path.join(SRC, name), "rb") as f:
        return f.read()


def build(out_dir=CDIR):
    a = read_src("container-a.phyphox")
    b = read_src("container-b.phyphox")
    res = read_src("with-resource.phyphox")
    png = make_png()

    with zipfile.ZipFile(os.path.join(out_dir, "two-experiments.zip"), "w") as z:
        zwrite(z, "container-a.phyphox", a)
        zwrite(z, "container-b.phyphox", b)

    with zipfile.ZipFile(os.path.join(out_dir, "with-resource.zip"), "w") as z:
        zwrite(z, "with-resource.phyphox", res)
        zwrite(z, "res/pic.png", png)

    with zipfile.ZipFile(os.path.join(out_dir, "traversal.zip"), "w") as z:
        zwrite(z, "container-a.phyphox", a)
        zwrite(z, "../evil.phyphox", b)

    # the partial zip: a STORED payload plus the data descriptor, matching
    # what the apps rebuild (method 0) and what the editor emits
    stream = a
    descriptor = (b"PK\x07\x08"
                  + struct.pack("<III", zlib.crc32(a) & 0xffffffff,
                                len(stream), len(a)))
    with open(os.path.join(out_dir, "partial.bin"), "wb") as f:
        f.write(stream + descriptor)


def check():
    """Content-level verification for the docs build."""
    problems = []
    try:
        with zipfile.ZipFile(os.path.join(CDIR, "two-experiments.zip")) as z:
            if sorted(z.namelist()) != ["container-a.phyphox",
                                        "container-b.phyphox"]:
                problems.append("two-experiments.zip: wrong entry set")
            elif (z.read("container-a.phyphox") != read_src("container-a.phyphox")
                  or z.read("container-b.phyphox") != read_src("container-b.phyphox")):
                problems.append("two-experiments.zip: stale content - run "
                                "tools/make_containers.py")
        with zipfile.ZipFile(os.path.join(CDIR, "with-resource.zip")) as z:
            if sorted(z.namelist()) != ["res/pic.png", "with-resource.phyphox"]:
                problems.append("with-resource.zip: wrong entry set")
            elif (z.read("with-resource.phyphox") != read_src("with-resource.phyphox")
                  or z.read("res/pic.png") != make_png()):
                problems.append("with-resource.zip: stale content")
        with zipfile.ZipFile(os.path.join(CDIR, "traversal.zip")) as z:
            if "../evil.phyphox" not in z.namelist():
                problems.append("traversal.zip lost its traversal entry")
        with open(os.path.join(CDIR, "partial.bin"), "rb") as f:
            blob = f.read()
        if blob[-16:-12] != b"PK\x07\x08":
            problems.append("partial.bin: no trailing data descriptor")
        else:
            crc, csize, usize = struct.unpack("<III", blob[-12:])
            data = blob[:-16]          # stored: the payload IS the file
            if (len(blob) - 16 != csize or len(data) != usize
                    or zlib.crc32(data) & 0xffffffff != crc
                    or data != read_src("container-a.phyphox")):
                problems.append("partial.bin: stale or inconsistent - run "
                                "tools/make_containers.py")
    except FileNotFoundError as e:
        problems.append(f"missing container artifact: {e.filename} - run "
                        f"tools/make_containers.py")
    return problems


if __name__ == "__main__":
    build()
    bad = check()
    for p in bad:
        print(f"  ! {p}")
    print("containers built" if not bad else "BUILD INCONSISTENT")
    sys.exit(1 if bad else 0)
