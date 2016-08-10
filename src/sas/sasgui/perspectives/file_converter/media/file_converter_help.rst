.. file_converter_help.rst

File Converter Tool
===================

Description
-----------

This tool converts file formats with the Q data and intensity data in separate
files, into a single CanSAS XML file.

It can also convert 2D BSL files into IGOR/DAT 2D files, which are 3 column
ASCII files of the format :code:`Qx - Qy - I(Qx,Qy)`.

The input files can be:

*   Single column ASCII data, with lines that end with a digit (no delimiter),
    comma or semi-colon.
*   `One-Dimensional OTOKO formatted
    <http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/
    SAXS-Software/CCP13/XOTOKO.html>`_ data files.
*   `Two-Dimensional BSL formatted
    <http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/
    SAXS-Software/CCP13/BSL.html>`_ data files.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using the Tool
--------------

1) Select the files containing your Q-Axis and Intensity-Axis data
2) Chose whether the files are in ASCII, OTOKO or BSL format
3) Chose where you would like to save the converted file
4) Optionally, input some metadata such as sample size, detector name, etc
5) Click *Convert* to save the converted file to disk

Files With Multiple Frames
^^^^^^^^^^^^^^^^^^^^^^^^^^

If a BSL/OTOKO file with multiple frames is selected for the intensity-axis
file, a dialog will appear asking which frames you would like converted. You
may enter a start frame, end frame & increment, and all frames in that subset
will be converted. For example: entering 0, 50 and 10 for the first frame, last
frame, and increment respectively will convert frames 0, 10, 20, 30, 40 & 50.
To convert a single frame, enter the same value for first frame & last frame,
and 1 as the increment.

For OTOKO files, there is also the option to output the data as multiple frames
in a single CanSAS file, or multiple files with one frame each. The single file
option will produce one file with multiple `<SASdata>` elements. The multiple
file option will output a file for each frame; each file will have one
`<SASdata>` element, and the frame number will appended to the file name.

All converted BSL frames will have the frame number appended to the file name.
