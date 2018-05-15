.. data_explorer_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

.. _Loading_data:

Loading Data
============

The data explorer
-----------------

*Data Explorer* is a panel that allows the user more interactions with data. 
Some functionalities provided by the *Data Explorer* are also available through 
the context menu of plot panels or other menus within the application.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Loading data
------------

To load data, do one of the following:

Select File -> Load Data File(s), and navigate to your data;

Select File -> Load Data Folder, which will attempt to load all the data in the
specified folder;

Drag and drop a file or multiple files from the external file explorer into
the Data Explorer area.

Or, in the *Data Explorer* click the button *Load Data*, then select one or more
(by holding down the Ctrl key) files to load into SasView.

The name of each loaded file will be listed in the *Data Explorer*. Clicking the
empty triangle symbol alongside will display any available metadata read from the file.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

The handy menu
--------------

Right-clicking on a loaded dataset (or model calculation, what SasView calls a 
'theory') brings up a *Handy Menu* from which it is possible to access *Data Info*,
*Save* the data/theory, *Delete* the data/theory or *Plot* the data/theory.

.. image:: hand_menu.png

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Activating data
---------------

To interact with data it must be activated. This is accomplished by checking 
the box next to the file name in the *Data Explorer*. A tick will appear.

Unchecking/unticking a box deactivates that data set.

There is also a combo box labeled *Selection Options* from which you can 
activate or deactivate multiple data sets in one go.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Removing data
-------------

*WARNING!* Remove Data *will stop any data operations currently using the 
selected data sets.*

*Delete Data* removes all references to selected data from SasView.

Right-clicking on one or more datasets also gives the option of removing 
the selected datasets.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Creating a new plot
-------------------

Click on the *Create New* button in the *Plot* section to create a new plot
panel where the currently selected data will be plotted.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Appending plots to a graph
--------------------------

This operation can currently only be performed on 1D data and plot panels
containing 1D data.

Click on the button *Append Plot To* to add selected data to a plot panel. Next
to the button is a combo box containing the names of available plot panels.
Selecting a name from this combo box will move that plot into focus.
 
If a plot panel is not available, the combo box and button will be 
disabled.

2D Data cannot be appended to any plot panels.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Freezing the theory
-------------------

The *Freeze Theory* button on the *Theory* tab page generates data from the selected theory.

*NOTE! This operation can only be performed when theory labels are selected in*
*the Data panel.*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Sending data to applications
----------------------------

Click on the *Send data TO* button to send the currently selected data to the currently
active analysis (*Fitting*, *P(r) Inversion*, or *Invariant* calculation).
 
The *Single*/*Batch* mode radio buttons only apply to *Fitting* and *P(r) Inversion*.

*Batch mode* provides serial (batch) fitting with one model function, that is, 
fitting one data set followed by another. If several data sets need to be 
fitted at the same time, use *Simultaneous* fitting under the *Fitting* 
option on the menu bar.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Piotr Rozyczko, 11May2018
