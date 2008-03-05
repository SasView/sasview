Learning about wx.Panel and matplotlib... 


The following URL has an example of putting matplotlib plots in a wx panel:
	
	http://www.scipy.org/Matplotlib_figure_in_a_wx_panel


	
The code provided here is a (very) simplified version of how we do plots in 
SliceView using a Graph object containing many Plottable objects.

Main.py: 		Shows how to create the application

PlotPanel.py: 	PlotPanel is the base class for our plots.

Plotter1D: 		ModelPanel1D inherits from PlotPanel to show a single plot.
				Right-click to get the context menu and load a file to display.
				Notice the log-scale toggle in the context menu.
				
plottables.py: 	This file, written by Paul Kienzle, implements the Graph and Plottable classes.



Coding rules:

  - All function and class method names start with an lowercase letter.
  - All class names start with an uppercase.
  - Private methods start with an underline character (e.g. blah._myPrivateClass).
  - All functions, class methods and class should be documented with docstrings.
  - Never duplicate code. Write a function and re-use it.
  - Minimize the disk access. If you have data in memory. Store it in memory and
    transform it whenever you can rather than reloading it.
 
Interface style rules:
  - Always try to be consistent in the way you present options to users.
    (example: if you have a toggle option for an axis, try to do the same for
      other axes if you have the same number of options)
 
 