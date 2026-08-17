# Phyphox file format

!!! tip "There is a visual editor for this"

    Experiment configurations do not have to be written by hand. The
    [phyphox experiment editor](https://phyphox.org/editor) assembles them from
    blocks in the browser and generates a QR code to get the result onto a
    phone. The pages here describe the format it writes, which is what you need
    if you want control over details the editor does not expose — or if you
    simply prefer a text editor.

This page is highly technical and meant for advanced users who want to control every minute detail of their experiment. On this page you will learn how the phyphox file format works and how to create a phyphox experiment - all you need is a text editor. Some experience with the XML format is recommended.

## Structure

The phyphox format is based on XML. The entire experiment is encapsulated within a *phyphox* root tag. Within this block, there are multiple blocks which define data-containers, inputs, outputs, translations, analysis etc.

Elements from a *foreign XML namespace* — any namespace other than the one of the root element, which is usually none — are ignored along with their entire content. This allows tools like experiment editors to embed their own metadata in an experiment file without breaking it for the apps. Elements in the file's own namespace remain strictly checked: an unknown element name is an error and the file will not load.

## Block: phyphox

The entire experiment is defined within the phyphox block. Its most important attribute is the version of the file format - not the version of the app. If the file format changes in a future version, this version number will increase. If phyphox (the app) encounters a file version newer than what it can read, it will not load the file but ask the user to update the app.

{{spec:root/phyphox}}

### Tag: title

The title of the experiment. This is just a simple string. Try to keep it short and concise.

{{spec:root/phyphox/title}}

### Tag: state-title

This should not be used for an experiment which will be distributed. This tag contains the title given by the user when saving the state of an experiment. If this is set, the app will show this experiment in the saved-states section.

{{spec:root/phyphox/state-title}}

### Tag: category

The category of the experiment. This is just a simple string used by the app to group the experiments. Try to keep it short and concise.

Note that this can and *should* be translated if you use translations (see below) as the app uses the localized version of this string and cannot match your experiment to the default group if the category is given in a different language.

{{spec:root/phyphox/category}}

### Tag: icon

The icon of the experiment. We recommend a small PNG with few colors; there are various web-based tools to create a base64-encoded PNG from a PNG file.

{{spec:root/phyphox/icon}}

### Tag: color

The base color for the experiment. This is used as a background of the icon (if a text-based icon is used or if it has a transparent background) and for the label of the category. If a category contains experiments with different colors, the most common color is used.

Color can be defined as a 6-digit hex value or as one of the named [Colors](colors.md).

{{spec:root/phyphox/color}}

### Tag: description

A description of the experiment. The first line should be a very short summary of what the experiment does as this line will be shown in the experiment list. Any whitespace at the beginning and end of the description as well as in each line will be stripped.

{{spec:root/phyphox/description}}

### Tag: link

A link tag defines a link to some resource on the web. You may have multiple link tags in your phyphox file and each will be listed as a button under the experiment description. When the user pushes the button, they will be redirected to the URL (usually in a web browser, but it might be a specific app for a specific URL - for example, YouTube links usually open in the YouTube app on Android).

{{spec:root/phyphox/link}}

## Block: translations

The translations block may hold one or more *translation* (note: singular) blocks, describing the translations of strings shown to the user. Any string outside the translations block is considered to be in English and then translated to other languages from within the translations block, unless a different global language has been defined in the tag of the phyphox-block or English appears explicitly as a translation block. If English is used in a translation block and no language has been defined in the phyphox-block, the text outside the translation block should be treated as a placeholder.

Exactly one translation block is applied: the one whose locale best matches the user's locale. Where no block matches better than the file's base language, the base strings are used as they are. Blocks are never combined, so each translation block has to be complete in itself.

{{inconsistency:translation-block-selection}}

```xml
<phyphox version="...">
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

Each translation block holds all the translations for a single language.

{{spec:root/translations/translation|attributes}}

#### Tag: title

Localized version of the title tag in the phyphox-block (see above). If the user's locale matches the locale of the translation block, the title will be replaced by this entry.

{{spec:root/translation/title}}

#### Tag: category

Localized version of the category tag in the phyphox-block (see above). If the user's locale matches the locale of the translation block, the category will be replaced by this entry. Note that phyphox will group experiments by the localized version of the category.

{{spec:root/translation/category}}

#### Tag: description

Localized version of the description tag in the phyphox-block (see above). If the user's locale matches the locale of the translation block, the description will be replaced by this entry.

{{spec:root/translation/description}}

#### Tag: link

This is the localized version of the link tag. The label identifies which link is meant: a link element carrying the label of a base link changes that link, one with a new label adds a link only shown in this language. The button text is localized with the *translation* attribute — the label itself always stays as written, since it is the key the two declarations are matched on. For example, if you link to a Demo video in English with

```xml
<link label="Demo">http://site.org/my/english/video</link>
```

you can point the button at a German version, with a German button text, in the translation block with

```xml
<link label="Demo" translation="Demo (deutsch)">http://site.org/my/german/video</link>
```

The URL may be left out to keep the original URL and only change the button text:

```xml
<link label="Demo" translation="Demo (deutsch)" />
```

And a link element with nothing but a label removes that link from this language:

```xml
<link label="Demo" />
```

{{spec:root/translation/link}}

#### Tag: string

Use the string-tag to translate any string shown to the user besides the title, description or category. If the text of a label, view etc. matches the string given in *original*, phyphox will display the tag's text instead. Of course, this only applies if the user's locale matches the translation locale.

{{spec:root/translation/string}}

## Block: data-containers

In data-containers all buffers are defined. Any input (sensors, microphone) writes to these buffers, any analysis module performs its operations on these buffers, the output modules read from these buffers and the results are shown to the user from these buffers. The buffers connect every module of the experiment.

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

The container tag defines the name of a single data container.

{{spec:root/data-containers/container}}

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

The export block may hold one or more *set* blocks, grouping and naming multiple data-containers as a logical unit to be written to a file when the user wants to export the data. The user may choose from these sets and for example select whether they want only the raw data, the analysis results or everything in their exported file.

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

The set block will define a group of data-containers to be exported. The attribute *name* will be shown to the user when they pick which of the sets should be exported. These sets may also be represented in the final file. For example, a CSV export results in a ZIP file containing a separate CSV file for each set, and an Excel export will contain a separate sheet for each set.

#### Tag: data

Within each set, you can define multiple data entries. Each of them maps a data-container to a name displayed to the user.

{{spec:root/set/data}}

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

The events block was introduced with file format 1.12 (phyphox version 1.1.8) as a temporary solution to store event and time reference data. It will remain supported in the future to allow reading old experiment state files, but there will be no specific use for this feature once the experiment state is stored in a form that separates measured data (and events) from the phyphox configuration file.

The events block contains a list of event blocks with tags corresponding to any known event, which are currently *start* and *pause*. Each event needs to have an attribute *experimentTime* and an attribute *systemTime* giving the experiment time (seconds since first start, ignoring pauses) and the system time (milliseconds since 1970) of the event.

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
