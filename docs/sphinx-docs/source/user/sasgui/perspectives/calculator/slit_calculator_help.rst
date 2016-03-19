.. slit_calculator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.


Slit Size Calculator Tool
=========================

Description
-----------

This tool enables X-ray users to calculate the slit size (FWHM/2) for smearing 
based on their half beam profile data.

*NOTE! Whilst it may have some more generic applicability, the calculator has
only been tested with beam profile data from Anton-Paar SAXSess*\ |TM|\  
*software.*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using the tool
--------------

1) Select *Slit Size Calculator* from the *Tool* menu on the SasView toolbar.

2) Load a beam profile file in the *Data* field using the *Browse* button.

   *NOTE! To see an example of the beam profile file format, visit the file 
   beam profile.DAT in your {installation_directory}/SasView/test folder.*

3) Once a data is loaded, the slit size is automatically computed and displayed 
   in the tool window.

*NOTE! The beam profile file does not carry any information about the units of 
the Q data. This calculator assumes the data has units of 1/\ |Ang|\ . If the
data is not in these units it must be manually converted beforehand.*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 01May2015
