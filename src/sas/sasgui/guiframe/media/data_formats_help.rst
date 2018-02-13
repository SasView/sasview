.. data_formats.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.
.. WG Bouwman, DUT, added during CodeCamp-V in Oct 2016 the SESANS data format
.. WG Bouwman, DUT, updated during CodeCamp-VI in Apr 2017 the SESANS data format

.. _Formats:

Data Formats
============

SasView reads several different 1D SAS (*I(Q) vs Q*), 2D SAS(*I(Qx,Qy) vs (Qx,Qy)*) and 1D SESANS (*P(z) vs z*) data files. From SasView 4.1 onwards, a :ref:`File_Converter_Tool` allows some legacy formats to be converted into modern formats that SasView will read.

1D SAS Formats
--------------

SasView will read ASCII ('text') files with 2 to 4 columns of numbers in the following order: 

    *Q, I(Q), ( dI(Q), dQ(Q) )*
    
where *dQ(Q)* is the instrumental resolution in *Q* and assumed to have originated 
from pinhole geometry.

Numbers can be separated by spaces or commas.

SasView recognises the following file extensions which are not case-sensitive:

*  .TXT
*  .DAT
*  .XML (in canSAS format v1.0 and 1.1)
*  .H5  (as NeXus NXcanSAS only)
*  .NXS (as NeXus NXcanSAS only)

.. note::
    From SasView version 4.2 onwards files written in the NIST .ASC format are no longer read. This is because that 
    format normally represents *raw* and not reduced data.

If using CSV output from, for example, a spreadsheet, ensure that it is not using commas as delimiters for thousands.

The SasView :ref:`File_Converter_Tool` available in SasView 4.1 onwards can be used to convert data sets with separated *I(Q)* and *Q* files (for example, BSL/OTOKO, and some output from FIT2D and other SAXS-oriented software) into either the canSAS SASXML (XML) format or the NeXus NXcanSAS (HDF5) format.

For a description of the CanSAS/SASXML format see:
http://www.cansas.org/formats/canSAS1d/1.1/doc/

For a description of the ISIS 1D format see:
https://www.isis.stfc.ac.uk/Pages/colette-ascii-file-format-descriptions.pdf

For a description of the NXcanSAS format see:
http://cansas-org.github.io/NXcanSAS/classes/contributed_definitions/NXcanSAS.html

All the above formats are written by the `Mantid Framework <http://www.mantidproject.org/>`_.

For a description of the NIST 1D format see:
http://danse.chem.utk.edu/trac/wiki/NCNROutput1D_IQ

For a description of the BSL/OTOKO format see: 
http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/SAXS-Software/CCP13/BSL.html

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

2D SAS Formats
--------------

SasView will read ASCII ('text') files in the NIST 2D format (with the extension .DAT) or files in the NeXus NXcanSAS (HDF5) format (with the extension .H5 or .NXS). File extensions are not case-sensitive. Both of these formats are written by the `Mantid Framework <http://www.mantidproject.org/>`_.

Most of the header lines in the NIST 2D format can actually be removed except the last line, and only the first three columns (*Qx, Qy,* and *I(Qx,Qy)*) are actually required.

.. note::
    From SasView version 4.2 onwards files written in the NIST .ASC format are no longer read. This is because that 
    format normally represents *raw* and not reduced data.

.. note::
    SasView does not read the standard NeXus format, only the NXcanSAS subset. 

The SasView :ref:`File_Converter_Tool` available in SasView 4.1 onwards can be used to convert data sets in the 2D BSL/OTOKO format into the NeXus NXcanSAS (HDF5) format.

For a description of the NIST 2D format see:
http://danse.chem.utk.edu/trac/wiki/NCNROutput1D_2DQxQy 

For a description of the NXcanSAS format see: 
http://cansas-org.github.io/NXcanSAS/classes/contributed_definitions/NXcanSAS.html

For a description of the BSL/OTOKO format see: For a description of the BSL/OTOKO format see: 
http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/SAXS-Software/CCP13/BSL.html


.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

1D SESANS Format
----------------

SasView version 4.1 onwards will read ASCII ('text') files in a prototype SESANS standard format (with the extensions .SES or .SESANS). The file extensions are not case-sensitive.

The file format has a list of name-value pairs at the top of the file which detail the general experimental parameters necessary for fitting and analyzing data. This list should contain all the information necessary for the file to be 'portable' between users.

Following the header is a 8 (only the first 4 are really needed) column list of instrument experimental variables:

- Spin echo length (z, in Angstroms)
- depolarization (:math:`log(P/P_0)/(lambda^2 * thickness)`, in Angstrom :sup:`-1` cm :sup:`-1`\ )
- depolarization error in the same unit) (measurement error)
- Spin echo length error (:math:`\Delta`\ z, in Angstroms) (experimental resolution)
- Neutron wavelength (:math:`\lambda`, in Angstroms)
- Neutron wavelength error (:math:`\Delta \lambda`, in Angstroms)
- Normalized polarization (:math:`P/P_0`, unitless)
- Normalized polarization error (:math:`\Delta(P/P_0)`, unitless) (measurement error)

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Wim Bouwman, 05Apr2017