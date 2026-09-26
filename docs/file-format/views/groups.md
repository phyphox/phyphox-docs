# View groups

!!! note "New in file format 1.21 (phyphox 1.3.0)"
    The elements on this page are part of file format 1.21, which the
    [next release](../../reference/version-history/next.md) carries. Every app released before it
    refuses a file declaring that version.

A view lays out its elements top to bottom, each taking the full width. View groups are view
elements that contain other view elements and arrange them differently: side by side, in a grid
that adapts to the screen width, or on top of each other. Together with a few additions to
[graphs](graph.md#fixing-the-plot-area) and [colors](../colors.md) they make gauges, compasses,
map overlays and dashboards possible with nothing but the experiment file.

The view elements on this page additionally accept the
[attributes common to all view elements](index.md#common-attributes), with two rules that hold
for every group: *label* has no effect on a group, and *visibility* hides the whole group.

## Nesting

| Group | May appear in | May contain |
|---|---|---|
| `vertical`, `horizontal`, `grid` | a view or any of these three | every view element, including these groups and `stack` |
| `stack` | a view, `vertical`, `horizontal` or `grid` | `info`, `separator`, `value`, `graph`, `image` and `transform` |
| `transform` | a `stack` only | exactly one of `info`, `separator`, `value`, `graph`, `image` |

The groups nest to any depth. A stack deliberately holds only elements that show data: it is
not interactive (see below), so user-input elements, the camera and the depth preview cannot sit
in it.

## Sizing

Inside every group a child keeps the height it would have on its own at the width it is given: a
graph follows its *aspectRatio*, an image its pixel aspect ratio, a value or button its text.
A row of a `horizontal` or `grid` group is as tall as its tallest child, and shorter children are
centred vertically in it. A child hidden through *visibility* takes no space; its siblings share
the row.

## View-Element: vertical

The layout of a view itself, available as an element so that it can be nested - most usefully as
one column of a `horizontal` group holding several elements.

{{spec:views/view/vertical}}

## View-Element: horizontal

The children sit side by side in one row and share the full width. By default they get equal
widths; the *weight* attribute on a child changes its share.

```xml
<view label="Controls">
    <info label="Three buttons next to each other:" />
    <horizontal>
        <button label="Start"><input type="value">1</input><output>run</output></button>
        <button label="Stop"><input type="value">0</input><output>run</output></button>
        <button label="Reset"><input type="value">0</input><output>count</output></button>
    </horizontal>
</view>
```

```xml
<view label="Plot and legend">
    <horizontal>
        <graph label="Pendulum" labelX="t" unitX="s" labelY="x" unitY="m" weight="3">
            <input axis="x">t</input>
            <input axis="y">x</input>
        </graph>
        <image src="legend.png" />
    </horizontal>
</view>
```

The graph gets three quarters of the width and the image one quarter.

{{spec:views/view/horizontal}}

{{spec:views/view/horizontal|common:horizontal_child_attributes}}

## View-Element: grid

The children fill rows of equal-width columns. The group uses as many columns as needed to keep
each child at or below *maxWidth*: one column while the available width is at most *maxWidth*,
two while it is at most twice *maxWidth*, and so on. A phone in portrait therefore shows the
familiar single column, while a tablet or a phone in landscape fills the width with several
elements instead of stretching each of them to a wide, flat plot.

*maxWidth* is given in text line heights, the unit the
[separator](basics.md#view-element-separator)'s *height* already uses. It follows the screen
density and the user's text size on every platform, so one value means the same on Android, iOS
and in the web interface, and larger text gives fewer columns.

```xml
<grid maxWidth="25" fillLastRow="true">
    <graph label="x" labelX="t" unitX="s" labelY="x" unitY="m/s²"><input axis="x">t</input><input axis="y">ax</input></graph>
    <graph label="y" labelX="t" unitX="s" labelY="y" unitY="m/s²"><input axis="x">t</input><input axis="y">ay</input></graph>
    <graph label="z" labelX="t" unitX="s" labelY="z" unitY="m/s²"><input axis="x">t</input><input axis="y">az</input></graph>
    <graph label="abs" labelX="t" unitX="s" labelY="a" unitY="m/s²"><input axis="x">t</input><input axis="y">a</input></graph>
</grid>
```

Four graphs: one column on a phone, two by two on a tablet, and with *fillLastRow* a single
graph left over on a row of three would stretch across the row instead of leaving two empty
cells.

{{spec:views/view/grid}}

## View-Element: stack

The children are drawn on top of each other in one rectangle, all taking the full width. The
tallest child sets the height of the stack and the others are centred vertically in it. Later
children are drawn over earlier ones - the same order as everywhere else in the file - so a
background image comes first. Transparent parts of a child show what lies below: images keep
their alpha channel, the plot area of a graph is transparent, and
[colors with an alpha byte](../colors.md) are blended.

A stack is not interactive. Its graphs cannot be maximized, zoomed or used for picking, and a
transformed element receives no touches - with children overlapping, a touch would be
ambiguous. Use a `horizontal` or `grid` group next to the stack for controls.

```xml
<stack>
    <image src="gauge-face.png" />
    <transform originX="0.5" originY="0.8">
        <input as="rotate" min="0" max="100" mapMin="-2.35" mapMax="2.35" clamp="true">percent</input>
        <image src="gauge-needle.png" />
    </transform>
    <value label="" unit="%" size="2"><input>percent</input></value>
</stack>
```

A gauge: the face is the background, the needle image is rotated about a point near its lower
edge from -135° to +135° as the container *percent* goes from 0 to 100 and stops at the ends,
and the numeric value is drawn on top.

{{spec:views/view/stack}}

## View-Element: transform

A transform wraps exactly one element of a stack and scales, rotates, moves or fades it under
the control of data containers. Each property is bound by an `input` child; a property without
an input keeps its neutral value (1 for the scales and the opacity, 0 for the shifts and the
rotation).

The properties compose as scale, then rotation, then translation, all about the origin given
by *originX* and *originY*. A positive rotation turns clockwise on screen, which is what all
three platforms do natively; note that this is the opposite of the mathematical convention.
Lengths are fractions of the wrapped element's own untransformed size, so `translateX` of 1
moves it by its full width, and the layout of the stack uses that untransformed size as well.

{{spec:views/stack/transform}}

{{spec:views/transform/input}}

The linear map turns a measured range into a property range without an analysis step: with
*min*, *max*, *mapMin* and *mapMax* the property is *mapMin + (v - min) · (mapMax - mapMin) /
(max - min)*, and *clamp* holds it at the ends outside the range. The defaults make the map the
identity, so a plain `<input as="rotate">angle</input>` uses the value as it is. Anything the map
cannot express is computed in the [analysis block](../analysis/index.md) into a container of its
own.

## What this enables

- **Gauges:** a static face image and a needle image in a `transform` bound to the value, as in
  the example above. A linear gauge scales a solid-colour image with `scaleX` from an origin at
  its left edge, under a face image whose window is transparent.
- **Compass:** a rose image rotated with `rotate` under a fixed needle, or the other way round,
  from the magnetometer heading mapped from degrees to radians.
- **Map with a position marker:** a marker image shifted with `translateX` and `translateY`
  over a map image, from coordinates mapped to fractions of the image.
- **Measurements on a map or a photograph:** a `graph` with `style="map"` over an image, with
  its [plot area fixed](graph.md#fixing-the-plot-area) to the image and its map colours given
  with an alpha byte so the image stays visible.
- **Dashboards:** a `grid` of graphs that becomes two by two on a tablet, a `horizontal` row of
  buttons, a `vertical` column of values next to a plot.

The images live in the [experiment's resource folder](basics.md#view-element-image), so an
experiment using them is shared as a zip container rather than a bare `.phyphox` file. Images for
common cases, such as gauge faces and a compass rose, are planned to ship with the app; until
then, bring your own.
