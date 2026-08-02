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
| attributes | 52 | 134 | 185 |
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

### Cross-checking against the documentation

The maintainer's suggestion, and it earned its place immediately.
`tools/spec_vs_docs.py` mines the documentation pages for XML skeletons and definition-list
terms and diffs them against the spec. The prose is not authoritative — it has now been
caught three times naming an attribute no implementation accepts — but a **mismatch is a
prompt to look again**, and it is the only check that can catch a construct that exists, is
documented, and was simply not noticed while reading the source.

It found two more documentation bugs of the `autoExposure` kind: `camera-gui` was documented
as taking `showControls` (four places) where every implementation reads `show_controls`, and
the graph skeleton had `logy` for `logY`. Both fixed. It also found that the spec described
the component of an input output as a property rather than naming the `component` attribute
it actually is.

The reverse direction — in the spec, documented nowhere — turned up four attributes:

| attribute | why it is missing |
|---|---|
| `bluetooth/address` | Android-only, already recorded as a divergence |
| `camera/threshold` | Android-only, already recorded |
| `edit/editable` | Android-only, already recorded |
| `bluetooth/output/decimalPoint` | implemented on **both**, documented nowhere |

Three of the four are Android-only attributes, which is a pattern worth noticing: **the
attribute only one app implements tends to be the attribute nobody documented.** The fourth
is a plain documentation gap.

Finding `decimalPoint` also demonstrated the Bluetooth hazard before reaching that block.
It appears nowhere in `PhyphoxFile.java`, because Android's BLE conversion classes read
their own attributes straight from the parser inside `ConversionsInput.java`. Reading the
block parser alone would have declared it iOS-only. The BLE block must be modelled from the
conversion classes outward, not from the element that names them.

The check now runs as part of `mkdocs build --strict`, in the direction that matters:
documented-but-not-modelled fails the build.

### What the maintainer's review of those four attributes changed

Reviewing the undocumented attributes settled more than the four:

| attribute | outcome |
|---|---|
| `bluetooth/address` | Android-only by platform limitation, and now documented with a plain warning that using it makes an experiment Android-only. iOS must **reject** the file rather than silently connect to a different device. |
| `camera/threshold` | An untested planned feature that reached the parser ahead of the decision to ship it. Not part of the format; removed from the spec, to be removed from the parser. |
| `edit/editable` | Makes little sense on an element whose purpose is user input, and is believed unused. Same treatment. |
| `bluetooth/output/decimalPoint` | A plain documentation gap, to be filled when the bluetooth block is modelled. |

Checking `address` prompted a re-read of the whole bluetooth element, which turned up two more
of my own errors:

- **`bluetooth/id` is read by Android too.** I had recorded it as iOS-only from a coarse grep
  over the wrong line range. It is documented, meaningful — it groups entries so the user
  picks a device once — and implemented on both.
- **`bluetooth/mtu` is a documented platform difference**, not an omission. The Bluetooth page
  already says it is "ignored on iOS which has no method to control the MTU size and always
  requests the maximum". Reclassified from `divergent` to `platform`.

So of the six attributes originally in `input-one-sided-attributes`, **four were wrong or
resolvable and two remain** — `camera/aeFPSTarget` and `depth/smooth`.
`views-one-sided-attributes` is down to one, `interpolateMapColors`. The category that looked
like it would scale with attributes has largely evaporated on inspection, which shifts the
projection further towards "a few rules and a short tail".

### The "one-sided attributes" category dissolved

The `input` probe predicted a category that would scale with attribute count: attributes one
app honours and the other ignores, each needing its own decision. It started with six. On
review, **not one of them was what it looked like**:

| attribute | what it actually was |
|---|---|
| `bluetooth/id` | never one-sided — read by both; my grep covered the wrong lines |
| `bluetooth/mtu` | a documented platform limit; iOS cannot control the MTU |
| `depth/smooth` | a documented platform limit; it selects between two ARKit frame properties |
| `bluetooth/address` | a platform limit needing a clearer failure mode, not a decision |
| `camera/threshold` | not part of the format; being removed from the parser |
| `camera/aeFPSTarget` | ordinary parity work — a 1.20 feature iOS has not implemented |

`views` told the same story: `edit/editable` was unofficial, `interpolateMapColors` is 1.20
parity work. So both "one-sided" entries are gone, replaced by one entry for the 1.20 features
iOS has yet to implement.

**That removes the only category that was projected to grow with the format.** What remains is
a small set of format-wide rules plus a handful of genuine one-offs. Two of the six were my
own misreadings and two were answered by documentation I had not read carefully enough —
which says the modelling needs to consult the prose *for meaning*, not only diff it for names.
`depth/smooth` was documented as iOS-only in the very entry I had classified as an unexplained
divergence.

### A spec-internal check earns its place immediately

An attribute cannot predate the element it belongs to. Adding that check found the
`aeFPSTarget` error it was written for — and one more the same second: `bluetooth` was
modelled as arriving in file format 1.11, a number I had guessed. The Bluetooth page says
plainly that BLE arrived in 1.7. Corrected, along with its two child elements.

The `since` values in this spec came from the documentation where it stated them and from
inference where it did not. The inferred ones deserve the same suspicion as everything else.

### Metadata identifiers: an entry that should never have existed

`metadata-uniqueid-spelling` claimed that Android accepts `uniqueID` and iOS `uniqueId`, so
an experiment requesting the identifier would work on exactly one platform. **That was
wrong.** iOS's *parser* accepts the string `uniqueID` — `PhyphoxElementHandler.swift` maps it
onto an internal case named `.uniqueId` — and `uniqueId` is accepted by neither. The bundled
`sensordb.phyphox` uses `uniqueID` and works on both, which is what prompted the check.

The error came from reading `Metadata.swift`, where the `identifier` property returns
`"uniqueId"`, and assuming that was the parsing surface. It is not: it names the *outgoing*
key. Two different vocabularies in the same file, and I conflated them.

Diffing the accepted sets properly: iOS's parser takes 19 identifiers, Android's enum 20, and
the only difference is Android's `sensorMetadata`, which is an internal routing value rather
than something a file would ever contain. Both are case-sensitive — iOS switches on exact
strings, Android uses `Enum.valueOf` — and they agree. Entry deleted.

Worth noting what this means for the case-sensitivity rule: `enum-case-insensitive` is scoped
to attributes with `type: enum`. Metadata identifiers are element *text*, so the rule does not
reach them, and both parsers are strict there. Whether it should be extended is an open
question, not an established divergence.

### The output block, and Bluetooth: the reflection hazard was smaller than feared

`output.yml` covers the block and, with it, the Bluetooth surface that spans both blocks —
`<bluetooth>` appears in `input` and `output` and they are *different elements*, sharing the
device-matching attributes and the `config` child but nothing else.

The block itself is small: 10 elements, 20 attributes. The interesting part is how the
conversion vocabulary had to be established. **Android resolves a conversion by reflection** —
it looks for a declared class of that name taking an `XmlPullParser`, which then reads its own
attributes, and falls back to a declared static method of the same name. So the vocabulary is
the set of declared classes and methods of `ConversionsInput`/`Output`/`Config`, and an
attribute such as `decimalPoint` appears nowhere in the block parser. iOS uses a
`ConversionFunction` enum plus a switch for the three names that are not simple numeric
conversions.

Compared name by name: **all three vocabularies agree exactly, 21 names each.** The block with
the most alarming mechanism turned out to have the most agreement in its core. Worth stating,
because the expectation going in was the opposite.

Two findings did come out of it:

- **The flashlight output does not exist on iOS at all** — no handler, no mention anywhere in
  the source. It is a file format 1.20 feature, so it joins `ios-behind-on-format-1-20`, and
  it is the largest single item there: an element, its `input` child and three parameters.
- `address` and `mtu` are Android-only on the output `<bluetooth>` exactly as on the input
  one, so the decisions already taken cover both.

The tooling needed one fix: a documentation page can describe more than one block, and
comparing `bluetooth-low-energy.md` against each spec file separately reported each block's
constructs as missing from the other. Pages are now compared against the *union* of the specs
that claim them, which also let the last `OTHER_BLOCK` exception go.

### The analysis block: a different shape, and the sharpest bug yet

`analysis.yml` covers the block and all 54 modules: 55 elements, 43 attributes and **194
named input/output slots**. It is structurally unlike the other three — the attribute count is
small, and almost the whole surface is the slot vocabulary of each module (`minuend` and
`subtrahend` for `subtract`, `x`/`y`/`threshold` for `threshold`, and so on).

Only Android states that vocabulary declaratively. Every module carries an `ioMapping` table
naming each slot, whether `as` is required for it, how many may appear and whether a literal
value is allowed. iOS resolves the same names implicitly — `priorityInputKey` in the
complex-update modules, position elsewhere. **Android's tables are the only explicit statement
of the slot names anywhere, including the documentation**, which describes them in prose.

The comparison came out well: 54 modules on Android against 52 on iOS, differing only by
`butterworth` and `imagedecode` (already recorded as 1.20 work), and 21 of the 24 modules that
carry attributes agree exactly.

The other three were `sinh`, `cosh` and `tanh` — and that turned out not to be an attribute
disagreement at all but **iOS computing the wrong function**. `ExperimentAnalysisFactory`
maps them onto `SinAnalysis`, `CosAnalysis` and `TanAnalysis`; the correct classes exist and
are referenced nowhere. Recorded as `ios-hyperbolic-modules-compute-trig`, since decided.

Worth noting how it surfaced. The extractor reported iOS reading a `deg` attribute on the
hyperbolic modules, which is mathematically meaningless — hyperbolic functions take a number,
not an angle. It looked like a fault in the tooling. It was the tooling being right about
something surprising. That is now the third time a wrong-looking extraction result has been
correct, against a consistent instinct to assume my own error first.

### The slot constraints, which the first pass reduced to comments

The first version of `analysis.yml` recorded the slot *names* and put a few of their
properties in YAML **comments** — so they were neither machine-readable nor complete. It also
dropped `asRequired` entirely, which matters more than anything else on that list.

Re-extracted properly, with Android's defaults applied rather than only the fields each
`ioMapping` sets explicitly, all 194 slots now carry:

| field | meaning | count |
|---|---|---|
| `as_required` | the `as` attribute must name this slot; an unnamed tag is never matched to it | **104 of 194** |
| `min` / `max` | how many tags may fill it (`unlimited` is Android's `maxCount = 0`) | — |
| `allows_value` | whether `type="value"` is accepted | 37 refuse it |
| `allows_empty` | whether `type="empty"` is accepted | only 3 accept it |
| `repeat_offset` | the slot belongs to a repeating group | 25 |

Two of those defaults are traps. `asRequired` defaults to **true**, so a slot is
`as`-required unless a module explicitly says otherwise — the opposite of what the sparse
Java initialisers suggest at a glance. And `maxCount = 0` means *no maximum*, not *none
allowed*, which the first pass had recorded as "repeatable" and conflated with
`repeatableOffset`.

**Android enforces all four; iOS enforces none.** It matches the `as` names each module knows,
falls back to document order, and applies no per-slot restriction on type or count. So a file
that omits a required `as` is refused by Android with a precise message and accepted by iOS,
which assigns positionally and runs an experiment computing something other than what its
author wrote. Recorded as `analysis-slot-constraints-unenforced` — the same shape as
`input-output-component-validation` one level down, and settled by the same decision.

Two things checked along the way that turned out **not** to be divergences, both after reading
further than the first grep suggested:

- `if` looked as though iOS required `as` and threw otherwise. It falls back positionally and
  only throws on a fifth input. Agrees with Android.
- `type="empty"` looked unimplemented on iOS, since no module matches `.empty`. The factory
  converts it into a shared permanently-empty buffer before the module sees it, which is
  exactly Android's semantics.

### Per-module confirmation of the iOS side

The slot table above is Android's. Confirming it against iOS meant reading all 52 modules
rather than inferring from a pattern. **48 agree**; four did not, and two of those are real.

**`average` — silently swapped values.** Android maps the outputs by name and the
documentation gives the standard deviation as `stddev`, `as` required. iOS looks for `"std"`
and otherwise falls back to position:

    if output.asString == "std" || avg != nil { std = output } else { avg = output }

So the documented name has no effect on iOS, and writing the outputs in the order
stddev-then-average — which Android accepts and maps correctly — puts the mean in the
standard deviation's buffer and vice versa. The experiment runs and the graph is plotted.

**`loess`** does the same for its three interpolation outputs, reading `outputs[0..2]`
positionally and never looking at their names, where Android requires `as` on `yi1` and
`yi2`. Both are recorded as `analysis-outputs-assigned-by-position`.

**`info`** was two false alarms and one real finding, and I got both false alarms backwards
before the maintainer corrected them.

`wifiSignalStrength` is a **documented platform limitation**, not a gap: iOS cannot obtain the
metric, and the documentation says so. It is right that iOS accepts the output and leaves the
container unfilled rather than refusing the file — the info module exists as a way in to
obscure system-specific values, and the other outputs of the same module stay useful. Marked
`platform`. The three battery outputs are the same, and 1.20 besides.

`info/batteryLevel` I reported as a documentation error, on the grounds that the docs require
`as` where Android's table has `asRequired = false`. **It is the other way round**: the
documentation is correct, `as` should be required as it is for every other output of the
module, and Android is the one to fix. Recorded as
`android-info-batterylevel-as-optional`; my "correction" to the page has been reverted.

**`power`** was a false positive: iOS does not match `exponent` by name, but with `base` as its
priority key the two-input case resolves correctly whichever order they appear in.

Both `info` mistakes share one cause with an earlier one. A definition-list term in these pages
carries `:` lines for type and requirement, and then a **paragraph underneath** with the
description — and that paragraph is where the platform notes live. "Only available on Android."
for `wifiSignalStrength`, "Only applies to LiDAR on iOS devices" for `depth/smooth`. I read the
`:` lines and skipped the prose, twice. `tools/spec_vs_docs.py` compares names and cannot catch
this; only reading can.

### Revised projection

Four blocks are now modelled — `input`, `views`, `output` and `analysis` — leaving
`network-connections` and the small root block. 101 elements, 249 attributes and 194 named
analysis slots, leaving roughly 80,
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
3. Document `bluetooth/output/decimalPoint` while modelling that block — implemented by both
   apps, described nowhere. `EXPECTED_UNDOCUMENTED` in `tools/spec_vs_docs.py` carries the
   reminder.
4. Only then write the generator. Generating reference pages from a spec that is still
   changing shape wastes the generator twice.
