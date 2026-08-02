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

## Suggested sequence, if this goes ahead

1. ~~Decide the four questions above.~~ Done for three; `input-one-sided-attributes` is
   case by case and does not block modelling, since each attribute can carry `undecided`
   until its turn comes.
2. Model `output` (3 attributes) and `views` (100) next — `views` is the largest block and
   the least like `input`, so it will either confirm the estimate or break it early.
3. Only then write the generator. Generating reference pages from a spec that is still
   changing shape wastes the generator twice.
