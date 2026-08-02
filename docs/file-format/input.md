# Input

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

## Input module: audio

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

## Input module: bluetooth

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

The bluetooth block defines an input from a Bluetooth Low Energy device. Please refer to the documentation on the [Bluetooth Low Energy](bluetooth-low-energy.md) interface in phyphox for details.

## Input module: camera

**Available since phyphox file format 1.19 (phyphox 1.2.0)**

```xml
<camera x1="FLOAT" x2="FLOAT" y1="FLOAT" y2="FLOAT" auto_exposure="BOOLEAN" aeStrategy="STRING" aeFPSTarget="FLOAT" locked="STRING" feature="STRING">
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

The remaining attributes control the exposure settings of the camera. *auto_exposure* can enable or disable automatic exposure adjustments to adapt the brightness. This auto exposure does not use the phone's internal auto exposure, but is an implementation within phyphox that can be set to use a specific *aeStrategy*. These strategies determine if the the auto exposure should prefer framerate over the ideal exposure or if it should avoid overexposure more aggressively.

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

auto_exposure
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

## Input module: depth

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

## Input module: location

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

## Input module: sensor

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
