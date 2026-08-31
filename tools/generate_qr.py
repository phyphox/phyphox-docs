#!/usr/bin/env python3
"""Build the QR codes shown on docs/transferring-experiments.md.

The transfer page describes three routes into the app - a link, a link
under the phyphox:// scheme, and the experiment itself encoded as one or
more offline codes - and until now described them without showing one.
The codes generated here are both the page's examples and the codes the
release checklist's scan test is run against (test-matrix.yml,
`qr-scan-printed`): print the page or put it on a second screen and every
route has something to scan.

Two example experiments in docs/assets/examples/ are the payloads:

    qr-offline-example.phyphox   small on purpose - one offline code
    qr-online-example.phyphox    the one the links point at, and the
                                 payload of the two-code set

Their titles say which route delivered them, so a scan that opens the
wrong experiment is visible immediately.

The offline encoding is the one documented on that page and implemented
by the editor's offlineQrCode.ts: a 13-byte header ("phyphox", the CRC32
of the whole payload big-endian, this code's index and the number of
codes) followed by a slice of the partial zip - the experiment file
STORED, with a trailing data descriptor and neither local file header nor
central directory. STORED rather than deflated because the header both
apps synthesize around it declares compression method 0
(Helper.inflatePartialZip, ExperimentLauncher's partial-zip path).

Byte mode matters and is not an implementation detail: iOS reads the QR
bitstream itself and refuses anything whose first four bits are not 0100
(ScannerViewController.metadataOutput), so every offline code has to be a
single byte-mode segment. verify() asserts that rather than trusting it.

Output goes to docs/assets/qr/ (gitignored - generated on every build,
write-if-changed so `mkdocs serve` does not loop), the same arrangement
as the generated validators.
"""

import io
import os
import struct
import sys
import zipfile
import zlib

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
EXAMPLES = os.path.join(ROOT, "docs", "assets", "examples")
OUT = os.path.join(ROOT, "docs", "assets", "qr")

# Where the docs are published. The links are burned into printed codes, so
# this is not a detail that may drift with the site's layout: moving
# docs/assets/examples/ invalidates every code already on paper.
BASE = "https://phyphox.org/docs/assets/examples/"
ONLINE = "qr-online-example.phyphox"
OFFLINE = "qr-offline-example.phyphox"

# The split point of a multi-code set is the producer's choice - the header
# carries index and count and nothing fixes the chunk size. EDITOR_CHUNK is
# what the Blockly editor uses (offlineQrCode.ts), which is what a reader
# will get if they let the editor make the codes; the small example fits in
# one code at that size. SPLIT_CHUNK exists only to make the two-code
# example actually take two codes, and is kept small so each of them stays
# comfortable to scan off a printed page.
EDITOR_CHUNK = 1500
SPLIT_CHUNK = 700

MAGIC = b"phyphox"


def partial_zip(data):
    """The headerless single-entry zip the QR and BLE routes carry."""
    return data + b"PK\x07\x08" + struct.pack(
        "<III", zlib.crc32(data) & 0xffffffff, len(data), len(data))


def offline_payloads(xml, chunk=EDITOR_CHUNK):
    """The byte string of each QR code carrying `xml` as an experiment."""
    payload = partial_zip(xml)
    crc = zlib.crc32(payload) & 0xffffffff
    chunks = [payload[i:i + chunk] for i in range(0, len(payload), chunk)] or [b""]
    return [MAGIC + struct.pack(">I", crc) + bytes([i, len(chunks)]) + c
            for i, c in enumerate(chunks)]


def _read(name):
    with open(os.path.join(EXAMPLES, name), "rb") as f:
        return f.read()


def codes():
    """Every code the page shows, as (filename, payload, error level).

    The payload is `str` for a link (encoded as text) and `bytes` for an
    experiment (encoded as a single byte-mode segment).
    """
    out = [
        ("link-https.svg", BASE + ONLINE, "m"),
        ("link-phyphox.svg", "phyphox://" + BASE.split("//", 1)[1] + ONLINE, "m"),
    ]
    # level L for the offline codes, as the editor uses: the payload is what
    # sets the version, and a denser code with less redundancy is still
    # easier to scan than a larger one with more.
    single = offline_payloads(_read(OFFLINE))
    if len(single) != 1:
        raise ValueError(
            f"{OFFLINE} has grown past one QR code ({len(single)} at "
            f"EDITOR_CHUNK={EDITOR_CHUNK}) - the page shows it as the "
            f"single-code example")
    out.append(("offline.svg", single[0], "l"))
    split = offline_payloads(_read(ONLINE), SPLIT_CHUNK)
    if len(split) != 2:
        raise ValueError(
            f"{ONLINE} now needs {len(split)} codes at "
            f"SPLIT_CHUNK={SPLIT_CHUNK}, not 2 - the page describes it as a "
            f"two-code set")
    for i, payload in enumerate(split):
        out.append((f"offline-split-{i + 1}.svg", payload, "l"))
    return out


def _svg(payload, error):
    try:
        import segno
    except ImportError:
        raise ValueError(
            "segno is not installed, so the QR codes on the transfer page "
            "cannot be generated. Install requirements.txt.")
    # mode="byte" for the binary payloads: iOS rejects anything else, and
    # letting segno pick would give a link the alphanumeric mode it cannot
    # use for a lowercase URL anyway.
    qr = segno.make(payload, error=error,
                    mode="byte" if isinstance(payload, bytes) else None)
    buf = io.BytesIO()
    # Black on white, spelled out rather than left transparent: the page has
    # a dark scheme and a code without its own light background is
    # unscannable there. These are not theme colours - they are the code.
    qr.save(buf, kind="svg", scale=4, border=4,
            dark="#000000", light="#ffffff", xmldecl=False, svgversion=1.1)
    return buf.getvalue(), qr


def generate(out_dir=OUT):
    """Write the codes, returning (out_dir, [(name, version, error)])."""
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name, payload, error in codes():
        svg, qr = _svg(payload, error)
        path = os.path.join(out_dir, name)
        old = None
        if os.path.exists(path):
            with open(path, "rb") as f:
                old = f.read()
        if old != svg:
            with open(path, "wb") as f:
                f.write(svg)
        written.append((name, qr.version, qr.error))
    return out_dir, written


def rebuild_zip(payload):
    """Rebuild the full zip around a partial one, as the apps do.

    A deliberate re-implementation of Helper.inflatePartialZip (Android) and
    the acceptPartialZip path (iOS): a local file header and a central
    directory for one STORED entry called a.phyphox, wrapped around the
    payload with the CRC32 and the sizes lifted out of its data descriptor.
    Reading the result back with zipfile is what makes verify() an
    independent opinion rather than a restatement of the generator - zipfile
    checks the CRC and the sizes on the way out.
    """
    body, descriptor = payload[:-16], payload[-16:]
    if descriptor[:4] != b"PK\x07\x08":
        raise ValueError("no trailing data descriptor")
    sizes = descriptor[4:]                       # crc32, compressed, uncompressed
    name = b"a.phyphox"
    lfh = (b"PK\x03\x04" + struct.pack("<HHHHH", 10, 0, 0, 0, 0) + sizes
           + struct.pack("<HH", len(name), 0) + name)
    cd = (b"PK\x01\x02" + struct.pack("<HHHHHH", 10, 10, 0, 0, 0, 0) + sizes
          + struct.pack("<HHHHHII", len(name), 0, 0, 0, 0, 0, 0) + name)
    eocd = (b"PK\x05\x06" + struct.pack("<HHHHIIH", 0, 0, 1, 1, len(cd),
                                         len(lfh) + len(body), 0))
    return lfh + body + cd + eocd


def verify():
    """Prove the codes carry what the page says they carry.

    Deliberately not a restatement of the generator: the payloads come from
    codes(), i.e. from what is actually encoded, and they are then taken
    apart the way the apps take them apart - header off, chunks joined,
    CRC32 checked, a zip rebuilt around the remainder and read back with
    zipfile, whose own CRC check is the part the generator cannot fake. What
    comes out has to be the example file byte for byte.

    Also checked: that every offline code came out as a single byte-mode
    segment, which is iOS's hard requirement.
    """
    problems = []
    try:
        encoded = codes()
    except ValueError as e:
        return [str(e)]
    sources = {"offline": OFFLINE, "offline-split": ONLINE}
    grouped = {"offline": [], "offline-split": []}
    for name, payload, _error in encoded:
        if not isinstance(payload, bytes):
            continue
        grouped["offline-split" if name.startswith("offline-split")
                else "offline"].append(payload)

    for group, payloads in grouped.items():
        joined = b""
        for i, p in enumerate(payloads):
            if p[:7] != MAGIC:
                problems.append(f"{group}: code {i} does not start with 'phyphox'")
            if p[11] != i or p[12] != len(payloads):
                problems.append(f"{group}: code {i} says {p[11]} of {p[12]}, "
                                f"not {i} of {len(payloads)}")
            if p[7:11] != payloads[0][7:11]:
                problems.append(f"{group}: code {i} carries a different CRC32")
            joined += p[13:]
        if struct.unpack(">I", payloads[0][7:11])[0] != zlib.crc32(joined) & 0xffffffff:
            problems.append(f"{group}: the header CRC32 is not the one of the "
                            f"reassembled payload")
            continue
        # zipfile is content-blind about the uncompressed size of a STORED
        # entry, so the descriptor is read here as well: the apps hand these
        # three numbers straight to their own zip readers.
        if joined[-16:-12] != b"PK\x07\x08":
            problems.append(f"{group}: no trailing data descriptor")
            continue
        crc, csize, usize = struct.unpack("<III", joined[-12:])
        body = joined[:-16]
        if (csize != len(body) or usize != len(body)
                or crc != zlib.crc32(body) & 0xffffffff):
            problems.append(f"{group}: the data descriptor does not describe "
                            f"its own STORED payload")
            continue
        try:
            with zipfile.ZipFile(io.BytesIO(rebuild_zip(joined))) as z:
                got = z.read("a.phyphox")
        except (ValueError, zipfile.BadZipFile, KeyError) as e:
            problems.append(f"{group}: the rebuilt zip does not open ({e})")
            continue
        if got != _read(sources[group]):
            problems.append(f"{group}: the codes do not carry "
                            f"{sources[group]}")

    for name, payload, error in encoded:
        if not isinstance(payload, bytes):
            continue
        _, qr = _svg(payload, error)
        if qr.mode != "byte":
            problems.append(f"{name}: encoded as {qr.mode}, not byte - iOS "
                            f"refuses any other mode for an offline code")
    return problems


if __name__ == "__main__":
    bad = verify()
    if bad:
        for p in bad:
            print(f"  {p}", file=sys.stderr)
        sys.exit(1)
    out_dir, written = generate()
    for name, version, error in written:
        print(f"{os.path.relpath(os.path.join(out_dir, name), ROOT)}: "
              f"version {version}, error correction {error}")
