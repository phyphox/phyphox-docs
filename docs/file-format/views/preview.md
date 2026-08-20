# Camera and depth preview

The view elements on this page additionally accept the [attributes common to all view elements](index.md#common-attributes).

## View-Element: camera-gui

This is a preview and control for a camera input, showing a preview of the camera and allowing for selecting an acquisition area and several camera settings. Note that this only makes sense if you also use a camera input in the configuration.

*exposure_adjustment_level* and *show_controls* determine which controls are available to the user and when they are shown. In the default experiments of phyphox you typically see *exposure_adjustment_level="3"* and *show_controls="full_view_only"*.

*grayscale*, *markOverexposure* and *markUnderexposure* are modifiers that influence the look of the image to make it easier to use for some measurements.

{{spec:views/view/camera-gui}}

## View-Element: depth-gui

This is a preview and control for a depth input, showing a preview of the camera and allowing for selecting an acquisition area and an aggregation method, and for switching cameras. At the moment, you can only set the label. Note that this only makes sense if you also use a depth input in the configuration.

{{spec:views/view/depth-gui}}

