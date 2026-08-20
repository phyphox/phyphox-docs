# Data generation

The `<input>` and `<output>` tags of every module on this page additionally accept the [attributes common to all analysis modules](index.md#analysis-modules-in-general).

## const

This module will initialize a buffer to a constant value. Both inputs are optional, and without any inputs it will fill the entire buffer with zero. If *value* is set, the buffer gets filled with this value, and if *length* is set, only *length* values will be initialized. (This is useful in combination with the *append* module to zero-pad a buffer.)

An explicit *length* of 0, an empty length buffer and a non-finite or negative length value all yield an empty output; only an absent length input falls back to the size of the output buffer. An empty value buffer is an error yielding an empty output, while a present NaN value is allowed and fills the output with NaN as a deliberate initialization.

{{spec:analysis/analysis/const}}

## ramp

This module will create a ramp of values, i.e. a linear range of values. This is very useful to create time bases, for example for audio recordings. The module takes as inputs *start*, *stop* and the optional *length*. It will make sure that the first value is exactly *start* and the last value is *stop*. It will return *length* values or, if *length* is not provided, as many values as the size of the output buffer. A *length* of 1 outputs exactly the start value.

An empty start/stop buffer and a non-finite start or stop value are errors yielding an empty output. The *length* input behaves like const's: an explicit 0, an empty buffer and a non-finite or negative value yield an empty output; only an absent length input falls back to the size of the output buffer.

{{spec:analysis/analysis/ramp}}

## timer

Simple module which outputs the (fractional) seconds that have passed since the experiment started (referred to as "experiment time") and the current analysis run began. By default, experiment time does not increase while the experiment is paused and will continue with barely any gap when the experiment is resumed. Alternatively, you can set the attribute `linearTime` to `true` to output "linear time" instead, which is almost identical to experiment time but keeps increasing while the experiment is paused.

The timer module has a second output that gives the offset between the given time (experiment or linear time) and the widely used Unix timestamp, which is the number of seconds since 01.01.1970.

{{spec:analysis/analysis/timer}}

## info

The info module is used as a generic way to access system information like the device's battery level. This is typically data that only has a use-case in a few specific applications and that cannot reasonably be considered as a sensor. It's more about metadata for the experiment (although this of course is not a precise criterion).

The module has no attributes, but several outputs, which are all optional and determine the system information to be retrieved:

{{spec:analysis/analysis/info}}

Current battery level of the device that runs phyphox.

Signal strength of the current wifi connection. (Only available on Android.)

Volume of the audio output (playback audio stream).

Current battery voltage of the device that runs phyphox. (Only available on Android.) **Available since phyphox file format 1.20 (phyphox 1.2.1)**

Current battery current of the device that runs phyphox. Android's convention is that positive values are charging the battery, but there have been reports of devices not following that convention correctly. (Only available on Android.) **Available since phyphox file format 1.20 (phyphox 1.2.1)**

Current battery temperature of the device that runs phyphox. (Only available on Android.) **Available since phyphox file format 1.20 (phyphox 1.2.1)**
