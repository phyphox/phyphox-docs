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

label
:   The name identifying this view. Will be translated if a matching translation string is defined.
:   *required*

## View-Element: info

```xml
<info color="COLOR" label="INFOTEXT" bold="BOOLEAN" italic="BOOLEAN" align="STRING" size="NUMERIC" />
```

The info element does not take any inputs or write to any outputs. It just displays a string defined as the *label* attribute.

label
:   The text to be displayed to the user
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

color
:   The text color as six-digit RGB hex value or a named choice from the phyphox [Colors](colors.md)
:   *optional*, default: white, **Available since phyphox file format 1.7 (phyphox 1.1.0)**

bold
:   If set to true, the text will be displayed using a bold font. (We cannot guarantee, that the combination of bold and italic is available on every device.) **Available since phyphox file format 1.8 (phyphox 1.1.3)**

italic
:   If set to true, the text will be displayed using an italic font. (We cannot guarantee, that the combination of bold and italic is available on every device.) **Available since phyphox file format 1.8 (phyphox 1.1.3)**

align
:   Can be set to left (default), center or right. The alignment of the text. (Note, that phyphox does not yet support RTL languages, but this attribute is designed to be reverse in such cases.) **Available since phyphox file format 1.8 (phyphox 1.1.3)**

size
:   Sets the font size of the info element as a factor to the default size. Hence, the default is 1. **Available since phyphox file format 1.8 (phyphox 1.1.3)**

## View-Element: separator

```xml
<separator color="orange" height="0.1" />
```

The separator element does not take any inputs or write to any outputs. It just acts as a separator to give a visual aid in grouping other elements. It defaults to a very thin height of 0.1 (in units of text line heights) and a color matching the background color of the experiment screen. To achieve a margin between elements, you should set the height to 1 or to create a narrow line, set the color (as six-digit RGB hex value or a named color from the phyphox [Colors](colors.md)) and leave the height at 0.1 - optionally padded b two other separator elements.

color
:   The color of the whole (rectangular) element as six-digit RGB hex value or a named choice from the phyphox [Colors](colors.md)
:   *optional*, default: background color

height
:   The height of the separator in text line heights
:   *optional*, default: 0.1

## View-Element: value

```xml
<value label="LABEL" size="FLOAT" precision="INTEGER" scientific="BOOLEAN" unit="UNIT" factor="FLOAT" format="STRING" color="COLOR">
    <input>BUFFER</input>
    <map min="DOUBLE" max="DOUBLE">STRING</map>
    <map>STRING</map>
</value>
```

The value element displays a single value to the user. If the input buffer contains more than one value, the latest value will be displayed. The input is defined by a simple *input* tag within the value block and needs to be a data-container (see above).

Since file format version 1.5 (phyphox 1.0.7) you can define range mappings with the map-tag. The map tag includes a string which will replace the number and unit that would be displayed otherwise. phyphox will test all mappings in the order they are given and replace the output with the first mapping that applies. A mapping applies if the value to be shown falls in the range given by the attributes *min* and *max* (inclusive). *min* and *max* can be left out and default to negative and positive infinity. So, a map-tag without any attributes acts as a catch-all case.

Since file format version 1.19 (phyphox 1.2.0) the attribute gives even more options to change how the value is displayed, like for example showing GPS coordinates not only as decimal value, but as degrees, minutes and seconds. Also the positiveUnit and negativeUnit allow to change the unit depending on the value's sign. In case of the GPS coordinate example, this allows to use N (for north) on positive latitude and S (for south) on negative latitudes behind the value.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

color
:   The text color as six-digit RGB hex value or a named choice from the phyphox [Colors](colors.md)
:   *optional*, default: white, **Available since phyphox file format 1.7 (phyphox 1.1.0)**

size
:   The size of the displayed value relative to the default font size. Label and unit will stay at their original size. **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: 1

precision
:   The number of digits after the decimal point.
:   *optional*, default: 2

scientific
:   If set to true, the value will be displayed in scientific notation (1.0e-3 instead of 0.001)
:   *optional*, default: false

unit
:   A unit to be displayed after the value
:   *optional*, default: no unit

positiveUnit
:   Replace the regular unit with this if the value is positive.
:   *optional*, default: no unit, **Available since phyphox file format 1.19 (phyphox 1.2.0)**

negativeUnit
:   Replace the regular unit with this if the value is negative.
:   *optional*, default: no unit, **Available since phyphox file format 1.19 (phyphox 1.2.0)**

factor
:   A factor to be applied to the value before displaying it. This is usually used for unit conversion. Example: The data is in meter, but should be displayed in cm. The factor would be 0.01
:   *optional*, default: 1.0

format
:   Choose alternative formats to show the value. Options are:

    float
    :   Show a simple decimal value (with significant digits, scientific notation etc. as defined by the other attributes)

    degree-minutes
    :   Split the decimal part of the value of and show it separately in minutes (part of 60). The output is formatted as degrees and minutes and the attribute *precision* affects the minutes part in this format. Example: 42.385 becomes 42° 23.1'

    degree-minutes-seconds
    :   Split the decimal part of the value of and show it separately in minutes (part of 60) and seconds (part of 3600). The output is formatted as degrees, minutes and seconds and the attribute *precision* affects the seconds part in this format. Example: 42.385 becomes 42° 23' 6"

    ascii
    :   Convert all values in the data-container to their ASCII character representation and show it as text. Non-integer values and those outside the range \[32,125\] will be skipped.
:   *optional*, default: float, **Available since phyphox file format 1.19 (phyphox 1.2.0)**

## View-Element: graph

```xml
<graph label="LABEL" aspectRatio="FLOAT" style="STYLE" partialUpdate="BOOLEAN" labelX="LABELX" labelY="LABELY" timeOnX="BOOLEAN" timeOnY="BOOLEAN" linearTime="BOOLEAN" systemTime="BOOLEAN" hideTimeMarkers="BOOLEAN" logX="BOOLEAN" logy="BOOLEAN" xPrecision="INTEGER" yPrecision="INTEGER" minX="0" maxX="0" minY="0" maxY="0" scaleMinX="auto" scaleMaxX="auto" scaleMinY="auto" scaleMaxY="auto" followX="false" lineWidth="1" color="orange" pickLabel="LABEL">
    <input axis="x">XBUFFER</input>
    <input axis="y">YBUFFER</input>
</graph>
```

The graph element will show a plot of the YBUFFER data against the XBUFFER data. The input buffers are defined by *input* tags within the value block and need to be a data-containers (see above). The input tags are linked to the axes with an additional *axis* attribute to the input tag, which may be *x* or *y*. See below for additional option for other graph types.

The resulting graph can be made up of lines (default) or dots (set attribute *style* to *dots*). (see attribute descriptions below)

The attributes *partialUpdate* is used for performance optimization. *PartialUpdate* should be set to true when the buffer is never changed entirely, but new data is just appended with increasing x values. *PartialUpdate* will then allow that only this data is transferred in the web-interface to save bandwidth.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

apectRatio
:   The ratio of the total width of this element to the total height of this element in the view. (Including labels and axes)
:   *optional*, default: 3

style
:   If set to *dots*, the graph will not connect the values with lines. See below for additional styles introduced with file format 1.7 (phyphox 1.1.0).
:   *optional*, default: display lines

partialUpdate
:   If set to true, this allows optimizations which only work if the data is appended with increasing x values. A typical example is sensor data: Only few new values are added and each data point has a greater timestamp than the previous one. In such cases this should be set to true as it allows the web interface to only transfer these new datapoints.
:   *optional*, default: false

labelX
:   The label of the x axis
:   *optional*, default: empty, but you should always label your axes... (Note that since file format 1.7 (phyphox 1.1.0) you should set the unit separately in the attribute unitX)

labelY
:   The label of the y axis
:   *optional*, default: empty, but you should always label your axes... (Note that since file format 1.7 (phyphox 1.1.0) you should set the unit separately in the attribute unitY)

unitX
:   The unit of the x axis
:   *optional*, default: empty, the units will be appended to the label, but are also used to give values of individual data points with correct units **Available since phyphox file format 1.7 (phyphox 1.1.0)**

unitY
:   The unit of the y axis
:   *optional*, default: empty, the units will be appended to the label, but are also used to give values of individual data points with correct units **Available since phyphox file format 1.7 (phyphox 1.1.0)**

unitYperX
:   An explicit unit for slopes, if not set, phyphox will use "unitY / unitX".
:   *optional*, default: not set, phyphox will fallback to generate this from x and y unit. **Available since phyphox file format 1.10 (phyphox 1.1.6)**

timeOnX
:   If set to true, the x data needs to be time data in seconds relative to the first start of the experiment. This allows to mark start/pause events and to switch to a system time scale (i.e. absolute date and time) on the x axis. **Available since phyphox file format 1.12 (phyphox 1.1.8)**
:   *optional*, default: false

timeOnY
:   If set to true, the y data needs to be time data in seconds relative to the first start of the experiment. This allows to mark start/pause events and to switch to a system time scale (i.e. absolute date and time) on the y axis. **Available since phyphox file format 1.12 (phyphox 1.1.8)**
:   *optional*, default: false

linearTime
:   If set to true, the time on each axis is interpreted as "linear" time, which is identical to "experiment" time with the difference that the time stamp increases even when phyphox is paused. This especially allows to plot data from external sources that have their own internal clock. In these cases you can use the timer module to get a reference time to shift data from an external clock appropriately. If the graph is shown with system time on the axis, all data is shown, but if the axis is set to experiment time, the data points with linear time corresponding to times during which phyphox was paused will be hidden. If linearTime is set to false, experiment time (the default) is expected. **Available since phyphox file format 1.12 (phyphox 1.1.8)**
:   *optional*, default: false

systemTime
:   If set to true, time axes will start as a system time scale (they can always be switched by the user). **Available since phyphox file format 1.12 (phyphox 1.1.8)**
:   *optional*, default: false

hideTimeMarkers
:   If set to true, no red markers are shown to indicate times at which the experiment was stopped. **Available since phyphox file format 1.14 (phyphox 1.1.10)**
:   *optional*, default: false (= markers are visible)

logX
:   If set to true, the x axis will be on a logarithmic scale
:   *optional*, default: false

logY
:   If set to true, the y axis will be on a logarithmic scale
:   *optional*, default: false

xPrecision
:   The number of significant digits on the x axis. **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: 3

yPrecision
:   The number of significant digits on the y axis. **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: 3

suppressScientificNotation
:   If set to true, phyphox will never use scientific notation like 2e-5 instead of 0.00002. This also changes the behavior of xPrecision and yPrecision to refer to decimal digits instead of significant digits. Please make sure that this works well with your measured data as forcing non-scientific notation can lead to extreme numbers in some edge cases. **Available since phyphox file format 1.19 (phyphox 1.2.0)**
:   *optional*, default: false

minX
:   Lowest value on the x axis. Only applied if scaleMinX = fixed
:   *optional*, default: 0

maxX
:   Highest value on the x axis. Only applied if scaleMaxX = fixed
:   *optional*, default: 0

minY
:   Lowest value on the y axis. Only applied if scaleMinY = fixed
:   *optional*, default: 0

maxY
:   Highest value on the y axis. Only applied if scaleMaxY = fixed
:   *optional*, default: 0

scaleMinX
:   Method to scale the minimum of the x axis. auto always scales this value to the minimum of the data set. extend scales to the historic minimum. fixed sets the minimum to minX.
:   *optional*, default: auto

scaleMaxX
:   Method to scale the maximum of the x axis. auto always scales this value to the maximum of the data set. extend scales to the historic maximum. fixed sets the minimum to maxX.
:   *optional*, default: auto

scaleMinY
:   Method to scale the minimum of the y axis. auto always scales this value to the minimum of the data set. extend scales to the historic minimum. fixed sets the minimum to minY.
:   *optional*, default: auto

scaleMaxY
:   Method to scale the maximum of the y axis. auto always scales this value to the maximum of the data set. extend scales to the historic maximum. fixed sets the minimum to maxY.
:   *optional*, default: auto

followX
:   If set to true, the graph follows new data with a fixed x axis scale. This is the same as selecting "follow new" data from the zoom dialog. The width of the x axis has to be defined by setting minX and maxX. Setting followX overrides scaleMinX and scaleMaxX and also forces partialUpdate to true. **Available since phyphox file format 1.15 (phyphox 1.1.11)**
:   *optional*, default: false

lineWidth
:   Width of the graph line relative to the default width
:   *optional*, default: 1

color
:   Color of the graph line as six-digit RGB hex value or a named choice from the phyphox [Colors](colors.md)
:   *optional*, default: phyphox orange

pickLabel
:   Rename the "Pick data" button to show to the user the purpose of the data picker (see data picker feature below). **Available since phyphox file format 1.20 (phyphox 1.2.1)**
:   *optional*, default: Do not change picker label

history
:   **Deprecation warning**: This feature has been marked as depricated and will be removed soon. Please implement it in phyphox analysis logic by using additional data-containers and copying the shown graph into these on each update. This has several advantages like being able to export the history data and better control over its style. Original description: The number of graphs to be shown. 1 means, that the current data is shown. n means, that n graphs are shown, with n-1 graphs containing the data from the previous update. This attribute only makes sense, when the whole graph is replaced on each analysis cycle and can be used to compare the previous n results within a single graph. **Deprecated since phyphox file format 1.15 (phyphox 1.1.12))**
:   *optional*, default: 1

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

labelZ
:   The label of the z axis
:   *optional*, default: empty, but you should always label your axes...

logZ
:   If set to true, the x axis will be on a logarithmic scale
:   *optional*, default: false

zPrecision
:   The number of significant digits on the z axis.
:   *optional*, default: 3

minZ
:   Lowest value on the z axis. Only applied if scaleMinZ = fixed
:   *optional*, default: 0

maxZ
:   Highest value on the z axis. Only applied if scaleMaxZ = fixed
:   *optional*, default: 0

scaleMinZ
:   Method to scale the minimum of the z axis. auto always scales this value to the minimum of the data set. extend scales to the historic minimum. fixed sets the minimum to minZ.
:   *optional*, default: auto

scaleMaxZ
:   Method to scale the maximum of the z axis. auto always scales this value to the maximum of the data set. extend scales to the historic maximum. fixed sets the minimum to maxZ.
:   *optional*, default: auto

mapWidth
:   Number of data points per line.
:   *optional*, but a color map chart won't work without this.

mapColor\[n\]
:   n-th color in the color map
:   *optional*, if none are defined, phyphox uses a black-orange-white color gradient

showColorScale
:   Show or hide the color scale above the color plot
:   *optional*, default: true (**Available since phyphox file format 1.19 (phyphox 1.2.0)**)

interpolateMapColors
:   Interpolate area between data points. If disabled, phyphox expects the datapoints to be aligned on an even spaced rectangular grid and will show each datapoint as a rectangular "pixel" centered on the data point's x/y coordinate. Default behavior is to assign colors to the data point coordinates and interpolate colors inbetween.
:   *optional*, default: true (**Available since phyphox file format 1.20 (phyphox 1.2.1)**)

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

```xml
<edit label="LABEL" signed="BOOLEAN" decimal="BOOLEAN" min="FLOAT" max="FLOAT" unit="UNIT" factor="FLOAT" default="FLOAT">
    <output>BUFFER</output>
</edit>
```

The edit element displays an edit box, which takes data from the user and writes it to a buffer. The output is defined by a simple *output* tag within the value block and needs to be a data-container (see above).

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

signed
:   If set to *false* the user may not enter negative numbers.
:   *optional*, default: true

decimal
:   If set to *false* the user may not enter decimal (i.e. non-integer) numbers.
:   *optional*, default: true

min
:   The minimum value allowed. Disable by not setting this attribute. **Available from phyphox file format 1.1 (phyphox 1.0.2)**.
:   *optional*, default: disabled

max
:   The maximum value allowed. Disable by not setting this attribute. **Available from phyphox file format 1.1 (phyphox 1.0.2)**.
:   *optional*, default: disabled

unit
:   A unit to be displayed after the value
:   *optional*, default: no unit

factor
:   A factor to be applied to the value before displaying it. This is usually used for unit conversion. Example: The data is in meter, but should be displayed in cm. The factor would be 0.01
:   *optional*, default: 1.0

default
:   The default value of the edit box. The experiment will start with this value.
:   *optional*, default: 0.0

## View-Element: button

**Available since phyphox file format 1.3 (phyphox 1.0.4)**

```xml
<button label="LABEL" dynamicLabel="BUFFER">
    <input>BUFFER1</input>
    <output>BUFFER1</output>
    <input type="value">42</input>
    <output>BUFFER2</output>
    <input type="empty" />
    <output>BUFFER3</output>
    <trigger>ID</trigger>
    ...
    <map min="FLOAT" max="FLOAT">LABEL 1</map>
    <map min="FLOAT" max="FLOAT">LABEL 2</map>
    ...
</button>
```

The button element displays a simple button, which interacts with the buffers **outside** the analysis cycle. Whenever the user presses the button, the last value from each inputs (which may be value types or data-containers) is written to each output (the first input is written to the first output, the second to the second and so on). Note, that this does not happen at a certain point during analysis, but between analysis cycles, independent of when the user pushes the button.

Since version 1.4 (phyphox 1.0.6) you may define empty inputs (type="empty"), effectively allowing to clear a buffer when pressing the button.

Since version 1.8 (phyphox 1.1.3) in addition to defining in and out buffer (or usually as an alternative), you can set a trigger tag defining an id. This triggers matching processes with the same id like a [network connection](network-connections.md) (the only example at the time of this writing).

Since version 1.19 (phyphox 1.2.0) you can additionally define map tags that works similar to the map function of the value element. Each map tag defines a minimum and/or maximum value and an associated text. In contrast to the value element, the button uses an attribute *dynamicLabel* to define a data-container that is used with these map values. Phyphox sequentially goes through the map tags in the order they have been defined and the first one for which the value in the buffer given in *dynamicLabel* falls within min/max of the map tag, the text in the tag is used as a label for the button. If no map tag matches, then the normal label from the *label* tag is used.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

dynamicLabel
:   A buffer (data-container) that controls the label of the button. The last value in this buffer is compared to the map tags in the button element and the first matching map tag determines the button's label.
:   *optional*, default: not set / show only the regular label

## View-Element: toggle

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<toggle label="LABEL" default="FLOAT">
    <output>BUFFER</output>
</toggle>
```

The toggle element displays a simple toggle (or a checkbox in the remote control interface), which allows the user to turn something off or on. The output buffer receives a 0 for off and a 1 for on. If the buffer is changed externally, a 0 is always interpreted as off while any other value is displayed as on.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

default
:   The value with which the associated buffer should start.
:   *optional*, default: do not set a starting value

## View-Element: slider

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<slider label="LABEL" type="STRING" default="FLOAT" minValue="FLOAT" maxValue="FLOAT" stepSize="FLOAT" precision="INTEGER" showValue="BOOL">
    <output>BUFFER_NORMAL</output>
    <output value="lowerValue">BUFFER_RANGE_LOWER</output>
    <output value="upperValue">BUFFER_RANGE_UPPER</output>
</slider>
```

This is a view element used to input values from a limited range determined by a minimum and maximum value as well as a step size. The current value is also shown separately. With *type="range"* the slider can be used as a range slider with two handles, allowing the user to select a range by picking a lower and an upper value.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

type
:   Can either be "normal" or "range". Normal is a slider representing a single value, while "range" is a range slider with two handles that allow picking a lower and an upper value.
:   *optional*, default: normal

default
:   The value with which the associated buffer should start. (Does not work in range slider mode. Use the init property of the data containers instead.)
:   *optional*, default: do not set a starting value

minValue
:   Value for a handle at the lower end of the slider.
:   *optional*, default: 0

maxValue
:   Value for a handle at the upper end of the slider.
:   *optional*, default: 1

stepSize
:   Determines the minimum distance between to values that can be selected with the slider. This is always relative to minValue, so a stepSize of 0.2 and a minValue of 0.1 will force the user to pick 0.1, 0.3, 0.5, etc.
:   *optional*, default: 1

precision
:   The number of decimal places shown in the field with the current vlaue
:   *optional*, default: 2

showValue
:   Show a title and the current value above the slider. If turned off, the title is also hidden, making the slider very thin and compact.
:   *optional*, default: true

## View-Element: dropdown

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<dropdown label="LABEL" default="FLOAT">
    <output>BUFFER</output>
    <map value="FLOAT">OPTION 1</map>
    <map value="FLOAT">OPTION 2</map>
                         ...
    <map value="FLOAT">OPTION 3</map>
</dropdown>
```

The dropdown view element gives the user a list of options, each of which is associated with a value. The user simply taps the dropdown box, picks an option and the associated value is written to the output buffer.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

default
:   The value with which the associated buffer should start.
:   *optional*, default: do not set a starting value

## View-Element: camera-gui

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<camera-gui label="LABEL" exposure_adjustment_level="INTEGER" showControls="STRING" grayscale="BOOLEAN" markOverexposure="COLOR" markUnderexposure="COLOR"/>
```

This is a preview and control for a camera input, showing a preview of the camera and allowing for selecting an acquisition area and several camera settings. Note that this only makes sense if you also use a camera input in the configuration.

*exposure_adjustment_level* and *showControls* determine which controls are available to the user and when they are shown. In the default experiments of phyphox you typically see *exposure_adjustment_level="3"* and *showControls="full_view_only"*.

*grayscale* and the *markOverexposure* and *markUnderexposure* are modifiers that influence the look of the image to make it easier to use for some measurements.

exposure_adjustment_level
:   This determines which controls are available to the user in three different levels of how much control over the exposure is possible: Level 1 only allows for changing the camera and zoom, but no control over exposure settings. Level 2 is a simplified exposure control, allowing the same as level 1 and adding a toggle to turn auto exposure on or off as well as a simple exposure value control, adjusting for a slight over or underexposure from the auto exposure result. Level 3 finally offers all controls, replacing the exposure value control from level 2 with shutter speed (exposure time), ISO and aperture and also showing the white balance control.
:   *optional*, default: 1

showControls
:   This determines when controls are shown. This can assume the following values:

    never
    :   Controls are never shown and this is only used as a preview (with the option to select the measurement area).

    full_view_only
    :   Controls are only shown after the preview has been tapped and maximized.

    always
    :   Controls are available even when only a small preview is shown
:   *optional*, default: full_view_only

grayscale
:   Show a grayscale image instead of colors
:   *optional*, default: false

markOverexposure
:   Overexposed parts of the image are replaced by the given color
:   *optional*, default: not used

markUnderxposure
:   Underexposed parts of the image are replaced by the given color
:   *optional*, default: not used

## View-Element: depth-gui

**Available since phyphox file format 1.14 (phyphox 1.1.10)**

```xml
<depth-gui label="LABEL" />
```

This is a preview and control for a depth input, showing a preview of the camera and allowing for selecting an acquisition area, an aggregation method and switching cameras. At the moment, you can only set the label. Note that this only makes sense if you also use a depth input in the configuration.

## View-Element: image

**Available since phyphox file format 1.18 (phyphox 1.1.16)**

```xml
    <image src="RESOURCE" scale="1.0" lightFilter="none" darkFilter="none" />
```

Display an image with the file name RESOURCE. Typically, RESOURCE is a png or jpg image (these are natively supported on both iOS and Android, hoping for SVG support on iOS eventually) that is placed in the resource folder "res" in a zip file along with the experiment XML file. So, for example, instead of sharing experiment.phyphox you would share a zip file that contains experiment.phyphox together with a folder called "res" that contains an image "demo.jpg". The image element would then set RESOURCE to "demo.jpg" (not res/demo.jpg), i.e. **<image src="demo.jpg" />**.

src
:   The file name of the image that should be displayed. (Relative to the resource folder.)
:   *required*

scale
:   Scales the size of the image. By default (scale="1.0") the image is shown in full width. The factor is relative to this, so scale="0.5" sets it to half the width of the view.
:   *optional*, default: 1.0

lightFilter
:   A filter that should be applied to the image if the interface of phyphox is in light mode. Currently, there are two options: **none** leaves the image as is. **invert** inverts the colors of the image.
:   *optional*, default: none

darkFilter
:   A filter that should be applied to the image if the interface of phyphox is in dark mode. Currently, there are two options: **none** leaves the image as is. **invert** inverts the colors of the image.
:   *optional*, default: none
