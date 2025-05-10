.. sizedistribution_help.rst

.. _Size_Distribution:

Size Distribution
=================

Size distribution analysis is a technique for extracting information from
scattering of a nominally two phase material where the shape of the domains
of the minority size are assumed to be known, but the size distribution is
completely unknown. Most often used in materials where the domain sizes have an
extremely large variation such as pores in rocks hence the oft used term “pore
size distribution” for this type of analysis. The scattered intensity in this
case is given by the integral of the scattering intensity from every size
present in the system. Basically a polydispersity integral of the monodisperse
I(Q) but where the shape of the distribution can be anything and most likely
not possible to put in a parameterized analytical form. Thus the equation
to fit is:

..math::
    I(Q)= \Delta \rho^2 \int N_p(r) P(Q,r) dr

Where $N_p(r)$ is the number density of particles of characteristic dimension
r, and P(Q,r) is the form factor for that characteristic dimension. For a
sphere this translates as:

..math::
P(Q,r) = \left[
        3V_p(\Delta\rho) \cdot \frac{\sin(Qr) - Qr\cos(qr))}{(Qr)^3}
        \right]^2

SasView is using the sasmodels package and other shapes are expected to be
added in the future. Also, sasmodels automatically scales to volume fraction
rather than number density using

..math::
    N_p = \phi/V_p

The current implementation uses an ellipsoid of revolution. The default is an
axial ratio of 1 which is a sphere. The equation for an ellipsoid of revolution
is given in the sasmodels documentation and $r = R_{eq}$ with an eccentricity
(aspect ratio) fixed by the user which is $Ecc = R_polar/R_eq$.

The “fitting parameter” in this approach then is the distribution function.
In order to calculate this practically over a finite $Q$ range, we replace the
integral equation with the following sum, where $r_{min}$ and $r_{max}$ should
be within the range that will significantly affect the scattering in the $Q$
range being used.

..math::
    I(Q)= \Delta \rho^2 \sum_{r_{min}}^{r_{max}} N_p(r) P(Q,r)

Even so, fitting is over determined, particularly given the noise in any real
data and the very shallow. Essentially this is an ill posed problem. In order
to provide a reasonably robust solution a regularization technique is generally
used. Here we implement only the most common MaxEnt (Maximum Entropy) method
used for example by the famous CONTIN algorithm used in light scattering.

Maximum Entropy
^^^^^^^^^^^^^^^

..note::
    The assmumptions inherent in this method:
    * The system can be approximated as a two phase system
    * The scattering length density of each phase is known
    * The minor phase is made up of domains of varying sizes but a fixed shape
    * The minor phase is sufficiently “dilute” as to not have any interdomain interference terms (i.e. no S(Q)


.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Reference
---------

TODO

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last modified by Paul Butler on May 10, 2025
