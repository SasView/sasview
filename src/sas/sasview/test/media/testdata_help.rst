.. testdata_help.rst

Test Data
=========

Test data sets are included as a convenience to our users. Look in the \test 
sub-folder in your SasView installation folder.

The test data sets are organized based on their data structure:

- *1D data*
- *convertible 1D data*
- *2D data*
- *coordinate data*
- *image data*
- *SESANS data*
- *DLS data*
- *NR data*
- *save states*
- *upcoming formats*
- *other test data*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

1D Data
^^^^^^^
1D data sets EITHER have:

- at least two columns of data with *Q* on the x-axis and *I(Q)* (assumed to be
  in absolute units) on the y-axis; optionally, additional columns of data may
  carry uncertainty data, resolution data, etc, or other metadata.

OR:

- the *Q* data and the *I(Q)* data in separate files *with no other information*;
  data in the this format need to be converted to a single file multi-column format
  with the :ref:`File_Converter_Tool` before they can be analysed in SasView; see
  `Convertible 1D Data`_ below.

1D Test Data
............
**Example data files are located in the \\1d_data sub-folder.**

1umSlitSmearSphere
  - Simulated NIST USANS data from a 1% dispersion of 1 micron spheres in D2O.

10wtAOT_Reline_120_reduced / Anton-Paar / saxsess_example
  - SAXS data from Anton-Paar SAXSess instruments saved in Otto Glatter's PDH format.
  
33837rear_1D_1.75_16.5
  - TOF-SANS data from a magnetically-oriented surfactant liquid crystal collected on
    the SANS2D instrument at ISIS.
  - The files were output by the Mantid framework v3.6.

AOT_Microemulsion
  - TOF-SANS data from Aerosol-OT surfactant-stabilised oil-in-water microemulsions
    collected on the LOQ instrument at ISIS.
  - Data are provided at three contrasts: core (oil core), drop (oil core + surfactant
    layer), and shell (surfactant layer).
  - The files were output by the Mantid framework v3.1.
  - Suitable for testing :ref:`Simultaneous_Fit_Mode` .

apoferritin
  - TOF-SANS data from a solution of the protein apoferritin collected on the SANS2D
    instrument at ISIS.
  - Suitable for testing :ref:`P(r)_Inversion` .

APS_DND-CAT
  - SAXS data from the DND-CAT instrument at the APS.

AUSANS_run3_2_no_buffer / AUSANS_run4_1_with_buffer
  - SANS data from the old AUSANS instrument at HIFAR (now decommissioned).

conalbumin
  - TOF-SANS data from a solution of the protein conalbumin collected on the SANS2D
    instrument at ISIS.
  - Suitable for testing :ref:`P(r)_Inversion` .

FK403_0006_Nika / Lew_Sa3_DSM_QinA
  - USAXS data from the 9ID instrument at the APS.

hSDS_D2O
  - TOF-SANS data from h25-sodium dodecyl sulphate solutions in D2O at 0.5wt%
    (just above the cmc), 2wt% (well above the cmc), and 2wt% but with 0.2mM
    NaCl electrolyte collected on the LOQ instrument at ISIS.
  - The files were output by the Mantid framework v3.1.
  - Suitable for testing charged S(Q) models.

ISIS_83404 / ISIS_98929
  - TOF-SANS data from polyamide-6 fibres hydrated in D2O collected on the LOQ
    instrument at ISIS. The data exhibit a broad lamellar peak from the semi-
    crystalline nanostructure.
  - This is the *same data* as that in the BSL/OTOKO Z8300* / Z9800* convertible
    files (see `Convertible 1D Data`_) but in an amalgamated format!
  - Suitable for testing :ref:`Correlation_Function_Analysis` .

ISIS_Polymer_Blend_RT2
  - TOF-SANS data from a monodisperse (Mw/Mn~1.03) polymer blend of 52wt%
    d8-polystyrene : 48wt% h8-polystyrene collected on the LOQ instrument at ISIS.
  - Mw~54180 g/mol, Rg~58 Ang.
  - The file was output by the Mantid framework v3.12.
  - Suitable for testing the mono_gauss_coil, poly_gauss_coil and rpa models.

ISIS_Polymer_Blend_TK49
  - TOF-SANS data from a monodisperse (Mw/Mn~1.02) polymer blend of 49wt%
    d8-polystyrene : 51wt% h8-polystyrene collected on the LOQ instrument at ISIS.
  - Mw~77500g/mol, Rg~74 Ang.
  - The file was output by the Mantid framework v2.6.
  - Suitable for testing the mono_gauss_coil, poly_gauss_coil and rpa models.

latex_smeared
  - SANS and USANS data from 500nm polymer latex particles dispersed in D2O.

Ludox_silica
  - TOF-SANS data from a dispersion of Ludox silica in mother liquor collected
    on the LOQ instrument at ISIS.
  - The file was output by the Mantid framework v3.11.

P123_D2O
  - TOF-SANS data from lyotropic liquid crystalline solutions of the non-ionic
    ABA block copolymer Pluronic P123 in D2O at 10wt%, 30wt%, and 40wt% collected
    on the LOQ instrument at ISIS.
  - This is the 1D radially-averaged form of the 2D data below (see `2D Data`_)!
  - The files were output by the Mantid framework v3.3.
  - Suitable for testing paracrystal models.

VTMA
  - Multi-frame USAXS data from a thermo-mechanical analysis scan performed at
    the APS.
  - Suitable for testing :ref:`Batch_Fit_Mode` .

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Convertible 1D Data
^^^^^^^^^^^^^^^^^^^
**Example data files are located in the \\convertible_files sub-folder.**

APS_X / APS_Y
  - ASCII format 1D SAXS data output by a reduction software package at the APS.
  - Suitable for testing the :ref:`File_Converter_Tool` .

FIT2D_I / FIT2D_Q
  - ASCII format 1D SAXS data output by the FIT2D software package at the ESRF.
  - Suitable for testing the :ref:`File_Converter_Tool` .

Z8300*.I1D / Z8300*.QAX / Z9800*.I1D / Z9800*.QAX
  - Binary BSL/OTOKO format 1D TOF-SANS data from polyamide-6 fibres hydrated
    in D2O collected on the LOQ instrument at ISIS. The data exhibit a broad
    lamellar peak from the semi-crystalline nanostructure.
  - This is the *same data* as that in ISIS_83404 / ISIS_98929 (see `1D Data`_)
    but in a historical separated format developed at the SRS Daresbury!
  - Suitable for testing the :ref:`File_Converter_Tool` .
  - Suitable for testing :ref:`Correlation_Function_Analysis` after conversion.

LMOG_100254_merged_ISIS2D
  - ASCII format TOF-SANS data from low-molecular weight organo-gelator system
    collected on the LOQ instrument at ISIS.
  - The data are written in the historical COLETTE (or RKH) 2D format.
  - Suitable for testing the :ref:`File_Converter_Tool` .

YBCO_12685__ISIS2D
  - ASCII format TOF-SANS data from a Nb/YBaCuO superconductor sample collected
    on the SANS2D instrument at ISIS.
  - The data are written in the historical COLETTE (or RKH) 2D format.
  - Suitable for testing the :ref:`File_Converter_Tool` .

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

2D Data
^^^^^^^
2D data sets are data sets that give the reduced intensity for a given *Qx-Qy* bin.
Depending on the file format, uncertainty data and metadata may also be present.

2D Test Data
............
**Example data files are located in the \\2d_data sub-folder.**

14250_2D_NoDetInfo_NXcanSAS_v3
  - TOF-SANS data from an unidentified sample collected on the LARMOR instrument
    at ISIS.
  - The data are written in a minimalist form of the NXcanSAS standard format.

33837rear_2D_1.75_16.5
  - TOF-SANS data from a magnetically-oriented surfactant liquid crystal collected
    on the SANS2D instrument at ISIS.
  - The data are written in the NIST 2D format and two variants of the NXcanSAS
    standard format.
  - The NXcanSAS files were output by the Mantid framework v3.6 and v3.7.

BAM_2D
  - SAXS data from an oriented Fe sample collected at BAM.
  - The data are written in a minimalist form of the NXcanSAS standard format.

exp18_14_igor_2dqxqy
  - SANS data from a non-centrosymmetric measurement collected on the HiResSANS
    instrument at ORNL.
  - The data are written in the NIST 2D format.

P123_D2O
  - TOF-SANS data from lyotropic liquid crystalline solutions of the non-ionic
    ABA block copolymer Pluronic P123 in D2O at 10wt%, 30wt%, and 40wt% collected
    on the LOQ instrument at ISIS.
  - This is the 2D form of the 1D radially-averaged data above (see `1D Data`_)!
  - The data are written in the NIST 2D format.
  - Suitable for testing paracrystal models.

SILIC010
  - SANS data from a 2% dispersion of silica nanoparticles in D2O collected at ORNL.
  - The data are written in the NIST 2D format.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Coordinate Data
^^^^^^^^^^^^^^^
Coordinate data, such as PDB (Protein Data Bank) or OMF/SLD (micromagnetic simulation)
files, and which describe a specific structure, are designed to be read and viewed in
the :ref:`SANS_Calculator_Tool` .

Coordinate Test Data
....................
**Example data files are located in the \\coordinate_data sub-folder.**

1n04
  - PDB format data file describing the structure of the protein transferrin.

2w0o
  - PDB format data file describing the structure of the protein apoferritin.

A_Raw_Example-1
  - OMF format data file from a simulation of magnetic spheres.

sphere_R=0_2025
  - vtk format data file describing a homogeneously magnetised sphere.  

diamond
  - PDB format data file describing the structure of diamond.

dna
  - PDB format data file describing the structure of DNA.

sld_file
  - Example SLD format data file.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Image Data
^^^^^^^^^^
Image data sets are designed to be read by the :ref:`Image_Viewer_Tool` .
They can also be converted into synthetic 2D data.

Image Test Data
...............
**Example data files are located in the \\image_data sub-folder.**

ISIS_98940
  - TOF-SANS data from polyamide-6 fibres hydrated in D2O collected on the LOQ
    instrument at ISIS. The data exhibit a broad lamellar peak from the semi-
    crystalline nanostructure which, because of the orientation of the fibres,
    gives rise to an anisotropic 2D scattering pattern.
  - The image data is presented in Windows Bitmap (.bmp), GIF (.gif), JPEG (.jpg),
    Portable Network Grpahics (.png), and TIFF (.tif) formats.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

SESANS Data
^^^^^^^^^^^
SESANS (Spin-Echo SANS) data sets primarily contain the normalised neutron
polarisation as a function of the spin-echo length. Also see :ref:`SESANS` .
SasView treats all files ending .ses as SESANS data.

.. note:: The .ses format is still under development and may be subject to change.

SESANS Test Data
................
**Example data files are located in the \\sesans_data sub-folder.**

sphere_isis
  - SESANS data from 100nm PMMA latex nanoparticles in h/d-decalin collected on
    the LARMOR instrument at ISIS over spin-echo lengths 260 < *z* < 19300 |Ang| .

spheres2micron
  - SESANS data from 2 micron polystyrene spheres in 53% H2O / 47% D2O collected
    on the LARMOR instrument at ISIS over spin-echo lengths 400 < *z* < 46000 |Ang| .

spheres2micron_long
  - SESANS data from 2 micron polystyrene spheres in 53% H2O / 47% D2O collected
    on the LARMOR instrument at ISIS over spin-echo lengths 400 < *z* < 200000 |Ang| .

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

DLS Data
^^^^^^^^
DLS (Dynamic Light Scattering) data sets primarily contain the intensity
autocorrelation function as a function of the delay time (in microseconds).

DLS Test Data
................
**Example data files are located in the \\dls_data sub-folder.**

dls_monodisperse / dls_polydisperse
  - DLS data from a very dilute dispersion of 3 nm polymer latex nanoparticles in
    h/d-water.
  - Suitable for testing the cumulants_dls model.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

NR Data
^^^^^^^
Neutron (NR) or X-ray (XR) Reflectometry data sets primarily contain the
interfacial reflectivity as a function of *Q*.

.. note:: The Refl1D reflectivity model-fitting software uses the same fitting
         engine (Bumps) as SasView.

NR Test Data
................
**Example data files are located in the \\nr_data sub-folder.**

NR_Ni_down_state / NR_Ni_up_state
  - Polarised (spin down/up) NR data from a Ni multilayer sample.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Save States
^^^^^^^^^^^
Saved states are projects and analyses saved by the SasView program.

A single analysis file contains the data and parameters for a single fit
(.fit), p(r) inversion (.prv), or invariant calculation (.inv).

A project file (.svs) contains the results for every active analysis in a
SasView session.

Saved State Test Data
.....................
fitstate.fitv
  - A saved fitting analysis.
  - The file contents are written in XML.

prstate.prv
  - A saved P(r) analysis.
  - The file contents are written in XML.
  
test.inv
  - A saved invariant analysis.
  - The file contents are written in XML.

test002.inv
  - A saved invariant analysis.
  - The file contents are written in XML.

constrained_fit_project
  - A saved fitting project.
  - The file contents are written in XML.

fit_pr_and_invariant_project
  - A saved fitting and invariant analysis project.
  - The file contents are written in XML.

project_multiplicative_constraint
  - A saved fitting project with multiple parameter constraints.
  - The file contents are written in XML.

project_new_style
  - A complex saved fitting project.
  - The file contents are written in JSON.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Upcoming Formats
^^^^^^^^^^^^^^^^
Data in this folder are in formats that are not yet implemented in SasView but
which might be in future versions of the program.

1000A_sphere_sm
  - CanSAS 1D format data from 1000 |Ang| spheres.
  - This version of the format was written by the NIST IGOR reduction software
    (cf. similar xml data in the `1D Data`_ folder).

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Other Test Data
^^^^^^^^^^^^^^^
Data in this folder include weights for testing user-defined distributions (i.e.,
polydispersity) on angular (theta/phi) or size (radius/length) parameters.

.. note:: Please read the help documentation on :ref:`polydispersityhelp` before
          attempting to use user-defined distributions.

dist_THETA_weights.txt

phi_weights.txt

radius_dist.txt

THETA_weights.txt

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 26Oct2021
