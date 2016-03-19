.. sm_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

.. |inlineimage004| image:: sm_image004.gif
.. |inlineimage005| image:: sm_image005.gif
.. |inlineimage008| image:: sm_image008.gif
.. |inlineimage009| image:: sm_image009.gif
.. |inlineimage010| image:: sm_image010.gif
.. |inlineimage011| image:: sm_image011.gif
.. |inlineimage012| image:: sm_image012.gif
.. |inlineimage018| image:: sm_image018.gif
.. |inlineimage019| image:: sm_image019.gif


.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Smearing Functions
==================

Sometimes it will be necessary to correct reduced experimental data for the
physical effects of the instrumental geometry in use. This process is called
*desmearing*. However, calculated/simulated data - which by definition will be
perfect/exact - can be *smeared* to make it more representative of what might
actually be measured experimentally.

SasView provides the following three smearing algorithms:

*  *Slit Smearing*
*  *Pinhole Smearing*
*  *2D Smearing*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Slit Smearing
-------------

**This type of smearing is normally only encountered with data from X-ray Kratky**
**cameras or X-ray/neutron Bonse-Hart USAXS/USANS instruments.**

The slit-smeared scattering intensity is defined by

.. image:: sm_image002.gif

where *Norm* is given by

.. image:: sm_image003.gif

**[Equation 1]**

The functions |inlineimage004| and |inlineimage005|
refer to the slit width weighting function and the slit height weighting 
determined at the given *q* point, respectively. It is assumed that the weighting
function is described by a rectangular function, such that

.. image:: sm_image006.gif

**[Equation 2]**

and

.. image:: sm_image007.gif

**[Equation 3]**

so that |inlineimage008| |inlineimage009| for |inlineimage010| and *u*\ .

Here |inlineimage011| and |inlineimage012| stand for
the slit height (FWHM/2) and the slit width (FWHM/2) in *q* space.

This simplifies the integral in Equation 1 to

.. image:: sm_image013.gif

**[Equation 4]**

which may be solved numerically, depending on the nature of |inlineimage011| and |inlineimage012| .

Solution 1
^^^^^^^^^^

**For** |inlineimage012| **= 0 and** |inlineimage011| **= constant.**

.. image:: sm_image016.gif

For discrete *q* values, at the *q* values of the data points and at the *q*
values extended up to *q*\ :sub:`N`\ = *q*\ :sub:`i` + |inlineimage011| the smeared
intensity can be approximately calculated as

.. image:: sm_image017.gif

**[Equation 5]**

where |inlineimage018| = 0 for *I*\ :sub:`s` when *j* < *i* or *j* > *N-1*.

Solution 2
^^^^^^^^^^

**For** |inlineimage012| **= constant and** |inlineimage011| **= 0.**

Similar to Case 1

|inlineimage019| for *q*\ :sub:`p` = *q*\ :sub:`i` - |inlineimage012| and *q*\ :sub:`N` = *q*\ :sub:`i` + |inlineimage012|

**[Equation 6]**

where |inlineimage018| = 0 for *I*\ :sub:`s` when *j* < *p* or *j* > *N-1*.

Solution 3
^^^^^^^^^^

**For** |inlineimage011| **= constant and** |inlineimage011| **= constant.**

In this case, the best way is to perform the integration of Equation 1
numerically for both slit height and slit width. However, the numerical
integration is imperfect unless a large number of iterations, say, at
least 10000 by 10000 for each element of the matrix *W*, is performed.
This is usually too slow for routine use.

An alternative approach is used in SasView which assumes
slit width << slit height. This method combines Solution 1 with the
numerical integration for the slit width. Then

.. image:: sm_image020.gif

**[Equation 7]**

for *q*\ :sub:`p` = *q*\ :sub:`i` - |inlineimage012| and *q*\ :sub:`N` = *q*\ :sub:`i` + |inlineimage012|

where |inlineimage018| = 0 for *I*\ :sub:`s` when *j* < *p* or *j* > *N-1*.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Pinhole Smearing
----------------

**This is the type of smearing normally encountered with data from synchrotron**
**SAXS cameras and SANS instruments.**

The pinhole smearing computation is performed in a similar fashion to the slit-
smeared case above except that the weight function used is a Gaussian. Thus
Equation 6 becomes

.. image:: sm_image021.gif

**[Equation 8]**

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

2D Smearing
-----------

The 2D smearing computation is performed in a similar fashion to the 1D pinhole
smearing above except that the weight function used is a 2D elliptical Gaussian.
Thus

.. image:: sm_image022.gif

**[Equation 9]**

In Equation 9, *x*\ :sub:`0` = *q* cos(|theta|), *y*\ :sub:`0` = *q* sin(|theta|), and
the primed axes, are all in the coordinate rotated by an angle |theta| about
the z-axis (see the figure below) so that *x'*\ :sub:`0` = *x*\ :sub:`0` cos(|theta|) +
*y*\ :sub:`0` sin(|theta|) and *y'*\ :sub:`0` = -*x*\ :sub:`0` sin(|theta|) +
*y*\ :sub:`0` cos(|theta|). Note that the rotation angle is zero for a x-y symmetric
elliptical Gaussian distribution. The *A* is a normalization factor.

.. image:: sm_image023.gif

Now we consider a numerical integration where each of the bins in |theta| and *R* are
*evenly* (this is to simplify the equation below) distributed by |bigdelta|\ |theta|
and |bigdelta|\ R, respectively, and it is further assumed that *I(x',y')* is constant
within the bins. Then

.. image:: sm_image024.gif

**[Equation 10]**

Since the weighting factor on each of the bins is known, it is convenient to
transform *x'-y'* back to *x-y* coordinates (by rotating it by -|theta| around the
*z* axis).

Then, for a polar symmetric smear

.. image:: sm_image025.gif

**[Equation 11]**

where

.. image:: sm_image026.gif

while for a *x-y* symmetric smear

.. image:: sm_image027.gif

**[Equation 12]**

where

.. image:: sm_image028.gif

The current version of the SasView uses Equation 11 for 2D smearing, assuming
that all the Gaussian weighting functions are aligned in the polar coordinate.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Weighting & Normalization
-------------------------

In all the cases above, the weighting matrix *W* is calculated on the first call
to a smearing function, and includes ~60 *q* values (finely and evenly binned)
below (>0) and above the *q* range of data in order to smear all data points for
a given model and slit/pinhole size. The *Norm*  factor is found numerically with the
weighting matrix and applied on the computation of *I*\ :sub:`s`.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 01May2015
