# Basic elements

The view elements on this page additionally accept the [attributes common to all view elements](index.md#common-attributes).

## View-Element: info

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![An info element with a short instruction](../../assets/screenshots/views/info-light.png#only-light){ .view-shot .on-glb }
![An info element with a short instruction](../../assets/screenshots/views/info-dark.png#only-dark){ .view-shot .on-glb }
</figure>

The info element does not take any inputs or write to any outputs. It just displays a string defined as the *label* attribute.

{{spec:views/view/info}}

## View-Element: separator

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![Two headings, each underlined by a thin orange separator, with a taller empty separator between the sections](../../assets/screenshots/views/separator-light.png#only-light){ .view-shot .on-glb }
![Two headings, each underlined by a thin orange separator, with a taller empty separator between the sections](../../assets/screenshots/views/separator-dark.png#only-dark){ .view-shot .on-glb }
</figure>

The separator element does not take any inputs or write to any outputs. It just acts as a separator to give a visual aid in grouping other elements. It defaults to a very thin height of 0.1 (in units of text line heights) and a color matching the background color of the experiment screen. To achieve a margin between elements, you should set the height to 1; to create a narrow line, set the color (as a six-digit RGB hex value or a named color from the phyphox [Colors](../colors.md)) and leave the height at 0.1 - optionally padded by two other separator elements.

{{spec:views/view/separator}}

## View-Element: value

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![Three value elements showing a frequency, a period and an amplitude with their units](../../assets/screenshots/views/value-light.png#only-light){ .view-shot .on-glb }
![Three value elements showing a frequency, a period and an amplitude with their units](../../assets/screenshots/views/value-dark.png#only-dark){ .view-shot .on-glb }
</figure>

The value element displays a single value to the user. If the input buffer contains more than one value, the latest value will be displayed. The input is defined by a simple *input* tag within the value block and needs to be a data-container (see above).

Since file format version 1.5 (phyphox 1.0.7) you can define range mappings with the map-tag. The map tag includes a string which will replace the number and unit that would be displayed otherwise. phyphox will test all mappings in the order they are given and replace the output with the first mapping that applies. A mapping applies if the value to be shown falls in the range given by the attributes *min* and *max* (inclusive). *min* and *max* can be left out and default to negative and positive infinity. So, a map-tag without any attributes acts as a catch-all case.

Since file format version 1.19 (phyphox 1.2.0) the attribute gives even more options to change how the value is displayed, like for example showing GPS coordinates not only as a decimal value, but as degrees, minutes and seconds. Also, the positiveUnit and negativeUnit make it possible to change the unit depending on the value's sign. In the case of the GPS coordinate example, this allows showing N (for north) after positive latitudes and S (for south) after negative latitudes.

The *unit* is either a [unit reference](../units.md#unit-references) such as `@meter`, which the app can convert to other units of the same quantity, or plain text shown as written.

{{spec:views/view/value}}

{{spec:views/value/input}}

{{spec:views/value/map}}

## View-Element: image

<figure class="view-example" markdown>
<figcaption>Example</figcaption>
![An info element above an image of a pendulum](../../assets/screenshots/views/image-light.png#only-light){ .view-shot .on-glb }
![An info element above an image of a pendulum](../../assets/screenshots/views/image-dark.png#only-dark){ .view-shot .on-glb }
</figure>

Display an image with the file name RESOURCE. RESOURCE should be a PNG or JPEG image, the formats both apps can display. SVG is not supported on either platform; for a drawing that should stay sharp at any size, see the [drawing elements](drawing.md). The image is placed in the resource folder "res" in a zip file along with the experiment XML file. So, for example, instead of sharing experiment.phyphox you would share a zip file that contains experiment.phyphox together with a folder called "res" that contains an image "demo.jpg". The image element would then set RESOURCE to "demo.jpg" (not res/demo.jpg), i.e. `<image src="demo.jpg" />`.

{{spec:views/view/image}}

### Images for light and dark mode

A diagram drawn for a white background is often unreadable on the dark interface of phyphox, and the other way round. For simple line drawings, *darkFilter* or *lightFilter* set to `invert` is enough. A photograph or a coloured diagram does not survive inverting, though, so since file format 1.21 an image element can name a separate file for each mode: *lightSrc* is shown instead of *src* while the interface is in light mode, *darkSrc* while it is in dark mode. *src* remains required and is shown in every mode that has no file of its own, so a picture that only needs a dark version gets one extra attribute:

```xml
<image src="circuit.png" darkSrc="circuit-dark.png" />
```

The filter of the active mode still applies, now to the alternative file, so a dedicated dark version normally comes without a *darkFilter*. Each file is bundled in the `res` folder like *src* (see [Bundling images](../../transferring-experiments.md#bundling-images)). If one of them is missing, the element shows that the image is not available in that mode; it does not fall back to *src*. The element follows a change of the mode while the experiment is open, and its height follows the image that is shown, so give both versions the same pixel dimensions - otherwise the layout shifts when the mode changes, and a [stack](groups.md#view-element-stack) or a graph aligned with the image no longer lines up. The remote interface chooses by its own light/dark switch.

