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

In general, the scattering length density (SLD) in each regions where the 
SLD (=/beta/) is uniform, is a combination of the nuclear and magnetic SLDs and 
depends on the spin states of the neutrons as follows. For magnetic scattering, 
only the magnetization component, *M*perp, perpendicular to the scattering 
vector *Q* contributes to the the magnetic scattering length.

.. image:: mag_vector.bmp

The magnetic scattering length density is then

.. image:: dm_eq.gif

where /gamma/ = -1.913 the gyromagnetic ratio, /mu/B is the Bohr magneton, r0 
is the classical radius of electron, and */sigma/* is the Pauli spin. For 
polarised neutron, the magnetic scattering is depending on the spin states. 

Let's consider that the incident neutrons are polarized parallel (+)/
anti-parallel (-) to the x' axis (See both Figures above). The possible 
out-coming states then are + and - states for both incident states

Non-spin flips: (+ +) and (- -)
Spin flips:     (+ -) and (- +)

.. image:: M_angles_pic.bmp

Now, let's assume that the angles of the *Q*  vector and the spin-axis (x') 
against x-axis are /phi/ and /theta/up, respectively (See Figure above). Then, 
depending upon the polarisation (spin) state of neutrons, the scattering length 
densities, including the nuclear scattering length density (/beta/N) are given 
as, for non-spin-flips

.. image:: sld1.gif

for spin-flips

.. image:: sld2.gif

where

.. image:: mxp.gif

.. image:: myp.gif

.. image:: mzp.gif

.. image:: mqx.gif

.. image:: mqy.gif

Here, the M0x, M0y and M0z are the x, y and z components of the magnetization 
vector given in the xyz lab frame. The angles of the magnetization, /theta/M 
and /phi/M as defined in the Figure (above)

.. image:: m0x_eq.gif

.. image:: m0y_eq.gif

.. image:: m0z_eq.gif

The user input parameters are M0_sld = DMM0, Up_theta = /theta/up, 
M_theta = /theta/M, and M_phi = /phi/M. The 'Up_frac_i' and 'Up_frac_f' are 
the ratio

(spin up)/(spin up + spin down)

neutrons before the sample and at the analyzer, respectively.

*Note:* The values of the 'Up_frac_i' and 'Up_frac_f' must be in the range
between 0 and 1.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
