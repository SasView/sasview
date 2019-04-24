Release Notes
=============

.. note:: In Windows use [Alt]-[Cursor left] to return to the previous page

.. toctree::
   :maxdepth: 1

Features
========

New in Version 4.2.2
--------------------
This release fixes the known issues reported in 4.2.1: the inability to read in
project files due to the fixes (changes) in the NXcanSAS reader, and the fact
that the 2D resolution smearing was only being applied to one quadrant. A
number of documentation issues were also completed.

Resolved Issues
^^^^^^^^^^^^^^^
.. These would need including if sasmodels PR #101 (Ticket 1257) is merged;
.. PR #103 is already merged. The explanation being that by providing easy
.. access to the source we absolve ourselves of the need to markup hideous
.. equations! The commentary above would also need updating.
.. * Close # 106 (Trac # 646): Check all model documentation for standardization
.. * Fixes # 146 (Trac # 883): Add link to source code of each model to model documentation
.. * Nofix #1189 (Trac #1148): Documentation for S(Q) models need updating
.. * Nofix # 188 (Trac #1187): S(Q) models need function descriptions in documentation
.. * Nofix #1266 (Trac #1240): Many models do not have their equation in the documentation
.. * Fixes #1285 (Trac #1263): Change source links in model docs to local paths
.. 
.. These next 10 documentation issues were resolved during Code Camp IX
.. but would have been committed to master I think
* Close # 512 (Trac # 378): Add documentation for BUMPS usage and integrate rst files to SasView from BUMPS repo
* Close # 647 (Trac # 514): Review User Documentation
* Fixes # 799 (Trac # 668): Update plugin model documentation and testing 
* Fixes # 928 (Trac # 833): Improve smearing help
* Fixes # 968 (Trac # 882): Add notes to doc about fitting integer parameters
* Close #1024 (Trac # 947): Include sasmodels api docs in sasview developer documentation
* Nofix #1072 (Trac #1003): Should we use Dispersity instead of Polydispersity/Monodispersity?
* Fixes # 178 (Trac #1108): "Writing a Plugin Model" does not explain function "random"
* Fixes #1211 (Trac #1175): Need to rethink Tutorial option in GUI Help menu
* Fixes #1225 (Trac #1190): Documentation for magnetism need update 
.. These next 3 are already live on the website
* Fixes #1254 (Trac #1225): Update correlation function documentation re non-Lorentz-corrected data
* Fixes #1256 (Trac #1227): Copy over pdfs of updated correlation function tutorial before 4.2.1 release
* Fixes #1258 (Trac #1229): Copy updated corfunc_help to Github for new website docs
.. These next 3 are the main reason for 4.2.2
* Fixes #1268 (Trac #1242): Resolution smearing is only applied to positive Qx and Qy in 2D
* Fixes #1269 (Trac #1243): Problem reopening saved project .svs file
* Fixes #1276 (Trac #1253): Clarify no longer any pure python orientation/magnetism plugin support in docs

.. note:: Issues were moved from Trac to Github for 4.2.2. Numbering changed.

New in Version 4.2.1
--------------------
The major changes for this point release were to fix several problems with using
the built in editor to create new models and to bring the NXcanSAS reader into
compliance with the final published specification.  The orignal reader was
based on a draft version of the specification.  As an early adopter,
interpretation and implementation of the spec was iterated with all producers
of NXcanSAS reduced data known to the SasView team in order to ensure
compatibility and verify the implementation.  A few other enhancements and bug
fixed were also introduced such as cleaning up the resolution section of the
fitting page GUI, increasing the max size range allowed in the corfunc
analysis, and adding the incomplete gamma function to the python library. 

Resolved Issues
^^^^^^^^^^^^^^^
* Fixes #  976:	CanSas HDF reader will not read all valid CanSas HDF (NXcanSAS) files
* Fixes # 1074:	Add incomplete gamma function to sasmodels
* Fixes # 1111:	Convert all input Q units to 1/A
* Fixes # 1129:	NXcanSAS writer not writing all meta data
* Fixes # 1142:	Plugin framework is broken
* Fixes # 1183:	Test from creating new model reset all parameters to default in all open FitPages
* Fixes # 1188: Colons removed from magnetic parameter names to address Python variable issue - done in 4.2. but documented in 4.2.1
* Fixes # 1205:	4.2 set weighting choice seems to be ignored.
* Fixes # 1206:	Incorrect (and confusing) presentation of dQ from data in instrumental smearing section
* Fixes # 1212:	Bug in Iqxqy plotting non rectangular / square matrices?
* Fixes # 1221:	ABS reader does not read in USANS data properly	GitHub
* Fixes # 1222:	smearing options incorrect on show2D and show1D in fitpage14: Loading a saved project is really really slow
* Fixes # 1223:	Expand permitted range of transformed data in Corfunc implementation


New in Version 4.2.0
--------------------
This release heralds many improvements and a host of bug fixes, along with
some significant changes from previous versions. Further, as promised, it
marks the end of support for 32 bit operating systems and is only
available for 64 bit operating systems.

With this version the change to the new model API and plugins infrastructure
begun with 4.0 is essentially complete (though extensions are in the works,
and more are likely, they should remain backwardly compatible with previous
versions of SasView).

.. warning:: Old-style plugin models, including old sum|multiply models, continue
             to be supported (i.e. SasView will run them) in 4.x, although our
             automatic on-the-fly translation may not cope in all use cases (see 
             Known Issues below). However, this backward compatibility will be 
             removed in 5.0 and users are therefore strongly encouraged to 
             convert their custom models to the new API.

Finally, the changes to orientation angles and orientational distribution
definitions are now also complete.

Changes
^^^^^^^
* The infrastucture for calculating 2D patterns from 3D orientated objects
  has been totally re-factored. It is now more accurate and consistent
  across models.
* The way that SasView defines the orientation of anisometric and
  aligned objects has been completely overhauled. It now differs from
  previous versions.
* Plugin models, including sum|multiply models, have completely migrated
  to the new infrastructure. NOTE that 3.x type models as well as early,
  intermediate 4.x type models, including those generated by sum|multiply
  will continue to be supported in 4.x but will likely no longer be
  supported after the move to 5.0.  Users are strongly encouraged to
  migrate any custom models.
* The NeXus loader has been removed as it is superseded by the NXcanSAS
  standard loader and SasView does not support the treatment of raw
  data.

Improvements
^^^^^^^^^^^^
* The accuracy/speed of some numerical integrations have been improved.
* An orientation viewer tool has been introduced to assist in
  understanding the new orientation framework.
* Problems with the computation of magnetic scattering from some
  objects have been rectified. Some questions remain however.
* The known issue with the core_shell_parallelepiped model is now fixed.
* An error in the be_polyelectrolyte model was identified and rectified, but 
  the fix is yet to be validated.
* (Added post-release) An error with the reporting of the scale parameter 
  from the spinodal model was rectified.
* A number of issues and inconsistencies with the creation of
  sum|multiply models have been rectified.
* A Boltzmann distribution has been added for polydispersity/orientational
  distributions.
* Some batch slicing options have been introduced.
* Correlation function analysis now computes both the 1D and 3D functions.
* There are several data loading improvements.
* There are several improvements to Save/Load Project.
* The SasView version number now appears in Reports.
* The Release Notes are now available from the program Help menu.
* There have been numerous other bug fixes.

Documentation
^^^^^^^^^^^^^
Several sections of the help documentation have undergone significant
checking and updating, particularly those relating to orientation,
magnetic scattering, and polydispersity distributions.

Detailed advanced instructions for plugin writing and some scripting
instructions have also been added.

Concerns about the intended versus implemented meaning of some parameters
in the bcc_paracrystal, fcc_paracrystal, and sc_paracrystal models have
been brought to our attention. These have yet to be resolved and so a
Warning has been placed on each of these models. Anyone who feels they
may have the requisite expertise to investigate these concerns is strongly
encouraged to contact the Developers!

Other Work
^^^^^^^^^^
* A Third-Party initiative has recently succeeded in getting SasView to
  run on Debian. More details at
  http://trac.sasview.org/wiki/DevNotes/Projects/Debian
* With this release we have started to prepare for the inevitable move
  to Python 3, which will occur with the release of 5.0
* SasView 5.0 is currently in development. The two most significant
  features of this version will be (i) a move away from the present
  WxPython GUIs to new, completely rewritten, Qt5 GUIs, and
  (ii)implementation of the Beta-approximation for S(Q). Subject to
  resources, some limited access to the latter functionality may be
  available in a future SasView 4.x release.

Bug Fixes
^^^^^^^^^
* Fixes #  14: Loading a saved project is really really slow
* Fixes # 260: Box integration does not update when entering values in dialog
* Fixes # 446: Saving plot as PGF (not PDF!) format throws error
* Fixes # 467: Extend batch functionality to slicer
* Fixes # 489: ABS reader (NIST 1D) does not handle negative dx properly (USANS slit smearing)
* Fixes # 499: create sin(x)/x, 2*J1(x)/x and 3*j1(x)/x functions
* Fixes # 510: Build PDF documentation along with HTML
* Fixes # 525: Add GUI category defaults to models in sasmodels
* Fixes # 579: clean up sasview directory
* Fixes # 597: Need to document Combine Batch Fit
* Fixes # 645: GUI logic problem in Batch vs single fit mode
* Fixes # 648: Need to allow user input background value in Pr perspective
* Fixes # 685: Fix data upload to marketplace
* Fixes # 695: linear slope in onion model
* Fixes # 735: Review new Corfunc documentation
* Fixes # 741: Recalculate P(Q) and S(Q) components on model update.
* Fixes # 767: Sum/Product Models don't do what they should
* Fixes # 776: angular dispersity
* Fixes # 784: Add 3D integral to Correlation Function analysis
* Fixes # 786: core_shell_parallelepiped 1-D model is incorrect
* Fixes # 818: â€œreport buttonâ€� followed by â€œsaveâ€� makes an empty pdf file???
* Fixes # 830: Check compliance of loader against NXcanSAS-1.0 release
* Fixes # 838: Fix model download from marketplace
* Fixes # 848: can't save analysis when only one fit page
* Fixes # 849: Load Folder should ignore files starting with .
* Fixes # 852: More unit tests, especially for oriented or 2d models
* Fixes # 854: remove unnecessary sleep() in fitting perspective
* Fixes # 856: Reading SAS_OPENCL from custom_config sometimes raises an ERROR
* Fixes # 861: cannot defined a structure factor plugin
* Fixes # 864: New Model Editor (simple plugin editor) error parsing parameter line
* Fixes # 865: Plugin live discovery issues
* Fixes # 866: inform user when NaN is returned from compute
* Fixes # 869: fit page computation thread cleanup
* Fixes # 875: Possible weirdness with 1D NXcanSAS data
* Fixes # 876: Add check for HDF5 format in dataloader
* Fixes # 887: reorganize tree, separating the installed source from the build source
* Fixes # 889: Refactor dataloader error handling infrastructure
* Fixes # 890: use new orientation definition for asymmetric shapes
* Fixes # 891: update docs for oriented shapes with new orientation definition
* Fixes # 896: equations in core shell parallelepiped docs do not match code
* Fixes # 898: Image Viewer Tool file selector issue
* Fixes # 899: Igor Reader q calculation
* Fixes # 902: IgorReader Q calculation needs fixing/improving
* Fixes # 903: sasview - all non-gui tests should be converted to run in Python 3
* Fixes # 906: polydispersity not showing up in tabulated results
* Fixes # 912: About box points to misleading contributors page on Github
* Fixes # 913: Need to add Diamond developer and logo in relevant places
* Fixes # 915: load project issues
* Fixes # 916: Proper Logging
* Fixes # 920: Logarithmic binning option in the slice viewer
* Fixes # 921: Improve developer communication methods
* Fixes # 922: Remove support for all data formats that are not in q space
* Fixes # 923: Add CI and trac integrations to Slack
* Fixes # 930: fitting help says chisq is normalized to number of points
* Fixes # 931: Allow admins to edit all models and upload data etc on marketplace
* Fixes # 932: Need to fix upload of data files to marketplace
* Fixes # 934: Slurp tutorial repo for tutorials
* Fixes # 935: Build new tutorials as PDF
* Fixes # 943: Deep copy error on setting model after data is selected
* Fixes # 950: Most of the readers don't close files properly.
* Fixes # 954: cross check dll/opencl/python polydispersity and orientation results
* Fixes # 956: Possible problem with new doc build process
* Fixes # 961: sasmodels tests should fail if the parameter name does not exist
* Fixes # 962: star polymer typo in docs
* Fixes # 966: Inconsistent chi2 reporting
* Fixes # 967: no uncertainties errors on fitting parameters
* Fixes # 969: About Box not picking up dls_logo.png
* Fixes # 970: ASCII loader doesn't handle ISIS 2D ASCII
* Fixes # 974: blacklist Intel HD 620/630 for double precision
* Fixes # 978: load project fails for pages which have not been defined
* Fixes # 983: Remove Nexus Loader
* Fixes # 984: PDF reports are not being properly generated on Windows
* Fixes # 985: Saving Project Fails
* Fixes # 986: Send to fitting overwrites theory page even if blank FitPage has focus
* Fixes # 990: utest_sasview.py giving different results than run_one.py
* Fixes # 993: Windows x64 versions not installing to correct folder
* Fixes # 994: Error changing fit engine
* Fixes # 995: OpenCL required on Linux even if turned off in GUI
* Fixes #1006: multiplicity models don't work with SQ
* Fixes #1007: spherical_sld model freezes SasView
* Fixes #1008: plugin model scaling not working?
* Fixes #1010: Win64 build script not creating working executable
* Fixes #1011: sld_test failing on ubuntu
* Fixes #1013: FileReaderBaseClass output[] not reset - same file loaded multiple times
* Fixes #1018: add Boltzmann distribution
* Fixes #1021: add PDF documentation to website and document in wiki release process
* Fixes #1024: Update version numbers in master
* Fixes #1025: Sum/multiply editor hangs
* Fixes #1030: volume normalization for hollow shapes is different from solvent-filled shapes
* Fixes #1032: convert C++ modules to C
* Fixes #1035: Order of combining P(Q) and S(Q) in Plugins seems to matter
* Fixes #1037: data loader crop not working? & all fits crashing
* Fixes #1043: problem compiling marketplace models
* Fixes #1044: Unable to upload c file to marketplace
* Fixes #1046: convert non builtin models in the marketplace to new API
* Fixes #1050: fix appveyor test for sasmodels win 64 python 3
* Fixes #1052: Can't use a user-created plugin model in a plugin model
* Fixes #1054: Check plugin & orientation descriptions in full docs once SasModels PR #57 is merged
* Fixes #1057: phi rotation issue for elliptical cylinder
* Fixes #1060: incorrect default for rectangle dispersion
* Fixes #1062: win32 build not installing correctly
* Fixes #1064: "Fitting did not converge!!!" error with a Sum|Multi plugin model
* Fixes #1068: 2d data (from NG7) not loadiing - strange format?
* Fixes #1069: GUI problem when using polydispersity/orientation distributions
* Fixes #1070: Parameter error boxes should not be editable
* Fixes #1072: Orientation distributions seem to depend on initial angle
* Fixes #1079: Remove save button in report dialog on Mac
* Fixes #1081: GUI problem with new orientation distribution
* Fixes #1083: Magnetic models not being computed
* Fixes #1099: Erratic behaviour of Sum|Multi model in 4.1.2
* Fixes #1101: Batch results page not displaying polydispersity values
* Fixes #1128: AutoPlot generation for model documentation does not include background
* Fixes #1131: OpencCl dialog does not open
* Fixes #1132: Slit Size Calculator Tool not working
* Fixes #1139: Missing Docs and Help for new Batch Slicing
* Fixes #1141: Intro to scripting.rst needs improvement
* Fixes #1142: Plugin framework is broken
* Fixes #1145: Update models in model marketplace to 4.2 when 4.2 is released.
* Fixes #1155: BE Polyelectrolyte errors
* Fixes #1160: fix VR for core_shell_cylinder, fractal_core_shell and hollow_cylinder
* Fixes #1163: Fix help note in sum of sum|multiply interface
* Fixes #1164: Sphinx doc build does not support superscript or substitution
* Fixes #1166: No longer able to report from multiple fit pages
* Fixes #1167: Clarify the documentation for the Spinodal Model
* Fixes #1173: more problems with math in plugins
* Fixes #1176: Make Release Notes/Known Issues available from Help in Menu Bar
* Fixes #1179: PDF Report should contain SasView Version Number
* Fixes #1183: Test from creating new model reset all parameters to default in all open FitPages
* Fixes #1188: fitpage hangs if change model while magnetism is on
* Fixes #1191: Correct erroneous Scale reported by Spinodal model

**It is recommended that all users upgrade to this version, but your 
attention is drawn to the Changes section above.**


New in Version 4.2.0-Beta
-------------------------
This is a beta pre-release version of 4.2.0.  A number of fixes and changes
have been made in the year since the previous release. Full release notes
will be compiled prior to the full release 4.2.0.

Highlights are:

* Infrastucture for calculating 2D patterns from 3D orientated objects
  has now been totally refactored
* Plugins have completely migrated to the new infrastructure now,
  including sum/multiply models
* Some batch slicing options have been introduced
* The known issue with the core_shell_parallelepiped is now fixed
* Several data loading improvements
* Several save Project improvements (though there are more to come)
* Numerous bug fixes
* Lots of documentation enhancement

In the meantime please report any bugs or issues found while using this beta


New in Version 4.1.2
--------------------
This point release is a bug-fix release addressing:

* Fixes #984: PDF Reports Generate Empty PDFs
* Fixes a path typo
* 64 bit and 32 bit Windows executables now available

It is recommended that all users upgrade to this version


New in Version 4.1.1
--------------------
This point release is a bug-fix release addressing:

* Fixes #948: Mathjax CDN is going away
* Fixes #938: Cannot read canSAS1D file output by SasView
* Fixes #960: Save project throws error if empty fit page
* Fixes #929: Problem deleting data in first fit page
* Fixes #918: Test folders not bundled with release
* Fixes an issue with the live discovery of plugin models
* Fixes an issue with the NXcanSAS data loader
* Updated tutorials for SasView 4.x.y


New in Version 4.1.0
--------------------
This incremental release brings a series of new features and improvements,
and a host of bug fixes. Of particular note are:

Correlation Function Analysis (Corfunc)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
This performs a correlation function analysis of one-dimensional SAXS/SANS data,
or generates a model-independent volume fraction profile from the SANS from an
adsorbed polymer/surfactant layer.

A correlation function may be interpreted in terms of an imaginary rod moving
through the structure of the material. G1(R) is the probability that a rod of
length R moving through the material has equal electron/neutron scattering
length density at either end. Hence a frequently occurring spacing within a
structure manifests itself as a peak.

A volume fraction profile \Phi(z) describes how the density of polymer
segments/surfactant molecules varies with distance from an (assumed locally flat)
interface. *This is not yet implemented*.

Fitting of SESANS Data
^^^^^^^^^^^^^^^^^^^^^^
Data from Spin-Echo SANS measurements can now be loaded and fitted. The data will
be plotted against the correct axes and models will automatically perform a Hankel
transform in order to calculate SESANS from a SANS model.

Documentation
^^^^^^^^^^^^^
The documentation has undergone significant checking and updating.

Improvements
^^^^^^^^^^^^
* Correlation function (corfunc) analysis of 1D SAS data added from CCP13
* File converter tool for multi-file single column data sets
* SESANS data loading and direct fitting using the Hankel transformation
* Saving and loading of simultaneous and constrained fits now supported
* Save states from SasView v3.x.y now loaded using sasmodel model names
* Saving and loading of projects with 2D fits now supported
* Loading a project removes all existing data, fits, and plots
* Structure factor and form factor can be plotted independently
* OpenCL is disabled by default and can be enabled through a fit menu
* Data and theory fields are now independently expandable

Bug Fixes
^^^^^^^^^
* Fixes #667: Models computed multiple times on parameters changes
* Fixes #673: Custom models override built in models of same name
* Fixes #678: Hard crash when running complex models on GPU
* Fixes $774: Old style plugin models unloadable
* Fixes #789: stacked disk scale doesn't match cylinder model
* Fixes #792: core_shell_fractal uses wrong effective radius
* Fixes #800: Plot range reset on plot redraws
* Fixes #811 and #825: 2D smearing broken
* Fixes #815: Integer model parameter handling
* Fixes #824: Cannot apply sector averaging when no detector data present
* Fixes #830: Cansas HDF5 reader fully compliant with NXCanSAS v1.0 format
* Fixes #835: Fractal model breaks with negative Q values
* Fixes #843: Multilayer vesicle does not define effective radius
* Fixes #858: Hayter MSA S(Q) returns errors
* Numerous grammatical and contexual errors in documention


New in Version 4.0.1
--------------------
This release fixes the critical bug #750 in P(Q)xS(Q).  Most damaging
it appears that the background term was being added to S(Q) prior to
multiplication by P(Q).


New in Version 4.0
------------------
This release fixes the various bugs found during the alpha and beta testing

Improvements
^^^^^^^^^^^^
* Support for reading data files from Anton Paar Saxess instruments
* Adds documentation on how to write custom models in the new framework

Bug Fixes
^^^^^^^^^
* Fixes #604: Pringle model questions
* Fixes #472: Reparameterize Teubner-Strey
* Fixes #530: Numerical instabilities in Teubner Strey model
* Fixes #658: ASCII reader very broken


New in Version 4.0 beta 1
-------------------------
This beta adds support for the magnetic and multilevel models of 3.1.2
and along with a host of bug fixes found in the alpha.

Model package changes and improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* All 3.1.2 models now available in new interface
* Old custom models should now still work
* Custom model editor now creates new style models
* Custom model editor supports better error checking
 
.. note:: Old custom models should be converted to the new model format 
          which is now the same as the built-in models and offers much 
          better support. The old custom model format will be deprecated 
          in a future version.

Documentation improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^
* Continued general cleanup

Other improvements/additions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Support for new canSAS 2D data files added
* Plot axes range can now be set manually as well as by zooming
* Plot annotations can now be moved around after being placed on plot.
* The active optimizer is now listed on the top of the fit panel.
* Linear fits now update qmin and max when the x scale limits are
  changed.  Also the plot range no longer resets after a fit.

Bug fixes
^^^^^^^^^
* Fixes #511: Errors in linearized fits and clean up of interface
  including Kratky representation
* Fixes #186: Data operation Tool now executes when something is
  entered in the text box and does not wait for the user to hit enter
* Fixes #459: plot context menu bug
* Fixes #559: copy to clipboard in graph menu broken
* Fixes #466: cannot remove a linear fit from graph
* Numerous bugs introduced in the alpha


New in Version 4.0.0-alpha
--------------------------
This alpha release brings a major overhaul of the model system. The new model
package allows rapid integration of custom models and access to polydispersity
without requiring a compiler.

Model package changes and improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Separation of GUI and calculations for future GUI enhancements
* Model interface moved to independent sasmodels package.
* Most models converted to new interface.
* Allows rapid integration of user-written models.
* OpenCL GPU utilization for faster fitting.
* Improved numerical integration of Bessel functions.

SESANS integration and implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Scripting interface added for analysis of SESANS data.
* Hankel transformation now accepts finite acceptance angles.
* 2D cosine transformation added for TOF SESANS analysis.

Documentation improvements
^^^^^^^^^^^^^^^^^^^^^^^^^^
* The documentation tree was restructured for a better end user experience.
* The documentation for each model was revamped and verified by at least
  two people following the conversion of the model.
* Theoretical 1D (and 2D if applicable) scattering curves are auto-generated
  and added to the model documentation for each model.
   
Bug fixes
^^^^^^^^^
* Fixes #411: No stop button on simultaneous fit page
* Fixes #410: Error with raspberry model
* Fixes #364: Possible inconsistency in Poly_GausCoil model
* Fixes #439: Hayter Penfold MSA code needs checking
* Fixes #484: lammellerPC is precision limited
* Fixes #498: $HOME/.matplotlib conflicts
* Fixes #348: Control order in which fit parameters appear in the gui
* Fixes #456: Provide DREAM Results Panel with something to identify
  data and age of results
* Fixes #556: Build script improvements for developers


New in Version 3.1.2
--------------------
This release is a major stability improvement, having fixed a serious bug
that came to light since release 3.1.1. All users should upgrade.

* Fixes #468: broken remove constraint buttons in
  simultaneous/constrained fitting panel
* Fixes #474: resulting from changes in 3.1.1 that had
  introduced an error in the high-Q of slit-smeared models.
* Fixes #478: which would cause wx to run out of IDs and result
  in SasView crashing even if left alone.
* Fixes #479: missing help button on simultaneous/constrained fit page
* Fixes #480: GUI resizing issues on simultaneous fit page
* Fixes #486: broken Report Results
* Fixes #488: redraw issues in fit page


New in Version 3.1.1
--------------------
Fixes #457 that prevented SasView from starting if the user was not
connected to the internet, or was behind a proxy server.


New in Version 3.1.0
--------------------
The documentation/help has had a complete overhaul including:

* A completely new presentation interface (Sphinx).
* Proof reading!
* Updating for latest features.
* A Help (or sometimes ?) button has been added to every panel, and some
  sub panels if appropriate, linking to the appropriate section in the
  documentation.
* The model help has been split so that the Details button now brings up
  a very short pop-up giving the equation being used while HELP goes to
  the section in the full documentation describing the model.
* Extensive help has also been added for the new optimizer engine (see
  below) including rules of thumb on how and when to choose a given
  optimizer and what the parameters do.

The optimizer engine has been completely replaced. The new optimizer
still defaults to the standard Levenberg-Marquardt algorithm. However 4
other optimizers are now also available. Each starts with a set of default
parameters which can be tuned. The DREAM optimizer takes the longest but
is the most powerful and yields rich information including full parameter
correlation and uncertainty plots. A results panel has been added to
accommodate this. The five new optimizers are:

* A Levenberg-Marquardt optimizer
* A Quasi-Newton BFGS optimizer
* A Nelder-Mead Simplex optimizer
* A Differential Evolution optimizer
* A Monte Carlo optimizer (DREAM)

New models were added:

* MicelleSphCoreModel (currently residing in the Uncategorized category)

Existing models were updated:

* LamellarPS (bug in polydispersity integration fixed)
* RectangularPrismModel
* RectangularHollowPrismModel
* RectangularHollowPrismInfThinWallsModel

Other work:

* Infrastructure to allow SESANS data to be fit with models was added. This
  will become available in a future release but can currently be used from
  the command line with some caveats.
* A number of bugs were fixed including a thread crashing issue and an
  incorrect slit smearing resolution calculation.
* Implemented much more robust error logging to enable much easier
  debugging in general but particularly the debugging of issues reported by
  SasView users.
* A number of infrastructure tasks under the hood to enhance maintainability
* Upgrade from Wx 2.8 to Wx 3.0.2 which allows several new features but
  required significant additional rework as well.
* Fully implemented Sphinx to the build process to produce both better
  user documentation and developer documentation.
* Restructuring of the code base to more unified nomenclature and structure
  so that the source installation tree more closely matches the installer
  version tree.
* Code cleanup (an ongoing task).
* Migration of the repository to github simplifying contributions from
  non-project personnel through pull requests.


New in Version 3.0.0
--------------------
* The GUI look and feel has been refactored to be more familiar for
  Windows users by using MDI frames. Graph windows are also now free-
  floating.
* Five new models have been added: PringlesModel, CoreShellEllipsoidXTModel,
  RectangularPrismModel, RectangularHollowPrismModel and
  RectangularHollowPrismInfThinWallsModel.
* The data loader now supports ILL DAT data files and reads the full meta
  information from canSAS file formats.
* Redefined convention for specifying angular parameters for anisotropic
  models.
* A number of minor features have been added such as permitting a log
  distribution of points when using a model to simulate data, and the
  addition of a Kratky plot option to the linear plots.
* A number of bugs have also been fixed.
* Save Project and Save Analysis now work more reliably.
* BETA: Magnetic contrast supporting full polarization analysis has been
  implemented for some spherical and cylindrical models.
* BETA: Two new tools have been added:

  * A generic scattering calculator which takes an atomic, magnetic or
    SLD distribution in space and generates the appropriate 2D
    scattering pattern. In some cases the orientationally averaged
    (powder) 1D scattering can also be computed. Supported formats
    include: SLD or text, PDB, and OMF magnetic moment distribution
    file.
  * An image viewer/converter for data in image format; this reads in
    an image file and will attempt to convert the image pixels to
    data. Supported formats include: TIFF, TIF, PNG, BMP, JPG.


New in Version 2.2.1
--------------------
* Minor patch to support CanSAS XML v1.1 file format
* Added DataInfo for data in the DataExplorer and plots
* Added Maximize/Restore button in the title bar of the graphs
* Added a hide button in the toolbar of the graph panel
* The 'x' button now deletes a graph
* Edit SUM Model from the menubar can now generate and save more than one sum model
* Reports can now be saved in pdf format on WIN and MAC
* Made significant improvements to the batch/grid panel and fixed several bugs
* Fixed a number of other minor bugs


New in Version 2.2.0
--------------------
* Application name changed to SasView
* New fully customizable Category Manager added for better management of
  increasing number of models
* Improved the Grid Window functionality in the batch fitting mode
* Added a simpler Graph/Plot modification interface
* Added a new 'Data Operation' tool for addition, subtraction, multiplication,
  division, of two data sets.
* The 'Sum Model' editor was extended and renamed 'Summation and Multiplication'
  editor
* Added more plot symbols options for 1d plots
* Added improved trapping of compiling errors to the 'New model editor'
* Added some intelligent outputs (e.g., Rg, background, or rod diameter
  depending on the choice of axis scale of the plot) to the linear fits
* Added more models


Feature set from previous versions
-----------------------------------
Perspectives Available
^^^^^^^^^^^^^^^^^^^^^^
* Invariant calculator: Calculates the invariant, volume fraction, and
  specific surface area.
* P(r) inversion calculator: Indirect Fourier transformation method.
* Fitting: the tool used for modeling and fitting 1D and 2D data to
  analytical model functions
* Tools: provides a number of useful supplementary tools such as SLD
  calculation

Fitting
^^^^^^^
* Includes a large number of model functions, both form factors and structure factors.
* Support P(Q)*S(Q) for form factors that flag they can be so multiplied.
* Supports Gaussian, lognormal, Shulz, rectangular and custom distribution
  functions for models that need to include polydispersity or for orientational
  distributions if appropriate.
* Anisotropic shapes and magnetic moment modeling in 2D allow for a non-uniform
  distribution of orientations of a given axis leading to modeling and fitting
  capabilities of non azimuthaly symmetric data.
* User can choose to weight fits or not. If using weights, the user can choose
  the error bar on each point if provided in the file, the square root
  of the intensity or the intensity itself.
* Instrumental resolution smearing of model or fits is provided with several
  options: read the resolution/point fromt he file. Input a pinhole resolution
  or a slit resolution.
* Users can define the Qrange (Qmin and Qmax) for both 1D and 2D data for
  fitting and modeling, but not graphically.  The range can be reset to the
  defaults (limits of q in data set for a fit) with the reset button.
* A mask can be applied to 2D calculation and fitting.
* Normalized residual plots are provided with every fit.
* Model function help available through detail button or from the fitting panel.
* Simultaneous/(advanced)constrained fitting allows for fitting a single
  data set or several different sets simultaneously with the application
  of advanced constraints relating fit parameters to functions of other
  parameters (including from a different set). For example thickness of
  shell = sin(30) times the length.
* Models that are the sum of two other models can be easily generated through the
  SUM Model menubar item.
* New Python models can be added on the fly by creating an appropriate Python
  file in the model plugin directory. Two tools are provided to help:
  An easy to use custom model editor allows the quick generation of new Python
  models by supplying only the parameters and their default value (box 1)
  and the mathematical function of the model (box 2) and generating the
  necessary .py file.  A separate advanced model editor provides a full Python
  file editor.  Either way once saved the model becomes immediately available
  to the application.
* A batch fitting capability allows for the analysis of a series of data sets to
  a single model and provides the results in a tabular form suitable for saving
  or plotting the evolution of the fit parameters with error bars (from within
  the application).

Tools
^^^^^
* A scattering length density calculator,including some X-ray information
  is provided.
* A density to vol. fraction converter is provided
* In application access to a Python shell/editor (PyCrust) is provided
* An instrument resolution calculator, including possible gravitational and
  TOF effects is provided
* A slit size calculator optimized for Anton Paar Saxess is provided.
* A kiessig fringe thickness calculator is provided

Plots and plot management
^^^^^^^^^^^^^^^^^^^^^^^^^
* A 3D graphing option (for 2d data/results) is provided with the view
  controlled by the mouse
* 2D plots are shown with an intensity color bar. 2D Color map can be user
  adjusted.
* Supports output of plot to a variety of graphic formats. Supported formats
  include: png, eps, emf, jpg/jpeg, pdf, ps, tif/tiff, rawRGBbitmap(raw, rgba),
  and scalable vector graphic (svg/svgz)
* Supports ouput of data in plot (1 or 2D) to limited data formats
* Multiple data sets can be loaded into a single graph for viewing (but a fit
  plot can currently only have a single plot).
* Extensive context sensitive plot/fitting/manipulation options are available
  through a right mouse click pop-up menu on plots.

Data management
^^^^^^^^^^^^^^^
* Supports 2 + column 1D ASCII data, NIST 1D and 2D data, and canSAS data
  via plug-in mechanism which can easily allow other readers as appropriate.
* 2D data is expected in Q space but for historical reasons accepts the
  NIST 2D raw pixel format and will do conversion internally.
* The full data and metadata available to SasView is viewable in ASCII via
  right clicking on a data set and choosing Data Info in the DataExplorer
  or on the plots
* Supports loading a single file, multiple files, or a whole folder
* An optional Data Explorer is provided (default) which simplifies managing,
  plotting, deleting, or setup for computation. Most functions however do
  not require access to the explorer/manager and can be accessed through
  right click menus and the toolbar.  The data explorer can be re-started
  from the menu bar.

Data manipulation
^^^^^^^^^^^^^^^^^
* Support various 2D averaging methods : Circular, sectors, annular,
  boxsum, boxQx and boxQy.
* A 2D data maks editor is provided
* 2D mask can be applied to the circular averaging.

Miscellaneous features
^^^^^^^^^^^^^^^^^^^^^^
* Limited reports can be generated in pdf format
* Provides multiprocessor support(Windows only)
* Limited startup customization currently includes default startup
  data folder and choice of default starting with data manager
* Limited support for saving(opening) a SasView project or a SasView analysis
  (subproject) is provided.
* SasView can be launched and loaded with a file of interesty by double-clicking
  on that file (recognized extension)
* A data file or data folder can be passed to SasView when launched from
  the command line.
* Limited bookmarking capability to later recall the results of a fit calculation
  is provided.
* Extensive help is provided through context sensitive mouse roll-over,
  information bar (at the bottom of the panel), the console menu, and
  access to the help files in several different ways.


Downloading and Installing
==========================

.. note:: If you have a SasView installer (.EXE or .MSI), you do not need to
          worry about any of the following.  However, it is highly recommended 
          that any previous versions of SasView are uninstalled prior to 
          installing the new version UNLESS you are installing SasView to 
          versioned folders.

.. note:: The easiest approach to setting up the proper environment to
          build from source is to use Conda.  Instructions for setting up
          and using Conda can be found at http://trac.sasview.org/wiki/DevNotes/CondaDevSetup
                    
.. note:: Much more information is available at www.sasview.org under 
          links/downloads. In particular, look in the 'For Developers' section. 
          Also have a look at http://trac.sasview.org/

System Requirements
-------------------
* Python version >= 2.5 and < 3.0 should be running on the system
* We currently use Python 2.7

Package Dependencies
--------------------
* Ensure the required dependencies are installed
* For the latest list of dependencies see the appropriate yml file in
  the SasView repo at sasview/build_tools/conda/ymls

Installing from Source
----------------------
* Get the source code
* Create a folder to contain the source code; if working with
  multiple versions you might want to use versioned folder names
  like 'sasview-x.x.x'
* Open a command line window in the source code folder
* To get the CURRENT DEVELOPMENT VERSION from source control use
  git clone https://github.com/SasView/sasview.git sasview
  git clone https://github.com/Sasview/sasmodels.git sasmodels
  git clone https://github.com/bumps/bumps.git bumps
* To get a SPECIFIC RELEASE VERSION from source control go to
  https://github.com/SasView/sasview/releases
  and download the required zip or tar.gz file. Unzip/untar it
  to the source code folder.

Building and Installing
-----------------------
* To build the code
  use 'python setup.py build'
* To build the documentation
  use'python setup.py docs'

Running SasView
---------------
* use 'python run.py'; this runs from the source directories, so you
  don't have to rebuild every time you make a change, unless you are
  changing the C model files.
* if using Conda the above command will also build SasView, but you 
  must issue 'activate sasview' first.


Known Issues
============

All known bugs/feature requests can be found in the issues on github. Note the
sasmodels issues are now separate from the sasview issues (i.e. in different
repositories)
* sasview:   https://github.com/SasView/sasview/issues
* sasmodels: https://github.com/SasView/sasmodels/issues

The old list, frozen as of April 2019, given by release version can still be
viewed at http://trac.sasview.org/report/3

4.2.1 - All systems
-------------------
Unfortunately, changes made to the data loader to address Trac ticket #976
(CanSas HDF reader will not read all valid CanSas HDF (NXcanSAS) files) have
broken backward compatibility and this version of SasView will not read in
saved project files (because these store data as NXcanSAS). 

4.2.0 - All systems
-------------------
The refactoring of the plugin model architecture means that some issues 
may be encountered if Save Project/Analysis files using plugin models 
created in earlier versions of SasView are loaded in version 4.2.0.

For example:

* on loading an old project file an error window appears with the error 
  *This model state has missing or outdated information* or *dictionary changed size during iteration*.

   * if this occurs, try restarting SasView and reloading the project.
   
* on loading an old project file all the FitPages and Graphs appear, but 
  only the SasView default model parameters appear in the FitPages.

  * this has happened because plugin model parameter names have changed. 
    There are two possible workarounds:
    
   * Install the version of SasView that the project was created in, 
     recreate the plugin in that version, then run 4.2.0 and re-load 
     the project. All being well, 4.2.0 will still compile the old 
     plugin.

   * If 4.2.0 cannot compile the old plugin, the more tedious solution 
     is to use a text editor to do global search & replace operations 
     to change all the parameter names in the project file by hand. The 
     quickest way to see the *existing* parameter names is simply to 
     scroll to the bottom of the project file. To see what the *new* 
     parameter names should be, simply create the equivalent plugin in 
     SasView 4.2.0. In most instances, what was *p1_parameter* will 
     become *A_parameter*, *p2_parameter* will become *B_parameter*, 
     and so on. 

4.1.x- All systems
------------------
The conversion to sasmodels infrastructure is ongoing and should be
completed in the next release. In the meantime this leads to a few known
issues:

* The way that orientation is defined is being refactored to address
  long standing issues and comments.  In release 4.1 however only models
  with symmetry (e.g. a=b) have been converted to the new definitions.
  The rest (a <> b <> c - e.g. parellelepiped) maintain the same
  definition as before and will be converted in 4.2.  Note that
  orientational distribution also makes much more sense in the new
  framework.  The documentation should indicate which definition is being
  used for a given model.
* The infrastructure currently handles internal conversion of old style
  models so that user created models in previous versions should continue
  to work for now. At some point in the future such support will go away.
  Everyone is encouraged to convert to the new structure which should be
  relatively straight forward and provides a number of benefits.
* In that vein, the distributed models and those generated by the new
  plugin model editor are in the new format, however those generated by
  sum|multiply models are the old style sum|multiply models. This should
  also disappear in the near future
* The on the fly discovery of plugin models and changes thereto behave
  inconsistently.  If a change to a plugin model does not seem to
  register, the Load Plugin Models (under fitting -> Plugin Model
  Operations) can be used.  However, after calling Load Plugin Models, the
  active plugin will no longer be loaded (even though the GUI looks like
  it is) unless it is a sum|multiply model which works properly.  All
  others will need to be recalled from the model dropdown menu to reload
  the model into the calculation engine.  While it might be annoying it
  does not appear to prevent SasView from working..
* The model code and documentation review is ongoing. At this time the
  core shell parellelepiped is known to have the C shell effectively fixed
  at 0 (noted in documentation) while the triaxial ellipsoid does not seem
  to reproduce the limit of the oblate or prolate ellipsoid. If errors are
  found and corrected, corrected versions will be uploaded to the
  marketplace.
* (Added after Release 4.2.0) The scale parameter reported from the spinodal 
  model is the square root of the true value.

3.1- All systems
----------------
* The documentation window may take a few seconds to load the first time
  it is called. Also, an internet connection is required before
  equations will render properly. Until then they will show in their
  original TeX format.
* If the documentation window remains stubbornly blank, try installing a
  different browser and set that as your default browser. Issues have
  been noted with Internet Explorer 11.
* Check for Updates may fail (with the status bar message ' Cannot
  connect to the application server') if your internet connection uses
  a proxy server. Tested resolutions for this are described on the
  website FAQ.
* The copy and paste functions (^C, ^V) in the batch mode results grid
  require two clicks: one to select the cell and a second to select the
  contents of the cell.
* The tutorial has not yet been updated and is somewhat out of date
* Very old computers may struggle to run the 3.x and later releases
* Polydispersity on multiple parameters included in a simultaneous/
  constrained fit will likely not be correct
* Constrained/simultaneous fit page does not have a stop button
* Constrained/simultaneous fit do not accept min/max limits
* Save project does not store the state of all the windows
* Loading projects can be very slow
* Save Project only works once a data set has been associated with
  a model.  Error is reported on status bar.
* There is a numerical precision problem with the multishell model when
  the inner radius gets large enough (ticket #288)
* The angular distribution angles are not clearly defined and may in
  some cases lead to incorrect calculations(ticket #332)

3.1 - Windows
-------------
* If installed to same directory as old version without first removing
  the old version, the old desktop icon will remain but point to the
  new exe version. Likewise all the start menu folders and items will
  have the old name even though pointing to the new version.  Usually
  safest to uninstall old version prior to installing new version anyway.

3.1 - MAC
---------
* Application normally starts up hidden. Click icon in Dock to view/use
  application.
* Multiprocessing does not currently work on MAC OS

3.1 - Linux
-----------
* Not well tested


SasView Website
===============
http://www.sasview.org

This main project site is the gateway to all information about the sasview 
project.  It includes information about the project, a FAQ page and links 
to all developer and user information, tools and resources.


Frequently Asked Questions
==========================
http://www.sasview.org/faq.html


Installer Download Website
==========================
Latest release Version
https://github.com/SasView/sasview/releases

Latest developer builds
https://jenkins.esss.dk/sasview/view/Master-Builds/
