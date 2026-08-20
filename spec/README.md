# Machine-readable specification of the phyphox file format

**This directory is a probe, not a commitment.** It contains one block of the format —
`input` — modeled completely, to find out what phase 3 actually costs before ~540
attributes are written in the same shape. `FINDINGS.md` has the result.

Nothing consumes these files yet. They are not wired into the docs build.

## Why a schema rather than RELAX NG

A grammar can say that `rate` is a float. It cannot say that `rateStrategy` defaults to
`auto` from file format 1.14 and to `limit` below it, which is real behavior in both
parsers (`InputElementHandler.swift`, `SensorInputDescriptor.defaults(forVersion:)`;
`PhyphoxFile.java`, `inputBlockParser`). Version-dependent *defaults* are the reason this
is structured YAML that generates a validator, rather than a validator written by hand.

## Shape

One file per block. Each element:

```yaml
elements:
  - name: sensor
    since: "1.0"
    parent: input
    summary: One-line description.
    attributes:
      - name: stride
        type: integer
        default: 1
        summary: ...
        agreement: agreed          # see below
    children: [output]
    outputs:                       # components a sensor may map to a buffer
      - {name: x, summary: ...}
```

An attribute whose *name* is numbered without bound - the map graph's
mapColor1, mapColor2, ... - is modelled once, with `name_pattern:` holding a
regular expression; the validators accept every attribute matching it and the
`name:` (e.g. `mapColorN`) is only what the rendered documentation displays.

Defaults that depend on the format version are a list, most recent first; the first entry
whose `since` the document satisfies wins:

```yaml
    default:
      - since: "1.14"
        value: auto
      - value: limit
```

### `agreement` is mandatory on every attribute

This is the field that keeps the spec honest. It records what was found when the two
parsers were compared, and it is what makes the spec reviewable rather than merely
plausible:

| value | meaning |
|---|---|
| `agreed` | Android and iOS behave the same; the spec states that behavior. |
| `divergent` | They differ. Requires `inconsistency:` naming an entry in `../inconsistencies.yml`. The spec states the behavior only if that entry has been decided. |
| `undecided` | They differ and nobody has chosen. Also requires `inconsistency:`. |
| `platform` | Deliberately one-sided, because the feature only exists on one platform. Requires `platforms:`. |

Where the entry has been **decided**, the attribute also carries `rules:` naming the
rule in `rules.yml` that settles it. `rules.yml` holds the questions that turned out not to
belong to any one block — how to treat an invalid enumerated value, whether enum matching
folds case, whether output components are validated. Answering those once is what keeps the
decision count from growing with the attribute count.

### The documentation is a third opinion, and it is checked

`tools/spec_vs_docs.py` diffs the spec against the documentation pages and runs as part of
`mkdocs build --strict`. Anything the docs describe that the spec does not model fails the
build. The other direction is reported but tolerated — the docs are often behind, and being
behind is not a modeling error.

The prose is not a source: it has been caught three times naming an attribute no
implementation accepts (`autoExposure`, `showControls`, `logy`). Its value is as an
independent list of what exists.

### Child elements are checked, not trusted

`tools/hooks.py` fails the build if an element declares a child in `children:` that is not
modeled, or models an element whose parent does not list it. Both directions matter: the
graph data picker and the button's `trigger` tag were both lost by writing a name into
`children:` and stopping there.

That check cannot tell you a child exists in the first place — only the parsers can. See
below.

### Enumerate child elements from both parsers, not one

The first pass at `views.yml` gave `graph` the single child `input`, missing `output`
entirely — and with it the whole data-picker feature. iOS registers both
(`childHandlers = ["input": ..., "output": ...]`) and Android parses both; the omission was
simply not looking. Children deserve the same treatment as attributes: list them from each
parser and compare, rather than assuming the obvious ones are all there are.

The same pass filed `calibrationParameter` under `input` when it belongs to `output`. When a
handler declares several private `Attribute` enums, check which one each belongs to.

A reliable way to enumerate them on iOS is the `childHandlers` dictionary each handler
builds; on Android it is the `AdditionalTag` names each view element accepts from
`ioBlockParser`, which are checked with an explicit `at.name.equals(...)` chain ending in
"Unknown tag". Reading those two lists side by side gives the child set directly.

### Extracting a list of cases from a parser

Two independent traps, both hit while probing the analysis modules:

* **Bound the class by brace depth, not by a byte window.** `analysisBlockParser` ends at line
  3472; a fixed-size window ran past it and picked up `audio`, `bluetooth`, `data`,
  `flashlight` and `set` from the parsers that follow.
* **A `case "..."` is not necessarily an element or module name.** Inside the same class,
  nested switches match *attribute values*: `sum` is a value of the `map` module's `zMode`,
  and `linear`, `nearest`, `next`, `previous` are values of `interpolate`'s `method`.
  Indentation separates the two levels reliably here; context (`= new`, `Mode.`) confirms it.

Of twelve names that first looked like Android-only analysis modules, exactly two were —
`butterworth` and `imagedecode`, both file format 1.20.

### Text content is part of the format

Many child elements carry their meaning in their text rather than in an attribute: an
`<output>` names a buffer, a `<trigger>` names an id, a `<map>` carries the label to display.
Record that with `text:`. A model that only lists attributes silently loses it — the
dropdown's option labels were briefly modeled as a `replacement` attribute, which iOS
declares but never reads and which appears nowhere in the documentation.

### Read the prose under a definition-list term, not just the term

Twice a platform limitation was already documented and still recorded as an unexplained
divergence, because the note lives in the paragraph *below* the term rather than in the
`:` lines beside it — `depth/smooth` ("Only applies to LiDAR on iOS devices") and
`info/wifiSignalStrength` ("Only available on Android."). `tools/spec_vs_docs.py` compares
names only and cannot catch this; the description has to be read.

### Android has two parsers; iOS has one

`PhyphoxFile.java` is Android's full parser, used when an experiment is opened. A separate,
minimal parser under `ExperimentList/datasource/` builds the collection list. iOS uses one
parser for both. So an attribute that only matters before an experiment is opened may be
absent from `PhyphoxFile.java` by design — `isLink`, which marks a collection entry that
redirects to a web page rather than running, is implemented only in the list parser, because
the full parser never sees such a file.

That is a third reason an attribute can be missing from the parser you are reading, after
dynamic names and attributes read by the class that consumes them.

### Verifying a one-sided attribute

Before recording an attribute as read by only one app, check *how* the other parser names
attributes. Android builds the map-graph color stops as `"mapColor" + index` in a loop, so
`mapColor1` appears nowhere in its source and a grep for it wrongly suggested the attribute
was iOS-only. That is currently the only dynamically constructed attribute name in either
codebase, but the failure is silent, so a negative grep is not on its own evidence of a
divergence.

`platform` must not become a dumping ground for divergences nobody wants to think about.
An attribute one parser silently ignores is `divergent`, not `platform`, unless there is a
reason it *cannot* exist on the other side.
