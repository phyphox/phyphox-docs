# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Project overview

The technical documentation for phyphox — a science-education app that turns smartphone sensors
into physics measuring instruments. Built with MkDocs + Material into static HTML.

The repository has two jobs, and they pull in different directions:

1. **Documentation for users** — readable, well-organised prose about how the app works and how to
   build experiments for it.
2. **An exact definition of the shared contracts** — the phyphox XML experiment file format and the
   remote-interface REST API, precise enough that the independent implementations can be checked
   against it.

Job 2 is why this repo matters beyond presentation. See `../CLAUDE.md` for the ecosystem and the
contracts themselves.

## Scope — what belongs here and what does not

This site covers **the app itself**: the file format and the remote interface.

The **experiment editor is not documented here**, only linked to at
<https://phyphox.org/editor>. It is a tool for producing files in this format rather than part of
the format, it carries its own context help, and the page that came across from the wiki was three
paragraphs of link — so the landing page and the file-format index each carry a tip pointing at it
and nothing more. If the editor ever needs real documentation, note that phase 5 makes it consume
the format spec, so that documentation would belong with the spec rather than in a section of its
own.

It deliberately does **not** cover individual experiments, phone sensors, or specific Bluetooth
devices. That material stays on the MediaWiki at phyphox.org/wiki, which remains live for it. The
reasoning is that this content is contributed and corrected by teachers and users, and a wiki
suits that far better than a git-reviewed static site — it also swamped the technical documentation
when both lived together, which is why it was pulled back out after the initial migration.

So when adding a page, ask whether it documents the app or an application *of* the app. If a user
would sensibly want to edit it themselves, it belongs on the wiki, and this site should link to it
rather than copy it. `tools/migrate_wiki.py` encodes the split: `SECTIONS` lists the pages that
migrate, `COMMUNITY_PAGES` and the `Experiment: `/`Sensor: ` title prefixes mark what stays behind,
and links pointing at anything in the second group are rewritten to absolute wiki URLs.

Branch: `main`.

## Commands

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/mkdocs serve            # live preview on :8000
.venv/bin/mkdocs build --strict   # what CI runs — build this way before pushing
```

`--strict` turns broken internal links and unknown nav entries into failures. Plain `mkdocs build`
will happily ship a broken link, so always use `--strict`.

Dependencies are pinned in `requirements.txt` to the versions the site is known to build with.

## Layout and conventions

Navigation is handled by **mkdocs-awesome-nav**, not by a `nav:` block in `mkdocs.yml` — the plugin
replaces any nav given there, so do not add one. Order and section titles come from `.nav.yml`
files inside `docs/` and its subdirectories.

Pages are plain Markdown. Material extensions available include admonitions, `attr_list`, tables,
`pymdownx.details`, `superfences` and `highlight`; they are declared in `mkdocs.yml`.

`validation.links.anchors: warn` is set, so under `--strict` a link to a heading that does not
exist fails the build, not only a link to a file that does not exist. Note this covers Markdown
links only — a bare autolink (`<../page.md#anchor>`) is invisible to it, and two of those survived
the wiki import unnoticed for exactly that reason. Write links as `[text](target)`.

### file-format is a hub plus one page per block

`file-format/index.md` walks through the blocks of a `.phyphox` file in the order they appear.
Blocks small enough to document in place (`phyphox`, `translations`, `data-containers`, `export`,
`events`) are there in full. The large ones live on their own page and the index carries a stub:
a sentence, a list of the elements with deep links, and a link to the page.

    input.md   output.md   views.md   analysis/   network-connections.md

Keep that pattern when a block outgrows the index — a stub that only links, without listing what is
on the other side, makes the index useless as an overview. The analysis block additionally splits
per module category under `analysis/`, with `analysis/index.md` holding the block's own attributes
and the rules common to all modules.

This structure is deliberately the one phase 3's generator should emit, so that generated pages can
be diffed against the hand-written ones page by page.

## The inconsistency mechanism

phyphox is implemented independently several times over — Android, iOS, the Blockly editor, the
Arduino and MicroPython libraries — and reconciling them is expected to take many releases. The
documentation therefore has to be able to say "these disagree, here is which one is right, this is
a bug" rather than pretending a single behaviour exists.

`inconsistencies.yml` holds one entry per divergence. `tools/hooks.py` renders each entry in two
places from that single source:

- inline, wherever a page contains the marker `{{inconsistency:<id>}}`, as an admonition warning
  the reader; and
- as a section of `docs/reference/known-inconsistencies.md`, which doubles as the to-do list.

A marker naming an id that is not in the YAML **fails the build** — a renamed or deleted entry
cannot leave a dangling warning behind.

Entry `status` drives the wording:

- `open` — nobody has decided which behaviour is correct. The reader is told not to rely on either.
- `decided` — `canonical:` records the correct behaviour; the reader is told the others are bugs
  that will be fixed.
- `fixed` — keep the entry until the release carrying the fix has shipped everywhere, then delete.

When adding an entry, cite where each behaviour was observed (file and symbol), so the next person
can re-verify rather than trust the file. Deciding the canonical behaviour is **the maintainer's
call, not yours** — record the divergence with `status: open` and surface it; do not pick a winner.

## The REST API is specified, not described

`docs/remote-interface/openapi.yaml` is the source of truth for the remote-interface API. It was
written by reading `RemoteServer.java` and `ExperimentWebServer.swift`, not by transcribing the
prose page, and the header records the two revisions it was derived from. Three things consume it:

- `docs/remote-interface/api-reference.md` renders it with Swagger UI (`mkdocs-swagger-ui-tag`,
  which vendors its own copy — the built site loads nothing from a CDN);
- `tools/hooks.py` validates it on every build, so an invalid spec fails `--strict` rather than
  producing a broken reference page;
- `tools/contract_test.py` validates live responses against its schemas.

`docs/remote-interface/index.md` stays as the narrative introduction. When the two disagree the
spec wins, and the prose should be corrected — it already carried one factual error (`countDown`
documented in seconds when both apps have always sent milliseconds).

Operations where the implementations diverge carry `x-phyphox-inconsistency: [id, …]`. The build
fails if such an id is not in `inconsistencies.yml`, the same guarantee the `{{inconsistency:…}}`
markers get. Do not describe a divergence in the spec's prose instead of recording it — the entry
is what puts it on the to-do list.

### The contract test

`tools/contract_test.py` runs one set of requests against a running Android and a running iOS
instance and diffs the responses. Two design points are worth keeping:

- **It compares shape, not values.** Two phones cannot produce the same measurements, device names
  or timestamps. What must match is keys, types, enum choices, status codes and content types.
  Booleans *are* compared by value, because `{"result": true}` vs `false` is the entire answer of
  `/control` — collapsing it to a type once hid the `control-set-infinity` divergence during
  development. `VOLATILE` lists the paths exempted from this.
- **Recorded divergences pass; unrecorded ones fail.** A probe names the inconsistency ids it
  expects to trip. This is what makes the test usable against implementations known to disagree in
  a dozen places: it reports the backlog and fails only on something new.

`tools/fake_phyphox.py` serves both platforms' quirks locally so the script can be exercised
without hardware. It is a fixture for testing the test — not a third implementation of phyphox, not
authoritative, and always the thing that is wrong if it disagrees with an app.

## The wiki migration

`tools/migrate_wiki.py` imported the old MediaWiki (83 pages, 109 uploaded files). It is kept for
auditability, not because it should run again:

- `--fetch` populates `.wiki-cache/` from the MediaWiki API (gitignored, ~80 MB).
- `--convert` turns that cache into `docs/` via pandoc, and **refuses to run if `docs/` already has
  content** unless given `--force`. That guard exists because re-running silently discards every
  hand edit made since — it destroyed edits twice during the initial import.

Of the wiki's 83 pages, 9 migrated and 8 survive — the editor page was dropped afterwards, see
Scope. The rest are community content that stays on the wiki, apart from the archived pre-Blockly
editor page, which was never imported at all (`SKIP`). `SECTIONS` still lists the editor page,
because it records what the import did; do not prune it to match the current state.

The wiki kept every release on one 66 KB "Version history" page. `split_version_history()` breaks
it into `docs/reference/version-history/<version>.md`, leaving the intro and overview table on the
index and linking the table's version column onward. `fix_version_links()` retargets inbound
references, which the wiki wrote as anchors (`#1112` for release 1.1.12). Two things to remember if
you touch that code: headings inside a release move up a level when the release becomes its own
page, and relative links in the extracted body need an extra `../` because the page sits one
directory deeper.

`tools/optimize_images.py` keeps `docs/assets` from accumulating camera-resolution photographs;
run it after adding images. The directory is currently empty: every image on the wiki belonged to a
community page, and this site has had no reason to add one since.

`MIGRATION-REPORT.md` records per-page conversion notes and the wiki links that had no destination
in the new structure. It is a review aid for the import, not living documentation; delete it once
the review pass is done. It names pages by the path they had *at import time* — `file-format/
analysis-modules.md` has since been split apart — and is left that way on purpose, because
rewriting it would make it a worse record of what the import actually did.

Code blocks needed the most care. The wiki writes them two ways — a leading-space `<nowiki>` line,
and `<code>` abused as a block element — and pandoc renders both as a run of single-line inline code
spans with every space replaced by U+00A0, which is unreadable and cannot be copy-pasted. They are
therefore lifted out before conversion (`extract_code_blocks`) and put back as fenced blocks after
(`restore_code_blocks`), so the content survives byte-exact. The placeholder is matched unanchored
on the way back, because pandoc frequently joins it onto the end of the preceding paragraph; an
unrestored placeholder raises rather than shipping. Inline `<code>` on a single line is left to
pandoc. A few authors also wrote Markdown-style `` `backticks` `` in MediaWiki, where they are
ordinary characters — `fix_markdown_inline_code` turns those into real inline code.

Definition lists are the backbone of the file-format and analysis pages — one per attribute, ~540
in all. Plain `gfm` has no such construct, so pandoc flattens each into `term<br>text` and every
attribute name becomes indistinguishable from body prose. The writer is therefore
`gfm+definition_lists`, which emits exactly the syntax python-markdown's `def_list` extension
expects (enabled in `mkdocs.yml`). Nested definition lists (`:;term` / `::text`) survive this too.

The Colors page is a special case handled by `extract_color_table`: the wiki wrote each colour as a
preformatted line with an inline HTML swatch, a mixture that converts into inline code spans wrapped
around raw HTML. It is rebuilt as a table.

`SOURCE_FIXES` corrects four places where the wiki source has unbalanced `''`/`'''` markup, which
pandoc faithfully passes through as stray apostrophes. Each fix must apply exactly once or the
migration aborts. Note that a lone `''` is not always a defect — the file format documents an empty
string default as `default: ''`.

Conversion decisions worth knowing if you touch the script: MediaWiki capitalises the first letter
of page and file names (so `[[analysis modules]]` and `[[File:mb_mag.png]]` resolve to `Analysis
modules` and `Mb_mag.png`); it encodes anchors as dot-hex (`.28` for `(`); pandoc converts
`[[Page]]` to `[Page](Page "wikilink")` *before* the script sees it, and leaves sized images as raw
`<img>` HTML.

## Roadmap

This repo is phase 1 of a larger plan recorded in `../CLAUDE.md`. Later phases add an OpenAPI
description of the REST API, a machine-readable specification of the XML format that generates both
the reference pages and validators, and a conformance corpus run by all the implementations' test
suites. Prose written now should assume the reference sections will eventually be **generated** —
so avoid investing heavily in hand-written element/attribute tables that a generator will replace.
