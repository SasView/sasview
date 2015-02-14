..pr_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

P(r) Inversion Perspective
==========================

The inversion approach is based on Moore, J. Appl. Cryst., (1980) 13, 168-175.

P(r) is set to be equal to an expansion of base functions  of the type 
phi_n(r) = 2*r*sin(pi*n*r/D_max).

The coefficient of each base function in the expansion is found by performing 
a least square fit with the following fit function:

chi**2 = sum_i[ I_meas(q_i) - I_th(q_i) ]**2/error**2 + Reg_term

where I_meas(q) is the measured scattering intensity and I_th(q) is the 
prediction from the Fourier transform of the P(r) expansion. 

The Reg_term term is a regularization term set to the second derivative 
d**2P(r)/dr**2 integrated over r. It is used to produce a smooth P(r) output.

The following are user inputs:

   - Number of terms: the number of base functions in the P(r) expansion. 
   
   - Regularization constant: a multiplicative constant to set the size of 
the regularization term.

   - Maximum distance: the maximum distance between any two points in the 
   system.
