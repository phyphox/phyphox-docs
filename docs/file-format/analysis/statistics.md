# Statistics

## average

This module calculates the average of all values in the input buffer. Optionally (i.e. if the output is connected), the standard deviation is calculated as well (Corrected sample standard deviation).

{{spec:analysis/analysis/average}}

## binning

The binning module distributes the values from its input *in* into ranges (bins) and outputs a mapping of these ranges and the number of values in each of them. The bins are set to x0..x0+dx..x0+2dx..x0+3dx etc. Therefore *x0* defines an offset of the bins and *dx* the size of each bin. *x0* defaults to zero and *dx* to 1, so without these, the module defaults to binning to integer intervals.

The output can directly be used to display a histogram. *binStarts* will receive the starting values of each range (bin) while the count is written to *binCounts*.

{{spec:analysis/analysis/binning}}

## movingaverage

Take *data* as input and calculate the moving average of its items. This means, that for each item an additional number of previous items is taken into account for averaging and the this average is sent to the output for each input item. The number of previous items is given by *width*, so a total of *width*+1 elements are used for each average.

The optional parameter *dropIncomplete* determines whether values are emitted for which less than *width* previous elements are available. This means that with *dropIncomplete* set to *true*, it will output n-*width*+1 values for an input of n data values. With *dropIncomplete* set to *false*, it will output exactly n values.

{{spec:analysis/analysis/movingaverage}}
