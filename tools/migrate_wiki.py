#!/usr/bin/env python3
"""One-shot migration of the MediaWiki at phyphox.org/wiki into docs/.

This is kept in the repo for reproducibility and so the conversion decisions are
auditable, not because it is expected to run again. Once the wiki is retired this
script is history.

Usage:
    python3 tools/migrate_wiki.py --fetch      # pull wikitext + images into .wiki-cache/
    python3 tools/migrate_wiki.py --convert    # convert the cache into docs/
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import unicodedata

API = "https://phyphox.org/wiki/api.php"
WIKI_PAGE_URL = "https://phyphox.org/wiki/index.php/"
UA = "phyphox-docs-migration"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, ".wiki-cache")
DOCS = os.path.join(ROOT, "docs")

# Where each wiki page lands. Anything not listed falls through to the rules in
# categorise() below.
SECTIONS = {
    "Phyphox file format": ("file-format", "index.md"),
    "Analysis modules": ("file-format", "analysis-modules.md"),
    "Colors": ("file-format", "colors.md"),
    "Network Connections": ("file-format", "network-connections.md"),
    "Bluetooth Low Energy": ("file-format", "bluetooth-low-energy.md"),
    "Remote-interface communication": ("remote-interface", "index.md"),
    "Experiment editor": ("editor", "index.md"),
    "Transferring phyphox experiments": (".", "transferring-experiments.md"),
    "Version history": ("reference", "version-history/index.md"),
}

# Pages not carried over.
#
# This site documents the app itself: the file format, the remote interface and
# the editor. The wiki also carries a large body of community material - one page
# per built-in experiment, per phone sensor and per Bluetooth device, plus German
# teaching material. That content thrives on wiki editing by contributors and does
# not fit a git-reviewed static site, so it stays at phyphox.org/wiki and is linked
# to from here rather than duplicated.
#
# "Main Page" was wiki-specific navigation; docs/index.md is hand-written and
# absorbs the links that were worth keeping.
SKIP = {
    "W",
    "Main Page",
    # Documents the pre-Blockly editor, which no longer exists. Superseded
    # by editor/index.md; not worth linking to even on the wiki.
    "OLD Experiment editor (Archived)",
}


def is_community_page(title):
    """True for wiki pages that stay on the wiki rather than migrating here."""
    return (title.startswith("Experiment: ")
            or title.startswith("Sensor: ")
            or title in COMMUNITY_PAGES)


# Community pages that do not follow the "Experiment: "/"Sensor: " naming.
COMMUNITY_PAGES = {
    # German-language teaching material contributed by the community.
    "Amontons‘sches Gesetz",
    "Auf- und Endladung eines Kondensators",
    "Barometrische Höhenstufe",
    "Distanzsensor (Federpendel)",
    "Drehrate und Beschleunigung",
    "Druckmesungen",
    "Drucksensor",
    "Ein Thermometer für alle Fälle",
    "Entladung eines Kondensators",
    "Externer Magnetfeldsensor",
    "Luftfeuchtigkeit und Lufttemperatur",
    "Luftkissenbahn und Federpendel",
    "Magnetfeld und Beschleunigung",
    "Oxidation (Photosynthese)",
    # Bluetooth / external hardware pages.
    "Bluetooth device database",
    "Micro-controller based sensors",
    "Arduino library",
    "An external pressure sensor",
    "Attitude sensor",
    "BBC:Microbit / Calliope",
    "Card10",
    "MbientLab MetaWear (MetaMotionR)",
    "Owon B35T",
    "Owon Multimeter",
    "Polar H9 or H10 (Bluetooth Heart Rate Service)",
    "Puck.js",
    "Texas Instruments SensorTag",
    "Texas Instruments SensorTag CC2541",
    "Texas Instruments SensorTag CC2650/CC1350 STK",
    # Experiment pages not using the "Experiment: " prefix.
    "Integrated acceleration",
    "Tone ramp",
    "Sensor Statistics",
    "Envelope (oscillations)",
    "Bandpass Amplitude",
    "Hysteresis curve of an iron core",
    "LC circuit",
    "Smartphones as ammeters",
    "Using the magnetic sensor as ammeter",
    "TVOC",
    "W",
}


# Typos in the wiki source where italic/bold markup is unbalanced. pandoc passes
# the stray quotes through faithfully, so they show up as literal apostrophes in
# the rendered page. Corrected here rather than in docs/ so the divergence from
# the wiki stays visible and survives a re-run. Keyed by cache file name; each
# fix must apply exactly once or the migration stops.
Q = chr(39)
SOURCE_FIXES = [
    ("phyphox-file-format",
     Q * 2 + 'showControls="full_view_only"' + Q + ".",
     Q * 2 + 'showControls="full_view_only"' + Q * 2 + "."),
    ("analysis-modules",
     "only " + Q + "length" + Q * 2 + " values",
     "only " + Q * 2 + "length" + Q * 2 + " values"),
    ("network-connections",
     "replaced with keep in phyphox 1.1.13 (file format 1.17)" + Q * 3 + ")",
     "replaced with keep in phyphox 1.1.13 (file format 1.17))"),
    ("network-connections",
     "replaced with append in phyphox 1.1.13 (file format 1.17)" + Q * 3 + ")",
     "replaced with append in phyphox 1.1.13 (file format 1.17))"),
]


def apply_source_fixes(name, text):
    for page, before, after in SOURCE_FIXES:
        if page != name:
            continue
        if text.count(before) != 1:
            raise AssertionError(
                "%s: source fix no longer applies cleanly: %r" % (name, before))
        text = text.replace(before, after)
    return text


def api(params):
    params["format"] = "json"
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return json.load(urllib.request.urlopen(req, timeout=60))


def slug(title):
    s = title.lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def anchor_slug(text):
    # MediaWiki encodes punctuation in anchors as .HH (dot-hex), e.g.
    # "Phyphox_event_characteristic_.280004.29" for "... (0004)".
    #
    # Only decode when the result is ASCII punctuation, which is all MediaWiki
    # escapes this way. Without that guard a version anchor like "1.1.12" is
    # mangled: ".12" looks like dot-hex and decodes to a control character,
    # leaving "1.1" -> "11" instead of "1112".
    def _dothex(m):
        c = chr(int(m.group(1), 16))
        return c if not c.isalnum() and c.isprintable() else m.group(0)

    text = re.sub(r"\.([0-9A-F]{2})", _dothex, text)
    text = text.replace("_", " ")
    """Match python-markdown's slugify, which is what the toc extension uses.

    Note this differs from slug() above: it strips punctuation rather than turning
    it into separators, so a heading "1.2.1" becomes "121", not "1-2-1".
    """
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def categorise(title):
    """Return (section_dir, filename) for a wiki page title, or None to skip it."""
    if title in SECTIONS:
        return SECTIONS[title]
    # Everything not explicitly placed above is community content: experiment,
    # sensor and Bluetooth device pages. Those stay on the wiki.
    return None


# --------------------------------------------------------------------------
# Fetch
# --------------------------------------------------------------------------

def fetch():
    os.makedirs(os.path.join(CACHE, "pages"), exist_ok=True)
    os.makedirs(os.path.join(CACHE, "images"), exist_ok=True)

    d = api({"action": "query", "list": "allpages", "aplimit": "500"})
    titles = [p["title"] for p in d["query"]["allpages"]]
    print(f"{len(titles)} pages")

    index = {}
    for i in range(0, len(titles), 20):
        batch = titles[i:i + 20]
        d = api({"action": "query", "prop": "revisions", "rvprop": "content",
                 "rvslots": "main", "titles": "|".join(batch)})
        for page in d["query"]["pages"].values():
            title = page["title"]
            try:
                content = page["revisions"][0]["slots"]["main"]["*"]
            except (KeyError, IndexError):
                print(f"  !! no content: {title}")
                continue
            fn = slug(title) + ".wiki"
            with open(os.path.join(CACHE, "pages", fn), "w") as f:
                f.write(content)
            index[title] = fn
        time.sleep(0.3)

    with open(os.path.join(CACHE, "index.json"), "w") as f:
        json.dump(index, f, indent=1, ensure_ascii=False)
    print(f"cached {len(index)} pages")

    d = api({"action": "query", "list": "allimages", "ailimit": "500",
             "aiprop": "url|size"})
    images = d["query"]["allimages"]
    print(f"{len(images)} images, "
          f"{sum(i.get('size', 0) for i in images) / 1e6:.1f} MB")
    for img in images:
        dest = os.path.join(CACHE, "images", img["name"])
        if os.path.exists(dest):
            continue
        try:
            req = urllib.request.Request(img["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(dest, "wb") as f:
                shutil.copyfileobj(r, f)
        except Exception as e:  # noqa: BLE001 - best effort, report and move on
            print(f"  !! {img['name']}: {e}")
    print("images cached")


# --------------------------------------------------------------------------
# Convert
# --------------------------------------------------------------------------

# Multi-line code blocks in the wiki are written two ways, neither of which
# pandoc turns into a Markdown code block: a leading-space "<nowiki>" line
# (MediaWiki preformatting) and "<code>" abused as a block element. Left to
# pandoc, both come out as a run of single-line inline code spans with every
# space replaced by U+00A0 - unreadable, and the XML cannot be copy-pasted.
# So they are lifted out before conversion and put back as fenced blocks after.
CODE_BLOCK_RE = re.compile(
    r"^[ \t]*<(nowiki|code)>[ \t]*\n(.*?)\n[ \t]*</\1>[ \t]*$",
    re.S | re.M)
PLACEHOLDER = "PHYPHOXCODEBLOCKX%dX"
# Not anchored to a line: pandoc often joins the placeholder onto the end of
# the preceding paragraph, which an anchored pattern would silently miss.
PLACEHOLDER_RE = re.compile(r"[ \t]*PHYPHOXCODEBLOCKX(\d+)X[ \t]*")


def guess_language(code):
    head = code.lstrip()[:1]
    if head == "<":
        return "xml"
    if head in "{[":
        return "json"
    return ""


# Some wiki authors wrote Markdown-style inline code in MediaWiki, where a
# backtick is an ordinary character. pandoc faithfully escapes those into literal
# backticks, so "set `linearTime` to `true`" ends up displaying the backticks
# instead of marking up the identifiers. Restricted to identifier characters so a
# genuinely literal backtick in prose is left alone.
MARKDOWN_INLINE_CODE = re.compile(r"`([A-Za-z0-9_.:/-]{1,40})`")


def fix_markdown_inline_code(text):
    return MARKDOWN_INLINE_CODE.sub(r"<code>\1</code>", text)


def extract_code_blocks(text, blocks):
    def take(m):
        blocks.append(("code", m.group(2)))
        return PLACEHOLDER % (len(blocks) - 1)

    return CODE_BLOCK_RE.sub(take, text)


# The Colors page lists each named colour as a MediaWiki preformatted line with an
# HTML swatch: "    orange <span style="background:#ff7e22;...">ff7e22</span>".
# That mixture converts to a mess of inline code spans wrapped around raw HTML, so
# the whole run is recognised here and rebuilt as a table with a visible swatch.
COLOR_LINE = re.compile(
    r'^[ \t]+(\w+)[ \t]+<span style="background:#([0-9a-fA-F]{6})[^"]*">'
    r'[0-9a-fA-F]{6}</span>[ \t]*$', re.M)
SWATCH = ('<span style="display:inline-block;width:3em;height:1em;'
          'vertical-align:middle;background:#{hex};'
          'border:1px solid rgba(128,128,128,.4)"></span>')


def extract_color_table(text, blocks):
    colors = COLOR_LINE.findall(text)
    if not colors:
        return text

    rows = "\n".join(f"| `{name}` | `{h.lower()}` | " + SWATCH.format(hex=h.lower())
                      + " |" for name, h in colors)
    table = "| Name | Hex | |\n|---|---|---|\n" + rows
    blocks.append(("raw", table))
    placeholder = PLACEHOLDER % (len(blocks) - 1)

    # Replace the first colour line with the table and drop the rest.
    first = COLOR_LINE.search(text)
    text = text[:first.start()] + placeholder + text[first.end():]
    return COLOR_LINE.sub("", text)


def restore_code_blocks(md, blocks):
    def put(m):
        kind, content = blocks[int(m.group(1))]
        if kind == "raw":
            return f"\n\n{content}\n\n"
        code = content.rstrip()
        # A fence must be longer than any backtick run inside the code.
        longest = max((len(r) for r in re.findall(r"`+", code)), default=0)
        fence = "`" * max(3, longest + 1)
        # Blank lines around the fence: pandoc drops the placeholder straight
        # against the neighbouring paragraph, and not every Markdown parser
        # opens a fence that is not preceded by one.
        return f"\n\n{fence}{guess_language(code)}\n{code}\n{fence}\n\n"

    return PLACEHOLDER_RE.sub(put, md)


INFOBOX_RE = re.compile(r"\{\{Infobox Experiment(.*?)\}\}", re.S)
TECHNICAL_RE = re.compile(r"\{\{Technical\|(.*?)\}\}", re.S)


def strip_templates(text, notes):
    """Pull the two templates the wiki uses out into something pandoc can handle."""
    m = INFOBOX_RE.search(text)
    infobox = {}
    if m:
        for line in m.group(1).split("\n"):
            line = line.strip()
            if line.startswith("|") and "=" in line:
                k, _, v = line[1:].partition("=")
                infobox[k.strip()] = v.strip()
        text = INFOBOX_RE.sub("", text)
        notes.append("infobox")

    def technical(m):
        notes.append("technical-banner")
        return ("''This page is highly technical. Most users will want "
                f"{m.group(1)} instead.''\n")

    text = TECHNICAL_RE.sub(technical, text)
    return text, infobox


def fix_links(md, title_to_path, current_section, dangling, attachments):
    """Rewrite internal wiki links to relative paths in the new tree.

    pandoc converts [[Some Page]] into [Some Page](Some_Page "wikilink") before we
    get to see it, so that -- not the original [[...]] -- is what we rewrite. Links
    to pages that did not survive the migration (category listings, redlinks) are
    downgraded to plain text rather than left pointing at nothing.
    """
    def repl(m):
        label, target = m.group(1), m.group(2)
        # Some wikilinks give a full wiki URL as their target rather than a page
        # title. Reduce those to the title so they resolve like any other.
        target = re.sub(r"^https?://phyphox\.org/wiki/index\.php/", "", target)
        target = urllib.parse.unquote(target).replace("_", " ").strip()
        page, _, frag = target.partition("#")
        page = page.strip()
        anchor = "#" + anchor_slug(frag) if frag else ""

        # MediaWiki treats the first letter of a title as case-insensitive, so
        # [[analysis modules]] and [[Analysis modules]] are the same page.
        if page not in title_to_path:
            cap = page[:1].upper() + page[1:]
            if cap in title_to_path:
                page = cap

        # [[Media:x]] and [[File:x]] link to an uploaded file rather than a page.
        m_file = re.match(r"(?:Media|File|Datei|Bild):(.+)", page, re.I)
        if m_file:
            name = m_file.group(1).strip().replace(" ", "_")
            name = name[:1].upper() + name[1:]
            attachments.add(name)
            prefix = "" if current_section == "." else "../"
            return f"[{label}]({prefix}assets/{name})"

        if page in title_to_path:
            section, fn = title_to_path[page]
            if section == current_section:
                dest = fn
            elif current_section == ".":
                dest = f"{section}/{fn}"
            elif section == ".":
                dest = "../index.md"
            else:
                dest = f"../{section}/{fn}"
            return f"[{label}]({dest}{anchor})"

        # Community pages still live on the wiki, so link out rather than drop
        # the reference.
        if is_community_page(page):
            url = WIKI_PAGE_URL + urllib.parse.quote(page.replace(" ", "_"))
            return f"[{label}]({url})"

        dangling.add(page)
        return label

    return re.sub(r'\[([^\]]*)\]\((.+?)\s+"wikilink"\)', repl, md)


ABSOLUTE_WIKI_URL = re.compile(
    r"https?://phyphox\.org/wiki/index\.php/([^\s<>\])]+)")


def fix_absolute_wiki_urls(md, title_to_path, current_section):
    """Point absolute wiki URLs at the migrated page when there is one.

    Some pages link to the wiki by full URL rather than [[wikilink]], so
    fix_links never sees them. Left alone, a migrated page would send readers
    back to the stale wiki copy of a page that now lives here. URLs naming a page
    that stayed on the wiki are untouched.
    """
    def repl(m):
        raw = m.group(1)
        page, _, frag = urllib.parse.unquote(raw).replace("_", " ").partition("#")
        page = page.strip()
        page = page[:1].upper() + page[1:]
        if page not in title_to_path:
            return m.group(0)
        section, fn = title_to_path[page]
        if section == current_section:
            dest = fn
        elif current_section == ".":
            dest = f"{section}/{fn}"
        elif section == ".":
            dest = "../index.md"
        else:
            dest = f"../{section}/{fn}"
        return dest + ("#" + anchor_slug(frag) if frag else "")

    return ABSOLUTE_WIKI_URL.sub(repl, md)


VERSION_LINK = re.compile(
    r"\((\.\./)?reference/version-history/index\.md#(\d+)\)")


def fix_version_links(md):
    """Retarget links into the old single-page version history.

    "#1112" was the anchor of the "1.1.12" heading; that release now has its own
    page. The anchor carries no separators, so the digits are split back apart
    using the fact that phyphox releases are all x.y.z with a single-digit x.
    """
    def repl(m):
        prefix, digits = m.group(1) or "", m.group(2)
        if len(digits) < 3:
            return m.group(0)
        version = f"{digits[0]}.{digits[1]}.{digits[2:]}"
        return f"({prefix}reference/version-history/{version}.md)"

    return VERSION_LINK.sub(repl, md)


def pandoc(wikitext):
    p = subprocess.run(
        # +definition_lists: the file format and analysis pages are built almost
        # entirely from MediaWiki definition lists (one per attribute). Plain gfm
        # has no such construct, so pandoc flattens each into "term<br>text",
        # leaving 500 attribute names indistinguishable from body prose.
        ["pandoc", "-f", "mediawiki", "-t", "gfm+definition_lists", "--wrap=none"],
        input=wikitext, capture_output=True, text=True, check=True)
    return p.stdout


VERSION_HEADING = re.compile(r"^## (\d+\.\d+\.\d+)\s*$", re.M)


def split_version_history(path):
    """Break the version history into one page per release.

    The wiki keeps every release on a single 66 KB page: an intro, an overview
    table, then one "## x.y.z" section per version. That is unpleasant to read and
    unpleasant to link into, so each version becomes its own page and the original
    page keeps the intro and the table, with the version column linking onwards.

    Returns the version strings, newest first, for the nav file.
    """
    text = open(path).read()
    matches = list(VERSION_HEADING.finditer(text))
    if not matches:
        return []

    outdir = os.path.dirname(path)
    head = text[:matches[0].start()].rstrip() + "\n"

    versions = []
    for i, m in enumerate(matches):
        version = m.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end].strip()
        # Section headings inside a release were level 3 under the release
        # heading; as their own page they move up a level.
        body = re.sub(r"^### ", "## ", body, flags=re.M)
        # The page sits one directory deeper than the page it came from, so
        # relative links out of it need another level.
        body = body.replace("](../", "](../../")
        with open(os.path.join(outdir, f"{version}.md"), "w") as f:
            f.write(f"# phyphox {version}\n\n{body}\n")
        versions.append(version)

    # Link the overview table's version column at the new pages.
    known = set(versions)

    def link_row(m):
        return f"| [{m.group(1)}]({m.group(1)}.md)" if m.group(1) in known else m.group(0)

    head = re.sub(r"^\| (\d+\.\d+\.\d+)", link_row, head, flags=re.M)

    with open(path, "w") as f:
        f.write(head)

    with open(os.path.join(outdir, ".nav.yml"), "w") as f:
        f.write("title: Version history\n"
                "# Newest first. Generated by tools/migrate_wiki.py; alphabetical\n"
                "# order would put 1.1.10 before 1.1.9.\n"
                "nav:\n  - index.md\n")
        for v in versions:
            f.write(f"  - {v}.md\n")

    return versions


def convert(force=False):
    # The migration is one-shot. Re-running it silently discards every hand edit
    # made to a migrated page since, which is how the marker on the /control
    # section got lost twice during the initial import.
    existing = [f for f in os.listdir(DOCS)
                if os.path.isdir(os.path.join(DOCS, f)) and f != "assets"] \
        if os.path.isdir(DOCS) else []
    if existing and not force:
        sys.exit("docs/ already contains migrated content. Re-running would discard\n"
                 "any hand edits made since. Pass --force if that is what you want.")

    index = json.load(open(os.path.join(CACHE, "index.json")))
    title_to_path = {}
    for t in index:
        if t in SKIP:
            continue
        dest = categorise(t)
        if dest is not None:
            title_to_path[t] = dest

    report = []
    used_images = set()
    dangling = set()

    for title, wikifile in sorted(index.items()):
        if title not in title_to_path:
            continue
        section, fn = title_to_path[title]
        outdir = os.path.join(DOCS, section) if section != "." else DOCS
        # fn may itself contain a directory (e.g. "version-history/index.md").
        os.makedirs(os.path.join(outdir, os.path.dirname(fn)), exist_ok=True)

        raw = open(os.path.join(CACHE, "pages", wikifile)).read()
        raw = apply_source_fixes(os.path.splitext(wikifile)[0], raw)
        notes = []
        raw, infobox = strip_templates(raw, notes)
        code_blocks = []
        raw = extract_code_blocks(raw, code_blocks)
        raw = extract_color_table(raw, code_blocks)
        raw = fix_markdown_inline_code(raw)

        try:
            md = pandoc(raw)
        except subprocess.CalledProcessError as e:
            print(f"  !! pandoc failed on {title}: {e.stderr[:200]}")
            report.append((title, section + "/" + fn, ["PANDOC FAILED"], 0))
            continue

        md = restore_code_blocks(md, code_blocks)
        if "PHYPHOXCODEBLOCK" in md:
            raise AssertionError(f"{title}: unrestored code block placeholder")
        if code_blocks:
            notes.append(f"{len(code_blocks)} code blocks")
        md = fix_links(md, title_to_path, section, dangling, used_images)
        md = fix_absolute_wiki_urls(md, title_to_path, section)
        md = fix_version_links(md)

        # Images. pandoc emits three shapes depending on the wiki markup:
        #   ![alt](Name.png)              plain [[File:...]]
        #   ![alt](Name.png "title")      with a caption
        #   <img src="Name.png" ... />    when the wiki specified a size/thumb
        # MediaWiki also uses [[File:...]] for PDFs and videos, which pandoc turns
        # into images too -- those become plain links instead.
        depth = "" if section == "." else "../"
        IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp")

        def asset(raw_name):
            name = urllib.parse.unquote(raw_name).strip().replace(" ", "_")
            name = re.sub(r"^(File|Image|Datei|Bild):", "", name, flags=re.I)
            # MediaWiki capitalises the first letter of a file name, so a page
            # referencing [[File:mb_mag.png]] is served as Mb_mag.png.
            name = name[:1].upper() + name[1:]
            used_images.add(name)
            return name

        def md_image(m):
            alt, target, title = m.group(1), m.group(2), m.group(3) or ""
            name = asset(target)
            title = f' "{title}"' if title else ""
            if not name.lower().endswith(IMAGE_EXT):
                label = alt or title.strip(' "') or name
                return f"[{label}]({depth}assets/{name})"
            return f"![{alt}]({depth}assets/{name}{title})"

        md = re.sub(r'!\[([^\]]*)\]\(([^\s)"]+)(?:\s+"([^"]*)")?\)', md_image, md)

        def html_image(m):
            name = asset(m.group(1))
            rest = m.group(2)
            title = re.search(r'title="([^"]*)"', rest)
            alt = title.group(1) if title else ""
            width = re.search(r'width="(\d+)"', rest)
            if not name.lower().endswith(IMAGE_EXT):
                return f"[{alt or name}]({depth}assets/{name})"
            suffix = "{ width=" + width.group(1) + " }" if width else ""
            return f"![{alt}]({depth}assets/{name}){suffix}"

        md = re.sub(r'<img\s+src="([^"]+)"([^>]*)/?>', html_image, md)

        front = [f"# {title}\n"] if not md.lstrip().startswith("#") else []
        if infobox:
            rows = "\n".join(f"| {k} | {v} |" for k, v in infobox.items())
            front.append("| | |\n|---|---|\n" + rows + "\n")
            notes.append("infobox->table")

        body = "\n".join(front) + "\n" + re.sub(r"\n{3,}", "\n\n", md)
        with open(os.path.join(outdir, fn), "w") as f:
            f.write(body)

        # crude quality signals for the review pass
        leftovers = len(re.findall(r"\{\{|\[\[|</?nowiki>|__[A-Z]+__", body))
        report.append((title, f"{section}/{fn}", notes, leftovers))

    vh = os.path.join(DOCS, "reference", "version-history", "index.md")
    if os.path.exists(vh):
        print(f"version history split into {len(split_version_history(vh))} pages")

    # copy images that are actually referenced
    assets = os.path.join(DOCS, "assets")
    os.makedirs(assets, exist_ok=True)
    copied = missing = 0
    for name in sorted(used_images):
        src = os.path.join(CACHE, "images", name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(assets, name))
            copied += 1
        else:
            missing += 1
    print(f"images: {copied} copied, {missing} referenced but not in cache")

    report.sort(key=lambda r: -r[3])
    with open(os.path.join(ROOT, "MIGRATION-REPORT.md"), "w") as f:
        f.write("# Wiki migration report\n\n")
        f.write("Generated by `tools/migrate_wiki.py`. `leftovers` counts unconverted\n")
        f.write("wiki markup (`{{`, `[[`, `<nowiki>`, `__TOC__`) still in the output -\n")
        f.write("a rough signal for which pages need a human pass. Sorted worst first.\n\n")
        f.write("| leftovers | page | source title | notes |\n")
        f.write("|---:|---|---|---|\n")
        for title, path, notes, n in report:
            f.write(f"| {n} | `{path}` | {title} | {', '.join(notes)} |\n")
        f.write("\n## Links that went nowhere\n\n")
        f.write("Wiki links whose target did not survive the migration (category\n")
        f.write("listings, redlinks, deleted pages). These were replaced with plain\n")
        f.write("text - check whether any deserve a real destination.\n\n")
        for t in sorted(dangling):
            f.write(f"- {t}\n")
    print(f"wrote MIGRATION-REPORT.md ({len(report)} pages, "
          f"{len(dangling)} dangling links)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true")
    ap.add_argument("--convert", action="store_true")
    ap.add_argument("--force", action="store_true",
                    help="allow --convert to overwrite existing docs/")
    args = ap.parse_args()
    if not (args.fetch or args.convert):
        ap.error("pass --fetch and/or --convert")
    if args.fetch:
        fetch()
    if args.convert:
        convert(force=args.force)
