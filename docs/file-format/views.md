# Views

The views block may hold one or more *view* blocks (note: singular), describing the different layout groups (views), from which the user may choose to view the experiment data.

At least one view block is required!

```xml
<phyphox version="1.0">
    ...
    <views>
        <view label="Pendulum">
            <value label="Frequency" unit="Hz">
                <input>frequencyBuffer</input>
            </value>
            <edit label="Length" unit="cm" factor="100" signed="false" default="50">
                <output>lengthBuffer</output>
            </edit>
            <info label="Example with user-input" />
        </view>
        <view label="Raw data">
            <graph label="Sensor data x" labelX="Time (s)" labelY="Amplitude">
                <input axis="x">timeBuffer</input>
                <input axis="y">sensorBuffer</input>
            </graph>
        </view>
    </views>
    ...
</phyphox>
```

## Block: view

Each view-block groups display elements to present data to the user. The view block has a single attribute *label* displayed to the user to identify this view when the user switches views. The label should be short and concise.

{{spec:views/views/view}}

## View-Element: info

The info element does not take any inputs or write to any outputs. It just displays a string defined as the *label* attribute.

{{spec:views/view/info}}

## View-Element: separator

The separator element does not take any inputs or write to any outputs. It just acts as a separator to give a visual aid in grouping other elements. It defaults to a very thin height of 0.1 (in units of text line heights) and a color matching the background color of the experiment screen. To achieve a margin between elements, you should set the height to 1 or to create a narrow line, set the color (as six-digit RGB hex value or a named color from the phyphox [Colors](colors.md)) and leave the height at 0.1 - optionally padded b two other separator elements.

{{spec:views/view/separator}}

## View-Element: value

The value element displays a single value to the user. If the input buffer contains more than one value, the latest value will be displayed. The input is defined by a simple *input* tag within the value block and needs to be a data-container (see above).

Since file format version 1.5 (phyphox 1.0.7) you can define range mappings with the map-tag. The map tag includes a string which will replace the number and unit that would be displayed otherwise. phyphox will test all mappings in the order they are given and replace the output with the first mapping that applies. A mapping applies if the value to be shown falls in the range given by the attributes *min* and *max* (inclusive). *min* and *max* can be left out and default to negative and positive infinity. So, a map-tag without any attributes acts as a catch-all case.

Since file format version 1.19 (phyphox 1.2.0) the attribute gives even more options to change how the value is displayed, like for example showing GPS coordinates not only as decimal value, but as degrees, minutes and seconds. Also the positiveUnit and negativeUnit allow to change the unit depending on the value's sign. In case of the GPS coordinate example, this allows to use N (for north) on positive latitude and S (for south) on negative latitudes behind the value.

{{spec:views/view/value}}

{{spec:views/value/input}}

{{spec:views/value/map}}

## View-Element: graph

The graph element will show a plot of the YBUFFER data against the XBUFFER data. The input buffers are defined by *input* tags within the value block and need to be a data-containers (see above). The input tags are linked to the axes with an additional *axis* attribute to the input tag, which may be *x* or *y*. See below for additional option for other graph types.

The resulting graph can be made up of lines (default) or dots (set attribute *style* to *dots*). (see attribute descriptions below)

The attributes *partialUpdate* is used for performance optimization. *PartialUpdate* should be set to true when the buffer is never changed entirely, but new data is just appended with increasing x values. *PartialUpdate* will then allow that only this data is transferred in the web-interface to save bandwidth.

{{spec:views/view/graph}}

{{spec:views/graph/input}}

### Data picker

**Available since phyphox file format 1.20 (phyphox 1.2.1))**

The graph can always be maximized by tapping it, to reveal additional tools like zooming and a data picker. The data picker can be repurposed to allow users to pick and map data to measured data points. This can for example be used to pick a starting point for an automated data analysis or to match points to reference values for a calibration process. You can define how many x, y and z values (in case of a color map plot) the user can pick, label the purpose of each pick and map it to data containers. Optionally, you can also request a value input from the user to map data points to calibration values. Finally, you can also rename the "pick data" button to reflect the use case for the data picker (see "pickLabel" attribute for the graph above.

The data picker is configured by adding outputs that are linked to the target data containers. Here is the most basic example, allowing the user to pick a single x value:

```xml
<graph label="Graph title"  pickLabel="Pick X" ...>
  <input axis="x">datax</input>
  <input axis="y">datay</input>
  <output axis="x" label="Offset X">picked</output>
</graph>
```

This example renames the pick mode to "Pick X" and if the user picks a data point, they will see an additional button "Offset X" as defined by the label-attribute of the output. If the user presses that button, the data-container "picked" will receive the x value of the selected data point.

In addition to allowing picking a point, the user can be allowed to map a value to the point:

```xml
<graph label="Graph title"  pickLabel="Pick X" ...>
  <input axis="x">datax</input>
  <input axis="y">datay</input>
  <output axis="x" label="Offset X">picked</output>
  <output axis="xcal" label="Enter a value to assign to your selected point">assigned</output>
</graph>
```

This example is identical to the previous one, except for having a second output that is assigned to the axis "xcal". This is used together with the axis="x" output and changes the behavior such that when the user presses the "Offset X" button, they will be prompted to enter a value. The label of the xcal output is shown as a prompt and when the user confirms their input, the data-container "picked" receives the x value of the selected point and "assigned" receives the entered value.

You can define an arbitrary number of outputs, assigning them to the axes "x", "y" or "z". Each will show up as a button to the user with the defined "label" of the output. Also, for each axis an additional "xcal", "ycal" or "zcal" can be defined, which will affect the previously defined "x", "y" or "z" output. The following example shows a configuration that allows the user to assign two x values for a spectrum calibration:

```xml
<graph label="Graph title"  pickLabel="Calibrate" ...>
  <input axis="x">datax</input>
  <input axis="y">datay</input>
  <output axis="x" label="Calibration point 1">cal_x1</output>
  <output axis="xcal" label="Assigned wavelength in nm">cal_lambda1</output>
  <output axis="x" label="Calibration point 2">cal_x2</output>
  <output axis="xcal" label="Assigned wavelength in nm">cal_lambda2</output>
</graph>
```

A formula node can then be used to calculate a linear calibration from these two points and generate a new x data set to show a calibrated version in another graph.

{{spec:views/graph/output}}

### Other graph types

**Available since phyphox file format 1.7 (phyphox 1.1.0))**

**Bar charts**

Since file format 1.7, you can also use bar charts by setting style to "hbars" or "vbars" for horizontal or vertical bars, respectively. For bar charts, you also define x and y values as you do for line charts, but the x value represents the left edge of a bar while y represents its height (for horizontal bars, y defines the bottom and x the width). Each bar ends where the next one begins and the last height will not be drawn as it only marks the end of the previous bar. Therefore, to draw 4 bars, you need to provide 5 value pairs.

For bar charts, the line width describes the gap between bars. A line width of 1 means that there is no gap, while a line width of 0.5 means that the bars only occupy 50% of the available width (they will be centered in this space).

**Color map charts**

File format 1.7 also introduces color map charts (also known as false color plots). These do not plot y values as a function of x values, but z values as a function of x and y. z is encoded as a color and the result is a map of different colors.

So, you need to provide three datasets, "x", "y" and "z". This is done similar to the traditional 2D plots:

```xml
<graph label="Fourier Transform" logZ="true" labelX="Frequency" unitX="Hz" labelY="Time" unitY="s" labelZ="FFT Mag" unitZ="a.u." aspectRatio="1" style="map" mapWidth="256" partialUpdate="true">
  <input axis="x">fmap</input>
  <input axis="y">tmap</input>
  <input axis="z">fftmap</input>
</graph>
```

The example shows the color map plot of the "Audio Spectrum" experiment. "fmap" contributes the frequencies for the x axis, "tmap" the timestamps for the y axis and "fftmap" the amplitudes that define the colors. Note that all three buffers need to provide the same number of values and that their indices need to match. There is no requirement that each value of each row needs to have exactly the same value, so the value has to be provide for every single data point. However, you cannot just provide arbitrarily distributed data point.

The color map creates a lattice from the provided points, which is then colored. For this, an additional paramtere "mapWidth" is set for the graph-Tag, which defines how many data points form a row. The datapoints within this row may be at slightly varied locations which will be displayed correctly (although the remote interface will not show their location correctly), but very large deviations can lead to a distorted image as connection to the next row won't match up. If you need to plot random data pairs, you might want to check our the [map analysis module](analysis/buffer-operations.md#map).

Also note, that due to the typical use of such color maps, the attribute "partialUpdate" (see above) now applies to the y axis, which needs to be monotonous instead of the x axis.

The color map plot introduces the following additional attributes:

mapColor\[n\]
:   n-th color in the color map
:   *optional*, if none are defined, phyphox uses a black-orange-white color gradient

The scale is read from `mapColor1` upward and ends at the first stop that is missing or does not name a valid color, so the number of stops is unlimited but a typo in one color ends the scale there.

{{inconsistency:views-map-color-unparseable}}

You can also define your own color palette. Phyphox uses a black-orange-white gradient by default, but introducing more colors can be very helpful to improve contrast. Colors a simply defined as a series of colors that are spread across the z range:

```xml
<graph label="Normalized history" labelX="distance" unitX="cm" labelY="time" unitY="s" labelZ="A" unitZ="a.u." aspectRatio="1" style="map" mapWidth="1200" mapColor1="000000" mapColor2="0000ff" mapColor3="00ffff" mapColor4="00ff00" mapColor5="ffff00" mapColor6="ff0000" mapColor7="ffffff" partialUpdate="true">
  <input axis="x">distance_map</input>
  <input axis="y">time_map</input>
  <input axis="z">weighted_map</input>
</graph>
```

This example shows the colorful palette of the sonar experiment.

**Multiple graphs**

Since file format 1.7 (phyphox 1.1.0) you can also combine multiple graph types (except for the color map). To do so, you can simply define more than one dataset for x and y:

```xml
<graph label="Acceleration" labelX="t" unitX="s" labelY="a" unitY="m/s²" partialUpdate="true">
  <input axis="x" color="green">acc_time</input>
  <input axis="y">accX</input>
  <input axis="x" color="blue">acc_time</input>
  <input axis="y">accY</input>
  <input axis="x" color="yellow">acc_time</input>
  <input axis="y">accZ</input>
  <input axis="x" color="white">acc_time</input>
  <input axis="y">acc</input>
</graph>
```

This example just creates four line charts for the "multi" page of the raw accelerometer experiment. You can define different colors (color attribute), line widths (lineWidth) and plot styles (style as line, dots, vbars or hbars) by applying these attributes to the input tag instead of the graph tag. Here, it does not matter if you define these for the x or y axis, but you should make sure that all inputs are assigned to an axis and that they are ordered correctly.

## View-Element: edit

The edit element displays an edit box, which takes data from the user and writes it to a buffer. The output is defined by a simple *output* tag within the value block and needs to be a data-container (see above).

{{spec:views/view/edit}}

{{spec:views/edit/output}}

## View-Element: button

The button element displays a simple button, which interacts with the buffers **outside** the analysis cycle. Whenever the user presses the button, the last value from each inputs (which may be value types or data-containers) is written to each output (the first input is written to the first output, the second to the second and so on). Note, that this does not happen at a certain point during analysis, but between analysis cycles, independent of when the user pushes the button.

Since version 1.4 (phyphox 1.0.6) you may define empty inputs (type="empty"), effectively allowing to clear a buffer when pressing the button.

Since version 1.8 (phyphox 1.1.3) in addition to defining in and out buffer (or usually as an alternative), you can set a trigger tag defining an id. This triggers matching processes with the same id like a [network connection](network-connections.md) (the only example at the time of this writing).

Since version 1.19 (phyphox 1.2.0) you can additionally define map tags that works similar to the map function of the value element. Each map tag defines a minimum and/or maximum value and an associated text. In contrast to the value element, the button uses an attribute *dynamicLabel* to define a data-container that is used with these map values. Phyphox sequentially goes through the map tags in the order they have been defined and the first one for which the value in the buffer given in *dynamicLabel* falls within min/max of the map tag, the text in the tag is used as a label for the button. If no map tag matches, then the normal label from the *label* tag is used.

{{spec:views/view/button}}

{{spec:views/button/input}}

{{spec:views/button/output}}

{{spec:views/button/trigger}}

{{spec:views/button/map}}

## View-Element: toggle

The toggle element displays a simple toggle (or a checkbox in the remote control interface), which allows the user to turn something off or on. The output buffer receives a 0 for off and a 1 for on. If the buffer is changed externally, a 0 is always interpreted as off while any other value is displayed as on.

{{spec:views/view/toggle}}

{{spec:views/toggle/output}}

## View-Element: slider

This is a view element used to input values from a limited range determined by a minimum and maximum value as well as a step size. The current value is also shown separately. With *type="range"* the slider can be used as a range slider with two handles, allowing the user to select a range by picking a lower and an upper value.

{{spec:views/view/slider}}

{{spec:views/slider/output}}

## View-Element: dropdown

The dropdown view element gives the user a list of options, each of which is associated with a value. The user simply taps the dropdown box, picks an option and the associated value is written to the output buffer.

{{spec:views/view/dropdown}}

{{spec:views/dropdown/output}}

{{spec:views/dropdown/map}}

## View-Element: camera-gui

This is a preview and control for a camera input, showing a preview of the camera and allowing for selecting an acquisition area and several camera settings. Note that this only makes sense if you also use a camera input in the configuration.

*exposure_adjustment_level* and *show_controls* determine which controls are available to the user and when they are shown. In the default experiments of phyphox you typically see *exposure_adjustment_level="3"* and *show_controls="full_view_only"*.

*grayscale* and the *markOverexposure* and *markUnderexposure* are modifiers that influence the look of the image to make it easier to use for some measurements.

{{spec:views/view/camera-gui}}

## View-Element: depth-gui

This is a preview and control for a depth input, showing a preview of the camera and allowing for selecting an acquisition area, an aggregation method and switching cameras. At the moment, you can only set the label. Note that this only makes sense if you also use a depth input in the configuration.

{{spec:views/view/depth-gui}}

## View-Element: image

Display an image with the file name RESOURCE. Typically, RESOURCE is a png or jpg image (these are natively supported on both iOS and Android, hoping for SVG support on iOS eventually) that is placed in the resource folder "res" in a zip file along with the experiment XML file. So, for example, instead of sharing experiment.phyphox you would share a zip file that contains experiment.phyphox together with a folder called "res" that contains an image "demo.jpg". The image element would then set RESOURCE to "demo.jpg" (not res/demo.jpg), i.e. **<image src="demo.jpg" />**.

{{spec:views/view/image}}
