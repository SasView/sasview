.. pr_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

.. |pi| unicode:: U+03C0
.. |bigphi| unicode:: U+03A6
.. |bigsigma| unicode:: U+03A3
.. |chi| unicode:: U+03C7

P(r) Inversion Perspective
==========================

Description
-----------

This tool calculates a real-space distance distribution function, *P(r)*, using 
the inversion approach (Moore, 1908).

*P(r)* is set to be equal to an expansion of base functions of the type

  |bigphi|\_n(r) = 2.r.sin(|pi|\ .n.r/D_max)

The coefficient of each base function in the expansion is found by performing 
a least square fit with the following fit function

  |chi|\ :sup:`2` = |bigsigma|\ :sub:`i` [ I\ :sub:`meas`\ (Q\ :sub:`i`\ ) - I\ :sub:`th`\ (Q\ :sub:`i`\ ) ] :sup:`2` / (Error) :sup:`2` + Reg_term

where I\ :sub:`meas`\ (Q) is the measured scattering intensity and 
I\ :sub:`th`\ (Q) is the prediction from the Fourier transform of the *P(r)* 
expansion. 

The *Reg_term* term is a regularization term set to the second derivative 
d\ :sup:`2`\ *P(r)* / dr\ :sup:`2` integrated over *r*. It is used to produce a 
smooth *P(r)* output.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using the perspective
---------------------

The user must enter

*  *Number of terms*: the number of base functions in the P(r) expansion.
   
*  *Regularization constant*: a multiplicative constant to set the size of
   the regularization term.

*  *Maximum distance*: the maximum distance between any two points in the
   system.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Reference
---------

P.B. Moore
*J. Appl. Cryst.*, 13 (1980) 168-175

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 01May2015
