.. testdata_help.rst

Test Data
=========

Test data sets are included as a convenience to our users. Look in the \test 
sub-folder in your SasView installation folder.

The data sets are organized based on their data structure; 1D data, 2D data, 
SASVIEW saved states, and data in formats that are not yet implemented but 
which are in the works for future versions.

1D data sets have at least two columns of data with Intensity (assumed 
absolute units) on the Y-axis and Q on the X-axis. 

2D data sets are data sets that give the deduced intensity for each detector 
pixel. Depending on the file extension, uncertainty and meta data may also be 
available.

Saved states are projects and analyses saved by the SasView program. A single 
analysis file contains the data and parameters for a single fit (.fit), p(r) 
inversion (.pr), or invariant calculation (.inv). A project file (.svs) contains 
the results for every active analysis.

Some of the available test data is described below.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

1D Test Data
^^^^^^^^^^^^

AOT_Microemulsion
  - Aerosol-OT surfactant stabilised oil-in-water microemulsion data at three 
    contrasts: core (oil core), drop (oil core + surfactant layer), and shell 
    (surfactant layer).
  - Suitable for testing simultaneous fitting.
  
hSDS_D2O
  - h25-sodium dodecyl sulphate solutions at two concentrations: 0.5wt% (just 
    above the cmc), 2wt% (well above the cmc), and 2wt% but with 0.2mM NaCl 
    electrolyte.
  - Suitable for testing charged S(Q) models.

P123_D2O
  - Lyotropic liquid crystalline solutions of non-ionic ABA block copolymer 
    Pluronic P123 in water at three concentrations: 10wt%, 30wt%, and 40wt%.
  - Suitable for testing paracrystal models.

ISIS_Polymer_Blend_TK49
  - Monodisperse (Mw/Mn~1.02) 49wt% d8-polystyrene : 51wt% h8-polystyrene 
    polymer blend.
  - Suitable for testing Poly_GaussCoil and RPA10 models.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

2D Test Data
^^^^^^^^^^^^

P123_D2O
  - Lyotropic liquid crystalline solutions of non-ionic ABA block copolymer 
    Pluronic P123 in water at three concentrations: 10wt%, 30wt%, and 40wt%.
  - Suitable for testing paracrystal models.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Saved State Test Data
^^^^^^^^^^^^^^^^^^^^^

_phi_weights.txt

_radius_dist.txt

_THETA_weights.txt

fitstate.fitv

newone.svs

prstate.prv

sld_file.sld

test.inv

test002.inv

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Other Test Data
^^^^^^^^^^^^^^^

1000A_sphere_sm.xml

diamond.pdb

dna.pdb

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 26Jun2015
