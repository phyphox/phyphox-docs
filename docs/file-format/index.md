# Phyphox file format

!!! tip "There is a visual editor for this"

    Experiment configurations do not have to be written by hand. The
    [phyphox experiment editor](https://phyphox.org/editor) assembles them from
    blocks in the browser and generates a QR code to get the result onto a
    phone. The pages here describe the format it writes, which is what you need
    if you want control over details the editor does not expose — or if you
    simply prefer a text editor.

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

The input block defines all hardware inputs such as sensors or the microphone used in the experiment. It is documented on a [separate page](input.md).

- [audio](input.md#input-module-audio)
- [bluetooth](input.md#input-module-bluetooth)
- [camera](input.md#input-module-camera)
- [depth](input.md#input-module-depth)
- [location](input.md#input-module-location)
- [sensor](input.md#input-module-sensor)

## Block: output

The output block defines all hardware outputs such as the speaker used in the experiment. It is documented on a [separate page](output.md).

- [audio](output.md#output-module-audio)
- [bluetooth](output.md#output-module-bluetooth)
- [flashlight](output.md#output-module-flashlight)

## Block: analysis

The analysis block describes all the math required for the experiment. Its attributes and the rules common to all analysis modules are documented on a [separate page](analysis/index.md). The modules themselves are listed by category:

- [Formula node](analysis/formula-node.md)
- [Basic math](analysis/basic-math.md)
- [Trigonometric functions](analysis/trigonometric-functions.md)
- [Statistics](analysis/statistics.md)
- [Advanced math](analysis/advanced-math.md)
- [Buffer operations](analysis/buffer-operations.md)
- [Data generation](analysis/data-generation.md)
- [Logic](analysis/logic.md)
- [Other](analysis/other.md)

## Block: views

The views block describes the different layout groups (views) from which the user may choose to view the experiment data. It is documented on a [separate page](views.md).

- [info](views.md#view-element-info)
- [separator](views.md#view-element-separator)
- [value](views.md#view-element-value)
- [graph](views.md#view-element-graph)
- [edit](views.md#view-element-edit)
- [button](views.md#view-element-button)
- [toggle](views.md#view-element-toggle)
- [slider](views.md#view-element-slider)
- [dropdown](views.md#view-element-dropdown)
- [camera-gui](views.md#view-element-camera-gui)
- [depth-gui](views.md#view-element-depth-gui)
- [image](views.md#view-element-image)

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

The network block can define network connections that allow requesting values
from or sending data to a service on a network (local or internet). It is
documented on a [separate page](network-connections.md), covering:

- [General implementation and syntax](network-connections.md#general-implementation-and-syntax)
- [Network services (protocols)](network-connections.md#network-services-protocols)
- [Response conversions](network-connections.md#response-conversions)
- [Discovery methods for network services](network-connections.md#discovery-methods-for-network-services)
- [Examples](network-connections.md#examples)

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
