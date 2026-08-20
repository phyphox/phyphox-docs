# Basic elements

The view elements on this page additionally accept the [attributes common to all view elements](index.md#common-attributes).

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

