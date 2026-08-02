# Data generation

## const

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

## ramp

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

## timer

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

## info

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

The info module is used as a generic way to access system information like the device's battery level. This is typically data that only has a use-case in few specific applications and that cannot reasonably be considered as a sensor. It's more about metadata for the experiment (although this of course is not a precise criterium).

The module has no attributes, but several outputs, which are all optional and determine the system information to be retrieved:

*batteryLevel*
:   *output*
:   *as* not required

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
