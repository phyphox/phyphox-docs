# phyphox-docs

The technical documentation for [phyphox](https://phyphox.org): the experiment
file format, the remote-interface API and the experiment editor.

Built with [MkDocs](https://www.mkdocs.org/) and
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/), deployed as
static HTML.

It replaces the technical parts of the MediaWiki at phyphox.org/wiki. The wiki
remains in use for community content — see [Scope](#scope).

## Building locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/mkdocs serve     # live preview on http://127.0.0.1:8000/
.venv/bin/mkdocs build     # static HTML into site/
```

CI builds with `--strict`, which turns broken internal links and unknown
navigation entries into errors, so build that way before pushing:

```bash
.venv/bin/mkdocs build --strict
```

## Layout

```
docs/                   the pages themselves
  .nav.yml              navigation order (mkdocs-awesome-nav)
  file-format/          the experiment XML format
    index.md            the blocks of a .phyphox file; links onward to the
                        blocks that have their own page
    input.md            \
    output.md            | one page per block
    views.md            /
    analysis/           the analysis block, one page per module category
  remote-interface/     the REST API
  editor/               the Blockly editor
  reference/            version history (one page per release),
                        known inconsistencies
inconsistencies.yml     known divergences between the implementations
tools/hooks.py          MkDocs hooks (renders inconsistencies.yml)
tools/migrate_wiki.py   one-shot import from the old MediaWiki
tools/optimize_images.py  keeps images in docs/assets from being committed
                          at camera resolution
```

## Scope

This site documents **the app itself**: the experiment file format, the remote
interface, and the editor.

It deliberately does not cover individual experiments, phone sensors or specific
Bluetooth devices. That material stays on the [phyphox wiki](https://phyphox.org/wiki),
where contributors can edit it directly — it benefits from community contribution
in a way that a git-reviewed static site works against. Pages here link out to the
wiki for it.

## Recording an inconsistency

phyphox is implemented independently several times over — two apps, the Blockly
editor, two microcontroller libraries — and they do not always agree. Where they
diverge, that is a bug, and readers should be told rather than left to discover it.

Add an entry to [`inconsistencies.yml`](inconsistencies.yml), then put the marker

```markdown
{{inconsistency:your-id}}
```

on each page where a reader would be misled without it. The entry renders as a
warning at that spot *and* as a row on the
[Known inconsistencies](docs/reference/known-inconsistencies.md) page, so the
to-do list cannot drift from the warnings. A marker naming an id that is not in
the YAML fails the build.

See the comments at the top of `inconsistencies.yml` for the fields.

## Contributing

Pages are plain Markdown; edit them directly. The wiki import is finished, so
`tools/migrate_wiki.py` should not need to run again — it refuses to overwrite
`docs/` without `--force` precisely because doing so would discard hand edits.

`MIGRATION-REPORT.md` records how each page came across and which wiki links had
no destination in the new structure. It is a review aid for the import, not
living documentation.
