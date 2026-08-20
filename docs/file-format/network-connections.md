# Network Connections

Since version 1.1.3 (file format 1.8), phyphox features a versatile interface for network connections. This is done on an experiment configuration level, so to use the network communication for your own project, you need to create your own [experiment configuration](index.md). In it, you can then define how network services should be discovered, when and which data should be sent, where to put received data and which protocols to use for the communication.

This network interface is designed to be easily extended, so while at the time of this writing not many services (protocols) are supported, you can expect more to come in the future, and if you think something relevant is missing, let us know so we can implement it.

Note that there is no network service provided by phyphox for your experiments. While we set up our own servers for projects like our [sensor database](https://phyphox.org/sensordb) using the interface described here, we cannot offer a generic service. If you want to use these features, you need to set up your own server on the receiving end and you need to know how to receive the data there (or know someone who knows this). Of course, we are happy to help you and give you insight into how we do this.

## General implementation and syntax

### How network connections work in phyphox

A network connection can define phyphox buffers from which data should be sent to a network service and buffers that should receive data from the network service. The communication can either be triggered by the user through a button press or automatically at a defined interval. However, due to the nature of network communication, a response does not need to come immediately and data may even be received independently of a prior request if the protocol allows this. For example, some protocols only receive updated data as a response to a request (HTTP) while others might subscribe to updates upon connection and receive new data at random times.

In any case, the sending part of the network communication is only triggered between analysis runs of phyphox and any received data is only written to the phyphox buffers in-between analysis runs as well.

When an experiment using the network interface is loaded by the user, phyphox will always present the user with detailed information about the data that might be transmitted by the experiment. Specifically, phyphox will mention:

- If you submit a unique id which can identify subsequent requests by the user
- The submission of audio data
- The submission of location data
- The submission of other sensor data, including a list of sensors used
- The submission of device information
- The submission of technical information on the sensors, including a list of these sensors

You need to provide a URL that points to a privacy policy that tells the user how their data will be handled.

### General syntax

The network connections are defined in a network block in the document root:

{{spec:network/network/connection|wrapped}}

{{inconsistency:network-privacy-missing-url}}

The send and receive tags within the connection tag define which data should be sent and received. Each entry has an id with varying meanings.

{{spec:network/connection/send}}

{{spec:network/connection/receive}}

### Metadata

If type="meta" is set for a send-tag, the following identifiers may be used to select metadata to be sent to the network service. Note that device-specific information is not available on all devices (especially not on Apple devices).

uniqueID
:   This is an md5 hash that is unique to the user and the address of the network service. It can be used to match subsequent submissions by a single user, but only as long as it was submitted to the same address. (You cannot match users across different remote servers as different addresses!)

version
:   The version of phyphox

build
:   The build number of phyphox

fileFormat
:   The file format version of phyphox

deviceModel
:   The model id of the device

deviceBrand
:   The brand of the device

deviceBoard
:   An id for the board on which the device is based

deviceManufacturer
:   The manufacturer of the device

deviceBaseOS
:   The operating system on which the device software is based

deviceCodename
:   A codename identifying the device

deviceRelease
:   The version of the device

Additionally, you can get detailed metadata on the sensors supported by phyphox. These are not available on Apple devices, and on Android devices their meaning and accuracy can vary.

\[sensor\]Name
:   Usually the model of the sensor

\[sensor\]Vendor
:   Usually the manufacturer of the sensor

\[sensor\]Range
:   Should give the maximum range of the sensor (not very reliable)

\[sensor\]Resolution
:   Should give the resolution of the sensor (not very reliable)

\[sensor\]MinDelay
:   Typically the period of the maximum available acquisition rate (not very reliable)

\[sensor\]MaxDelay
:   The maximum delay value from Android

\[sensor\]Power
:   An estimate of the power consumption

\[sensor\]Version
:   A version of the sensor

In this list, \[sensor\] can be replaced by "accelerometer", "linear_acceleration", "gravity", "gyroscope", "magnetic_field", "pressure", "temperature", "humidity", "light", "proximity" and "attitude". Note that in some cases, phyphox will try to find a sensor by its name even though it is not officially designated to be a sensor of that type (for example vendor-specific temperature sensors).

Metadata identifiers are matched without regard to case, like every enumerated value in the format, and an identifier outside this vocabulary rejects the experiment file.

Aside from the sensors that are exposed through a unified API on Android, there are some additional metadata identifiers available for specific sensors:

depthFrontSensor
:   Number of depth sensors on the front of the device (typically 0 or 1)

depthFrontResolution
:   Highest resolution of all front depth sensors (usually, there is only one sensor supporting one resolution)

depthFrontRate
:   Highest frame rate of all front depth sensors (usually, there is only one sensor supporting one rate; if not, this rate is not guaranteed to work with the resolution reported by depthFrontResolution)

depthBackSensor
:   Number of depth sensors on the back of the device (typically 0 or 1)

depthBackResolution
:   Highest resolution of all back depth sensors (usually, there is only one sensor supporting one resolution)

depthBackRate
:   Highest frame rate of all back depth sensors (usually, there is only one sensor supporting one rate; if not, this rate is not guaranteed to work with the resolution reported by depthBackResolution)

camera2apiFull
:   JSON object with information on the cameras exposed through Android's camera2 API. Be warned, this dataset can be massive and will include many details about the camera system. Still, it is only what we implemented and by no means includes everything accessible via camera2.

camera2api
:   Shorter version of camera2apiFull with selected general data about available cameras. Note that this is still significantly larger than other metadata results.

## Network Services (Protocols)

### HTTP/GET

Attribute service="http/get"

Does not support array data

The HTTP/GET service makes an http request to a webserver. The GET version will do a GET request and encode the submitted data in the request URL. It only supports the last value in each buffer. The response may be delayed, and this service will give up on a request after the default timeout time of the device.

#### Meaning of id

The id attribute of the send tags is used as an identifier when encoding the buffer. For example, <send id="abc"\>buffer</send\> will contribute "abc=42" to the URL if the last value in the buffer is 42. If you try to receive this data on a web server using PHP, you should be able to access this value via $\_GET\["abc"\].

### HTTP/POST

Attribute service="http/post"

Supports array data

The HTTP/POST service makes an http request to a webserver. The POST version will do a POST request and encode the submitted data as JSON. By default it will encode the buffers as JSON arrays, even if they only contain a single value. You can set dataype to send single values as numbers. Metadata is encoded as strings. The response may be delayed, and this service will give up on a request after the default timeout time of the device.

Note for PHP users: Encoding POST data as JSON will not fill $\_POST by default. Instead, you will need to do the following first:

```
$json = file_get_contents('php://input');
$data = json_decode($json, true);
```

Then, if you submitted <send id="abc"\>buffer</send\> you can access an array with the entire content of the buffer at $data\["abc"\] or its first value at $data\["abc"\]\[0\].

#### Meaning of id

The ids of the send tags are used to label the JSON arrays and strings within the JSON object. A buffer with id "abc" (<send id="abc"\>buffer</send\>) and metadata with id "def" (<send id="def" type="meta"\>deviceBrand</send\>) would be encoded as

```json
{
  "abc": [0, 3, 42],
  "def": "Fancy Company"
}
```

#### Additional attributes to send

Since file format 1.10 (phyphox version [version 1.1.6](../reference/version-history/1.1.6.md)), you can additionally set the *datatype* attribute to determine whether a buffer should be encoded as an array (default) or number (last value only).

For example

```xml
<send id="abc" datatype="array">buffer</send>
<send id="def" datatype="number">buffer</send>
```

is encoded as

```json
{
  "abc": [0, 3, 42],
  "def": 42
}
```

### MQTT/CSV

**Available since phyphox 1.1.7 (file format 1.11)**

Attribute service="mqtt/csv"

Supports array data

The MQTT/CSV service connects to an MQTT broker at the given address and will send the data of "send" blocks there. Each entry of "send" will generate an individual message, using the ID as the MQTT topic. You may set a datatype for each send, with "array" (default) sending a comma-separated list of all values in the buffer and "number" only sending the last value.

If a `receiveTopic` is set, it will subscribe to this topic (or set of topics if MQTT-typical wildcards are used) and will treat the payload of each received message as a response (note that there is no mechanism to assign responses to requests - it is very likely that this received message was received before a message was sent).

If the broker requires authentication, set the optional `username` and `password` attributes (this applies to `mqtt/json` as well). Note that on a plain (non-TLS) connection these credentials travel unencrypted; use the mqtts services if that matters.

Example:

```xml
    <connection privacy="..." service="mqtt/csv" address="some.service.com/your/endpoint:1234" receiveTopic="fancySensor/value" conversion="csv" interval="1">
        <send keep="true" id="phone/pressure" type="buffer" datatype="array">p</send>
        <send keep="true" id="phone/altitude" type="buffer" datatype="number">h</send>
        <receive append="true">sensordata</receive>
    </connection>
```

In this setup, phyphox would connect to "some.service.com/your/endpoint:1234" and subscribe to "fancySensor/value". Once every second, it would send all the values from the buffer "p" as a comma-separated list to the topic "phone/pressure" and the last value from "h" to the topic "phone/altitude". Every time it does so, it takes the latest message it received under the topic "fancySensor/value" and lets the csv-conversion handle it (typically appending the list of values to sensordata).

### MQTT/JSON

**Available since phyphox 1.1.7 (file format 1.11)**

Attribute service="mqtt/json"

Supports array data

The MQTT/JSON service connects to an MQTT broker at the given address and will send the data of "send" blocks there. All entries of "send" will be combined into a single JSON object using their respective ID (also see "HTTP/POST"). The JSON string will be sent to the MQTT topic set as sendTopic. You may set a datatype for each send, with "array" (default) sending a JSON Array of all values in the buffer and "number" only sending the last value as an individual number.

If a `receiveTopic` is set, it will subscribe to this topic (or set of topics if MQTT-typical wildcards are used) and will treat the payload of each received message as a response (note that there is no mechanism to assign responses to requests - it is very likely that this received message was received before a message was sent).

Example:

```xml
    <connection privacy="..." service="mqtt/json" address="some.service.com/your/endpoint:1234" receiveTopic="fancySensor/value" sendTopic="phone/data" conversion="csv" interval="1">
        <send keep="true" id="pressure" type="buffer" datatype="array">p</send>
        <send keep="true" id="altitude" type="buffer" datatype="number">h</send>
        <receive append="true">sensordata</receive>
    </connection>
```

In this setup, phyphox would connect to "some.service.com/your/endpoint:1234" and subscribe to "fancySensor/value". Once every second, it would send all the values from the buffer "p" and the last value from "h" to the topic "phone/data". This would be done in a message with a JSON object as payload in a form like {"pressure":\[1.1,1.2,1.3\],"altitude":42.0}. Every time it does so, it takes the latest message it received under the topic "fancySensor/value" and lets the csv-conversion handle it (typically appending the list of values to sensordata).

Note that if you want to receive JSON data via MQTT, you have to pick the conversion "json" (see "Response conversion"). If you do not want to send anything, but only receive JSON, you should use the "mqtt/csv" service without setting any "send" and trigger it periodically. If you use "mqtt/json" without setting any "send", it will still send an empty JSON object.

### MQTTS/CSV and MQTTS/JSON (MQTT over TLS)

Attribute `service="mqtts/csv"` or `service="mqtts/json"`

These behave exactly like `mqtt/csv` and `mqtt/json` respectively, but connect to the broker over a TLS-encrypted connection. Two further attributes:

- `username` — the user name for the broker connection. For the mqtts services it is also used as the MQTT client id.
- `password` — the password for the broker connection.

Both are mandatory for the mqtts services (and optional for the plain mqtt services, see above). If the address does not name a port, the standard MQTT-over-TLS port 8883 is used (the plain `mqtt/*` services default to 1883).

#### Certificate

To trust a broker whose certificate is not signed by a public certificate authority — for example a self-hosted broker with a self-signed or private-CA certificate — provide the certificate as an experiment resource and name it with the optional `certificate` attribute:

- Put a certificate file in **PEM or DER** format (extension `.pem`, `.crt`, `.cer` or `.der`) in the experiment's `res` directory, exactly like an image resource. Set `certificate="broker-ca.pem"` on the connection to reference it by file name. Because it is a resource, it is bundled in the experiment zip and, when the user saves the experiment to their collection, copied along with it — so it keeps working after saving.
- The certificate is used as a trusted anchor: the broker's certificate is accepted if its chain validates against it. If the `certificate` attribute is omitted, the device's system certificate authorities are used instead. If it is set but the file cannot be loaded, the connection is not made (rather than silently falling back to a different trust).
- With a `certificate`, the broker's host name is **not** verified against it; trust rests entirely on the pinned certificate. This is intended for a self-hosted broker, whose certificate commonly names an internal host name or IP address that could not be matched anyway.
- Without a `certificate`, the host name **is** verified: since any publicly trusted authority is then accepted, the certificate must also be issued for the host the experiment connects to, or the connection is refused.

Example (the experiment is packaged as a zip whose `res` directory contains `broker-ca.pem`):

```xml
    <connection privacy="..." service="mqtts/json" address="some.service.com:8883"
                username="phone1" password="secret" certificate="broker-ca.pem"
                sendTopic="phone/data" receiveTopic="fancySensor/value"
                conversion="json" interval="1">
        <send keep="true" id="pressure" type="buffer" datatype="array">p</send>
        <receive append="true">sensordata</receive>
    </connection>
```

### Persistence and delivery quality

The `persistence` attribute applies to `mqtt/json` and `mqtts/json`. When set to `true`, messages are published with MQTT quality-of-service level 1 (at-least-once): the broker acknowledges every message while the connection is up. When it is `false` (the default), messages are published with QoS 0 (at-most-once, fire-and-forget). There is no offline buffering — a message generated while the connection is down is not resent.

## Response conversions

### None

**default**

Simply ignores the retrieved data. Good for testing data submission from phyphox to a server to avoid error messages from an empty response. However, we highly recommend that the server respond with some kind of acknowledgement that is interpreted by a proper conversion function to give feedback to the user. If you actually want to retrieve data from a server, of course, *none* is not an option anyway.

#### Meaning of id

Not applicable as response data is discarded and no data will ever be written to receiving buffers.

### CSV

**Available since phyphox 1.1.7 (file format 1.11)**

Attribute conversion="csv"

Interprets the data as comma-separated values. It accepts multiple lines based on line-break characters (Windows or Unix style) and splits columns either by comma or semicolon.

#### Meaning of id

If ID is set to an integer number, only values from the respective column (starting at zero) will be used. Otherwise (we suggest id="\*"), all data will be copied to the associated buffer, allowing a single line of comma-separated values to be parsed as an array on its own.

### JSON

Attribute conversion="json"

Supports array data

The response is interpreted as a UTF8 encoded string, which is then parsed as a JSON object.

#### Meaning of id

The IDs of the receive tags represent a simple hierarchy within the JSON object, separated by dots. So, let's take the following JSON object as an example:

```json
{
  "main": {
    "subentry": [2, 3, 23]
  },
  "other": 42,
  "yetanother": [1, 7, 42]
}
```

A receive tag with id="other" will receive a single value, 42. id="yetanother" will receive three values, 1, 7 and 42. To access something deeper within the hierarchy, id="main.subentry" will receive three values, 2, 3 and 23.

## Discovery methods for network services

A discovery service was meant to be a protocol or method to get a list of possible network services, from which the user picks one (or phyphox connects to the first one when "autoConnect" is set). This feature was never completed, and there is little point in using *discovery* or *discoveryAddress* at the moment: real discovery methods like mDNS do not exist, the selection dialog does not exist either, and *autoConnect* currently has no effect - both apps always connect to the first result.

The only accepted *discovery* value, "http", is a simple availability probe rather than a discovery: phyphox sends an HTTP GET request to *discoveryAddress* and, if the response status is in the 200 range, connects to that same address. In practice you simply set a fixed *address* for the service you use.

## Examples

Here are some example XML files for different scenarios, which might help you get started. Note that most of them will not work out of the box as they require a server to provide or receive data, so you will need to adapt them to your needs.

**The network connections are not supported by our web editor. If you want to use this function, you need to download the configuration files and edit them with a text editor.**

### HTTP

#### [Send data via HTTP/POST in JSON format](https://phyphox.org/wiki/images/8/82/Http-post-example.phyphox)

This minimalistic example collects data from the accelerometer at a rate of 4Hz and sends the last 20 collected values every 5 seconds to a php script via HTTP POST. Any reply from the server is ignored (you might want to consider using the response as a confirmation to the user by mapping response values to texts via the mapping function of the [value element](views/basics.md#view-element-value)).

The following is a minimalistic example for a PHP script receiving the data and writing it to a simple text file. Note that you need to explicitly parse the JSON data from `php://input` instead of directly accessing POST as you might be used to when receiving data from web forms.

```xml
<?php
  $json = file_get_contents('php://input');
  $data = json_decode($json, true);

  $line = time()."\t".implode(",", $data["t"])."\t".implode(",", $data["x"])."\n";

  file_put_contents("data.txt", $line, FILE_APPEND | LOCK_EX);
?>
```

**Warning: Do not use this minimalistic example on a public server! A real-world PHP example should have some sanity checks, flood protection and similar security measures to avoid misuse or sabotage of your webserver. Of course a local server for select users does not necessarily require such measures. You need to consider this when running any web service.**

#### [Send a value via HTTP/GET and receive a plot in JSON format](https://phyphox.org/wiki/images/6/69/Http-get-example.phyphox)

This example demonstrates sending a value as a URL parameter via HTTP (GET method), which in this case is a frequency that the user may enter. Moreover, the value is sent when the user pushes a button and a PHP script will respond with a JSON package that contains 100 value pairs that form a sine function with the given frequency. The received sine function is then plotted in phyphox.

The following is the PHP script that takes the frequency and generates a JSON object with the sine function as a response for phyphox. Note that this script packs the data as `{"curve": {"t": [...], "a": [...]}}`, but the extra step of packing it into a "curve" object is not really necessary. It is only done here to demonstrate how to access a JSON path from within phyphox by using `id="curve.t"`.

```xml
<?php
  $f = floatval($_GET["f"]); //Get frequency submitted by phyphox

  //Build curve
  $curve = array("t" => array(), "a" => array());
  for ($t = 0.0; $t < 10.0; $t += 0.1) {
    $curve["t"][] = $t;
    $curve["a"][] = sin($f*$t);
  }

  //Pack answer into another array (just for demonstration of id style "curve.a")
  $result = array("curve" => $curve);

  //Generate JSON and write it as output
  echo json_encode($result);
?>
```

**Warning: Do not use this minimalistic example on a public server! A real-world PHP example should have some sanity checks, flood protection and similar security measures to avoid misuse or sabotage of your webserver. Of course a local server for select users does not necessarily require such measures. You need to consider this when running any web service.**

### MQTT

#### [Send CSV via MQTT](https://phyphox.org/wiki/images/2/23/Mqtt-csv-example.phyphox)

In this example, time and x acceleration are acquired from the accelerometer (averaging to a rate of 1 Hz) and the last ten readings are sent every 10 seconds as a comma-separated list (CSV) to an MQTT broker at 192.168.2.5. As this example uses comma-separated lists, time and acceleration are sent to separate topics.

#### [Send JSON via MQTT](https://phyphox.org/wiki/images/8/86/Mqtt-json-example.phyphox)

This example only sends data when a button is pressed. It then takes the latest readings from the accelerometer and sends the x, y and z components as a JSON object to the topic "phyphox/acc" on an MQTT broker at 192.168.2.5.

#### [Octoprint tool temperature](https://phyphox.org/wiki/images/1/1d/Octoprint.phyphox)

This example connects to an MQTT broker at 192.168.2.5 and subscribes to the topic octoPrint/temperature/tool0 which is used by the 3d printing software "octoprint" to report the current tool temperature. The phyphox experiment adds a timestamp and plots the current temperature and the target temperature over time. Note that Octoprint sends JSON messages, but as this example should not write anything to the topic, it uses "mqtt/csv" as a service and "json" as a conversion function to decode the json data.

#### [Octoprint tool and bed temperature](https://phyphox.org/wiki/images/0/0f/Octoprint2.phyphox)

Like the simpler Octoprint example above, but this example subscribes to two topics to print the bed temperature as well. Note that adding a timestamp to both temperatures is what makes this example rather large.
