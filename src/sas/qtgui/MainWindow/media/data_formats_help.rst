.. data_formats.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.
.. WG Bouwman, DUT, added during CodeCamp-V in Oct 2016 the SESANS data format
.. WG Bouwman, DUT, updated during CodeCamp-VI in Apr 2017 the SESANS data format

.. _Formats:

Data Formats
============

SasView recognises 1D SAS (*I(Q) vs Q*), 2D SAS(*I(Qx,Qy) vs (Qx,Qy)*) and 1D
SESANS (*P(z) vs z*) data in several different file formats. It will also read
and analyse other data adhering to the same file formats (e.g. DLS or NR data)
but not necessarily recognise what that data represents (e.g. plot axes may be
mislabelled).

.. note:: From SasView 4.1 onwards, the :ref:`File_Converter_Tool` allows some
          legacy formats to be converted into either the canSAS SASXML format
          or the NeXus NXcanSAS format. These legacy formats include BSL/OTOKO,
          output from FIT2D and some other SAXS-oriented software, and the ISIS
          COLETTE (or 'RKH') 2D format.

1D SAS Formats
--------------

SasView recognizes 1D data either arranged in separated columns in ASCII
('text') files, or in binary arrays in HDF5 files, if the files have the
following extensions (which are not case-sensitive):

*  .ABS
*  .ASC
*  .COR (in canSAS XML v1.0 and v1.1 formats)
*  .CSV
*  .DAT
*  .PDH (Anton Paar SAXSess format)
*  .TXT
*  .XML (in canSAS XML v1.0 and v1.1 formats)

*  .H5, .NXS, .HDF, or .HDF5 (in NXcanSAS v1.0 and v1.1 formats)

The CanSAS & NXcanSAS formats are both output by the `Mantid data reduction framework <http://www.mantidproject.org/>`_.

The ASCII formats can be viewed in any text editor (Notepad, vi, etc) but the
HDF formats require a viewer, such as `HDFView <https://www.hdfgroup.org/downloads/hdfview/>`_.

The ASCII ('text') files are expected to have 2, 3, or 4 columns of values,
separated by spaces or commas, in the following order:

    *Q, I(Q), ( dI(Q), dQ(Q) )*
    
where dI(Q) is the uncertainty on the intensity value, **and *dQ(Q)* is the**
**instrumental resolution in *Q*, assumed to have arisen from pinhole**
**geometry**. If the data are slit-smeared, see below.

If using CSV output from, for example, a spreadsheet, ensure that it is not
using commas as delimiters for the thousands. Also note that with some computer
language settings commas in CSV files can be replaced by semi-colons!

As a general rule, SasView will provide better fits when it is provided with
more information (i.e. more columns) about each observation (i.e. data point).

**Examples of these formats can be found in the \\test\\1d_data folder**
**in the SasView installation folder.**

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

2D SAS Formats
--------------

SasView will read ASCII ('text') files in the NIST 2D format (with the
extensions .ASC or .DAT) or HDF files in the NeXus NXcanSAS (HDF5) format
(with the extension .H5, .NXS, .HDF, or .HDF5). The file extensions are not
case-sensitive.

The NXcanSAS format is output by the `Mantid data reduction framework <http://www.mantidproject.org/>`_.

Most of the header lines in the `NIST 2D format <http://danse.chem.utk.edu/trac/wiki/NCNROutput1D_2DQxQy>`_
can be removed *except the last line*, and only the first three columns
(*Qx, Qy,* and *I(Qx,Qy)*) are actually required.

**Examples of these formats can be found in the \\test\\2d_data folder**
**in the SasView installation folder.**

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

1D SESANS Format
----------------

SasView version 4.1 onwards will read ASCII files in a prototype SESANS
standard format with the extensions .SES or .SESANS (which are not case-
sensitive).

The file format starts with a list of name-value pairs at the top which
detail the general experimental parameters necessary for fitting and analyzing
the data. This list should contain all the information necessary for the file
to be 'portable' between users.

Following the header are up to 8 space-delimited columns of experimental
variables of which the first 4 columns are required:

- Spin-echo length (z, in Angstroms)
- Depolarization (:math:`log(P/P_0)/(lambda^2 * thickness)`, in Angstrom :sup:`-1` cm :sup:`-1`\ )
- Depolarization error (also in in Angstrom :sup:`-1` cm :sup:`-1`\ ) (the measurement error)
- Spin-echo length error (:math:`\Delta`\ z, in Angstroms) (the experimental resolution)
- Neutron wavelength (:math:`\lambda`, in Angstroms)
- Neutron wavelength error (:math:`\Delta \lambda`, in Angstroms)
- Normalized polarization (:math:`P/P_0`, unitless)
- Normalized polarization error (:math:`\Delta(P/P_0)`, unitless) (the measurement error)

**Examples of this format can be found in the \\test\\sesans_data folder**
**in the SasView installation folder.**

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Coordinate Formats
------------------

The :ref:`SANS_Calculator_Tool` in SasView recognises ASCII files containing
coordinate data with the following extensions (which are not case-sensitive):

*  .PDB (Protein Data Bank format)
*  .OMF (OOMMF micromagnetic simulation format)
*  .SLD (Spin-Lattice Dynamics simulation format)

**Examples of these formats can be found in the \\test\\coordinate_data folder**
**in the SasView installation folder.**

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Slit-Smeared Data
-----------------

SasView will only account for slit smearing if the data being processed are
recognized as slit-smeared. It does not allow for manually inputing a slit value.

Currently, only the canSAS \*.XML and NIST \*.ABS formats facilitate slit-
smeared data. The easiest way to include $\Delta q_v$ in a way recognizable
by SasView is to mimic the \*.ABS format. The data must follow the normal
rules for general ASCII files **but include 6 columns**, not 4 columns. The
SasView general ASCII loader assumes the first four columns are *Q*, *I(Q)*,
*dI(Q)*, and *dQ(Q)*. If the data does not contain any *dI(Q)* information,
these can be faked by making them ~1% (or less) of the *I(Q)* data. The fourth
column **must** then contain the the $\Delta q_v$ value, in |Ang^-1|, but as a
**negative number**. Each row of data should have the same value. The 5th
column **must** be a duplicate of column 1. **Column 6 can have any value but**
**cannot be empty**. Finally, the line immediately preceding the actual
columnar data **must** begin with: "The 6 columns".

For an example of a 6 column file, see the example data set
1umSlitSmearSphere.ABS in the \\test\\1d folder in the SasView installation
folder.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Further Information
-------------------

ASCII
https://en.wikipedia.org/wiki/ASCII

HDF
https://en.wikipedia.org/wiki/Hierarchical_Data_Format

NXS
https://en.wikipedia.org/wiki/Nexus_(data_format)
https://www.nexusformat.org/

For a description of the CanSAS SASXML 1D format see:
http://www.cansas.org/formats/canSAS1d/1.1/doc/

For a description of the NXcanSAS format see:
http://cansas-org.github.io/NXcanSAS/classes/contributed_definitions/NXcanSAS.html

For descriptions of the ISIS COLETTE (or 'RKH') 1D & 2D formats see:
https://www.isis.stfc.ac.uk/Pages/colette-ascii-file-format-descriptions.pdf

For a description of the NIST 1D format see:
http://danse.chem.utk.edu/trac/wiki/NCNROutput1D_IQ

For a description of the NIST 2D format see:
http://danse.chem.utk.edu/trac/wiki/NCNROutput1D_2DQxQy 

For a description of the BSL/OTOKO format see: 
http://www.diamond.ac.uk/Beamlines/Soft-Condensed-Matter/small-angle/SAXS-Software/CCP13/BSL.html

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 27Oct2021
