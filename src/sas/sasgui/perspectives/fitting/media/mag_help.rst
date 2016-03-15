.. mag_help.rst

.. This is a port of text from the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

.. |beta| unicode:: U+03B2
.. |gamma| unicode:: U+03B3
.. |mu| unicode:: U+03BC
.. |sigma| unicode:: U+03C3
.. |phi| unicode:: U+03C6
.. |theta| unicode:: U+03B8
.. |chi| unicode:: U+03C7

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

Polarisation/Magnetic Scattering
--------------------------------

Magnetic scattering is implemented in five (2D) models 

*  *SphereModel*
*  *CoreShellModel*
*  *CoreMultiShellModel*
*  *CylinderModel*
*  *ParallelepipedModel*

In general, the scattering length density (SLD, = |beta|) in each region where the
SLD is uniform, is a combination of the nuclear and magnetic SLDs and, for polarised
neutrons, also depends on the spin states of the neutrons.

For magnetic scattering, only the magnetization component, *M*\ :sub:`perp`,
perpendicular to the scattering vector *Q* contributes to the the magnetic
scattering length.

.. image:: mag_vector.bmp

The magnetic scattering length density is then

.. image:: dm_eq.gif

where |gamma| = -1.913 is the gyromagnetic ratio, |mu|\ :sub:`B` is the
Bohr magneton, *r*\ :sub:`0` is the classical radius of electron, and |sigma|
is the Pauli spin.

Assuming that incident neutrons are polarized parallel (+) and anti-parallel (-)
to the *x'* axis, the possible spin states after the sample are then

No spin-flips (+ +) and (- -)

Spin-flips    (+ -) and (- +)

.. image:: M_angles_pic.bmp

If the angles of the *Q* vector and the spin-axis (*x'*) to the *x*-axis are |phi|
and |theta|\ :sub:`up`, respectively, then, depending on the spin state of the
neutrons, the scattering length densities, including the nuclear scattering
length density (|beta|\ :sub:`N`) are

.. image:: sld1.gif

when there are no spin-flips, and

.. image:: sld2.gif

when there are, and

.. image:: mxp.gif

.. image:: myp.gif

.. image:: mzp.gif

.. image:: mqx.gif

.. image:: mqy.gif

Here, *M*\ :sub:`0x`, *M*\ :sub:`0y` and *M*\ :sub:`0z` are the x, y and z components
of the magnetization vector given in the laboratory xyz frame given by

.. image:: m0x_eq.gif

.. image:: m0y_eq.gif

.. image:: m0z_eq.gif

and the magnetization angles |theta|\ :sub:`M` and |phi|\ :sub:`M` are defined in
the figure above.

The user input parameters are:

===========   ================================================================
 M0_sld        = *D*\ :sub:`M` *M*\ :sub:`0`
 Up_theta      = |theta|\ :sub:`up`
 M_theta       = |theta|\ :sub:`M`
 M_phi         = |phi|\ :sub:`M`
 Up_frac_i     = (spin up)/(spin up + spin down) neutrons *before* the sample
 Up_frac_f     = (spin up)/(spin up + spin down) neutrons *after* the sample
===========   ================================================================

*Note:* The values of the 'Up_frac_i' and 'Up_frac_f' must be in the range 0 to 1.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Steve King, 02May2015
