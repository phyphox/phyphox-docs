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
- **Never start the experiment.** No start event is recorded and no
  sensors run (the vectors carry a minimal view, but nothing renders).
  The `timer` cases rely on this: the experiment time before the first
  start is exactly 0.
- **Drive the analysis kernel directly**, once per cycle, for the number
  of cycles the `.expected.json` states, with cycle numbers 0, 1, 2, ….
  One kernel run is exactly what one in-app analysis pass does per module
  in document order: honor the module's `cycles` attribute against the
  current cycle number; snapshot the inputs; clear `keep=false`
  non-static input buffers on read; clear non-`append` output buffers
  before writing (the `if` module manages its own output clearing); run
  the module. Of the scheduling layer above the kernel, `sleep`,
  `dynamicSleep` and `onUserInput` must not gate the runs (no vector
  uses them); `requireFill` MUST be honored with its ruled semantics —
  the first run after opening or starting is exempt, later runs are
  gated — because the execution/requirefill-first-run-exempt case pins
  exactly that.
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

Most cases exercise a single module; `cases/execution.yml` holds the
execution-model cases that need more than one (a per-case `modules:`
list) or an analysis-block attribute (`analysis_attributes:`) — the
static write-once skip and the requireFill first-run exemption, both
ruled 2026-08-24.

## What the vectors deliberately avoid

Constructs that are inherently non-deterministic or platform-defined
are left out:

- `timer`'s `offset1970` output — the current timestamp before the first
  start (ruled 2026-08-24), inherently unpinnable as a golden value;
  only the experiment-time output is pinned, in the never-started state.
- The static-buffer reset on the user's clear-data action (ruled with
  the write-once lifecycle) — the runner has no user-clear step; the
  write-once skip itself is pinned by execution/static-write-once.
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
they carry the minimal view the loading path requires and are never
started.
