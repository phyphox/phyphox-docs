# Graph

The view elements on this page additionally accept the [attributes common to all view elements](index.md#common-attributes).

The graph element will show a plot of the YBUFFER data against the XBUFFER data. The input buffers are defined by *input* tags within the value block and need to be data-containers (see above). The input tags are linked to the axes with an additional *axis* attribute to the input tag, which may be *x* or *y*. See below for additional options for other graph types.

The attribute *partialUpdate* is used for performance optimization. *PartialUpdate* should be set to true when the buffer is never changed entirely, but new data is just appended with increasing x values. *PartialUpdate* then allows only this new data to be transferred to the web interface to save bandwidth.

{{spec:views/view/graph}}

{{spec:views/graph/input}}

## Data picker

The graph can always be maximized by tapping it to reveal additional tools like zooming and a data picker. The data picker can be repurposed to allow users to pick and map data to measured data points. This can for example be used to pick a starting point for an automated data analysis or to match points to reference values for a calibration process. You can define how many x, y and z values (in the case of a color map plot) the user can pick, label the purpose of each pick and map it to data containers. Optionally, you can also request a value input from the user to map data points to calibration values. Finally, you can also rename the "pick data" button to reflect the use case for the data picker (see the "pickLabel" attribute of the graph above).

The data picker is configured by adding outputs that are linked to the target data containers. Here is the most basic example, allowing the user to pick a single x value:

```xml
<graph label="Graph title"  pickLabel="Pick X" ...>
  <input axis="x">datax</input>
  <input axis="y">datay</input>
  <output axis="x" label="Offset X">picked</output>
</graph>
```

This example renames the pick mode to "Pick X", and if the user picks a data point, they will see an additional button "Offset X" as defined by the label-attribute of the output. If the user presses that button, the data-container "picked" will receive the x value of the selected data point.

In addition to picking a point, the user can be allowed to map a value to the point:

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

## Other graph types

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

### Bar charts

Since file format 1.7, you can also use bar charts by setting style to "hbars" or "vbars" for horizontal or vertical bars, respectively. For bar charts, you also define x and y values as you do for line charts, but the x value represents the left edge of a bar while y represents its height (for horizontal bars, y defines the bottom and x the width). Each bar ends where the next one begins and the last height will not be drawn as it only marks the end of the previous bar. Therefore, to draw 4 bars, you need to provide 5 value pairs.

For bar charts, the line width describes the gap between bars. A line width of 1 means that there is no gap, while a line width of 0.5 means that the bars only occupy 50% of the available width (they will be centered in this space).

### Color map charts

File format 1.7 also introduces color map charts (also known as false color plots). These do not plot y values as a function of x values, but z values as a function of x and y. z is encoded as a color and the result is a map of different colors.

So, you need to provide three datasets, "x", "y" and "z". This is done similarly to the traditional 2D plots:

```xml
<graph label="Fourier Transform" logZ="true" labelX="Frequency" unitX="Hz" labelY="Time" unitY="s" labelZ="FFT Mag" unitZ="a.u." aspectRatio="1" style="map" mapWidth="256" partialUpdate="true">
  <input axis="x">fmap</input>
  <input axis="y">tmap</input>
  <input axis="z">fftmap</input>
</graph>
```

The example shows the color map plot of the "Audio Spectrum" experiment. "fmap" contributes the frequencies for the x axis, "tmap" the timestamps for the y axis and "fftmap" the amplitudes that define the colors. Note that all three buffers need to provide the same number of values and that their indices need to match. There is no requirement that each value of each row has exactly the same value, so the value has to be provided for every single data point. However, you cannot just provide arbitrarily distributed data points.

The color map creates a lattice from the provided points, which is then colored. For this, an additional parameter "mapWidth" is set for the graph-Tag, which defines how many data points form a row. The datapoints within this row may be at slightly varied locations, which will be displayed correctly (although the remote interface will not show their location correctly), but very large deviations can lead to a distorted image as the connection to the next row won't match up. If you need to plot random data pairs, you might want to check out the [map analysis module](../analysis/buffer-operations.md#map).

Also note that, due to the typical use of such color maps, the attribute "partialUpdate" (see above) now applies to the y axis, which needs to be monotonic, instead of the x axis.

The colors of the map are set with the *mapColor[N]* attributes (mapColor1, mapColor2, ..., see the attribute list above). A stop that is present but does not name a valid color (a named phyphox color or a six-digit hex RGB value, optionally prefixed with `#`) is an error and the experiment will not load — the same strictness that applies to every color attribute in the format.

You can also define your own color palette. Phyphox uses a black-orange-white gradient by default, but introducing more colors can be very helpful to improve contrast. Colors are simply defined as a series of colors that are spread across the z range:

```xml
<graph label="Normalized history" labelX="distance" unitX="cm" labelY="time" unitY="s" labelZ="A" unitZ="a.u." aspectRatio="1" style="map" mapWidth="1200" mapColor1="000000" mapColor2="0000ff" mapColor3="00ffff" mapColor4="00ff00" mapColor5="ffff00" mapColor6="ff0000" mapColor7="ffffff" partialUpdate="true">
  <input axis="x">distance_map</input>
  <input axis="y">time_map</input>
  <input axis="z">weighted_map</input>
</graph>
```

This example shows the colorful palette of the sonar experiment.

### Multiple graphs

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

This example just creates four line charts for the "multi" page of the raw accelerometer experiment.

How the input tags form datasets: each pair of an *x* input directly followed by its *y* input defines one dataset (one curve). Write the pairs in exactly this interleaved order — x, then y, dataset by dataset — even when several datasets share the same x data container: repeat the x input before each y, as the example above does with `acc_time`. A dataset may also consist of a y input alone, which is plotted against the element index. Assign every input to an axis.

{{inconsistency:graph-multiset-input-order}}

{{inconsistency:graph-multiset-omitted-x}}

{{inconsistency:graph-input-axis-required}}

Per dataset you can override the graph-level *color*, *lineWidth* and *style* (as lines, dots, vbars or hbars) by applying these attributes to one of the dataset's input tags — it does not matter whether to the x or the y input; if both carry an attribute, the later tag wins. Datasets without an explicit color cycle through six default colors (orange, green, blue, yellow, magenta, red, then repeating), while a *color* attribute on the graph tag itself colors every dataset the same.

