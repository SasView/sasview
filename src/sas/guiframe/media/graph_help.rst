.. graph_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

.. |delta| unicode:: U+03B4
.. |phi| unicode:: U+03C6


Plotting Data/Models
====================

Graph_Window_Options_

Dataset_Menu_Options_

2D_Data_Averaging_

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Graph_Window_Options:

Graph Window Options
--------------------

Invoking_the_Graph_Menu_

Hide_Show_Delete_Graph_

Drag_Plot_

Zoom_In_Out_

Save_Plot_Image_

Print_Plot_

Reset_Graph_

Graph_Modifications_

Change_Scale_

Toggle_Scale_

2D_Color_Map_

Data_Coordinates_

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Dataset_Menu_Options:

Dataset Menu Options
--------------------

Invoking_the_Dataset_Menu_

Data_Info_

Save_Data_

Linear_Fit_

Remove_Data_from_Plot_

Show_Hide_Error_Bars_

Modify_Plot_Property_

2D Averaging
------------

2D_Data_Averaging_

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Invoking_the_Graph_Menu:

Invoking the Graph Menu
-----------------------

To invoke the *Graph Menu* simply right-click on a data/theory plot, or click 
the *Graph Menu* (bullet list) icon in the toolbar at the bottom of the plot. 
Then select a menu item.

.. _Hide_Show_Delete_Graph:

Hide/Show/Delete Graph
----------------------

To expand a plot window, click the *Maximise* (square) icon in the top-right 
corner.

To shrink a plot window, click the *Restore down* (square-on-square) icon in 
the top-right corner.

To hide a plot, click the *Minimise* (-) icon in the top-right corner of the 
plot window.

To show a hidden plot, select the *Restore up* (square-on-square) icon on the 
minimised window.

To delete a plot, click the *Close* (x) icon in the top-right corner of the 
plot window.

*NOTE! If a residuals graph (when fitting data) is hidden, it will not show up 
after computation.*

.. _Drag_Plot:

Drag Plot
---------

Select the *Pan* (crossed arrows) icon in the toolbar at the bottom of the plot 
to activate this option. Move the mouse pointer to the plot. It will change to 
a hand. Then left-click and drag the plot around. The axis values will adjust 
accordingly.
 
To disable dragging mode, unselect the *crossed arrows* icon on the toolbar.

.. _Zoom_In_Out:

Zoom In/Out
-----------

Select the *Zoom* (magnifying glass) button in the toolbar at the bottom of 
the plot to activate this option. Move the mouse pointer to the plot. It will 
change to a cross-hair. Then left-click and drag the pointer around to generate 
a region of interest. Release the mouse button to generate the new view.

To disable zoom mode, unselect the *Zoom* button on the toolbar.

After zooming in on a a region, the *left arrow* or *right arrow* buttons on 
the toolbar will switch between recent views.

*NOTE! If a wheel mouse is available scrolling the wheel will zoom in/out 
on the current plot (changing both axes). Alternatively, point at the numbers 
on one axis and scroll the wheel to zoom in/out on just that axis.*

To return to the original view of the data, click the the *Reset* (home) icon 
in the toolbar at the bottom of the plot (see Reset_Graph_ for further details).

.. _Save_Plot_Image:

Save Plot Image
---------------

To save the current plot as an image file, right click on the plot to bring up 
the *Graph Menu* (see Invoking_the_Graph_Menu_) and select *Save Image*. 
Alternatively, click on the *Save* (floppy disk) icon in the toolbar at the 
bottom of the plot.
 
A dialog window will open. Select a folder, enter a filename, choose an output 
image type, and click *Save*.

The currently supported image types are:

*  EPS (encapsulated postscript)
*  EMF (enhanced metafile)
*  JPG/JPEG (joint photographics experts group)
*  PDF (portable documant format)
*  PNG (portable network graphics)
*  PS (postscript)
*  RAW/RGBA (bitmap)
*  SVG/SVGA (scalable vector graphics)
*  TIF/TIFF (tagged iamge file)

.. _Print_Plot:

Print Plot
----------

To send the current plot to a printer, click on the *Print* (printer) icon in 
the toolbar at the bottom of the plot.

.. _Reset_Graph:

Reset Graph
-----------

To reset the axis range of a graph to its initial values select *Reset Graph 
Range* on the *Graph Menu* (see Invoking_the_Graph_Menu_). Alternatively, use 
the *Reset* (home) icon in the toolbar at the bottom of the plot.

.. _Graph_Modifications:

Graph Modifications
-------------------

From the *Graph Menu* (see Invoking_the_Graph_Menu_) it is also possible to 
make some custom modifications to plots, including:

*  changing the plot window title
*  changing the axis legend locations
*  changing the axis legend label text
*  changing the axis legend label units
*  changing the axis legend label font & font colour
*  adding/removing a text string
*  adding a grid overlay

.. _Change_Scale:

Change Scale
------------

This menu option is only available with 1D data.

From the *Graph Menu* (see Invoking_the_Graph_Menu_) select *Change Scale*. A 
dialog window will appear in which it is possible to choose different 
transformations of the x (usually Q) or y (usually I(Q)) axes, including:

*  x, x^2, x^4, ln(x), log10(x), log10(x^4)
*  y, 1/y, ln(y), y^2, y.(x^4), 1/sqrt(y),
*  log10(y), ln(y.x), ln(y.x^2), ln(y.x^4), log10(y.x^4)
 
A *View* option includes short-cuts to common SAS transformations, such as:

*  linear
*  Guinier
*  X-sectional Guinier
*  Porod
*  Kratky

For properly corrected and scaled data, these SAS transformations can be used 
to estimate, for example, Rg, rod diameter, or SANS incoherent background 
levels, via a linear fit (see Linear_Fit_).

.. _Toggle_Scale:

Toggle Scale
------------

This menu option is only available with 2D data.

From the *Graph Menu* (see Invoking_the_Graph_Menu_) select *Toggle Linear/Log 
Scale* to switch between a linear to log intensity scale. The type of scale 
selected is written alongside the colour scale.

.. _2D_Color_Map:

2D Color Map
------------

This menu option is only available with 2D data.

From the *Graph Menu* (see Invoking_the_Graph_Menu_) select *2D Color Map* to 
choose a different color scale for the image and/or change the maximum or 
minimum limits of the scale.

.. _Data_Coordinates:

Data Coordinates
----------------

Clicking anywhere in the plot window will cause the current coordinates to be 
displayed in the status bar at the very bottom-left of the SasView window.
 
.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Invoking_the_Dataset_Menu:

Invoking_the_Dataset_Menu
-------------------------

From the *Graph Menu* (see Invoking_the_Graph_Menu_) highlight a plotted 
dataset.

.. _Data_Info:

Data Info
---------

In the *Dataset Menu* (see Invoking_the_Dataset_Menu_), highlight a data set 
and select *DataInfo* to bring up a data information dialog panel for that 
data set.

.. _Save_Data:

Save Data
---------

In the *Dataset Menu* (see Invoking_the_Dataset_Menu_), select *Save Points as 
a File* (if 1D data) or *Save as a file(DAT)* (if 2D data). A save dialog will 
appear.

1D data can be saved in either ASCII text (.TXT) or CanSAS/SASXML (.XML) 
formats (see :ref:`1D_Formats`).

2D data can only be saved in the NIST 2D format (.DAT) (see :ref:`2D_Formats`).

.. _Linear_Fit:

Linear Fit
----------

Linear fit performs a simple ( y(x)=ax+b ) linear fit within the plot window.

In the *Dataset Menu* (see Invoking_the_Dataset_Menu_), select *Linear Fit*. A 
fitting dialog will appear. Set some initial parameters and data limits and 
click *Fit*. The fitted parameter values are displayed and the resulting line 
calculated from them is added to the plot. 

This option is most useful for performing simple Guinier, XS Guinier, and
Porod type analyses, for example, to estimate Rg, a rod diameter, or incoherent 
background level, respectively.

The following figure shows an example of a Guinier analysis using this option

.. image:: guinier_fit.png

.. _Remove_Data_from_Plot:

Remove Data from Plot
---------------------

In the *Dataset Menu* (see Invoking_the_Dataset_Menu_), select *Remove*. The 
selected data will be removed from the plot.

*NOTE! This action cannot be undone.*

.. _Show_Hide_Error_Bars:

Show/Hide Error Bars
--------------------

In the *Dataset Menu* (see Invoking_the_Dataset_Menu_), select *Show Error Bar* 
or *Hide Error Bar* to switch between showing/hiding the errors associated 
with the chosen dataset. 

.. _Modify_Plot_Property:

Modify Plot Property
--------------------

In the *Dataset Menu* (see Invoking_the_Dataset_Menu_), select *Modify Plot 
Property* to change the size, color, or shape of the displayed marker for the 
chosen dataset, or to change the dataset label that appears on the plot.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _2D_Data_Averaging:

2D Data Averaging
-----------------

Purpose_

How_to_Average_

Available_Averagings_

Unmasked_Circular_Average_

Masked_Circular_Average_

Sector_Average_

Annular_Average_

Box_Sum_

Box_Averaging_in_Qx_

Box_Averaging_in_Qy_

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. Purpose: 

Purpose
-------

This feature is only available with 2D data.

2D data averaging allows you to perform different types of averages on your 
data. The region to be averaged is displayed in the plot window and its limits 
can be modified by dragging the boundaries around.

.. _How_to_Average:

How to Average
--------------

In the *Dataset Menu* (see Invoking_the_Dataset_Menu_), select one of the 
following averages

*  Perform Circular Average
*  Sector [Q view]
*  Annulus [Phi view]
*  Box sum
*  Box averaging in Qx
*  Box averaging on Qy

A 'slicer' will appear (except for *Perform Circular Average*) in the plot that 
you can drag by clicking on a slicer's handle. When the handle is highlighted 
in red, it means that the slicer can move/change size.

*NOTE! The slicer size will reset if you try to select a region greater than 
the size of the data.*

Alternatively, once a 'slicer' is active you can also select the region to 
average by bringing back the *Dataset Menu* and selecting *Edit Slicer 
Parameters*. A dialog window will appear in which you can enter values to 
define a region or select the number of points to plot (*nbins*).

A separate plot window will also have appeared, displaying the requested 
average.

*NOTE! The displayed average only updates when input focus is moved back to 
that window; ie, when the mouse pointer is moved onto that plot.*

Selecting *Box Sum* automatically brings up the 'Slicer Parameters' dialog in 
order to display the average numerically, rather than graphically.

To remove a 'slicer', bring back the *Dataset menu* and select *Clear Slicer*.

.. _Available_Averagings:

Available Averagings
--------------------

The available averages are

.. _Unmasked_Circular_Average:

Unmasked Circular Average
-------------------------

This operation will perform an average in constant Q-rings around the (x,y) 
pixel location of the beam center.

.. _Masked_Circular_Average:

Masked Circular Average
-----------------------

This operation is the same as 'Unmasked Circular Average' except that any 
masked region is excluded.

.. _Sector_Average:

Sector Average [Q View]
-----------------------

This operation averages in constant Q-arcs.

The width of the sector is specified in degrees (+/- |delta|\|phi|\) each side 
of the central angle (|phi|\).

.. _Annular_Average:

Annular Average [|phi| View]
----------------------------

This operation performs an average between two Q-values centered on (0,0), 
and averaged over a specified number of pixels.

The data is returned as a function of angle (|phi|\) in degrees with zero 
degrees at the 3 O'clock position.

.. _Box_Sum:

Box Sum
-------

This operation performs a sum of counts in a 2D region of interest.

When editing the slicer parameters, the user can enter the length and the width 
the rectangular slicer and the coordinates of the center of the rectangle.

.. _Box_Averaging_in_Qx:

Box Averaging in Qx
-------------------

This operation computes an average I(Qx) for the region of interest.

When editing the slicer parameters, the user can control the length and the 
width the rectangular slicer. The averaged output is calculated from constant 
bins with rectangular shape. The resultant Q values are nominal values, that 
is, the central value of each bin on the x-axis.

.. _Box_Averaging_in_Qy:

Box Averaging in Qy
-------------------


This operation computes an average I(Qy) for the region of interest.

When editing the slicer parameters, the user can control the length and the 
width the rectangular slicer. The averaged output is calculated from constant 
bins with rectangular shape. The resultant Q values are nominal values, that 
is, the central value of each bin on the x-axis.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 18Feb2015
