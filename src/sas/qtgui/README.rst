QtGUI
=====

This is a full rewrite of the Wx interface to SasView using Qt4 with PyQt4 bindings.

Running
-------
Compile UI resources first:

    cd src/sas/qtgui
    python convertUI.py

Run the GUI with:

    python run.py



Unit testing
------------

Unit testing suite can be run with

     python GUITesting.py


Requirements
------------

The following modules need to be additionally installed:

    Qt >= 4.8.0

    PyQt >= 4.10

    twisted >= 16.3

    qt4reactor >= 1.6

    unittest.mock >= 3.0

    qtconsole

    IPython


[SasView website](http://www.sasview.org)


