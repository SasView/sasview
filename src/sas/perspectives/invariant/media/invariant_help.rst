.. invariant_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

.. |Ang| unicode:: U+212B
.. |pi| unicode:: U+03C0
.. |bigdelta| unicode:: U+0394
.. |rho| unicode:: U+03C1
.. |phi| unicode:: U+03C6

Invariant Calculation Perspective
=================================

Description
-----------

The scattering, or Porod, invariant (Q*\) is a model-independent quantity that 
can be easily calculated from scattering data.

For two phase systems, the scattering invariant is defined as the integral of 
the square of the wave transfer (Q) multiplied by the scattering cross section 
over the full range of Q from zero to infinity, that is

.. image:: image001.gif

where *g = Q* for pinhole geometry (SAS) and *g = Qv* (the slit height) for  
slit geometry (USAS).

The worth of Q*\  is that it can be used to determine the volume fraction and 
the specific area of a sample. Whilst these quantities are useful in their own 
right they can also be used in further analysis.

The difficulty with using Q*\  arises from the fact that experimental data is 
never measured over the range 0 =< *Q* =< infinity. At best, combining USAS and 
WAS data might cover the range 1e-5 =< *Q* =< 10 1/\ |Ang| . Thus it is usually 
necessary to extrapolate the experimental data to low and high *Q*. For this

High-*Q* region (>= *Qmax* in data)

*  The power law function *C*/*Q*\ :sup:`4` is used where the constant 
   *C* (= 2.\ |pi|\ .(\ |bigdelta|\ |rho|\ ).\ *Sv*\ ) is to be found by fitting part of data 
   within the range *Q*\ :sub:`N-m` to *Q*\ :sub:`N` (where m < N).

Low-*Q* region (<= *Qmin* in data)

*  The Guinier function *I0.exp(-Rg*\ :sup:`2`\ *Q*\ :sup:`2`\ */3)* where *I0* 
   and *Rg* are obtained by fitting as for the high-*Q* region above. 
   Alternatively a power law can be used.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using the perspective
---------------------

1) Select *Invariant* from the *Analysis* menu on the SasView toolbar.

2) Load some data with the *Data Explorer*.

3) Select a dataset and use the *Send To* button on the *Data Explorer* to load 
   the dataset into the *Invariant* perspective.

4) Use the *Customised Input* boxes on the *Invariant* perspective to subtract 
   any background, specify the contrast (i.e. difference in SLDs - this must be 
   specified for the eventual value of Q*\  to be on an absolute scale), or to 
   rescale the data.

5) Adjust the extrapolation range as necessary. In most cases the default 
   values will suffice.

6) Click the *Compute* button.

7) To include a lower and/or higher Q range, check the relevant *Enable 
   Extrapolate* check boxes.
   
   If power law extrapolations are chosen, the exponent can be either held 
   fixed or fitted. The number of points, Npts, to be used for the basis of the 
   extrapolation can also be specified.

8) If the value of Q*\  calculated with the extrapolated regions is invalid, a 
   red warning will appear at the top of the *Invariant* perspective panel.

   The details of the calculation are available by clicking the *Details* 
   button in the middle of the panel.

.. image:: image005.gif

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Parameters
----------

Volume Fraction
^^^^^^^^^^^^^^^

The volume fraction |phi| is related to Q*\  by

.. image:: image002.gif

where |bigdelta|\ |rho| is the SLD contrast.

.. image:: image003.gif

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Specific Surface Area
^^^^^^^^^^^^^^^^^^^^^

The specific surface area *Sv* is related to Q*\  by

.. image:: image004.gif

where *Cp* is the Porod constant.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Reference
---------

O. Glatter and O. Kratky
Chapter 2 in *Small Angle X-Ray Scattering*
Academic Press, New York, 1982

http://physchem.kfunigraz.ac.at/sm/

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 01May2015
