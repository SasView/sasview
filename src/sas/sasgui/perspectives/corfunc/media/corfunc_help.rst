.. corfunc_help.rst

Correlation Function Perspective
================================

Description
-----------

This perspective performs a correlation function analysis of one-dimensional
SANS data, or generates a model-independent volume fraction profile from a
one-dimensional SANS pattern of an adsorbed layer.

The correlation function analysis is performed in 3 stages:

*  Extrapolation of the scattering curve to :math:`Q = 0` and
   :math:`Q = \infty`
*  Fourier Transform of the extrapolated data to give the correlation function
*  Interpretation of the 1D correlation function based on an ideal lamellar
   morphology

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Extrapolation
-------------

To :math:`Q = 0`
^^^^^^^^^^^^^^^^

The data are extrapolated to Q = 0 by fitting a Guinier model to the data
points in the lower Q range.
The equation used is:

.. math::
    I(Q) = Ae^{Bq^2}

The Guinier model assumes that the small angle scattering arises from particles
and that parameter :math:`B` is related to the radius of gyration of those
particles. This has dubious applicability to polymer systems. However, the
correlation function is affected by the Guinier back-extrapolation to the
greatest extent at large values of R and so the back-extrapolation only has a
small effect on the analysis.

To :math:`Q = \infty`
^^^^^^^^^^^^^^^^^^^^^

The data are extrapolated to Q = :math:`\infty` by fitting a Porod model to
the data points in the upper Q range.

The equation used is:

.. math::
    I(Q) = B + KQ^{-4}e^{-Q^2\sigma^2}

Where :math:`B` is the Bonart thermal background, :math:`K` is the Porod
constant, and :math:`\sigma` describes the electron (or neutron scattering
length) density profile at the interface between crystalline and amorphous
regions (see figure 1).

.. figure:: fig1.gif
   :align: center

   ``Figure 1`` The value of :math:`\sigma` is a measure of the electron
   density profile at the interface between crystalline and amorphous regions.

Smoothing
^^^^^^^^^

The extrapolated data set consists of the Guinier back-extrapolation up to the
highest Q value of the lower Q range, the original scattering data up to the
highest value in the upper Q range, and the Porod tail-fit beyond this. The
joins between the original data and the Guinier/Porod fits are smoothed using
the algorithm below, to avoid the formation of ripples in the transformd data.

Functions :math:`f(x_i)` and :math:`g(x_i)` where :math:`x_i \in \left\{  {x_1, x_2, ..., x_n} \right\}`
, are smoothed over the range :math:`[a, b]` to produce :math:`y(x_i)`, by the
following equations:

.. math::
    y(x_i) = h_ig(x_i) + (1-h_i)f(x_i)

where:

.. math::
    h_i = \frac{1}{1 + \frac{(x_i-b)^2}{(x_i-a)^2}}
