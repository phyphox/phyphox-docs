# Output

The output block defines all hardware outputs such as the speaker used in the experiment.

```xml
<phyphox version="...">
    ...
    <output>
        <audio rate="48000" loop="true">
            <input>waveform</input>
        </audio>
    </output>
    ...
</phyphox>
```

## Output module: audio

The audio tag defines audio as an output (i.e. a speaker). The audio waveform can be composed from one or multiple sources:

**input** An input tag on the immediate level below *audio* denotes a direct source. At the end of an analysis period phyphox will write the input buffer to an internal audio buffer and start the playback, so the sound is played after each analysis execution. It has a fixed amplitude of 1 and the duration is defined by the number of samples in the input buffer. Audio data is represented by values ranging from -1 to +1. The mono signal is played identically on both stereo channels; a direct source takes no parameter inputs. Only one direct source is supported.

**tone** A **tone** block represents a parametric tone generator. Its parameters **amplitude**, **duration** and **frequency** can either be fixed values (type="value") or a buffer (type="buffer", default) to control it dynamically. Each tone block (multiple are allowed) generates a tone of a chosen waveform (like sine or square) and keeps track of the momentary phase of the sine function to avoid click noises due to mismatch of the frequency and the sampling rate or when changing the frequency.

**noise** A **noise** block represents a generator for white noise. Its parameters **amplitude** and **duration** can either be fixed values (type="value") or a buffer (type="buffer", default) to control it dynamically. Only one *noise* block is supported.

Playback is triggered after each analysis process and each source can have individual durations (in seconds) and amplitudes (float value with 0.0 being silent and 1.0 maximum amplitude without clipping). If loop is set to true, the playback will loop. The default playback rate is 48kHz, but it can be changed using the *rate* attribute (in Hz). However, this is not recommended if the experiment targets a wide audience since supported playback rates are very device specific.

Since **file format 1.20 (phyphox version 1.2.1)** the tone and noise generators support panning from left to right, mapped to values from -1 (left) to +1 (right) with 0 being center. Note that this does not compensate for amplitude or loudness, but instead a center tone will be played at full amplitude on both channels and a pan to the right will not change the amplitude on the right channel but reduce the one on the left (and vice versa). The direct source cannot be panned — it always plays centered on both channels.

{{spec:output/output/audio}}

Example for a waveform composed from two tone generators and a noise generator, each driven by its own data containers:

```xml
<audio rate="48000" loop="true" normalize="true">
    <tone>
        <input parameter="frequency">f1</input>
        <input parameter="amplitude" type="value">0.5</input>
        <input parameter="duration" type="value">1.0</input>
    </tone>
    <tone>
        <input parameter="frequency">f2</input>
        <input parameter="amplitude">a2</input>
        <input parameter="duration" type="value">1.0</input>
    </tone>
    <noise>
        <input parameter="amplitude" type="value">0.1</input>
        <input parameter="duration" type="value">1.0</input>
    </noise>
</audio>
```

### The direct source

{{inconsistency:audio-direct-input-type}}

{{spec:output/audio/input}}

### tone

{{spec:output/audio/tone}}

{{spec:output/tone/input}}

### noise

{{spec:output/audio/noise}}

{{spec:output/noise/input}}

## Output module: bluetooth

The bluetooth block defines an output to a Bluetooth Low Energy device. Please refer to the documentation on the [Bluetooth Low Energy](bluetooth-low-energy.md) interface in phyphox for details.

{{spec:output/output/bluetooth|xml}}

## Output module: flashlight

The flashlight tag defines the phone's flashlight (usually part of the camera group) as an output. If frequency and dutycycle are not set, you can simply control the brightness of the flashlight (including turning it off) via the **intensity** input. If **frequency** is set to a value above 0, the flashlight acts as a stroboscope with the given frequency. You can also change the duty cycle through the **dutycycle** input.

Note that most phones cannot switch the flash state faster than 25ms. High frequencies or duty cycles far from 0.5 will require faster changes and may not be reproduced correctly by the phone. Phyphox cannot measure how fast the flashlight reacts and the reaction time may even vary from switch event to switch event. So be careful to verify that it is working correctly if fast switches are required.

{{spec:output/output/flashlight}}

{{spec:output/flashlight/input}}
