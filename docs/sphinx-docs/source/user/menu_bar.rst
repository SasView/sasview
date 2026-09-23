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

- copy and paste parameters between *SasView* analysis windows;
- copy parameters from a *SasView* analysis window to the Clipboard as either tab-delimited text (compatible with Microsoft Excel) or LaTex-wrapped text;
- generate a summary 'Report' of the most recent analysis performed;
- reset parameter values in the P(r) Inversion analysis page;
- freeze/copy fit results as separate data sets.

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

- enable window cascading/tiling (windows detached from the workspace are not affected);
- move focus between windows both forward and backward, including detached windows;
- detach the active window from the workspace, or attach it back (see :ref:`detaching_windows`);
- minimize all plot windows;
- close all plot windows;
- access plots by name;

.. _detaching_windows:

Detaching windows from the workspace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Analysis perspectives, plots and panels such as the Batch Fitting Results normally open inside the
*SasView* workspace. Any of them can be detached into its own window, which can then be moved
anywhere on the desktop, for example onto a second monitor. A detached window keeps all of its
content and settings, and can be attached back to the workspace at any time.

To detach a window, do one of the following:

- drag the window by its title bar out of the workspace and release it; a thumbnail of the
  window follows the mouse and the window opens where you release it;
- click the icon at the top-left corner of the window and select *Detach from Workspace*;
- make the window active and select *Window > Detach Window from Workspace*, or press
  [Ctrl]-[Shift]-[D];
- for a plot, right-click on the plot and select *Detach from Workspace*.

To attach a detached window back to the workspace, do one of the following:

- drag the strip at the top of the detached window (the one holding its title and the
  *Attach to Workspace* button) onto the workspace and release it where you want the window;
  an outline shows where it will land;
- double-click that strip;
- click *Attach to Workspace* at the top-right of the detached window;
- make the window active and select *Window > Attach Window to Workspace*, or press
  [Ctrl]-[Shift]-[D];
- for a plot, right-click on the plot and select *Attach to Workspace*.

The strip at the top of a detached window is only for attaching. To move a detached window
around the desktop, drag its normal title bar.

When SasView opens, all perspectives are attached or detached, as selected in the general preferences,
and switching from one perspective to another may result in some perspectives being attached
and others detached.
Closing a detached analysis perspective minimises it, as in the workspace.
When you switch to another perspective and back, the perspective reappears where you left it,
attached or detached. Detached windows are closed when *SasView* exits; their placement is
not saved in project files.

New plots and perspectives can also be opened detached automatically. See :ref:`General_Preferences`.

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

.. note::  This help document was last changed by Piotr Rozyczko, 16 September 2026
