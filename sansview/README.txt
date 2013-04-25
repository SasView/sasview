Release Notes
=============

SasView 3.0.0

    - Implemented Polarization and magnetic SANS parameters in some models.
    - New Tool: Generic SANS / PDB reader & atomic scattering calculator
    - New Tool: Image viewer
    - Redefined angles of angular parameters for anisotropic models
    - Use MDI frames in GUI

	- Previous Versions: 
	
	- Changed the application name to 'SasView'.
	- Model category can be modified via (Category Manager).
	- Improved Grid/Batch window functionality.
	- Added a new tool; Data operation for addition, subtraction, multiplication, division, and combination of two data sets.
	- Extended Sum Model Editor to Summation and Multiplication Editor.
	- Better compiling error captures in the 'New' model editor.
	- More outputs (e.g., Rg, background, or rod diameter) on LinearFit in certain axis scales.
	- Added DataInfo for data in the DataExplorer and plots
	- Added Maximize/Restore button in the title bar of the graphs
	- The 'x' button now works as deleting the graph
	- Added a hide button in the toolbar of the graph panel
	- Fixed some bugs and improved some behaviors in the batch/grid panel.
	- Edit SUM Model from the menubar can now generate more than one sum model.
	- Report can now be saved as a pdf format on WIN and MAC.
	- Multiprocessor support(Windows)
	- Simple custom model editor
	- Advanced model editor
	- Sum model editing panel 
	- 3D graphic (for 2d data/results) and legend moves with mouse
	- New Tool: density to vol fraction calculator and Python file editor
	- Batch Fit included.
	- More Graph modifications.
	- More options for the fit weighting.
	- Added a Python (PyCrust) shell in the 'Tool' menu.
	- The 'Startup Setting' in the View menu can remember the last data file folder.
	- Updated the resolution computation for the gravitational effect and added TOF estimation  capability.
	- Fixed the problem of displaying the fit results in the wrong parameter (with ParkMC FitEngine).
	- Pr Inversion: Fixed a missing Rg output
	- Startup Setting: fixed a problem with DataExplorer ON/OFF
	- Fixed a bug w/ 2D color map dialog
	- Minor feature added: Enable to load a data folder from the command line	
	- Much easier graphical user interface
	- Optimized for the speed and accuracy of the computations
	- Added Many shape, polymer, and other models including SphericalSLD, OnionExponetialShell, and even ReflectivityModels
	- Added Data Explorer to manage, plot, delete, or setup for computation
	- Added Instrumental resolution estimator (as a Tool)
	- Customizable Startup appearance
	- More functionalities on plot panels
	- Combined Modeling and Fitting
	- Save/open a SasView project or SasView analysis (subproject)
	- Start the SasView application from a data file by double-clicking or from command line
	- Easy manipulation of data and plot
	- Provides Normalized residual plot
	- Added useful key-combinations to copy (fitpage), paste (fitpage), change fit-tolerance, etc.
	- Report
	- 2D masked circular averaging
	- 2D smearing calculation now uses dQ_parrellel and dQ_perpendicular
	- Improved the speed of loading 2D data.
	- Improved the speed of P*S calculations.
	- Added 2D smearing calculation for dQx and dQy given along the x-y axes.
	- MAC release
  	- Implemented the invariant, volume fraction, and specific surface area computation.
	- Implemented the scattering length density calculator.
  	- Re-structured 2D calculation to 2D reduced(Q) data rather than raw pixel data
	- Capable of Mask enhanced 2D calculation and fitting.
	- Added a 2D mask data editor.
	- Added inputs for the slit and pinhole resolution.
	- Added a slit size calculator.
	- Support more format options to save a graph.
	- Enable to display multiple data sets in one graph by loading a data into the graph.
	- Added a tool bar in a plot panel.
  	- Implemented P(r) inversion (Indirect Fourier transformations).
	- Improved fitting and model calculation speed by a factor of ten.
  	- Supporting many more model functions.
	- Supporting P(Q)*S(Q) for most of the shape based form factors.
	- Added more distribution functions for the polydispersion calculations.
	- Added a bookmark feature so that the results of the calculation can be recalled later.
	- Q range reset button is added.
	- Added a color bar in 2D data plots.
	- Added a model function detail button for an easy access to the model help from the fitting panel.
	- Simultaneous fit of a number of different sets of data with/without the constraints. 
	- Loading and displaying 1D and 2D data of various formats.
	- 1D and 2D data fitting using Scipy or Park (a MC fitting optimizer) fit engine. 
	- 2D data manipulation and modeling. 
	- Supporting a number of standard model and model-independent functions including form factor and structure factor functions and their multiplications.  
	- Plug-in mechanism for data readers. 
	- Easy pop-up menu by mouse clicking on a given plot. 
	- Users arrange the various windows. 
	- Supporting varius 2D averaging methods : Circular, sectorslicer, annulus, boxsum, boxQx and boxQy.  
	- User defined Qrange (Qmin and Qmax) for both 1D and 2D data for fitting and modeling.  
	- The user can toggle between a number of different scales on all plots.
	- Support saving data in the formats of ASCII and xml.


2- Downloading and Installing
	
	*** Note: If you have EXE or ZIP SasView installer, you don't need any of the following.
	
	2.1- System Requirements:
		- Python version >= 2.5 and < 3.0 should be running on the system
		- We currently use Python 2.6

	2.2- Installing from source:
		- Get the code from https://sasviewproject.svn.sourceforge.net/svnroot/sansviewproject/releases/sasview-x.x.x
			- run 'python setup.py install' under the 'sasview-x.x.x' folder
			- run 'python sasview.py' under the 'sasview' folder.
		- The following modules are required (version numbers are what are used in the release build):
			- wxPython 2.8.12.1 (NOTE: do NOT use version 2.9)
			- matplotlib 1.1.0  (NOTE: Mac build is using version 1.0.1)
			- SciPy 0.10.1
			- pisa 3.0.27 (NOTE Mac Version uses 3.0.33 BUT -- DO NOT USE ver 3.0.33 on windows: it will not work!)
			- setuptools 0.6c11

			(The following three are easily installed using easy_install)
			- lxml 2.3.0
			- numpy 1.6.1 (NOTE: Mac build is using version 1.5.1)
			- periodictable 1.3.0

			(The following are additional dependencies for Mac)
			- py2app

			(The following are additional dependencies for Windows)
			- comtypes 0.6.2 (for PDF support on windows systems)
			- pywin32 build 217 (to read ms office)
			- pyPdf 1.13
			- html5lib 0.95
			- reportlab 2.5
			- pyparsing 1.5.5 (required for periodictable and bundling)
			- PIL 1.1.7 (Python Image Library)
			- py2exe 0.6.9 (WIN)
			- svn
			- MinGW w/ gcc version 4.6.1 (WIN)
			- Innosetup (WIN).

			(On Windows, the following site has all the dependencies nicely packaged)
			http://www.lfd.uci.edu/~gohlke/pythonlibs/


3- Known Issues

	3.1- All systems:
		- very old computers may not be able to run 

	3.2- Windows:
		- None
		
	3.3- MAC:
		- None
		
	3.4- Linux:
		- None

4- Troubleshooting

	- None

5- Frequently Asked Questions

	- None

6- Installer download website

	- http://sourceforge.net/projects/sansviewproject/files/
