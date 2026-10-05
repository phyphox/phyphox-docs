# Next release (unreleased)

In development. This page collects the format changes of the release that is currently being prepared; it is renamed to the version number when the release ships.

## File format update to version 1.21

- New attribute *preferUncalibrated* for sensor inputs: an experiment can start with the uncalibrated version of a sensor that the device offers in a calibrated and an uncalibrated version (see [Input module: sensor](../../file-format/input.md#input-module-sensor)). The default, calibrated, matches the previous behavior, and the user can still switch between the two versions manually.
- The manual switch between the calibrated and the uncalibrated version, previously offered for the magnetometer only, is available for every sensor type that comes in both versions on the device.
- The *accuracy* output of sensor inputs is no longer limited to the magnetometer: Android reports the calibration status for every sensor type, iOS for the magnetometer and the attitude sensor, and the uncalibrated version of a sensor writes 0 on both platforms (see [Input module: sensor](../../file-format/input.md#input-module-sensor)). This is a behavior change only in that buffers mapped to *accuracy* of other sensors, which stayed empty before, now receive data.

Further additions, specified in the documentation first (2026-09-25) and implemented on both platforms, in the remote interface and in the editor from that specification:

- **View groups** - new view elements that contain and arrange other view elements:
  [vertical](../../file-format/views/groups.md#view-element-vertical),
  [horizontal](../../file-format/views/groups.md#view-element-horizontal) (children side by side,
  with a *weight* attribute on each child for the split),
  [grid](../../file-format/views/groups.md#view-element-grid) (rows of equal columns, as many as
  the screen width allows under *maxWidth*, with *fillLastRow*) and
  [stack](../../file-format/views/groups.md#view-element-stack) (children drawn on top of each
  other). Groups nest to any depth; a stack is not interactive and holds only elements that show
  data.
- **transform** - a wrapper inside a stack that scales, rotates, moves or fades its one child
  under the control of data containers, each property bound by an `input` child with an optional
  linear range map (*min*, *max*, *mapMin*, *mapMax*, *clamp*) and a fixed origin (*originX*,
  *originY*). See [View-Element: transform](../../file-format/views/groups.md#view-element-transform).
  Together with images this gives gauges, compasses and map overlays without app changes.
- **Colors with an alpha byte:** every color attribute accepts eight hex digits `RRGGBBAA`; six
  digits stay opaque (see [Colors](../../file-format/colors.md)).
- **Fixed plot area on graphs:** *plotLeft*, *plotTop*, *plotRight* and *plotBottom* pin the
  plot rectangle to fractions of the graph element, so a plot can be aligned with an image below
  it (see [Graph: fixing the plot area](../../file-format/views/graph.md#fixing-the-plot-area)).

Specified 2026-09-27 as a follow-up to the view groups and implemented on both platforms, in the
remote interface and in the editor from that specification:

- **`maxWidthUnit` on grid:** *maxWidth* may be given in multiples of the shorter side of the
  app's window (`screen`) instead of text line heights, so that a grid is one column in portrait
  and two in landscape on phones and tablets alike (see
  [View-Element: grid](../../file-format/views/groups.md#view-element-grid)).
- **`verticalLayout`** on value, edit, toggle, dropdown and slider places the label above the
  control instead of to its left, for narrow columns (see
  [Labels in narrow columns](../../file-format/views/groups.md#labels-in-narrow-columns)).
- **Optional labels:** the label may be left out on value, edit, toggle, dropdown, slider, graph,
  camera-gui and depth-gui, which omits the caption and its space instead of leaving it blank.
  An info without a label keeps the height of one line of text, a button keeps its size with an
  empty caption, as before.

Specified 2026-09-26 as a second follow-up and implemented on both platforms, in the remote
interface and in the editor from that specification:

- **`align`** on value, edit, toggle, dropdown and slider aligns the label and the control left,
  centred or right when they take the full width - with *verticalLayout* or without a label (see
  [Labels in narrow columns](../../file-format/views/groups.md#labels-in-narrow-columns)).
- **`spacing`** on vertical, horizontal and grid inserts a gap between the children, in text
  line heights (see [Sizing](../../file-format/views/groups.md#sizing)).

Specified 2026-09-30 ahead of the implementations and implemented from that specification the
same day on both platforms, in the remote interface and in the editor:

- **Unit references:** the *unit* attributes of value, edit and graph (*unit*, *unitX*, *unitY*,
  *unitZ*, *unitYperX*) take `@id` naming one of the [known units](../../file-format/units.md)
  (`unit="@meter"`, `unitY="@meter_per_square_second"`). A referenced unit is shown with the
  app's symbol and can be converted: a new app setting *Unit system* (as defined by the
  experiment / metric / imperial) converts to the other system's counterpart, and the user can
  switch the unit of any graph axis, value or edit element to another unit of the same quantity
  from a dialog. Text units stay text and are never converted. The placeholder form
  `[[unit_short_…]]` is deprecated and resolves to the same units, so existing experiments
  become convertible unchanged (see [Units](../../file-format/units.md)). Exports and the remote
  interface's data endpoints carry the original values; the remote interface converts in the
  browser.

Specified 2026-09-30 ahead of the implementations and implemented from that specification the
same day on both platforms:

- **Colour channels of the camera input:** the outputs *red*, *green* and *blue* (mean of the
  gamma-encoded channel, 0 to 1) and *linearRed*, *linearGreen* and *linearBlue* (linearized and
  exposure-normalized like *luminance*), defined so that *luma* and *luminance* are exactly the
  BT.709 combination of the respective triple. With the spectroscopy feature the three linear
  channels carry a spectrum each, paired with *pixelPosition* like *luminance* (see
  [Colour channels](../../file-format/input.md#colour-channels)).

Specified 2026-10-01 ahead of the implementations and implemented from that specification the
same day on both platforms:

- **White balance in the camera's *locked* attribute:** `white_balance` alone freezes the
  automatic white balance when the measurement is first started; `white_balance=5600` balances
  for a correlated colour temperature in Kelvin; `white_balance_tint` shifts the white point off
  the Planckian locus as Duv. The format knows no named presets - the phones' presets are only
  approximations that differ per device. The camera-gui's preset picker becomes a control with
  the same three choices, automatic, locked, or a temperature scale with tint, and no named
  presets (see [White balance](../../file-format/input.md#white-balance)).

## Changes on Android and iOS

- **Bluetooth devices can control the measurement.** A device that offers the new [command characteristic](../../file-format/bluetooth-low-energy.md#phyphox-command-characteristic-0005) (`cddf0005-…`) can start, pause and toggle the measurement and clear the data, with the same meaning as the app's own buttons, and ask the app to report its current state on the event characteristic. A clear from a device leaves clear groups alone unless it explicitly asks for them.
- **Saved states are a new file format.** A saved state is a zip container with the experiment file untouched, the recorded data as binary files, and the title, time reference and device as CSV files, in the layout of the CSV export (see [Saved states](../../saved-states.md)). Shared states get the `.zip` extension. States saved by earlier versions, with the data in the *init* attributes and the `state-title` and `events` tags, keep loading; those two tags are deprecated and no longer written. Apps older than 1.3.0 open a new saved state as the plain experiment, without its data.
- An empty graph explains itself: "No data" while nothing has been measured, "No valid data" when every point is NaN or one axis has no values, and "No data in range" with an arrow towards the nearest point when the data lies outside the current zoom or a fixed range (see [Graph: axis ranges and empty plots](../../file-format/views/graph.md#axis-ranges-and-empty-plots)).
- A graph whose values on an axis are all identical (or a fixed range with min = max) opens a small range around that value with a single tic, instead of an empty plot or an inverted axis.
- Graph headroom is only added at axis ends the data determines: a fixed range, a zoomed range and a followed x range are shown exactly as set. Previously Android padded fixed ends too and iOS lost the padding on a one-sided fixed axis.
- Tic labels on the plot border (fixed ranges, zoom) are kept inside the plot instead of being clipped by the view or colliding with the neighbouring axis.
- The graphs of the remote interface are rebuilt on Chart.js 4 and built by the interface itself from a graph description the app embeds, instead of JavaScript generated by the app. New there: zoom and pan with mouse (drag, wheel, shift+drag box) and touch (pinch, drag), a follow mode, a data picker like the app's (nearest point, two-point difference and slope) that writes the experiment's pick outputs, log axis toggles, clock-labelled time axes, zoomable color maps with a color scale, "No data" hints, and a tap or click on a plot to maximize it. The interface still loads nothing from the network.
- Leaving a maximized graph after zooming asks "Keep this view?" instead of the old "Apply zoom" dialog: "Reset zoom" and "Keep this section" answer it directly, "More options…" opens the per-axis choices (reset, keep, keep and follow new data, and applying the range to other graphs with the same data, the same unit or any x/y axis), each headed by the axis label and its zoomed range in the displayed unit. The question is only asked when something is zoomed; switching a time axis to system time alone no longer triggers it. iOS now also offers the colour scale of a colour map in the per-axis choices, and no longer drops a kept colour-scale zoom when another axis is reset. The remote interface asks the same question.
- Easier ways back from a maximized graph, camera preview or depth preview: the collapse icon is clearly larger than before (twice its size on Android, one and a half times on iOS, two text lines high in the remote interface); a tap anywhere outside the plot of a maximized graph (except on an axis title, which opens the unit dialog) collapses it; the back arrow of the toolbar first collapses a maximized element and leaves the experiment only when nothing is maximized; a tab change while an element is maximized waits until the element has been collapsed (a zoomed graph asks first, Cancel stays), and the page swipe is disabled meanwhile.
- Sonar and Doppler effect: both experiments got a new analysis. The sonar loops a strictly periodic chirp (a 10 ms sweep from 2 to 10 kHz in a 2048-sample period), so any recording contains whole periods and no alignment of playback and recording is needed; a crosscorrelation with the chirp and its quadrature gives the envelope, averaged over seven chirps, and echoes are timed and scaled relative to the direct sound from speaker to microphone. The Doppler effect experiment asks only for the base frequency, a time step and the speed of sound, mixes the recording down with the base frequency and fits the phase over each time step to get the frequency; values appear only while the phase is coherent, so noise and silence produce no points. Views, histories, maps and exports keep their structure.
- Audio output: a looped output plays on undisturbed when the next analysis cycle ends, and a one-shot output starts over from its beginning even if it has not finished yet. Previously Android restarted a looped waveform after every cycle (it stayed continuous only if its length divided 2048 samples), while iOS let an unfinished one-shot output play to its end and cut it at its old length when its data grew in the meantime (see [Output module: audio](../../file-format/output.md#output-module-audio)).

## Changes on Android

- Fix: a file without a *locale* attribute on its root element could get a translation block that did not match the device language, most visibly a German block on an English device whose locale carries no region (as the in-app language setting produces). The base strings now count as English, as on iOS, and a block carrying the file's own base language stands in for them (see [Block: translations](../../file-format/index.md#block-translations)).
- Fix: on a graph without a colour map, the x tic labels were drawn left-aligned on the first frame, and a label at the right border vanished.
- The magnetometer and gyroscope switches in the experiment menu are joined by one for the accelerometer, shown when the device offers the uncalibrated type.
- Fix: the calibrated magnetometer always reported accuracy 3, whatever the system said.
- Fix: an averaged accuracy value never exceeded 0.

## Changes on iOS

- Fix: a graph with *followX* showed the minX..maxX window of the attributes until the first zoom gesture instead of following new data from the start.
- The experiment menu offers a raw/calibrated switch for the gyroscope, next to the existing one for the magnetometer.
