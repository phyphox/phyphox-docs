# Phyphox file format

*This page is highly technical. Most users will want [the visual experiment editor](../editor/index.md) instead.*

This page is highly technical and meant for advanced users who want to control every minute detail of their experiment. On this page you will learn, how the phyphox file format works and how to create a phyphox experiment - all you need is a text editor. Some experience about the XML format is recommended.

## Structure

The phyphox format is based on xml. The entire experiment is encapsulated within a *phyphox* root tag. Within this block, there are multiple blocks which allow to define data-containers, inputs, outputs, translations, analysis etc.

```xml
<phyphox version="1.0">
    <title>Experiment title</title>
    <category>Experiment category</category>
    <icon>
        ... Defines which icon should be shown ...
    </icon>
    <description>
        ... A description of the experiment ...
    </description>
    <translations>
        ... Translations into other languages than English ...
    </translations>
    <data-containers>
        ... Defines data buffers to hold sensor and result data ...
    </data-containers>
    <input>
        ... Inputs like sensors or the microphone ...
    </input>
    <output>
        ... Outputs like the speaker ...
    </output>
    <views>
        ... Different views, defining how the results are presented to the user ...
    </views>
    <analysis>
        ... All the math goes in here ...
    </analysis>
    <export>
        ... Export sets define how data-containers are grouped and named when exporting them to a file ...
    </export>
</phyphox>
```

## Block: phyphox

The entire experiment is defined within the phyphox block. It has a single attribute, which is the version of the file format (not the version of the app). If the file format changes in future version, this version number will increase. If phyphox (the app) encounters a file version newer than what it can read, it will not load the file but ask the user to update the app.

**Tag: Title**

```xml
<title>TITLE</title>
```

The title of the experiment. This is just a simple string. Try to keep it short and concise.

**Tag: State-Title**

**Available since phyphox file format 1.5 (phyphox 1.0.7)**

```xml
<state-title>TITLE</state-title>
```

This should not be used for a experiment, which will be distributed. This tag contains the title given by the user when saving the state of an experiment. If this is set, the app will show this experiment in the saved-states section.

**Tag: category**

```xml
<category>CATEGORY</category>
```

The category of the experiment. This is just a simple string used by the app to group the experiments. Try to keep it short and concise.

Note that this can and *should* be translated if you use translations (see below) as the app uses the localized version of this string and cannot match your experiment to the default group if the category is given in a different language.

**Tag: icon**

```xml
<icon format="FORMAT">ICON</icon>
```

The icon of the experiment. The attribute *format* controls whether *ICON* is just a string or a base64 encoded image. If it is a string, phyphox will take the first three characters (using fewer characters is ok) and create a simple icon with these. If it is a base64-encoded image, phyphox will decode it and display the image.

We recommend to use a small PNG with few colors as an icon. There are various web-based tools to create a base64-encoded PNG from a PNG file.

format
:   Can be *string* or *base64* and controls whether the icon should be interpreted as a string or as a base64 encoded image.
:   *optional*, default: *string*

**Tag: color**

```xml
<color>COLOR</color>
```

The base color for the experiment. This is used as a background of the icon (if a text-based icon is used or if it has a transparent background) and for the label of the category. If a category contains experiments with different colors, the most common color is used.

Color can be defined as a 6-digit hex value or as one of the named [Colors](colors.md).

**Tag: description**

```xml
<description>DESCRIPTION</description>
```

A description of the experiment. The first line should be a very short information of what the experiment does as this line will be shown in the experiment list. Any white spaces at the beginning and end of DESCRIPTION as well as in each line will be stripped.

**Tag: link**

```xml
<link label="LABEL" highlight="false">URL</link>
```

A link-Tag defines a link to some resource on the web. You may have multiple link tags in your phyphox file and they will be listed as a button each under the experiment description. When the user pushes the button, he will be redirected to the URL (usually in a web browser, but it might be a specific app for a specific URL - for example Youtube links usually open in the Youtube-App in Android). If the attribute *highlight* is set to true, the link will also be featured in the experiment menu. (Note, that the highlight attribute is meant to highlight especially relevant links, like instructions for the experiment. Its actual implementation, i.e. the way a link is "highlighted" might change in newer versions.)

## Block: translations

The translations block may hold one or more *translation* (note: singular) blocks, describing the translations of strings shown to the user. Any string outside the translations block is considered to be in English and then translated to other languages from within the translations block, unless a different global language has been defined in the tag of the phyphox-block or if English appears explicitly as a translation block. If English is used in a translation block and no language has been defined in the phyphox-block, the text outside the translation block should be treated as a placeholder.

```xml
<phyphox version="1.0">
    <title>My experiment</title>
    <category>Example</category>
    ...
    <translations>
        <translation locale="de">
            <title>Mein Experiment</title>
            <category>Beispiel</category>
            <string original="Some string used in the experiment.">Ein im Experiment genutzter String.</string>
            ...
        </translation>
        <translation locale="fr">
            <title>Mon expérience</title>
            <category>Exemple</category>
            <string original="Some string used in the experiment.">Une chaîne de caractères utilisèe dans l'experiénce.</string>
            ...
        </translation>
    </translations>
    ...
</phyphox>
```

### Block: translation

Each translation block holds all the translations for a single language. The attribute

locale
:   Defines the two-character iso language code for the translations within this language block. (for example "de" for German or "fr" for French)
:   *required*

**Tag: title**

```xml
<title>TITLE</title>
```

Localized version of the title tag in the phyphox-block (see above). If the user's locale matches the locale of the translation block, the title will be replaced by this entry.

**Tag: category**

```xml
<category>CATEGORY</category>
```

Localized version of the category tag in the phyphox-block (see above). If the user's locale matches the locale of the translation block, the title will be replaced by this entry. Note that phyphox will group experiments by the localized version of the category.

**Tag: description**

```xml
<description>DESCRIPTION</description>
```

Localized version of the description tag in the phyphox-block (see above). If the user's locale matches the locale of the translation block, the title will be replaced by this entry.

**Tag: link**

```xml
<link label="LABEL">URL</link>
```

This is the localized version of the link-Tag. For example, if you link to a Demo video in English with

```xml
<link label="Demo">http://site.org/my/english/video</link>
```

you can link to a German version in the translation block with

```xml
<link label="Demo">http://site.org/my/german/video</link>
```

**Tag: string**

```xml
<string original="ORIGINAL">TRANSLATION</string>
```

Use the string-tag to translate any string shown to the user besides the title, description or category. If the text of a label, view etc. matches the string in ORIGINAL, phyphox will display TRANSLATION instead. (Of course, this only applies if the user's locale matches the translation locale.)

original
:   The string which should be translated with TRANSLATION. This has to be an exact match.
:   *required*

## Block: data-containers

In data-containers all buffers are defined. Any input (sensors, microphone) write to these buffers, any analysis module performs its operations on these buffers, the output modules read from these buffers and the results are shown to the user from these buffers. The buffers connect every module of the experiment.

```xml
<phyphox version="1.0">
    ...
    <data-containers>
        <container>Buffer 1</container>
        <container size="1000">Buffer 2</container>
        <container type="buffer">Buffer 3</container>
    </data-containers>
    ...
</phyphox>
```

### Tag: container

```xml
<container size="INTEGER" init="FLOAT" static="BOOLEAN" clearGroup="STRING">NAME</container>
```

The container tag defines the name of a single data container. For now, the only container type is buffer, so the attribute *type* can be left out - It is only there for future new container types.

The *buffer* type is a queue of a fixed length. New data is appended until the buffer is full. If data is appended to a full buffer, old data is removed from the other end. Any module reading from the buffer will receive the whole data set. However, if the module only requires a single value, it may access the last added value directly.

The size can be set by the *size* attribute, which defaults to 1.

Infinite buffers are allowed and can be achieved by setting size to zero. However, you should be careful when using this. Never keep filling an infinite buffer if it is the base for complex analysis as this will lead to extreme load when the experiment runs for a long period. Also, infinite buffers are not allowed to hold the recording from an audio input.

type
:   The only type supported right now is *buffer*. This attribute can be ignored for now, but other container types may be added in the future.
:   *optional*, default: *buffer*

size
:   The size of the data-container. For the buffer type this is the number of values, the buffer can hold.
:   *optional*, default: 1

static
:   If set to true, the content of this buffer should only be written once. Analysis modules writing to this buffer will not execute if all output buffers are static to improve performance. This should be set if the content does not depend on measured data.
:   *optional*, default: false

init, **Available since phyphox file format 1.3 (phyphox 1.0.4)**
:   If set, the buffer will be initialized with the given value when loading the experiment as well as when clearing the data. If not set, the buffer will start empty. Since file format 1.5 (phyphox 1.0.7) you can also separate multiple values by comma to initialize a buffer with multiple values.

clearGroup, **Available since phyphox file format 1.20 (phyphox 1.2.1)**
:   If set, the buffer will not be cleared automatically when the user presses the trash symbol. Instead, the string assigned to *clearGroup* will be shown as an option that the user can select. This is particularly usefull if the experiment contains settings or calibration data that should be preserved when measured data is deleted. Multiple data containers can be assigned to the same *clearGroup*. Also, the string assigned to the *clearGroup* can be translated. Take care when using multiple clear groups that are translated as the translated name will then be used to address the groups, so the translated names have to be distinct. If you want to prevent users from ever deleting specific buffers, you can assign the special clearGroup "\_" (only an underscore), which will never be offered for the user to pick for clearing.
:   *optional*, default: no set (will always be cleared through the trash button)

## Block: input

The input block defines all hardware inputs such as sensors or the microphone used in the experiment.

```xml
<phyphox version="1.0">
    ...
    <input>
        <sensor type="pressure">
            <output component="x">Pressure</output>
        </sensor>
        <sensor type="accelerometer" average="true" rate="0.5">
            <output component="x">AccX</output>
            <output component="y">AccY</output>
            <output component="z">AccZ</output>
            <output component="t">AccT</output>
        </sensor>
        <audio rate="48000">
            <output>recording</output>
        </audio>
    </input>
    ...
</phyphox>
```

### Input module: audio

```xml
<audio rate="INTEGER" append="false">
    <output>BUFFER</output>
    <output component="rate">BUFFER</output>
</audio>
```

The audio tag defines audio as a data source (i.e. a microphone). Phyphox will record continously and write the recording to the buffer at the beginning of an analysis execution (see analysis block). The target buffer is defined with a simple output-tag.

The default recording rate is 48kHz, but can be changed using the *rate* attribute (in Hz). However, this is not recommended if the experiment targets a wide audience since supported recording rates are very device specific. Also, the rate you set is not guaranteed. Instead you should read the actual rate from the rate output (see example above) and use that for any calculations that use a time base. Note that the rate output is written independently from the recording output (mostly when the rate changes, which usually only should happen if the audio setup changes). Therefore you should not delete this buffer while reading it. The rate output is **available since phyphox file format 1.6 (phyphox 1.0.10)**

rate
:   The recording rate in Hz.
:   *optional*, default: 48000

append
:   Append data to the output buffer instead of only offering new data since the last analysis cycle. **Available since file format 1.16 (phyphox version [version 1.1.12](../reference/version-history/1.1.12.md)).**
:   *optional*, default: false (buffer contains only new data)

### Input module: bluetooth

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

The bluetooth block defines an input from a Bluetooth Low Energy device. Please refer to the documentation on the [Bluetooth Low Energy](bluetooth-low-energy.md) interface in phyphox for details.

### Input module: camera

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<camera x1="FLOAT" x2="FLOAT" y1="FLOAT" y2="FLOAT" autoExposure="BOOLEAN" aeStrategy="STRING" aeFPSTarget="FLOAT" locked="STRING" feature="STRING">
    <output component="t">BUFFER</output>
    <output component="luma">BUFFER</output>
    <output component="luminance">BUFFER</output>
    <output component="hue">BUFFER</output>
    <output component="saturation">BUFFER</output>
    <output component="value">BUFFER</output>
    <output component="shutterSpeed">BUFFER</output>
    <output component="iso">BUFFER</output>
    <output component="apertue">BUFFER</output>
</camera>
```

Get data from the phone's camera(s). At the time of phyphox file format 1.19 (phyphox 1.2.0) this data is photometric data, but this is expected to be expanded in the future.

**Photometric measurements**

When *feature* is set to "photometric" (the default if you omit this attribute), you can collect various photometric properties from a stream of camera frames. For each frame you will get a single value like luminance or hue. The coordinates x1, y1 and x2, y2 mark a rectangle from the camera image (ranging from 0 to 1 from one edge of the image to the other) that is taken into account to calculate the value.

The remaining attributes control the exposure settings of the camera. *autoExposure* can enable or disable automatic exposure adjustments to adapt the brightness. This auto exposure does not use the phone's internal auto exposure, but is an implementation within phyphox that can be set to use a specific *aeStrategy*. These strategies determine if the the auto exposure should prefer framerate over the ideal exposure or if it should avoid overexposure more aggressively.

The camera input is typically used together with a *camera-gui* view element (see view elements), which shows a preview and allows the user to adjust x1, x2, y1 and y2 along with auto exposure, exposure settings or zoom. In this case, the values set here are just the initial value.

The *locked* attribute takes a string that specifically sets certain exposure properties to a fixed value. These properties are then also blocked in the *camera-gui* interface, preventing the user from changing them. Multiple properties are separated by a comma. They can also be set to a specific value with an equal sign followed by a floating point value (fractions can also be used to express the value). However, be aware that the same settings will have very different results for different phone models, espacially as the aperture cannot be controlled on most phones.

The available locks are: *shutter_speed*, *iso*, *exposure*, *aperture*, *focus_distance* (since phyphox file format 1.20 (phyphox 1.2.1) Note that aperture is not supported on iOS as there are no iPhones with adjustable aperture and that this is untested on Android as it is also rare here. *exposure* is the exposure value when using the simplified exposure control (see camera-gui).

So, for example, setting *locked* to *iso* will prevent the user from changing iso values. Setting it to *iso=1600* will also set it to a specific value and setting the attribute to *iso=100,shutter_speed=1/240* will lock the camera to ISO 100 with an exposure time of 1/240s.

*focus_distance* was added in **phyphox file format 1.20 (phyphox 1.2.1)** to allow disabling auto focus and setting the focus distance to a fixed position. The distance is given in meters with the special case of zero representing a focus at infinity.

The framerate of your measurement will depend on your phone's camera. Different cameras on the same phone can have different framerates and the exposure setting can also reduce the framerate if the exposure time (shutter speed) is longer than the duration of a frame. This could be a reasong to lock the shutter_speed, but in most scenarious the better solution is using an auto exposure strategy *aeStrategy* for this.

The photometric properties are calculated on the GPU, so keeping up a high framerate is not limited by processing power on most phones.

The possible outputs are:

t
:   Timestamp of the frame

luma
:   Luma (non-linear brightness relative to the image's color range) of the selected area in the range from 0 to 1

luminance
:   Relative luminance in arbitrary units. This is linearized (gamma corrected) and adjusted for the exposure paramters such that the value 1 represents a white image when the camera is set to ISO 100, a shutter speed of 1/60s and an aperture of f/1.

hue
:   Hue according to the HSV color model, ranging from 0° to 360°. (Note that this is a cyclic average of the pixels in the selected area.)

saturation
:   Saturation according to the HSV color model, ranging from 0 to 1

value
:   Value according to the HSV color model, ranging from 0 to 1

shutterSpeed
:   Shutter speed used to take this frame

aperture
:   Aperture used to take this frame

iso
:   ISO value used to take this frame

Note that the shutter speed, aperture and ISO can change their value even though it takes a few more frames for them to take effect. This can happen as the phone smoothly ramps the values when the settings have been changed or there is a delay between setting change and execution.

Details about the attributes for the *camera* input element:

x1, x2, y1, y2
:   Sets the initial acquisition area, which can still be modified by the user. x1 and x2 describe the horizontal limits and y1 and y2 the vertical ones. The values are floating point values ranging from 0.0 to 1.0, with 0.0 refering to the left/top edge of the image and 1.0 to the right/bottom edge.
:   *optional*, default: 0.4, 0.6, 0.4, 0.6

autoExposure
:   Determines whether auto exposure is enabled after loading the experiment
:   *optional*, default: true

aeStrategy
:   Determines the strategy to find the optimal exposure settings. The following values can be given:

    mean
    :   The goal is to achieve a mean luma of 0.5 in the selected area. Exposure times shorter than the frame duration are preferred, so ISO settings will be used first, but if the scene is dark, exposure times can go down to 1/15s, significantly limiting the frame rate.

    avoidUnderexposure
    :   Like *mean*, but if one or more pixels are particularly dark, this strategy will brighten the image even if the mean luma goes above the target of 0.5.

    avoidOverexposure
    :   Like *avoidUnderexposure*, but aiming for a darker image if some bright pixels are close to overexposure.

    prioritizeFramerate
    :   Like *mean*, but the hard limit of the longes possible exposure time is the frame duration of the highest possible framerate. So, this strategy accepts under exposure to achieve the highest possible framerate at all cost. (also see *aeFPSTarget* below)
:   *optional*, default: mean

aeFPSTarget
:   Set a target framerate when using *aeStrategy* *prioritizeFramerate*. If this is not set, *prioritizeFramerate* will default to the shorted supported frame duration (inverse of max framerate). If it is set, the target FPS acts as a maximum exposure time to at least achieve the set FPS. It does not prevent the camera from going above the target FPS.
:   *optional*, default: 0, **Available since phyphox file format 1.3 (phyphox 1.0.4)**

locked
:   A string that locks some values preventing the user from changing them through a camera-gui element. Specific values can also be given. See explanation and examples above.
:   *optional*, default: not used

feature
:   This determines the kind of camera analysis. At the moment the only option and the default is *photometric*.
:   *optional*, default: photometric

### Input module: depth

**Available since phyphox file format 1.14 (phyphox 1.1.10)**

```xml
<depth mode="AGGREGATIONMODE" x1="FLOAT" x2="FLOAT" y1="FLOAT" y2="FLOAT" smooth="BOOLEAN">
    <output component="z">BUFFER</output>
    <output component="t">BUFFER</output>
</depth>
```

Get a depth measurement from the depth sensor, which is typically a dedicated optical sesor as part of the camera array. On iOS, this type of sensor is called "LiDAR", while on Android you usually have to look for "ToF". Both systems have very different APIs to access this data with various advantages and drawbacks:

On iOS we access the LiDAR sensor through ARkit, which is the framework for augmented reality applications. The depth data is almost perfectly aligned with the camera image, but it is not raw data from the sensor, but processed and remapped for AR applications. Therefore, the data might have been fused with depth data derived from the normal color camera (for example depth estimation from parallax effects). Newer iOS devices also feature a depth sensor on the front, which is designed for FaceID, but this is available through an entirely different API and may be supported by phyphox in the future. (Details on Apple's API can be found at <https://developer.apple.com/documentation/arkit/ardepthdata>)

On Android we decided against using ARcore, Google's augmented reality framework, as a more direct API is available and dependencies on Google Services could be avoided in favor of platforms that do not have Google support. Here we use the camera2 API to access the sensor data, which has the benefit that we do not expect any fusion with AR data. However, the disadvantage is that the depth data has not been remapped to align with the regular camera image and you will experience an offset, which in particular will depend on the viewing distance as camera and sensor are placed at a distance in the phone's case. The camera2 API allows for accessing front and back facing depth sensors, but be aware that some phones advertise a ToF sensor for camera autofocus without exposing its data through the camera2 API. (Details on the camera2 API can be found at: <https://developer.android.com/reference/android/hardware/camera2/package-summary>)

Typically the user selects an area within the camera/depth data (which can be preset using the attributes x1, x2, y1, y2) that is aggregated into one depth value per frame. For each frame a pair of an aggregated depth value "z" and the corresponding timestamp "t" will be returned. There are currently three aggregation methods for all data points within the selected area: "average" takes the average value, "closest" the data point with the smallest distance to the camera and "weighted" creates the weighted average using the confidence data provided by each API. Note that phyphox automatically drops the lowest confidence value and that lower confidences typically only appear at edges and represent a small portion of most scenes. Therefore, the difference between "average" and "weighted" should be negligible for most situations.

In order to give the user a preview and control over the depth input, you will want to also add a depth-gui view element to the configuration (see in the views section).

mode
:   Defines the aggregation method and can be "average", "closest" or "weighted" (see description above).
:   *optional*, default: closest

x1, x2, y1, y2
:   Sets the initial acquisition area, which can still be modified by the user. x1 and x2 describe the horizontal limits and y1 and y2 the vertical ones. The values are floating point values ranging from 0.0 to 1.0, with 0.0 refering to the left/top edge of the image and 1.0 to the right/bottom edge.
:   *optional*, default: 0.4, 0.6, 0.4, 0.6

smooth
:   Only applies to LiDAR on iOS devices. Can be set to true or false, to use smoothedSceneDepth (https://developer.apple.com/documentation/arkit/arframe/3674209-smoothedscenedepth) or sceneDepth (https://developer.apple.com/documentation/arkit/arframe/3566299-scenedepth), employing ARkits smoothing or not.
:   *optional*, default: true

### Input module: location

**Available since phyphox file format 1.5 (phyphox 1.0.7)**

```xml
<location>
    <output component="x">BUFFER</output>
    ...
    <output component="t">BUFFER</output>
</location>
```

The location block defines an input from the GPS sensor. The data will be written to the output buffers at the rate as it is provided from the sensor. On Android, the location data is expected to come from satellite navigation exclusively (although some unusual implementations may occur), but on iOS we cannot deactivate other sources. Therefore in most cases on iOS the first reading is based on the mobile and WIFI networks.

There are several components for the outputs:

t
:   Experiment time (seconds since start of experiment) for the location (as set by the operating system)

lat
:   Latitude in degree

lon
:   Longitude in degree

z
:   Elevation (note that elevation provided by GPS is generally rather imprecise) in meters (using EGM84 geoid as reference, i.e. "above see level")

zwgs84
:   Same as z but taking the WGS84 ellipsoid as reference (i.e. the coordinate system used by GPS). Note that the Android API provides WGS84 ellipsoid elevation while the iOS API provides EGM84 geoid elevation. Phyphox calculates the difference using a port of GeographiLib's algorithm with a 30' resolution EGM84 dataset (see <https://geographiclib.sourceforge.io/>).

v
:   Speed (provided by the system, based on consecutive GPS fixes) in m/s

dir
:   Direction (determined by the system along with the speed) in degree (counted from north towards east)

accuracy
:   An estimate by the system of the horizontal accuracy in meters

zAccuracy
:   An estimate by the system of the vertical accuracy in meters (not on Android)

satellites
:   Number of satellites used for this measurement (not on iOS)

status
:   -1 means that GPS is unavailable (usually deactivated by the user), 0 means that it is searching for a signal, 1 means that it is active. 2 means active, but the altitude is given above the WGS84 ellipsoid instead of the geoid, which can happen in the case of very basic GPS implementations on some (mostly cheap) phones. Note that this value is updated independently from the other outputs.

The location tag has no additional attributes.

### Input module: sensor

```xml
<sensor type="TYPE" average="BOOLEAN" rate="FLOAT" rateStrategy="STRATEGY" stride="INTEGER" ignoreUnavailable="BOOLEAN">
    <output component="x">BUFFER</output>
    ...
    <output component="t">BUFFER</output>
</sensor>
```

The sensor block defines a sensor as an input. The data will be written to the output buffers at the rate as it is provided from the sensor. Alternatively, you may define a different *rate*, in which case the latest reading is picked at the given rate. In addition you may turn on averaging in combination with the forced rate, in which case all data during the interval of the rate is averaged and only the average is written to the buffer. The exact strategy to achieve the target rate can be defined by the parameters *rateStrategy* and *stride*. Please see details about this in the explanation of these parameters and note that these have been introduced with a behavior change in file format 1.14 (phyphox 1.1.10).

Many sensors (accelerometer, magnetometer, gyroscope) are 3D sensors writing to a total of four buffers (x, y, z and timestamp t), but you do not need to attach a buffer to all outputs. Also some sensors are only 1D (pressure, light) and will only fill the x buffers. The outputs are mapped to data-containers by simple output-tags. Each requires a *component* attribute set to *x*, *y*, *z* or *t* to map the data o the data-container.

Since file format version 1.4 (phyphox 1.0.6) there is another output *abs* which gives the absolute (sqrt(x\*x+y\*y\*z\*z)) for 3D sensor data.

Since file format version 1.5 (phyphox 1.0.7) there is another output *accuracy* which gives information about the current accuracy. Typically, "-1" means that the sensor is uncalibrated (which might be an error state), "0" means that uncalibrated raw data is presented (but this is expected) and positive values represent accuracy in a way specific to the sensor. This is currently only used by the magnetometer, which encodes its accuracy as 1 low, 2 medium and 3 high.

If a sensor is not available on the device, the experiment will notify the user and refuse to work.

Note, that the somewhat cumbersome names for "acceleration with g" and "acceleration (without g)" have been chosen to aid students in understanding the data given by these sensors. But internally we stick to the names commonly used in the Android as "accelerometer" and "linear_acceleration". Usually, "accelerometer" (the one with g) is a physical sensor which measures the acceleration force applied to a sample mass (in form of a MEMS device), so it will give a constant acceleration of 9.81 m/s² for a resting device (hence our descriptive name "with g"). In contrast, "linear_acceleration" is usually just a virtual sensor, which may use additional sensors to remove the earth's acceleration (hence our descriptive annotation "without g") to report the actual acceleration of the phone in the reference system of the user. So "linear_acceleration" will report zero acceleration when the phone is resting and moved at a constant speed.

type
:   Defines the sensor type to be used. Allowed values:

    accelerometer
    :   The accelerometer in m/s². This gives the earth's acceleration when the device is resting. (Usually named "acceleration with g" in phyphox)

    linear_acceleration
    :   A virtual sensor giving the actual acceleration of the device. Should report zero when the device is resting. (Usually named "acceleration (without g)" in phyphox)

    gravity
    :   A virtual sensor giving the gravitational acceleration in the frame of reference of the device. This removes the device motion from the accelerometer readings and should therefore be approximately the difference of accelerometer and linear_acceleration. (Depending on the implementation on each device.) Available since file format 1.15 (phyphox 1.1.11)

    magnetic_field
    :   Readings from the magnetometer in µT

    gyroscope
    :   Readings from the gyroscope in rad/s.

    humidity
    :   Relative humidity in %. Available since file format 1.7 (phyphox 1.1.0)

    light
    :   The illuminance from the light sensor in lx

    pressure
    :   The air pressure from the barometer in hPa

    proximity
    :   Distance from the proximity sensor in cm (most devices only output 0cm or 5cm)

    temperature
    :   Temperature. This is supposed to be ambient temperature, but we have some fallback logic to find any temperature reading from the device. This usually represents the device temperature and cannot be used for external temperature measurement. (in °C) Available since file format 1.7 (phyphox 1.1.0)

    attitude
    :   The orientation (absolute rotation) of the device as calculated by the device's own algorithms. This uses TYPE_ROTATION_VECTOR on Android and "CMAttitude" from Core Motion on iOS, which (depending on the device) fuses data from the accelerometer, gyroscope and magnetometer to calculate the attitude of the device. The result is given as a quaternion in a reference system with y pointing towards magnetic North and z pointing upwards (the Android coordinate system, iOS attitude is converted to this system). The *x*, *y* and *z* channels correspond to the last three components of the quaternion (w, x, y, z) and w can be retrieved through the *abs* channel. Available since file format 1.9 (phyphox 1.1.5)

    custom
    :   Use typeFilter and/or nameFilter to use a sensor that is not directly supported by phyphox. You can check the device info (i menu on main screen) to see which sensors are available on your phone. Phyphox will pick the first sensor with a type that matches the typeFilter (if set) and a name that contains the value of nameFilter (not case-sensitive, only if set). Note, that not all sensors will work properly with phyphox, especially if they do not generate values but events or states. Available since file format 1.19 (phyphox 1.2.0)
:   *required*

rate
:   The rate at which sensor data will be provided in Hz. A value of 0.0 means "as fast as possible". Note that the maximum rate of a sensor is device-specific and will limit the rate that can be achieved.
:   *optional*, default: 0.0

average
:   If set to true, instead of just giving the latest reading at the defined rate, the sensor data will be averaged over a period of the rate. This only makes sense if a rate is set, which is lower than the maximum rate the device can achieve.
:   *optional*, default: false

rateStrategy
:   Defines the strategy to achieve the rate set with the attribute *rate*. Available since file format 1.14 (phyphox 1.1.10)

    auto
    :   Requests the target sensor rate directly from the system like the strategy *request*. If the actual rate provided by the system is more than 10% faster than the requested rate, the strategy automatically switches to *generate*, delivering the data points exactly at the desired rate. This is strategy prevents duplicate data points as both strategies cannot be faster than what the sensor provides and it picks the ideal method to achieve get close to the target rate. However, in cases when it has to switch to *generate* it is susceptible to strong sampling effects when the target rate is close to the actual sensor rate.

    request
    :   The target rate set by *rate* is directly requested from the system and the provided sensor data will be provided as is. It depends on the system if the provided rate is close to the requested one and the system might not be able to provide sensor data at given rates or it might decide to provide a different rate if the sensor data is shared with other apps. This strategy is most likely to yield a rate that strongly differs from the expected one, but as it will not group or discard data points, it will not introduce additional sampling or aliasing effects. For the same reason, the *average* attribute has no effect.

    generate
    :   The target rate is generated internally by phyphox while requesting the highest possible rate from the system. It is guaranteed to give data points at the rate set by *rate* and can even exceed the sensor rate (be careful not to waste performance with this). While the resulting data points seem very easy to interpret afterwards and while it makes it easy to synchronize different sensors, this strategy can severely degrade the recorded sensor data as data points might be duplicated or discarded in unforeseen patterns. If the target rate is close to the actual internal sensor rate, this will very likely introduce additional sampling effects like aliasing between the sensors sample rate and this target rate. Therefore, this strategy is recommended for educational purposes to simplify data analysis, but if you know how to analyze data and want the best possible data quality, it is highly recommended to use the *request* strategy instead as you can emulate the *generate* strategy in your data analysis later, but you could not go back to the quality of *request* from *generate* data.

    limit
    :   The maximum sensor rate is requested by the system and the setting of *rate* is used as a limiter. More precisely, phyphox generates a new data point whenever the time interval from the last data point to the latest sensor event exceeds 1/*rate*. The resulting rate will always be close to but lower than the requested rate and the actual rate strongly depends on the actual sensor rate. This strategy is a compromise to get close to a target rate without the strong degradation introduced by the *generate* strategy as it usually leads to a similar number of sensor events per actually generated data points. The downside is that the data point rate may be quite different on different devices if the target rate is in the range of typical sensor rates. Note that this was the only rate strategy before file format 1.14 (phyphox 1.1.10) and that this is the default behavior if your phyphox-file targets a file format before 1.14.
:   *optional*, default: "auto" (Note, that experiment configurations with a file format below 1.14 will default to "limit" to assure backwards compatibility with the old behavior)

stride
:   If stride is set to N, only every Nth data point generated by the *rateStrategy* (see above) is used. Other data points are simply discarded. A stride of 1 will use every data point, a stride of 2 only every second, a stride of 3 only every third and so on. This is mostly useful to achieve a very specific data rate on a specific device that is a integer fraction of the actual sensor rate in order to avoid additional aliasing effects from non-fractional rates. Available since file format 1.14 (phyphox 1.1.10)
:   *optional*, default: "1" (use every data point)

ignoreUnavailable
:   Allow the user to open and start the experiment even if the sensor is not available. You won't receive any data for that server if it is not available and your experiment should still work and make sense for the user if this is the case. Available since file format 1.8 (phyphox 1.1.3)

typeFilter
:   See custom sensor type. Available since file format 1.19 (phyphox 1.2.0)
:   *optional*, default: not set

nameFilter
:   See custom sensor type. Available since file format 1.19 (phyphox 1.2.0)
:   *optional*, default: not set

## Block: output

The input block defines all hardware outputs such as the speaker used in the experiment.

```xml
<phyphox version="1.0">
    ...
    <output>
        <audio rate="48000" loop="true">
            <input>waveform</input>
        </audio>
    </output>
    ...
</phyphox>
```

### Output module: audio

```xml
<audio rate="INTEGER" loop="BOOLEAN" normalize="BOOLEAN">
    <input>BUFFER</input>
    <tone waveform="STRING">
        <input parameter="pan" type="VALUE/BUFFER">VALUE/BUFFER</input>
        <input parameter="amplitude" type="VALUE/BUFFER">VALUE/BUFFER</input>
        <input parameter="frequency" type="VALUE/BUFFER">VALUE/BUFFER</input>
        <input parameter="duration" type="VALUE/BUFFER">VALUE/BUFFER</input>
    </tone>
    <tone waveform="STRING">
        <input parameter="pan" type="VALUE/BUFFER">VALUE/BUFFER</input>
        <input parameter="amplitude" type="VALUE/BUFFER">VALUE/BUFFER</input>
        <input parameter="frequency" type="VALUE/BUFFER">VALUE/BUFFER</input>
        <input parameter="duration" type="VALUE/BUFFER">VALUE/BUFFER</input>
    </tone>
    <noise>
        <input parameter="pan" type="VALUE/BUFFER">VALUE/BUFFER</input>
        <input parameter="amplitude" type="VALUE/BUFFER">VALUE/BUFFER</input>
        <input parameter="duration" type="VALUE/BUFFER">VALUE/BUFFER</input>
    </noise>
</audio>
```

The audio tag defines audio as an output (i.e. a speaker). The audio waveform can be composed from one or multiple sources:

**input** An input tag on the immediate level below *audio* denotes a direct source. At the end of an analysis period phyphox will write the input buffer to an internal audio buffer and start the playback, so the sound is played after each analysis execution. It has a fixed amplitude of 1 and the duration is defined by the number of samples in the input buffer. Audio data is represented by values ranging from -1 to +1. Only one direct source is supported.

**tone** A **tone** block represents a parametric tone generator. Its parameters **amplitude**, **duration** and **frequency** can either be fixed values (type="value") or a buffer (type="buffer", default) to control it dynamically. Each tone block (multiple are allowed) generates a sine tone and keeps track of the momentary phase of the sine function to avoid click noises due to mismatch of the frequency and the sampling rate or when changing the frequency. **Available since file format 1.10 (phyphox version [version 1.1.6](../reference/version-history/1.1.6.md)).**

Since file format 1.19 (phyphox version [version 1.2.0](../reference/version-history/1.2.0.md)) the tone tag also has an attribute *waveform*, which can be set to *sine* (the default), *square* or *sawtooth* to generate sine, square or sawtooth waves.

**noise** A **noise** block represents a generator for white noise. Its parameters **amplitude** and **duration** can either be fixed values (type="value") or a buffer (type="buffer", default) to control it dynamically. Only one *noise* block is supported. **Available since file format 1.10 (phyphox version [version 1.1.6](../reference/version-history/1.1.6.md)).**

Playback is triggered after each analysis process and each source can have individual durations (in seconds) and amplitudes (float value with 0.0 being silent and 1.0 maximum amplitude without clipping). If loop is set to true, the playback will loop. The default playback rate is 48kHz, but can be changed using the *rate* attribute (in Hz). However, this is not recommended if the experiment targets a wide audience since supported playback rates are very device specific.

Since **file format 1.20 (phyphox version 1.2.1)** all inputs support panning from left to right, mapped to values from -1 (left) to +1 (right) with 0 being center. Note that this does not compensate for amplitude or loudness, but instead a center tone will be played at full amplitude on both channels and a pan to the right will not change the amplitude on the right channel but reduce the one on the left (and vice versa).

rate
:   The recording rate in Hz.
:   *optional*, default: 48000

loop
:   Loop playback
:   *optional*, default: false

normalize
:   Normalize the amplitude of all inputs to achieve a total amplitude of 1. If the sum of all inputs exceeds 1 and this options is disabled, distortions might occur as the momentary amplitude might exceed 1 and get truncated. **Available since file format 1.10 (phyphox version [version 1.1.6](../reference/version-history/1.1.6.md)).**
:   *optional*, default: false

### Output module: bluetooth

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

The bluetooth block defines an output to a Bluetooth Low Energy device. Please refer to the documentation on the [Bluetooth Low Energy](bluetooth-low-energy.md) interface in phyphox for details.

### Output module: flashlight

**Available since phyphox file format 1.20 (phyphox 1.2.1)**

```xml
<flashlight>
    <input parameter="intensity" type="VALUE/BUFFER">VALUE/BUFFER</input>
    <input parameter="frequency" type="VALUE/BUFFER">VALUE/BUFFER</input>
    <input parameter="dutycycle" type="VALUE/BUFFER">VALUE/BUFFER</input>
</flashlight>
```

The flashlight tag defines the phone's flashlight (usually part of the camera group) as an output. If frequency and dutycycle are not set, you can simply control the brightness of the flashlight (including turning it off) via the **intensity** input. If **frequency** is set to a value above 0, the flashlight acts as a stroboscope with the given frequency. You can also change the duty cycle through the **dutycycle** input.

Note, that most phones cannot switch the flash state faster than 25ms. High frequencies or duty cycles far from 0.5 will require faster changes and may not be reproduced correctly by the phone. Phyphox cannot measure how fast the flashlight reacts and the reaction time may even vary from switch event to switch event. So be careful to verify if it is working correctly if fast switches are required.

**input (intensity)** The **intensity** input controls the brightness of the flashlight. It can be set from 0 (off) to 1 (max brightness). The number of supported brightness levels varies from phone to phone and older models might only support an on and off state. (Default: 1 / max brightness)

**input (frequency)** The frequency of the strobe output. If this is set to zero, the flashlight will be on constantly. (Default: 0)

**input (dutycycle)** The duty cycle of the strobe output. This is given in the range from 0 (always off) to 1 (always on). The default is 0.5 (equal on/off durations). (Default: 0.5)

## Block: analysis

The analysis block describes all the math required for the experiment. Each element within this block is executed consecutively and usually reads from a data-container, performs a mathematical operation on the data and writes the results to another data-container.

In most experiments the analysis block is executed in a loop, so the experiment data is analysed as fast as possible. However, if you need to aquire a certain amount of data first (mostly when recording from the microphone) or if the results only change if the user changes a parameter, you can define the attributes *sleep*, *dynamicSleep* and/or *onUserInput* to pause the analysis loop.

sleep
:   The minimum time in seconds before the whole analysis block is executed again after the last execution has finished. Decimal values allowed.
:   *optional*, default: '0.0' (immediately)

dynamicSleep
:   The minimum time in seconds before the whole analysis block is executed again after the last execution has finished. This refers to a buffer, so the sleep time can be set by the analysis result. If the buffer is empty, the value from *sleep* is used instead. **Available since phyphox file format 1.5 (phyphox 1.0.7)**
:   *optional*, default: not set (no dynamic sleep)

onUserInput
:   If true, the analysis block will not be executed again unless the user changes the content of an input view.
:   *optional*, default: 'false'

requireFill
:   Sets the name of a data container that needs to be filled. The attribute requireFillThreshold or requireFillDynamic define a required number of elements in the data container (default 1 element). If this number is not fulfilled, the analysis block is skipped. **Available since phyphox file format 1.16 ([phyphox 1.1.12](../reference/version-history/1.1.12.md))**

requireFillThreshold
:   A static integer number setting the threshold for the requireFill attribute. **Available since phyphox file format 1.16 ([phyphox 1.1.12](../reference/version-history/1.1.12.md))**
:   *optional*, default: '1'

requireFillDynamic
:   A dynamic value for the required number of elements in the data container defined by requireFill. This attribute points to another data container, which defines this value. If it is empty, the value from requireFillThreshold is used instead. **Available since phyphox file format 1.16 ([phyphox 1.1.12](../reference/version-history/1.1.12.md))**
:   *optional*, default: '' (requireFillThreshold used instead)

timedRun
:   Enable the timed run setting by default. This just acts as a preset. The user can still deactivate it from the main menu. **Available since phyphox file format 1.10 ([phyphox 1.1.6](../reference/version-history/1.1.6.md))**
:   *optional*, default: 'false' (deactivated)

timedRunStartDelay
:   Start delay in seconds for the timed run setting. This just acts as a preset. The user can still change it from the main menu. Also, this does not enable the function by default. To enable it, see *timedRun* above. **Available since phyphox file format 1.10 ([phyphox 1.1.6](../reference/version-history/1.1.6.md))**
:   *optional*, default: '3'

timedRunStopDelay
:   Stop delay in seconds for the timed run setting. This just acts as a preset. The user can still change it from the main menu. Also, this does not enable the function by default. To enable it, see *timedRun* above. **Available since phyphox file format 1.10 ([phyphox 1.1.6](../reference/version-history/1.1.6.md))**
:   *optional*, default: '10'

optimization
:   **Removed in phyphox file format 1.10 (phyphox 1.1.6)** This barely added any value but increased confusion significantly.

```xml
<phyphox version="1.0">
    ...
    <analysis sleep="2.0" dynamicSleep="buffer" onUserInput="false">
        <add>
            <input>Buffer1</input>
            <input type="buffer">Buffer 2</input>
            <output>sumBuffer</output>
        </add>
        <divide>
            <input type="value" as="dividend">1</input>
            <input as="divisor">sumBuffer</input>
            <output>inverseSum</output>
        </divide>
    </analysis>
    ...
</phyphox>
```

### Analysis modules in general

```xml
<input type="TYPE" as="AS">BUFFER/VALUE</input>
<output as="AS">BUFFER</output>
```

Almost all analysis modules take inputs and write their results to an output buffer. All inputs and outputs are defined as *input* and *output* tags within the analysis module. While the output always has to be a data-container, the input may also be a floating point value which can be defined by setting the attribute *type* to *value*. If *type* is not set, it defaults to *buffer* and the given name has to match a data-container. Additionally, the input may be set to the *type* *empty*, which is similar to *value* but represents a constant empty buffer. This only makes sense and is supported for few modules and will be noted there.

Both, inputs and outputs, can be given a specific function by the *as* attribute. For many modules this attribute can be omitted if it is obvious. For example the *add* module takes an arbitrary number of inputs in an arbitrary order (a+b equals b+a), but the *subtract* module needs an explicit mapping for the *minuend* and the *subtrahend* (a-b does not equal b-a). Similarly, a single output does not need to be mapped, while multiple outputs (for example value and position of a maximum in the *max* module) need to be mapped.

Additionally, some analysis modules take parameters that are not dynamically defined, but as an attribute to the analysis module tag. As an example, the *threshold* module searches the point at which the input values cross a given threshold and the attribute *falling* can switch it to look for a crossing from larger to smaller values.

**Since file format version 1.10 (phyphox 1.1.6)** all analysis module support a new attribute that allows to determine whether the module should be executed in each anlysis cycle or only for specific cycles. For this, each run of the analysis process (a cycle) is numbered. When the user opens the experiment and **before** he presses start, analysis is triggered with the cycle number 0, which can be used to prepare some buffers or fill graphs with defaults. After pressing start, the first cycle is number 1, followed by cycle 2 etc.

You can then set the attribute *cycles* for any analysis module. If not set, the module is executed in every cycle (including 0). If set it is only executed in the cycles that you specify by a space separated list. For example, cycles="1 3 42" means that the module is only executed in cycle 1, 3 and 42. You can also define ranges with a simple dash, so cycles="3-6" means that it will be executed in 3, 4, 5 and 6. Open ended lists can be achieved by simply omitting a number, so cycles="1-" will run in every cycle except for 0 and cycles="-5" will run in every cycle up to and including number 5. As a final example, mixing all these, cycles="0 3 5-7 10-" will run in cycle 0, 3, 5, 6, 7, 10 and then every subsequent cycle.

attributes
:   for all analysis modules

    cycles
    :   Determine in which cycles the modules should be executed, see above. default: Execute in every cycle.

<!-- -->

input-tag
:   Attributes for input tags:

    as
    :   The mapping of the input to a function
    :   *optional* or *required* depending on the module

    type
    :   Can be set to *buffer* or *value* and indicates whether the content of the the tag is a numeric value or refers to a data-container
    :   *optional*, default: *buffer*

    keep
    :   *true* will mean, that the buffer retains its data after reading. If set to false, the buffer is cleared after reading, which can be used to process each dataset from an input only once.
    :   *optional*, default: *false*

    clear (deprecated in file format 1.17)
    :   *false* will mean, that the buffer retains its data after reading. If set to true, the buffer is cleared after reading, which can be used to process each dataset from an input only once. Note that this attribute has been deprecated with file format 1.17 (phyphox 1.1.13) and should be repalced with the more intuitive keep attribute. clear=true corresponds to keep=false.
    :   *optional*, default: *true*

<!-- -->

output-tag
:   Attributes for output tags:

    as
    :   The mapping of the input to a function
    :   *optional* or *required* depending on the module

    append
    :   *true* will mean, that new data is appended to the content that is already in the buffer. *false* will clear the buffer first, effectively replacing its content with new data.
    :   *optional*, default: *false*

    clear (deprecated in file format 1.17)
    :   *false* will mean, that the buffer retains its data (from another module writing to this buffer or from the previous analysis run) and new data is appended. *true* will clear the buffer first. Note that this attribute has been deprecated with file format 1.17 (phyphox 1.1.13) and should be repalced with the more intuitive append attribute. clear=true corresponds to append=false.
    :   *optional*, default: *true*

### List of analysis modules

The specific mappings, attributes and functionality of the analysis modules are documented on a separate page listing all the [analysis modules](analysis-modules.md).

## Block: views

The views block may hold one or more *view* blocks (note: singular), describing the different layout groups (views), from which the user may choose to view the experiment data.

At least one view block is required!

```xml
<phyphox version="1.0">
    ...
    <views>
        <view label="Pendulum">
            <value label="Frequency" unit="Hz">
                <input>frequencyBuffer</input>
            </value>
            <edit label="Length" unit="cm" factor="100" signed="false" default="50">
                <output>lengthBuffer</output>
            </edit>
            <info label="Example with user-input" />
        </view>
        <view label="Raw data">
            <graph label="Sensor data x" labelX="Time (s)" labelY="Amplitude">
                <input axis="x">timeBuffer</input>
                <input axis="y">sensorBuffer</input>
            </graph>
        </view>
    </views>
    ...
</phyphox>
```

### Block: view

Each view-block groups display elements to present data to the user. The view block has a single attribute *label* displayed to the user to identify this view when the user switches views. The label should be short and concise.

label
:   The name identifying this view. Will be translated if a matching translation string is defined.
:   *required*

### View-Element: info

```xml
<info color="COLOR" label="INFOTEXT" bold="BOOLEAN" italic="BOOLEAN" align="STRING" size="NUMERIC" />
```

The info element does not take any inputs or write to any outputs. It just displays a string defined as the *label* attribute.

label
:   The text to be displayed to the user
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

color
:   The text color as six-digit RGB hex value or a named choice from the phyphox [Colors](colors.md)
:   *optional*, default: white, **Available since phyphox file format 1.7 (phyphox 1.1.0)**

bold
:   If set to true, the text will be displayed using a bold font. (We cannot guarantee, that the combination of bold and italic is available on every device.) **Available since phyphox file format 1.8 (phyphox 1.1.3)**

italic
:   If set to true, the text will be displayed using an italic font. (We cannot guarantee, that the combination of bold and italic is available on every device.) **Available since phyphox file format 1.8 (phyphox 1.1.3)**

align
:   Can be set to left (default), center or right. The alignment of the text. (Note, that phyphox does not yet support RTL languages, but this attribute is designed to be reverse in such cases.) **Available since phyphox file format 1.8 (phyphox 1.1.3)**

size
:   Sets the font size of the info element as a factor to the default size. Hence, the default is 1. **Available since phyphox file format 1.8 (phyphox 1.1.3)**

### View-Element: separator

```xml
<separator color="orange" height="0.1" />
```

The separator element does not take any inputs or write to any outputs. It just acts as a separator to give a visual aid in grouping other elements. It defaults to a very thin height of 0.1 (in units of text line heights) and a color matching the background color of the experiment screen. To achieve a margin between elements, you should set the height to 1 or to create a narrow line, set the color (as six-digit RGB hex value or a named color from the phyphox [Colors](colors.md)) and leave the height at 0.1 - optionally padded b two other separator elements.

color
:   The color of the whole (rectangular) element as six-digit RGB hex value or a named choice from the phyphox [Colors](colors.md)
:   *optional*, default: background color

height
:   The height of the separator in text line heights
:   *optional*, default: 0.1

### View-Element: value

```xml
<value label="LABEL" size="FLOAT" precision="INTEGER" scientific="BOOLEAN" unit="UNIT" factor="FLOAT" format="STRING" color="COLOR">
    <input>BUFFER</input>
    <map min="DOUBLE" max="DOUBLE">STRING</map>
    <map>STRING</map>
</value>
```

The value element displays a single value to the user. If the input buffer contains more than one value, the latest value will be displayed. The input is defined by a simple *input* tag within the value block and needs to be a data-container (see above).

Since file format version 1.5 (phyphox 1.0.7) you can define range mappings with the map-tag. The map tag includes a string which will replace the number and unit that would be displayed otherwise. phyphox will test all mappings in the order they are given and replace the output with the first mapping that applies. A mapping applies if the value to be shown falls in the range given by the attributes *min* and *max* (inclusive). *min* and *max* can be left out and default to negative and positive infinity. So, a map-tag without any attributes acts as a catch-all case.

Since file format version 1.19 (phyphox 1.2.0) the attribute gives even more options to change how the value is displayed, like for example showing GPS coordinates not only as decimal value, but as degrees, minutes and seconds. Also the positiveUnit and negativeUnit allow to change the unit depending on the value's sign. In case of the GPS coordinate example, this allows to use N (for north) on positive latitude and S (for south) on negative latitudes behind the value.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

color
:   The text color as six-digit RGB hex value or a named choice from the phyphox [Colors](colors.md)
:   *optional*, default: white, **Available since phyphox file format 1.7 (phyphox 1.1.0)**

size
:   The size of the displayed value relative to the default font size. Label and unit will stay at their original size. **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: 1

precision
:   The number of digits after the decimal point.
:   *optional*, default: 2

scientific
:   If set to true, the value will be displayed in scientific notation (1.0e-3 instead of 0.001)
:   *optional*, default: false

unit
:   A unit to be displayed after the value
:   *optional*, default: no unit

positiveUnit
:   Replace the regular unit with this if the value is positive.
:   *optional*, default: no unit, **Available since phyphox file format 1.19 (phyphox 1.2.0)**

negativeUnit
:   Replace the regular unit with this if the value is negative.
:   *optional*, default: no unit, **Available since phyphox file format 1.19 (phyphox 1.2.0)**

factor
:   A factor to be applied to the value before displaying it. This is usually used for unit conversion. Example: The data is in meter, but should be displayed in cm. The factor would be 0.01
:   *optional*, default: 1.0

format
:   Choose alternative formats to show the value. Options are:

    float
    :   Show a simple decimal value (with significant digits, scientific notation etc. as defined by the other attributes)

    degree-minutes
    :   Split the decimal part of the value of and show it separately in minutes (part of 60). The output is formatted as degrees and minutes and the attribute *precision* affects the minutes part in this format. Example: 42.385 becomes 42° 23.1'

    degree-minutes-seconds
    :   Split the decimal part of the value of and show it separately in minutes (part of 60) and seconds (part of 3600). The output is formatted as degrees, minutes and seconds and the attribute *precision* affects the seconds part in this format. Example: 42.385 becomes 42° 23' 6"

    ascii
    :   Convert all values in the data-container to their ASCII character representation and show it as text. Non-integer values and those outside the range \[32,125\] will be skipped.
:   *optional*, default: float, **Available since phyphox file format 1.19 (phyphox 1.2.0)**

### View-Element: graph

```xml
<graph label="LABEL" aspectRatio="FLOAT" style="STYLE" partialUpdate="BOOLEAN" labelX="LABELX" labelY="LABELY" timeOnX="BOOLEAN" timeOnY="BOOLEAN" linearTime="BOOLEAN" systemTime="BOOLEAN" hideTimeMarkers="BOOLEAN" logX="BOOLEAN" logy="BOOLEAN" xPrecision="INTEGER" yPrecision="INTEGER" minX="0" maxX="0" minY="0" maxY="0" scaleMinX="auto" scaleMaxX="auto" scaleMinY="auto" scaleMaxY="auto" followX="false" lineWidth="1" color="orange" pickLabel="LABEL">
    <input axis="x">XBUFFER</input>
    <input axis="y">YBUFFER</input>
</graph>
```

The graph element will show a plot of the YBUFFER data against the XBUFFER data. The input buffers are defined by *input* tags within the value block and need to be a data-containers (see above). The input tags are linked to the axes with an additional *axis* attribute to the input tag, which may be *x* or *y*. See below for additional option for other graph types.

The resulting graph can be made up of lines (default) or dots (set attribute *style* to *dots*). (see attribute descriptions below)

The attributes *partialUpdate* is used for performance optimization. *PartialUpdate* should be set to true when the buffer is never changed entirely, but new data is just appended with increasing x values. *PartialUpdate* will then allow that only this data is transferred in the web-interface to save bandwidth.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

apectRatio
:   The ratio of the total width of this element to the total height of this element in the view. (Including labels and axes)
:   *optional*, default: 3

style
:   If set to *dots*, the graph will not connect the values with lines. See below for additional styles introduced with file format 1.7 (phyphox 1.1.0).
:   *optional*, default: display lines

partialUpdate
:   If set to true, this allows optimizations which only work if the data is appended with increasing x values. A typical example is sensor data: Only few new values are added and each data point has a greater timestamp than the previous one. In such cases this should be set to true as it allows the web interface to only transfer these new datapoints.
:   *optional*, default: false

labelX
:   The label of the x axis
:   *optional*, default: empty, but you should always label your axes... (Note that since file format 1.7 (phyphox 1.1.0) you should set the unit separately in the attribute unitX)

labelY
:   The label of the y axis
:   *optional*, default: empty, but you should always label your axes... (Note that since file format 1.7 (phyphox 1.1.0) you should set the unit separately in the attribute unitY)

unitX
:   The unit of the x axis
:   *optional*, default: empty, the units will be appended to the label, but are also used to give values of individual data points with correct units **Available since phyphox file format 1.7 (phyphox 1.1.0)**

unitY
:   The unit of the y axis
:   *optional*, default: empty, the units will be appended to the label, but are also used to give values of individual data points with correct units **Available since phyphox file format 1.7 (phyphox 1.1.0)**

unitYperX
:   An explicit unit for slopes, if not set, phyphox will use "unitY / unitX".
:   *optional*, default: not set, phyphox will fallback to generate this from x and y unit. **Available since phyphox file format 1.10 (phyphox 1.1.6)**

timeOnX
:   If set to true, the x data needs to be time data in seconds relative to the first start of the experiment. This allows to mark start/pause events and to switch to a system time scale (i.e. absolute date and time) on the x axis. **Available since phyphox file format 1.12 (phyphox 1.1.8)**
:   *optional*, default: false

timeOnY
:   If set to true, the y data needs to be time data in seconds relative to the first start of the experiment. This allows to mark start/pause events and to switch to a system time scale (i.e. absolute date and time) on the y axis. **Available since phyphox file format 1.12 (phyphox 1.1.8)**
:   *optional*, default: false

linearTime
:   If set to true, the time on each axis is interpreted as "linear" time, which is identical to "experiment" time with the difference that the time stamp increases even when phyphox is paused. This especially allows to plot data from external sources that have their own internal clock. In these cases you can use the timer module to get a reference time to shift data from an external clock appropriately. If the graph is shown with system time on the axis, all data is shown, but if the axis is set to experiment time, the data points with linear time corresponding to times during which phyphox was paused will be hidden. If linearTime is set to false, experiment time (the default) is expected. **Available since phyphox file format 1.12 (phyphox 1.1.8)**
:   *optional*, default: false

systemTime
:   If set to true, time axes will start as a system time scale (they can always be switched by the user). **Available since phyphox file format 1.12 (phyphox 1.1.8)**
:   *optional*, default: false

hideTimeMarkers
:   If set to true, no red markers are shown to indicate times at which the experiment was stopped. **Available since phyphox file format 1.14 (phyphox 1.1.10)**
:   *optional*, default: false (= markers are visible)

logX
:   If set to true, the x axis will be on a logarithmic scale
:   *optional*, default: false

logY
:   If set to true, the y axis will be on a logarithmic scale
:   *optional*, default: false

xPrecision
:   The number of significant digits on the x axis. **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: 3

yPrecision
:   The number of significant digits on the y axis. **Available since phyphox file format 1.2 (phyphox 1.0.3)**
:   *optional*, default: 3

suppressScientificNotation
:   If set to true, phyphox will never use scientific notation like 2e-5 instead of 0.00002. This also changes the behavior of xPrecision and yPrecision to refer to decimal digits instead of significant digits. Please make sure that this works well with your measured data as forcing non-scientific notation can lead to extreme numbers in some edge cases. **Available since phyphox file format 1.19 (phyphox 1.2.0)**
:   *optional*, default: false

minX
:   Lowest value on the x axis. Only applied if scaleMinX = fixed
:   *optional*, default: 0

maxX
:   Highest value on the x axis. Only applied if scaleMaxX = fixed
:   *optional*, default: 0

minY
:   Lowest value on the y axis. Only applied if scaleMinY = fixed
:   *optional*, default: 0

maxY
:   Highest value on the y axis. Only applied if scaleMaxY = fixed
:   *optional*, default: 0

scaleMinX
:   Method to scale the minimum of the x axis. auto always scales this value to the minimum of the data set. extend scales to the historic minimum. fixed sets the minimum to minX.
:   *optional*, default: auto

scaleMaxX
:   Method to scale the maximum of the x axis. auto always scales this value to the maximum of the data set. extend scales to the historic maximum. fixed sets the minimum to maxX.
:   *optional*, default: auto

scaleMinY
:   Method to scale the minimum of the y axis. auto always scales this value to the minimum of the data set. extend scales to the historic minimum. fixed sets the minimum to minY.
:   *optional*, default: auto

scaleMaxY
:   Method to scale the maximum of the y axis. auto always scales this value to the maximum of the data set. extend scales to the historic maximum. fixed sets the minimum to maxY.
:   *optional*, default: auto

followX
:   If set to true, the graph follows new data with a fixed x axis scale. This is the same as selecting "follow new" data from the zoom dialog. The width of the x axis has to be defined by setting minX and maxX. Setting followX overrides scaleMinX and scaleMaxX and also forces partialUpdate to true. **Available since phyphox file format 1.15 (phyphox 1.1.11)**
:   *optional*, default: false

lineWidth
:   Width of the graph line relative to the default width
:   *optional*, default: 1

color
:   Color of the graph line as six-digit RGB hex value or a named choice from the phyphox [Colors](colors.md)
:   *optional*, default: phyphox orange

pickLabel
:   Rename the "Pick data" button to show to the user the purpose of the data picker (see data picker feature below). **Available since phyphox file format 1.20 (phyphox 1.2.1)**
:   *optional*, default: Do not change picker label

history
:   **Deprecation warning**: This feature has been marked as depricated and will be removed soon. Please implement it in phyphox analysis logic by using additional data-containers and copying the shown graph into these on each update. This has several advantages like being able to export the history data and better control over its style. Original description: The number of graphs to be shown. 1 means, that the current data is shown. n means, that n graphs are shown, with n-1 graphs containing the data from the previous update. This attribute only makes sense, when the whole graph is replaced on each analysis cycle and can be used to compare the previous n results within a single graph. **Deprecated since phyphox file format 1.15 (phyphox 1.1.12))**
:   *optional*, default: 1

#### Data picker

**Available since phyphox file format 1.20 (phyphox 1.2.1))**

The graph can always be maximized by tapping it, to reveal additional tools like zooming and a data picker. The data picker can be repurposed to allow users to pick and map data to measured data points. This can for example be used to pick a starting point for an automated data analysis or to match points to reference values for a calibration process. You can define how many x, y and z values (in case of a color map plot) the user can pick, label the purpose of each pick and map it to data containers. Optionally, you can also request a value input from the user to map data points to calibration values. Finally, you can also rename the "pick data" button to reflect the use case for the data picker (see "pickLabel" attribute for the graph above.

The data picker is configured by adding outputs that are linked to the target data containers. Here is the most basic example, allowing the user to pick a single x value:

```xml
<graph label="Graph title"  pickLabel="Pick X" ...>
  <input axis="x">datax</input>
  <input axis="y">datay</input>
  <output axis="x" label="Offset X">picked</output>
</graph>
```

This example renames the pick mode to "Pick X" and if the user picks a data point, they will see an additional button "Offset X" as defined by the label-attribute of the output. If the user presses that button, the data-container "picked" will receive the x value of the selected data point.

In addition to allowing picking a point, the user can be allowed to map a value to the point:

```xml
<graph label="Graph title"  pickLabel="Pick X" ...>
  <input axis="x">datax</input>
  <input axis="y">datay</input>
  <output axis="x" label="Offset X">picked</output>
  <output axis="xcal" label="Enter a value to assign to your selected point">assigned</output>
</graph>
```

This example is identical to the previous one, except for having a second output that is assigned to the axis "xcal". This is used together with the axis="x" output and changes the behavior such that when the user presses the "Offset X" button, they will be prompted to enter a value. The label of the xcal output is shown as a prompt and when the user confirms their input, the data-container "picked" receives the x value of the selected point and "assigned" receives the entered value.

You can define an arbitrary number of outputs, assigning them to the axes "x", "y" or "z". Each will show up as a button to the user with the defined "label" of the output. Also, for each axis an additional "xcal", "ycal" or "zcal" can be defined, which will affect the previously defined "x", "y" or "z" output. The following example shows a configuration that allows the user to assign two x values for a spectrum calibration:

```xml
<graph label="Graph title"  pickLabel="Calibrate" ...>
  <input axis="x">datax</input>
  <input axis="y">datay</input>
  <output axis="x" label="Calibration point 1">cal_x1</output>
  <output axis="xcal" label="Assigned wavelength in nm">cal_lambda1</output>
  <output axis="x" label="Calibration point 2">cal_x2</output>
  <output axis="xcal" label="Assigned wavelength in nm">cal_lambda2</output>
</graph>
```

A formula node can then be used to calculate a linear calibration from these two points and generate a new x data set to show a calibrated version in another graph.

#### Other graph types

**Available since phyphox file format 1.7 (phyphox 1.1.0))**

**Bar charts**

Since file format 1.7, you can also use bar charts by setting style to "hbars" or "vbars" for horizontal or vertical bars, respectively. For bar charts, you also define x and y values as you do for line charts, but the x value represents the left edge of a bar while y represents its height (for horizontal bars, y defines the bottom and x the width). Each bar ends where the next one begins and the last height will not be drawn as it only marks the end of the previous bar. Therefore, to draw 4 bars, you need to provide 5 value pairs.

For bar charts, the line width describes the gap between bars. A line width of 1 means that there is no gap, while a line width of 0.5 means that the bars only occupy 50% of the available width (they will be centered in this space).

**Color map charts**

File format 1.7 also introduces color map charts (also known as false color plots). These do not plot y values as a function of x values, but z values as a function of x and y. z is encoded as a color and the result is a map of different colors.

So, you need to provide three datasets, "x", "y" and "z". This is done similar to the traditional 2D plots:

```xml
<graph label="Fourier Transform" logZ="true" labelX="Frequency" unitX="Hz" labelY="Time" unitY="s" labelZ="FFT Mag" unitZ="a.u." aspectRatio="1" style="map" mapWidth="256" partialUpdate="true">
  <input axis="x">fmap</input>
  <input axis="y">tmap</input>
  <input axis="z">fftmap</input>
</graph>
```

The example shows the color map plot of the "Audio Spectrum" experiment. "fmap" contributes the frequencies for the x axis, "tmap" the timestamps for the y axis and "fftmap" the amplitudes that define the colors. Note that all three buffers need to provide the same number of values and that their indices need to match. There is no requirement that each value of each row needs to have exactly the same value, so the value has to be provide for every single data point. However, you cannot just provide arbitrarily distributed data point.

The color map creates a lattice from the provided points, which is then colored. For this, an additional paramtere "mapWidth" is set for the graph-Tag, which defines how many data points form a row. The datapoints within this row may be at slightly varied locations which will be displayed correctly (although the remote interface will not show their location correctly), but very large deviations can lead to a distorted image as connection to the next row won't match up. If you need to plot random data pairs, you might want to check our the [map analysis module](analysis-modules.md#map).

Also note, that due to the typical use of such color maps, the attribute "partialUpdate" (see above) now applies to the y axis, which needs to be monotonous instead of the x axis.

The color map plot introduces the following additional attributes:

labelZ
:   The label of the z axis
:   *optional*, default: empty, but you should always label your axes...

logZ
:   If set to true, the x axis will be on a logarithmic scale
:   *optional*, default: false

zPrecision
:   The number of significant digits on the z axis.
:   *optional*, default: 3

minZ
:   Lowest value on the z axis. Only applied if scaleMinZ = fixed
:   *optional*, default: 0

maxZ
:   Highest value on the z axis. Only applied if scaleMaxZ = fixed
:   *optional*, default: 0

scaleMinZ
:   Method to scale the minimum of the z axis. auto always scales this value to the minimum of the data set. extend scales to the historic minimum. fixed sets the minimum to minZ.
:   *optional*, default: auto

scaleMaxZ
:   Method to scale the maximum of the z axis. auto always scales this value to the maximum of the data set. extend scales to the historic maximum. fixed sets the minimum to maxZ.
:   *optional*, default: auto

mapWidth
:   Number of data points per line.
:   *optional*, but a color map chart won't work without this.

mapColor\[n\]
:   n-th color in the color map
:   *optional*, if none are defined, phyphox uses a black-orange-white color gradient

showColorScale
:   Show or hide the color scale above the color plot
:   *optional*, default: true (**Available since phyphox file format 1.19 (phyphox 1.2.0)**)

interpolateMapColors
:   Interpolate area between data points. If disabled, phyphox expects the datapoints to be aligned on an even spaced rectangular grid and will show each datapoint as a rectangular "pixel" centered on the data point's x/y coordinate. Default behavior is to assign colors to the data point coordinates and interpolate colors inbetween.
:   *optional*, default: true (**Available since phyphox file format 1.20 (phyphox 1.2.1)**)

You can also define your own color palette. Phyphox uses a black-orange-white gradient by default, but introducing more colors can be very helpful to improve contrast. Colors a simply defined as a series of colors that are spread across the z range:

```xml
<graph label="Normalized history" labelX="distance" unitX="cm" labelY="time" unitY="s" labelZ="A" unitZ="a.u." aspectRatio="1" style="map" mapWidth="1200" mapColor1="000000" mapColor2="0000ff" mapColor3="00ffff" mapColor4="00ff00" mapColor5="ffff00" mapColor6="ff0000" mapColor7="ffffff" partialUpdate="true">
  <input axis="x">distance_map</input>
  <input axis="y">time_map</input>
  <input axis="z">weighted_map</input>
</graph>
```

This example shows the colorful palette of the sonar experiment.

**Multiple graphs**

Since file format 1.7 (phyphox 1.1.0) you can also combine multiple graph types (except for the color map). To do so, you can simply define more than one dataset for x and y:

```xml
<graph label="Acceleration" labelX="t" unitX="s" labelY="a" unitY="m/s²" partialUpdate="true">
  <input axis="x" color="green">acc_time</input>
  <input axis="y">accX</input>
  <input axis="x" color="blue">acc_time</input>
  <input axis="y">accY</input>
  <input axis="x" color="yellow">acc_time</input>
  <input axis="y">accZ</input>
  <input axis="x" color="white">acc_time</input>
  <input axis="y">acc</input>
</graph>
```

This example just creates four line charts for the "multi" page of the raw accelerometer experiment. You can define different colors (color attribute), line widths (lineWidth) and plot styles (style as line, dots, vbars or hbars) by applying these attributes to the input tag instead of the graph tag. Here, it does not matter if you define these for the x or y axis, but you should make sure that all inputs are assigned to an axis and that they are ordered correctly.

### View-Element: edit

```xml
<edit label="LABEL" signed="BOOLEAN" decimal="BOOLEAN" min="FLOAT" max="FLOAT" unit="UNIT" factor="FLOAT" default="FLOAT">
    <output>BUFFER</output>
</edit>
```

The edit element displays an edit box, which takes data from the user and writes it to a buffer. The output is defined by a simple *output* tag within the value block and needs to be a data-container (see above).

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

signed
:   If set to *false* the user may not enter negative numbers.
:   *optional*, default: true

decimal
:   If set to *false* the user may not enter decimal (i.e. non-integer) numbers.
:   *optional*, default: true

min
:   The minimum value allowed. Disable by not setting this attribute. **Available from phyphox file format 1.1 (phyphox 1.0.2)**.
:   *optional*, default: disabled

max
:   The maximum value allowed. Disable by not setting this attribute. **Available from phyphox file format 1.1 (phyphox 1.0.2)**.
:   *optional*, default: disabled

unit
:   A unit to be displayed after the value
:   *optional*, default: no unit

factor
:   A factor to be applied to the value before displaying it. This is usually used for unit conversion. Example: The data is in meter, but should be displayed in cm. The factor would be 0.01
:   *optional*, default: 1.0

default
:   The default value of the edit box. The experiment will start with this value.
:   *optional*, default: 0.0

### View-Element: button

**Available since phyphox file format 1.3 (phyphox 1.0.4)**

```xml
<button label="LABEL" dynamicLabel="BUFFER">
    <input>BUFFER1</input>
    <output>BUFFER1</output>
    <input type="value">42</input>
    <output>BUFFER2</output>
    <input type="empty" />
    <output>BUFFER3</output>
    <trigger>ID</trigger>
    ...
    <map min="FLOAT" max="FLOAT">LABEL 1</map>
    <map min="FLOAT" max="FLOAT">LABEL 2</map>
    ...
</button>
```

The button element displays a simple button, which interacts with the buffers **outside** the analysis cycle. Whenever the user presses the button, the last value from each inputs (which may be value types or data-containers) is written to each output (the first input is written to the first output, the second to the second and so on). Note, that this does not happen at a certain point during analysis, but between analysis cycles, independent of when the user pushes the button.

Since version 1.4 (phyphox 1.0.6) you may define empty inputs (type="empty"), effectively allowing to clear a buffer when pressing the button.

Since version 1.8 (phyphox 1.1.3) in addition to defining in and out buffer (or usually as an alternative), you can set a trigger tag defining an id. This triggers matching processes with the same id like a [network connection](network-connections.md) (the only example at the time of this writing).

Since version 1.19 (phyphox 1.2.0) you can additionally define map tags that works similar to the map function of the value element. Each map tag defines a minimum and/or maximum value and an associated text. In contrast to the value element, the button uses an attribute *dynamicLabel* to define a data-container that is used with these map values. Phyphox sequentially goes through the map tags in the order they have been defined and the first one for which the value in the buffer given in *dynamicLabel* falls within min/max of the map tag, the text in the tag is used as a label for the button. If no map tag matches, then the normal label from the *label* tag is used.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

dynamicLabel
:   A buffer (data-container) that controls the label of the button. The last value in this buffer is compared to the map tags in the button element and the first matching map tag determines the button's label.
:   *optional*, default: not set / show only the regular label

### View-Element: toggle

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<toggle label="LABEL" default="FLOAT">
    <output>BUFFER</output>
</toggle>
```

The toggle element displays a simple toggle (or a checkbox in the remote control interface), which allows the user to turn something off or on. The output buffer receives a 0 for off and a 1 for on. If the buffer is changed externally, a 0 is always interpreted as off while any other value is displayed as on.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

default
:   The value with which the associated buffer should start.
:   *optional*, default: do not set a starting value

### View-Element: slider

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<slider label="LABEL" type="STRING" default="FLOAT" minValue="FLOAT" maxValue="FLOAT" stepSize="FLOAT" precision="INTEGER" showValue="BOOL">
    <output>BUFFER_NORMAL</output>
    <output value="lowerValue">BUFFER_RANGE_LOWER</output>
    <output value="upperValue">BUFFER_RANGE_UPPER</output>
</slider>
```

This is a view element used to input values from a limited range determined by a minimum and maximum value as well as a step size. The current value is also shown separately. With *type="range"* the slider can be used as a range slider with two handles, allowing the user to select a range by picking a lower and an upper value.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

type
:   Can either be "normal" or "range". Normal is a slider representing a single value, while "range" is a range slider with two handles that allow picking a lower and an upper value.
:   *optional*, default: normal

default
:   The value with which the associated buffer should start. (Does not work in range slider mode. Use the init property of the data containers instead.)
:   *optional*, default: do not set a starting value

minValue
:   Value for a handle at the lower end of the slider.
:   *optional*, default: 0

maxValue
:   Value for a handle at the upper end of the slider.
:   *optional*, default: 1

stepSize
:   Determines the minimum distance between to values that can be selected with the slider. This is always relative to minValue, so a stepSize of 0.2 and a minValue of 0.1 will force the user to pick 0.1, 0.3, 0.5, etc.
:   *optional*, default: 1

precision
:   The number of decimal places shown in the field with the current vlaue
:   *optional*, default: 2

showValue
:   Show a title and the current value above the slider. If turned off, the title is also hidden, making the slider very thin and compact.
:   *optional*, default: true

### View-Element: dropdown

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<dropdown label="LABEL" default="FLOAT">
    <output>BUFFER</output>
    <map value="FLOAT">OPTION 1</map>
    <map value="FLOAT">OPTION 2</map>
                         ...
    <map value="FLOAT">OPTION 3</map>
</dropdown>
```

The dropdown view element gives the user a list of options, each of which is associated with a value. The user simply taps the dropdown box, picks an option and the associated value is written to the output buffer.

label
:   A label for this element
:   *required*

visibility
:   Points to a data container that determines visibility of this element. If the data container has no elements or its last element is invalid (NaN), zero or less than zero, this view element will be hidden. If its last element is larger than zero, the view element will be visible.
:   *optional*, default: not set / always visible, **Available since phyphox file format 1.20 (phyphox 1.2.1)**

default
:   The value with which the associated buffer should start.
:   *optional*, default: do not set a starting value

### View-Element: camera-gui

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<camera-gui label="LABEL" exposure_adjustment_level="INTEGER" showControls="STRING" grayscale="BOOLEAN" markOverexposure="COLOR" markUnderexposure="COLOR"/>
```

This is a preview and control for a camera input, showing a preview of the camera and allowing for selecting an acquisition area and several camera settings. Note that this only makes sense if you also use a camera input in the configuration.

*exposure_adjustment_level* and *showControls* determine which controls are available to the user and when they are shown. In the default experiments of phyphox you typically see *exposure_adjustment_level="3"* and *showControls="full_view_only"*.

*grayscale* and the *markOverexposure* and *markUnderexposure* are modifiers that influence the look of the image to make it easier to use for some measurements.

exposure_adjustment_level
:   This determines which controls are available to the user in three different levels of how much control over the exposure is possible: Level 1 only allows for changing the camera and zoom, but no control over exposure settings. Level 2 is a simplified exposure control, allowing the same as level 1 and adding a toggle to turn auto exposure on or off as well as a simple exposure value control, adjusting for a slight over or underexposure from the auto exposure result. Level 3 finally offers all controls, replacing the exposure value control from level 2 with shutter speed (exposure time), ISO and aperture and also showing the white balance control.
:   *optional*, default: 1

showControls
:   This determines when controls are shown. This can assume the following values:

    never
    :   Controls are never shown and this is only used as a preview (with the option to select the measurement area).

    full_view_only
    :   Controls are only shown after the preview has been tapped and maximized.

    always
    :   Controls are available even when only a small preview is shown
:   *optional*, default: full_view_only

grayscale
:   Show a grayscale image instead of colors
:   *optional*, default: false

markOverexposure
:   Overexposed parts of the image are replaced by the given color
:   *optional*, default: not used

markUnderxposure
:   Underexposed parts of the image are replaced by the given color
:   *optional*, default: not used

### View-Element: depth-gui

**Available since phyphox file format 1.14 (phyphox 1.1.10)**

```xml
<depth-gui label="LABEL" />
```

This is a preview and control for a depth input, showing a preview of the camera and allowing for selecting an acquisition area, an aggregation method and switching cameras. At the moment, you can only set the label. Note that this only makes sense if you also use a depth input in the configuration.

### View-Element: image

**Available since phyphox file format 1.18 (phyphox 1.1.16)**

```xml
    <image src="RESOURCE" scale="1.0" lightFilter="none" darkFilter="none" />
```

Display an image with the file name RESOURCE. Typically, RESOURCE is a png or jpg image (these are natively supported on both iOS and Android, hoping for SVG support on iOS eventually) that is placed in the resource folder "res" in a zip file along with the experiment XML file. So, for example, instead of sharing experiment.phyphox you would share a zip file that contains experiment.phyphox together with a folder called "res" that contains an image "demo.jpg". The image element would then set RESOURCE to "demo.jpg" (not res/demo.jpg), i.e. **<image src="demo.jpg" />**.

src
:   The file name of the image that should be displayed. (Relative to the resource folder.)
:   *required*

scale
:   Scales the size of the image. By default (scale="1.0") the image is shown in full width. The factor is relative to this, so scale="0.5" sets it to half the width of the view.
:   *optional*, default: 1.0

lightFilter
:   A filter that should be applied to the image if the interface of phyphox is in light mode. Currently, there are two options: **none** leaves the image as is. **invert** inverts the colors of the image.
:   *optional*, default: none

darkFilter
:   A filter that should be applied to the image if the interface of phyphox is in dark mode. Currently, there are two options: **none** leaves the image as is. **invert** inverts the colors of the image.
:   *optional*, default: none

## Block: export

The export block may hold one or more *set* blocks, grouping and naming multiple data-containers as a logical unit to be written to a file when the user wants to export the data. The user may choose from these sets and for example select if he wants only the raw data, the analysis results or everything in his exported file.

```xml
<phyphox version="1.0">
    ...
    <export>
        <set name="Results">
            <data name="Frequency">frequency</data>
            <data name="Period">period</data>
        </set>
        <set name="Raw data">
            <data name="Time t (s)">accT</data>
            <data name="Acceleration x (m/s²)">accX</data>
            <data name="Acceleration y (m/s²)">accY</data>
            <data name="Acceleration z (m/s²)">accZ</data>
        </set>
    </export>
    ...
</phyphox>
```

### Block: set

The set block will define a group of data-containers to be exported. The attribute *name* will be shown to the user as he may pick which of the sets should be exported. Also these sets may be represented in the final file. For example a CSV export results in a ZIP file containing a separate CSV files for each set. In another example a Excel export will contain a separate sheet for each set.

**Tag: data**

```xml
<data name="NAME">BUFFER</data>
```

Within each set, you can define multiple data enties. Each of them maps a data-container to a name displayed to the user. Usually, this name is the column title corresponding to the data in the exported file.

name
:   A name describing the data
:   *required*

## Block: network

The network block can define network connections that allow requesting values from or sending data to a service on a network (local or internet). This function is documented on a [separate page](network-connections.md).

## Block: events

The events block was introduced with file format 1.12 (phyphox version 1.1.8) as a temporary solution to store event and time reference data. It will be supported in the future to allow for reading old experiment state files, but at the time of this writing, there will be no specific use for this feature once the experiment state is stored in a form that separates measured data (and events) from the phyphox-configuration file.

The events block contains a list of event-block with tags corresponding to any known event, which are currently *start* and *pause*. Each event needs to have an attribute *experimentTime* and an attribute *systemTime* giving the experiment time (seconds since first start, ignoring pauses) and the system time (milliseconds since 1970) of the event.

```xml
<phyphox version="1.0">
    ...
    <events>
        <start experimentTime="0.0" systemTime="1608126693705"/>
        <pause experimentTime="1.3307273210000001" systemTime="1608126695035"/>
        <start experimentTime="1.3307273210000001" systemTime="1608126696552"/>
        <pause experimentTime="2.310827263" systemTime="1608126697532"/>
        ...
    </events>
    ...
</phyphox>
```

