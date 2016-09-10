.. graph_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.


Plotting Data/Models
====================

SasView generates three different types of graph window: one that displays *1D data*
(ie, I(Q) vs Q), one that displays *1D residuals* (ie, the difference between the
experimental data and the theory at the same Q values), and *2D color maps*.

Graph window options
--------------------

.. _Invoking_the_graph_menu:

Invoking the graph menu
^^^^^^^^^^^^^^^^^^^^^^^

To invoke the *Graph Menu* simply right-click on a data/theory plot, or click
the *Graph Menu* (bullet list) icon in the toolbar at the bottom of the plot.
Then select a menu item.

How to Hide-Show-Delete a graph
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

.. note:: 
    *If a residuals graph (when fitting data) is hidden, it will not show up
    after computation.*

Dragging a plot
^^^^^^^^^^^^^^^

Select the *Pan* (crossed arrows) icon in the toolbar at the bottom of the plot
to activate this option. Move the mouse pointer to the plot. It will change to
a hand. Then left-click and drag the plot around. The axis values will adjust
accordingly.

To disable dragging mode, unselect the *crossed arrows* icon on the toolbar.

Zooming In-Out on a plot
^^^^^^^^^^^^^^^^^^^^^^^^

Select the *Zoom* (magnifying glass) button in the toolbar at the bottom of
the plot to activate this option. Move the mouse pointer to the plot. It will
change to a cross-hair. Then left-click and drag the pointer around to generate
a region of interest. Release the mouse button to generate the new view.

To disable zoom mode, unselect the *Zoom* button on the toolbar.

After zooming in on a a region, the *left arrow* or *right arrow* buttons on
the toolbar will switch between recent views.

The axis range can also be specified manually.  To do so go to the *Graph Menu*
(see Invoking_the_graph_menu_ for further details), choose the *Set Graph Range*
option and enter the limits in the pop box.

*NOTE! If a wheel mouse is available scrolling the wheel will zoom in/out
on the current plot (changing both axes). Alternatively, point at the numbers
on one axis and scroll the wheel to zoom in/out on just that axis.*

To return to the original view of the data, click the the *Reset* (home) icon
in the toolbar at the bottom of the plot (see Resetting_the_graph_ for further details).

Saving a plot image
^^^^^^^^^^^^^^^^^^^

To save the current plot as an image file, right click on the plot to bring up
the *Graph Menu* (see Invoking_the_graph_menu_) and select *Save Image*.
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
*  RAW/RGBA (bitmap, stored as 935x635 pixels of depth 8)
*  SVG/SVGA (scalable vector graphics)
*  TIF/TIFF (tagged iamge file)

Printing a plot
^^^^^^^^^^^^^^^

To send the current plot to a printer, click on the *Print* (printer) icon in
the toolbar at the bottom of the plot.

.. _Resetting_the_graph:

Resetting the graph
^^^^^^^^^^^^^^^^^^^

To reset the axis range of a graph to its initial values select *Reset Graph
Range* on the *Graph Menu* (see Invoking_the_graph_menu_). Alternatively, use
the *Reset* (home) icon in the toolbar at the bottom of the plot.

Modifying the graph
^^^^^^^^^^^^^^^^^^^

It is possible to make custom modifications to plots including:

*  changing the plot window title
*  changing the default legend location and toggling it on/off
*  changing the axis label text
*  changing the axis label units
*  changing the axis label font & font colour
*  adding/removing a text string
*  adding a grid overlay

The legend and text strings can be drag and dropped around the plot

These options are accessed through the *Graph Menu* (see Invoking_the_graph_menu_)
and selecting *Modify Graph Appearance* (for axis labels, grid overlay and
legend position) or *Add Text* to add textual annotations, selecting font, color,
style and size. *Remove Text* will remove the last annotation added. To change
the legend. *Window Title* allows a custom title to be entered instead of Graph
x. 

Changing scales
^^^^^^^^^^^^^^^

This menu option is only available with 1D data.

From the *Graph Menu* (see Invoking_the_graph_menu_) select *Change Scale*. A
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
levels, via a linear fit (see Making_a_linear_fit_).

Toggling scales
^^^^^^^^^^^^^^^

This menu option is only available with 2D data.

From the *Graph Menu* (see Invoking_the_graph_menu_) select *Toggle Linear/Log
Scale* to switch between a linear to log intensity scale. The type of scale
selected is written alongside the colour scale.

2D color maps
^^^^^^^^^^^^^

This menu option is only available with 2D data.

From the *Graph Menu* (see Invoking_the_graph_menu_) select *2D Color Map* to
choose a different color scale for the image and/or change the maximum or
minimum limits of the scale.

Getting data coordinates
^^^^^^^^^^^^^^^^^^^^^^^^

Clicking anywhere in the plot window will cause the current coordinates to be
displayed in the status bar at the very bottom-left of the SasView window.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Dataset menu options
--------------------

.. _Invoking_the_dataset_menu:

Invoking the dataset menu
^^^^^^^^^^^^^^^^^^^^^^^^^

From the *Graph Menu* (see Invoking_the_graph_menu_) highlight a plotted
dataset.

Getting data info
^^^^^^^^^^^^^^^^^

In the *Dataset Menu* (see Invoking_the_dataset_menu_), highlight a data set
and select *DataInfo* to bring up a data information dialog panel for that
data set.

Saving data
^^^^^^^^^^^

In the *Dataset Menu* (see Invoking_the_dataset_menu_), select *Save Points as
a File* (if 1D data) or *Save as a file(DAT)* (if 2D data). A save dialog will
appear.

1D data can be saved in either ASCII text (.TXT) or CanSAS/SASXML (.XML)
formats (see :ref:`Formats`).

2D data can only be saved in the NIST 2D format (.DAT) (see :ref:`Formats`).

.. _Making_a_linear_fit:

Making a linear fit
^^^^^^^^^^^^^^^^^^^

Linear fit performs a simple ( y(x)=ax+b ) linear fit within the plot window.

In the *Dataset Menu* (see Invoking_the_dataset_menu_), select *Linear Fit*. A
fitting dialog will appear. Set some initial parameters and data limits and
click *Fit*. The fitted parameter values are displayed and the resulting line
calculated from them is added to the plot.

This option is most useful for performing simple Guinier, XS Guinier, and
Porod type analyses, for example, to estimate Rg, a rod diameter, or incoherent
background level, respectively.

The following figure shows an example of a Guinier analysis using this option

.. image:: guinier_fit.png

Removing data from the plot
^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the *Dataset Menu* (see Invoking_the_dataset_menu_), select *Remove*. The
selected data will be removed from the plot.

.. note::
    The Remove data set action cannot be undone.

Show-Hide error bars
^^^^^^^^^^^^^^^^^^^^

In the *Dataset Menu* (see Invoking_the_dataset_menu_), select *Show Error Bar*
or *Hide Error Bar* to switch between showing/hiding the errors associated
with the chosen dataset.

Modify plot properties
^^^^^^^^^^^^^^^^^^^^^^

In the *Dataset Menu* (see Invoking_the_dataset_menu_), select *Modify Plot
Property* to change the size, color, or shape of the displayed marker for the
chosen dataset, or to change the dataset label that appears in the plot legend
box.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

2D data averaging
-----------------

Purpose
^^^^^^^

This feature is only available with 2D data.

2D data averaging allows you to perform different types of averages on your
data. The region to be averaged is displayed in the plot window and its limits
can be modified by dragging the boundaries around.

How to average
^^^^^^^^^^^^^^

In the *Dataset Menu* (see Invoking_the_dataset_menu_), select one of the
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

.. note::
    The displayed average only updates when input focus is moved back to
    that window; ie, when the mouse pointer is moved onto that plot.

Selecting *Box Sum* automatically brings up the 'Slicer Parameters' dialog in
order to display the average numerically, rather than graphically.

To remove a 'slicer', bring back the *Dataset menu* and select *Clear Slicer*.

Unmasked circular average
^^^^^^^^^^^^^^^^^^^^^^^^^

This operation will perform an average in constant Q-rings around the (x,y)
pixel location of the beam center.

Masked circular average
^^^^^^^^^^^^^^^^^^^^^^^

This operation is the same as 'Unmasked Circular Average' except that any
masked region is excluded.

Sector average [Q View]
^^^^^^^^^^^^^^^^^^^^^^^

This operation averages in constant Q-arcs.

The width of the sector is specified in degrees (+/- |delta|\|phi|\) each side
of the central angle (|phi|\).

Annular average [|phi| View]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This operation performs an average between two Q-values centered on (0,0),
and averaged over a specified number of pixels.

The data is returned as a function of angle (|phi|\) in degrees with zero
degrees at the 3 O'clock position.

Box sum
^^^^^^^

This operation performs a sum of counts in a 2D region of interest.

When editing the slicer parameters, the user can enter the length and the width
the rectangular slicer and the coordinates of the center of the rectangle.

Box Averaging in Qx
^^^^^^^^^^^^^^^^^^^

This operation computes an average I(Qx) for the region of interest.

When editing the slicer parameters, the user can control the length and the
width the rectangular slicer. The averaged output is calculated from constant
bins with rectangular shape. The resultant Q values are nominal values, that
is, the central value of each bin on the x-axis.

Box Averaging in Qy
^^^^^^^^^^^^^^^^^^^

This operation computes an average I(Qy) for the region of interest.

When editing the slicer parameters, the user can control the length and the
width the rectangular slicer. The averaged output is calculated from constant
bins with rectangular shape. The resultant Q values are nominal values, that
is, the central value of each bin on the x-axis.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last modified by Paul Butler, 05 September, 2016
