Release Notes
=============

1- Features
===========
    - New in Version 4.1.2
      --------------------
      This point release is a bug-fix release addressing:

       - Fixes #984: PDF Reports Generate Empty PDFs
       - Fixes a path typo
       - 64 bit and 32 bit Windows executables now available

      It is recommended that all users upgrade to this version

    - New in Version 4.1.1
      --------------------
      This point release is a bug-fix release addressing:

       - Fixes #948: Mathjax CDN is going away
       - Fixes #938: Cannot read canSAS1D file output by SasView
       - Fixes #960: Save project throws error if empty fit page
       - Fixes #929: Problem deleting data in first fit page
       - Fixes #918: Test folders not bundled with release
       - Fixes an issue with the live discovery of plugin models
       - Fixes an issue with the NXcanSAS data loader
       - Updated tutorials for SasView 4.x.y

    - New in Version 4.1.0
      ------------------
      This incremental release brings a series of new features and improvements,
      and a host of bug fixes. Of particular note are:
      
      - Correlation Function Analysis (Corfunc)
      	This performs a correlation function analysis of one-dimensional SAXS/SANS data, 
	or generates a model-independent volume fraction profile from the SANS from an 
	adsorbed polymer/surfactant layer.

	A correlation function may be interpreted in terms of an imaginary rod moving 
	through the structure of the material. Γ1D(R) is the probability that a rod of 
	length R moving through the material has equal electron/neutron scattering 
	length density at either end. Hence a frequently occurring spacing within a 
	structure manifests itself as a peak.

	A volume fraction profile \Phi(z) describes how the density of polymer 
	segments/surfactant molecules varies with distance from an (assumed locally flat)
	interface.

      - Fitting of SESANS Data
      	Data from Spin-Echo SANS measurements can now be loaded and fitted. The data will 
	be plotted against the correct axes and models will automatically perform a Hankel 
	transform in order to calculate SESANS from a SANS model.

      - Documentation
      	The documentation has undergone significant checking and updating.

      - Improvements
        - Correlation function (corfunc) analysis of 1D SAS data added from CCP13
        - File converter tool for multi-file single column data sets
        - SESANS data loading and direct fitting using the Hankel transformation
        - Saving and loading of simultaneous and constrained fits now supported
        - Save states from SasView v3.x.y now loaded using sasmodel model names
        - Saving and loading of projects with 2D fits now supported
        - Loading a project removes all existing data, fits, and plots
        - Structure factor and form factor can be plotted independently
        - OpenCL is disabled by default and can be enabled through a fit menu
        - Data and theory fields are now independently expandable
      - Bug Fixes
        - Fixes #667: Models computed multiple times on parameters changes
        - Fixes #673: Custom models override built in models of same name
        - Fixes #678: Hard crash when running complex models on GPU
        - Fixes $774: Old style plugin models unloadable
        - Fixes #789: stacked disk scale doesn't match cylinder model
        - Fixes #792: core_shell_fractal uses wrong effective radius
        - Fixes #800: Plot range reset on plot redraws
        - Fixes #811 and #825: 2D smearing broken
        - Fixes #815: Integer model parameter handling
        - Fixes #824: Cannot apply sector averaging when no detector data present
        - Fixes #830: Cansas HDF5 reader fully compliant with NXCanSAS v1.0 format
        - Fixes #835: Fractal model breaks with negative Q values
        - Fixes #843: Multilayer vesicle does not define effective radius
        - Fixes #858: Hayter MSA S(Q) returns errors
        - Numerous grammatical and contexual errors in documention


    - New in Version 4.0.1
      ------------------
      This release fixes the critical bug #750 in P(Q)*S(Q).  Most damaging
      it appears that the background term was being added to S(Q) prior to
      multiplication by P(Q).


    - New in Version 4.0
      ------------------
      This release fixes the various bugs found during the alpha and beta testing
      - Improvements
        - Support for reading data files from Anton Paar Saxess instruments
        - Adds documentation on how to write custom models in the new framework
      - Bug Fixes
        - Fixes bug #604 Pringle model questions
        - Fixes bug #472 Reparameterize Teubner-Strey
        - Fixes bug #530 Numerical instabilities in Teubner Strey model
        - Fixes bug #658 ASCII reader very broken


    - New in Version 4.0 beta 1
      --------------------
      This beta adds support for the magnetic and multilevel models of 3.1.2
      and along with a host of bug fixes found in the alpha.

      - Model package changes and improvements
         - All 3.1.2 models now available in new interface
         - Old custom models should now still work
            - '''NOTE:''' These will be deprecated in a future version. Old
            custom models should be converted to the new model format which
            is now the same as the built in models and offers much better
            support.
         - Custom model editor now creates new style models
         - Custom model editor supports better error checking
      - Documentation improvements
        - Continued general cleanup
      - Other improvements/additions
         - Support for new canSAS 2D data files added
         - Plot axes range can now be set manually as well as by zooming
         - Plot annotations can now be moved around after being placed on plot.
         - The active optimizer is now listed on the top of the fit panel.
         - Linear fits now update qmin and max when the x scale limits are
         changed.  Also the plot range no longer resets after a fit.
      - Bug fixes
         - Fixes bug #511 Errors in linearized fits and clean up of interface
         including Kratky representation
         - Fixes bug #186 Data operation Tool now executes when something is
         entered in the text box and does not wait for the user to hit enter
         - Fixes bug #459 plot context menu bug
         - Fixes bug #559 copy to clipboard in graph menu broken
         - Fixes bug #466 cannot remove a linear fit from graph
         - Numerous bugs introduced in the alpha



    - New in Version 4.0 beta 1
      --------------------
      This beta adds support for the magnetic and multilevel models of 3.1.2
      and along with a host of bug fixes found in the alpha.

      - Model package changes and improvements
         - All 3.1.2 models now available in new interface
         - Old custom models should now still work
            - '''NOTE:''' These will be deprecated in a future version. Old
            custom models should be converted to the new model format which 
            is now the same as the built in models and offers much better
            support.
         - Custom model editor now creates new style models
         - Custom model editor supports better error checking
      - Documentation improvements
        - Continued general cleanup
      - Other improvements/additions
         - Support for new canSAS 2D data files added
         - Plot axes range can now be set manually as well as by zooming
         - Plot annotations can now be moved around after being placed on plot.
         - The active optimizer is now listed on the top of the fit panel.
         - Linear fits now update qmin and max when the x scale limits are
         changed.  Also the plot range no longer resets after a fit.
      - Bug fixes
         - Fixes bug #511 Errors in linearized fits and clean up of interface
         including Kratky representation
         - Fixes bug #186 Data operation Tool now executes when something is
         entered in the text box and does not wait for the user to hit enter
         - Fixes bug #459 plot context menu bug
         - Fixes bug #559 copy to clipboard in graph menu broken
         - Fixes bug #466 cannot remove a linear fit from graph
         - Numerous bugs introduced in the alpha



    - New in Version 4.0.0-alpha
      --------------------
      This alpha release brings a major overhaul of the model system. The new model
      package allows rapid integration of custom models and access to polydispersity
      without requiring a compiler.

      - Model package changes and improvements
         - Model interface moved to independent sasmodels package.
         - Most models converted to new interface.
         - Allows rapid integration of user-written models.
         - OpenCL GPU utilization for faster fitting.
         - Improved numerical integration of Bessel functions.
      - SESANS integration and implementation
         - Scripting interface added for analysis of SESANS data.
         - Hankel transformation now accepts finite acceptance angles.
         - 2D cosine transformation added for TOF SESANS analysis.
      - Documentation improvements
         - The documentation tree was restructured for a better end user experience.
         - The documentation for each model was revamped and verified by at least
           two people following the conversion of the model.
         - Theoretical 1D (and 2D if applicable) scattering curves are auto-generated
           and added to the model documentation for each model.
      - Separation of GUI and calculations for future GUI enhancements
      - Bug fixes
         - Fixes bug #411 No stop button on simultaneous fit page
         - Fixes bug #410 Error with raspberry model
         - Fixes bug #364 Possible inconsistency in Poly_GausCoil model
         - Fixes bug #439 Hayter Penfold MSA code needs checking
         - Fixes bug #484 lammellerPC is precision limited
         - Fixes bug #498 $HOME/.matplotlib conflicts
         - Fixes bug #348 Control order in which fit parameters appear in the gui
         - Fixes bug #456 Provide DREAM Results Panel with something to identify
           data and age of results
         - Fixes bug #556 Build script improvements for developers



   - New in Version 3.1.2
     --------------------
     This release is a major stability improvement, having fixed a serious bug
     that came to light since release 3.1.1. All users should upgrade.

     - Fixes bug #468 broken remove constraint buttons in
       simultaneous/constrained fitting panel
     - Fixes bug #474 resulting from changes in 3.1.1 that had
       introduced an error in the high-Q of slit-smeared models.
     - Fixes bug #478 which would cause wx to run out of IDs and result
       in SasView crashing even if left alone.
     - Fixes bug #479 missing help button on simultaneous/constrained fit page
     - Fixes bug #480 GUI resizing issues on simultaneous fit page
     - Fixes bug #486 broken Report Results
     - Fixes bug #488 redraw issues in fit page



   - New in Version 3.1.1
     --------------------
     - Fixes bug #457 that prevented SasView from starting if the user was not
       connected to the internet, or was behind a proxy server.

   - New in Version 3.1.0
     --------------------
     - The documentation/help has had a complete overhaul including:
       - A completely new presentation interface (Sphinx).
       - Proof reading!
       - Updating for latest features.
       - A Help (or sometimes ?) button has been added to every panel, and some
         sub panels if appropriate, linking to the appropriate section in the
         documentation.
       - The model help has been split so that the Details button now brings up
         a very short pop-up giving the equation being used while HELP goes to
         the section in the full documentation describing the model.
       - Extensive help has also been added for the new optimizer engine (see
         below) including rules of thumb on how and when to choose a given
         optimizer and what the parameters do.
     - The optimizer engine has been completely replaced. The new optimizer
       still defaults to the standard Levenberg-Marquardt algorithm. However 4
       other optimizers are now also available. Each starts with a set of default
       parameters which can be tuned. The DREAM optimizer takes the longest but
       is the most powerful and yields rich information including full parameter
       correlation and uncertainty plots. A results panel has been added to
       accommodate this.
       - The five new optimizers are:
         - A Levenberg-Marquardt optimizer
         - A Quasi-Newton BFGS optimizer
         - A Nelder-Mead Simplex optimizer
         - A Differential Evolution optimizer
         - A Monte Carlo optimizer (DREAM)
     - New models were added:
         - MicelleSphCoreModel (currently residing in the Uncategorized category)
     - Existing models were updated:
         - LamellarPS (bug in polydispersity integration fixed)
         - RectangularPrismModel
         - RectangularHollowPrismModel
         - RectangularHollowPrismInfThinWallsModel
     - Infrastructure to allow SESANS data to be fit with models was added. This
       will become available in a future release but can currently be used from
       the command line with some caveats.
     - A number of bugs were fixed including a thread crashing issue and an
       incorrect slit smearing resolution calculation.
     - Implemented much more robust error logging to enable much easier
       debugging in general but particularly the debugging of issues reported by
       SasView users.
     - A number of infrastructure tasks under the hood to enhance maintainability
     - Upgrade from Wx 2.8 to Wx 3.0.2 which allows several new features but
       required significant additional rework as well.
     - Fully implemented Sphinx to the build process to produce both better
       user documentation and developer documentation.
     - Restructuring of the code base to more unified nomenclature and structure
       so that the source installation tree more closely matches the installer
       version tree.
     - Code cleanup (an ongoing task) .
     - Migration of the repository to github simplifying contributions from
       non-project personnel through pull requests.

   - New in Version 3.0.0
     --------------------
     - The GUI look and feel has been refactored to be more familiar for
       Windows users by using MDI frames. Graph windows are also now free-
       floating.
     - Five new models have been added: PringlesModel, CoreShellEllipsoidXTModel,
       RectangularPrismModel, RectangularHollowPrismModel and
       RectangularHollowPrismInfThinWallsModel.
     - The data loader now supports ILL DAT data files and reads the full meta
       information from canSAS file formats.
     - Redefined convention for specifying angular parameters for anisotropic
       models.
     - A number of minor features have been added such as permitting a log
       distribution of points when using a model to simulate data, and the
       addition of a Kratky plot option to the linear plots.
     - A number of bugs have also been fixed.
     - Save Project and Save Analysis now work more reliably.
     - BETA: Magnetic contrast supporting full polarization analysis has been
       implemented for some spherical and cylindrical models.
     - BETA: Two new tools have been added:
       - A generic scattering calculator which takes an atomic, magnetic or
         SLD distribution in space and generates the appropriate 2D
         scattering pattern. In some cases the orientationally averaged
         (powder) 1D scattering can also be computed. Supported formats
         include: SLD or text, PDB, and OMF magnetic moment distribution
         file.
       - An image viewer/converter for data in image format; this reads in
         an image file and will attempt to convert the image pixels to
         data. Supported formats include: TIFF, TIF, PNG, BMP, JPG.

   - New in Version 2.2.1
     --------------------
     - Minor patch to support CanSAS XML v1.1 file format
     - Added DataInfo for data in the DataExplorer and plots
     - Added Maximize/Restore button in the title bar of the graphs
     - Added a hide button in the toolbar of the graph panel
     - The 'x' button now deletes a graph
     - Edit SUM Model from the menubar can now generate and save more than one sum model
     - Reports can now be saved in pdf format on WIN and MAC
     - Made significant improvements to the batch/grid panel and fixed several bugs
     - Fixed a number of other minor bugs

   - New in Version 2.2.0
     --------------------
     - Application name changed to SasView
     - New fully customizable Category Manager added for better management of
       increasing number of models
     - Improved the Grid Window functionality in the batch fitting mode
     - Added a simpler Graph/Plot modification interface
     - Added a new 'Data Operation' tool for addition, subtraction, multiplication,
       division, of two data sets.
     - The 'Sum Model' editor was extended and renamed 'Summation and Multiplication'
       editor
     - Added more plot symbols options for 1d plots
     - Added improved trapping of compiling errors to the 'New model editor'
     - Added some intelligent outputs (e.g., Rg, background, or rod diameter
       depending on the choice of axis scale of the plot) to the linear fits
     - Added more models

   - Feature set from previous versions
     -----------------------------------
     - Perspectives Available
       - Invariant calculator: Calculates the invariant, volume fraction, and
         specific surface area.
       - P(r) inversion calculator: Indirect Fourier transformation method.
       - Fitting: the tool used for modeling and fitting 1D and 2D data to
         analytical model functions
       - Tools: provides a number of useful supplementary tools such as SLD
         calculation

     - Fitting
       - Includes a large number of model functions, both form factors and structure factors.
       - Support P(Q)*S(Q) for form factors that flag they can be so multiplied.
       - Supports Gaussian, lognormal, Shulz, rectangular and custom distribution
         functions for models that need to include polydispersity or for orientational
         distributions if appropriate.
       - Anisotropic shapes and magnetic moment modeling in 2D allow for a non-uniform
         distribution of orientations of a given axis leading to modeling and fitting
         capabilities of non azimuthaly symmetric data.
       - User can choose to weight fits or not. If using weights, the user can choose
         the error bar on each point if provided in the file, the square root
         of the intensity or the intensity itself.
       - Instrumental resolution smearing of model or fits is provided with several
         options: read the resolution/point fromt he file. Input a pinhole resolution
         or a slit resolution.
       - Users can define the Qrange (Qmin and Qmax) for both 1D and 2D data for
         fitting and modeling, but not graphically.  The range can be reset to the
         defaults (limits of q in data set for a fit) with the reset button.
       - A mask can be applied to 2D calculation and fitting.
       - Normalized residual plots are provided with every fit.
       - Model function help available through detail button or from the fitting panel.
       - Simultaneous/(advanced)constrained fitting allows for fitting a single
         data set or several different sets simultaneously with the application
         of advanced constraints relating fit parameters to functions of other
         parameters (including from a different set). For example thickness of
         shell = sin(30) times the length.
       - Models that are the sum of two other models can be easily generated through the
         SUM Model menubar item.
       - New Python models can be added on the fly by creating an appropriate Python
         file in the model plugin directory. Two tools are provided to help:
         An easy to use custom model editor allows the quick generation of new Python
         models by supplying only the parameters and their default value (box 1)
         and the mathematical function of the model (box 2) and generating the
         necessary *.py file.  A separate advanced model editor provides a full Python
         file editor.  Either way once saved the model becomes immediately available
         to the application.
       - A batch fitting capability allows for the analysis of a series of data sets to
         a single model and provides the results in a tabular form suitable for saving
         or plotting the evolution of the fit parameters with error bars (from within
         the application).

     - Tools
       - A scattering length density calculator,including some X-ray information
         is provided.
       - A density to vol. fraction converter is provided
       - In application access to a Python shell/editor (PyCrust) is provided
       - An instrument resolution calculator, including possible gravitational and
         TOF effects is provided
       - A slit size calculator optimized for Anton Paar Saxess is provided.
       - A kiessig fringe thickness calculator is provided

     - Plots and plot management
       - A 3D graphing option (for 2d data/results) is provided with the view
         controlled by the mouse
       - 2D plots are shown with an intensity color bar. 2D Color map can be user
         adjusted.
       - Supports output of plot to a variety of graphic formats. Supported formats
         include: png, eps, emf, jpg/jpeg, pdf, ps, tif/tiff, rawRGBbitmap(raw, rgba),
         and scalable vector graphic (svg/svgz)
       - Supports ouput of data in plot (1 or 2D) to limited data formats
       - Multiple data sets can be loaded into a single graph for viewing (but a fit
         plot can currently only have a single plot).
       - Extensive context sensitive plot/fitting/manipulation options are available
         through a right mouse click pop-up menu on plots.

     - Data management
       - Supports 2 + column 1D ASCII data, NIST 1D and 2D data, and canSAS data
         via plug-in mechanism which can easily allow other readers as appropriate.
       - 2D data is expected in Q space but for historical reasons accepts the
         NIST 2D raw pixel format and will do conversion internally.
       - The full data and metadata available to SasView is viewable in ASCII via
         right clicking on a data set and choosing Data Info in the DataExplorer
         or on the plots
       - Supports loading a single file, multiple files, or a whole folder
       - An optional Data Explorer is provided (default) which simplifies managing,
         plotting, deleting, or setup for computation. Most functions however do
         not require access to the explorer/manager and can be accessed through
         right click menus and the toolbar.  The data explorer can be re-started
         from the menu bar.

     - Data manipulation
       - Support various 2D averaging methods : Circular, sectors, annular,
         boxsum, boxQx and boxQy.
       - A 2D data maks editor is provided
       - 2D mask can be applied to the circular averaging.

     - Miscellaneous features
       - limited reports can be generated in pdf format
       - Provides multiprocessor support(Windows only)
       - Limited startup customization currently includes default startup
         data folder and choice of default starting with data manager
       - Limited support for saving(opening) a SasView project or a SasView analysis
         (subproject) is provided.
       - SasView can be launched and loaded with a file of interesty by double-clicking
         on that file (recognized extension)
       - A data file or data folder can be passed to SasView when launched from
         the command line.
       - Limited bookmarking capability to later recall the results of a fit calculation
         is provided.
       - Extensive help is provided through context sensitive mouse roll-over,
         information bar (at the bottom of the panel), the console menu, and
         access to the help files in several different ways.


2- Downloading and Installing
=============================

   *** Note 1:  Much more information is available at www.sasview.org under links.
	            Look in the 'For Developers' section and particularly the wiki at
                www.sasview.org/trac/wiki.
   *** Note 2:  If you have EXE or ZIP SasView installer, you won't need any of
                the following.  However it is highly recommended that any
                previous versions be un-installed prior to installing the
                new version.

   2.1- System Requirements
        - Python version >= 2.5 and < 3.0 should be running on the system
        - We currently use Python 2.7

   2.2- Installing from source
        - Get the source code
          - to follow the current development version from source control use
              git clone https://github.com/SasView/sasview.git
              git clone https://github.com/bumps/bumps.git
	  - to install a specific version

        - Build, install and run a specific release
          - make sure the requirements below are already installed
          - retrieve the source from https://github.com/SasView/sasview/releases
          - open a command line window in the 'sasview-x.x.x' directory
          - run 'python setup.py install'
          - run 'python sasview.py' under the 'sasview' folder.

        - Build, install and run the current development version
          - clone the source from git; also clone bumps, which is developed in parallel
              git clone https://github.com/SasView/sasview.git
              git clone https://github.com/bumps/bumps.git
          - open a command line window in the 'sasview' directory
          - run 'python setup.py build'
          - run 'python run.py'; this runs from the source directories, so you
            don't have to rebuild every time you make a change, unless you are
            changing the C++ model files

        - The following modules are required (version numbers are what are used
          in the windows release build):

          - Common Packages
            - reportlab 3.1.44
            - lxml 3.4.4.0 (MAC 3.4.2.0)
            - PIL 1.1.7
            - xhtml2pdf 3.0.33 (MAC = not installed on build server)
            - unittest-xml-reporting 1.12.0 (MAC 1.10.0)
            - matplotlib Version Installed: 1.4.3 (MAC 1.1.1)
            - bumps Version Installed: 0.7.5.9
            - scipy Version Installed: 0.16.0b2 (MAC 0.11.0)
            - periodictable Version Installed: 1.4.1
            - setuptools Version Installed: 7.0 (MAC 12.0.5)
            - sphinx Version Installed: 1.3.1 (MAC 1.3b2)
            - pyparsing Version Installed: 2.0.3
            - numpy Version Installed: 1.9.2 (MAC 1.6.2)
            - html5lib Version Installed: 0.99999
            - wx Version Installed: 3.0.2.0

          - Windows Specific Packages
            - pywin 219
            - py2exe 0.6.9
            - comtypes 1.1.1
            - MinGW w/ gcc version 4.6.1 (WIN)
            - vcredist_x86.exe (version 9.0.21022.8  -microsoft visual C 2008
              re-distributable)
            - Innosetup (WIN - isetup 5.4.2-unicode) - used to create distributable

            *** Note: Windows build dependencies can be set up using anaconda. Instructions
                can be found at http://trac.sasview.org/wiki/AnacondaSetup

          - MAC Specifc Packages
            - py2app 0.7.1


3- Known Issues
===============


   4.1- All systems:
      The conversion to sasmodels infrastructure is ongoing and should be
      completed in the next release. In the meantime this leads to a few known
      issues:
        - The way that orientation is defined is being refactored to address
        long standing issues and comments.  In release 4.1 however only models
        with symmetry (e.g. a=b) have been converted to the new definitions.
        The rest (a <> b <> c - e.g. parellelepiped) maintain the same
        definition as before and will be converted in 4.2.  Note that
        orientational distribution also makes much more sense in the new
        framework.  The documentation should indicate which definition is being
        used for a given model.
        - The infrastructure currently handles internal conversion of old style
        models so that user created models in previous versions should continue
        to work for now. At some point in the future such support will go away.
        Everyone is encouraged to convert to the new structure which should be
        relatively straight forward and provides a number of benefits. 
        - In that vein, the distributed models and those generated by the new
        plugin model editor are in the new format, however those generated by
        sum|multiply models are the old style sum|multiply models. This should
        also disappear in the near future 
        - The on the fly discovery of plugin models and changes thereto behave
        inconsistently.  If a change to a plugin model does not seem to
        register, the Load Plugin Models (under fitting -> Plugin Model
        Operations) can be used.  However, after calling Load Plugin Models, the
        active plugin will no longer be loaded (even though the GUI looks like
        it is) unless it is a sum|multiply model which works properly.  All
        others will need to be recalled from the model dropdown menu to reload
        the model into the calculation engine.  While it might be annoying it
        does not appear to prevent SasView from working..
        - The model code and documentation review is ongoing. At this time the
        core shell parellelepiped is known to have the C shell effectively fixed
        at 0 (noted in documentation) while the triaxial ellipsoid does not seem
        to reproduce the limit of the oblate or prolate ellipsoid. If errors are
        found and corrected, corrected versions will be uploaded to the
        marketplace. 
   
   3.1- All systems:
        - The documentation window may take a few seconds to load the first time
          it is called. Also, an internet connection is required before
          equations will render properly. Until then they will show in their
          original TeX format.
        - If the documentation window remains stubbornly blank, try installing a
          different browser and set that as your default browser. Issues have
          been noted with Internet Explorer 11.
        - Check for Updates may fail (with the status bar message ' Cannot
          connect to the application server') if your internet connection uses
          a proxy server. Tested resolutions for this are described on the
          website FAQ.
        - The copy and paste functions (^C, ^V) in the batch mode results grid
          require two clicks: one to select the cell and a second to select the
          contents of the cell.
        - The tutorial has not yet been updated and is somewhat out of date
        - Very old computers may struggle to run the 3.x and later releases
        - Polydispersity on multiple parameters included in a simultaneous/
          constrained fit will likely not be correct
        - Constrained/simultaneous fit page does not have a stop button
        - Constrained/simultaneous fit do not accept min/max limits
        - Save project does not store the state of all the windows
        - Loading projects can be very slow
        - Save Project only works once a data set has been associated with
          a model.  Error is reported on status bar.
        - There is a numerical precision problem with the multishell model when
          the iner radius gets large enough (ticket #288)
        - The angular distribution angles are not clearly defined and may in
          some cases lead to incorrect calculations(ticket #332)

   3.2- Windows:
        - If installed to same directory as old version without first removing
          the old version, the old desktop icon will remain but point to the
          new exe version. Likewise all the start menu folders and items will
          have the old name even though pointing to the new version.  Usually
          safest to uninstall old version prior to installing new version anyway.

   3.3- MAC:
        - Application normally starts up hidden. Click icon in Dock to view/use
          application.
        - Multiprocessing does not currently work on MAC OS

   3.4- Linux:
        - Not well tested


4- SasView website
==================

   - www.sasview.org.  This main project site is the gateway to all
     information about the sasview project.  It includes information
     about the project, a FAQ page and links to all developer and user
     information, tools and resources.


5- Frequently Asked Questions
=============================

   - www.sasview.org/faq.html


6- Installer download website
=============================

   - Latest release Version
     - https://github.com/SasView/sasview/releases
   - Latest developer builds
     - https://jenkins.esss.dk/sasview/view/Master-Builds/
