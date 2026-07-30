
## Formula node

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

For simple calculations, you can either use the math nodes listed below or write it all in a single formula node. In most cases, when you would need multiple math nodes otherwise, the formula node is faster as it does not need to read and write large buffers multiple times but can do the whole calculation in a single step. However, in some cases, not all options are available in the formula node and the implementation of both versions are not necessarily identical.

```xml
<formula formula="[1]+sqrt((7+[2_])^[3_])">
    <input>singleValue</input>
    <input>multipleValues</input>
    <input>multipleValues2</input>
    <output>result</output>
</formula>
```

The example above takes a single value from the buffer "singleValue" and multiple values from the buffers "multipleValues" and "multipleValues2". These buffers are represented in the formula according to their order as 1, 2 and 3. If only a single value from a buffer is used, it is referred to as \[1\], but if multiple values should be used and the calculation should be repeated for each value and output a result for each value, an underscore is added as in \[2\_\] or \[3\_\]. The example then output the result of "A + sqrt((7+B)^C)", with A being the last single value from "singleValue" and B and C being the first value from "multipleValues" and "multipleValues2" respectively. This is repeated with the same single value for A but the second values from "multipleValues" and "multipleValues2" for B and C. In this example, sqrt is a common function across many programming languages and denotes the square root of its parameter.

The formula parser respects brackets ("(" and ")"), understands simple binary operants (+, -, \*, /, % (modulo), ^ (power)) and common functions (sqrt, sin, cos, tan, asin, acos, atan, atan2¹, sinh, cosh, tanh, exp, log, abs, sign, heaviside², round, ceil, floor, min¹², max¹²).

¹ *atan2*, *min* and *max* take two parameters (for example *min(2,5)* yields 2)

² *heaviside*, *min* and *max* are available since file format 1.10 (phyphox [version 1.1.6](../reference/version-history/1.1.6.md))

## Basic math

### abs (absolute)

Calculates the absolute value of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*abs*
:   *output*
:   *as* not required

### add

Calculates the sum of all inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*summand*
:   *input*
:   *as* not required
:   Number of inputs: At least one

<!-- -->

*sum*
:   *output*
:   *as* not required

### divide

Calculates the quotient of multiple divisors from a single dividend element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

For this simple function you can leave out the *as* attribute. If you do so, the first input will be used as dividend and all subsequent values as divisors.

*dividend*
:   *input*
:   *as* not required, but order matters if left out
:   Number of inputs: Exactly one

*divisor*
:   *input*
:   *as* not required, but order matters if left out
:   Number of inputs: Arbitrary

<!-- -->

*quotient*
:   *output*
:   *as* not required

### gcd (greatest common divisor)

Calculates the greatest common divisor of two inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly two

<!-- -->

*gcd*
:   *output*
:   *as* not required

### lcm (least common multiple)

Calculates the least common multiple of two inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly two

<!-- -->

*lcm*
:   *output*
:   *as* not required

### log

**Available since phyphox file format 1.5 (phyphox 1.0.7)**

Calculates the natural logarithm of a single input element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*log*
:   *output*
:   *as* not required

### multiply

Calculates the product of all inputs element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*factor*
:   *input*
:   *as* not required
:   Number of inputs: At least one

<!-- -->

*product*
:   *output*
:   *as* not required

### power

Calculates the power of a base and an exponent element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

*base*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*exponent*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

<!-- -->

*power*
:   *output*
:   *as* not required

### round

**Available since phyphox file format 1.5 (phyphox 1.0.7)**

Round the values from the single input element-wise and writes the results to a single output buffer. This module will write as many values as there are values in the input buffer. By default it will round to the nearest integer. The attributes *ceil* and *floor* can change that to the nearest larger integer or the nearest smaller integer.

*floor*
:   *attribute*
:   *optional*, default: false

<!-- -->

*ceil*
:   *attribute*
:   *optional*, default: false

<!-- -->

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*round*
:   *output*
:   *as* not required

### subtract

Calculates the difference of multiple subtrahends from a single minuend element-wise and writes it to a single output buffer. This module will write as many values as there are values in the biggest input buffer. If a buffer is shorter than the others (especially if one input is a single value), its last value will be repeated. (Exception: If any buffer is empty, the result will be an empty buffer, too.)

For this simple function you can leave out the *as* attribute. If you do so, the first input will be used as minuend and all subsequent values as subtrahends.

*minuend*
:   *input*
:   *as* not required, but order matters if left out
:   Number of inputs: Exactly one

*subtrahend*
:   *input*
:   *as* not required, but order matters if left out
:   Number of inputs: Arbitrary

<!-- -->

*difference*
:   *output*
:   *as* not required

## Trigonometric functions

### acos

Calculates the inverse cosine of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

*deg*
:   *attribute*, **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: false

<!-- -->

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*acos*
:   *output*
:   *as* not required

### asin

Calculates the inverse sine of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

*deg*
:   *attribute*, **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: false

<!-- -->

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*asin*
:   *output*
:   *as* not required

### atan

Calculates the inverse tangens of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

*deg*
:   *attribute*, **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: false

<!-- -->

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*atan*
:   *output*
:   *as* not required

### atan2

Calculates the two-argument variant of the inverse tangens (corresponding to atan(y/x), see [Wikipadia](https://en.wikipedia.org/wiki/Atan2) for an explanation) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

*deg*
:   *attribute*, **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: false

<!-- -->

*y*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*x*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*atan2*
:   *output*
:   *as* not required

### cos

Calculates the cosine of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

*deg*
:   *attribute*, **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: false

<!-- -->

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*cos*
:   *output*
:   *as* not required

### cosh

Calculates the hyperbolic cosine of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*cosh*
:   *output*
:   *as* not required

### sin

Calculates the sine of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

*deg*
:   *attribute*, **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: false

<!-- -->

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*sin*
:   *output*
:   *as* not required

### sinh

Calculates the hyperbolic sine of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*sinh*
:   *output*
:   *as* not required

### tan

Calculates the tangens of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer. The module will calculate in radians unless degrees are specified using the *deg* attribute.

*deg*
:   *attribute*, **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: false

<!-- -->

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*tan*
:   *output*
:   *as* not required

### tanh

Calculates the hyperbolic tangens of a single input (in radians) element-wise and writes it to a single output buffer. This module will write as many values as there are values in the input buffer.

*value*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*tanh*
:   *output*
:   *as* not required

## Statistics

### average

**Available since phyphox file format 1.2 (phyphox 1.0.3)**

This module calculates the average of all values in the input buffer. Optionally (i.e. if the output is connected), the standard deviation is calculated as well (Corrected sample standard deviation).

*buffer*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*average*
:   *output*
:   *as* required

*stddev*
:   *output*
:   *as* required

### binning

**Available since phyphox file format 1.2 (phyphox 1.0.3)**

The binning module distributes the values from its input *in* into ranges (bins) and outputs a mapping of these ranges and the number of values in each of them. The bins are set to x0..x0+dx..x0+2dx..x0+3dx etc. Therefore *x0* defines an offset of the bins and *dx* the size of each bin. *x0* defaults to zero and *dx* to 1, so without these, the module defaults to binning to integer intervals.

The output can directly be used to display a histogram. *binStarts* will receive the starting values of each range (bin) while the count is written to *binCounts*.

*in*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

*x0*
:   *input*
:   *as* required
:   Number of inputs: One or none

*dx*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*binStarts*
:   *output*
:   *as* not required

*binCounts*
:   *output*
:   *as* not required

### movingaverage

**Available since phyphox file format 1.18 (phyphox 1.1.16)**

Take *data* as input and calculate the moving average of its items. This means, that for each item an additional number of previous items is taken into account for averaging and the this average is sent to the output for each input item. The number of previous items is given by *width*, so a total of *width*+1 elements are used for each average.

The optional parameter *dropIncomplete* determines whether values are emitted for which less than *width* previous elements are available. This means that with *dropIncomplete* set to *true*, it will output n-*width*+1 values for an input of n data values. With *dropIncomplete* set to *false*, it will output exactly n values.

*dropIncomplete*
:   *attribute*
:   optional, defaults to false

<!-- -->

*data*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*width*
:   *input*
:   *as* required
:   Number of inputs: One or none, defaults to 10

<!-- -->

*data*
:   *output*
:   *as* not required

## Advanced math

### autocorrelation

This module will calculate the autocorrelation. It takes at least one input buffer *y*, but can take a second input *x* as well. If *x* is omitted, it will be filled with indices. Additionally, single value inputs *minX* and *maxX* can be set as well. These limit the x range over which the autocorrelation is calculated to improve performance. The module will return as many values as provided by the input buffer and fill the output buffer *y* with the normalized autocorrelation of the *y* input buffer. The *x* output buffer will be filled with the relative *x* of the autocorrelation based on the *x* input buffer.

*x*
:   *input*
:   *as* required
:   Number of inputs: One or none

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*minX*
:   *input*
:   *as* required
:   Number of inputs: One or none

*maxX*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*y*
:   *output*
:   *as* required

*x*
:   *output*
:   *as* required

### butterworth

**Available since phyphox file format 1.20 (phyphox 1.2.1)**

This module represents the transfer function of a Butterworth filter. It takes the order *n* and (upper) *cutoff* frequency as inputs and acts as a low pass. Optionally, you can also provide a lower cutoff frequency as *cutoffLow*, in which case it acts as a bandpass. The *x* input needs to provide frequencies for each data point of the *y* input. Frequencies are taken as absolute values for the filter. Note that this is only the transfer function, so you want to use it together with the *fft* module.

*x*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*n*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*cutoff*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*cutoffLow*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*filtered*
:   *output*
:   *as* not required

### crosscorrelation

This module will calculate a crosscorrelation of two inputs. It will only calculate the part of the crosscorrelation for which the smaller buffer is entirely covered by the larger one. So with one input buffer of size n and one input of size m it will return exactly abs(m-n) values. If you need the crosscorrelation of two buffers of similar size, you will need to pad one of them with zeros first.

*in*
:   *input*
:   *as* not required
:   Number of inputs: Exactly two

<!-- -->

*out*
:   *output*
:   *as* not required

### differentiate

Performs a simple differentiation of a single input by calculating the difference of consecutive elements. It will write the result to the output buffer with exactly one value less than there are values in the input buffer.

*in*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*out*
:   *output*
:   *as* not required

### fft

This module will perform a fast fourier transform of a complex input and will write the complex result to the output buffers. For input and output the complex data is defined by two buffers *re* and *im* corresponding to the real and imaginary part. The *imaginary* buffer is optional and will be filled with zeros if omitted. This module will return as many values as provided by the input buffer.

*re*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

*im*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*re*
:   *output*
:   *as* not required

*im*
:   *output*
:   *as* required

### gausssmooth

This module will smooth the data provided from the only input. The data of each point will be calculated from neighbouring points with a gaussian distribution. The width of this distribution can be controlled by the attribute *sigma* and is interpreted in terms of value indices. This module will output as many values as there are values in the input buffer.

*sigma*
:   *attribute*
:   *optional*, default: 3.0

<!-- -->

*in*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*out*
:   *output*
:   *as* not required

### interpolate

Interpolate input data. It takes x and y values from the source data and a buffer with x values at which to interpolate the y input data. The attribute *method* determines the method for interpolation, which can be *previous* (the y value corresponding to the x value immediately preceeding the x value at which the data is to be interpolated), *next* (the y value corresponding to the x value immediately succeeding the x value at which the data is to be interpolated), *nearest* (the y value corresponding to the nearest x value to the x value at which the data is to be interpolated) and *linear* (the y is interpolated linearly). In all cases, the first or the last y value is simply reused if the evaluated x value is entirely outside the range of the input x values.

Note that both, x and xi need to be monotic (i.e. ordered).

*method*
:   *attribute*
:   *optional*, default: linear
:   can be *previous*, *next*, *nearest* or *linear*

<!-- -->

*x*
:   *input*
:   *as* required
:   Number of inputs: Exactly one
:   Source data x values

<!-- -->

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one
:   Source data y values

<!-- -->

*xi*
:   *input*
:   *as* required
:   Number of inputs: Exactly one
:   x values at which output should be calculated

<!-- -->

*out*
:   *output*
:   *as* not required

### integrate

Performs a simple integration of a single input by summing all elements and returning each step of the summation as a value. It will write as many values as there are values in the input buffer. So, if the input is a three-value array \[v1, v2, v3\], the output will be \[v1, v1+v2, v1+v2+v3\].

*in*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*out*
:   *output*
:   *as* not required

### loess

Smooths data using locally estimated scatterplot smoothing (LOESS) aka local regression. It takes x and y data as well as a list of x values at which to generate smoothed y values. Additionally, you have to set the width of the windowing function (tri-cubic window). Smoothed data can be generated at the same x positions as the source data or anywhere as long as it is near the source data, so that it contributes within the window width. The data does not need to be ordered.

Optionally, you can use three outputs to directly get the local fit parameters yi0, yi1 and yi2 to the function y(x) = yi0 + yi1 \* x + yi2 \* x². In this formula, the axis for x is shifted such that x=0 is in place of the evaluated position xi. If the input is position data versus time, these parameters are great estimates for a (smoothed) position, the momentary velocity and the momentary acceleration. Note, that if you describe the location as a function of time from an initial location, velocity and acceleration, you would have the formula y(t) = y0 + v\*t + 1/2 a\*t², so if you want to extract location y0, velocity v and acceleration a from the fit parameters, you need to multiply the yi2 by two as yi2 = a/2.

*x*
:   *input*
:   *as* required
:   Number of inputs: Exactly one
:   Source data x values

<!-- -->

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one
:   Source data y values

<!-- -->

*d*
:   *input*
:   *as* required
:   Number of inputs: Exactly one
:   Width of the tri-cubic weighting window

<!-- -->

*xi*
:   *input*
:   *as* required
:   Number of inputs: Exactly one
:   x values at which output should be calculated

<!-- -->

*yi0*
:   *output*
:   *as* not required
:   Default output that corresponds to a smoothed curve.

<!-- -->

*yi1*
:   *output*
:   *as* required
:   Linear parameter of the fit (i.e. velocity for position data).

<!-- -->

*yi2*
:   *output*
:   *as* required
:   Square parameter of the fit (i.e. acceleration for position data).

### periodicity

Mathematically, this module is similar to the autocorrelation module, but is meant to analyse large amounts of data in small subsets. The output is the periodicity of each subset and the x location of this subset. The typical use is a time-based frequency analysis. You put in the recording of a (single frequency) musical melody and the output will be the frequencies as a function of time.

The *x* and *y* inputs take the data to be analyzed and you also need to define a step size *dx* in units of samples. This means, that the data will be split into subsets \[0..dx-1\], \[dx..2dx-1\], \[2dx..3dx-1\], etc. Optionally, you may define an *overlap*, describing the number of samples taken into the calculation from before and after the subset (hence, used in multiple subsets).

The algorithm expects the autocorrelation to be periodic. It looks for the first offset i0 at which it becomes negative and then searches for a maximum in the next positive period at 3\*i0..5\*i0. You may define an offset range (in samples) by setting *min* and/or *max*. If you do so, the algorithm will just search for a maximum between *min* and *max*. If you can set this range quite narrow, this will speed up the calculation vastly, but if min/max cover multiple periods, this will quite certainly be slower and give wrong results.

While all parameters are defined in samples, the resulting output *time* will be in units of the input *x*.

*x*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*dx*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*overlap*
:   *input*
:   *as* required
:   Number of inputs: One or none

*min*
:   *input*
:   *as* required
:   Number of inputs: One or none

*max*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*time*
:   *output*
:   *as* required

*period*
:   *output*
:   *as* required

## Buffer operations

### append

This module appends all the values of the input buffers to a single output buffer. The order of the buffers will match the order their values appear in the output buffer. This module will return as many value as the sum of the input buffer sizes.

*in*
:   *input*
:   *as* not required
:   *type="empty"* allowed
:   Number of inputs: At least one

<!-- -->

*out*
:   *output*
:   *as* not required

### count

**Available since phyphox file format 1.2 (phyphox 1.0.3)**

Returns the number of values in the input buffer

*buffer*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*count*
:   *output*
:   *as* not required

### eventstream

**Available since phyphox file format 1.18 (phyphox 1.1.16)**

This is a convenient and faster substitute for stopwatch implementations like it is used in the acoustic stopwatch. The idea is to detect events in a stream of data according to a given criterion and the index of each event within the input data stream is written to the output. The eventstream module also has multiple matching inputs and outputs to keep track of the status between multiple iterations of the analysis cycle.

The inputs that determine its behavior are *data* (the input data stream), *threshold* (with a slightly varying meaning according to the chosen *mode*) and *distance* (the minimum number of values before the next event may be detected).

Furthermore it takes *index*, *skip* and *last* as inputs. These represent the *index* (nth sample) of the data within a stream, the number of values to be skipped before the first event (typically the remainder of the last *distance* from the previous block in the last analysis cycle) and the *last* value from the previous data block in case it is needed to determine the criterion (for example a difference between consecutive values). For most purposes it should be enough to assign a data container for each of *index*, *skip* and *last* and attach it to the matching inputs AND outputs.

The output is mainly *events* which will hold the indices of detected events. Additionally, there are also index, skip und last as outputs, corresponding to the inputs.

The criterion is set by the attribute "mode" determining whether raw values, derivatives or absolutes are used for triggering:

*mode*
:   *attribute*
:   *optional*, determines the criterion for an event:

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

*data*
:   *input*
:   *as* required
:   Number of inputs: At least one

<!-- -->

*threshold*
:   *input*
:   *as* required
:   Number of inputs: One or none, defaults to 0

<!-- -->

*distance*
:   *input*
:   *as* required
:   Number of inputs: One or none, defaults to 0

<!-- -->

*index*
:   *input*
:   *as* required
:   Number of inputs: One or none, defaults to 0

<!-- -->

*skip*
:   *input*
:   *as* required
:   Number of inputs: One or none, defaults to 0

<!-- -->

*last*
:   *input*
:   *as* required
:   Number of inputs: One or none, defaults to NaN

<!-- -->

*events*
:   *output*
:   *as* required

<!-- -->

*index*
:   *output*
:   *as* required

<!-- -->

*skip*
:   *output*
:   *as* required

<!-- -->

*last*
:   *output*
:   *as* required

### first

Retrieves the first entry of each buffer and appends it to each output buffer.

*value*
:   *input*
:   *as* not required
:   Number of inputs: At least one

<!-- -->

*first*
:   *output*
:   *as* not required
:   **Multiple may be defined!**

### match

This module takes multiple inputs and match valid values to the same number of outputs. The module will go through all inputs simultaneously and only return those value for which **all** inputs have a finite value.

If for example input1 provides \[1, 2, NaN, 4, 5\] and input2 provides \[11, +Inf, 13, 14\], the result will be \[1, 4\] for output1 and \[11, 14\] for output2. The other value pairs (more than two inputs are allowed though) were filtered as one of both inputs was infinite, not a number ("NaN") or just did not have any more values.

*in*
:   *input*
:   *as* not required
:   Number of inputs: At least one

<!-- -->

*out*
:   *output*
:   *as* not required
:   **Multiple may be defined!**

### map

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

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

*zMode*
:   *attribute*
:   *optional*, determines how the z data is produced from the input points, *average* averages all z values in a grid point, *count* counts the number of values (no z data has to be provided here) for each point and "sum" adds up all z values of a grid point, default: average

<!-- -->

*mapWidth*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*minX*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*maxX*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*mapHeight*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*minY*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*maxY*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*x*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*z*
:   *input*
:   *as* required
:   Number of inputs: One or none.

<!-- -->

*x*
:   *output*
:   *as* required
:   Number of inputs: Exactly one.

*y*
:   *output*
:   *as* required
:   Number of inputs: Exactly one.

*z*
:   *output*
:   *as* required
:   Number of inputs: Exactly one.

### max

Returns the maximum and its position. This module takes at least one input *y* and looks for the maximum of this buffer, but may also take a second input *x*. If *x* is defined, it will return the position of this maximum in terms of the associated x value. If *x* is not defined, position will be the index of the maximum.

If you want to find multiple local maxima, you can set the attribute "multiple" to true. In this case a third input may be used, which provides a threshold. The algorithm will split the data into sets that are entirely above the threshold and return a maximum and position for each set.

This module will return exactly one value per call if multiple is deactivated (default).

*x*
:   *input*
:   *as* required
:   Number of inputs: One or none

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*threshold*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*max*
:   *output*
:   *as* required

*position*
:   *output*
:   *as* required

### min

Returns the minimum and its position. This module takes at least one input *y* and looks for the minimum of this buffer, but may also take a second input *x*. If *x* is defined, it will return the position of this minimum in terms of the associated x value. If *x* is not defined, position will be the index of the minimum.

If you want to find multiple local minima, you can set the attribute "multiple" to true. In this case a third input may be used, which provides a threshold. The algorithm will split the data into sets that are entirely above the threshold and return a minimum and position for each set.

This module will return exactly one value per call if multiple is deactivated (default).

*x*
:   *input*
:   *as* required
:   Number of inputs: One or none

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*threshold*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*min*
:   *output*
:   *as* required

*position*
:   *output*
:   *as* required

### rangefilter

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

*in*
:   *input*
:   *as* not required
:   Number of inputs: At least one

*min*
:   *input*
:   *as* required
:   Number of inputs: One or none per *in* input. This always refers to the previously defined *in* buffer.

*max*
:   *input*
:   *as* required
:   Number of inputs: One or none per *in* input. This always refers to the previously defined *in* buffer.

<!-- -->

*out*
:   *output*
:   *as* not required
:   **Multiple may be defined!**

### reduce

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

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

*averageX*
:   *attribute*
:   *optional*, x values will be averaged to produce x output values, default: false

*averageY*
:   *attribute*
:   *optional*, y values will be averaged to produce y output values, default: false

*sumY*
:   *attribute*
:   *optional*, the y output values will be the sum of the original y value, default: false

<!-- -->

*factor*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*x*
:   *input*
:   *as* required
:   Number of inputs: Exactly one.

*y*
:   *input*
:   *as* required
:   Number of inputs: One or none.

<!-- -->

*x*
:   *output*
:   *as* required
:   Number of inputs: Exactly one.

*y*
:   *output*
:   *as* required
:   Number of inputs: One or none.

### sort

This module takes at least one input and sorts it. Values in additional inputs will follow the sorting of the first input buffer. By default, the values in the first buffer will be sorted in ascending order. This can be reversed with the attribute *descending*.

The number of values returned matches the number of values in the shortest buffer.

*descending*
:   *attribute*
:   *optional*, default: false

<!-- -->

*in*
:   *input*
:   *as* not required
:   Number of inputs: At least one
:   The first input will determine the order of all values

<!-- -->

*out*
:   *output*
:   *as* not required

### split

**Available since phyphox file format 1.18 (phyphox 1.1.16)**

Takes *data* as input and splits it into two buffers at the given *index*. A third parameter *overlap* allows to set a number of elements from before the split index that will also end up in the second buffer. *index* defaults to the length of the input data if not given, i.e. the entire input is returned as the first output without any splitting, which only makes sense in combination with an overlap, for example to take all data from a buffer associated with the input from a sensor and setting "overlap" such that a certain number of values is retained as a starting point for the next iteration.

*data*
:   *input*
:   *as* required
:   Number of inputs: At least one
:   The buffer that should be split and sent to the outputs

<!-- -->

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

*out1*
:   *output*
:   *as* not required
:   Buffer that receives the first part of the original data.

<!-- -->

*out2*
:   *output*
:   *as* not required
:   Buffer that receives the second part of the original data.

### subrange

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

*from*
:   *input*
:   *as* required
:   Number of inputs: One or none. Defaults to 0

<!-- -->

*to*
:   *input*
:   *as* required
:   Number of inputs: One or none. Defaults to length of input

<!-- -->

*length*
:   *input*
:   *as* required
:   Number of inputs: One or none. Defaults to length of input, supersedes *to*

<!-- -->

*in*
:   *input*
:   *as* not required
:   Number of inputs: At least one

<!-- -->

*out*
:   *output*
:   *as* not required
:   **Multiple may be defined!**

### threshold

This module takes at least one input *y* and looks for position at which the values cross a given threshold. the input *threshold* is interpreted as a single value (last added element). This module may also take a third input *x*. If *x* is defined, it will return the position of the crossing in terms of the associated x value. If *x* is not defined, position will be the index of the crossing.

You can also define the attribute *falling* as true to search for a crossing from larger to smaller values.

This module will return exactly one value per call.

*falling*
:   *attribute*
:   *optional*, default: false

<!-- -->

*x*
:   *input*
:   *as* required
:   Number of inputs: One or none

*y*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*threshold*
:   *input*
:   *as* required
:   Number of inputs: One or none (defaults to 0.0)

<!-- -->

*position*
:   *output*
:   *as* not required

## Data generation

### const

This module will initialize a buffer to a constant value. Both inputs are optional and without any inputs it will fill the entire buffer with zero. If *value* is set, the buffer gets filled with this value and if *length* is set, only *length* values will be initialized. (This is usefull in combination with the *append* module to zero-pad a buffer.)

*value*
:   *input*
:   *as* required
:   Number of inputs: One or none

*length*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*out*
:   *output*
:   *as* not required

### ramp

This module will create a ramp of values, i.e. a linear range of values. This is very usefull to create time bases for example for audio recordings. The module takes as inputs *start*, *stop* and the optional *length*. It will make that the first value is exactly *start* and the last value is *stop*. It will return *length* values or if *length* is not provided as many values as the size of the output buffer.

*start*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*stop*
:   *input*
:   *as* required
:   Number of inputs: Exactly one

*length*
:   *input*
:   *as* required
:   Number of inputs: One or none

<!-- -->

*out*
:   *output*
:   *as* not required

### timer

Simple module which outputs the (fractional) seconds that have past since the experiment started (referred to as "experiment time") and the current analysis run began. By default, experiment time does not increase while the experiment is paused and will continue with barely any gap when the experiment is resumed. Alternatively, you can set the attribute `linearTime` to `true` to output "linear time" instead which is almost identical to experiment time but keeps increasing while the experiment is paused.

The timer module has a second output that gives the offset between the given time (experiment or linear time) and the widely used Unix timestamp which is seconds since 01.01.1970.

*linearTime*
:   *attribute*
:   optional, default: false, **Available since phyphox file format 1.12 (phyphox 1.1.8)**

*out*
:   *output*
:   *as* not required

*offset1970*
:   *output*
:   *as* required, **Available since phyphox file format 1.12 (phyphox 1.1.8)**

### info

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

The info module is used as a generic way to access system information like the device's battery level. This is typically data that only has a use-case in few specific applications and that cannot reasonably be considered as a sensor. It's more about metadata for the experiment (although this of course is not a precise criterium).

The module has no attributes, but several outputs, which are all optional and determine the system information to be retrieved:

*batteryLevel*
:   *output*
:   *as* required

Current battery level of the device that runs phyphox.

*wifiSignalStrength*
:   *output*
:   *as* required

Signal strength of the current wifi connection. (Only available on Android.)

*systemVolume*
:   *output*
:   *as* required

Volume of the audio output (playback audio stream).

*batteryVoltage*
:   *output*
:   *as* required

Current battery voltage of the device that runs phyphox. (Only available on Android.) **Available since phyphox file format 1.20 (phyphox 1.2.1)**

*batteryCurrent*
:   *output*
:   *as* required

Current battery current of the device that runs phyphox. Android's convention is that positive values are charging the battery, but there have been reports of devices not following that convention correctly. (Only available on Android.) **Available since phyphox file format 1.20 (phyphox 1.2.1)**

*batteryTemperature*
:   *output*
:   *as* required

Current battery temperature of the device that runs phyphox. (Only available on Android.) **Available since phyphox file format 1.20 (phyphox 1.2.1)**

## Logic

### if

**Available since phyphox file format 1.3 (phyphox 1.0.4)**

The if module is the phyphox equivalent to the if-statement of a programming language. It takes two inputs a and b and will behave differently depending on the relation of the last values found there. By changing the attributes *less*, *equal* or *greater*, you can decide whether you are looking for a \< b, a = b or a \> b, respectively. If the relation is true, the if-module will write the data from the input *true* to the output, otherwise it will write the data from the input *false*. If you enable multiple attributes, the input *true* is used if any of them is fulfilled, so if you enable *less* and *equal*, a \<= b will write the *true* input to the output, while a \> b writes the *false* input.

Since version 1.4 (phyphox 1.0.6) you may set an input to be of the type *empty*. Effectively, this does not change the output as nothing is written, but can make sense in combination with setting the output to *clear*. In this case, the if module behaves somewhat special as it only clears its output if a matching input is connected. For example if you set the true input to *empty*, do not connect the false input and set the output to *clear*, it will only clear the output if the condition is true, but leaves it alone otherwise. This can be used as a reset condition. Note, that since the visual editor does not support reusing buffers, you probably cannot do this there in a reasonable way...

*less*
:   *attribute*
:   *optional*, default: false

*equal*
:   *attribute*
:   *optional*, default: false

*greater*
:   *attribute*
:   *optional*, default: false

<!-- -->

*a*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

*b*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

*true*
:   *input*
:   *as* not required
:   *type="empty"* allowed
:   Number of inputs: Exactly one

*false*
:   *input*
:   *as* not required
:   *type="empty"* allowed
:   Number of inputs: Exactly one

<!-- -->

*out*
:   *output*
:   *as* not required

## Other

### imagedecode

**Available since phyphox file format 1.20 (phyphox 1.2.1)**

This module takes the input data as a stream of bytes encoded by the values 0 to 255. The data is decoded using the operating system's image decoding class, which should support PNG, JPEG and BMP data as a minimum. As output the decoded image data becomes available as red (r), green (g), blue (b), alpha (a), luma and luminance channels (Rec. 709) with each value encoded in the range 0 to 1. The outputs receive one value per pixel line-wise starting from the top. Additionally, the outputs *width* and *height* receive width and height in pixels respectively.

This module can be used to transfer image files via Bluetooth or network interface and then decode them for further processing or display in a color map graph.

*in*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*width*
:   *output*
:   *as* required

*height*
:   *output*
:   *as* required

*r*
:   *output*
:   *as* required

*g*
:   *output*
:   *as* required

*b*
:   *output*
:   *as* required

*a*
:   *output*
:   *as* required

*luma*
:   *output*
:   *as* required

*luminance*
:   *output*
:   *as* required
