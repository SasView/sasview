.. residuals_help.rst


.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Assessing_Fit_Quality:

Assessing Fit Quality
---------------------

When performing model-fits to some experimental data it is helpful to be able to
gauge how good an individual fit is, how it compares to a fit of the *same model*
*to another set of data*, or how it compares to a fit of a *different model to the*
*same data*.

One way is obviously to just inspect the graph of the experimental data and to
see how closely (or not!) the 'theory' calculation matches it. But *SasView*
also provides two other measures of the quality of a fit:

*  |chi|\  :sup:`2` (or 'Chi2'; pronounced 'chi-squared')
*  *Residuals*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Chi2
^^^^

Chi2 is a statistical parameter that quantifies the differences between an observed
data set and an expected dataset (or 'theory').

*SasView* actually returns this parameter normalized to the number of data points,
*Npts* such that

  *Chi2/Npts* = { SUM[(*Y_i* - *Y_theory_i*)^2 / (*Y_error_i*)^2] } / *Npts*

This differs slightly from what is sometimes called the 'reduced chi-squared'
because it does not take into account the number of fitting parameters (to
calculate the number of 'degrees of freedom'), but the 'normalized chi-squared'
and the 'reduced chi-squared' are very close to each other when *Npts* >> number of
parameters.

For a good fit, *Chi2/Npts* tends to 0.

*Chi2/Npts* is sometimes referred to as the 'goodness-of-fit' parameter.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Residuals
^^^^^^^^^

A residual is the difference between an observed value and an estimate of that
value, such as a 'theory' calculation (whereas the difference between an observed
value and its *true* value is its error).

*SasView* calculates 'normalized residuals', *R_i*, for each data point in the
fit:

  *R_i* = (*Y_i* - *Y_theory_i*) / (*Y_err_i*)

For a good fit, *R_i* ~ 0.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 08Jun2015
