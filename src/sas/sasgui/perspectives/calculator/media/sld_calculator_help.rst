.. sld_calculator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

SLD Calculator Tool
===================

Description
-----------

The neutron scattering length density (SLD, $\beta_N$) is defined as

.. math::

  \beta_N = (b_{c1} + b_{c2} + ... + b_{cn}) / V_m

where $b_{ci}$ is the bound coherent scattering length of ith of n atoms in a molecule
with the molecular volume $V_m$.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Specifying the Compound Name
----------------------------

To calculate scattering length densities enter the empirical formula of a
compound and its mass density and click "Calculate".

Entering a wavelength value is optional (a default value of 6.0 |Ang| will
be used).

TIPS!

*  Formula strings consist of atoms and the number of them, such as "CaCO3+6H2O".

*  Groups can be separated by *'+'* or *space*, so "CaCO3 6H2O" works as well.

*  Groups can be defined using parentheses, such as "CaCO3(H2O)6".

*  Parentheses can be nested, such as "(CaCO3(H2O)6)1".

*  Isotopes are represented by their atomic number in *square brackets*, such
   as "CaCO[18]3+6H2O", H[1], or H[2].

*  Numbers of atoms can be integer or decimal, such as "CaCO3+(3HO0.5)2".

*  The SLD of mixtures can be calculated as well. For example, for a 70-30
   mixture of H2O/D2O write "H14O7+D6O3" or more simply "H7D3O5" (i.e. this says
   7 hydrogens, 3 deuteriums, and 5 oxygens) and enter a mass density calculated
   on the percentages of H2O and D2O.

*  Type "C[13]6 H[2]12 O[18]6" for C(13)6H(2)12O(18)6 (6 Carbon-13 atoms, 12
   deuterium atoms, and 6 Oxygen-18 atoms).

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Paul Kienzle, 05Apr2017

