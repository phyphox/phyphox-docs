# phyphox-docs

The technical documentation for [phyphox](https://phyphox.org): the experiment
file format and the remote-interface API.

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

The built site is fully self-contained: reading it makes a visitor's browser
contact nothing but the host serving it. No web fonts, no analytics, no
star-count lookups, no CDN. The build fails if that stops being true, so if you
add something that pulls in an external asset, vendor the asset instead.

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
    index.md            introduction
    openapi.yaml        OpenAPI 3.1 description - the source of truth
    api-reference.md    renders openapi.yaml with Swagger UI
  reference/            version history (one page per release),
                        known inconsistencies
inconsistencies.yml     known divergences between the implementations
tools/hooks.py          MkDocs hooks (renders inconsistencies.yml, validates
                        openapi.yaml)
tools/contract_test.py  runs the same requests against a running Android and
                        iOS phone and diffs the responses
tools/fake_phyphox.py   local stand-ins for both apps, so the contract test can
                        be exercised without hardware
tools/migrate_wiki.py   one-shot import from the old MediaWiki
tools/optimize_images.py  keeps images in docs/assets from being committed
                          at camera resolution
```

## Checking the two apps against the spec

`docs/remote-interface/openapi.yaml` describes the remote-interface API. To check that a real
Android and a real iOS phone still agree with it and with each other, put both on the network,
enable remote access, load **the same experiment** on both, and run:

```bash
.venv/bin/python tools/contract_test.py \
    --android http://192.168.0.10:8080 \
    --ios     http://192.168.0.11
```

It validates every response against the spec and diffs the two phones by shape — keys, types,
status codes — not by values, which cannot match. Divergences already listed in
`inconsistencies.yml` are reported and tolerated; anything else fails the run.

Add `--allow-control` to include commands that change the experiment state, and `--allow-clear` to
include clearing, which destroys measured data.

Without phones, `python tools/fake_phyphox.py` serves stand-ins on ports 8111 and 8112 that
reproduce both platforms' known behaviour, which is enough to exercise the script itself.

## Scope

This site documents **the app itself**: the experiment file format and the
remote interface.

The [experiment editor](https://phyphox.org/editor) is only linked to, not
documented here — it is a tool for producing files in this format, and its own
help is reachable from inside it.

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
