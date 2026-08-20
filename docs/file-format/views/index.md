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

The view elements are documented by category:

- [Graph](graph.md) — plots of all kinds, including bar charts, color maps and the data picker
- [User input](user-input.md) — [edit](user-input.md#view-element-edit), [button](user-input.md#view-element-button), [toggle](user-input.md#view-element-toggle), [slider](user-input.md#view-element-slider) and [dropdown](user-input.md#view-element-dropdown)
- [Camera and depth preview](preview.md) — [camera-gui](preview.md#view-element-camera-gui) and [depth-gui](preview.md#view-element-depth-gui)

The basic display elements — [info](#view-element-info), [separator](#view-element-separator), [value](#view-element-value) and [image](#view-element-image) — follow below.

## View-Element: info

The info element does not take any inputs or write to any outputs. It just displays a string defined as the *label* attribute.

{{spec:views/view/info}}

## View-Element: separator

The separator element does not take any inputs or write to any outputs. It just acts as a separator to give a visual aid in grouping other elements. It defaults to a very thin height of 0.1 (in units of text line heights) and a color matching the background color of the experiment screen. To achieve a margin between elements, you should set the height to 1; to create a narrow line, set the color (as a six-digit RGB hex value or a named color from the phyphox [Colors](../colors.md)) and leave the height at 0.1 - optionally padded by two other separator elements.

{{spec:views/view/separator}}

## View-Element: value

The value element displays a single value to the user. If the input buffer contains more than one value, the latest value will be displayed. The input is defined by a simple *input* tag within the value block and needs to be a data-container (see above).

Since file format version 1.5 (phyphox 1.0.7) you can define range mappings with the map-tag. The map tag includes a string which will replace the number and unit that would be displayed otherwise. phyphox will test all mappings in the order they are given and replace the output with the first mapping that applies. A mapping applies if the value to be shown falls in the range given by the attributes *min* and *max* (inclusive). *min* and *max* can be left out and default to negative and positive infinity. So, a map-tag without any attributes acts as a catch-all case.

Since file format version 1.19 (phyphox 1.2.0) the attribute gives even more options to change how the value is displayed, like for example showing GPS coordinates not only as a decimal value, but as degrees, minutes and seconds. Also, the positiveUnit and negativeUnit make it possible to change the unit depending on the value's sign. In the case of the GPS coordinate example, this allows showing N (for north) after positive latitudes and S (for south) after negative latitudes.

{{spec:views/view/value}}

{{spec:views/value/input}}

{{spec:views/value/map}}

## View-Element: image

Display an image with the file name RESOURCE. Typically, RESOURCE is a png or jpg image (these are natively supported on both iOS and Android; we hope for SVG support on iOS eventually) that is placed in the resource folder "res" in a zip file along with the experiment XML file. So, for example, instead of sharing experiment.phyphox you would share a zip file that contains experiment.phyphox together with a folder called "res" that contains an image "demo.jpg". The image element would then set RESOURCE to "demo.jpg" (not res/demo.jpg), i.e. **<image src="demo.jpg" />**.

{{spec:views/view/image}}

