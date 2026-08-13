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

## Commits

Unlike the other phyphox repositories, where nothing is committed unless the maintainer asks,
finished work in this repository is **committed automatically**: end a task by committing it on
`main` with a descriptive message. Never push — publishing remains the maintainer's call, here as
everywhere.

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

## Colours come from the app, not from Material

`docs/assets/stylesheets/phyphox.css` restates the theme's palette in the app's own colours, taken
from `phyphox-android/app/src/main/res/values/colors.xml` — `#ff7e22` for the brand orange, white
on top of it, and the desaturated grey ladder (`#101010`, `#202020`, `#303030`, …). Do not invent
shades; if you need a new one, take it from that file.

Three things to know before touching it:

- **There are two schemes**, light and dark, selected by `prefers-color-scheme` and switchable from
  the header. Check both after any change — the toggle is easy to forget, and the dark scheme is
  the one most contributors will see.
- **Material has no `custom` palette entry in this version.** `mkdocs.yml` still names
  `deep orange`, and the stylesheet overrides everything it sets; renaming it changes nothing.
- **Some theme variables are scoped with two attributes**
  (`[data-md-color-scheme=slate][data-md-color-primary=deep-orange]` sets `--md-typeset-a-color`).
  A single attribute selector loses to those no matter how late it loads, which is why the scheme
  blocks here are written with two.

Link colour differs between the schemes on purpose. The brand orange on white is only 2.5:1, which
fails WCAG AA for body text, so the light scheme uses a darkened `#b85c00` (4.6:1) for links while
the dark scheme uses `#ff7e22` directly (6.4:1). Large areas such as the header bar keep the brand
colour in both.

If you verify colours in a browser, note that `navigation.instant` swaps the document without
re-running the cascade the way you would expect: measuring computed styles after toggling the
scheme by script gives stale answers. Navigate to a fresh URL instead.

## The site makes no third-party requests

Reading this site must not make a visitor's browser contact anyone but the host serving it. phyphox
is used in classrooms, largely in Europe, by a publicly funded project — a documentation page is
not a reason to hand anyone's IP address to a third party.

Three defaults had to be turned off, and each would come back on its own:

- **Google Fonts.** Material requests Roboto from `fonts.googleapis.com` on every page unless
  `theme.font` is `false`. Any font *name* there reintroduces the request; the site uses the system
  stack instead.
- **GitHub stars.** With `repo_url` set, Material mounts a component on
  `data-md-component="source"` that calls `api.github.com` per page view.
  `overrides/partials/source.html` is a copy of the theme's partial with that attribute removed —
  the link and icon stay, only the counts go. **It is a copy, so re-check it against the theme when
  bumping mkdocs-material.**
- **The Swagger validator badge.** Swagger UI posts the spec URL to `validator.swagger.io` by
  default. `mkdocs-swagger-ui-tag` already defaults `validatorUrl` to `none`; do not set it to
  anything else.

`tools/hooks.py` enforces this in `on_post_build`: it walks the generated site and fails the build
if any `<link>`, `<script>`, `<img>`, `<iframe>` or CSS `url()`/`@import` points at an absolute URL.
Ordinary hyperlinks are fine — a visitor choosing to follow one is not the site phoning home — so
`rel` values that describe a relationship without fetching (`canonical` and friends) are exempt.

If a future feature genuinely needs an external asset, vendor it into `docs/assets` rather than
relaxing the check.

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

There is deliberately no `fixed` status, and the build rejects one. Once every implementation
agrees, **delete the entry** — together with its `{{inconsistency:…}}` markers,
`x-phyphox-inconsistency` references and `inconsistency:` fields in `spec/`, in the same change as
the fix. Readers learn about corrected behaviour from the release changelog; a lingering "recently
corrected" note only clutters the documentation.

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

## The file-format reference is generated

`spec/*.yml` is the machine-readable model of the phyphox XML format — every element, attribute,
type, allowed value, default and `since` version, with an `agreement:` field recording what the two
parsers were found to do. `spec/README.md` describes its shape and the traps met while writing it.

The reference sections of the file-format pages are **generated from it at build time**. A page
carries a marker where its reference belongs:

    {{spec:BLOCK/PARENT/NAME}}

`tools/spec_reference.py` renders it and `tools/hooks.py` expands it during the build. Nothing is
generated into the repository — the Markdown keeps the marker — so there is no second copy to keep
in step and no generated file to edit by mistake. `|xml`, `|attributes` and `|slots` restrict the
output to one part; a root element with no parent is named `{{spec:BLOCK/NAME}}`.

**So an element's facts are edited in `spec/`, not on the page.** What stays hand-written is
everything the spec does not know: how the two depth APIs differ, why "acceleration with g" is
called that, the worked examples in the data-picker section. If you find yourself writing a
default, a type or a version note into a page, it belongs in the spec instead.

Three fields exist for the split between what the spec records and what a reader sees:

- `summary:` — the one-liner the spec was written with. Kept short; used where a whole block has to
  fit on one screen.
- `description:` — the full documentation text, moved across from the pages during the conversion.
  Rendered in preference to `summary:` where both exist.
- `note:` — what was found while reading the parsers: source citations, why a divergence is not
  one, what to search for next time. **Never rendered.** Reader-facing detail that belongs beside an
  attribute goes in `remark:`, so the distinction has to be made deliberately.

### Code blocks come in two kinds

A **skeleton** is generated and shows the surface — every attribute that may appear. Its
placeholders are uppercase and name the kind of value that goes in the blank: `STRING`, `INTEGER`,
`FLOAT`, `BOOLEAN`, `COLOR`, and `BUFFER`/`TEXT` for element content. Uppercase means "replace
this". Anything lowercase inside a skeleton is a literal to type verbatim — the slot and component
names, `component="hue"`, `as="threshold"` — so the case tells the reader which is which.

An **example** is hand-written and shows a real, valid configuration that can be pasted into an
experiment. It never contains an uppercase placeholder.

Enumerated attributes get a type like everything else, not their list of choices: spelling them out
reads well for `type="buffer/value"` and runs to 128 characters for `sensor`'s `type`, and
collapsing past a length threshold put `scaleMinX="auto/extend/fixed"` next to
`rateStrategy="STRING"` for no visible reason. The values belong in the attribute list under the
skeleton, where there is room to explain them.

`value_notes:` describes the values of an enumerated attribute and renders as a nested definition
list — the shape the hand-written pages used for `aeStrategy` and the audio parameters.
`undocumented: intentionally` keeps an attribute out of the output while the spec still models it;
`appleBan` is the case it exists for.

Divergences place themselves: an attribute whose `agreement:` is `divergent` carries a pointer to
its entry, and the first element on a page to reach a given entry emits the full admonition. Before
this, fourteen file-format entries were recorded in `inconsistencies.yml` and not one appeared on a
file-format page — the mechanism was there, the markers were never placed by hand.

### What checks it

- `tools/spec_vs_docs.py` diffs the spec against the pages and fails the build on anything the docs
  describe that the spec does not model. It expands the markers first, so it still checks the
  hand-written parts of a half-converted page. It can no longer be an independent opinion about the
  parts that are generated — those agree with the spec by construction.
- `tools/spec_vs_ios.py` walks the iOS handler tree from `<phyphox>` and reports any attribute iOS
  declares that the spec does not model.
- `tools/validate_experiments.py` validates real `.phyphox` files against the spec. Run it over
  `phyphox-experiments` after changing the spec; a finding is as likely to be a spec error as a
  file error.
- `tools/hooks.py` checks the spec against `inconsistencies.yml`, that declared children are
  modelled, that an attribute does not predate its element, and that slot names survived YAML.

## Roadmap

This repo was phase 1 of a larger plan recorded in `../CLAUDE.md`. Phase 2 (the OpenAPI description
of the REST API) and phase 3 (the format spec, and the reference pages generated from it) are done.
What is left is phase 4 — generated validators, RELAX NG and Schematron, plus a conformance corpus
run by the implementations' test suites — and phase 5, making the Blockly editor consume the spec
instead of encoding the format a fifth time.
