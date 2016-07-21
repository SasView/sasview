.. file_converter_help.rst

File Converter Tool
===================

Description
-----------

This tool converts file formats with the Q data and intensity data in separate
files, into a single CanSAS XML file.

The input files can be:

*   Single column ASCII data, with lines that end with a digit, comma or
    semi-colon.
*   `BSL/OTOKO formatted
    <http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/
    SAXS-Software/CCP13/BSL.html>`_ data files.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using the Tool
--------------

1) Select the files containing your Q-Axis and Intensity-Axis data
2) Chose whether the files are in ASCII or BSL format
3) Chose where you would like to save the converted XML file
4) Optionally, input some metadata such as sample size, detector name, etc
5) Click *Convert* to save the converted file to disk

**Note**: If a BSL/OTOKO file with multiple frames is selected for the
intensity-axis file, a dialog will appear asking which frames you would like
converted. You may enter a start frame, end frame & increment, and all frames
in that subset will be converted. For example: entering 0, 50 and 10 for the
first frame, last frame, and increment respectively will convert frames 0, 10,
20, 30, 40 & 50. To convert a single frame, enter the same value for first
frame & last frame, and 1 as the increment.
