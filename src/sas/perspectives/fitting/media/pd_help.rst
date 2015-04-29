.. pd_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
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

Polydispersity Distributions
----------------------------

Calculates the form factor for a polydisperse and/or angular population of 
particles with uniform scattering length density. The resultant form factor 
is normalized by the average particle volume such that 

P(q) = scale*\<F*F\>/Vol + bkg

where F is the scattering amplitude and the\<\>denote an average over the size 
distribution.  Users should use PD (polydispersity: this definition is 
different from the typical definition in polymer science) for a size 
distribution and Sigma for an angular distribution (see below).

Note that this computation is very time intensive thus applying polydispersion/
angular distribution for more than one parameters or increasing Npts values
might need extensive patience to complete the computation. Also note that 
even though it is time consuming, it is safer to have larger values of Npts 
and Nsigmas.

The following five distribution functions are provided

*  *Rectangular Distribution*
*  *Array Distribution*
*  *Gaussian Distribution*
*  *Lognormal Distribution*
*  *Schulz Distribution*

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Rectangular Distribution
^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: pd_image001.png

The xmean is the mean of the distribution, w is the half-width, and Norm is a 
normalization factor which is determined during the numerical calculation. 
Note that the Sigma and the half width *w*  are different.

The standard deviation is

.. image:: pd_image002.png

The PD (polydispersity) is

.. image:: pd_image003.png

.. image:: pd_image004.jpg

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Array Distribution
^^^^^^^^^^^^^^^^^^

This distribution is to be given by users as a txt file where the array 
should be defined by two columns in the order of x and f(x) values. The f(x) 
will be normalized by SasView during the computation.

Example of an array in the file

30        0.1
32        0.3
35        0.4
36        0.5
37        0.6
39        0.7
41        0.9

We use only these array values in the computation, therefore the mean value 
given in the control panel, for example â€˜radius = 60â€™, will be ignored.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Gaussian Distribution
^^^^^^^^^^^^^^^^^^^^^

.. image:: pd_image005.png

The xmean is the mean of the distribution and Norm is a normalization factor 
which is determined during the numerical calculation.

The PD (polydispersity) is

.. image:: pd_image003.png

.. image:: pd_image006.jpg

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Lognormal Distribution
^^^^^^^^^^^^^^^^^^^^^^

.. image:: pd_image007.png

The /mu/=ln(xmed), xmed is the median value of the distribution, and Norm is a 
normalization factor which will be determined during the numerical calculation. 
The median value is the value given in the size parameter in the control panel, 
for example, â€œradius = 60â€�.

The PD (polydispersity) is given by /sigma/

.. image:: pd_image008.png

For the angular distribution

.. image:: pd_image009.png

The mean value is given by xmean=exp(/mu/+p2/2). The peak value is given by 
xpeak=exp(/mu/-p2).

.. image:: pd_image010.jpg

This distribution function spreads more and the peak shifts to the left as the 
p increases, requiring higher values of Nsigmas and Npts.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Schulz Distribution
^^^^^^^^^^^^^^^^^^^

.. image:: pd_image011.png

The xmean is the mean of the distribution and Norm is a normalization factor
which is determined during the numerical calculation.

The z = 1/p2â€“ 1.

The PD (polydispersity) is

.. image:: pd_image012.png

Note that the higher PD (polydispersity) might need higher values of Npts and 
Nsigmas. For example, at PD = 0.7 and radisus = 60 A, Npts >= 160, and 
Nsigmas >= 15 at least.

.. image:: pd_image013.jpg

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ
