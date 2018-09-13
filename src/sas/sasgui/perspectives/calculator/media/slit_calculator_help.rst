.. slit_calculator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.


Slit Size Calculator Tool
=========================

Description
-----------

This tool enables X-ray users to calculate the slit size (FWHM/2) for resolution 
smearing purposes based on their half beam profile data (as Q vs Intensity; any 
other data fields are ignored).

Method
------

The tool works by sequentially summing 10 or more intensity values until a 
maximum value is attained. It then locates the Q values for the points just before, 
and just after, **half** of this maximum value and interpolates between them to get 
an accurate value for the Q value for the half maximum.

NOTE! Whilst it may have some more generic applicability, the calculator has
only been tested with beam profile data from Anton-Paar SAXSess\ :sup:`TM`\  software.
The beam profile file does not carry any information about the units of the 
Q data. It is probably |nm^-1| but the resolution calculations assume the slit 
height/width has units of |Ang^-1|. If the beam profile data is not in these 
units then it, or the result, must be manually converted.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using the tool
--------------

1) Select *Slit Size Calculator* from the *Tool* menu on the SasView toolbar.

2) Load a beam profile file in the *Data* field using the *Browse* button.

   *NOTE! To see an example of the beam profile file format, visit the file
   beam profile.DAT in your {installation_directory}/SasView/test_1d folder.*

3) Once a data is loaded, the slit size is automatically computed and displayed
   in the tool window.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 09Sep2018
