# Transferring phyphox experiments

------------------------------------------------------------------------

**Warning: The information on this page refers to version 1.1.0 (file format 1.7) onwards. Earlier versions only allowed transferring phyphox-files directly (no QR-codes and no zips) and through a phyphox:// URL.**

------------------------------------------------------------------------

After you have created your custom experiment (either with our editor or "manually" as a text file), you need to transfer it to your phone. The editor can directly generate QR codes, which is usually the recommended and most reliable method. However, if you did not use the editor or if you need other options, here you can learn about all the ways phyphox can receive your custom experiment.

## File format

The most basic experiment definition is a .phyphox file as described by our [phyphox file format](file-format/index.md). This is just a simple text file, which is simple to handle, but can only hold a single experiment. It has some disadvantages when transferring it directly (see below) or using it as an offline QR code (see below).

Alternatively, you can place .phyphox-files in a zip file. Phyphox will list all phyphox-files found within a zip file and ask the user how to proceed. If only a single phyphox-file is found in the zip file, it is handled as if the phyphox-file was transferred directly. Zip files should be preferred for direct transfer or offline QR codes.

## Transfer method

### Direct transfer

You can copy a phyphox-file or a zip containing one or more files directly onto your phone using any method convenient to you (for example email, Dropbox, messenger services, USB cable, Bluetooth file transfer...). On your phone, you then need to open the file from the appropriate app (for USB or Bluetooth transfer, this could be a file manager app like Total Commander), which should then offer to open the file in phyphox.

However, there are some problems with this method, especially on Android: File formats are no longer assigned to apps (in this case phyphox) by their file name extension ("abc.phyphox"), but by their "MIME type" instead. A MIME type describes the content type and format, like for example "image/png". If you open a PNG-image from a file manager or your email client, it will tell the system that it wants to open a file of the type "image/png" and the system will list all the apps that can handle images. For a phyphox-file, we have the problem that the email client has no idea what a phyphox-file is and it will report it to the system as one of many types that correspond to an unknown file type. Better apps may (correctly) report an XML file, but some worse apps will not report anything. Whether you can open your phyphox-file with phyphox will depend on what this app reports and at least in the case of reporting "nothing", we cannot change anything about this.

This problem usually does not occur with zip files as this is a rather well-known file format. However, some apps might insist on opening the zip file themselves instead of handing it over to the next app (i.e. phyphox).

Therefore, the direct transfer should only be used to transfer files for yourself when you know that this works on the target device. It is not suitable for an audience with different devices.

### phyphox:// URL

If you want to share a phyphox file or a zip containing one or more phyphox files for an audience with access to a web page, you can place the file on a webserver and link to it. If your file can be accessed as "<http://myhost.com/myfancyexperiment.phyphox>", you can create a link that is recognized by the system by replacing "<http://>" or "<https://>" by "phyphox://". If the user opens a phyphox-link and already has phyphox installed, the system should hand the URL to phyphox, which downloads the experiment (or the collection of experiments if it is a zip file) directly from the web.

For this you need to be able to upload your experiment to a webserver and you need to be able to create a phyphox-link somewhere convenient for your audience. This usually means that you are placing the link on your own website as a `<a href="phyphox://...">`-tag, because many CMS, forums or blog systems might enforce using a <http://> or <https://> link.

### Opening a bundled experiment: phyphox://asset=…

**Not yet in a released app version (added to the development branches 2026-08).**

A phyphox-link can also open one of the experiments that ship with the app, without any server involved. The identifier is the experiment file's path within the bundled collection, URL-encoded:

```
phyphox://asset=accelerometer.phyphox
phyphox://asset=bluetooth%2Fphyphox_m_bmp581.phyphox
```

This is meant for links in worksheets, documentation and classroom materials that should land the user directly in the right bundled experiment, and it is what automated testing uses to drive the app. It is deliberately limited to the bundled collection: experiment titles are not unique, and files elsewhere on the device keep going through the regular file-opening routes. An unknown path shows the app's normal "could not load" message.

### Online QR-Codes (recommended)

If your audience has internet access, this is the recommended method and the QR code can be created directly from our editor. This method is very similar to the phyphox:// URL, but the URL is encoded into a QR code, which can simply be scanned from the phyphox main menu. If you want to or need to create the QR code yourself, simply create a QR-Code that contains a link starting with phyphox://, <http://> or <https://> and phyphox should simply download the experiment after scanning the QR code.

### Offline QR-Codes

If your audience does not have internet access, the entire experiment configuration can be encoded in one or more QR codes. This can be done directly by our editor, but you should be aware that this produces very large QR codes which can be tough to scan. Also, there are size limitations if you want to avoid creating too many codes, so you should not embed a PNG icon and should remove any translations not necessary for your audience. Also, offline QR-codes should always use a zipped phyphox-file for the same reason.

If you need to create an offline QR code without our editor, you should create a QR code which starts with 13 specific bytes, starting with seven bytes encoding the letters "phyphox". Following this, you need to put four bytes which are a CRC32 hash (big endian) of the entire experiment file (only the zip, not the first 13 bytes of the header). The remaining two bytes of the 13 byte header describe how many QR codes form the entire experiment and which QR code index is the current one.

So, for example, if you spread your experiment across three QR codes, your codes need to start with

```
 p  h  y  p  h  o  x --[crc32]--  0  3
70 68 79 70 68 6f 78 ?? ?? ?? ?? 00 03
```

```
 p  h  y  p  h  o  x --[crc32]--  1  3
70 68 79 70 68 6f 78 ?? ?? ?? ?? 01 03
```

and

```
 p  h  y  p  h  o  x --[crc32]--  2  3
70 68 79 70 68 6f 78 ?? ?? ?? ?? 02 03
```

followed by the raw data. As the CRC32 is calculated across the entire experiment, it is identical in all three codes and is used by the app to check if the codes belong to the same experiment.

In practice, you should try to fit your experiment into a single QR code, so you should strip unnecessary tags and attributes from your phyphox XML file. Also, you can save a few more bytes if you do not include the entire zip file. If your zip file only contains a single experiment, you can leave out the local file header and the entire local directory. Just include our 13 byte header, followed by the compressed data and add a single data descriptor at the end. Phyphox will add a default local file header and a default local directory to extract and interpret the experiment file inside.

### Bluetooth device

If you have created your own Bluetooth Low Energy device, it can directly transmit an experiment to phyphox. Please check our [Bluetooth Low Energy](file-format/bluetooth-low-energy.md) documentation for details on this method.
