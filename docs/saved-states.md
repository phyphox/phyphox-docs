# Saved states

A *saved state* is an experiment together with the data it has recorded: the user saves it from the experiment menu, either into the app's own collection, where it appears under "Saved states", or as a file to share. Opening a saved state restores the experiment with its buffers filled and its time reference intact, so the measurement can be looked at, exported, or continued.

Up to phyphox 1.2 a saved state was a single `.phyphox` file with the recorded data written into the *init* attributes of the data containers, the title in a `state-title` element and the start and pause events in an `events` block. That form is described under [the legacy format](#the-legacy-format) below; the apps keep reading it indefinitely, but no longer write it.

Since phyphox 1.3.0 a saved state is a **zip container** that keeps the experiment configuration untouched and stores the data next to it, in the same arrangement the CSV export uses. This page defines that container.

## Layout

```
experiment.phyphox      the experiment file, byte for byte as it was loaded
res/<name>              the resources the experiment references, if any
data/index.csv          which container's data is in which file
data/<file>.bin         one file of binary64 values per data container
meta/device.csv         the device, as in the CSV export
meta/time.csv           the start and pause events, as in the CSV export
meta/state.csv          the title of the state and when it was saved
```

A container is recognised as a saved state by the presence of `meta/state.csv`. Everything else that a phyphox container may hold is handled as described under [Transferring experiments](transferring-experiments.md): apps that predate this format extract the `.phyphox` entry and `res/` and ignore the rest, so an old app opens a saved state as the plain experiment, without its data (see [Older apps](#older-apps)).

The file is shared with the `.zip` extension, like any experiment that comes with resources, so that users and their operating system can tell it from a bare XML file that a text editor can open. The apps accept it under `.phyphox` too, because they detect a container by its content, not by its name.

Everything in the container other than the `.bin` files is text: CSV in the fixed dialect given below, so a saved state can be read with a spreadsheet and the data with one line of numpy, without any phyphox tool.

### The CSV dialect

The CSV files of the export follow the user's separator and decimal-point settings. The files of a saved state are read back by the app, so they use one fixed dialect regardless of settings:

- UTF-8, lines ending in LF, the first line a header;
- fields separated by a comma;
- strings in double quotes, a double quote inside a string doubled;
- numbers unquoted, with a dot as decimal separator; a reader accepts plain and scientific notation (`1.5`, `1.5E0`, `1.5e+00`), `NaN`, `Infinity` and `-Infinity`, in any case.

A writer should not emit anything a plain CSV reader stumbles over: no separators other than the comma, no line breaks inside a string.

## The experiment file

`experiment.phyphox` is the configuration of the experiment **exactly as it was loaded**, byte for byte: from the bundled collection, from the user's collection, from a downloaded file, or the one `.phyphox` entry of a container the user chose. Nothing is added, stripped or rewritten. In particular:

- its `title`, `category`, `color` and `icon` are the experiment's own. The list shows a saved state under the "Saved states" category with the state's title and overrides the colour itself; that presentation is the app's, not the file's.
- if the source was itself a legacy saved state, its `state-title`, `events` and data-carrying *init* attributes are copied along. A reader of this container ignores `state-title` and `events` when `meta/state.csv` and `meta/time.csv` are present, and the data files replace whatever *init* put into the buffers. The file is larger than it needs to be, and that is accepted: the legacy format cannot tell recorded values from the start values an analysis needs, so there is no safe way to strip them.

A saved state therefore holds exactly one experiment. Saving the state of an experiment that was opened from a multi-experiment container stores only the experiment that was running.

## Resources

`res/` holds the files the experiment references, under the names the experiment uses, the same way a [zip of an experiment with images](transferring-experiments.md#bundling-images) carries them. Which files that is follows from the experiment, as it does when an experiment is saved to the collection: the `src` of every [image view element](file-format/views/basics.md#view-element-image), for instance. Only referenced files are included; a resource the source container carried for another experiment is not. An experiment that references nothing has no `res/` folder.

## The data

### data/index.csv

The index maps every data container of the experiment to its data file:

```csv
"container","file","count"
"acc_time","acc_time.bin",2048
"acc_x","acc_x.bin",2048
"calibration","calibration.bin",0
"max x (m/s²)","max_x__m_s__.bin",1
```

container
:   The buffer name, exactly as written in the `data-containers` block.

file
:   The name of the entry under `data/` that holds its values.

count
:   The number of values in that file. The file is `count` times eight bytes long; a mismatch means the container is damaged and the state is refused.

The rows are in the order of the `data-containers` block, one per container. A writer derives the file name from the buffer name by keeping ASCII letters, digits, `_` and `-`, replacing every other character by `_`, truncating to 64 characters and appending `.bin`; if two containers map to the same name, the later ones get `-2`, `-3`, … inserted before the extension. That rule is for writers; **a reader goes through the index and never derives a file name**, so a container written by another tool with any entry names it likes is read all the same. Buffer names are free text and would collide or be invalid as entry names on some file systems, which is why the index exists.

A container of the experiment that has no row in the index is loaded as if the experiment were opened fresh, with its *init* values. A row naming a container the experiment does not have is ignored.

### data/\<file\>.bin

Each data file is the plain sequence of the container's values, oldest first, as IEEE 754 binary64 (double precision) in little-endian byte order, with no header and nothing else: a buffer holding 2048 values is a file of 16384 bytes, an empty buffer is an empty file. NaN and the infinities are stored as they are; this is one of the reasons for the binary form, the other being size and speed.

```python
import numpy as np
acc_x = np.fromfile("data/acc_x.bin", dtype="<f8")
```

## Loading semantics

Restoring a state from the container means:

1. The experiment is loaded from `experiment.phyphox` as if it were opened on its own, resources resolved from `res/`.
2. For every row of the index, the named buffer's contents are **replaced** by the values of its file, whatever *init* put there. If the file holds more values than the buffer's *size* allows (which can only happen if the experiment file was changed since the state was written), the newest values are kept.
3. A [static buffer](file-format/index.md#tag-container) that received at least one value is marked as filled, so the analysis does not fill it again.
4. The time reference is restored from `meta/time.csv`, so that the experiment time continues where it stopped and system-time axes are correct. An `events` block in the experiment file is ignored.
5. The title shown for the state is taken from `meta/state.csv`; a `state-title` in the experiment file is ignored.

The experiment is not started by loading a state. Starting it afterwards continues the measurement: new data appends to the restored buffers, and the new start is added to the time reference.

## Metadata

### meta/device.csv

The device the state was recorded on, in the two-column form of the CSV export (`"property","value"`; the properties are those the export writes on the respective platform). It is informational, nothing is read back from it, and a reader does not require it.

### meta/time.csv

The time reference, in the form the CSV export writes:

```csv
"event","experiment time","system time","system time text"
"START",0.000000000E0,1759650000.000,"2025-10-05 10:20:00.000 UTC+02:00"
"PAUSE",1.330727321E0,1759650001.331,"2025-10-05 10:20:01.331 UTC+02:00"
"START",1.330727321E0,1759650005.512,"2025-10-05 10:20:05.512 UTC+02:00"
"PAUSE",2.310827263E0,1759650006.492,"2025-10-05 10:20:06.492 UTC+02:00"
```

event
:   `START` or `PAUSE`, upper case. A reader ignores a row with any other event name, so that a later event type does not make older apps refuse the file.

experiment time
:   Seconds since the measurement first started, not counting pauses - the same quantity as the *experimentTime* attribute of the legacy `events` block.

system time
:   Seconds since the Unix epoch, with millisecond resolution (the legacy block stored milliseconds as an integer; here it is the export's column). A reader parses the number and rounds to milliseconds.

system time text
:   The same instant as text, `yyyy-MM-dd HH:mm:ss.SSS 'UTC'XXX` with the device's time zone offset. Informational; a reader does not parse it.

Rows are in chronological order, alternating START and PAUSE, as the apps' time reference produces them. A state saved while the experiment runs has an unpaired trailing START; the writer pauses the experiment before writing, as both apps do today, so this does not normally occur, but a reader accepts it. A state with no event at all, saved before the experiment was ever started, has only the header line. The file is required; a container without it is not a saved state and is refused as such (it would still open as a plain experiment in an app that does not know the format).

### meta/state.csv

What makes the container a saved state:

```csv
"property","value"
"format","1"
"title","Pendulum, long string"
"saved","1759650100.000"
"saved text","2025-10-05 10:21:40.000 UTC+02:00"
"app","phyphox 1.3.0 (Android)"
```

format
:   Version of this container format, `1`. It is raised only for a change that an older reader cannot handle; a reader refuses a format it does not know. Required.

title
:   The title the user gave the state, shown in the experiment list in place of the experiment's title (which becomes the subtitle). Required; renaming a state in the collection rewrites this value and nothing else.

saved
:   When the state was written, in seconds since the Unix epoch with millisecond resolution, like the *system time* column above. Required; the list may sort by it.

saved text
:   The same instant as text, in the format of *system time text*. Informational.

app
:   The app and version that wrote the state, free text. Informational, useful in support requests.

Unknown properties are ignored, so a writer may add more. The values are strings as far as the CSV is concerned (the numbers are quoted here because the whole column is), and a reader parses *format* and *saved* itself.

## Older apps

An app that predates this format opens the container through its usual path: it finds one `.phyphox` entry and a `res/` folder, extracts those and ignores `data/` and `meta/` as unknown entries. The user gets the experiment without its data, not an error. This cannot be helped without touching the experiment file, which this format deliberately does not do; a note to that effect when sharing is advisable.

## The legacy format

Saved states written by phyphox up to version 1.2 are single `.phyphox` files in which

- the recorded data of every container is written into its *init* attribute, as a comma-separated list, which is why those files can run to many megabytes;
- a [`state-title`](file-format/index.md#tag-state-title) element holds the title the user gave;
- a `color` element is forced to `blue`, which is how the old serializer marked a state in the list;
- an [`events`](file-format/index.md#block-events) block holds the start and pause events with *experimentTime* and *systemTime* attributes.

Both elements are **deprecated** with this format and are no longer written, but the apps will keep accepting such files so that every state ever saved stays loadable. There is no conversion of a legacy state into the container form: a legacy file cannot tell the values an analysis needs as its start from the values that were recorded, so its *init* attributes have to stay as they are, and re-saving a legacy state produces a container whose experiment file still carries them.

A legacy state in the collection is shown and renamed as before: the rename rewrites its `state-title`.
