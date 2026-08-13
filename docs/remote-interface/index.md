# Remote-interface communication

!!! info "The reference lives next door"

    This page is the introduction: what the interface is for and how the requests fit together.
    The exact description of every endpoint — parameters, response schemas, status codes — is on
    the [API reference](api-reference.md) page, generated from
    [`openapi.yaml`](openapi.yaml). That file is the authority; where this page and the reference
    disagree, the reference is right.

While the [remote interface](http://phyphox.org/remote-control/) of phyphox is a very powerful tool, you might be interested in communicating and controlling phyphox directly using your own software. The web page called by your browser when using the default remote interface is mostly based on some (not too complex) Javascript code. This code does a range of AJAX requests and receives responses in a JSON format, which are documented on this page. So, when the remote access feature is enabled, phyphox can be controlled through a REST API.

In principle, with this information, you could embed phyphox into many other projects. For example, you could write an interface to perform measurements including more than one phones with phyphox or you could include phyphox into a more capable measurement software (LabView, Labber, Matlab) or control phyphox alongside other lab equipment like programmable voltage sources or power supplies of electro magnets.

Here is a little example on how to use this interface to control musical instruments: <https://www.youtube.com/watch?v=sFx9zZKe4E4>

The [Python script](https://phyphox.org/phyphox-files/phyphox2midi.py) from this video is a quick solution specific for the MIDI interface of musical experiments, but it may be useful as a starting point for other projects.

As the interface is designed around a webserver running on the phone, all functions are available as documents below the devices URL. So, this documentation will list all these documents from the document root. For example "/get" can be called as <http://192.168.0.42:8080/get> (if the phone's IP is 192.168.0.42 and the server is running on port 8080. On iPhones, the server runs in port 80, so for http the port can usually be omitted.)

Also, if you are developing a Java application, you might want to check out this [Java interface](https://github.com/tfassbender/phyphox_java_interface) created by Tobias Faßbender, FH Aachen.

## Documents

### /, /style.css and /logo

These documents are not relevant for controlling phyphox with your own code. They make up the webpage that is the default remote interface. The document root itself serves an html file with the Javascript of the interface, while style.css and logo serve the Style Sheet and an image file of the phyphox logo.

### /get

A call to get retrieves the measured data as well as the current status of phyphox. The response is a JSON object of the following form:

```json
{"buffer": {...}, "status": {...}}
```

Both, "buffer" and "status" again are JSON objects, containing buffer data and the app status respectively. The contents of "buffer" depend on the buffer that you request as parameters to /get. For example, you can request the buffers "abc" and "def" using the request "/get?abc&def". This request, however, will only return the last value in each buffer. To receive more values, you have to specify to either retrieve the full buffer or all values beyond a certain threshold: "/get?abc=full&def=42" will return all values of buffer "abc", but only the remaining values from buffer "def" after the first value exceeding 42.

Retrieving the full buffer is straight forward, but can be quite inefficient. Instead using the threshold can save a lot of bandwidth if you only need to retrieve new data from a monotonic reference. A typical example is a time axis - you have already received data from a sensor every second as pairs of (time\|value): (1,7), (2,-1), (3,4) As you know, that "time" will always increase monotonic. So from buffer "time", you only need to request anything after the value 3: "/get?t=3". Buffer "value" is slightly more complicated as it might have any value, but you know that you only need those values at the same index as the values of "time" larger than 3. So, when giving a threshold to a buffer in the get-request, you can add a specific reference buffer: "/get?time=3&value=3\|time". If the threshold value does not belong to the requested buffer itself, you have to provide it after the threshold with the symbol "\|".

**Warning: Although this documentation uses a plain "\|", you should make sure that whatever you use to make the request properly encodes it to create a valid URL. If you need to encode it manually, you need to use "%7C" instead.**

This is necessary as values are not explicitly paired in phyphox experiment. It may be absolutely valid, that you need a subset from the "time" buffer, and the full "value" buffer, which might be unrelated. So, a last example:

```
/get?abc&def=full&ghi=42&jkl=23|mno
```

This request will return the last value of "abc", all values from "def", the values from "ghi" occuring after the first value above 42 and all values from "jkl" ocurring after the first index at which the value in buffer "mno" is larger than 23. Note, that "mno" itself is not requested.

The "buffer" JSON object in the response looks like this:

```
"buffer": {
  "abc":{"size":100, "updateMode":"partial", "buffer":[1,2,3.456E1]},
  "def":{"size":20, "updateMode":"single", "buffer":[1.222E-2]}
}
```

This response contains data for the buffers "abc" and "def". The "size" gives the total capacity of the buffer - not the number of values returned and not how much it is filled. "updateMode" can be "full", "partial" or "single", in which case you know that you have retrieved the whole buffer, a part of it or only its last value. "buffer" finally contains an array of the values returned.

The "status" JSON object contains four values:

```
"status": {
  "session":"abcdef", "measuring": true, "timedRun": true, "countDown":2700
}
```

"session" gives a string identifier which is unique per session. If this changes, you may expect that the user has switched to a different experiment and all your old data has become invalid. "measuring" gives the current state of the measurement - false means that the experiment is paused, true that it is running. "timedRun" and "countDown" represent the timed run function. **"countDown" is given in milliseconds**, so in this case it is enabled and will stop the current measurement in 2.7 seconds. If "measuring" was false, it would mean that the measurement would start in 2.7 seconds.

### /control

The document "control" is used to send commands to phyphox to start and stop the experiment. It will always respond with a simple confirmation object {"result": true} if successfull or {"result": false} if something went wrong.

Currently, there are four commands available:

/control?cmd=start starts the experiment (or the countdown if timed run is enabled)

/control?cmd=stop stops the experiment

/control?cmd=clear clears all buffer (and stops the experiment if running)

/control?cmd=set&buffer=abc&value=42 Writes the value 42 into the buffer abc (typically used for edit fields)

### /export

When requesting "export", you are effectively triggering the export function of phyphox to retrieve all recorded data in a single file. You can specify the format of this file using the index of the available formats. For example /export?format=0 will give an Excel file and /export?format=2 will give a CSV file (at the time of this writing).

### /config

**Available since [version 1.1.6](../reference/version-history/1.1.6.md)**

"config" does not take any parameters and returns a JSON structure with information on the current experiment configuration, including the following details:

crc32
:   A hex repesentation of the CRC32 of the entire experiment configuration file, useful to precisely identify a specific configuration.

title
:   Title of the experiment in its base language.

localTitle
:   Title of the experiment in the currently presented language.

category
:   Category of the experiment in its base language.

localCategory
:   Category of the experiment in the currently presented language.

buffers
:   An array of buffers in the experiment. Each entry provides the name (as usable in the /get command) and the size (defined size, not actual filled size) of each buffer. Note that there is no guarantee that they contain usable data. This will depend on the logic of the experiment as some buffers might only contain intermediate or temporary data. The *export* buffers (see below) are a much better indicator for good buffers to poll as they have been handpicked by the author of the configuration.

inputs
:   An array of inputs to the experiment. These include the microphone ("audio"), the sensors (named following the configuration naming scheme), GPS ("location") and Bluetooth. All inputs except for bluetooth will also provide information on which buffer is attached to which output. However, this will not assure that you can reliably access the data from this particular buffer as experiments might clear the buffer during analysis.

export
:   An array of export sets, which in turn contain combinations of labels and buffers. These are the buffers that have been chosen by the configuration author which should be included if the user exports the data. In properly designed experiments, these contain valid data.

### /meta

**Available since [version 1.1.8](../reference/version-history/1.1.8.md)**

{{inconsistency:meta-sensors}}

"meta" does not take any parameters and returns a JSON structure with information about the device and its software. This is all the metadata listed on the [network connections documentation](../file-format/network-connections.md#metadata) except for the unique id.

### /time

**Available since [version 1.1.8](../reference/version-history/1.1.8.md)**

"time" does not take any parameters and returns a JSON structure with information helping to synchronize the data from this device to the real world using its system clock. The result is a simle JSON array with event objects representing events during experimentation, which at the moment are start and pause, when the user started or paused the experiment. Each event entry has the experiment time (seconds since first start of the experiment, ignoring pauses) and the system time (seconds since 1970) of the event, which allows to map the timestamp of sensor data (experiment time) to the real world.

Note, that the experiment time is based on the devices high resolution clock, which runs independently of the system clock. On each event phyphox reads both clocks right after each other to get a match that should be accurate to within few milliseconds. However, as both clocks run independently, they may diverge over time and especially if the system clock is updated, which is usually done automatically in the background by the operating system.

### /res

"res" serves a file that was bundled with the experiment - in practice an image named by an
`image` view element. It takes a single parameter `src`, the file name as written in the view
element, and refuses anything the experiment does not actually reference. See the
[API reference](api-reference.md) for the exact responses.
