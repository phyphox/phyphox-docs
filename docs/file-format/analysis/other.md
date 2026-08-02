# Other

## imagedecode

**Available since phyphox file format 1.20 (phyphox 1.2.1)**

This module takes the input data as a stream of bytes encoded by the values 0 to 255. The data is decoded using the operating system's image decoding class, which should support PNG, JPEG and BMP data as a minimum. As output the decoded image data becomes available as red (r), green (g), blue (b), alpha (a), luma and luminance channels (Rec. 709) with each value encoded in the range 0 to 1. The outputs receive one value per pixel line-wise starting from the top. Additionally, the outputs *width* and *height* receive width and height in pixels respectively.

This module can be used to transfer image files via Bluetooth or network interface and then decode them for further processing or display in a color map graph.

*in*
:   *input*
:   *as* not required
:   Number of inputs: Exactly one

<!-- -->

*width*
:   *output*
:   *as* required

*height*
:   *output*
:   *as* required

*r*
:   *output*
:   *as* required

*g*
:   *output*
:   *as* required

*b*
:   *output*
:   *as* required

*a*
:   *output*
:   *as* required

*luma*
:   *output*
:   *as* required

*luminance*
:   *output*
:   *as* required
