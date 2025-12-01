.. _InView_Documentation:

InView Documentation
=====================

.. toctree::
   :maxdepth: 1

qtgui/Perspectives/Fitting/inview

The 'InView' widget (Interactive View) is a tool that allows user to visualize in real-time how the model is changing when selected parameters are adjusted,
and to compare this changes with 1D experimental data.

Accessing InView 
----------------
By clicking button 'InView' in Fitting, InView widget window is opened. This button is disabled in case of Batch fitting (REF) and when 2D option in Fitting is selected. 
The InView window is divided into two sections, InvView and Sliders.

.. image:: FittingWidget_marked.png

How to use
----------
After sending data into Fitting and choosing the model, one has to tick desired parameters and open the InView window.
Next to the interactive plot, one would see sliders for each parameter that has been previously selected. Once the model is satisfactory, it can be send back to Fitting
via 'Update fitted parameters'.

.. image:: InViewWindow.png