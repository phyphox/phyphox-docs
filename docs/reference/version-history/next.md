# Next release (unreleased)

In development. This page collects the format changes of the release that is currently being prepared; it is renamed to the version number when the release ships.

## File format update to version 1.21

- New attribute *preferUncalibrated* for sensor inputs: an experiment can start with the uncalibrated version of a sensor that the device offers in a calibrated and an uncalibrated version (see [Input module: sensor](../../file-format/input.md#input-module-sensor)). The default, calibrated, matches the previous behavior, and the user can still switch between the two versions manually.
- The manual switch between the calibrated and the uncalibrated version, previously offered for the magnetometer only, is available for every sensor type that comes in both versions on the device.
- The *accuracy* output of sensor inputs is no longer limited to the magnetometer: Android reports the calibration status for every sensor type, iOS for the magnetometer and the attitude sensor, and the uncalibrated version of a sensor writes 0 on both platforms (see [Input module: sensor](../../file-format/input.md#input-module-sensor)). This is a behavior change only in that buffers mapped to *accuracy* of other sensors, which stayed empty before, now receive data.

## Changes on Android

- The magnetometer and gyroscope switches in the experiment menu are joined by one for the accelerometer, shown when the device offers the uncalibrated type.
- Fix: the calibrated magnetometer always reported accuracy 3, whatever the system said.
- Fix: an averaged accuracy value never exceeded 0.

## Changes on iOS

- The experiment menu offers a raw/calibrated switch for the gyroscope, next to the existing one for the magnetometer.
