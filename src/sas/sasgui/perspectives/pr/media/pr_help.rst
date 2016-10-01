.. pr_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

P(r) Calculation
================

Description
-----------

This tool calculates a real-space distance distribution function, *P(r)*, using 
the inversion approach (Moore, 1908).

*P(r)* is set to be equal to an expansion of base functions of the type

.. math::
  \Phi_{n(r)} = 2 r sin(\frac{\pi n r}{D_{max}})

The coefficient of each base function in the expansion is found by performing
a least square fit with the following fit function

.. math::

  \chi^2=\frac{\sum_i (I_{meas}(Q_i)-I_{th}(Q_i))^2}{error^2}+Reg\_term
  

where $I_{meas}(Q_i)$ is the measured scattering intensity and $I_{th}(Q_i)$ is
the prediction from the Fourier transform of the *P(r)* expansion. 

The $Reg\_term$ term is a regularization term set to the second derivative 
$d^2P(r)/d^2r$ integrated over $r$. It is used to produce a smooth *P(r)* output.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using P(r) inversion
--------------------

The user must enter

*  *Number of terms*: the number of base functions in the P(r) expansion.
   
*  *Regularization constant*: a multiplicative constant to set the size of
   the regularization term.

*  *Maximum distance*: the maximum distance between any two points in the
   system.

P(r) inversion requires that the background be perfectly subtracted.  This is
often difficult to do well and thus many data sets will include a background.
For those cases, the user should check the "estimate background" box and the
module will do its best to estimate it.

The P(r) module is constantly computing in the background what the optimum
*number of terms* should be as well as the optimum *regularization constant*.
These are constantly updated in the buttons next to the entry boxes on the GUI.
These are almost always close and unless the user has a good reason to choose
differently they should just click on the buttons to accept both.  {D_max} must
still be set by the user.  However, besides looking at the output, the user can
click the explore button which will bring up a graph of chi^2 vs Dmax over a
range around the current Dmax.  The user can change the range and the number of
points to explore in that range.  They can also choose to plot several other
parameters as a function of Dmax including: I0, Rg, Oscillation parameter,
background, positive fraction, and 1-sigma positive fraction.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Reference
---------

P.B. Moore
*J. Appl. Cryst.*, 13 (1980) 168-175

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last modified by Paul Butler, 05 September, 2016
