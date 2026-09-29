# Units

!!! note "New in file format 1.21 (phyphox 1.3.0)"
    Unit references are part of file format 1.21, which the
    [next release](../reference/version-history/next.md) carries. A file using them must declare
    that version, and every app released before it refuses such a file. This page was written
    ahead of the implementations (2026-09-30): it is the design the apps, the remote interface and
    the editor are built from.

Several view elements show a unit next to a number: the [value](views/basics.md#view-element-value)
and [edit](views/user-input.md#view-element-edit) elements with their *unit* attribute, and the
[graph](views/graph.md) with *unitX*, *unitY*, *unitZ* and *unitYperX*. Each of these attributes
takes either a **unit reference** or plain **text**.

## Unit references

A unit reference is the character `@` followed by the id of one of the [known units](#known-units):

```xml
<value label="Distance" unit="@meter">
    <input>distance</input>
</value>
<graph label="Acceleration" labelX="[[quantity_short_time]]" unitX="@second"
       labelY="[[quantity_short_acceleration]]" unitY="@meter_per_square_second">
    <input axis="x">t</input>
    <input axis="y">a</input>
</graph>
```

A reference names the unit *logically*. The app shows the unit's symbol from its own string
table, never text from the experiment file, and it knows what the unit measures, so it can
convert the values to any other unit of the same quantity — a length shown in metres can be shown
in centimetres or in feet at the user's request ([Conversion in the app](#conversion-in-the-app)).
The ids are English words, so they can be typed on any keyboard; `@micro_tesla` displays as µT
(with the micro sign U+00B5, which is the character the apps use for every micro- prefix).

Anything that is not a unit reference is **text**: `unit="m/s³"`, `unitYperX="rad/s²"`,
`unit="m (WGS84)"`. Text is shown exactly as written, can be translated through the
[translation block](index.md#block-translations) like any other string, and is never converted.
This is what every experiment written before file format 1.21 uses, and it remains the way to
write a unit the table does not know.

Three rules follow from the version gate:

- In a file declaring a format **older than 1.21**, a value starting with `@` is text like any
  other, so a reference never changes what a released app shows. The
  [validators](../reference/validators.md) warn about it, because the author almost certainly
  meant to declare 1.21.
- In a 1.21 file, an `@` followed by an **unknown id** (`@metre`) is a validation error. The apps
  tolerate it as text and show it verbatim, without conversion: the value space of a unit
  attribute is open, so an unknown id cannot be told from a deliberate custom string with
  certainty, and showing the author's text hides nothing.
- A reference is not translatable. The symbols are language-independent, and where a language
  uses native designations (Cyrillic-script languages write м/с² for m/s²), the app's own string
  table provides them, which is what `[[…]]` placeholders already did.

### The deprecated placeholder form

Since phyphox 1.1.6 an experiment could write a unit as a
[common-string placeholder](index.md#common-strings), `unit="[[unit_short_meter]]"`, which the
app replaced by the translated symbol `m`. That form did nothing but look the symbol up. From
file format 1.21 it is **deprecated**: every placeholder of the 2021 set resolves to the same
logical unit as the corresponding reference (`[[unit_short_meter]]` behaves exactly like
`@meter`), so existing experiments become convertible without being edited, and the placeholder
stays accepted in every format version. New experiments write `@meter`. The validators warn about
the placeholder form in a 1.21 file, and the table below lists which ids ever had one — the units
added with 1.21 have no placeholder form, only the reference.

## Known units

The table is generated from `spec/units.yml`, which is the single source for the validators and
for the conversion tables of the apps and the remote interface. Units of one quantity convert
into each other through the quantity's base unit; the *conversion* column gives the factor to
that base unit. *System* is metric, imperial or common (neither — a unit the unit-system setting
never touches); *counterpart* is the unit the app switches to when the user forces the other
system.

{{units}}

Two units look alike and are deliberately distinct: `@per_minute` (1/min) is a frequency, the
reading of a heart-rate or event counter, while `@revolution_per_minute` (rpm) is an angular
velocity with 2π radians per revolution. Conversion between angles and time-based quantities
(rad/s ↔ Hz) is not offered.

## Conversion in the app

This section defines the behaviour both apps and the remote interface implement for a unit
given as a reference. Text units are never converted and show none of the controls below.

**The unit-system setting.** A setting of the app, *Unit system*, offers three values:

- *As defined by the experiment* (the default) shows every unit as the file names it.
- *Metric (SI)* replaces every unit of the imperial system by its counterpart (ft → m, in → cm,
  mph → km/h, °F → °C). Metric units are left alone even where they are not strict SI (km/h, °C,
  hPa), and so are the common units (s, Hz, °, dB, %).
- *Imperial / US customary* replaces every metric unit that has a counterpart (m → ft, cm → in,
  mm → in, km → mi, km/h → mph, m/s² → ft/s², hPa → inHg, °C → °F, lx → fc). Units without a
  counterpart (nm, µm, µT, Pa, bar) and the common units stay. One option covers both imperial
  and US customary units: for the quantities phyphox shows they agree.

The counterparts are declared in the table, not computed: the nearest unit by magnitude would
map metres to yards, and the intent is feet. The setting is applied when an experiment is loaded.

**Switching a unit by hand.** Independently of the setting, the user can change the unit of any
element that shows a referenced unit: on a graph by tapping an axis while the graph is in its
exclusive (maximised) mode — the x and y axis labels, and the colour-scale label for z — and on a
value or edit element by tapping the unit text. A dialog lists every unit of the same quantity,
in the order of the table and grouped by system, with the experiment's own unit marked as its
default. The choice holds while the experiment is open and is not stored: it is not part of a
saved state, and reopening the experiment applies the setting again.

**What a converted element shows.** Everything the element displays uses the converted numbers:
the value text, the edit field (a number the user types is converted back before the *factor*
of the element is applied, and the *min* and *max* limits, which are in buffer units, are
converted the same way for the check), axis tick labels, fixed and extended axis ranges, the
*followX* window, the points, differences and slope of the [data picker](views/graph.md#data-picker),
and the colour scale of a colour map. The data itself is untouched: buffers, analysis, saved
states, [exports](index.md#block-export) and the [remote interface's](../remote-interface/index.md)
data endpoints always carry the original values. The remote interface performs the same
conversion in the browser from the same table, starting from the phone's setting.

**Elements that are not converted**, even with a referenced unit: a value element whose *format*
is not `float` (degrees-minutes forms are angles by construction), a value element with
*positiveUnit* or *negativeUnit* (those are labels, not units), an edit element with
`decimal="false"` (an integer restriction in feet is not one in metres), and a time axis while
the *system time* toggle shows a clock. These elements offer no unit dialog and the setting
skips them.

**Precision.** The decimals an author chose fit the experiment's unit. After conversion by a
display factor *f* (metres to centimetres: *f* = 100), an explicit *precision* *p* becomes
max(0, *p* − ⌊log₁₀ *f*⌋): a length with two decimals in metres has none in centimetres, one
decimal in centimetres becomes two in inches. The result is never coarser than the author's
resolution. *scientific* and the automatic graph precision are unchanged; the temperature scales
have factors of 1 and 1.8, so their decimals stay as they are.

**Temperature** is the one affine conversion: base = value × scale + offset. Positions — values,
axis ranges, tick labels, picked points — use scale and offset; differences — the data picker's
Δ read-out, the slope, the width of the *followX* window — use the scale alone.

**Slopes.** The data picker shows the slope in *unitYperX* (explicit or composed from the axis
units) as long as both axes show their experiment units. Once either axis has been switched, the
slope value is scaled by the ratio of the two axis scales and the unit is composed from the two
displayed symbols (ft/s per s → "ft/s / s"); an explicit *unitYperX* cannot be converted in
general and is not used in that state.

**Linked zoom.** Graphs whose axes carry the same unit zoom together. With references this is
decided by the logical unit, so two graphs sharing `@second` stay linked when one of them shows
milliseconds, and the range is converted on the way; text units keep linking by equal text.
