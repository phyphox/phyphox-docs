# Next release (unreleased)

In development. This page collects the format changes of the release that is currently being prepared; it is renamed to the version number when the release ships.

## File format update to version 1.21

- New attribute *preferUncalibrated* for sensor inputs: an experiment can start with the uncalibrated version of a sensor that the device offers in a calibrated and an uncalibrated version (see [Input module: sensor](../../file-format/input.md#input-module-sensor)). The default, calibrated, matches the previous behavior, and the user can still switch between the two versions manually.
- The manual switch between the calibrated and the uncalibrated version, previously offered for the magnetometer only, is available for every sensor type that comes in both versions on the device.
- The *accuracy* output of sensor inputs is no longer limited to the magnetometer: Android reports the calibration status for every sensor type, iOS for the magnetometer and the attitude sensor, and the uncalibrated version of a sensor writes 0 on both platforms (see [Input module: sensor](../../file-format/input.md#input-module-sensor)). This is a behavior change only in that buffers mapped to *accuracy* of other sensors, which stayed empty before, now receive data.

## Changes on Android and iOS

- An empty graph explains itself: "No data" while nothing has been measured, "No valid data" when every point is NaN or one axis has no values, and "No data in range" with an arrow towards the nearest point when the data lies outside the current zoom or a fixed range (see [Graph: axis ranges and empty plots](../../file-format/views/graph.md#axis-ranges-and-empty-plots)).
- A graph whose values on an axis are all identical (or a fixed range with min = max) opens a small range around that value with a single tic, instead of an empty plot or an inverted axis.
- Graph headroom is only added at axis ends the data determines: a fixed range, a zoomed range and a followed x range are shown exactly as set. Previously Android padded fixed ends too and iOS lost the padding on a one-sided fixed axis.
- Tic labels on the plot border (fixed ranges, zoom) are kept inside the plot instead of being clipped by the view or colliding with the neighbouring axis.

## Changes on Android

- Fix: on a graph without a colour map, the x tic labels were drawn left-aligned on the first frame, and a label at the right border vanished.
- The magnetometer and gyroscope switches in the experiment menu are joined by one for the accelerometer, shown when the device offers the uncalibrated type.
- Fix: the calibrated magnetometer always reported accuracy 3, whatever the system said.
- Fix: an averaged accuracy value never exceeded 0.

## Changes on iOS

- Fix: a graph with *followX* showed the minX..maxX window of the attributes until the first zoom gesture instead of following new data from the start.
- The experiment menu offers a raw/calibrated switch for the gyroscope, next to the existing one for the magnetometer.
