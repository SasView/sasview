.. fitting_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

.. |beta| unicode:: U+03B2
.. |gamma| unicode:: U+03B3
.. |mu| unicode:: U+03BC
.. |sigma| unicode:: U+03C3
.. |phi| unicode:: U+03C6
.. |theta| unicode:: U+03B8
.. |chi| unicode:: U+03C7

.. |inlineimage004| image:: sm_image004.gif
.. |inlineimage005| image:: sm_image005.gif
.. |inlineimage008| image:: sm_image008.gif
.. |inlineimage009| image:: sm_image009.gif
.. |inlineimage010| image:: sm_image010.gif
.. |inlineimage011| image:: sm_image011.gif
.. |inlineimage012| image:: sm_image012.gif
.. |inlineimage018| image:: sm_image018.gif
.. |inlineimage019| image:: sm_image019.gif


Fitting Perspective
===================

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Preparing to fit data
---------------------

To fit some data you must first load some data, activate one or more data sets,
send those data sets to the fitting perspective, and select a model to fit to
each data set.

Instructions on how to load and activate data are in the section :ref:`Loading_data`.

SasView can fit data in one of three ways:

*  in *Single* fit mode - individual data sets are fitted independently one-by-one

*  in *Simultaneous* fit mode - multiple data sets are fitted simultaneously to the *same* model with/without constrained parameters (this might be useful, for example, if you have measured the same sample at different contrasts)

*  in *Batch* fit mode - multiple data sets are fitted sequentially to the *same* model (this might be useful, for example, if you have performed a kinetic or time-resolved experiment and have *lots* of data sets!)

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Selecting a model
-----------------

By default, the models in SasView are grouped into five categories

*  *Shapes* - models describing 'objects' (spheres, cylinders, etc)
*  *Shape-Independent* - models describing structure in terms of density correlation functions, fractals, peaks, power laws, etc
*  *Customized Models* - SasView-created (non-library) Python models
*  *Uncategorised* - other models (for reflectivity, etc)
*  *Structure Factor* - S(Q) models

Use the *Category* drop-down menu to chose a category of model, then select
a model from the drop-down menu beneath. A graph of the chosen model, calculated
using default parameter values, will appear. The graph will update dynamically
as the parameter values are changed.

You can decide your own model categorizations using the :ref:`Category_Manager`.

Once you have selected a model you can read its help documentation by clicking
on the *Description* button to the right.

Show 1D/2D
^^^^^^^^^^

Models are normally fitted to 1D (ie, I(Q) vs Q) data sets, but some models in
SasView can also be fitted to 2D (ie, I(Qx,Qy) vs Qx vs Qy) data sets.

*NB: Magnetic scattering can only be fitted in SasView in 2D.*

To activate 2D fitting mode, click the *Show 2D* button on the *Fit Page*. To
return to 1D fitting model, click the same button (which will now say *Show 1D*).

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Category_Manager:

Category Manager
----------------

To change the model categorizations, either choose *Category Manager* from the
*View* option on the menubar, or click on the *Modify* button on the *Fit Page*.

.. image:: cat_fig0.bmp

The categorization of all models except the customized models can be reassigned,
added to, and removed using *Category Manager*. Models can also be hidden from view
in the drop-down menus.

.. image:: cat_fig1.bmp

Changing category
^^^^^^^^^^^^^^^^^

To change category, highlight a model in the list by left-clicking on its entry and
then click the *Modify* button. Use the *Change Category* panel that appears to make
the required changes.

.. image:: cat_fig2.bmp

To create a category for the selected model, click the *Add* button. In order
to delete a category, select the category name and click the *Remove Selected*
button. Then click *Done*.

Showing/hiding models
^^^^^^^^^^^^^^^^^^^^^

Use the *Enable All/Disable All* buttons and the check boxes beside each model to
select the models to show/hide. To apply the selection, click *Ok*. Otherwise click
*Cancel*.

*NB: it may be necessary to change to a different category and then back again*
*before any changes take effect.*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Model Functions
---------------

For a complete list of all the library models available in SasView, see the section
:ref:`SasView_model_functions`.

It is also possible to add your own models.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Adding your own models
----------------------

There are currently two ways to add your own models to SasView:

* using the :ref:`Custom_Model_Editor`
* by :ref:`Writing_a_Plugin`

*NB: Because of the way these options are implemented, it is not possible for them*
*to use the polydispersity algorithms in SasView. Only models in the model library*
*can do this. At the time of writing (Release 3.1.0) work is in hand to make it*
*easier to add new models to the model library.*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Custom_Model_Editor:

Custom Model Editor
-------------------

From the *Fitting* option in the menu bar, select *Edit Custom Model*.

.. image:: edit_model_menu.bmp

and then one of the options

*  *New* - to create a new custom model template
*  *Sum|Multi(p1,p2)* - to create a new model by summing/multiplying existing models in the model library
*  *Advanced* - to edit a new custom model
*  *Delete* - to delete a custom model

New
^^^^

.. image:: new_model.bmp

A model template generated by this option can be viewed and further modified using
the :ref:`Advanced` option.

Sum|Multi(p1,p2)
^^^^^^^^^^^^^^^^

.. image:: sum_model.bmp

This option creates a custom model of the form

Custom Model = scale_factor * (model1 +/* model2)

In the *Easy Sum/Multi Editor* give the new custom model a function name and brief
description (to appear under the *Details* button on the *Fit Page*). Then select
two existing models, as p1 and p2, and the required operator, '+' or '*' between
them. Finally, click the *Apply* button to generate the model and then click *Close*.

*NB: Any changes to a custom model generated in this way only become effective after*
*it is re-selected from the model drop-down menu on the Fit Page.*

.. _Advanced:

Advanced
^^^^^^^^

Selecting this option shows all the custom models in the plugin model folder

C:\Users\[username]\.sasview\plugin_models - (on Windows)

You can edit, modify, and save the Python code in any of these models using the
*Advanced Custom Model Editor*.

*NB: Unless you are confident about what you are doing, it is recommended that you*
*only modify lines denoted with the ## <----- comments!*

When editing is complete, select *Run -> Compile* from the *Model Editor* menu bar. An
*Info* box will appear with the results of the compilation and model unit tests. The
model will only be usable if the tests 'pass'.

To use the model, go to the relevant *Fit Page*, select the *Customized Models*
category and then select the model from the drop-down menu.

*NB: Any changes to a custom model generated in this way only become effective after*
*it is re-selected from the model drop-down menu on the Fit Page.*

Delete
^^^^^^

Simply highlight the custom model to be removed. This operation is final!

*NB: Custom models shipped with SasView cannot be removed in this way.*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Writing_a_Plugin:

Writing a Plugin
----------------

Advanced users can write their own model in Python and save it to the the SasView
*plugin_models* folder

C:\Users\[username]\.sasview\plugin_models - (on Windows)

in .py format. The next time SasView is started it will compile the plugin and add
it to the list of *Customized Models*.

It is recommended that existing plugin models be used as templates.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Fitting_Options:

Fitting Options
---------------

It is possible to specify which optimiser SasView should use to fit the data, and
to modify some of the configurational parameters for each optimiser.

From *Fitting* in the menu bar select *Fit Options*, then select one of the following
optimisers:

*  DREAM
*  Levenberg-Marquardt
*  Quasi-Newton BFGS
*  Differential Evolution
*  Nelder-Mead Simplex

These optimisers form the *Bumps* package written by P Kienzle. For more information
on each optimiser, see the :ref:`Fitting_Documentation`.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Shortcuts
---------

Copy/Paste Parameters
^^^^^^^^^^^^^^^^^^^^^

It is possible to copy the parameters from one *Fit Page* and to paste them into
another *Fit Page* using the same model.

To *copy* parameters, either:

*  Select *Edit -> Copy Params* from the menu bar, or
*  Use Ctrl(Cmd on Mac) + Left Mouse Click on the *Fit Page*.

To *paste* parameters, either:

*  Select *Edit -> Paste Params* from the menu bar, or
*  Use Ctrl(Cmd on Mac) + Shift + Left-click on the *Fit Page*.

If either operation is successful a message will appear in the info line at the
bottom of the SasView window.

Bookmark
^^^^^^^^

To *Bookmark* a *Fit Page* either:

*  Select a *Fit Page* and then click on *Bookmark* in the tool bar, or
*  Right-click and select the *Bookmark* in the popup menu.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Status_bar:

Status Bar & Console
--------------------

The status bar is located at the bottom of the SasView window and displays
messages, hints, warnings and errors.

At the right-hand side of the status bar is a button marked *Console*. The *Console*
displays available message history and some run-time traceback information.

During a long task the *Console* can also be used to monitor the progress.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Single Fit Mode
---------------

*NB: Before proceeding, ensure that the Single Mode radio button at the bottom of*
*the Data Explorer is checked (see the section* :ref:`Loading_data` *).*

When data is sent to the fitting perspective it is plotted in a graph window as
markers.

If a graph does not appear, or a graph window appears but is empty, then the data
has not loaded correctly. Check to see if there is a message in the :ref:`Status_Bar`
or in the *Console* window.

Assuming the data has loaded correctly, when a model is selected a green model
calculation (or what SasView calls a 'Theory') line will appear in the earlier graph
window, and a second graph window will appear displaying the residuals (the
difference between the experimental data and the theory) at the same X-data values.

The objective of model-fitting is to find a *physically-plausible* model, and set
of model parameters, that generate a theory that reproduces the experimental data
and gives residual values as close to zero as possible.

Change the default values of the model parameters by hand until the theory line
starts to represent the experimental data. Then uncheck the tick boxes alongside
all parameters *except* the 'background' and the 'scale'. Click the *Fit* button.
SasView will optimise the values of the 'background' and 'scale' and also display
the corresponding uncertainties on the optimised values.

*NB: If no uncertainty is shown it generally means that the model is not very*
*dependent on the corresponding parameter (or that one or more parameters are*
*'correlated').*

In the bottom left corner of the *Fit Page* is a box displaying the normalised value
of the statistical |chi|\  :sup:`2` parameter returned by the optimiser.

Now check the box for another model parameter and click *Fit* again. Repeat this
process until most or all parameters are checked and have been optimised. As the
fit of the theory to the experimental data improves the value of 'chi2/Npts' will
decrease. A good model fit should easily produce values of 'chi2/Npts' that are
close to zero, and certainly <100.

SasView has a number of different optimisers (see the section :ref:`Fitting_Options`).
The DREAM optimiser is the most sophisticated, but may not necessarily be the best
option for fitting simple models. If uncertain, try the Levenberg-Marquardt optimiser
initially.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Simultaneous Fit Mode
---------------------

This fitting option enables to set a number of the constraints between the 
parameters of fitting(s). It requires one or more FitPages with a data and a 
model set for the fitting, and performs multiple fittings given by the 
FitPage(s). The Complex (ParkMC) FitEngine will be used automatically.

Simultaneous Fit without Constraint

Assuming some FitPages are already set up, check the checkboxes of the 
model_data rows to fit. And click the 'Fit' button. The results will return to 
each FitPages.

Note that the chi2/Npts returned is the sum of the chi2/Npts of each fits. If 
one needs the chi2 value only for a page, click the 'Compute' button in the 
FitPage to recalculate.

Simultaneous Fit with Constraint

Enter constraint in the text control next to *constraint fit*  button. 
Constraint should be of type model1 parameter name = f(model2 parameter name) 
for example, M0.radius=2*M1.radius. Many constraints can be entered for a 
single fit. Each of them should be separated by a newline charater or ";" 
The easy setup can generate many constraint inputs easily when the selected 
two models are the same type.

Note that the chi2/Npts returned is the sum of the chi2/Npts of each fits. 
If one needs the chi2 value only for one fit, click the 'Compute' button in 
the FitPage to recalculate.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Batch Fit Mode
--------------

Batch Fit
^^^^^^^^^

Create a *Batch Page* by selecting the *Batch* radio button on the DataExplorer
(see figure below) and for a new control page select 'New FitPage' in the 
Fitting menubar.

.. image:: batch_button_area.bmp

Figure 1: MenuBar: 

Load Data to the DataExplorer if not already loaded.

Select one or more data sets by checking the check boxes, and then make sure 
that "Fitting" is selected in the dropdown menu next to the "Send To" button. 
Once ready, click the 'Send To' button to set data to a BatchPage. If already 
an empty batch page exists, it will be set there. Otherwise it will create a 
new Batch Page. Set up the model and the parameter values as same as a single 
fitting (see Single Fit help). Then use 'Fit' button to
perform the fitting.

Unlike a single fit, the results of the fittings will not return to the 
BatchPage'. Instead, a Grid window will be provided once the fitting is 
completed. The Grid window is also accessible from the 'View' menu 
(see Figure 2).

Note that only one model is used for all the data. The initial parameter 
values given in the control page will be used all the data fittings. If one 
wants the FitEngine to use the initial values from the results of the 
previous data fitting (if any), choose the 'Chain Fitting' option in the 
Fitting menubar, which will speed up the fitting especially when you have 
lots of, and similar, data sets.

Batch Window
^^^^^^^^^^^^
Batch Window provides an easy way to view the fit results, i.e., plot data, 
fits, and residuals. Batch window will be automatically shown after a batch 
fit is finished.

Once closed, it can be opened anytime from the "View" menubar item (see 
Figure 2).

.. image:: restore_batch_window.bmp

Figure 2: Edit Menu: 

Edit Grid
^^^^^^^^^

Once a batch fit is completed, all fitted and fixed model parameters are 
displayed to the current sheet of the batch window except the errors of the 
parameters. To view the errors, click on a given column then under *Edit*  
menubar item, and insert the desired parameter by selecting a menu item with 
the appropriated label. Empty column can be inserted in the same way. A 
column value can be customized by editing an existing empty column.

To Remove column from the grid, select it, choose edit menu, and click the 
*'remove'*  menu item. Any removed column should reinserted whenever needed.

All above options are also available when right clicking on a given column 
label(see Figure 3).

*Note:*  A column always needs to be selected in order to remove or insert a 
column in the grid.

.. image:: edit_menu.bmp

Figure 3: Edit Menu:

Save Grid
^^^^^^^^^
To save the current page on the batch window, select the *'File'*  menubar 
item(see Figure 4), then choose the *'Save as'*  menu item to save it as a 
.csv file.

*Note:* The grid doesn't save the data array, fits, and the array residuals.
As a result, the 'View (fit) Results' functionality will be lost when
reloading the saved file.

Warning! To ensure accuracy of saved fit results, it is recommended to save 
the current grid before modifying it .

Open Batch Results
^^^^^^^^^^^^^^^^^^

Any *csv*  file can be opened in the grid by selecting the *'Open'*  under 
the *'File'*  menu in the Grid Window(see Figure 4). All columns in the file 
will be displayed but insertion will not available. Insertion will be 
available only when at least one column will be removed from the grid.

.. image:: file_menu.bmp

Figure 4: MenuBar:

Plot
^^^^

To *plot*  a column versus another, select one column at the time, click the 
*'Add'*  button next to the text control of X/Y -axis *Selection Range*  to 
plot the value of this column on the X/Y axis. Alternatively, all available 
range can be selected by clicking the column letter (eg. B). Repeat the same 
procedure the next axis. Finally, click the *'Plot'*  button. When clicking 
on *Add*  button, the grid will automatically fill the axis label, but 
different labels and units can be entered in the correct controls before 
clicking on the plot button.

*X/Y -Axis Selection Range* can be edited manually. These text controls
allow the following types of expression (operation can be + - * /, or pow)
 
1) if the current axis label range is a function of 1 or more columns, write 
this type of expression

constant1  * column_name1 [minimum row index :  maximum  row index] operator 
constant2 * column_name2 [minimum row index :  maximum  row index] 

Example: radius [2 : 5] -3 * scale [2 : 5] 

2) if only some values of a given column are need but the range between the 
first row and the last row used is not continuous, write the following 
expression in the text control

column_name1 [minimum row index1 :  maximum  row index1] , column_name1 
[minimum row index2 :  maximum  row index2] 

Example : radius [2 : 5] , radius [10 : 25] 

Note: Both text controls ( X and Y-axis Selection Ranges) need to be filled 
with valid entries for plotting to work. The dY-bar is optional (see Figure 5).

.. image:: plot_button.bmp

Figure 5: Plotting

View Column/Cell(s)
^^^^^^^^^^^^^^^^^^^

Select 1 or more cells from the same column, click the 'View Fits' button to 
display available curves. 

For example, select the cells of the  'Chi2'  column, then click the  'View Fits'  
button. The plots generates will represent the residuals  plots. 
 
If you select any cells of the 'Data' column and click the 'View Fits' button. 
It generates both  data and fits in the graph (see Figure 6). 

Alternatively, just click the column letter (eg. B) to choose all the 
available data sets, then simply click the 'View Fits' button to plot the 
data and fits. 

.. image:: view_button.bmp

Figure 6: View Fits

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
