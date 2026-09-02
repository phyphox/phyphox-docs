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
- `init-vs-default` — behavior only, no goldens: every input control once
  over a container that already holds a value and once over an empty one.
  The spec says a default fills an EMPTY buffer and never overwrites one,
  and both halves have to be asserted together, because "fixing" the first
  by not seeding at all would break the second. It asserts again after
  paging away and back: a load builds each page once, but a rebuilt widget
  used to hand its own default to the next write pass, which is the form
  the bug actually took on Android.
- The same files drive the behavior tests (row `view-behavior`, T1):
  type into the edits, press the buttons, move the sliders, pick from
  the dropdown — and assert the target buffers through the remote API.
  The elements' outputs are wired so every interaction has an observable
  buffer effect.

## The snapshot contract

- **Goldens live in the app repos**, not here — they are renderer
  output, platform-specific by nature (plain git, no LFS). What is
  shared is this fixture set and the configuration matrix.
- **The golden locale is part of the contract.** Value formatting is
  locale-dependent (1234.5678 renders as 1.234,57 on a German device and
  1,234.57 on en_US), so every golden is recorded and compared in
  **en_US with English resources**, forced by the harness — iOS pins
  `-AppleLocale en_US -AppleLanguages (en)` in the test action, Android
  the equivalent Robolectric/instrumentation locale override. Rendering
  in OTHER languages is the translations-ui row's job, not a golden
  here.
- **Theme is a phyphox setting, not the system's.** The app defaults to
  dark regardless of the system theme and can be set to light, dark, or
  follow-system. The full golden matrix runs the two explicit settings
  (light, dark); the two follow-system combinations (system light,
  system dark) are covered by spot-check goldens on one fixture, pinning
  the resolution logic without doubling the whole matrix.
- **Configurations per fixture**: the two explicit themes; two font
  scales (1.0 and the platform's large setting); phone and tablet width;
  one RTL smoke pass (forced RTL layout direction — no RTL language
  ships yet, so this is layout-mirroring only, not translation). The
  RTL pass currently means different things per platform, deliberately
  recorded rather than papered over: iOS mirrors already (UIKit does it
  without an opt-in), so its goldens capture real mirrored layouts;
  Android does not yet declare RTL support, so its pass is a no-op whose
  goldens are identical to LTR — which is itself the pin: the day
  supportsRtl is switched on (needed before ar/fa can ship), those
  goldens change loudly instead of silently. Do not read the row as
  "RTL layout is covered on both platforms".
- **Naming**: goldens are keyed by fixture stem, view element label and
  configuration (e.g. `values/precision-6/dark-phone`), so a failing
  golden names its fixture line directly.
- A golden mismatch after an intentional UI change is re-recorded on
  the platform where it changed; a mismatch on ONE platform after a
  cross-platform change is a finding for the docs session.

These files are render fixtures, not maintained experiments: never
started, no analysis, nothing device-dependent (the image resolves
against the bundled res folder).
