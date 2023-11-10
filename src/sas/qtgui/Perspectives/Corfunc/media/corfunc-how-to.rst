.. _corfunc-how-to:

How To Use Corfunc
==================

Running a Calculation
---------------------

Upon sending data for correlation function analysis, it will be plotted (minus
the background value), along with a bar indicating the upper end of the
low-Q range (used for Guinier back-extrapolation) and 2 bars indicating
the range to be used for Porod forward-extrapolation.

This information is also shown on the orange and green interactive slider on the left.
You can drag bars on this left-hand plot, or enter values manually.

.. figure:: tutorial_data_loaded.png
   :align: center

Once the Q ranges have been set, click the "Go" button to run the analysis.
This will run through the process described in the technical documentation.

The parameters used along the way can be overriden by changing them in the appropriate text boxes,
and whether or not they are recalculated is controlled by the check boxes.

Output
------

When the calculation is complete, the extrapolated curve will be shown on the Q-space plot.

 .. figure:: tutorial_after_go.png
    :align: center

The `Real Space` tab shows plots of :math:`\Gamma_1` and :math:`\Gamma_3`

 .. figure:: tutorial_real_space.png
    :align: center

To check the extrapolation parameters, a diagram shows the geometric construction used to
derive them in the `Extraction Diagram` tab.

 .. figure:: tutorial_extraction.png
    :align: center

Finally, you can see the interface distribution function in the `IDF` tab

 .. figure:: tutorial_idf.png
    :align: center

The export buttons allow you to produce .csv files containing either the extrapolated
Q-space data, or the transformed data.

The structure of the transformed data file is shown below.

 .. figure:: tutorial_export_data.png
    :align: center


