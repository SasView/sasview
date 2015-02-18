.. data_explorer_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

Loading Data
============

Introduction_

Load_Data_

Handy_Menu_

Activate_Data_

Remove_Data_

Append_Plot_to_Graph_

Create_New_Plot_

Freeze_Theory_

Send_Data_to_Applications_

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Introduction:

Introduction
------------

*Data Explorer* is a panel that allows the user more interactions with data. 
Some functionalities provided by the *Data Explorer* are also available through 
the context menu of plot panels or other menus within the application.

Under *View* in the menu bar, *Data Explorer* can be toggled between Show and 
Hide by clicking *Show/Hide Data Explorer*.

*NOTE! When* Data Explorer *is hidden, all data loaded will be sent directly 
to the current active application, if possible. When* Data Explorer *is 
shown, data go first to the* Data Explorer.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Load_Data:

Load Data
---------

To load data, click the button *Load Data*, then select one or more (by holding 
the Ctrl key) files to load into the application. The name of each selected 
file will be listed.

Clicking the *+*  symbol will display any available metadata.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Handy_Menu:

Handy Menu
----------

Right-clicking on a loaded dataset (or model calculation, what SasView calls a 
theory) brings up a *Handy Menu* from which it is possible to access Datainfo, 
Save the data/theory, or Plot the data/theory.

.. image:: hand_menu.png

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Activate_Data:

Activate Data
-------------

To interact with data it must be activated. This is accomplished by checking 
the box next to the data label. A green tick will appear.

Unchecking/unticking the box deactivates a data set.

There is also a combo box labeled *Selection Options* from which you can 
activate or deactivate multiple data sets.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Remove_Data:

Remove Data
-----------

*WARNING!* Remove Data *will stop any data operations currently using the 
selected data sets.*

*Remove Data* removes all reference to selected data from the application.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Append_Plot_to_Graph:

Append Plot to Graph
--------------------

This operation can only be performed on 1D data and plot panels currently 
containing 1D data.

Click on the button *Append To* to add selected data to a plot panel. Next to 
the button is a combo box containing the names of available plot panels. 
Selecting a name from this combo box will move that plot into focus.
 
If a plot panel is not available, the combo box and button will be 
disabled.

2D Data cannot be appended to any plot panels.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Create_New_Plot:

Create New Plot
---------------

Click on the *New Plot* button to create a new plot panel where the currently 
selected data will be plotted.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Freeze_Theory:

Freeze Theory
-------------

The *Freeze Theory* button generates data from the selected theory.

*NOTE! This operation can only be performed when theory labels are selected.*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Send_Data_to_Applications:

Send to Application
-------------------

Click on the button *Send To* button to send the currently selected data to 
a perspective (for *Fitting*, *P(r) Inversion*, or *Invariant* calculation).
 
The *Single*/*Batch* mode radio buttons only apply to the *Fitting* perspective.

*Batch mode* provides serial (batch) fitting with one model function, that is, 
fitting one data set followed by another. If several data sets need to be 
fitted at the same time, use *Simultaneous* fitting under the *Fitting* 
option on the menu bar.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 18Feb2015
