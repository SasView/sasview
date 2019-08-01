.. pr_help.rst

P(r) Calculation
================

Description
-----------

This tool calculates a real-space distance distribution function, *P(r)*, using
the inversion approach (Moore, 1980).

A set of base functions of the type

.. math::
  \Phi_{n(r)} = 2 r sin(\frac{\pi n r}{D_{max}})

are used to describe the measured scattering data. The set of base functions is
chosen such that their Fourier transform is straightforward. The coefficients
of each base function in the expansion are optimised by performing a least
square fit with the following function

.. math::

  \chi^2=\frac{\sum_i (I_{meas}(Q_i)-I_{th}(Q_i))^2}{error^2}+Reg\_term

where $I_{meas}(Q_i)$ is the measured scattering intensity and $I_{th}(Q_i)$ is
the summation of the base functions.

The $Reg\_term$ term is a regularization term set to the second derivative
$d^2P(r)/d^2r$ integrated over $r$. It is used to produce a smooth *P(r)* output.

The sum of the optimised Fourier-transformed base functions then yields *P(r)*.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using P(r) inversion
--------------------

The user must enter

*  *Number of terms*: the number of base functions in the P(r) expansion. If
   too small the summation of base functions will be unable to provide the
   necessary resolution; but if it is too large the number of coefficients
   may exceed the number of independent parameters that can be deduced from the
   data! A number between 10-30 is typical.

*  *Regularization constant*: a multiplicative constant to set the size of
   the regularization term. The suggested value is that above which P(r)
   will only have one peak.

*  *Maximum distance*: the maximum distance between any two points in the
   system. This should be smaller than $pi$/$Q_{min}$.

P(r) inversion requires that the background be perfectly subtracted.  This is
often difficult to do well and thus many data sets will include a background.
For those cases, the user should check the "Estimate background level" option
and the module will do its best to estimate it. If you know the background
value for your data, select the "Input manual background level" option. Note
that this value will be treated as having zero error.

The P(r) module is constantly computing in the background what the optimum
*number of terms* should be as well as the optimum *regularization constant*.
These are constantly updated in the buttons next to the entry boxes on the GUI.
These are almost always close and unless the user has a good reason to choose
differently they should just click on the buttons to accept both.  {D_max} must
still be set by the user.  However, besides looking at the output, the user can
click the explore button which will bring up a graph of chi^2 vs Dmax over a
range around the current Dmax.  The user can change the range and the number of
points to explore in that range.  They can also choose to plot several other
parameters as a function of Dmax including:

*  *Rg*: the radius-of-gyration computed from the P(r).

*  *I(Q=0)*: the forward scattering intensity of the base function fit.

*  *Background*: the estimated background level.

*  *Chi2/dof*: chi-squared divided by the degrees of freedom.

*  *Oscillations*: P(r) for a sphere has an oscillation paramneter of 1.1

*  *Positive fraction*: the fraction of P(r) that is positive. This should be
   as close to 1.0 as possible.

*  *1-sigma positive fraction*: the fraction of P(r) that is at least one
   standard deviation greater than zero.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Reference
---------

P.B. Moore
*J. Appl. Cryst.*, 13 (1980) 168-175

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last modified by Steve King, 01 August 2019
