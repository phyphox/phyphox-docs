# Phase 3 estimate

The `input` block of the file format was modelled completely in `input.yml`, by comparing
`PhyphoxFile.java`'s `inputBlockParser` against `InputElementHandler.swift` attribute by
attribute, with `docs/file-format/input.md` and the Blockly editor as third and fourth
opinions where they had something to say. This is what that cost, and what it implies for
the rest.

## The count

47 attributes across 9 elements, plus 5 output-component sets covering 32 component names.

| | attributes | share |
|---|---|---|
| Both parsers agree — spec states it and moves on | 35 | 74% |
| They differ — needs a decision | 10 | 21% |
| Genuinely platform-specific | 2 | 4% |

Plus all 5 output-component sets, which diverge for the same single reason.

**15 facts needed a decision — but they collapse into 4 distinct questions.**

| question | facts it settles |
|---|---|
| `input-one-sided-attributes` — six attributes one app honours and the other ignores | 6 |
| `input-output-component-validation` — Android validates component names and counts, iOS does not | 5 |
| `input-invalid-enum-handling` — invalid enum value: refuse the file, or silently use the default? | 2 |
| `input-enum-case-sensitivity` — is `mode="Closest"` the same as `mode="closest"`? | 2 |

**Three of the four have since been decided** (2026-08-02), and are written up as
format-wide rules in `rules.yml`:

| question | decision |
|---|---|
| invalid enumerated value | Reject the file. Silent substitution is not permitted. |
| enum case sensitivity | Match case-insensitively, so long as no allowed set collides once folded — none does. Keeps files that already work on Android working. |
| output component validation | Validate names and counts, reject on mismatch. |

The fourth, `input-one-sided-attributes`, is case by case: each of the six attributes needs
its own answer about whether the feature should exist on both platforms.

That the three decidable questions all turned out to be *format-wide* — and were answered in
one exchange — is the strongest evidence for the estimate below.

That ratio is the finding. Roughly one attribute in five raises a question, but **the
questions repeat**. Three of the four are policy questions about the format as a whole, not
about the `input` block, and answering them once resolves the same issue everywhere it
appears. Only `input-one-sided-attributes` is a genuine list of individual cases.

## What this means for the remaining ~215 attributes

The file-format pages carry 262 documented attributes, of which 37 are in `input`. So the
block modelled here is about 14% of the format — a fair sample in size, though not in
character: `input` has more platform-specific hardware in it than `analysis`, and fewer
elements than `views`.

Extrapolating the *mechanical* work is safe: it was steady, roughly a minute of comparison
per attribute, and it scales linearly. Extrapolating the decisions is not, and the direction
of the error is favourable:

- The four questions here are already **format-wide**. Enum handling, case sensitivity and
  component validation apply to `output`, `views` and `analysis` too — so the same four
  answers cover much of what the remaining blocks would otherwise raise, and the decision
  count should grow far more slowly than the attribute count.
- Against that, `views` (100 attributes) and `bluetooth-low-energy` (74) are both larger
  than `input` and neither has been sampled. `views` in particular has per-element quirks
  that may not reduce to shared policy.

A defensible estimate: **on the order of 10–20 distinct decisions for the whole format**,
not one per attribute and not four. The bulk of phase 3 is mechanical comparison, and the
maintainer's involvement is a handful of policy calls made once, plus a review pass.

## Three things the probe changed about the plan

**1. The spec must record agreement, not just behaviour.** Every attribute in `input.yml`
carries an `agreement:` field saying whether the two parsers were found to agree. Without
it a reader cannot tell a fact that was verified from one that was assumed, and neither can
the next person to touch the file. This is the same lesson the phase 2 hardware run taught:
reading code reliably gives the happy path and unreliably gives the edges.

**2. Defaults are the easy part; error behaviour is the hard part.** The version-dependent
default that motivated the structured-YAML approach (`rateStrategy`: `auto` from 1.14,
`limit` below) turned out to be the *simplest* kind of entry — both parsers implement it
identically and it is trivially expressible. Every genuine difficulty was about what happens
when a value is wrong: refuse, ignore, or silently substitute. A schema that models only
valid documents would have found none of them.

**3. The documentation cannot be a source.** `docs/file-format/input.md` documented the
camera attribute as `autoExposure`. No implementation accepts that — Android, iOS *and* the
editor all read `auto_exposure`, so the documented spelling has never worked. Corrected on
the page, and a reminder that phase 3 must derive from the parsers and treat the prose as a
fourth opinion, not as input.

## The `views` block confirms the estimate

`views.yml` models the second block: 27 elements, 135 attributes — two and a half times the
size of `input`, and the block least like it.

| | `input` | `views` | both |
|---|---|---|---|
| attributes | 52 | 135 | 187 |
| agree — state it and move on | 67% | **84%** | 79% |
| need a decision | 29% | 16% | 20% |

**It raised no new questions of the decidable kind.** All 13 of its enum-related divergences
fall under `enum-invalid-value` and `enum-case-insensitive`, decided already — `align`,
`style`, `scaleMin*`/`scaleMax*`, `axis`, slider `type`, `darkFilter`, `lightFilter`,
`show_controls`. That is the prediction from the `input` probe holding: the format-wide
rules do the work, and modelling a new block mostly consumes them rather than adding to
them.

The new entries are `views-one-sided-attributes` (five attributes) and
`views-map-color-limit` (one). Both are the same *kind* of question as
`input-one-sided-attributes` — the category already agreed to be case by case — and they
scale with attributes rather than being answered once. So the shape of the estimate is:
**a small fixed set of policy rules, plus a short parity list per block.**

The substantive one is the guided calibration workflow — `calibrationMode` on the graph with
`calibrationParameter` on its datasets — which exists only on iOS. Android loads such a
graph without complaint and silently does not offer the workflow, so an author testing on
iOS cannot discover that half their audience gets a different experiment.

### A correction, and the method lesson behind it

The first version of this section claimed the two apps colour map graphs *incompatibly* —
that `mapColor1`…`mapColor9` were iOS-only and Android offered `interpolateMapColors` over a
built-in scale instead. That was wrong, and the maintainer caught it.

Android reads the same explicit stops, in a `while` loop that builds the attribute name as
`"mapColor" + index`. The literal string `mapColor1` therefore never appears in the Android
source, and a grep for it returned nothing. Both apps in fact read stops numbered from 1 and
end the scale at the first gap, so scales of up to nine stops behave identically;
`interpolateMapColors` is simply a newer feature not yet ported.

**Grepping for literal attribute names does not find dynamically constructed ones.** A
search of both codebases turned up exactly one such case — this one — so nothing else in the
182 attributes modelled so far is affected. But the failure mode is silent and it produced a
confident, wrong, and quite dramatic claim, which is worth remembering when the remaining
blocks are modelled: an attribute that appears one-sided deserves a second look at *how* the
other parser reads attributes before it is written down as a divergence.

### A second correction: a whole feature was missed

`graph` was modelled with one child element, `input`. It has two. The `output` tag configures
the **data picker** — the graph's outputs name data containers that receive the coordinates of
a point the user picks, with `axis` values `x`, `xcal`, `y`, `ycal`, `z`, `zcal` and a `label`
per button — and it was omitted completely, along with the finding that goes with it.

That finding is the sharpest in the block. Both apps accept `<output>` inside a graph and
**neither can read the other's**: Android reads `axis`, iOS reads `calibrationParameter` and
reads it as *required*, so a data-picker graph does not merely lose the feature on iOS, it
stops the file parsing. The version gate hides this today — the picker is file format 1.20
and iOS supports 1.19 — but a file declaring an older version and using the construct fails
with a confusing parse error rather than the clean "update the app" message.

The calibration attributes turn out to be a superseded draft of the spectroscopy feature
rather than a live iOS-only capability, so `views-one-sided-attributes` shrinks again, to
`interpolateMapColors` and `editable`.

Two lessons, both now in `README.md`: **enumerate child elements from both parsers** rather
than assuming, and **check which of a handler's several `Attribute` enums an attribute
belongs to** — `calibrationParameter` was filed under `input` when it is an `output`
attribute. Neither error would have been caught by any check in the repo; both were caught by
the maintainer knowing the feature existed.

### A third correction: child elements were declared but not modelled

`children:` lists were written on every view element, but only three child elements were
actually modelled. Nine were missing, including the button's `trigger` tag — the mechanism
that fires a network connection, in the format since 1.8 — and every plain `<output>` and
`<input>` that names a buffer.

Two related errors came out of the same pass. The dropdown's entries are `<map>`, not
`<mapping>` as modelled; and their text was recorded as a `replacement` attribute, which iOS
declares but never reads and which is in neither Android nor the documentation. The option
label is the element's text.

That last one exposed a gap in the schema itself: it had no way to say that an element's
**text** carries meaning, which is true of `output`, `input`, `trigger` and `map` alike.
There is now a `text:` key.

`views.yml` grew from 18 elements to 27 and from 132 attributes to 135 — the attribute count
barely moved, which is the point: the missing surface was structural, not attributive, and
counting attributes would never have revealed it.

**The build now checks this.** An element declaring a child that is not modelled, or a
modelled element its parent does not list, fails the build. Verified against the exact
omission: deleting the `trigger` element while leaving it in `children:` is now an error.
That check would have caught two of the three corrections in this section.

### Revised projection

262 documented attributes; 187 now modelled — **71% of the format**, leaving roughly 80,
spread across `analysis`, `bluetooth-low-energy`, `network-connections`, `output` and the
root block.

With two blocks done and only one new *category* of question between them, the earlier
"10–20 distinct decisions" looks high for policy rules and about right overall. A better
split: **4–6 format-wide rules** (three already decided) plus **one parity list per block**.
The mechanical share did not just hold on the larger block, it improved — 85% against 67% —
which is the opposite of what a pessimistic estimate would predict.

## Suggested sequence, if this goes ahead

1. ~~Decide the four questions above.~~ Done for three; `input-one-sided-attributes` is
   case by case and does not block modelling, since each attribute can carry `undecided`
   until its turn comes.
2. ~~Model `views` next.~~ Done, and it confirmed the estimate rather than breaking it.
   `bluetooth-low-energy` (74 attributes) is the largest untouched block and the next
   worthwhile test, since its conversion machinery is unlike anything modelled so far.
3. Only then write the generator. Generating reference pages from a spec that is still
   changing shape wastes the generator twice.
