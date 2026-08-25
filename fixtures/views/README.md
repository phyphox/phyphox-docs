# View fixtures

The fixture set behind the view-element suites (test-matrix rows
`view-snapshots`, `graph-snapshots`, `view-behavior`): one experiment per
element family, every configuration worth a golden, all data fixed by
container `init` values — loading one of these renders a deterministic
screen with no sensors and no analysis.

- `values`, `edits`, `buttons-toggles`, `sliders-dropdowns`,
  `info-separator-image` — the non-graph elements (row `view-snapshots`,
  T0: Robolectric on Android, swift-snapshot-testing on iOS).
- `graphs-styles`, `graphs-axes`, `graphs-special` — the OpenGL-rendered
  graphs (row `graph-snapshots`, T1: emulator + PixelCopy on Android,
  GLKView.snapshot in the simulator on iOS).
- The same files drive the behavior tests (row `view-behavior`, T1):
  type into the edits, press the buttons, move the sliders, pick from
  the dropdown — and assert the target buffers through the remote API.
  The elements' outputs are wired so every interaction has an observable
  buffer effect.

## The snapshot contract

- **Goldens live in the app repos**, not here — they are renderer
  output, platform-specific by nature (plain git, no LFS). What is
  shared is this fixture set and the configuration matrix.
- **Configurations per fixture**: light and dark theme; two font scales
  (1.0 and the platform's large setting); phone and tablet width; one
  RTL smoke pass (forced RTL layout direction — no RTL language ships
  yet, so this is layout-mirroring only, not translation).
- **Naming**: goldens are keyed by fixture stem, view element label and
  configuration (e.g. `values/precision-6/dark-phone`), so a failing
  golden names its fixture line directly.
- A golden mismatch after an intentional UI change is re-recorded on
  the platform where it changed; a mismatch on ONE platform after a
  cross-platform change is a finding for the docs session.

These files are render fixtures, not maintained experiments: never
started, no analysis, nothing device-dependent (the image resolves
against the bundled res folder).
