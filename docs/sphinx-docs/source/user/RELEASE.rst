.. RELEASE.rst

.. _Release_Notes:

Release Notes
=============

.. note:: In Windows use [Alt]-[Cursor left] to return to the previous page

.. toctree::
   :maxdepth: 1

Features
========

New in Version 6.1.1
--------------------

This is a minor bug fix release of SasView. It is built with Sasmodels v1.0.11, Sasdata v0.11.0, and Bumps v1.0.2.

Bug fixes
^^^^^^^^^

* Fix the magnetic fitting widget functionality by @rozyczko in https://github.com/SasView/sasview/pull/3581
* Fix for PD plotting by @krzywon in https://github.com/SasView/sasview/pull/3505
* Ensure plugin models are removed from the original user directory when moved by @krzywon in https://github.com/SasView/sasview/pull/3538
* Fix new version available widget on non-Windows systems by @jamescrake-merani in https://github.com/SasView/sasview/pull/3552
* Overide Qdialog closeEvent method to force kill(x) button to behave like the close button by @butlerpd in https://github.com/SasView/sasview/pull/3465
* Move the example data to the user directory and clean up by @krzywon in https://github.com/SasView/sasview/pull/3535
* Ensure the example data directory is in the same location as the tutorial says it is by @krzywon in https://github.com/SasView/sasview/pull/3585
* Clear the calculated values in the Inversion perspective when a lone data entry is removed by @DrPaulSharp in https://github.com/SasView/sasview/pull/3567
* Enable batch slicing to P(r) inversion by @dehoni and @jamescrake-merani in https://github.com/SasView/sasview/pull/3512
* Various fixes to batch P(r)  by @jamescrake-merani in https://github.com/SasView/sasview/pull/3563
* Ensure the external libausaxs is downloaded when building installers by @klytje in https://github.com/SasView/sasview/pull/3554

Documentation fixes
^^^^^^^^^^^^^^^^^^^

* Fixed MumMag typo (should be MuMag) by @krzywon in https://github.com/SasView/sasview/pull/3514
* Update corfunc-theory.rst by @lucas-wilkins in https://github.com/SasView/sasview/pull/3565

Linting changes
^^^^^^^^^^^^^^^

* Applies automatic fixes from the default ruff ruleset by @DrPaulSharp in https://github.com/SasView/sasview/pull/3507
* Adds ability to automatically apply ruff linting fixes to CI by @DrPaulSharp in https://github.com/SasView/sasview/pull/3520
* Applies fixes for Ruff linting errors by @DrPaulSharp in https://github.com/SasView/sasview/pull/3539
* Adds isort (I) ruleset to ruff linter by @DrPaulSharp in https://github.com/SasView/sasview/pull/3555
* Adds Pyupgrade (UP) ruleset and rules SIM118 & SIM300 to ruff linter by @DrPaulSharp in https://github.com/SasView/sasview/pull/3560
* Fixes whitespace errors by @DrPaulSharp in https://github.com/SasView/sasview/pull/3561

Infrastructure Changes
^^^^^^^^^^^^^^^^^^^^^^

* Fixes fatal access violation in Windows tests by @DrPaulSharp in https://github.com/SasView/sasview/pull/3497
* Disable dependabot for python dependency checks - Disable Dependabot by @krzywon in https://github.com/SasView/sasview/pull/3517
* Stop new version dialogue from appearing in test by @llimeht in https://github.com/SasView/sasview/pull/3364
* Speed up CI with faster python module installation with uv by @llimeht in https://github.com/SasView/sasview/pull/3351
* Update tarball name in nightly flow to match CI.yml by @llimeht in https://github.com/SasView/sasview/pull/3334
* Clean out nightly files by @llimeht in https://github.com/SasView/sasview/pull/3337
* Suppress signature errors when CI run on PRs from forks by @llimeht in https://github.com/SasView/sasview/pull/3355
* Publish wheels along side other installers in nightly-builds action by @llimeht in https://github.com/SasView/sasview/pull/3335
* Specify a requirement of at least Python 3.11 in the pyproject.toml  by @jamescrake-merani in https://github.com/SasView/sasview/pull/3508
* Use requirements-dev.txt instead of list of dependencies by @krzywon in https://github.com/SasView/sasview/pull/3515
* Fix Invariant Test Warnings by @krzywon in https://github.com/SasView/sasview/pull/3509


**Full Changelog**: https://github.com/SasView/sasview/compare/v6.1.0...v6.1.1


New in Version 6.1.0
--------------------

This release comes with a number of new features, enhancements, and bug fixes as described below.

This version of SasView is built with Sasmodels v1.0.10, Sasdata v0.10.0, and bumps v1.0.0beta4.

New Features
^^^^^^^^^^^^
* Shape2SAS is now available as a Tool by @Qerneas in https://github.com/SasView/sasview/pull/3204
* MuMag, a polSANS analysis method is now available as a Tool by @Funkmich008 in https://github.com/SasView/sasview/pull/2825
* Poresize distribution is now available as an analysis perspective by @achicks15 in https://github.com/SasView/sasview/pull/3247
* A model reparameterization editor is now available from the fitting menu by @tsole0 in https://github.com/SasView/sasview/pull/3136

Feature Enhancements
^^^^^^^^^^^^
* P(r) analysis now allows multiple files and batch processing by @ru4en in https://github.com/SasView/sasview/pull/3137
* Fitting widget refactor by @rozyczko in https://github.com/SasView/sasview/pull/3169
* Initial implementation of the undelete mechanism for fitting tabs by @rozyczko in https://github.com/SasView/sasview/pull/3140
* Use platformdirs package for all user-related file paths by @krzywon in https://github.com/SasView/sasview/pull/3166
* Refactor bumps result views by @bmaranville in https://github.com/SasView/sasview/pull/3269
* Update model editor (rebase) by @krzywon in https://github.com/SasView/sasview/pull/3135

Bug Fixes
^^^^^^^^^^^^
* Fix LaTeX equation in corfunc docs by @llimeht in https://github.com/SasView/sasview/pull/3162
* Allow webfit to run in Django v5.0 by @summerhenson in https://github.com/SasView/sasview/pull/3200
* Bumps v1.* compatibility fixes by @krzywon in https://github.com/SasView/sasview/pull/3165 and @bmaranville in https://github.com/SasView/sasview/pull/3268
* Whats new window no longer shows previous version information by @lucas-wilkins in https://github.com/SasView/sasview/pull/3261

Infrastructure Changes
^^^^^^^^^^^^
* Bump dawidd6/action-download-artifact from 2 to 6 in /.github/workflows by @dependabot in https://github.com/SasView/sasview/pull/3151
* Renabling the Ubuntu installer test by @jamescrake-merani in https://github.com/SasView/sasview/pull/3174
* Remove Ubuntu 20.04 from CI by @jamescrake-merani in https://github.com/SasView/sasview/pull/3214
* remove need for old "six" library by @a-detiste in https://github.com/SasView/sasview/pull/3203
* Remove bumps dependence from doc build. by @pkienzle in https://github.com/SasView/sasview/pull/3195
* Fix SyntaxWarning from tex/re strings by @llimeht in https://github.com/SasView/sasview/pull/3163
* Replace tinycc with tccbox by @krzywon in https://github.com/SasView/sasview/pull/3265
* Readd macos-latest to test installer matrix. by @jamescrake-merani in https://github.com/SasView/sasview/pull/3182
* Fix nightly build issues by @krzywon in https://github.com/SasView/sasview/pull/3262
* Auto generate wheels by @llimeht in https://github.com/SasView/sasview/pull/3281

Known Issues
^^^^^^^^^
All known bugs and feature requests can be found in the issues on github.

`sasview issues <https://github.com/SasView/sasview/issues>`_ | `sasmodels issues <https://github.com/SasView/sasmodels/issues>`_ | `sasdata issues <https://github.com/SasView/sasdata/issues>`_


New in Version 6.0.1
--------------------
This is a bug fix release and the issues fixed for this release are described below.

This version of SasView is built with Sasmodels v1.0.9, Sasdata v0.9.0, and bumps v0.9.3.

General GUI Fixes
^^^^^^^^^
* Open a pop-up on start-up if a new version is available by @lucas-wilkins in https://github.com/SasView/sasview/pull/3216
* Removed superfluous signal connection causing duplicate theories by @rozyczko in https://github.com/SasView/sasview/pull/3199
* Removing data from the context menu now removes it from perspectives by @rozyczko in https://github.com/SasView/sasview/pull/3236

Plotting Fixes
^^^^^^^^^
* Fix to ensure default plot scaling matches the plot type by @krzywon in https://github.com/SasView/sasview/pull/3184
* Delete intermediate theory plots by tab id not model id. by @jamescrake-merani in https://github.com/SasView/sasview/pull/3160
* Linear fit no longer causes graph rescaling by @krzywon in https://github.com/SasView/sasview/pull/3187
* Fix for errors thrown when modifying tick labels by @jamescrake-merani in https://github.com/SasView/sasview/pull/3191

Fitting and Other Perspective Fixes
^^^^^^^^^
* Status bar message does not clear on gsc exit by @rozyczko in https://github.com/SasView/sasview/pull/3185
* Guard against bad fit results to ensure fit tabs can run new fits by @rozyczko in https://github.com/SasView/sasview/pull/3172
* A number of model editor bug fixes by @tsole0 in https://github.com/SasView/sasview/pull/2901
* Fix model documentation not showing when plugin folder is empty by @krzywon in https://github.com/SasView/sasview/pull/3237
* Added OpenCL support for the Flatpak release by @jamescrake-merani in https://github.com/flathub/org.sasview.sasview/pull/4

Other Fixes
^^^^^^^^^
* Call the system default csv viewer to allow batch fit results output for any OS by @summerhenson in https://github.com/SasView/sasview/pull/3186
* Remove a button that did nothing by @jamescrake-merani in https://github.com/SasView/sasview/pull/3217

Infrastructure Fixes
^^^^^^^^^
* Fixes to the flatpak metadata by @jamescrake-merani in https://github.com/SasView/sasview/pull/3150
* Replace the expired OSX Notarization key by @krzywon in https://github.com/SasView/sasview/pull/3183
* Include new contributors in the contributor file by @krzywon in https://github.com/SasView/sasview/pull/3192
* Fix for sasmodel doc build by @krzywon in https://github.com/SasView/sasview/pull/3212

Known Issues
^^^^^^^^^
All known bugs and feature requests can be found in the issues on github.

`sasview issues <https://github.com/SasView/sasview/issues>`_ | `sasmodels issues <https://github.com/SasView/sasmodels/issues>`_ | `sasdata issues <https://github.com/SasView/sasdata/issues>`_


New in Version 6.0.0
--------------------
This is a major release with a number of new features, enhancements, and bug fixes as described below. Many of the new
features are now highlighted in our 'What's New' window displayed when SasView starts.

This version of SasView is built with Sasmodels v1.0.8, Sasdata v0.9.0, and bumps v0.9.2.

New Features
^^^^^^^^^^^^
* Improvements to Corfunc by @lucas-wilkins in https://github.com/SasView/sasview/pull/2450
* Corfunc perspective needs export and report capabilities by @lucas-wilkins in https://github.com/SasView/sasview/pull/2065
* Allow for user adjusted relative weighting of different data sets in constrained fits by @Caddy-Jones in https://github.com/SasView/sasview/pull/1973
* Replace the custom_config.py system with a more robust configuration system by @lucas-wilkins in https://github.com/SasView/sasview/pull/2168
* Add a preferences window by @krzywon in https://github.com/SasView/sasview/pull/2167
* Debye efficiency by @klytje in https://github.com/SasView/sasview/pull/2859
* Rog and beta q by @smalex-z in https://github.com/SasView/sasview/pull/2535
* Custom fit models by @smalex-z in https://github.com/SasView/sasview/pull/2565
* Implement the orientation viewer in 5x and GL Subsystem by @lucas-wilkins in https://github.com/SasView/sasview/pull/2394
* Slicer extension by @butlerpd in https://github.com/SasView/sasview/pull/1919
* Wedge slicer by @ehewins in https://github.com/SasView/sasview/pull/2566
* Add command line interface to allow scripts to be run from sasview.exe by @pkienzle in https://github.com/SasView/sasview/pull/2280
* Documentation displayed in a SasView window by @tsole0 in https://github.com/SasView/sasview/pull/2576
* What's new dialog by @lucas-wilkins in https://github.com/SasView/sasview/pull/2608
* Flatpak release for Linux by @jamescrake-merani in https://github.com/SasView/sasview/pull/3121
* Separate MacOS releases for both Silicon and Intel architectures by @wpotrzebowski in https://github.com/SasView/sasview/pull/2917
* A new logo and welcome screen by @wpotrzebowski in https://github.com/SasView/sasview/pull/2920

Feature Enhancements
^^^^^^^^^^^^^^^^^^^^

Log Explorer Enhancements
_________________________
* Improved log explorer behaviour by @rozyczko in https://github.com/SasView/sasview/pull/2620 and @rprospero in https://github.com/SasView/sasview/pull/2639
* Drop logger level required to force log explorer to pop up from error to warning by @lucas-wilkins in https://github.com/SasView/sasview/pull/2879

Tool Enhancements
_________________
* Tool[s] menu reorganised and renamed by @lucas-wilkins in https://github.com/SasView/sasview/pull/2430
* SLD calculator tool buttons by @rozyczko in https://github.com/SasView/sasview/pull/2302
* SLD calculation allows density to be calculated from component weight fractions by @krzywon in https://github.com/SasView/sasview/pull/2986
* Update sas_gen.py to speed up data loading by @timsnow in https://github.com/SasView/sasview/pull/2617
* Read oommf v2 files by @wpotrzebowski in https://github.com/SasView/sasview/pull/2116

Plotting Enhancements
_____________________
* Allow user to choose default for plot navigation tools - merge into release_6.0.0 by @juliuskarliczek in https://github.com/SasView/sasview/pull/2849
* Two options to disable residuals and polydispersity distribution plots by @lozanodorian in https://github.com/SasView/sasview/pull/2558
* Grid lines toggle for standard Plot1D by @rozyczko in https://github.com/SasView/sasview/pull/2630
* Created submenu for slicers by @astellhorn in https://github.com/SasView/sasview/pull/2610
* Plot label customisation widget by @rozyczko in https://github.com/SasView/sasview/pull/2096
* Add persistent legend visibility toggle by @pbeaucage in https://github.com/SasView/sasview/pull/2266
* Add masked data toggle to 2D plots by @krzywon in https://github.com/SasView/sasview/pull/2368
* Add +/- 1 and 3 sigma lines on residual plots by @butlerpd in https://github.com/SasView/sasview/pull/2443
* New color map code, based on a BSD-3 licensed module by @rozyczko in https://github.com/SasView/sasview/pull/2335
* Update fitting and plotting defaults by @butlerpd in https://github.com/SasView/sasview/pull/2354

General GUI Enhancements
________________________
* initial version of modified Send To button by @rozyczko in https://github.com/SasView/sasview/pull/2613
* Add a button group to allow for proper logic of radio buttons by @rozyczko in https://github.com/SasView/sasview/pull/2848
* Quit dont ask me again by @lucas-wilkins in https://github.com/SasView/sasview/pull/2294
* Inconsistent tabbing order across the widgets by @rozyczko in https://github.com/SasView/sasview/pull/2401
* Stop making huge folder tree in user profile by @llimeht in https://github.com/SasView/sasview/pull/2262
* Call magnetic angles up_theta by @dehoni in https://github.com/SasView/sasview/pull/1971

Fitting Enhancements
____________________
* Improved/fixed category manager by @rozyczko in https://github.com/SasView/sasview/pull/2649
* Handling of constraints for polydisperse parameters by @gonzalezma in https://github.com/SasView/sasview/pull/2348

Bug Fixes
^^^^^^^^^
General GUI Fixes
_________________
* Phantom perspective windows by @krzywon in https://github.com/SasView/sasview/pull/2790
* Re-enabled "close window" option on modal dialogs by @rozyczko in https://github.com/SasView/sasview/pull/2690
* When loading data the data explorer should revert to the data tab by @juliuskarliczek in https://github.com/SasView/sasview/pull/2852
* Force main window to maximize by @rozyczko in https://github.com/SasView/sasview/pull/2273
* A few more or less obvious fixes for speed of SasView startup by @rozyczko in https://github.com/SasView/sasview/pull/2275

Plotting Fixes
______________
* Fix for broken context menus in 1d plots by @rozyczko in https://github.com/SasView/sasview/pull/2670
* Differentiate which combobox to put the graphs in. by @rozyczko in https://github.com/SasView/sasview/pull/2298
* Fit intermittent plot blanking by @pbeaucage in https://github.com/SasView/sasview/pull/2300
* Fix unusable legend size with long filenames on Mac by @pbeaucage in https://github.com/SasView/sasview/pull/2264
* Fix plot legend not updating on custom change by @rozyczko in https://github.com/SasView/sasview/pull/2362
* Close the BUMPS/DREAM results panel when data is deleted by @krzywon in https://github.com/SasView/sasview/pull/2365
* Fixed sesans residuals plots to show in real space rather than q space by @caitwolf in https://github.com/SasView/sasview/pull/2338

Fitting and Other Perspective Fixes
_____________
* Fix model date format in the user model docstring by @mrakitin in https://github.com/SasView/sasview/pull/2713
* Various Multiplicity Model Fixes by @krzywon in https://github.com/SasView/sasview/pull/2647
* Fix model save error by @krzywon in https://github.com/SasView/sasview/pull/2864
* Fix "Use dQ Data" bug that swtiched slit length and slit width in the gui by @caitwolf in https://github.com/SasView/sasview/pull/2336
* Fix copy/paste when selecting a structure factor by @krzywon in https://github.com/SasView/sasview/pull/2320
* Clip fitting values set outside the fit range by @krzywon in https://github.com/SasView/sasview/pull/2422
* Fixed breaking bug in pr_inversion by @lucas-wilkins in https://github.com/SasView/sasview/pull/2178
* Fixes in invariant prespective by @wpotrzebowski in https://github.com/SasView/sasview/pull/2357
* Fixes binning bug in implementation of sesans data by @caitwolf in https://github.com/SasView/sasview/pull/2331
* Fix confusing slit resolution parameters and add guardrails by @pbeaucage in https://github.com/SasView/sasview/pull/2283

Other Fixes
___________
* Cherry-picked new_numpy_behaviour by @wpotrzebowski in https://github.com/SasView/sasview/pull/2655
* Fit report save fix by @rozyczko in https://github.com/SasView/sasview/pull/2684
* Fix for empty save format for grid files by @rozyczko in https://github.com/SasView/sasview/pull/2683
* The installer warns the user if the chosen installation directory is already populated by @krzywon in https://github.com/SasView/sasview/pull/3042

Documentation Changes
^^^^^^^^^^^^^^^^^^^^^
* Update preferences documentation by @krzywon in https://github.com/SasView/sasview/pull/2680
* Include SasData documentation in SasView by @krzywon in https://github.com/SasView/sasview/pull/2672
* Corfunc Docs by @lucas-wilkins in https://github.com/SasView/sasview/pull/2823
* Docstrings in perspective.py by @lucas-wilkins in https://github.com/SasView/sasview/pull/2207
* Update Optimizer Help Doc by @smk78 in https://github.com/SasView/sasview/pull/2359
* Update of the sld calculator documentation by @katieweigandt in https://github.com/SasView/sasview/pull/2785
* Update rst strings to fix doc build warnings by @smk78 in https://github.com/SasView/sasview/pull/2288

Infrastructure Changes
^^^^^^^^^^^^^^^^^^^^^^

Build System
____________
* Rework CI to be non-repetitive, simpler, test more things by @llimeht in https://github.com/SasView/sasview/pull/2263
* Stop existing concurrent CI by @krzywon in https://github.com/SasView/sasview/pull/2638
* Release 6.0.0 notarization fix by @wpotrzebowski in https://github.com/SasView/sasview/pull/2709
* Fixes problem with using deprecated node.js by @butlerpd in https://github.com/SasView/sasview/pull/2836
* Run unit tests of Qt GUI and have CI gate on them by @llimeht in https://github.com/SasView/sasview/pull/2252
* Remove ubuntu 18.04 from CI by @krzywon in https://github.com/SasView/sasview/pull/2439

Python Dependencies
___________________
* Added python 3.11 support, removed 3.8 by @rozyczko in https://github.com/SasView/sasview/pull/2582
* Warnings removals and python 3.9 drop in tests by @wpotrzebowski in https://github.com/SasView/sasview/pull/2860
* Change GUI package from PyQt5 to Pyside6 by @rozyczko in https://github.com/SasView/sasview/pull/2478
* Pyinstaller 6 by @krzywon in https://github.com/SasView/sasview/pull/2854
* Cleanup of requirements.txt by @krzywon in https://github.com/SasView/sasview/pull/2856
* Remove imp module by @krzywon in https://github.com/SasView/sasview/pull/2809
* Remove pyopengl_accelerate from requirements.txt by @wpotrzebowski in https://github.com/SasView/sasview/pull/2865

Developer Enhancements
______________________
* Add argument to convertUI that forces full UI rebuild by @krzywon in https://github.com/SasView/sasview/pull/2483
* Run.py: Prioritize sibling modules over installed modules by @krzywon in https://github.com/SasView/sasview/pull/2772
* Use sasdata package in place of sas.sascalc.dataloader by @krzywon in https://github.com/SasView/sasview/pull/2141
* Clean up sas.sasview by @lucas-wilkins in https://github.com/SasView/sasview/pull/2154, https://github.com/SasView/sasview/pull/2159, and https://github.com/SasView/sasview/pull/2161

New Models
^^^^^^^^^^
One new model has been added to SasView since v5.0.6 was released:

* [micromagnetic_FF_3D](https://marketplace.sasview.org/models/140/) SANS of bulk ferromagnets by @stellhorn in https://github.com/SasView/sasmodels/pull/592

The following models have been added to the `[Model Marketplace] <https://marketplace.sasview.org/>`_ since v5.0.6 was released:

* [Superball](https://marketplace.sasview.org/models/154/)
* [core_multi_shell_cylinder](https://marketplace.sasview.org/models/155/)
* [fuzzy_sphere_extended](https://marketplace.sasview.org/models/156/)
* [Spherical Micelle](https://marketplace.sasview.org/models/157/)
* [Cylindrical Micelle](https://marketplace.sasview.org/models/158/)
* [Long Cylindrical Micelle](https://marketplace.sasview.org/models/159/)
* [Enhanced Cylinder Models for SasView](https://marketplace.sasview.org/models/161/)
* [Enhanced Ellipsoid Models for SasView](https://marketplace.sasview.org/models/163/)
* [Supercylinder](https://marketplace.sasview.org/models/164/)

Known Issues
^^^^^^^^^^^^
All the known bugs/feature requests can be found in the issues on github.
Note the sasmodels issues are now separate from the sasview issues (i.e. different repositories)

`[sasview] <https://github.com/SasView/sasview/milestones>`_

`[sasmodels] <https://github.com/SasView/sasmodels/milestones>`_


New in Version 5.0.6
--------------------
This is a point release which fixes a number of issues reported in earlier versions
of 5.0.x. Of particular note, the failure of the program to start when installing on
a new system due to issues finding the config file has been fixed. The speed with
which the program starts up has also been improved. The paracrystalline models, which
have been labelled as "under review" since 2018, have been checked and corrected (bcc
and fcc) and the documentation completely reworked (bcc, fcc, and sc).  Elsewhere,
plots now properly support custom data names in the legend, the LM optimizer failing
to run on GPUs or when the starting value of a parameter is outside the min/max range
has been fixed, a problem with the intermittent blanking of plots has also been fixed,
a number of defaults have been changed to be more reasonable, and a number of other
issues in the documentation have been corrected and/or updated.

This version of SasView is built with Sasmodels 1.0.7 and Bumps master.

Pull Request Changes
^^^^^^^^^^^^^^^^^^^^
* Fix error being thrown when the initial guess it outside the min/max range for the LM optimizer @krzywon `[#2422] <https://github.com/SasView/sasview/pull/2422/>`_
* Fix for failure to find custom_config preventing sasview from starting @krzywon `[#2407] <https://github.com/SasView/sasview/pull/2407/>`_
* Cleanup (close) the bumps/DREAM results panel when associate data is removed from sasview @krzywon `[#2365] <https://github.com/SasView/sasview/pull/2365/>`_
* Fix plot legend not updating on custom change @rozyczko `[#2362] <https://github.com/SasView/sasview/pull/2362/>`_
* Add more informative error message to invariant calculator @wpotrzebowski `[#2357] <https://github.com/SasView/sasview/pull/2357/>`_
* Provide more reasonable defaults (number of points in curves, log vs linear scale, residuals don't have error bars) @butlerpd `[#2354] <https://github.com/SasView/sasview/pull/2354/>`_
* Make sesans residual plots show in real space rather than q space @caitwolf `[#2338] <https://github.com/SasView/sasview/pull/2338/>`_
* Fix rare bug that switches slit width and length in the gui @caitwolf `[#2336] <https://github.com/SasView/sasview/pull/2336>`_
* Fix binning bug in implementation of sesans @caitwolf `[#2331] <https://github.com/SasView/sasview/pull/2331/>`_
* Fix problem of a second plot showing up when loading certain data files @pbeaucage `[#2329] <https://github.com/SasView/sasview/pull/2329>`_
* Fix to chaging parameters in FitPage not updating plots. Was most obvious for sesans. @caitwolf `[#2318] <https://github.com/SasView/sasview/pull/2318/>`_
* Fix problem with SlD calculator tool buttons sometimes being squashed hiding the button label @rozyczko `[#2302] <https://github.com/SasView/sasview/pull/2302>`_
* Fix problem with intermittent plot blanking @pbeaucage `[#2300] <https://github.com/SasView/sasview/pull/2300/>`_
* Fix problem with appending graphs when using theory data @rozyczko `[#2298] <https://github.com/SasView/sasview/pull/2298/>`_
* Properly support custom names in plot legend @pbeaucage `[#2293] <https://github.com/SasView/sasview/pull/2293/>`_
* Tweaks to improve startup speed @rozyczko `[#2275] <https://github.com/SasView/sasview/pull/2275/>`_
* Fix problem with losing minimize/restore/close buttons when maximizing fit window @rozyczko `[#2273] <https://github.com/SasView/sasview/pull/2273/>`_
* Add persistent legend visibility toggle @pbeaucage `[#2266] <https://github.com/SasView/sasview/pull/2266/>`_
* Fix label rendering problems due to incorrect escape sequences @llimeht `[#2217] <https://github.com/SasView/sasview/pull/2217/>`_
* Fix update to numpy verion breaking P(R) analysis @lucas-wilkins `[#2178] <https://github.com/SasView/sasview/pull/2178/>`_
* Fix problem with use of Data Operation Tool preventing project saving @rozyczko `[#2099] <https://github.com/SasView/sasview/pull/2099/>`_
* Correct paracrystal model error and rework documentation @butlerpd `[#545] <https://github.com/SasView/sasmodels/pull/545>`_
* Fix rare race condition causing errors @bmaranville `[#537] <https://github.com/SasView/sasmodels/pull/537/>`_
* Fix to allow multiple scattering script to run @wpotrzebowski `[#521] <https://github.com/SasView/sasmodels/pull/521/>`_
* Fix error in core shell Ellipsoid documentation @pkienzle `[#512] <https://github.com/SasView/sasmodels/pull/512/>`_
* Fix models with complex amplitudes not compiling on the fly @pkienzle `[#511] <https://github.com/SasView/sasmodels/pull/511/>`_
* Fix problem with LM optimizer failing when GPUs are turned on by updating to the latest bumps version `[issue #518] <https://github.com/SasView/sasmodels/issues/518/>`_

Documentation Changes
^^^^^^^^^^^^^^^^^^^^^
* Update optimizer help documentation @smk78 `[#2359] <https://github.com/SasView/sasview/pull/2359/>`_
* Update contributor list @wpotrzebowski `[#2114] <https://github.com/SasView/sasview/pull/2114>`_
* Update web links from http to https @smk78 `[#2087] <https://github.com/SasView/sasview/pull/2087/>`_ and `[#2265] <https://github.com/SasView/sasview/pull/2265/>`_
* Update corfunc documentation @lucas-wilkins `[#2047] <https://github.com/SasView/sasview/pull/2047/>`_
* Update gel_fit model documentation and fix formating @smk78 `[#541] <https://github.com/SasView/sasmodels/pull/541/>`_
* Correct and update cylinder model documentation @butlerpd `[#539] <https://github.com/SasView/sasmodels/pull/539>`_
* Restructuring and cross-linking of sasmodels docs @smk78 `[#534] <https://github.com/SasView/sasmodels/pull/534/>`_
* Update marketplace url to https @smk78 `[#522] <https://github.com/SasView/sasmodels/pull/522/>`_

Build System Changes
^^^^^^^^^^^^^^^^^^^^
* Fix Sphinx some of the warnings during build process @smk78 `[#2288] <https://github.com/SasView/sasview/pull/2288/>`_

New Models
^^^^^^^^^^
The following models have been added to the `[Model Marketplace] <https://marketplace.sasview.org/>`_ since v5.0.5 was released:

* Pringle-Schmidt Helices (documentation update)
* Lamellar Slab Partition Constant

Known Issues
^^^^^^^^^^^^
All the known bugs/feature requests can be found in the issues on github.
Note the sasmodels issues are now separate from the sasview issues (i.e. different repositories)

`[sasview] <https://github.com/SasView/sasview/milestones>`_

`[sasmodels] <https://github.com/SasView/sasmodels/milestones>`_


New in Version 5.0.5
--------------------
This is a point release which fixes some issues reported in earlier versions
of 5.0.x. A few highlights are:

* The long standing issue with the Levenberg-Marquardt optimiser not respecting
  parameter bounds has been resolved by the move to a later version of
  the Bumps package.
* A bug which prevented the radius_effective parameter from being updated
  in $P(Q)*S(Q)$ models when the data were resolution smeared has been fixed.
* A bug that prevented the formation of composite mixture models with multiplicity
  (for example, models such as core_multi_shell*hardsphere + cylinder or
  core_multi_shell\@hardsphere + cylinder) has been fixed.
* The button to reset the selected Q-limits for fitting now works again!
* There has been a technical change to the point in the calculation at which the
  volume normalisation of $P(Q)*S(Q)$ models is applied by the move to a later
  version of the Sasmodels package. This change was actually incorporated into
  v5.0.4 but due to an oversight was omitted from the release notes at the time,
  although a note was added to the web version after the release (and has been
  subsequently added below). In most instances this change will go un-noticed
  unless you happen to be plotting the individual contributions of $P(Q)$ or
  $S(Q)$ and comparing them with similar calculations performed in versions of
  SasView before v5.0.4, at which point the scaling of the functions will be
  seen to be different.

There are also some **new features** in this version. Most notably:

* The Generic Scattering Calculator Tool has been overhauled and its
  capabilities significantly expanded. In particular, it will now perform
  magnetic/polarised SANS computations. As part of this upgrade, coordinate data
  in some VTK formats are now also supported.
* The data loaders have also been improved. SasView will now read CanSAS1D XML
  data files with multiple <SASdata> blocks in a single <SASentry>. And, by
  popular demand, 1D data can now be saved in CSV format. SESANS data files
  with the extension .sesans are now also recognised.
* A Boucher-type interfacial profile function has been added to the spherical_sld model.

This version of SasView is built with Sasmodels 1.0.6 and Bumps 0.9.0.

Pull Request Changes
^^^^^^^^^^^^^^^^^^^^
* Add CSV Writer and Allow freeform file extensions by @krzywon in `[#1793] <https://github.com/SasView/sasview/pull/1793>`_
* Ticket 1804: Remove redundant checks so dx==0 is allowed by @krzywon in `[#1807] <https://github.com/SasView/sasview/pull/1807>`_
* Implement 3d polarisation in SasView by @dehoni in `[1714] <https://github.com/SasView/sasview/pull/1714>`_
* Implement 3d polarisation in Sasmodels by @dehoni in `[#437] <https://github.com/SasView/sasmodels/pull/437>`_
* Limit adding [n] to name on data load and name change by @krzywon in `[#1790] <https://github.com/SasView/sasview/pull/1790>`_
* Various P(r) GUI Fixes by @krzywon in `[#1799] <https://github.com/SasView/sasview/pull/1799>`_
* Image Viewer bug fix by @rozyczko in `[#1871] <https://github.com/SasView/sasview/pull/1871>`_
* Optimizer parameters checked against UI fields #1867 by @rozyczko in `[#1873] <https://github.com/SasView/sasview/pull/1873>`_
* Syntax checker in the model editor. by @rozyczko in `[#1875] <https://github.com/SasView/sasview/pull/1875>`_
* Attempt to address file load widget sluggishness issue. #1866 by @rozyczko in `[#1876] <https://github.com/SasView/sasview/pull/1876>`_
* Data import/export syntax fixes by @krzywon in `[#1877] <https://github.com/SasView/sasview/pull/1877>`_
* Add Compute Button and Limit Fitting Computations by @krzywon in `[#1798] <https://github.com/SasView/sasview/pull/1798>`_
* Minor change to sas_gen.py which should fix #1886 by @rjbourne in `[#1887] <https://github.com/SasView/sasview/pull/1887>`_
* canSAS XML Reader: Load multiple SASdata in a single SASentry by @krzywon in `[#1890] <https://github.com/SasView/sasview/pull/1890>`_
* Ticket 1406: cancel calculation by @rjbourne in `[#1892] <https://github.com/SasView/sasview/pull/1892>`_
* Uncertainties for constrained parameters by @m2cci-NMZ in `[#1682] <https://github.com/SasView/sasview/pull/1682>`_
* Undoing changes from PR #1682 by @Caddy-Jones in `[#1915] <https://github.com/SasView/sasview/pull/1915>`_
* Ticket 1861: Adding the SasView version number by @Caddy-Jones in `[#1893] <https://github.com/SasView/sasview/pull/1893>`_
* Improved add/multiply editor by @rozyczko in `[#1901] <https://github.com/SasView/sasview/pull/1901>`_
* Ticket 1825: scattering calculator enhancements by @rjbourne in `[#1888] <https://github.com/SasView/sasview/pull/1888>`_
* python console fix by @rozyczko in `[#1913] <https://github.com/SasView/sasview/pull/1913>`_
* Ticket 1728: Finishing the Q-Range Sliders by @krzywon in `[#1891] <https://github.com/SasView/sasview/pull/1891>`_
* Using the uncertainties module to propagate errors by @Caddy-Jones in `[#1916] <https://github.com/SasView/sasview/pull/1916>`_
* Distinguish standard model list from full list with plugin models. #1906 by @rozyczko in `[#1907] <https://github.com/SasView/sasview/pull/1907>`_
* Fix Color Map Slider in 2D plots by @dehoni in `[#1929] <https://github.com/SasView/sasview/pull/1929>`_
* Re-create toc entry for sesans_fitting in sasview by @smk78 in `[#1945] <https://github.com/SasView/sasview/pull/1945>`_
* Fixes missing plugin models from structure factor combo box by @caitwolf in `[#1860] <https://github.com/SasView/sasview/pull/1860>`_
* Ticket 1882: Enhance functionality of coordinate systems by @rjbourne in `[#1899] <https://github.com/SasView/sasview/pull/1899>`_
* File loader enhancement of the General Scattering Calculator by @dehoni in `[#1930] <https://github.com/SasView/sasview/pull/1930>`_
* Q-Range slider fix for linear fits by @krzywon in `[#1943] <https://github.com/SasView/sasview/pull/1943>`_
* Fixes to invariant plot high q extrapolation by @phgilbert in `[#1859] <https://github.com/SasView/sasview/pull/1859>`_
* Add .sesans extension to associations.py by @krzywon in `[#1942] <https://github.com/SasView/sasview/pull/1942>`_
* Fix for loader modules not found error by @krzywon in `[#1962] <https://github.com/SasView/sasview/pull/1962>`_
* Remove global variable LOADED_PERSPECTIVES by @krzywon in `[#1984] <https://github.com/SasView/sasview/pull/1984>`_
* Ticket 1814: Allow Q-range reset by @krzywon in `[#1884] <https://github.com/SasView/sasview/pull/1884>`_
* Allow output of scattering calculator to be used as a theory curve by @rjbourne in `[#1912] <https://github.com/SasView/sasview/pull/1912>`_
* Ticket 1820: Enable legacy VTK files in scattering calculator by @rjbourne in `[#1898] <https://github.com/SasView/sasview/pull/1898>`_
* Fix handedness of magnetic structures in mag SLD by @dehoni in `[#1976] <https://github.com/SasView/sasview/pull/1976>`_
* Fixing high CPU consumption on MacOSX by @wpotrzebowski in `[#2005] <https://github.com/SasView/sasview/pull/2005>`_
* Added a simple check so cancelling the dialog doesn't throw an error #1551 by @rozyczko in `[#2014] <https://github.com/SasView/sasview/pull/2014>`_
* Add check for custom structure factors by @rozyczko in `[#2006] <https://github.com/SasView/sasview/pull/2006>`_
* Enable model update on adding new plugin. #1597 by @rozyczko in `[#2013] <https://github.com/SasView/sasview/pull/2013>`_
* Save project: Properly handle scalars by @krzywon in `[#1994] <https://github.com/SasView/sasview/pull/1994>`_
* Change default options on file load widget to not display dir icons by @rozyczko in `[#2015] <https://github.com/SasView/sasview/pull/2015>`_
* radius_effective update for smeared data by @rozyczko in `[#2024] <https://github.com/SasView/sasview/pull/2024>`_
* Don't show RPA in the list of models #2022 by @rozyczko in `[#2025] <https://github.com/SasView/sasview/pull/2025>`_
* Allow composite mixtures with multiplicity #468 by @pkienzle in `[#472] <https://github.com/SasView/sasmodels/pull/472>`_
* FIX: turned magic constants to named magic constants. Refs #468 by @pkienzle in `[#470] <https://github.com/SasView/sasmodels/pull/470>`_
* Spherical boucher model cherry pick by @dehoni in `[#476] <https://github.com/SasView/sasmodels/pull/476>`_
* Pre release fixes by @wpotrzebowski in `[#2028] <https://github.com/SasView/sasview/pull/2028>`_
* Use MPFit fitter as the default fit engine by @krzywon in `[#2037] <https://github.com/SasView/sasview/pull/2037>`_

Documentation Changes
^^^^^^^^^^^^^^^^^^^^^
* Scattering calculator docs by @dehoni in `[#1974] <https://github.com/SasView/sasview/pull/1974>`_
* Doc Update: P Scaling by @smk78 in `[#1956] <https://github.com/SasView/sasview/pull/1956>`_
* Eliminate old tutorial from SasView 5x by @smk78 in `[#1949] <https://github.com/SasView/sasview/pull/1949>`_
* Doc Update: Polydispersity by @smk78 in `[#1938] <https://github.com/SasView/sasview/pull/1938>`_
* Doc Update: Formats by @smk78 in `[#1933] <https://github.com/SasView/sasview/pull/1933>`_
* Doc Update: SESANS in SasView by @smk78 in `[#1931] <https://github.com/SasView/sasview/pull/1931>`_
* Doc building fixes by @llimeht in `[#1744] <https://github.com/SasView/sasview/pull/1744>`_
* Doc Update: P Scaling in Sasmodels by @smk78 in `[#487] <https://github.com/SasView/sasmodels/pull/487>`_
* Doc Update: Polydispersity in sasmodels by smk78 in `[#484] <https://github.com/SasView/sasmodels/pull/484>`_
* Doc Update Formats in Sasmodels by @smk78 in `[#479] <https://github.com/SasView/sasmodels/pull/479>`_
* Doc Update: SESANS in Sasmodels by @smk78 in `[#477] <https://github.com/SasView/sasmodels/pull/477>`_
* DOC: remove sphinx warnings by @pkienzle in `[#462] <https://github.com/SasView/sasmodels/pull/462>`_
* Latex typos in fitting_sq.rst by @pkienzle in `[#456] <https://github.com/SasView/sasmodels/pull/456>`_
* Typo in fitting_sq.rst by @pkienzle in `[#455] <https://github.com/SasView/sasmodels/pull/455>`_
* Miscellaneous typo fixes in models by llimeht in `[#438] <https://github.com/SasView/sasmodels/pull/438>`_

Build System Changes
^^^^^^^^^^^^^^^^^^^^
* Try to run tests everywhere rather than fast-fail by @llimeht in `[#1771] <https://github.com/SasView/sasview/pull/1771>`_
* TST: Lxml dependencies by @wpotrzebowski in `[#1815] <https://github.com/SasView/sasview/pull/1815>`_
* Build installer for windows using GitHub actions by @llimeht in `[#1747] <https://github.com/SasView/sasview/pull/1747>`_
* Release 5.0.4 by @wpotrzebowski in `[#1829] <https://github.com/SasView/sasview/pull/1829>`_
* Adding pip dependency to yml file so that conda doesn't complain by @wpotrzebowski in `[#1853] <https://github.com/SasView/sasview/pull/1853>`_
* Updated file for parity with the yml used in build process by @rozyczko in `[#1854] <https://github.com/SasView/sasview/pull/1854>`_
* Add py3.9 remove py3.6 from github actions by @llimeht in `[#1856] <https://github.com/SasView/sasview/pull/1856>`_
* Update h5py version for all operating systems by @krzywon in `[#1849] <https://github.com/SasView/sasview/pull/1849>`_
* Adding h5py=3.1 as a pip package by @wpotrzebowski in `[#1880] <https://github.com/SasView/sasview/pull/1880>`_
* CI: use pip --cache to find dir by @andyfaff in `[#1926] <https://github.com/SasView/sasview/pull/1926>`_
* Github actions for OSX build by @wpotrzebowski in `[#1927] <https://github.com/SasView/sasview/pull/1927>`_
* Fixing syntax in release.yml by @wpotrzebowski in `[#1946] <https://github.com/SasView/sasview/pull/1946>`_
* Use version parsing package for MPL version check by @krzywon in `[#1947] <https://github.com/SasView/sasview/pull/1947>`_
* Fix for removed _activeQue in newer Matplotlib by @bmaranville in `[#1951] <https://github.com/SasView/sasview/pull/1951>`_
* Gh actions artifacts by @wpotrzebowski in `[#1969] <https://github.com/SasView/sasview/pull/1969>`_
* Update to version 5.0.5b1 by @butlerpd in `[#1970] <https://github.com/SasView/sasview/pull/1970>`_
* Increment the installation directory number to 5.0.5 by @krzywon in `[#1983] <https://github.com/SasView/sasview/pull/1983>`_
* Update of the github workflows by @wpotrzebowski in `[#1985] <https://github.com/SasView/sasview/pull/1985>`_
* GitHub: Freezing MPL to 2.2.5 on windows by @rozyczko in `[#1989] <https://github.com/SasView/sasview/pull/1989>`_
* Switching to PyQT 5.13  by @wpotrzebowski in `[#2021] <https://github.com/SasView/sasview/pull/2021>`_

The full sasview and sasmodels changelogs, respectively, are available at:

* https://github.com/SasView/sasview/compare/v5.0.4...v5.0.5
* https://github.com/SasView/sasmodels/compare/v1.0.5...v1.0.6

New Models
^^^^^^^^^^
The following models have been added to the `[Model Marketplace] <https://marketplace.sasview.org/>`_ since v5.0.4 was released:

* Magnetic Whirl
* Maier-Saupe distribution
* Cyclic Gaussian distribution
* Superball Model - Neither Sphere nor Cube
* OrientedMagneticChains

Known Issues
^^^^^^^^^^^^
The ‘rpa’ (Random Phase Approximation, for polymer scattering) model has been
temporarily withdrawn. Some gremlins had crept into how the model parameters
interacted with the Fit Page which meant you were not performing the calculation
you thought you were. This is being investigated. Should you need it, a separate
binary blend model (the most performed calculation) is available from the
`[Model Marketplace] <https://marketplace.sasview.org/>`_ .

All the known bugs/feature requests can be found in the issues on github.
Note the sasmodels issues are now separate from the sasview issues (i.e. different repositories)

`[sasview] <https://github.com/SasView/sasview/milestones>`_

`[sasmodels] <https://github.com/SasView/sasmodels/milestones>`_


New in Version 5.0.4
--------------------
This is a point release which fixes some issues reported in earlier versions
of 5.0.x:

* A bug that had been around since 4.2.2 and which prevented Batch Fitting from
  using any dI values in the data file has finally been fixed. The consequence of
  this bug was that Single Fits and Batch Fits on the same datasets could return
  different parameters. Now, where present, dI values will always be used by default
  in both cases.
* The bug introduced in 5.0.3 which prevented the plotting of Batch Fit results has also
  been fixed.
* An issue with the behaviour of the 1D pinhole resolution smearing routine in cases of
  large divergence has been addressed.
* A number of improvements have been made to plotting and plot management.
* Several usability issues in the P(r) Inversion and Invariant Analysis perspectives
  have been addressed.
* Improvements have also been made to the functioning of Project Save/Load.

There are also some new features in this version:

* Though not strictly a new feature, the functionality and operation of parameter
  constraints has been significantly overhauled for this version.
* The slicer functionality has been significantly overhauled and made to work properly.
* The slider bars on plots for selecting the q-range for fitting that featured in earlier
  versions of SasView have been re-introduced by popular request, although they do not
  yet work on linearized plots.
* It is now possible to swap the dataset used to create an existing FitPage for a different
  dataset. This removes the need to re-generate a complex model (eg, featuring many parameters
  and/or constraints) many times over to use it to fit several datasets.
* It is now also possible to assign custom names to loaded datasets, rather than just
  identifying the data by its filename. Right-click on a dataset in the Data Explorer
  to activate.

There has also been a technical change in this version to how the volume
normalisation is incorporated in the interaction calculator that computes $I(Q)$
from $P(Q) S(Q)$. The change was made in Sasmodels 1.0.5 with which this version
is built and will affect all future versions of SasView. Prior to the change
the scaling of the $P(Q)$ function that might appear in the *Data Explorer* was
incorrect. This was easily seen if $P(Q)$ and $I(Q)$ were plotted together but
had apparently escaped notice for some time. But this does, of course, mean that 
comparisons of the $P(Q)$ contributions to models between this version of SasView
and previous versions will differ. Further details of the change can be found
`here <https://github.com/SasView/sasview/issues/1698>`_.

New features/improvements
^^^^^^^^^^^^^^^^^^^^^^^^^
* sasview #1725: Horizontal line at y=0 needed in P(r) plots
* sasview #1702: Allow for a choice of how data is named in the Data Explorer
* sasview #1699: Allow check/uncheck of sub-selected data in Data Explorer
* sasview #1676: Checkbox of highlighted row is checked also when clicking another checkbox
* sasview #1303: CanSAS XML Reader refactor

* sasmodels #443: Update to polydispersity.rst
* sasmodels #429: Create model for superparamagnetic relaxing particles
* sasmodels #390: Re-describe Source intensity in model parameter tables
* sasmodels #253: use new orientation for magnetic models (Trac #910)

Bug fixes
^^^^^^^^^
* Fixes sasview #1796: Batch Fitting does not respect Q-range for fitting 
* Fixes sasview #1795: Display of batch fitting results is broken in 5.0.4
* Fixes sasview #1794: Batch fitting in 5.x returns different parameters to single fits in 5.x
* Fixes sasview #1782: RgQmax and RgQmin are inverted in the Gunier linear fit
* Fixes sasview #1776: Slicers Using Masked Data Points in Calculation
* Fixes sasview #1754: Delete Data does not remove data or plots from Fitting, P(r) or Inversion
* Fixes sasview #1738: Conflicting definition of displayData()
* Fixes sasview #1711: sasview 5, Q resolution smearing issues with broad_peak model
* Fixes sasview #1710: sasview fails to open .h5 files using h5py 3.1
* Fixes sasview #1701: Issue with slashes in data titles in CanSAS1D (and probably NXcanSAS)
* Fixes sasview #1698: Provide P(Q) separately when fitting
* Fixes sasview #1696: Failure in getSymbolDict on selecting parameters for constraints
* Fixes sasview #1681: Generic Scattering Calculator produces empty 2D map on sld file
* Fixes sasview #1674: Reloading a project in the same session duplicates the model/residuals in the Data Explorer
* Fixes sasview #1671: pdh data loader bug in 4.x and ESS_GUI 5.x
* Fixes sasview #1657: Loading project without fit_params entry causes empty fit window (v5.0.3)
* Fixes sasview #1655: Corfunc and Invariant Perspectives not able to remove/swap data (5.x)
* Fixes sasview #1654: 5.0.4 disable rather than remove constraints if do a fit on a single FitPage
* Fixes sasview #1653: 5.0.4 new constraints checks over zealous on load project
* Fixes sasview #1649: 4.x/5.x: Slicer Parameters control only appears in context menu once you have sliced
* Fixes sasview #1648: 5.0.3 not updating radius_effective in GUI
* Fixes sasview #1647: 4.x/5.x: Sector slicer tool Q plot could do with better resolution
* Fixes sasview #1646: 4.x/5.x: Annulus slicer tool phi plot could do with better resolution
* Fixes sasview #1640: Linux: SasView >5.0.1 binary cannot copy default custom_config.py
* Fixes sasview #1616: ESS_GUI: Model label on plot keeps being reset
* Fixes sasview #1611: Inconsistent behaviour of extrapolation Fit/Fix radio buttons in Invariant Perspective
* Fixes sasview #1610: Chart in Invariant Perspective Status Dialog not displaying the low-Q contribution to Q*
* Fixes sasview #1609: Changing Q-range limits in Invariant Perspective has no effect on extrapolations
* Fixes sasview #1608: No Q-limit bars in Invariant Perspective
* Fixes sasview #1607: Once extrapolation is turned on in the invariant it cannot be turned off
* Fixes sasview #1606: Invariant does not report the total invariant
* Fixes sasview #1605: Problem loading canSAS data into Invariant
* Fixes sasview #1604: The Invariant low Q extrapolation choice is not honored
* Fixes sasview #1600: v5 constrained value within single FitPage not being returned to gui
* Fixes sasview #1589: 5.0 turn off or remove constraint ?
* Fixes sasview #1583: calc.py throws erros after building SasView
* Fixes sasview #1574: Invariant perspective fixes need to be ported to 5.x
* Fixes sasview #1566: Default Checkboxes in data manager need changing
* Fixes sasview #1557: GUI losing track of fitpage and plot associations
* Fixes sasview #1547: Resolution is incorrectly handled in 5.x
* Fixes sasview #1544: Need to examine 2D data pixel sizes
* Fixes sasview #1542: Crosstalk between Corfunc and Invariant perspectives
* Fixes sasview #1541: Invariant and the infinite multiplication of plots
* Fixes sasview #1539: Corfunc requires two shots to populate the data name box
* Fixes sasview #1537: Allow for replacing data in a Fit Page
* Fixes sasview #1535: ESS_GUI: Existing common parameters not preserved between models in 5.x
* Fixes sasview #1534: ESS_GUI: Something strange with 5.x and the .sasview folder
* Fixes sasview #1532: Add a constraint checking mechanism
* Fixes sasview #1526: Project Save/Load functionality of 4.x needs to be restored
* Fixes sasview #1478: v5 & v4 TEst that P(Q)S(Q) plugin works
* Fixes sasview #1472: Sort out the Invariant Perspective & Documentation (#1434 & #1461)
* Fixes sasview #1469: 2D tools
* Fixes sasview #1453: 5.1 gui initialisation issue for Onion model
* Fixes sasview #1446: 5.0 dI uncertainty unavailable in batch mode
* Fixes sasview #1408: Magnetic model documentation is inconsistent with code
* Fixes sasview #1381: Slicer in 5.0 doesn't contain the batch, fitting, log/linear etc features
* Fixes sasview #1340: 5.0 invariant mac not plotting
* Fixes sasview #1243: Display title rather than filename in data browser (Trac #1213)
* Fixes sasview #1137: Verify and document up_frac_i and up_frac_f calculations for magnetic models (Trac #1086)
* Fixes sasview #863:  Make it easier to use the same fit set-up with different data sets (Trac #747)

* Fixes sasmodels #367: Correlation length model documentation is wrong
* Fixes sasmodels #210: Show all failing tests rather than stopping at the first

New Models
^^^^^^^^^^
The following models have been added to the `[Model Marketplace] <https://marketplace.sasview.org/>`_ since v5.0.0 was released:

* Magnetic vortex in a disc
* Field-dependent magnetic SANS of misaligned magnetic moments in bulk ferromagnets
* SANS of bulk ferromagnets
* Core_shell_ellipsoid_tied and core_shell_ellipsoid_repar
* Lamellar_Slab_APL_nW
* 5 Layer Core Shell Disc
* Superparamagnetic Core-Shell Spheres with 3D field orientation
* Superparamagnetic Core-Shell Spheres
* Octahedron
* Magnetically oriented, rotating and precessing anisometric particle (MORP)
* Cumulants
* Cumulants DLS
* Peak Voigt
* Long Cylinder
* Sphere Concentration A
* Binary Blend
* Exponential
* 2 Layer General Guinier Porod
* Core double shell sphere filled with many cylinders in the core
* Fractal S(q)
* Mass Fractal S(q)
* Core shell cuboid
* Core shell sphere filled with a cylinder in the core
* Correlated_spheres

Known Issues
^^^^^^^^^^^^
It has come to our attention that some Mac users get a dialogue box
saying *“SasView5.app”* is damaged and can’t be opened. You should move
it to the Trash when they try and install 5.0.4. This seems to affect
machines running MacOS earlier than 10.15. However, we have found that
it is possible to install SasView on 10.13, for example, by clearing
the extended attributes on the package by executing the command:
xattr -cr /Applications/SasView5.app

At this time, the reinstated slider bars on plots for selecting the
q-range for fitting do not work on linearized plots.

The button for resetting the Q-range for fitting to the data limits
(FitPage > Fit Options > Fitting Range) is also not working.

All the known bugs/feature requests can be found in the issues on github.
Note the sasmodels issues are now separate from the sasview issues (i.e. different repositories)

`[sasview] <https://github.com/SasView/sasview/milestones>`_

`[sasmodels] <https://github.com/SasView/sasmodels/milestones>`_


New in Version 5.0.3
--------------------
This is a point release which fixes several issues, but in particular:

* a serious bug in the resolution smearing interface which was applying
  a single value of $dq/q$ to all data points even if $dq/q$ was provided in
  the data file;
* a very long-standing bug in the Invariant Analysis interface which was
  computing specific surface ($Sv$) values that were *twice* what they should
  have been (The opportunity has also been taken to completely overhaul the
  documentation for the Invariant Analysis at the same time);
* inconsistent and incorrect behaviour of the 'is fittable' checkbox
  for polydispersities which could lead to unrealistic PD values being
  returned during fitting.

New features/improvements
^^^^^^^^^^^^^^^^^^^^^^^^^
* sasview # 1622: RC1 problems with installation/running on Windows
* sasview # 1565: (ESS_GUI) Report dialog enhancements
* sasview # 1564: Enhancements to Report Results
* sasview # 1552: Enable mpl toolbar
  
There are also several usability improvements, including better handling of
constraints between datasets for simultaneous fits, and control over plots.

With this release Windows users are no longer guided to install SasView
to C:\Program Files. This had started to become an issue as some IT providers
tightened their security settings, particularly under Windows 10, either
causing installation to fail (unless the user could elevate permissions), or
prevent SasView starting ('failed to execute script sasview'). The installation
process now prompts for the type of installation required, and defaults to
C:\SasView-x.x.x

Bug fixes
^^^^^^^^^
* Fixes sasview  # 1632: ESS_GUI Documentation: How to test a plugin model needs updating
* Fixes sasview  # 1623: 5.0.3 RC1 crashing during fitting
* Fixes sasview  # 1606: Invariant does not report the total invariant
* Fixes sasview  # 1599: ESS_GUI: fix data test
* Fixes sasview  # 1598: ESS_GUI: allow data replacement on a fit page
* Fixes sasview  # 1579: Save inversion state in project and analysis files (ESS_GUI)
* Fixes sasview  # 1578: Changing perspective closes the perspective
* Fixes sasview  # 1567: Ess gui 1554 slicer
* Fixes sasview  # 1560: set the sasmodels dll cache directory in sasview startup
* Fixes sasview  # 1556: Fixed the edge cases and added a beefy unit test. #1546
* Fixes sasview  # 1554: ESS_GUI: annulus slicer not opening
* Fixes sasview  # 1553: Ess gui 1547 smearing
* Fixes sasview  # 1550: Ess gui 1522 poly check
* Fixes sasview  # 1548: Sasview 5.0.2 "file converter" tool does not open
* Fixes sasview  # 1547: Resolution is incorrectly handled in 5.x
* Fixes sasview  # 1546: Plotting an already plotted dataset causes the new plot to only show model
* Fixes sasview  # 1543: SasView application window needs to be scrollable
* Fixes sasview  # 1538: Constrained fitting doesn't work when setting min/max for polydispersity
* Fixes sasview  # 1536: ESS GUI: Paste Params not activated until Copy Params has been used
* Fixes sasview  # 1535: ESS_GUI: Existing common parameters not preserved between models in 5.x
* Fixes sasview  # 1534: ESS_GUI: Something strange with 5.x and the .sasview folder
* Fixes sasview  # 1529: ESS GUI Corfunc: Input area is not scrollable in Corfunc Perspective in 5.0.2
* Fixes sasview  # 1527: NXcanSAS definition changes
* Fixes sasview  # 1523: Plot legend visibility toggle needs to be restored
* Fixes sasview  # 1522: Incorrect behavior of "fittable" checkbox in polydispersity tab
* Fixes sasview  # 1490: Problem using constraints in 5.x
* Fixes sasview  # 1456: 5.0.1 constraints between FitPages stop working
* Fixes sasview  # 1414: No pan function in plot windows in 5.0.1
* Fixes sasview  # 1002: canSAS XML should save transmission spectrum
* Fixes sasview  #  726: Check default value of cansas_version property in CansasReader class
* Fixes sasmodels # 415: Suppress pyopencl caching bug for Intel on Mac
* Fixes sasmodels # 414: sasview saying unknown distribution option 'test_requires'
* Fixes sasmodels # 404: delay the inevitable a little longer and reenable python 2.7 support
* Fixes sasmodels # 402: sasview 1534: use source hash as part of dll name to avoid collisions
* Fixes sasmodels # 401: warn if ER() is ignored
* Fixes sasmodels # 365: OpenCL errors on macbook pro 2017

Known Issues
^^^^^^^^^^^^
At this time, and unlike version 4.x, only fitting and P(r) inversion sessions can be saved as project files.

There is also a bug which is stopping Batch Fitting from using the intensity uncertainty (dI) data if this 
is present in the files being processed. As the default behaviour of normal Single Fitting is to automatically 
use the dI data in the file if it is present, this means that the results of Single Fitting and Batch Fitting 
the same data will differ.

All the known bugs/feature requests can be found in the issues on github.
Note the sasmodels issues are now separate from the sasview issues (i.e. different repositories)

`[sasview] <https://github.com/SasView/sasview/milestones>`_

`[sasmodels] <https://github.com/SasView/sasmodels/milestones>`_


New in Version 5.0.2
--------------------
This is a point release which fixes several issues reported in version 5.0.1, however
there are also some new features:

New features/improvements
^^^^^^^^^^^^^^^^^^^^^^^^^
* sasview  # 1480: Added enumeration of plots in the Windows menu, with raising/setting
* sasview  # 1355: SasView 5.0 lacks file conversion option in tool menu
* sasmodels # 390: Re-describe Source intensity in model parameter tables
* sasmodels # 382: Doc gen speedup, improved random model generation and minor fixes
* sasmodels # 211: Reparameterize existing model.

Bug Fixes
^^^^^^^^^
* Fixes sasview  # 1501: Update 5.x documentation for Corfunc
* Fixes sasview  # 1499: Ess gui 1355 file converter
* Fixes sasview  # 1484: SasView 5 (Ubuntu) - Need to change colors in Data operation combobox
* Fixes sasview  # 1482: 4.x: Check packages comparison to YAML files
* Fixes sasview  # 1481: Fix for Fit Panel based Plot command for single-data/multiple fit tab
* Fixes sasview  # 1479: linspace errors
* Fixes sasview  # 1476: Quick Plot in Data Explorer not working for 1D data
* Fixes sasview  # 1463: Dmax explorer : pressing enter closes window
* Fixes sasview  # 1460: resolution setting not persistent in theory mode of 5.0.1
* Fixes sasview  # 1459: dy = 1 for every point of Freeze theory curves (and saved as data file) in 5.0.
* Fixes sasview  # 1455: 5.0.1 load project generates a second FitPage1
* Fixes sasview  # 1454: 5.0.1 sending same data to more than one fit page - plotting issues
* Fixes sasview  # 1444: ESS GUI: Warn user when data set fully masked
* Fixes sasview  # 1431: When loading plugin model with a spurious unicode character plugin editor crashes
* Fixes sasview  # 1419: Could we improve stepping through graph windows in 5.x
* Fixes sasview  # 1138: Check package versions in yaml files and setup.py
* Fixes sasview  #  697: Update check_packages to flag required package versions
* Fixes sasmodels # 383: Model docs build failing on linspace error
* Fixes sasmodels # 381: reparameterize has a bug (at least in v5)

Known Issues
^^^^^^^^^^^^
A very long-standing error has been identified in the Invariant Analysis
perspective. The value of the specific surface $Sv$ that is being returned
is in fact *twice* the value that it should be. Work is underway to correct this
and some other deficiencies in the operation of the perspective, and to significantly
enhance the invariant documentation.

Also, at this time, and unlike version 4.x, only fitting sessions can be saved as project files.


New in Version 5.0.1
--------------------
This is a point release which fixes several issues reported in version 5.0.0.

Bug Fixes
^^^^^^^^^
* Fixes sasview # 1452: Clarified issue with Add/Multiply operation for plugin models
* Fixes sasview # 1441: Show SLD profile plot - linear not log
* Fixes sasview # 1431: When loading plugin model with unicode character, plugin editor crashes
* Fixes sasview # 1417: Ambiguous labeling in Resolution tab
* Fixes sasview # 1413: Corfunc is not working well
* Fixes sasview # 1412: Windows installer shortcut is misnamed
* Fixes sasview # 1410: Issues with multi-core shell model
* Fixes sasview # 1374: Data Operations not including all datasets
* Fixes sasview # 1371: Multiple issues with fit plot lifetimes
* Fixes sasview # 1361: Data with negative values not showing on linear scale
* Fixes sasview # 1357: Q-range in the Correlation Function can be set by dragging
* Fixes sasview # 1356: Load in Mask Data column from NCNR 2D Data
* Fixes sasview # 1356: Change default state of dependent plots to unchecked
* Fixes sasview # 1350: Multiple issues with the 2D slicer
* Fixes sasview # 1339: Problem with plotting of the Correlation Function
* Fixes sasview # 1337: Automatically resizing plot legends
* Fixes sasview # 1337: Non-resizing plot legend on OSX
* Fixes sasview # 1336: Issues with closing and reopening fit plots
* Fixes sasview # 1327: Append functionality too generous
* Fixes sasview # 1325: Changing model resets the Q-range
* Fixes sasview # 1293: Cannot model SESANS Data in GUI
* Fixes sasview # 1086: Added separate thread for OpenCL tests
* Fixes sasview #  937: Set theory and data to the same Vmin/Vmax for 2D plots
* Fixes sasview #  690: Set reasonable min/max on polydispersity values for fitting

Known Issues
^^^^^^^^^^^^
A problem has been identified in Version 4.2.2 which also affects versions
5.0.0 and 5.0.1. The Easy Add/Multiply Editor dialog should not be used to
combine a plugin model with a built-in model, or to combine two plugin models.
In 5.0.0 the operation will fail (generating an error message in the Log Explorer).
Whilst in 5.0.1 the operation has been blocked until the problem can be fixed.
If it is necessary to generate a plugin model from more than two built-in models,
please edit the plugin model .py file directly and specify the combination of built-in
models directly. For example::

     from sasmodels.core import load_model_info
     from sasmodels.sasview_model import make_model_from_info
     model_info = load_model_info('power_law+fractal+gaussian_peak+gaussian_peak')
     model_info.name = 'MyBigPluginModel'
     model_info.description = 'For fitting pores in crystalline framework'
     Model = make_model_from_info(model_info)


New in Version 5.0
------------------
This is a new version of SasView featuring new and enhanced GUI, back-end calculations,
GUI separation, optimization of calculations and other improvements. This release also
includes beta (decoupling) approximation for intensity calculation.

The release is based on Python 3 and Qt5/PyQt5.

We recommend that you avoid using installation folder paths which contain spaces, non-Latin
characters or characters not available on a standard keyboard.

Changes/Improvements from 5.0.beta2
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
* Beta (decoupling) approximation has been introduced
* Stop fit button added to Constrained and Simultaneous Fitting
* Plotting has been improved
* Volume fraction naming conflicts has been resolved
* SLD calculator user interface has been improved
* Fit Options tab has been improved
* Windows installer path specification has been resolved
* Copy parameters function has been fixed
* Save/Load Project functionality has been improved

Documentation
^^^^^^^^^^^^^
* Documentation for Constrained and Simultaneous Fitting has been considerably reworked.
* Tutorials have been adapted to match 5.0 interface

Known Issues
^^^^^^^^^^^^
All the known bugs/feature requests can be found in the issues on github.

`[sasview] <https://github.com/SasView/sasview/milestones>`_

`[sasmodels] <https://github.com/SasView/sasmodels/milestones>`_


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
  https://github.com/SasView/sasview/wiki/DevNotes_Projects_Debian
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
* Fixes # 818: 'report button' followed by 'save' makes an empty pdf file???
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

The easiest approach to setting up the proper environment to build from source 
is to use Conda. Instructions for setting up and using Conda can be found at 
https://github.com/SasView/sasview/wiki/DevNotes_DevEnviroment
                    
Additional information is available at http://www.sasview.org/download/ under 
the 'For Developers' section, and on our Trac site at https://github.com/SasView/sasview/wiki/

System Requirements
-------------------
* For SasView 4.x and earlier: A Python version >= 2.5 and < 3.0 should be running 
  on the system. We currently use Python 2.7
* For SasView 5.x: A Python version > 3.0 should be running on the system. We 
  currently use Python 3.6

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
* To build and install the code
  use 'pip install .'
* To build a wheel for installation elsewhere
  use 'hatchling build --wheel'
* To build the documentation
  use 'hatchling build --hooks-only'

Running SasView
---------------
* use 'python run.py'; this runs from the source directories, so you
  don't have to rebuild every time you make a change, unless you are
  changing the C model files.
* if using Conda the above command will also build SasView, but you 
  must issue 'activate sasview' first.

Known Issues
============

A full list of known bugs and feature requests by release version that 
users may wish to be aware of can be viewed at the following links:

`[sasview] <https://github.com/SasView/sasview/milestones>`_

`[sasmodels] <https://github.com/SasView/sasmodels/milestones>`_

All 5.0.x versions / 4.2.2 - All systems
----------------------------------------
A problem has been identified in Version 4.2.2 which also affects all 5.0.x
versions. The Easy Add/Multiply Editor dialog should not be used to combine
a plugin model with a built-in model, or to combine two plugin models. In
5.0.x the operation will fail, generating an error message in the Log Explorer
similar to

     ModuleNotFoundError: No module named 'plugin_module_name'

If it is necessary to generate a plugin model from more than two built-in models,
please edit the plugin model .py file directly and specify the combination of
built-in models directly. For example::

     from sasmodels.core import load_model_info
     from sasmodels.sasview_model import make_model_from_info
     model_info = load_model_info('power_law+fractal+gaussian_peak+gaussian_peak')
     model_info.name = 'MyBigPluginModel'
     model_info.description = 'For fitting pores in crystalline framework'
     Model = make_model_from_info(model_info)
     
5.0.0 / 5.0.1 / 5.0.2 / 5.0.3 - All systems
-------------------------------------------
There is a bug which is stopping Batch Fitting from using the intensity 
uncertainty (dI) data if this is present in the files being processed. 
As the default behaviour of normal Single Fitting is to automatically 
use the dI data in the file if it is present, this means that the results 
of Single Fitting and Batch Fitting the same data will differ.

All versions upto and including 5.0.2 - All systems
---------------------------------------------------
A very long-standing error has been identified in the Invariant Analysis
perspective. The value of the specific surface $Sv$ that is being returned
is in fact *twice* the value that it should be.
     
5.0.0 / 5.0.1 / 5.0.2 - All systems
-----------------------------------
In these versions, and unlike version 4.x, only fitting sessions can be saved as project files.

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
http://www.sasview.org/faq/
