.. testdata_help.rst

Test Data
=========

Test data sets are included as a convenience to our users. Look in the \test 
sub-folder in your SasView installation folder.

The data sets are organized based on their data structure; 1D data, 2D data, 
SASVIEW saved states, and data in formats that are not yet implemented but 
which are in the works for future versions.

1D data sets have at least two columns of data with Intensity (assumed 
absolute units) on the Y-axis and Q on the X-axis. 

2D data sets are data sets that give the deduced intensity for each detector 
pixel. Depending on the file extension, uncertainty and meta data may also be 
available.

Saved states are projects and analyses saved by the SasView program. A single 
analysis file contains the data and parameters for a single fit (.fit), p(r) 
inversion (.pr), or invariant calculation (.inv). A project file (.svs) contains 
the results for every active analysis.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 17Jun2015
