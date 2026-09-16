# Next release (unreleased)

In development. This page collects the format changes of the release that is currently being prepared; it is renamed to the version number when the release ships.

## File format update to version 1.21

- New attribute *preferUncalibrated* for sensor inputs: an experiment can start with the uncalibrated version of a sensor that the device offers in a calibrated and an uncalibrated version (see [Input module: sensor](../../file-format/input.md#input-module-sensor)). The default, calibrated, matches the previous behavior, and the user can still switch between the two versions manually.
- The manual switch between the calibrated and the uncalibrated version, previously offered for the magnetometer only, is available for every sensor type that comes in both versions on the device.
