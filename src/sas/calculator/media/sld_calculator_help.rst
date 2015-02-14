..sld_calculator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

SLD Calculator Tool
===================

Description
-----------

The neutron scattering length density is defined as

SLD = (b_c1 +b_c2+...+b_cn )/Vm

where 

b_ci is the bound coherent scattering length of ith of n atoms in a molecule 
with the molecular volume Vm

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

How to Format the Compound Name
-------------------------------

To calculate scattering length densities enter a compound and a mass density 
and click "Calculate". Entering a wavelength value is optional (a default 
value of 6.0 Angstroms will be used).

* Formula strings consist of counts and atoms such as "CaCO3+6H2O".

* Groups can be separated by *'+'* or *space*, so "CaCO3 6H2O" works as well.

* Groups and be defined using parentheses, such as "CaCO3(H2O)6".

* Parentheses can be nested, such as "(CaCO3(H2O)6)1".

* Isotopes are represented by their index, e.g., "CaCO[18]3+6H2O", H[1], or 
H[2].

* Counts can be integer or decimal, e.g. "CaCO3+(3HO0.5)2".

* Other compositions can be calculated as well, for example, for a 70-30 
mixture of H2O/D2O write *H14O7+ D6O3* or more simply *H7D3O5* (i.e. this says 
7 hydrogens, 3 deuteriums, and 5 oxygens) and the mass density calculated 
based on the percentages of H and D.

* Type *C[13]6 H[2]12 O[18]6* for C(13)6H(2)12O(18)6 (6 Carbon-13 atoms, 12 
deuterium atoms, and 6 Oxygen-18 atoms)
