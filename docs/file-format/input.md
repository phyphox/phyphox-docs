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

The audio tag defines audio as a data source (i.e. a microphone). Phyphox will record continuously and write the recording to the buffer at the beginning of an analysis execution (see analysis block). The target buffer is defined with a simple output-tag.

{{spec:input/input/audio}}

## Input module: bluetooth

The bluetooth block defines an input from a Bluetooth Low Energy device. Please refer to the documentation on the [Bluetooth Low Energy](bluetooth-low-energy.md) interface in phyphox for details.

{{spec:input/input/bluetooth|xml}}

## Input module: camera

Get data from the phone's camera(s). At the time of phyphox file format 1.19 (phyphox 1.2.0) this data is photometric data, but this is expected to be expanded in the future.

### Photometric measurements

When *feature* is set to "photometric" (the default if you omit this attribute), you can collect various photometric properties from a stream of camera frames. For each frame you will get a single value like luminance or hue. The coordinates x1, y1 and x2, y2 mark a rectangle from the camera image (ranging from 0 to 1 from one edge of the image to the other) that is taken into account to calculate the value.

The remaining attributes control the exposure settings of the camera. *auto_exposure* can enable or disable automatic exposure adjustments to adapt the brightness. This auto exposure does not use the phone's internal auto exposure, but is an implementation within phyphox that can be set to use a specific *aeStrategy*. These strategies determine whether the auto exposure should prefer framerate over the ideal exposure or whether it should avoid overexposure more aggressively.

The camera input is typically used together with a *camera-gui* view element (see view elements), which shows a preview and allows the user to adjust x1, x2, y1 and y2 along with auto exposure, exposure settings or zoom. In this case, the values set here are just the initial values.

The framerate of your measurement will depend on your phone's camera. Different cameras on the same phone can have different framerates and the exposure setting can also reduce the framerate if the exposure time (shutter speed) is longer than the duration of a frame. This could be a reason to lock the shutter_speed, but in most scenarios the better solution is using an auto exposure strategy *aeStrategy* for this.

The photometric properties are calculated on the GPU, so keeping up a high framerate is not limited by processing power on most phones.

{{spec:input/input/camera}}

## Input module: depth

Get a depth measurement from the depth sensor, which is typically a dedicated optical sensor as part of the camera array. On iOS, this type of sensor is called "LiDAR", while on Android you usually have to look for "ToF". Both systems have very different APIs to access this data with various advantages and drawbacks:

On iOS we access the LiDAR sensor through ARKit, which is the framework for augmented reality applications. The depth data is almost perfectly aligned with the camera image, but it is not raw data from the sensor, but processed and remapped for AR applications. Therefore, the data might have been fused with depth data derived from the normal color camera (for example depth estimation from parallax effects). Newer iOS devices also feature a depth sensor on the front, which is designed for FaceID, but this is available through an entirely different API and may be supported by phyphox in the future. (Details on Apple's API can be found at <https://developer.apple.com/documentation/arkit/ardepthdata>)

On Android we decided against using ARCore, Google's augmented reality framework, as a more direct API is available and dependencies on Google Services could be avoided in favor of platforms that do not have Google support. Here we use the camera2 API to access the sensor data, which has the benefit that we do not expect any fusion with AR data. However, the disadvantage is that the depth data has not been remapped to align with the regular camera image and you will experience an offset, which in particular will depend on the viewing distance as camera and sensor are placed at a distance in the phone's case. The camera2 API allows for accessing front and back facing depth sensors, but be aware that some phones advertise a ToF sensor for camera autofocus without exposing its data through the camera2 API. (Details on the camera2 API can be found at: <https://developer.android.com/reference/android/hardware/camera2/package-summary>)

Typically the user selects an area within the camera/depth data (which can be preset using the attributes x1, x2, y1, y2) that is aggregated into one depth value per frame. For each frame a pair of an aggregated depth value "z" and the corresponding timestamp "t" will be returned.

In order to give the user a preview and control over the depth input, you will want to also add a depth-gui view element to the configuration (see the views section).

{{spec:input/input/depth}}

## Input module: location

The location block defines an input from the GPS sensor. The data will be written to the output buffers at the rate at which it is provided by the sensor. On Android, the location data is expected to come from satellite navigation exclusively (although some unusual implementations may occur), but on iOS we cannot deactivate other sources. Therefore, in most cases on iOS the first reading is based on the mobile and Wi-Fi networks.

{{spec:input/input/location}}

## Input module: sensor

The sensor block defines a sensor as an input. The data will be written to the output buffers at the rate at which it is provided by the sensor. Alternatively, you may define a different *rate*, in which case the latest reading is picked at the given rate. In addition you may turn on averaging in combination with the forced rate, in which case all data during the interval of the rate is averaged and only the average is written to the buffer. The exact strategy to achieve the target rate can be defined by the parameters *rateStrategy* and *stride*. Please see details about this in the explanation of these parameters and note that these have been introduced with a behavior change in file format 1.14 (phyphox 1.1.10).

The outputs are mapped to data-containers by simple output-tags. Each requires a *component* attribute to map the data to the data-container.

Note that the somewhat cumbersome names for "acceleration with g" and "acceleration (without g)" have been chosen to aid students in understanding the data given by these sensors. But internally we stick to the names commonly used on Android, "accelerometer" and "linear_acceleration". Usually, "accelerometer" (the one with g) is a physical sensor which measures the acceleration force applied to a sample mass (in the form of a MEMS device), so it will give a constant acceleration of 9.81 m/s² for a resting device (hence our descriptive name "with g"). In contrast, "linear_acceleration" is usually just a virtual sensor, which may use additional sensors to remove the earth's acceleration (hence our descriptive annotation "without g") to report the actual acceleration of the phone in the reference system of the user. So "linear_acceleration" will report zero acceleration when the phone is at rest or moving at a constant speed.

{{spec:input/input/sensor}}
