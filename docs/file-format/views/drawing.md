# Drawing elements

!!! note "New in file format 1.21 (phyphox 1.3.0)"
    The elements on this page are part of file format 1.21, which the
    [next release](../../reference/version-history/next.md) carries; every app released before
    1.3.0 refuses a file declaring that version. This page was written ahead of the
    implementations (2026-10-05), which followed it the same day on both apps' development
    branches and in the remote interface; it remains the definition they are checked against.

A gauge built as a [stack](groups.md#view-element-stack) of images needs a new image whenever
its range changes, cannot follow a [unit conversion](../units.md), and asks the author to draw
a dial in the first place. The two elements on this page replace the images with drawings the
app makes from attributes: `geometry` draws a shape - a face, a needle, a coloured band - and
`scale` draws the axis of a gauge with tics, values and a label. A geometry is static, and so
is the geometry of a scale; only the range of a scale can follow data. Motion comes from
wrapping either in a [transform](groups.md#view-element-transform), exactly as with images.

The view elements on this page additionally accept the
[attributes common to all view elements](index.md#common-attributes). On a geometry the *label*
has no effect; on a scale it is the axis label.

## Drawing coordinates

Every child of a stack takes the full width, and its height follows from its own content: an
image from its pixel ratio, a graph from its *aspectRatio*. A geometry or scale has an
*aspectRatio* too (default 1, a square), so children that are meant to line up carry the same
ratio and share one rectangle. Inside that rectangle the two elements use the conventions the
format already has for the [plot area](graph.md#fixing-the-plot-area) and for the transform's
*originX*/*originY* and *translateX*/*translateY*:

- **Positions** are fractions of the element's box: an x coordinate is a fraction of the width
  measured from the left edge, a y coordinate a fraction of the height measured from the top
  edge. `0.5`/`0.5` is the centre.
- **Lengths** - radii, line widths, tic lengths, distances from a baseline - are fractions of
  the element's **width**, whatever the aspect ratio. The width is what every child of a stack
  shares, so a needle drawn in one child and a radius in another agree pixel for pixel even
  when their aspect ratios differ, and a circle stays a circle. In a square element lengths and
  positions use the same unit.
- **Angles** are in radians, positive clockwise on screen, measured from twelve o'clock. This is
  the transform's rotation convention: a needle drawn pointing up and rotated by *θ* through
  a transform points at the position of angle *θ* on a circular scale, with no conversion
  between the two.
- Values outside 0 to 1 are allowed; what falls outside the element's box is clipped.

So a needle, a scale and a face line up by construction: give the stack's children the same
*aspectRatio*, put the pivot of the needle (the transform's origin) at the centre of the scale,
and the numbers in the file are the same numbers in every child.

## View-Element: geometry

A single shape on a transparent background. An area shape - rectangle, circle, arc - is filled
with *color* and outlined with *lineColor*, each only when the attribute is given; a line is
drawn with *lineColor*, or with *color* when there is no *lineColor*. Which position
attributes apply depends on *shape*; the others are ignored.

```xml
<geometry shape="circle" radius="0.48" color="202020" lineColor="ff7e22" lineWidth="0.01" />
```

A dark face with an orange rim, nearly filling a square element.

```xml
<geometry shape="arc" radius="0.45" innerRadius="0.4" startAngle="1.57" sweepAngle="0.79" color="fe005d" />
```

A red band on the outer rim between 90° and 135°: the danger zone of a gauge.

```xml
<transform originX="0.5" originY="0.5">
    <input as="rotate" min="0" max="100" mapMin="-2.3562" mapMax="2.3562" clamp="true">percent</input>
    <geometry shape="line" startX="0.5" startY="0.5" endX="0.5" endY="0.12" lineColor="ff7e22" lineWidth="0.015" />
</transform>
```

A needle: a line from the centre straight up, rotated about the centre. For a needle with a
rounded or tapered look use a tall, narrow rectangle with *cornerRadius* instead of a line.

{{spec:views/view/geometry}}

## View-Element: scale

The axis of a gauge: a baseline from the position of *min* to the position of *max*, major tics
every *ticStep*, optional minor tics between them, the value at every *valueEvery*-th major tic,
and a label with a unit. Each part can be left out: *lineWidth* 0 draws no baseline,
*ticLength* 0 no tics, *valueEvery* 0 no values, and without *label* and *unit* there is no
label.

A **linear** scale runs straight from *startX*/*startY* to *endX*/*endY*, in any direction. A
**circular** scale runs on the arc around *centerX*/*centerY* with *radius*, from *startAngle*
over *sweepAngle* - clockwise for a positive sweep, counter-clockwise for a negative one. The
defaults of the circular shape, -135° over 270°, give the usual three-quarter dial with the
gap at the bottom.

**Sides.** The distances from the baseline - *ticLength*, *minorTicLength*, *valueDistance* -
are signed. On a circular scale positive is outward from the centre. On a linear scale positive
is to the right of the direction from start to end as seen on screen: below a scale that runs
from left to right, to the right of one that runs upwards. A negative value puts that part on
the other side.

**Tics.** Major tics sit at *min* + *k* · *ticStep* for *k* = 0, 1, 2, … up to *max*, so the
ends of a gauge get a tic when the range is a multiple of the step. Without *ticStep* the step
is chosen as a graph axis would choose it for an axis of the same length on screen. *minorTics*
puts that many minor tics between two major ones. The values are formatted with as many
decimals as the step needs, or with *precision* when it is given.

**Text** - the values and the label - is drawn centred on its position, in the app's text
size scaled by *size*. The values are upright by default; *valueOrientation* turns them
*tangential* (along the baseline, reading from *min* to *max*, so they follow a dial round)
or *radial* (across the baseline, reading outward on a dial). The label is always upright. It follows the user's text-size setting like every other text in
the app rather than the size of the element, so a dial that is small on a phone keeps readable
numbers; leave room for them, as text outside the element's box is clipped. The label is drawn
as "label (unit)", or either part alone, centred at *labelPositionX*/*labelPositionY*, which
defaults to the centre of the element - the open middle of a dial.

```xml
<scale shape="circular" min="0" max="100" ticStep="10" minorTics="4"
       radius="0.42" ticLength="-0.04" minorTicLength="-0.02" valueDistance="-0.11"
       label="Load" unit="%" labelPositionY="0.72" />
```

Tics inward from a ring of radius 0.42, with the values inside and the label below the pivot.

```xml
<scale shape="linear" min="-20" max="60" ticStep="10" minorTics="1" unit="@degree_celsius"
       aspectRatio="4" startX="0.05" startY="0.25" endX="0.95" endY="0.25"
       ticLength="0.03" valueDistance="0.08" label="Temperature" labelPositionX="0.5" labelPositionY="0.88" />
```

A thermometer scale across a wide element, tics and values below the line, in degrees Celsius -
convertible to Fahrenheit by the user.

**Range from data.** *min* and *max* are attributes, but an `input` child binds either of
them to a data container, so a gauge can take its range from a user's edit field or from an
analysis result:

```xml
<scale shape="circular" min="0" max="100" unit="@meter">
    <input as="max">range</input>
</scale>
```

The last value of the container replaces the attribute; while the container is empty or its
value is not finite, the attribute holds. The baseline does not move - only the tics, the values
and the conversion follow. A needle driven by a transform has a map with fixed ends and does
not follow by itself; an experiment with a changing range maps the value to the needle's angle
in the [analysis block](../analysis/index.md) and binds the transform to that result.

**Units.** *unit* takes a [unit reference](../units.md#unit-references) or text, like the unit
of a value or a graph axis. With a reference the scale takes part in the unit conversion: the
*Unit system* setting converts it on loading, and tapping the label opens the unit dialog. The
tap works inside a stack as well, as long as the scale is not wrapped in a transform - this is
the one touch a stack passes on, so that a gauge can be switched like a graph axis. The tap is
offered to the stack's children from the topmost down, skipping transformed children and any
child that does not handle it, so a scale at the bottom of the stack with a needle drawn over
its label is still reached. A converted
scale keeps its geometry: the positions of *min* and *max* do not move (a needle driven by the
buffer value still points at the right place), only the numbers change. While another unit is
shown, the tics are chosen automatically in that unit, as a graph axis does - an explicit
*ticStep* and the *valueEvery* rhythm describe the experiment's unit, where nice numbers in
metres would be odd numbers in feet - and an explicit *precision* follows the
[precision rule](../units.md#conversion-in-the-app) of converted values. Temperature scales
convert with their offset, as every position does.

{{spec:views/view/scale}}

{{spec:views/scale/input}}

## A gauge without images

```xml
<stack>
    <geometry shape="circle" radius="0.48" color="202020" lineColor="ff7e22" lineWidth="0.01" />
    <geometry shape="arc" radius="0.45" innerRadius="0.4" startAngle="1.57" sweepAngle="0.79" color="fe005d" />
    <scale shape="circular" min="0" max="100" ticStep="10" minorTics="4"
           radius="0.42" ticLength="-0.04" minorTicLength="-0.02" valueDistance="-0.11"
           label="Load" unit="%" labelPositionY="0.72" />
    <transform originX="0.5" originY="0.5">
        <input as="rotate" min="0" max="100" mapMin="-2.3562" mapMax="2.3562" clamp="true">percent</input>
        <geometry shape="line" startX="0.5" startY="0.5" endX="0.5" endY="0.12" lineColor="ff7e22" lineWidth="0.015" />
    </transform>
    <geometry shape="circle" radius="0.04" color="ff7e22" />
    <value unit="%" size="2" align="center"><input>percent</input></value>
</stack>
```

Every child is square (the default *aspectRatio* of geometry and scale), so the stack is one
square: a face, a red band on the rim from 90° to 135°, the scale with its tics pointing inward,
a needle rotated about the centre over the same -135° to 135° the scale spans, a hub over the
needle's pivot, and the numeric value. Changing the range means changing *min*, *max* and the
transform's map; nothing is drawn by hand, and the experiment ships as a bare `.phyphox` file.

A linear gauge is the same idea laid flat: a rounded rectangle as the trough, a second one
scaled with `scaleX` from an origin at its left edge as the bar, and a linear scale below.
