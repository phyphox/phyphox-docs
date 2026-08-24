# Analysis golden vectors

Deterministic input/output pins for the analysis modules (test-matrix row
`analysis-golden-vectors`). Every case is a miniature experiment whose
input data arrives through container `init` values — the real parser is
the injection path — plus a machine-readable statement of what the output
buffers must hold after a given number of analysis cycles.

- `cases/<module>.yml` — the human-authored source: buffers, the module's
  input/output tags, attributes, cycle count, expected values, tolerances.
  Expected values are computed with `tools/analysis_reference.py`
  (`expected_source: reference`), a plain-Python restatement of the
  semantics both apps agreed on in the 2026-08 audit.
- `vectors/<module>/<case>.phyphox` and `.expected.json` — generated from
  the case files by `tools/generate_analysis_vectors.py` and committed;
  the docs build regenerates them and fails on drift, so the YAML stays
  the single source of truth and the app runners need neither YAML nor
  Python.

## The runner contract

Both app test suites run every pair under `vectors/`. The contract:

- **Where.** The vectors are found in a phyphox-docs checkout next to the
  app repository, like the conformance corpus; a missing checkout skips
  with a visible notice, CI checks the sibling out explicitly.
- **Load** each `.phyphox` through the real experiment-loading path. A
  file declaring a newer format version than the platform supports is
  skipped, not failed (same rule as corpus-valid-load).
- **Never start the experiment.** No start event is recorded, no sensors
  run, no views exist. The `timer` cases rely on this: the experiment
  time before the first start is exactly 0.
- **Drive the analysis kernel directly**, once per cycle, for the number
  of cycles the `.expected.json` states, with cycle numbers 0, 1, 2, ….
  One kernel run is exactly what one in-app analysis pass does per module
  in document order: honor the module's `cycles` attribute against the
  current cycle number; snapshot the inputs; clear `keep=false`
  non-static input buffers on read; clear non-`append` output buffers
  before writing (the `if` module manages its own output clearing); run
  the module. The scheduling layer above the kernel — `sleep`,
  `dynamicSleep`, `onUserInput`, `requireFill` — must not gate the runs
  (no vector uses those attributes).
- **Compare** after the cycle whose 1-based execution count equals an
  `expect` entry's `after_cycle`: for each listed buffer the full
  contents must match the expected list — same length, NaN equal to NaN,
  infinities by sign, finite values within
  `|actual - expected| <= abs + rel * |expected|` using the per-buffer
  `rel`/`abs` overrides or the file's `default_tolerance`. In the JSON,
  non-finite expected values are the strings `"nan"`, `"inf"`, `"-inf"`.
- A mismatch is a **finding to report, not to code around**: either the
  reference expectation or both apps are wrong, and which one is a docs
  decision (the case files record the derivation).

## What the vectors deliberately avoid

Constructs whose behavior currently differs between the platforms or is
inherently non-deterministic are left out:

- `atan2` mixing a fixed value with a longer buffer
  (`atan2-scalar-input`, decided: element-wise) — buffer-with-buffer
  cases only until iOS conforms; then a mixed case is added.
- `timer`'s `offset1970` output — the current timestamp before the first
  start (both platforms conform since 2026-08-24), inherently unpinnable
  as a golden value; only the experiment-time output is pinned, in the
  never-started state.
- `static="true"` buffers (`static-buffer-lifecycle`, decided: written
  once, module skipped, reset by user clear) — a skip-pinning
  multi-cycle case is added once iOS conforms.
- The block-level `requireFill` gate (`requirefill-first-run`, decided:
  the first run is exempt) — a case is added once iOS conforms.
- `fft` with non-power-of-two input (`fft-non-power-of-two-input`,
  permanent) — power-of-two lengths only. The fft and crosscorrelation
  tolerances are widened to cover Android's float32 native path, and
  gausssmooth's for iOS's single-precision vImage path.
- The `info` module — every output is live device state; no vector
  exists for it.
- `periodicity` without an explicit min/max search range (the adaptive
  scan), and degenerate parameters (NaN overlap, empty dx) where the
  platforms differ at the edges.

These files are parsing-and-math fixtures, not maintained experiments:
they declare no views and are never started.
