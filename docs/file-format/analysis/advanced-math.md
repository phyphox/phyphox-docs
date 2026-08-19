# Advanced math

## autocorrelation

This module will calculate the autocorrelation. It takes at least one input buffer *y*, but can take a second input *x* as well. If *x* is omitted, it will be filled with indices. Additionally, single value inputs *minX* and *maxX* can be set as well. These restrict the output to the given x range. Without them the module returns as many values as provided by the input buffer; with them only the lags within the range are returned. The output buffer *y* is filled with the autocorrelation of the *y* input buffer, each lag divided by the number of samples that overlap at that lag - so the value at lag zero is the mean square of the input, not 1. The *x* output buffer will be filled with the relative *x* of the autocorrelation based on the *x* input buffer.

{{inconsistency:autocorrelation-omitted-x-output}}

{{spec:analysis/analysis/autocorrelation}}

## butterworth

This module represents the transfer function of a Butterworth filter. It takes the order *n* and (upper) *cutoff* frequency as inputs and acts as a low pass. Optionally, you can also provide a positive lower cutoff frequency as *cutoffLow*, in which case it acts as a bandpass (a *cutoffLow* of zero keeps it a low pass). The *x* input needs to provide frequencies for each data point of the *y* input. Frequencies are taken as absolute values for the filter. The module multiplies the *y* values by the magnitude of the filter's transfer function at their frequencies, so you want to use it together with the *fft* module.

{{spec:analysis/analysis/butterworth}}

## crosscorrelation

This module will calculate a crosscorrelation of two inputs. It will only calculate offsets at which the smaller buffer is entirely covered by the larger one, leaving out the last such offset. So with one input buffer of size n and one input of size m it will return exactly abs(m-n) values. If you need the crosscorrelation of two buffers of similar size, you will need to pad one of them with zeros first.

{{inconsistency:crosscorrelation-normalization}}

{{spec:analysis/analysis/crosscorrelation}}

## differentiate

Performs a simple differentiation of a single input by calculating the difference of consecutive elements. It will write the result to the output buffer with exactly one value fewer than there are values in the input buffer.

{{spec:analysis/analysis/differentiate}}

## fft

This module will perform a fast Fourier transform of a complex input and will write the complex result to the output buffers. For input and output the complex data is defined by two buffers *re* and *im* corresponding to the real and imaginary part. The *imaginary* buffer is optional and will be filled with zeros if omitted (the full complex spectrum is returned either way, not a shortened real-input half).

Provide a **power-of-two** number of input samples: only then is the output guaranteed to be identical on both platforms. This lets the module use the fastest transform each platform offers. For other input lengths the result is implementation-defined and differs between platforms; a separate general-purpose `dft` module (slower, exact input length) is planned for those cases.

{{inconsistency:fft-non-power-of-two-input}}

{{inconsistency:fft-imaginary-input-length}}

{{spec:analysis/analysis/fft}}

## gausssmooth

This module will smooth the data provided from the only input. The data of each point will be calculated from neighboring points with a Gaussian distribution. The width of this distribution can be controlled by the attribute *sigma* and is interpreted in terms of value indices. This module will output as many values as there are values in the input buffer.

{{inconsistency:gausssmooth-empty-sigma}}

{{spec:analysis/analysis/gausssmooth}}

## interpolate

Interpolates input data. It takes x and y values from the source data and a buffer with x values at which to interpolate the y input data. The attribute *method* determines the method for interpolation, which can be *previous* (the y value corresponding to the x value immediately preceding the x value at which the data is to be interpolated), *next* (the y value corresponding to the x value immediately succeeding the x value at which the data is to be interpolated), *nearest* (the y value corresponding to the nearest x value to the x value at which the data is to be interpolated) and *linear* (the y value is interpolated linearly). In all cases, the first or the last y value is simply reused if the evaluated x value is entirely outside the range of the input x values.

Note that both x and xi need to be monotonic (i.e. ordered).

{{inconsistency:value-type-inputs-rejected-by-ios}}

{{spec:analysis/analysis/interpolate}}

## integrate

Performs a simple integration of a single input by summing all elements and returning each step of the summation as a value. It will write as many values as there are values in the input buffer. So, if the input is a three-value array \[v1, v2, v3\], the output will be \[v1, v1+v2, v1+v2+v3\].

{{spec:analysis/analysis/integrate}}

## loess

Smooths data using locally estimated scatterplot smoothing (LOESS) aka local regression. It takes x and y data as well as a list of x values at which to generate smoothed y values. Additionally, you have to set the width of the windowing function (tri-cubic window). Smoothed data can be generated at the same x positions as the source data or anywhere as long as it is near the source data, so that it contributes within the window width. Both the x data and the xi values need to be monotonically increasing.

Optionally, you can use three outputs to directly get the local fit parameters yi0, yi1 and yi2 to the function y(x) = yi0 + yi1 \* x + yi2 \* x². In this formula, the axis for x is shifted such that x=0 is in place of the evaluated position xi. If the input is position data versus time, these parameters are great estimates for a (smoothed) position, the momentary velocity and the momentary acceleration. Note that if you describe the location as a function of time from an initial location, velocity and acceleration, you would have the formula y(t) = y0 + v\*t + 1/2 a\*t², so if you want to extract location y0, velocity v and acceleration a from the fit parameters, you need to multiply yi2 by two as yi2 = a/2.

{{inconsistency:loess-parameter-edges}}

{{inconsistency:value-type-inputs-rejected-by-ios}}

{{spec:analysis/analysis/loess}}

## periodicity

Mathematically, this module is similar to the autocorrelation module, but is meant to analyze large amounts of data in small subsets. The output is the periodicity of each subset and the x location of this subset. The typical use is a time-based frequency analysis. You put in the recording of a (single frequency) musical melody and the output will be the frequencies as a function of time.

The *x* and *y* inputs take the data to be analyzed and you also need to define a step size *dx* in units of samples. This means that the data will be split into subsets \[0..dx-1\], \[dx..2dx-1\], \[2dx..3dx-1\], etc. Optionally, you may define an *overlap*, describing the number of samples taken into the calculation from before and after the subset (hence, used in multiple subsets).

The algorithm expects the autocorrelation to be periodic. It looks for the first offset i0 at which it becomes negative and then searches for a maximum in the next positive period at 3\*i0..5\*i0. You may define an offset range (in samples) by setting *min* and/or *max*. If you do so, the algorithm will just search for a maximum between *min* and *max*. If you can set this range quite narrow, this will speed up the calculation vastly, but if min/max cover multiple periods, this will quite certainly be slower and give wrong results.

While all parameters are defined in samples, the resulting output *time* will be in units of the input *x*.

{{inconsistency:periodicity-parameter-edges}}

{{spec:analysis/analysis/periodicity}}
