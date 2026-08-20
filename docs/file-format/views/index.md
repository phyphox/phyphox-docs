# Views

The views block may hold one or more *view* blocks (note: singular), describing the different layout groups (views), from which the user may choose to view the experiment data.

At least one view block is required!

```xml
<phyphox version="...">
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

## Common attributes

Every view element accepts two attributes beyond the ones listed in its own section:

{{spec:views/phyphox/views|common}}

## View elements

The view elements are documented by category:

- [Basic elements](basics.md) — [info](basics.md#view-element-info), [separator](basics.md#view-element-separator), [value](basics.md#view-element-value) and [image](basics.md#view-element-image)
- [Graph](graph.md) — plots of all kinds, including bar charts, color maps and the data picker
- [User input](user-input.md) — [edit](user-input.md#view-element-edit), [button](user-input.md#view-element-button), [toggle](user-input.md#view-element-toggle), [slider](user-input.md#view-element-slider) and [dropdown](user-input.md#view-element-dropdown)
- [Camera and depth preview](preview.md) — [camera-gui](preview.md#view-element-camera-gui) and [depth-gui](preview.md#view-element-depth-gui)
