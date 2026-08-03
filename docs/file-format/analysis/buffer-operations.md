# Buffer operations

## append

This module appends all the values of the input buffers to a single output buffer. The order of the buffers will match the order their values appear in the output buffer. This module will return as many value as the sum of the input buffer sizes.

{{spec:analysis/analysis/append}}

## count

Returns the number of values in the input buffer

{{spec:analysis/analysis/count}}

## eventstream

This is a convenient and faster substitute for stopwatch implementations like it is used in the acoustic stopwatch. The idea is to detect events in a stream of data according to a given criterion and the index of each event within the input data stream is written to the output. The eventstream module also has multiple matching inputs and outputs to keep track of the status between multiple iterations of the analysis cycle.

The inputs that determine its behavior are *data* (the input data stream), *threshold* (with a slightly varying meaning according to the chosen *mode*) and *distance* (the minimum number of values before the next event may be detected).

Furthermore it takes *index*, *skip* and *last* as inputs. These represent the *index* (nth sample) of the data within a stream, the number of values to be skipped before the first event (typically the remainder of the last *distance* from the previous block in the last analysis cycle) and the *last* value from the previous data block in case it is needed to determine the criterion (for example a difference between consecutive values). For most purposes it should be enough to assign a data container for each of *index*, *skip* and *last* and attach it to the matching inputs AND outputs.

The output is mainly *events* which will hold the indices of detected events. Additionally, there are also index, skip und last as outputs, corresponding to the inputs.

The criterion is set by the attribute "mode" determining whether raw values, derivatives or absolutes are used for triggering:

{{spec:analysis/analysis/eventstream}}

    *mode="above"*
    :   triggers if a raw value of the data stream is greater than the threshold

    *mode="below"*
    :   triggers if a raw value of the data stream is less than the threshold

    *mode="aboveAbsolute"*
    :   triggers if an absolute value of the data stream is greater than the threshold

    *mode="belowAbsolute"*
    :   triggers if an absolute value of the data stream is less than the threshold

    *mode="aboveDerivative"*
    :   triggers if the derivative (difference of current minus previous value) of the data stream is greater than the threshold

    *mode="belowDerivative"*
    :   triggers if the derivative (difference of current minus previous value) of the data stream is less than the threshold

    *mode="aboveDerivativeAbsolute"*
    :   triggers if the absolute of the derivative (difference of current minus previous value) of the data stream is greater than the threshold

    *mode="belowDerivativeAbsolute"*
    :   triggers if the absolute of the derivative (difference of current minus previous value) of the data stream is less than the threshold

<!-- -->

## first

Retrieves the first entry of each buffer and appends it to each output buffer.

{{spec:analysis/analysis/first}}

## match

This module takes multiple inputs and match valid values to the same number of outputs. The module will go through all inputs simultaneously and only return those value for which **all** inputs have a finite value.

If for example input1 provides \[1, 2, NaN, 4, 5\] and input2 provides \[11, +Inf, 13, 14\], the result will be \[1, 4\] for output1 and \[11, 14\] for output2. The other value pairs (more than two inputs are allowed though) were filtered as one of both inputs was infinite, not a number ("NaN") or just did not have any more values.

{{spec:analysis/analysis/match}}

## map

This module takes three buffers representing x, y and z data. The data may be scattered across randomly and may be unordered. This module will be given ranges as well as a desired number of values along x and y and then rearrange the x, y, z data into a grid that is suitable to be displayed in a color map plot.

```xml
<map zMode="average">
    <input as="mapWidth" type="value">100</input>
    <input as="minX" type="value">0</input>
    <input as="maxX" type="value">10</input>
    <input as="mapHeight" type="value">100</input>
    <input as="minY" type="value">1</input>
    <input as="maxY" type="value">2</input>
    <input as="x">xData</input>
    <input as="y">yData</input>
    <input as="z">zData</input>
    <output as="x">xMapOut</output>
    <output as="y">yMapOut</output>
    <output as="z">zMapOut</output>
</map>
```

The example above takes xData, yData and zData and creates a grid of 100 by 100 data points covering x values from 0 to 10 and y values from 1 to 2.

{{spec:analysis/analysis/map}}

## max

Returns the maximum and its position. This module takes at least one input *y* and looks for the maximum of this buffer, but may also take a second input *x*. If *x* is defined, it will return the position of this maximum in terms of the associated x value. If *x* is not defined, position will be the index of the maximum.

If you want to find multiple local maxima, you can set the attribute "multiple" to true. In this case a third input may be used, which provides a threshold. The algorithm will split the data into sets that are entirely above the threshold and return a maximum and position for each set.

This module will return exactly one value per call if multiple is deactivated (default).

{{spec:analysis/analysis/max}}

## min

Returns the minimum and its position. This module takes at least one input *y* and looks for the minimum of this buffer, but may also take a second input *x*. If *x* is defined, it will return the position of this minimum in terms of the associated x value. If *x* is not defined, position will be the index of the minimum.

If you want to find multiple local minima, you can set the attribute "multiple" to true. In this case a third input may be used, which provides a threshold. The algorithm will split the data into sets that are entirely above the threshold and return a minimum and position for each set.

This module will return exactly one value per call if multiple is deactivated (default).

{{spec:analysis/analysis/min}}

## rangefilter

This module takes multiple inputs and allows to set min and max limits for each of them. The module will go through all inputs simultaneously and only return those value for which **all** inputs fall within their set min and max range. If one input is shorter than the others, its values are set to NaN and will not trigger the filter.

Min and max have to be defined immediately after the corresponding input and are treated as a single value (last value for buffers). The outputs correspond to the order of the inputs. Here multiple outputs can be defined with the same name!

In the following example in1 will trigger the filter if not in the range of 0 and 42, in2 will not trigger the filter at all (but if in1 or in3 trigger the filter only corresponding elements will be returned) and in3 will trigger the filter if the value is larger than the value in the buffer "limit". The results will be written to the buffers "out1", "out2" and "out3".

```xml
<rangefilter>
    <input>in1</input>
    <input as="min" type="value">0</input>
    <input as="max" type="value">42</input>
    <input>in2</input>
    <input>in3</input>
    <input as="max">limit</input>
    <output>out1</output>
    <output>out2</output>
    <output>out3</output>
</rangefilter>
```

{{spec:analysis/analysis/rangefilter}}

## reduce

This module takes a buffer with multiple values and reduces the number of items by a given (integer) factor. It distinguishes between x and y values and allows for different strategies like summing or averaging values which fall into a single value. A factor smaller than 1 can be used to inflate the size, but in this case the module will simply duplicate each item, so each item occurs round(1/factor) times.

```xml
<reduce averageX="false" averageY="false" sumY="false">
    <input as="factor" type="value">2</input>
    <input as="x">xBuffer</input>
    <input as="y">yBuffer</input>
    <output as="x">out1</output>
    <output as="y">out2</output>
</reduce>
```

{{spec:analysis/analysis/reduce}}

## sort

This module takes at least one input and sorts it. Values in additional inputs will follow the sorting of the first input buffer. By default, the values in the first buffer will be sorted in ascending order. This can be reversed with the attribute *descending*.

The number of values returned matches the number of values in the shortest buffer.

{{spec:analysis/analysis/sort}}

## split

Takes *data* as input and splits it into two buffers at the given *index*. A third parameter *overlap* allows to set a number of elements from before the split index that will also end up in the second buffer. *index* defaults to the length of the input data if not given, i.e. the entire input is returned as the first output without any splitting, which only makes sense in combination with an overlap, for example to take all data from a buffer associated with the input from a sensor and setting "overlap" such that a certain number of values is retained as a starting point for the next iteration.

{{spec:analysis/analysis/split}}

*index*
:   *as* required
:   Number of inputs: One or none, defaults to the number of values in the *data* buffer
:   Index at which *data* should be split. The value at *index* will be the first one that is not appended to the first output.

<!-- -->

*overlap*
:   *as* required
:   Number of inputs: One or none, default: 0
:   Number of elements that should be sent to both outputs. This does not change the output to the first output buffer, but sends values before *index* also to the second output.

<!-- -->

## subrange

This module takes multiple inputs and returns all values within a given index range. This is much faster than using the rangefilter module for this purpose. The range is set using the inputs *from* (inclusive) and *to* (exclusive). Optionally, instead of setting *to*, you can set *length*, defining the total number of values returned after *from*.

```xml
<subrange>
    <input as="from" type="value">0</input>
    <input as="to">countBuffer</input>
    <input>in1</input>
    <input>in2</input>
    <output>out1</output>
    <output>out2</output>
</subrange>
```

{{spec:analysis/analysis/subrange}}

## threshold

This module takes at least one input *y* and looks for position at which the values cross a given threshold. the input *threshold* is interpreted as a single value (last added element). This module may also take a third input *x*. If *x* is defined, it will return the position of the crossing in terms of the associated x value. If *x* is not defined, position will be the index of the crossing.

You can also define the attribute *falling* as true to search for a crossing from larger to smaller values.

This module will return exactly one value per call.

{{spec:analysis/analysis/threshold}}
