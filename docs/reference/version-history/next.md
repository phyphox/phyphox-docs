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

## Changes on Android and iOS

- An empty graph explains itself: "No data" while nothing has been measured, "No valid data" when every point is NaN or one axis has no values, and "No data in range" with an arrow towards the nearest point when the data lies outside the current zoom or a fixed range (see [Graph: axis ranges and empty plots](../../file-format/views/graph.md#axis-ranges-and-empty-plots)).
- A graph whose values on an axis are all identical (or a fixed range with min = max) opens a small range around that value with a single tic, instead of an empty plot or an inverted axis.
- Graph headroom is only added at axis ends the data determines: a fixed range, a zoomed range and a followed x range are shown exactly as set. Previously Android padded fixed ends too and iOS lost the padding on a one-sided fixed axis.
- Tic labels on the plot border (fixed ranges, zoom) are kept inside the plot instead of being clipped by the view or colliding with the neighbouring axis.
- The graphs of the remote interface are rebuilt on Chart.js 4 and built by the interface itself from a graph description the app embeds, instead of JavaScript generated by the app. New there: zoom and pan with mouse (drag, wheel, shift+drag box) and touch (pinch, drag), a follow mode, a data picker like the app's (nearest point, two-point difference and slope) that writes the experiment's pick outputs, log axis toggles, clock-labelled time axes, zoomable color maps with a color scale, "No data" hints, and a tap or click on a plot to maximize it. The interface still loads nothing from the network.

## Changes on Android

- Fix: on a graph without a colour map, the x tic labels were drawn left-aligned on the first frame, and a label at the right border vanished.
- The magnetometer and gyroscope switches in the experiment menu are joined by one for the accelerometer, shown when the device offers the uncalibrated type.
- Fix: the calibrated magnetometer always reported accuracy 3, whatever the system said.
- Fix: an averaged accuracy value never exceeded 0.

## Changes on iOS

- Fix: a graph with *followX* showed the minX..maxX window of the attributes until the first zoom gesture instead of following new data from the start.
- The experiment menu offers a raw/calibrated switch for the gyroscope, next to the existing one for the magnetometer.
