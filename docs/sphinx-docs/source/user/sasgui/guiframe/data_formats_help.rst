.. data_formats.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.
.. WG Bouwman, DUT, added during CodeCamp-V in Oct 2016 the SESANS data format

.. _Formats:

Data Formats
============

SasView reads several different 1D (I(Q) vs Q), 2D SANS(I(Qx,Qy) vs (Qx,Qy))
and SESANS (P(z) vs z)
data files. But please note that SasView does not at present load data where
the Q and I(Q) data are in separate files.

1D Formats SANS
---------------

SasView will read files with 2 to 4 columns of numbers in the following order: 

    Q, I(Q), (dI(Q), dQ(Q))
    
where dQ(Q) is the instrumental resolution in Q and assumed to have originated 
from pinhole geometry.

Numbers can be separated by spaces or commas.

SasView recognises the following file extensions:

*  .TXT
*  .ASC
*  .DAT
*  .XML (in canSAS format v1.0 and 1.1)

If using CSV output from, for example, a spreadsheet, ensure that it is not 
using commas as delimiters for thousands.

For a description of the CanSAS/SASXML format see:
http://www.cansas.org/formats/canSAS1d/1.1/doc/

For a description of the NIST 1D format see:
http://danse.chem.utk.edu/trac/wiki/NCNROutput1D_IQ

For a description of the ISIS 1D format see:
http://www.isis.stfc.ac.uk/instruments/loq/software/colette-ascii-file-format-descriptions9808.pdf

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

2D Formats SANS
---------------

SasView will only read files in the NIST 2D format with the extensions 
.ASC or .DAT

Most of the header lines can be removed except the last line, and only the 
first three columns (Qx, Qy, and I(Qx,Qy)) are actually required.

For a description of the NIST 2D format see:
http://danse.chem.utk.edu/trac/wiki/NCNROutput1D_2DQxQy 

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Format SESANS
---------------

The current file extension is .ses or .sesans (not case sensitive).

The file format is to have a list of name-value pairs as a header at the top of the file, detailing general experimental parameters necessary for fitting and analyzing data. This list should contain all information necessary for the file to be 'portable' between users.

Following that is a 6 column list of instrument experimental variables:

- Spin echo length (z, in Angstroms)
- Spin echo length error (:math:`\Delta` z, in Angstroms) (experimental resolution)
- neutron wavelength (:math:`\lambda`, in Angstroms) (essential for ToF instruments)
- neutron wavelength error (:math:`\Delta \lambda`, in Angstroms)
- Normalized polarization (:math:`P/P_0`, unitless)
- Normalized polarization error (:math:`\Delta(P/P_0)`, unitless) (measurement error)


.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Wim Bouwman, 05Oct2016