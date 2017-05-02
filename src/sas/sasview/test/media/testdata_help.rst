.. testdata_help.rst

Test Data
=========

Test data sets are included as a convenience to our users. Look in the \test 
sub-folder in your SasView installation folder.

The test data sets are organized based on their data structure:

- *1D data*
- *convertible 1D data files*
- *2D data*
- *coordinate data*
- *image data*
- *SESANS data*
- *save states*
- *upcoming formats*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

1D Data
^^^^^^^
1D data sets EITHER have:

- at least two columns of data with I(Q) (assumed to be in absolute units) on the y-axis and Q on the x-axis. And additional columns of data may carry uncertainty data, resolution data, or other metadata.

OR:

- the I(Q) and Q data in separate files *with no other information*.

Data in the latter format need to be converted to a single file format with the :ref:`File_Converter_Tool` before they can be analysed in SasView. Test files are located in the /convertible_files folder.

1D Test Data
............
33837rear_1D_1.75_16.5
  - Data from a magnetically-oriented surfactant liquid crystal output by the Mantid framework. The data was collected on the SANS2D instrument at ISIS.

10wtAOT_Reline_120_reduced / Anton-Paar / saxsess_example
  - Data from Anton-Paar SAXSess instruments saved in Otto Glatter's PDH format.
  
AOT_Microemulsion
  - Aerosol-OT surfactant stabilised oil-in-water microemulsion data at three 
    contrasts: core (oil core), drop (oil core + surfactant layer), and shell 
    (surfactant layer).
  - Suitable for testing simultaneous fitting.

APS_DND-CAT
  - ASCII data from the DND-CAT beamline at the APS.

hSDS_D2O
  - h25-sodium dodecyl sulphate solutions at two concentrations: 0.5wt% (just 
    above the cmc), 2wt% (well above the cmc), and 2wt% but with 0.2mM NaCl 
    electrolyte.
  - Suitable for testing charged S(Q) models.

ISIS_83404 / ISIS_98929
  - Polyamide-6 fibres hydrated in D2O exhibiting a broad lamellar peak from the semi-crystalline nanostructure.
  - This is the *same data* as that in the BSL/OTOKO Z8300* / Z9800* files but in an amalgamated ASCII format!
  - Suitable for testing :ref:`Correlation_Function_Analysis` .

ISIS_Polymer_Blend_TK49
  - Monodisperse (Mw/Mn~1.02) 49wt% d8-polystyrene : 51wt% h8-polystyrene 
    polymer blend.
  - Suitable for testing Poly_GaussCoil and RPA10 models.

P123_D2O
  - Lyotropic liquid crystalline solutions of non-ionic ABA block copolymer 
    Pluronic P123 in water at three concentrations: 10wt%, 30wt%, and 40wt%.
  - Suitable for testing paracrystal models.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Convertible 1D Data
^^^^^^^^^^^^^^^^^^^

APS_X / APS_Y
  - ASCII data output by a reduction software package at the APS.
  - Suitable for testing the :ref:`File_Converter_Tool` .

FIT2D_I / FIT2D_Q
  - ASCII data output by the FIT2D software package at the ESRF.
  - Suitable for testing the :ref:`File_Converter_Tool` .

Z8300*.I1D / Z8300*.QAX / Z9800*.I1D / Z9800*.QAX
  - BSL/OTOKO data from polyamide-6 fibres hydrated in D2O exhibiting a broad lamellar peak from the semi-crystalline nanostructure.
  - This is the *same data* as that in ISIS_83404 / ISIS_98929 but in an older separated format!
  - Suitable for testing the :ref:`File_Converter_Tool` .
  - Suitable for testing :ref:`Correlation_Function_Analysis` .

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

2D Data
^^^^^^^
2D data sets are data sets that give the reduced intensity for each Qx-Qy bin. Depending on the file format, uncertainty data and metadata may also be available.

2D Test Data
............
33837rear_2D_1.75_16.5
  - Data from a magnetically-oriented surfactant liquid crystal output by the Mantid framework. The data was collected on the SANS2D instrument at ISIS.

P123_D2O
  - Lyotropic liquid crystalline solutions of non-ionic ABA block copolymer 
    Pluronic P123 in water at three concentrations: 10wt%, 30wt%, and 40wt%.
  - Suitable for testing paracrystal models.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Coordinate Data
^^^^^^^^^^^^^^^
Coordinate data sets, such as PDB or OMF files, and which describe a specific structure, are designed to be read and viewed in the :ref:`SANS_Calculator_Tool` .

Coordinate Test Data
....................
A_Raw_Example-1
  - OMF format data file from a simulation of magnetic spheres.

diamond
  - PDB format data file for diamond.

dna
  - PDB format data file for DNA.

sld_file
  - Example SLD format data file.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Image Data
^^^^^^^^^^
Image data sets are designed to be read by the :ref:`Image_Viewer_Tool` . They can be converted into synthetic 2D data.

Image Test Data
...............
ISIS_98940
  - Polyamide-6 fibres hydrated in D2O exhibiting a broad lamellar peak from the semi-crystalline nanostructure.
  - Data is presented in Windows Bitmap (BMP), GIF, JPEG (JPG), PNG, and TIFF (TIF) formats.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

SESANS Data
^^^^^^^^^^^
SESANS (Spin-Echo SANS) data sets primarily contain the neutron polarisation as a function of the spin-echo length. Also see :ref:`SESANS` .

SESANS Test Data
................
spheres2micron
  - SESANS data from 2 micron polystyrene spheres in 53% H2O / 47% D2O.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Save States
^^^^^^^^^^^
Saved states are projects and analyses saved by the SasView program. A single 
analysis file contains the data and parameters for a single fit (.fit), p(r) 
inversion (.prv), or invariant calculation (.inv). A project file (.svs) contains 
the results for every active analysis in a SasView session.

Saved State Test Data
.....................
fitstate.fitv
  - a saved fitting analysis.

test.inv
  - a saved invariant analysis.

test002.inv
  - a saved invariant analysis.

prstate.prv
  - a saved P(r) analysis.

newone.svs
  - a saved SasView project.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Upcoming Formats
^^^^^^^^^^^^^^^^
Data in this folder are in formats that are not yet implemented in SasView but which might be in future versions of the program.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Other Test Data
^^^^^^^^^^^^^^^
phi_weights.txt

radius_dist.txt

THETA_weights.txt

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 06Oct2016
