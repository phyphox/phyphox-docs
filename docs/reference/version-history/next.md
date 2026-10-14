# Next release (unreleased)

In development. This page collects the changes of the release that is currently being prepared; it is renamed to the version number when the release ships.

## Changes on Android and iOS

- Unit conversion: a new setting switches between metric and imperial units, and tapping the unit of a graph axis, value or input field switches it to another unit of the same quantity. All bundled experiments support it.
- New compass tab in the magnetometer experiment and new speedometer tab in the location (GPS) experiment
- Graphs that belong together (x/y/z, histories) are shown in two columns in landscape
- Reworked Sonar and Doppler effect experiments with a new, more robust analysis that needs no alignment of playback and recording
- New experiments for the phyphox:mini sensor box. Fixed labels and export columns of the phyphox:m experiments
- New language: Azerbaijani
- Remote interface: rebuilt graphs with zoom and pan by mouse and touch, data picker, follow mode, log axes, color maps with a color scale and maximizing a graph by tapping or clicking it
- New file format for saved states: a zip container with the unchanged experiment and the recorded data as binary files (see [Saved states](../../saved-states.md)). Old states keep loading, apps older than 1.3.0 open a new state without its data.
- Bluetooth devices can start, pause and clear the measurement via the new [command characteristic](../../file-format/bluetooth-low-energy.md#phyphox-command-characteristic-0005)
- Camera white balance can be set by color temperature and tint, besides automatic and locked
- "Keep this view?" replaces the "Apply zoom" dialog when leaving a zoomed full-screen graph, with "Reset zoom" and "Keep this section" as direct answers and the per-axis choices under "More options…". It is only asked if something is zoomed.
- Easier ways back from a full-screen graph or camera preview: a larger collapse icon, tapping outside the plot, and the back arrow collapses first before leaving the experiment
- Empty graphs explain themselves ("No data", "No valid data", "No data in range" with an arrow towards the data) and constant values get a small range instead of an empty plot (see [Graph: axis ranges and empty plots](../../file-format/views/graph.md#axis-ranges-and-empty-plots))
- Calibrated/uncalibrated switch in the experiment menu for every sensor that the device offers in both versions (previously magnetometer and gyroscope on Android, magnetometer only on iOS)
- Camera controls in full-screen landscape stand in compact columns beside the preview
- Fix: graph headroom is only added at axis ends determined by the data; fixed, zoomed and followed ranges are shown exactly as set
- Fix: tic labels on the plot border were clipped or collided with the other axis
- Fix: a looped audio output restarted after every analysis cycle (Android), an unfinished one-shot output was not restarted by a new trigger (iOS) (see [Output module: audio](../../file-format/output.md#output-module-audio))
- Fix: input elements (edit, toggle, dropdown, slider) replace a NaN in their data container with their default
- Fix: HTTP network connections could lose a response when two requests finished close together
- Fix: images with a space, & or + in their file name did not load in the remote interface
- Fix: typos in experiment texts

## Changes on Android

- Much smaller download: the app shrinks from 20.5 MB to 7.8 MB
- Fix: crash when picking a point on an empty graph (the most frequent crash of 1.2.1)
- Fix: crash on swipe gestures on some devices
- Fix: crash when loading an experiment file too large for the available memory, now an error message instead
- Fix: crash when saving an export to Downloads failed
- Fix: several rare crashes around the camera preview, graphs and network requests
- Fix: sensors not found if the system reports no default sensor of a type. The device info lists more details on the sensors.
- Fix: a control's default overwrote the *init* value of its data container
- Fix: zoom and "keep and follow new data" were lost on a tab switch
- Fix: the data picker's readout was drawn inverted (black in light mode)
- Fix: a full-screen graph collapsed to nothing when the remote access or Bluetooth status bars left little space
- Fix: the white balance panel stayed open after leaving the full-screen camera preview
- Fix: the *scale* attribute of images left blank space around the image instead of resizing it
- Fix: a file without a *locale* attribute could get a translation block that did not match the device language (see [Block: translations](../../file-format/index.md#block-translations))
- Fix: x tic labels left-aligned on the first frame, and a label at the right border vanished
- Fix: the calibrated magnetometer always reported accuracy 3, and an averaged accuracy never exceeded 0
- Fix: *fft* of a single sample returned nothing

## Changes on iOS

- Minimum iOS version increased to 15.0 (dropping iPhone 5s, 6, 6 Plus, iPad Air 1, iPad mini 2/3 and iPod touch 6)
- Bluetooth headphones keep playing while the microphone records
- Buttons use the system button style
- Fix: crash when audio recording stops (the most frequent crash since 1.1.11)
- Fix: crashes in graph updates (the most frequent new crash of 1.2.1), in concurrent sensor access and on tab taps during a page transition
- Fix: pan and zoom froze after switching off the log scale (audio spectrum)
- Fix: Bluetooth config and event writes could be dropped (for example the script of a puck.js)
- Fix: a Bluetooth input without *mode* was rejected instead of defaulting to notification
- Fix: an empty visibility data container did not hide its element
- Fix: a graph with *followX* did not follow new data until the first zoom gesture
- Fix: the microphone's rate was missing until recording started, distorting the history of a loaded audio spectrum
- Fix: hint bubbles were hidden behind the navigation bar
- Fix: an unknown `[[…]]` placeholder was shown as "common_…" instead of verbatim

## File format update to version 1.21

- View groups *vertical*, *horizontal*, *grid* and *stack* contain and arrange other view elements and nest to any depth, with *weight*, *spacing*, *maxWidth* in multiples of the screen and *fillLastRow* (see [View groups](../../file-format/views/groups.md))
- New element *transform* inside a stack scales, rotates, moves or fades its child controlled by data containers (see [View-Element: transform](../../file-format/views/groups.md#view-element-transform))
- New drawing elements *geometry* (rectangle, circle, line, ring segment) and *scale* (gauge axis with tics, values and a converted unit), so gauges can be built without images (see [Drawing elements](../../file-format/views/drawing.md))
- Unit references: *unit* attributes of value, edit and graph take `@id` of a [known unit](../../file-format/units.md) (`unit="@meter"`), which the app can convert. The `[[unit_short_…]]` placeholders are deprecated and resolve to the same units.
- Colors with an alpha byte as `RRGGBBAA` (see [Colors](../../file-format/colors.md))
- New attributes *plotLeft*, *plotTop*, *plotRight* and *plotBottom* fix the plot area of a graph, for example to align it with an image (see [Graph: fixing the plot area](../../file-format/views/graph.md#fixing-the-plot-area))
- New attributes *verticalLayout* and *align* for value, edit, toggle, dropdown and slider, and the label may be omitted on most elements (see [Labels in narrow columns](../../file-format/views/groups.md#labels-in-narrow-columns))
- New camera outputs *red*, *green*, *blue* and their linear counterparts *linearRed*, *linearGreen*, *linearBlue*, the latter also as spectra (see [Colour channels](../../file-format/input.md#colour-channels))
- The camera's *locked* attribute sets the white balance by color temperature and tint (see [White balance](../../file-format/input.md#white-balance))
- New analysis modules *dft* and *idft* for any input length and *ifft*, all four Fourier modules with a new *normalization* attribute (see [Fourier transforms](../../file-format/analysis/advanced-math.md#fourier-transforms))
- New attribute *nameRegex* for Bluetooth devices, matching the whole device name. Both name criteria now ignore leading and trailing whitespace (see [BLE device matching](../../file-format/bluetooth-low-energy.md#ble-device-matching)).
- New attributes *lightSrc* and *darkSrc* for images, shown instead of *src* in light or dark mode (see [Images for light and dark mode](../../file-format/views/basics.md#images-for-light-and-dark-mode))
- New attribute *preferUncalibrated* for sensor inputs to start with the uncalibrated version of a sensor (see [Input module: sensor](../../file-format/input.md#input-module-sensor))
- The *accuracy* output of sensor inputs is no longer limited to the magnetometer: Android reports it for every sensor, iOS for the magnetometer and attitude, uncalibrated sensors report 0
