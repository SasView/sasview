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

*  $\chi^2$ (or 'Chi2'; pronounced 'chi-squared')
*  *Residuals*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Chi2
^^^^

$\chi^2$ is a statistical parameter that quantifies the differences between
an observed data set and an expected dataset (or 'theory') calculated as

.. math::

  \chi^2
  =  \sum[(Y_i - \mathrm{theory}_i)^2 / \mathrm{error}_i^2]

Fitting typically minimizes the value of $\chi^2$.  For assessing the quality of
the model and its "fit" however, *SasView* displays the traditional reduced
$\chi^2_R$ which normalizes this parameter by dividing it by the number of
degrees of freedom (or DOF). The DOF is the number of data points being
considered, $N_\mathrm{pts}$, reduced by the number of free (i.e. fitted)
parameters, $N_\mathrm{par}$. Note that model parameters that are kept fixed do
*not* contribute to the DOF (they are not "free"). This reduced value is then
given as

.. math::

  \chi^2_R
  =  \sum[(Y_i - \mathrm{theory}_i)^2 / \mathrm{error}_i^2]
  / [N_\mathrm{pts} - N_\mathrm{par}]

Note that this means the displayed value will vary depending on the number of
parameters used in the fit. In particular, when doing a calculation without a
fit (e.g. manually changing a parameter) the DOF will now equal $N_\mathrm{pts}$
and the $\chi^2_R$ will be the smallest possible for that combination of model,
data set, and set of parameter values.

When $N_\mathrm{pts} \gg N_\mathrm{par}$ as it should for proper fitting, the
value of the reduced $\chi^2_R$ will not change very much.

For a good fit, $\chi^2_R$ tends to 1.

$\chi^2_R$ is sometimes referred to as the 'goodness-of-fit' parameter.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Residuals
^^^^^^^^^

A residual is the difference between an observed value and an estimate of that
value, such as a 'theory' calculation (whereas the difference between an
observed value and its *true* value is its error).

*SasView* calculates 'normalized residuals', $R_i$, for each data point in the
fit:

.. math::

  R_i = (Y_i - \mathrm{theory}_i) / \mathrm{error}_i

Think of each normalized residual as the number of standard deviations
between the measured value and the theory.  For a good fit, 68% of $R_i$
will be within one standard deviation, which will show up in the Residuals
plot as $R_i$ values between $-1$ and $+1$.  Almost all the values should
be between $-3$ and $+3$.

Residuals values larger than $\pm 3$ indicate that the model
is not fit correctly, the wrong model was chosen (e.g., because there is
more than one phase in your system), or there are problems in
the data reduction.  Since the goodness of fit is calculated from the
sum-squared residuals, these extreme values will drive the choice of fit
parameters.  Any uncertainties calculated for the fitting parameters will
be meaningless.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

*Document History*

| 2015-06-08 Steve King
| 2017-09-28 Paul Kienzle
| 2018-03-04 Paul Butler