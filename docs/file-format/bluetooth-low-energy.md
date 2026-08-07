# Bluetooth Low Energy

------------------------------------------------------------------------

**If you want to integrate your Arduino or ESP32 project with phyphox, the easiest approach ist our [Arduino library](https://phyphox.org/arduino).**

------------------------------------------------------------------------

The information on this page refers to version 1.1.0 (file format 1.7) onwards. Bluetooth Low Energy was not available on earlier versions of phyphox.

Phyphox can communicate with almost any Bluetooth Low Energy (BLE) device to receive and send data. It comes with several prepared experiment configurations, which you can use without any additional knowledge. On top you can add support for additional devices through our editor or by directly creating/editing a phyphox-file with a text editor. If you are just looking for devices with existing support, you can check out our [Bluetooth device database](https://phyphox.org/wiki/index.php/Bluetooth_device_database) instead.

This page describes how the Bluetooth Low Energy integration works in phyphox files, which applies to both, the editor and direct editing of the phyphox-file. It also explains in detail the syntax in the phyphox file and the protocol how a device can offer its own phyphox-file to the app, so you can for example program an Arduino so it can be used without the necessity to manually transfer a phyphox-file.

If this is the first time that you use the editor, you should start with our [experiment editor](https://phyphox.org/editor) and if you just started to learn about our file format (without using the editor), you should start on the main page about our [file format](index.md). Also, if you are new to Bluetooth Low Energy, you should look for a short introduction, so you know what the terms "GATT", "UUID", "service", "characteristic" and "notification" mean.

In order to write a phyphox-file for a BLE device, you will need to know how its communication works. If the device is supported by phyphox out of the box, you can open the existing phyphox-file in our editor to see how we communicate with it. If this is not the case and you try to communicate with the device for the first time, you can often use some documentation by the manufacturer or some similar source of information. Finally, you can try to figure out the communication yourself by using apps that list the services and characteristics and capturing the communication from other apps (please make sure that you are legally allowed to do so).

If you create support for a device which is of interest to a wider audience (or need help to do so), please contact us as we might want to include it with the next phyphox version (with concent by the manufacturer).

Also, if you want to add support for your own sensors (for example Arduino-based), the [Arduino library](https://phyphox.org/arduino) is the easiest starting point.

## BLE integration in phyphox

### Accessing BLE devices

There are two methods to access a BLE device from the user interface.

The first one is the one that is probably most familiar to many users. If you tap the plus button on the main screen (bottom right corner on Android, top right on iOS) you can select the option "Bluetooth" which initiates a scan for such devices. This lists every device, but will show most of them in grey unless phyphox has a matching experiment in its collection. A matching experiment needs to be included with phyphox and cannot be achieved by transferring a phyphox-file. The only exception is if the device brings its own phyphox-file, which is a rather advanced method for your own hardware, described below. Also note that these experiments will only work with a single BLE device as you first scan for one device and pick matching experiments afterwards.

The other method works just like opening any other custom eperiment in phyphox. You transfer your file to the phone (as a .phyphox-file, in a zip file or through a QR code) or pick an experiment from the list on the main screen (after you have chosen to add the transfered file or an included BLE experiment to the collection). The experiment is opened in phyphox and it will try to connect to all devices required for the experiment, which in many cases is a single device but you could also use many different devices in the same experiment.

### BLE as input or output

BLE devices can be either used as an input to phyphox or as an output to receive data acquired by phyphox.

When used as an input, the characteristics are read from the device, their data will be interpreted and then written to a phyphox buffer. When used as an output, the values from a phyphox buffer are converted to a binary representation and then written to a characteristic on the device.

### Notifications and polling

Most BLE devices support notifications, which means that phyphox can subscribe to a characteristic and gets notified if the device offers a new value. This is the most efficient way to retrieve data and should be used when using a BLE device as input (it does not apply to writing to the device).

However, when the device does not support notifications or if you want values at a fixed rate (i.e. not having "gaps" if there is no new value for a long time or not collecting many data points if only few are sufficient), the mode of the input device can be switched to "poll". In this case you also need to define a rate at which values are being read from the device.

Phyphox also supports indications, which are similar to notifications, but most devices typically do not support them for simple data values.

### Accessing characteristics as input, output or config

When a BLE device is used as input, it needs to define its outputs to the phyphox buffers. Therefore, a BLE device that is an input to phyphox, sets up buffers to which it outputs its data. Each of these output buffers needs to be associated with a characteristic and multiple output buffers may be associated with the same characteristic. Each time the characteristic is read (through polling or because of a notification), the same value is fed to all buffers, which then interpret the data differently according to a conversion function which needs to be set as well (the conversion functions are listed below). Many conversion functions offer to set an offset and/or a size, so they only interpret a part of the incoming data. This way different values within a single characteristic can be split to different buffers.

Output devices work similar, but instead of defining output buffers, they define input buffers, which also use slightly different conversion functions.

In case of an output buffer (for an input device) the conversion function can be left out if instead the "extra" field is set to "time", in which case the output buffer does not recieve values from the characteristic, but the time (in seconds since the start of the experiment) at which it has been read.

Both, input and output devices, can also define config settings for a characteristic. These do not associate the characteristic with a buffer but with a constant value. This value will be written to the device once after a connection has been established. This is usually used for configuration like enabling a sensor or setting a data acquisition rate.

## BLE-related syntax in phyphox-files

### BLE device matching

Whenever a BLE device is defined in phyphox, you will need to set up how it is matched against scan results. You can define a text that is compared to the name of the device and/or the UUID of an advertised service.

The device-matching attributes are the same wherever a bluetooth element appears, in the input block and in the output block alike.

{{spec:input/input/bluetooth|attributes}}

### BLE as input

If data should be read from a BLE device and displayed in phyphox, the device should be defined within the input block of the phyphox file:

```
    ...
    <input>
        <bluetooth name="..." uuid="..." id="..." autoConnect="..." mode="..." rate="..." subscribeOnStart="...">
            ...
            <config ...>...</config>
            ...
            <output ...>...</output>
            ...
        </bluetooth>
    </input>
    ...
```

When using the "bluetooth" tag within an "input" tag, values are read from the device and written to buffers specified in output tags (more on these below). Additionally, "config" tags can be used to set up the device by writing configuration values to the device after connecting.

In addition to the device-matching attributes above, these define how and when data is read from the device:

{{spec:input/input/bluetooth}}

### BLE as output

If data should be transmitted to a BLE device (i.e. a characteristic), the device should be defined within the output block of the phyphox file:

```
    ...
    <output>
        <bluetooth name="..." uuid="..." id="..." autoConnect="...">
            ...
            <config ...>...</config>
            ...
            <input ...>...</input>
            ...
        </bluetooth>
    </output>
    ...
```

In contrast to using the tag "bluetooth" within an input tag, you cannot specify a mode or a poll rate. The values are read from buffers defined in input tags and written to the device when the analysis process of the experiment has finished. Config tags work as usual.

Since phyphox file format 1.19 (phyphox version 1.2.0) you can also set the attribute "keep" for each input tag. This works like the keep attribute in analysis modules: If you set keep="false", the data container is cleared after the data has been sent, allowing you to sent data only once. The default is keep="true" and the same behavior as in older versions, in which the data container is not altered after data has been sent.

Since phyphox file format 1.20 (phyphox version 1.2.1) you can also set the attribute "triggerId" for each input tag. If set, the data associated with this characteristic is only sent at the end of an analysis process if the user has pressed a button view element with a matching trigger tag. Other input tags may continue to send periodically as usual, but this allows to assign certain submissions directly to user input.

### config, input and output block

There are three different tags within a bluetooth block:

config
:   The config tag writes a configuration value to the device after the connection has been established. This is usually used to enable a specific sensor, set a data acquisition rate or set a measurement mode. The config tag always takes a constant value.

input
:   An input tag can only be used in an output block. The name "output" of the outer block refers to phyphox as it outputs data from phyphox, while the name "input" of the inner block refers to the BLE device, as it is the input to the device. This defines a buffer from which data is written to the device.

output
:   Output tags can only be used in an input block. The name "input" of the outer block refers to phyphox as it represents a data input for phyphox, while the name "output" of the inner block refers to the BLE device, as it is the output of the device. This defines a buffer to which data is written from the device.

{{spec:input/bluetooth/output}}

{{spec:output/bluetooth/input}}

{{spec:input/bluetooth/config}}

All three types have to be connected to the UUID of a characteristic on the BLE device through its UUID. This is defined through the "char" attribute. On top of this, a range of conversion functions are available, which need to be defined through the attribute "conversion". These are different for input, output and config tags and may imply additional attributes. They are discussed separately below.

Here are some examples:

This sets the a HID mouse to BIOS mode by writing 0x00 to the characteristic 0x2a4e after connecting to the device:

```xml
 <config char="00002A4e-0000-1000-8000-00805F9B34FB" conversion="hexadecimal">00</config>
```

These two outputs read from the same characteristic but use different conversion functions (or rather different parameters to the same function) to get x and y movement of the mouse and write it to the buffers dx and dy:

```xml
 <output char="00002A33-0000-1000-8000-00805F9B34FB" offset="1" length="1" conversion="singleByte">dx</output>
 <output char="00002A33-0000-1000-8000-00805F9B34FB" offset="2" length="1" conversion="singleByte">dy</output>
```

The following line defines buffer "char" as an input, so its values are written to the LED character output of a BBC Micro:bit.

```xml
 <input char="E95D93EE-251D-470A-A062-FA1922DFA9A8" conversion="singleByte">char</input>
```

### config conversion functions

Config tags take a constant string and convert it to a binary value to be written to a characteristic. Currently, the following conversion functions are defined:

string
:   The string is interpreted as a string and written directly to the characteristic

hexadecimal
:   The string is a hexadecimal representation of the binary value that should be written to the characteristic. (Note that there is no leading "0x", so 0x1f is simply written as 1f.) Spaces may be used to group the digits ("1A 2B"). Any other non-hexadecimal character makes the whole value empty, and a dangling digit of an odd-length string is ignored.

singleByte
:   The string is parsed as a decimal number and encoded as a single byte value (same as uInt8)

int8
:   The string is parsed as a decimal number and encoded as a signed 8bit integer

uInt8
:   The string is parsed as a decimal number and encoded as an unsigned 8bit integer

int16LittleEndian
:   The string is parsed as a decimal number and encoded as a signed 16bit integer with little endian byte order (that is starting with the LSB)

uInt16LittleEndian
:   The string is parsed as a decimal number and encoded as an unsigned 16bit integer with little endian byte order (that is starting with the LSB)

int16BigEndian
:   The string is parsed as a decimal number and encoded as a signed 16bit integer with big endian byte order (that is starting with the MSB)

uInt16BigEndian
:   The string is parsed as a decimal number and encoded as an unsigned 16bit integer with big endian byte order (that is starting with the MSB)

int24LittleEndian
:   The string is parsed as a decimal number and encoded as a signed 24bit integer with little endian byte order (that is starting with the LSB)

uInt24LittleEndian
:   The string is parsed as a decimal number and encoded as an unsigned 24bit integer with little endian byte order (that is starting with the LSB)

int24BigEndian
:   The string is parsed as a decimal number and encoded as a signed 24bit integer with big endian byte order (that is starting with the MSB)

uInt24BigEndian
:   The string is parsed as a decimal number and encoded as an unsigned 24bit integer with big endian byte order (that is starting with the MSB)

int32LittleEndian
:   The string is parsed as a decimal number and encoded as a signed 32bit integer with little endian byte order (that is starting with the LSB)

uInt32LittleEndian
:   The string is parsed as a decimal number and encoded as an unsigned 32bit integer with little endian byte order (that is starting with the LSB)

int32BigEndian
:   The string is parsed as a decimal number and encoded as a signed 32bit integer with big endian byte order (that is starting with the MSB)

uInt32BigEndian
:   The string is parsed as a decimal number and encoded as an unsigned 32bit integer with big endian byte order (that is starting with the MSB)

float32LittleEndian
:   The string is parsed as a decimal number and encoded as a 32bit floating point number with little endian byte order (that is starting with the LSB)

float64LittleEndian
:   The string is parsed as a decimal number and encoded as a 64bit floating point number with little endian byte order (that is starting with the LSB)

float32BigEndian
:   The string is parsed as a decimal number and encoded as a 32bit floating point number with big endian byte order (that is starting with the MSB)

float64BigEndian
:   The string is parsed as a decimal number and encoded as a 64bit floating point number with big endian byte order (that is starting with the MSB)

### output conversion functions

The input tags in an output block take a number from a phyphox buffer and convert it to a binary value to be written to a characteristic. Some functions can also take the whole content of the buffer instead of a single value.

In order to combine multiple buffers into one characteristic (for example to send x, y and z to a single characteristic), you can define multiple inputs within a bluetooth output with the same target characteristic. The result from the previous conversion function will overwrite the content generated by the previous one, extending the size of the result if necessary. This becomes useful when combined with the "offset" attribute (available since file format version 1.15 (phyphox version 1.1.11)) as you can specify a sequence of inputs with increasing offsets. For example, you could sent x, y and z as float32LittleEndian with offsets 0, 4 and 8 to create 12 bytes of data containing all three values.

Currently, the following conversion functions are defined:

string
:   The value from the buffer is converted to a string representation of a decimal number

byteArray
:   All values from the buffer are taken, individually converted to bytes and then written as sequence of bytes to the characteristic

singleByte
:   The value from the buffer is converted to a decimal number and encoded as a single byte value (same as uInt8)

int8
:   The value from the buffer is converted to a decimal number and encoded as a signed 8bit integer

uInt8
:   The value from the buffer is converted to a decimal number and encoded as an unsigned 8bit integer

int16LittleEndian
:   The value from the buffer is converted to a decimal number and encoded as a signed 16bit integer with little endian byte order (that is starting with the LSB)

uInt16LittleEndian
:   The value from the buffer is converted to a decimal number and encoded as an unsigned 16bit integer with little endian byte order (that is starting with the LSB)

int16BigEndian
:   The value from the buffer is converted to a decimal number and encoded as a signed 16bit integer with big endian byte order (that is starting with the MSB)

uInt16BigEndian
:   The value from the buffer is converted to a decimal number and encoded as an unsigned 16bit integer with big endian byte order (that is starting with the MSB)

int24LittleEndian
:   The value from the buffer is converted to a decimal number and encoded as a signed 24bit integer with little endian byte order (that is starting with the LSB)

uInt24LittleEndian
:   The value from the buffer is converted to a decimal number and encoded as an unsigned 24bit integer with little endian byte order (that is starting with the LSB)

int24BigEndian
:   The value from the buffer is converted to a decimal number and encoded as a signed 24bit integer with big endian byte order (that is starting with the MSB)

uInt24BigEndian
:   The value from the buffer is converted to a decimal number and encoded as an unsigned 24bit integer with big endian byte order (that is starting with the MSB)

int32LittleEndian
:   The value from the buffer is converted to a decimal number and encoded as a signed 32bit integer with little endian byte order (that is starting with the LSB)

uInt32LittleEndian
:   The value from the buffer is converted to a decimal number and encoded as an unsigned 32bit integer with little endian byte order (that is starting with the LSB)

int32BigEndian
:   The value from the buffer is converted to a decimal number and encoded as a signed 32bit integer with big endian byte order (that is starting with the MSB)

uInt32BigEndian
:   The value from the buffer is converted to a decimal number and encoded as an unsigned 32bit integer with big endian byte order (that is starting with the MSB)

float32LittleEndian
:   The value from the buffer is converted to a decimal number and encoded as a 32bit floating point number with little endian byte order (that is starting with the LSB)

float64LittleEndian
:   The value from the buffer is converted to a decimal number and encoded as a 64bit floating point number with little endian byte order (that is starting with the LSB)

float32BigEndian
:   The value from the buffer is converted to a decimal number and encoded as a 32bit floating point number with big endian byte order (that is starting with the MSB)

float64BigEndian
:   The value from the buffer is converted to a decimal number and encoded as a 64bit floating point number with big endian byte order (that is starting with the MSB)

### input conversion functions

The output tags in an input block take a byte sequence from the characteristic and convert it to a number to be written to a phyphox buffer. Most conversion functions (unless noted otherwise) can use the attributes "offset" and "size" to define a subsequence of bytes. The start is defined by "offset" (in bytes, starting at zero) and the length is set by "size" (in bytes).

Optionally, the attribute "repeating" can be set to a value larger than zero. If set, multiple values can be extracted from a single dataset and the conversion function will try and get values from \[offset\], \[offset\]+\[repeating\], \[offset\]+2\*\[repeating\] etc.

Instead of defining a conversion function, you can also set the attribute "extra" to "time" (extra="time"). This means that the associated buffer does not receive the value from the characteristic, but the time at which the characteristic has been read in seconds since the beginning of the experiment.

Currently, the following conversion functions are defined:

string
:   The value from the characteristic parsed as a decimal number

formattedString
:   This function always parses the whole data sequence from the characteristic as a single string (i.e. there is no "offset" or "size" attribute) and tries to split it into several values at the sequence set by the "separator" attribute. Each output tag can then specify which chunk corresponds to the buffer by either setting the "index" attribute, which gives the n-th entry (starting at zero), or by setting the "label" attribute, which is another character sequence which prepends the entry. Each entry is then parsed as a decimal number (labels are stripped before that happens).
:   Examples:
:   
:   A simple comma-separated value string
:   42;23
:   An output tag with separator=";" and index="0" returns 42 and a second output tag with separator=";" and index="1" returns 23.
:   
:   A string with simple labels:
:   U42;I23
:   An output tag with separator=";" and label="U" returns 42, an output tag with separator=";" and label="I" returns 23.
:   
:   A string from the characteristic with a line break and labels:
:   U = 42
:   I = 23
:   An output tag with separator="\n" and label="U = " returns 42 and an output tag with separator="\n" and label="I = " returns 23.

singleByte
:   The data from the characteristic is interpreted as a single byte value (same as uInt8)

int8
:   The data from the characteristic is interpreted as a signed 8bit integer

uInt8
:   The data from the characteristic is interpreted as an unsigned 8bit integer

int16LittleEndian
:   The data from the characteristic is interpreted as a signed 16bit integer with little endian byte order (that is starting with the LSB)

uInt16LittleEndian
:   The data from the characteristic is interpreted as an unsigned 16bit integer with little endian byte order (that is starting with the LSB)

int16BigEndian
:   The data from the characteristic is interpreted as a signed 16bit integer with big endian byte order (that is starting with the MSB)

uInt16BigEndian
:   The data from the characteristic is interpreted as an unsigned 16bit integer with big endian byte order (that is starting with the MSB)

int24LittleEndian
:   The data from the characteristic is interpreted as a signed 24bit integer with little endian byte order (that is starting with the LSB)

uInt24LittleEndian
:   The data from the characteristic is interpreted as an unsigned 24bit integer with little endian byte order (that is starting with the LSB)

int24BigEndian
:   The data from the characteristic is interpreted as a signed 24bit integer with big endian byte order (that is starting with the MSB)

uInt24BigEndian
:   The data from the characteristic is interpreted as an unsigned 24bit integer with big endian byte order (that is starting with the MSB)

int32LittleEndian
:   The data from the characteristic is interpreted as a signed 32bit integer with little endian byte order (that is starting with the LSB)

uInt32LittleEndian
:   The data from the characteristic is interpreted as an unsigned 32bit integer with little endian byte order (that is starting with the LSB)

int32BigEndian
:   The data from the characteristic is interpreted as a signed 32bit integer with big endian byte order (that is starting with the MSB)

uInt32BigEndian
:   The data from the characteristic is interpreted as an unsigned 32bit integer with big endian byte order (that is starting with the MSB)

float32LittleEndian
:   The data from the characteristic is interpreted as a 32bit floating point number with little endian byte order (that is starting with the LSB)

float64LittleEndian
:   The data from the characteristic is interpreted as a 64bit floating point number with little endian byte order (that is starting with the LSB)

float32BigEndian
:   The data from the characteristic is interpreted as a 32bit floating point number with big endian byte order (that is starting with the MSB)

float64BigEndian
:   The data from the characteristic is interpreted as a 64bit floating point number with big endian byte order (that is starting with the MSB)

## Phyphox service

Additional functionality becomes accessible if your device supports the phyphox service with UUID cddf0001-30f7-4671-8b43-5e40ba53514a. Specifically, this service may implement any of the following characteristics within cddfxxxx-30f7-4671-8b43-5e40ba53514a:

- 0002 - experiment characteristic (transfer XML configuration to phyphox)
- 0003 - experiment control characteristic (optional helper to control data flow of 0002)
- 0004 - event characteristic (receive events and time references from phyphox)

Note that you have to implement 0002 if you advertise the phyphox service. If you do not advertise the service, all characteristics are optional.

### Sending phyphox-files from a device (0002 and 0003)

If you create your own device (for example an Arduino-based sensor with a BLE module), you can also store experiments on the device and send them to phyphox.

To do so, your device needs to advertise and implement the phyphox service, which uses the UUID cddf0001-30f7-4671-8b43-5e40ba53514a. When the user picks the Bluetooth scan from the "+" button on the main screen, phyphox will list devices that advertise this UUID in white like any other device for which it has an internal phyphox-file.

When connecting to this device, phyphox will look for a characteristic with the UUID cddf0002-30f7-4671-8b43-5e40ba53514a and subscribe to its notifications. Your device needs to react to this subscription by starting to send the experiment file (preferably in a zip file) through this characteristic. Alternatively (since phyphox version 1.1.6), if you cannot react to a subscription (some libraries are limited in this way), you can also offer an additional characteristic with the UUID cddf0003-30f7-4671-8b43-5e40ba53514a. If present, phyphox will write a 1 to it to request the start of the transfer and a 0 before disconnecting (if possible - you should be prepared for a disconnect that does not allow writing a zero).

Sending the experiment file starts with a header. So the first package you send needs to consist of (at least 15 bytes):

phyphox\[size\]\[crc32\]

The first seven bytes need to contain the keyword "phyphox", followed by four bytes for an unsigned 32-bit big endian integer giving the size of the experiment file (not including this header) and the last four bytes must give the CRC32 check value of the whole experiment file (again, not including this header). Remaining bytes in the first message are ignored and can be set to zero.

The experiment is transmitted sequentially in subsequent messages. If there is space left in the final message, it can simply be filled with zeros as phyphox ignores any bytes after the size set in the header has been reached.

### Phyphox event characteristic (0004)

If phyphox sees this characteristic, it will write any START or PAUSE event as soon as possible. Additionally, it will write a SYNC event after connecting to the device.

The data block of each event consists of 17 bytes with following meaning:

Byte 0 is the event type: PAUSE (0x00), START (0x01), CLEAR (0x02), SYNC (0xff). So, for example, you can look for 0xff on byte 1 to find sync events or check for 0x01 to see if phyphox is currently measuring.

Byte 1-8 is the experiment time in milliseconds, i.e. the time the measurement has been running since the first start event. This value will not increase while the experiment is paused and for the first START event it will be zero. SYNC events will set this to -1 (i.e. 0xffffffffffffffff) as this occurs before the reference START event. The format is a 64bit signed integer in big endian format. This also means that for most applications, you can simply interpret bytes 5 to 8 as a 32bit unsigned integer (big endian) to get millis since the start of the measurement without running into any problems as long as the measurement does not run longer than about three weeks. (In fact, the choice for 64bit signed was just made for consistency with Java system time and there is not much practical relevance to interpreting it as 64bit over 32bit.)

Byte 9-16 is the system time in milliseconds since midnight on 1.1.1970 UTC. This is a 64bit signed integer and identical to the Javas System.currentTimeMillis() (converted to this format on iOS systems). The byte order is big endian.

Events are sent as soon as possible with the SYNC event being as close to the actual time measurement as possible, so the SYNC event is usually the best option to get the real world clock from phyphox. Still, you should be aware that network latency can be significant, especially if multiple Bluetooth devices, bad reception or a lot of traffic is involved.

This feature is available since phyphox file format 1.15 (version 1.1.11).

Note, the CLEAR event is generated when the user selects to delete the current experiment data. It is sent before clear is executed, so it will contain the old experiment time before it is reset to zero. This is sent from phyphox version 1.2.0 onwards.
