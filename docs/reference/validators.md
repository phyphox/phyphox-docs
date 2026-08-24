# Format validators

Machine checks for `.phyphox` files, generated from the same
[format specification](../file-format/index.md) that produces the reference
pages — so they cannot drift from the documentation.

- **[phyphox.rng](../assets/validators/phyphox.rng)** — a
  [RELAX NG](https://relaxng.org/) grammar (XML syntax). Checks structure:
  which elements and attributes may appear where, required attributes and
  children, and attribute values — enumerations and colors exactly as the
  format defines them, numbers and booleans by syntax.
- **[phyphox.rnc](../assets/validators/phyphox.rnc)** — the same grammar in
  RELAX NG compact syntax, for reading rather than for tools.
- **[phyphox.sch](../assets/validators/phyphox.sch)** — a
  [Schematron](https://schematron.com/) ruleset for what a grammar cannot
  express: buffer references must name a declared container, container names
  must be unique, the [graph dataset pairing rules](../file-format/views/graph.md#multiple-graphs),
  the numbered `mapColor[N]` attribute shape, and — as *warnings*, not
  errors — the version gates: an element or attribute used by a file that
  declares an older format version than the feature requires.

## Running them

With [lxml](https://lxml.de/) (what this site's own build uses):

```python
from lxml import etree
from lxml.isoschematron import Schematron

tree = etree.parse("experiment.phyphox")

rng = etree.RelaxNG(etree.parse("phyphox.rng"))
print(rng.validate(tree), rng.error_log)

sch = Schematron(etree.parse("phyphox.sch"), store_report=True)
sch.validate(tree)
for fail in sch.validation_report.iter("{http://purl.oclc.org/dsdl/svrl}failed-assert"):
    level = "warning" if fail.get("role") == "warning" else "error"
    print(level, fail.findtext("{http://purl.oclc.org/dsdl/svrl}text").strip())
```

`xmllint --relaxng phyphox.rng experiment.phyphox` works too, as does any
other RELAX NG validator. The grammar accepts a file with no namespace or
with the phyphox namespace in either URI spelling (`http://phyphox.org/xml`
or `https://phyphox.org/xml`). The apps themselves go further — they ignore
the namespace entirely and treat whatever the root element declares as the
file's own — but that rule is beyond what a fixed grammar can express, and
no other namespace is in circulation.

## What a pass means — and what it does not

The grammar is deliberately no stricter than the apps' parsers. Files that
load today must validate, so it allows what they allow:

- **stray text** between elements (the parsers skip text nodes they do not
  expect, and real files use that for inline notes);
- **attributes from foreign namespaces** anywhere (the parsers read
  attributes by their plain name and ignore the rest — this is how
  editor-generated files carry their `editor:*` bookkeeping);
- **unknown elements in foreign namespaces** likewise.

An *unknown element or attribute in the phyphox namespace or in no
namespace* is an error, matching the strictness the format rules require of
the parsers themselves.

A pass is therefore necessary, not sufficient: whether an experiment makes
sense — buffers wired to the right modules, sensible rates, units that mean
something — is beyond any schema. The build of this site additionally runs
every corpus and shipped experiment file through both validators plus the
spec-driven checker in `tools/validate_experiments.py`, which knows a few
things the published artifacts cannot see.

The version gates are warnings because the apps only compare a file's
declared `version` against the newest version they support — a file that
understates its version still loads on a current app, but older app versions
will mishandle it, so an author should raise the declaration instead of
relying on that.
