# Output

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

## Output module: audio

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

## Output module: bluetooth

**Available since phyphox file format 1.7 (phyphox 1.1.0)**

The bluetooth block defines an output to a Bluetooth Low Energy device. Please refer to the documentation on the [Bluetooth Low Energy](bluetooth-low-energy.md) interface in phyphox for details.

## Output module: flashlight

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
