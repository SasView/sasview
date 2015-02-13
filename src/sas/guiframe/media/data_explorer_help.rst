.. _data_explorer_help.rst

Loading Data
============

Introduction_ 
Load data_
Handy menu_
Activate data_
Remove data_
Append plot to graph_
Create new plot_
Freeze theory_
Send data to applications_

.. _Introduction : 
------------------
*Data Explorer*  is a panel that allows the user more interactions with data. Some functionalities provided by the Data Explorer are also available through the context menu of plot panels or other menus of the applications.Under menu *View*  of the menubar, Data explorer can be toggled between Show and Hide by clicking the menu *Show/Hide Data Explorer* .

*IMPORTANT!*  When Data explorer is hidden, all the data loaded will be sent directly to the current active application, if possible. When data Explorer is shown data go first to the Data Explorer for the user to handle them later.

.. _Load data : 
---------------
To Load data, click the button *Load Data* , then select one or more (holding Ctrl key) files to load into the application. In the list, the *Data*  will be displayed as the name of each selected file. Expending this data by clicking the *+*  symbol will display available information about the data such as data title if exists.

.. _Handy menu : 
----------------
For a quick Data-info/Save/Plot/3d-plot(2d only)/Edit-mask(2d only), high-light the data/theory, right-click, and select a proper item from the context menu.
.. _ image:: hand_menu.png


.. _Activate data : 
-------------------
To interact with data, check a data label and click on a button. Checking Data make them active for the button operation. Unchecking Data labels will deactivate them.

There is a combo box labeled *Selection Options*  that allows to activate or select multiple data simultaneously.

.. _Remove data : 
-----------------
Remove data button remove all reference of this data into the application.

*WARNING!* Remove data will stop any jobs currently using the selected data.

.. _Append plot to graph : 
--------------------------
Click on the button *Append To*  to append selected Data to a plot panel on focus. Next to this button is a combo box containing available panels names. Selecting a name from this combo box will set the corresponding lot panel on focus. If not plot panel is available, the combo box and button will be disable. 2D Data cannot be appended to any plot panels . This operation can only be performed on 1D data and plot panels currently containing 1D data.

.. _Create new plot : 
---------------------
Click on *New Plot*  button to create a new plot panel where selected data will be plotted.

.. _Freeze theory : 
-------------------
*Freeze Theory*  button generate Data from selected theory. This operation can only be performed when theory labels are selected.

.. _Send to application : 
-------------------------
Click on the button *Send To*  to send Data to the current active control page. One of the single/batch mode can be selected only for Fitting. The batch mode provides serial (batch) fitting with one model, i.e., fitting one data by another data. Note that only the Fitting allows more that one data to be sent.

