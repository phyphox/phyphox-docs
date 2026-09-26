# User input

The view elements on this page additionally accept the [attributes common to all view elements](index.md#common-attributes).

## View-Element: edit

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![Two edit elements for a mass in grams and a length in centimetres](../../assets/screenshots/views/edit-light.png#only-light){ .view-shot .on-glb }
![Two edit elements for a mass in grams and a length in centimetres](../../assets/screenshots/views/edit-dark.png#only-dark){ .view-shot .on-glb }
</figure>

The edit element displays an edit box, which takes data from the user and writes it to a buffer. The output is defined by a simple *output* tag within the value block and needs to be a data-container.

{{spec:views/view/edit}}

{{spec:views/edit/output}}

## View-Element: button

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![An info element explaining a button labelled Clear positions](../../assets/screenshots/views/button-light.png#only-light){ .view-shot .on-glb }
![An info element explaining a button labelled Clear positions](../../assets/screenshots/views/button-dark.png#only-dark){ .view-shot .on-glb }
</figure>

The button element displays a simple button, which interacts with the buffers **outside** the analysis cycle. Whenever the user presses the button, the last value from each input (which may be value types or data-containers) is written to each output (the first input is written to the first output, the second to the second and so on). Note that this does not happen at a certain point during analysis, but between analysis cycles, independent of when the user pushes the button.

Since version 1.4 (phyphox 1.0.6) you may define empty inputs (type="empty"), effectively making it possible to clear a buffer when pressing the button. The buffer is emptied, not reset to its *init* values; only the user's clear-data action restores those.

Since version 1.8 (phyphox 1.1.3), in addition to defining input and output buffers (or, usually, as an alternative), you can set a trigger tag defining an id. This triggers matching processes with the same id, such as a [network connection](../network-connections.md).

Since version 1.19 (phyphox 1.2.0) you can additionally define map tags that work similarly to the map function of the value element. Each map tag defines a minimum and/or maximum value and an associated text. In contrast to the value element, the button uses an attribute *dynamicLabel* to define a data-container that is used with these map values. Phyphox sequentially goes through the map tags in the order they have been defined, and for the first one for which the value in the buffer given in *dynamicLabel* falls within min/max of the map tag, the text in the tag is used as the label for the button. If no map tag matches, then the normal label from the *label* tag is used.

{{spec:views/view/button}}

{{spec:views/button/input}}

{{spec:views/button/output}}

{{spec:views/button/trigger}}

{{spec:views/button/map}}

## View-Element: toggle

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![Two toggles, one switched on and one switched off](../../assets/screenshots/views/toggle-light.png#only-light){ .view-shot .on-glb }
![Two toggles, one switched on and one switched off](../../assets/screenshots/views/toggle-dark.png#only-dark){ .view-shot .on-glb }
</figure>

The toggle element displays a simple toggle (or a checkbox in the remote control interface), which allows the user to turn something off or on. The output buffer receives a 0 for off and a 1 for on. If the buffer is changed externally, a 0 is always interpreted as off while any other value is displayed as on.

{{spec:views/view/toggle}}

{{spec:views/toggle/output}}

## View-Element: slider

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![A slider from 100 to 1000 set to 440, with the current value shown above it](../../assets/screenshots/views/slider-light.png#only-light){ .view-shot .on-glb }
![A slider from 100 to 1000 set to 440, with the current value shown above it](../../assets/screenshots/views/slider-dark.png#only-dark){ .view-shot .on-glb }
</figure>

This is a view element used to input values from a limited range determined by a minimum and maximum value as well as a step size. The current value is also shown separately. With *type="range"* the slider can be used as a range slider with two handles, allowing the user to select a range by picking a lower and an upper value.

{{spec:views/view/slider}}

{{spec:views/slider/output}}

## View-Element: dropdown

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![A dropdown labelled Waveform with Square selected](../../assets/screenshots/views/dropdown-light.png#only-light){ .view-shot .on-glb }
![A dropdown labelled Waveform with Square selected](../../assets/screenshots/views/dropdown-dark.png#only-dark){ .view-shot .on-glb }
</figure>

The dropdown view element gives the user a list of options, each of which is associated with a value. The user simply taps the dropdown box, picks an option and the associated value is written to the output buffer.

{{spec:views/view/dropdown}}

{{spec:views/dropdown/output}}

{{spec:views/dropdown/map}}

