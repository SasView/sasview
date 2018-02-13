.. file_converter_help.rst

.. _File_Converter_Tool:

File Converter Tool
===================

Description
-----------

This tool converts file formats with the Q data and Intensity data stored in separate
files, into a single CanSAS (XML) or NXcanSAS (HDF5) file.

It can also convert 2D BSL/OTOKO files into a NXcanSAS file.

Supported input file formats (examples may be found in the /test/convertible_files folder):

*   Single-column ASCII data, with lines that end without any delimiter,
    or with a comma or semi-colon delimiter
*   2D `ISIS ASCII formatted
    <https://www.isis.stfc.ac.uk/Pages/colette-ascii-file-format-descriptions.pdf>`_ data
*   `1D BSL/OTOKO format
    <http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/
    SAXS-Software/CCP13/BSL.html>`_ data
*   `2D BSL/OTOKO format
    <http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/
    SAXS-Software/CCP13/BSL.html>`_ data

Supported output file formats:

*   `CanSAS <http://www.cansas.org/formats/canSAS1d/1.1/doc/>`_
*   `NXcanSAS <http://download.nexusformat.org/sphinx/classes/contributed_definitions/NXcanSAS.html>`_

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using the Tool
--------------

1) Select the files containing your Q-axis and Intensity-axis data
2) Choose whether the files are in ASCII 1D, ASCII 2D, 1D BSL/OTOKO or 2D BSL/OTOKO format
3) Choose where you would like to save the converted file
4) Optionally, input some metadata such as sample size, detector name, etc
5) Click *Convert* to save the converted file

Files With Multiple Frames
^^^^^^^^^^^^^^^^^^^^^^^^^^

If a BSL/OTOKO file with multiple frames is selected for the Intensity-axis
file, a dialog will appear asking which frames you would like converted. You
may enter a start frame, end frame & increment, and all frames in that subset
will be converted. For example, entering 0, 50 and 10 will convert frames 0,
10, 20, 30, 40 & 50.

To convert a single frame, enter the same value for first frame & last frame,
and 1 as the increment.

CanSAS XML files can become quite large when exporting multiple frames to a
single file, so there is an option in the *Select Frame* dialog to output each
frame to its own file. The single file option will produce one file with
multiple `<SASdata>` elements. The multiple file option will output a separate
file with one `<SASdata>` element for each frame. The frame number will also be
appended to the file name.

The multiple file option is not available when exporting to NXcanSAS because
the HDF5 format is more efficient at handling large amounts of data.


.. note::
    This help document was last changed by Steve King, 08Oct2016
