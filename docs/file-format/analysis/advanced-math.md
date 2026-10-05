# Advanced math

The `<input>` and `<output>` tags of every module on this page additionally accept the [attributes common to all analysis modules](index.md#analysis-modules-in-general).

## autocorrelation

This module will calculate the autocorrelation. It takes at least one input buffer *y*, but can take a second input *x* as well. If *x* is omitted, it will be filled with indices. Additionally, single value inputs *minX* and *maxX* can be set as well. These restrict the output to the given x range. Without them the module returns as many values as provided by the input buffer; with them only the lags within the range are returned. The output buffer *y* is filled with the autocorrelation of the *y* input buffer, each lag divided by the number of samples that overlap at that lag - so the value at lag zero is the mean square of the input, not 1. The *x* output buffer is optional; if connected, it will be filled with the relative *x* of the autocorrelation based on the *x* input buffer.

{{spec:analysis/analysis/autocorrelation}}

## butterworth

This module represents the transfer function of a Butterworth filter. It takes the order *n* and (upper) *cutoff* frequency as inputs and acts as a low pass. Optionally, you can also provide a positive lower cutoff frequency as *cutoffLow*, in which case it acts as a bandpass (a *cutoffLow* of zero keeps it a low pass). The *x* input needs to provide frequencies for each data point of the *y* input. Frequencies are taken as absolute values for the filter. The module multiplies the *y* values by the magnitude of the filter's transfer function at their frequencies, so you want to use it together with the *fft* module.

{{spec:analysis/analysis/butterworth}}

## crosscorrelation

This module will calculate a crosscorrelation of two inputs. It will only calculate offsets at which the smaller buffer is entirely covered by the larger one, leaving out the last such offset. So with one input buffer of size n and one input of size m it will return exactly abs(m-n) values. If you need the crosscorrelation of two buffers of similar size, you will need to pad one of them with zeros first.

The output values are the raw correlation sums without any normalization, matching the default of numpy.correlate, scipy.signal.correlate and MATLAB xcorr. Any empty input yields an empty output.

{{spec:analysis/analysis/crosscorrelation}}

## Fourier transforms

Four modules transform between a signal and its spectrum: *fft* and *dft* compute the forward transform, *ifft* and *idft* the inverse. They share one interface and one set of conventions, so a spectrum computed by one module can be transformed back by any inverse module. They differ in what they promise about the input length:

- **fft** and **ifft** use the fastest transform each platform offers. Only a **power-of-two** number of input samples is guaranteed to give identical results on both platforms; for any other length the output is implementation-defined and differs between platforms.
- **dft** and **idft** are the exact transforms for **any length**: N input samples give exactly N output values on every platform. They are slower than fft for lengths that are not a power of two, which is rarely a concern for the buffer sizes of a phone experiment, and the right choice whenever the buffer length is not under the experiment's control. Both are available since file format 1.21.

For a power-of-two length fft and dft (and ifft and idft) give the same result.

**Complex data.** Input and output are complex, each given as two buffers *re* and *im* for the real and the imaginary part. The *im* input is optional and filled with zeros if omitted; the full complex spectrum is returned either way, not a shortened real-input half, so a real signal of N samples gives N bins with the upper half mirroring the lower. A *provided* *im* input truncates the transform to the shorter of *re* and *im*. Both outputs are optional as well; omit *im* on the inverse of a spectrum that stems from a real signal.

**Kernel.** With N the transform length, the forward modules compute

    X[k] = s · Σ x[n] · e^(−2πi·k·n/N)        (sum over n = 0 … N−1)

and the inverse modules compute

    x[n] = s · Σ X[k] · e^(+2πi·k·n/N)        (sum over k = 0 … N−1)

so bin k of the forward transform belongs to the frequency k · (sample rate) / N, and bins above N/2 are the negative frequencies.

**Normalization.** The factor s is set by the *normalization* attribute, the same attribute with the same values on all four modules. It names which of the two directions carries the 1/N factor, as in NumPy and SciPy:

| *normalization* | forward (fft, dft) | inverse (ifft, idft) | round trip |
|---|---|---|---|
| `backward` (default) | 1 | 1/N | returns the input |
| `forward` | 1/N | 1 | returns the input |
| `ortho` | 1/√N | 1/√N | returns the input; both transforms are unitary |
| `none` | 1 | 1 | returns N times the input |

The default is the convention of NumPy, SciPy, MATLAB and FFTW: an unscaled forward transform and an inverse divided by N. For the forward modules it is exactly what *fft* has always produced, so existing experiments are unchanged; for the inverse modules it means *ifft* after *fft* (or *idft* after *dft*) returns the input. Use `forward` when a bin should hold the amplitude of its frequency component directly (for a real signal, half of it in each of the two mirrored bins), `ortho` when the sum of squared magnitudes must be preserved (Parseval), and `none` when the experiment applies its own scaling - for the forward modules `none` is the same as `backward`, for the inverse modules the same as `forward`.

Like every enumerated attribute the value is matched without regard to case, and an unknown value refuses the file.

```xml
<fft normalization="forward">
    <input as="re">signal</input>
    <output as="re">spectrumRe</output>
    <output as="im">spectrumIm</output>
</fft>
<ifft normalization="forward">
    <input as="re">spectrumRe</input>
    <input as="im">spectrumIm</input>
    <output as="re">signalBack</output>
</ifft>
```

## dft

The discrete Fourier transform of a complex input of **any length**, written as complex output of exactly that length: N samples in, N bins out, on every platform. See [Fourier transforms](#fourier-transforms) for the interface, the kernel and the *normalization* attribute, all of which it shares with *fft*. An empty input gives an empty output; a single sample is returned unchanged (the transform of length one is the identity).

The module is free to use any algorithm (a direct sum, Bluestein's algorithm or a mixed-radix FFT); what it promises is the exact transform within floating-point tolerance. It is slower than *fft* for lengths that are not a power of two and equal to it for lengths that are.

{{spec:analysis/analysis/dft}}

## differentiate

Performs a simple differentiation of a single input by calculating the difference of consecutive elements. It will write the result to the output buffer with exactly one value fewer than there are values in the input buffer.

{{spec:analysis/analysis/differentiate}}

## fft

The fast Fourier transform of a complex input, written as complex output. See [Fourier transforms](#fourier-transforms) for the interface, the kernel and the *normalization* attribute, all of which it shares with *dft*, *ifft* and *idft*.

Provide a **power-of-two** number of input samples: only then is the output guaranteed to be identical on both platforms. This lets the module use the fastest transform each platform offers. For other input lengths the result is implementation-defined and differs between platforms; use *dft*, the exact transform of any length, for those cases. A single input sample is returned unchanged, as the transform of length one is the identity.

{{inconsistency:fft-non-power-of-two-input}}

{{spec:analysis/analysis/fft}}

## gausssmooth

This module will smooth the data provided from the only input. The data of each point will be calculated from neighboring points with a Gaussian distribution. The width of this distribution can be controlled by the attribute *sigma* and is interpreted in terms of value indices. An omitted or empty *sigma* attribute selects the default of 3; a present value must be greater than zero. This module will output as many values as there are values in the input buffer.

{{spec:analysis/analysis/gausssmooth}}

## idft

The inverse discrete Fourier transform of a complex spectrum of **any length**, written as complex output of exactly that length - the inverse of *dft*, with the opposite sign in the kernel and, under the default *normalization*, divided by N, so *idft* after *dft* returns the input. See [Fourier transforms](#fourier-transforms) for the interface and the conventions. Like *dft* it is exact for every length on every platform; an empty input gives an empty output.

{{spec:analysis/analysis/idft}}

## ifft

The inverse fast Fourier transform of a complex spectrum - the inverse of *fft*, with the opposite sign in the kernel and, under the default *normalization*, divided by N, so *ifft* after *fft* returns the input. See [Fourier transforms](#fourier-transforms) for the interface and the conventions.

It carries the same guarantee as *fft*: only a **power-of-two** number of input samples (the length of the spectrum) is guaranteed to give identical results on both platforms, any other length is implementation-defined - use *idft* for those. A spectrum of a single bin is returned unchanged, like a single sample by [fft](#fft).

{{spec:analysis/analysis/ifft}}

## interpolate

Interpolates input data. It takes x and y values from the source data and a buffer with x values at which to interpolate the y input data. The attribute *method* determines the method for interpolation, which can be *previous* (the y value corresponding to the x value immediately preceding the x value at which the data is to be interpolated), *next* (the y value corresponding to the x value immediately succeeding the x value at which the data is to be interpolated), *nearest* (the y value corresponding to the nearest x value to the x value at which the data is to be interpolated) and *linear* (the y value is interpolated linearly). In all cases, the first or the last y value is simply reused if the evaluated x value is entirely outside the range of the input x values.

Note that both x and xi need to be monotonic (i.e. ordered).

{{spec:analysis/analysis/interpolate}}

## integrate

Performs a simple integration of a single input by summing all elements and returning each step of the summation as a value. It will write as many values as there are values in the input buffer. So, if the input is a three-value array \[v1, v2, v3\], the output will be \[v1, v1+v2, v1+v2+v3\].

{{spec:analysis/analysis/integrate}}

## loess

Smooths data using locally estimated scatterplot smoothing (LOESS) aka local regression. It takes x and y data as well as a list of x values at which to generate smoothed y values. Additionally, you have to set the width of the windowing function (tri-cubic window). Smoothed data can be generated at the same x positions as the source data or anywhere as long as it is near the source data, so that it contributes within the window width. Both the x data and the xi values need to be monotonically increasing.

Optionally, you can use three outputs to directly get the local fit parameters yi0, yi1 and yi2 to the function y(x) = yi0 + yi1 \* x + yi2 \* x². In this formula, the axis for x is shifted such that x=0 is in place of the evaluated position xi. If the input is position data versus time, these parameters are great estimates for a (smoothed) position, the momentary velocity and the momentary acceleration. Note that if you describe the location as a function of time from an initial location, velocity and acceleration, you would have the formula y(t) = y0 + v\*t + 1/2 a\*t², so if you want to extract location y0, velocity v and acceleration a from the fit parameters, you need to multiply yi2 by two as yi2 = a/2.

The window width *d* is read as a single value (last added element of its buffer); a non-positive or non-finite *d* is an error yielding empty outputs.

{{spec:analysis/analysis/loess}}

## periodicity

Mathematically, this module is similar to the autocorrelation module, but is meant to analyze large amounts of data in small subsets. The output is the periodicity of each subset and the x location of this subset. The typical use is a time-based frequency analysis. You put in the recording of a (single frequency) musical melody and the output will be the frequencies as a function of time.

The *x* and *y* inputs take the data to be analyzed and you also need to define a step size *dx* in units of samples. This means that the data will be split into subsets \[0..dx-1\], \[dx..2dx-1\], \[2dx..3dx-1\], etc. Optionally, you may define an *overlap*, describing the number of samples taken into the calculation from before and after the subset (hence, used in multiple subsets).

The algorithm expects the autocorrelation to be periodic. It looks for the first offset i0 at which it becomes negative and then searches for a maximum in the next positive period at 3\*i0..5\*i0. You may define an offset range (in samples) by setting *min* and/or *max*. If you do so, the algorithm will just search for a maximum between *min* and *max*. If you can set this range quite narrow, this will speed up the calculation vastly, but if min/max cover multiple periods, this will quite certainly be slower and give wrong results.

While all parameters are defined in samples, the resulting output *time* will be in units of the input *x*. A non-positive, non-finite or empty *dx* yields empty outputs. Fractional bounds are treated conservatively: *min* is rounded down and *max* is rounded up, so periods on the boundary are included in the search.

{{spec:analysis/analysis/periodicity}}
