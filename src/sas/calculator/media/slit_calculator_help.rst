..slit_calculator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

Slit Size Calculator Tool
=========================

Description
-----------
This tool is for X-ray users to calculate the slit size (FWHM/2) for smearing 
based on their half beam profile data (SAXSess).

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

How To
-------
To calculate the slit size (FWHM/2), just load the beam profile data using the 
browse button.

Once a data is loaded, the slit size will be computed and show up in the text 
box.

Because the unit is not specified in the data file, we do not convert it into 
1/Angstrom so  users are responsible for converting the units of their data.

Note: This slit size calculator only works for beam profile data produced by 
'SAXSess'.

To see the file format, check the file, 'beam profile.DAT', in the 'test' 
folder of SasView.
