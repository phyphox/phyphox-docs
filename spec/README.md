# Machine-readable specification of the phyphox file format

**This directory is a probe, not a commitment.** It contains one block of the format —
`input` — modelled completely, to find out what phase 3 actually costs before ~540
attributes are written in the same shape. `FINDINGS.md` has the result.

Nothing consumes these files yet. They are not wired into the docs build.

## Why a schema rather than RELAX NG

A grammar can say that `rate` is a float. It cannot say that `rateStrategy` defaults to
`auto` from file format 1.14 and to `limit` below it, which is real behaviour in both
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
| `agreed` | Android and iOS behave the same; the spec states that behaviour. |
| `divergent` | They differ. Requires `inconsistency:` naming an entry in `../inconsistencies.yml`. The spec states the behaviour only if that entry has been decided. |
| `undecided` | They differ and nobody has chosen. Also requires `inconsistency:`. |
| `platform` | Deliberately one-sided, because the feature only exists on one platform. Requires `platforms:`. |

`platform` must not become a dumping ground for divergences nobody wants to think about.
An attribute one parser silently ignores is `divergent`, not `platform`, unless there is a
reason it *cannot* exist on the other side.
