.. _menu_bar:

Menu Bar
========
The menu bar at the top of the *SasView* window gives you access to additional features of the program:

File
----
The File option allows you load data into *SasView* for analysis, or to save the work you have been doing.

Data can be loaded one file at a time, or by selecting multiple files, or by loading an entire folder of 
files (in which case *SasView* will attempt to make an intelligent guess as to what to load based on the 
file formats it recognises in the folder!). Data can also be loaded by dragging and dropping files directly
onto Data Explorer.

A *SasView* session can also be saved and reloaded as an 'Analysis' (an individual model fit or invariant 
calculation, etc), or as a 'Project' (everything you have done since starting your *SasView* session).
Finally, a session can be closed so a new project can be created. This will clear all plots, data and
content in all the perspectives, even those which are not currently visible.

Edit
----
The Edit option allows you to:

- undo the most recent parameter change (``Ctrl+Z``);
- redo a previously undone parameter change (``Ctrl+Y``);
- copy and paste parameters between *SasView* analysis windows;
- copy parameters from a *SasView* analysis window to the Clipboard as either tab-delimited text (compatible with Microsoft Excel) or LaTex-wrapped text;
- generate a summary 'Report' of the most recent analysis performed;
- reset parameter values in the P(r) Inversion analysis page;
- freeze/copy fit results as separate data sets.

The **Undo** and **Redo** commands are also available as buttons in the
main toolbar, and their tooltips dynamically show which action will be
reverted (e.g. "Undo Change radius").

Undo/Redo is supported in the following perspectives:

- **Model Fitting** – parameter changes in individual fit pages;
- **P(r) Inversion** – parameter changes in each inversion page;
- **Invariant** – parameter changes in the invariant calculator;
- **Size Distribution** – parameter changes in the size distribution
  calculator;
- **Correlation Function** – parameter changes in the correlation
  function analysis.

Each tab or page maintains its own independent undo history, so
switching between perspectives or fit pages preserves the undo/redo
state of each. The default history depth is 200 actions per tab,
configurable via the ``UNDO_STACK_MAX_DEPTH`` setting in
:file:`src/sas/system/config/config.py`.

.. note:: Undo/Redo is automatically suppressed during programmatic
          operations such as loading a project or applying fit results,
          to prevent spurious entries from cluttering the undo history.

View
----
The View option allows you to:

- show the Batch Fitting Results Panel if it has been closed;
- show/hide the Toolbar of icons below the Menu Bar;

Tools
-----
The Tools option provides access to a comprehensive range of tools and utilities. See :ref:`tools` for more information.

Window
------
The Window option allows you to select which *SasView* windows are visible;

- enable window cascading/tiling;
- move focus between windows both forward and backward;
- minimize all plot windows;
- close all plot windows;
- access plots by name;

Analysis
--------
The Analysis option provides access to the key functionality of *SasView*:

- Model Fitting;
- P(r) Inversion;
- Invariant Analysis;
- Correlation Function Analysis (*SasView* 4.1 and later)

See :ref:`analysis` for more information.

Fitting
-------
The Fitting option allows you to:

- create a new FitPage;
- setting up a Constrained or Simultaneous Fit;
- change optimiser (under Fit Options);
- view fit parameter correlations, distributions, and convergence traces (under Fit Results);
- manage model categories;
- create a Plugin Model;
- edit a Plugin Model;
- manage Plugin Models;
- create a Sum/Multiple Plugin Model.
 

Help
----
The Help option provides access to:

- this help documentation;
- a :ref:`tutorial` on using *SasView* (in pdf format);
- information on how to acknowledge *SasView* in publications;
- information about the version of *SasView* you are using;
- the :ref:`marketplace`\ ;
- a check to see if there is a more recent version of *SasView*.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Piotr Rozyczko, 10 May 2019
