.. _corfunc-how-to:

How to use Corfunc
==================

Running a Calculation
---------------------

Upon sending data for correlation function analysis, it will be plotted (minus
the background value), along with a bar indicating the *upper end of the
low-Q range* (used for Guinier back-extrapolation), and 2 bars indicating
the range to be used for Porod forward-extrapolation. These bars may be moved by
entering appropriate values in the Q range input boxes or by clicking on them and
dragging them to the desired location..

.. figure:: tutorial1.png
   :align: center

Once the Q ranges have been set, click the "Calculate" button in the *Background* section
of the dialog to determine the background level.
Alternatively, enter your own value into the box. If the box turns
yellow this indicates that background subtraction has created some negative intensities.

Now click the "Extrapolate" button to extrapolate the data. The graph window will update
to show the extrapolated data, and the values of the parameters used for the Guinier and
Porod extrapolations will appear in the "Extrapolation Parameters" section of the Corfunc
GUI.

.. figure:: tutorial2.png
   :align: center

Now click the "Transform" button to perform the Fourier transform and plot
the results. The lower graph will display the 1D and 3D-averaged correlation functions.
The Interface Distribution Function (or IDF) is also computed, but is not displayed
for clarity. How to access the IDF, and the correlation functions themselves, is
explained shortly.

 .. figure:: tutorial3.png
    :align: center

*If* the sample morphology can be adequately described as an ideal lamellar morphology
the Corfunc GUI can attempt to derive morphological characterization parameters from the
1D correlation function. To do this, click the "Extract Parameters" button.

 .. figure:: tutorial4.png
    :align: center

Finally, it is possible to save the values of the real-space distance axis, the 1D and 3D
correlation functions, and the IDF to a simple ASCII text file by clicking on the "Save"
button. The file is given the unique file descriptor *.crf*.

 .. figure:: tutorial5.png
    :align: center

The structure of the file is shown below.

 .. figure:: tutorial6.png
    :align: center

.. note:: At the time of writing SasView will not load these *.crf* files, but they can
   be easily loaded and displayed in most spreadsheet applications.

.. note::
    This help document was last changed by Steve King, 21May2020


