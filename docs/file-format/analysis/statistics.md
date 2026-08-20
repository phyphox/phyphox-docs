# Statistics

## average

This module calculates the average of all values in the input buffer. Optionally (i.e. if the output is connected), the standard deviation is calculated as well (corrected sample standard deviation). Non-finite values in the input are skipped. A single valid input value yields the value itself as average and a single NaN as standard deviation (which needs at least two values); an empty input or an input without any finite value writes NaN to each connected output.

{{spec:analysis/analysis/average}}

## binning

The binning module distributes the values from its input *in* into ranges (bins) and outputs a mapping of these ranges and the number of values in each of them. The bins are set to x0..x0+dx..x0+2dx..x0+3dx etc. Therefore *x0* defines an offset of the bins and *dx* the size of each bin. *x0* defaults to zero and *dx* to 1, so without these, the module defaults to binning to integer intervals.

The output can directly be used to display a histogram. *binStarts* will receive the starting values of each range (bin) while the count is written to *binCounts*.

Bins are lower-edge inclusive: a value exactly on a bin boundary is counted in the bin that starts there. Non-finite input values are skipped. A *dx* of zero, a negative or non-finite *dx* and a non-finite *x0* are errors yielding empty outputs — there is no silent substitution; only an absent input (or an empty parameter buffer) selects the defaults of *x0* = 0 and *dx* = 1.

{{spec:analysis/analysis/binning}}

## movingaverage

Takes *data* as input and calculates the moving average of its items. This means that for each item an additional number of previous items is taken into account for averaging and this average is sent to the output for each input item. The number of previous items is given by *width*, so a total of *width*+1 elements are used for each average.

The optional parameter *dropIncomplete* determines whether values are emitted for which fewer than *width* previous elements are available. This means that with *dropIncomplete* set to *true*, it will output n-*width* values for an input of n data values. With *dropIncomplete* set to *false*, it will output exactly n values.

Non-finite values inside the averaging window are skipped: the average is taken over the finite values only, and a window without any finite value yields NaN. An absent *width* input or an empty width buffer selects the default of 10, while a present but non-finite or negative width is an error yielding an empty output.

{{spec:analysis/analysis/movingaverage}}
