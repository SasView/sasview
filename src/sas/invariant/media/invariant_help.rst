.. invariant_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

Invariant Calculation Perspective
=================================

Scattering_Invariant_

Volume_Fraction_

Specific_Surface_Area_

Definitions_

Reference_

How_to_Use_

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Scattering_Invariant:

Scattering Invariant
--------------------

The scattering invariant (Q*) is a model-independent quantity that can be 
easily calculated from scattering data.

For two phase systems, the scattering invariant, Q*, is defined as the 
integral of the square of the wave transfer (q) multiplied by the scattering 
cross section over the full range of q.

Q* is given by the following equation

.. image:: image001.gif

This model independent quantity (Q*) is calculated from the scattering data 
that can be used to determine the volume fraction and the specific area of the 
sample under consideration.

These quantities are useful in their own right and can be used in further 
analysis. With this scattering invariant module users will also be able to 
determine the consistency of those properties between data. There is no real 
data defined from zero to infinity, there usually have limited range.

Q* is not really computed from zero to infinity. Our maximum q range is 
1e-5 ~ 10 (1/Angstrom). The lower and/or higher q range than data given can be 
extrapolated by fitting some data nearby.

The scattering invariant is computed as follows

*I(q)* = *I(q)*  w/o background : If the data includes a background, user sets 
the value to subtract the background for the Q* computation.

Reset *I(q)* = *I(q)* scaling factor* , delta *I(q) =*  delta *I(q)*scaling 
factor* : If non-zero scaling factor is given, it will be considered.

Invariant

.. image:: image001.gif

where *g =q*  for the pinhole geometry and *g =qv*  (the slit height) for the 
slit geometry which can be given in data or as a value.

Higher q-region (\>= qmax in data)

Power law (w/o background term) function = C/q4will be used

where the constant C(=2pi(delta(rho))Sv) is to be found by fitting part of 
data with the range of qN-mto qN(m\<N).

Lower q-region (\<= qmin in data):

Guinier function = *I0exp(-Rg2q2/3)*  where I0and Rgare obtained by fitting,

similarly to the high q region above.

Power law can also be used.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Volume_Fraction:

Volume Fraction
---------------

.. image:: image002.gif

where delta(rho) is the SLD contrast of which value is given by users.

.. image:: image003.gif

Thus

where 0 =\< *A*  =\<1/4 in order for these values to be physically valid.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Specific_Surface_Area:

Specific Surface Area
---------------------

.. image:: image004.gif

where *A*  and *Q**  are obtained from previous sections, and the Porod 
constant *Cp*  is given by users.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Definitions:

Definitions
-----------

Q: the magnitude of neutron (or X-ray) momentum transfer vector.

I(Q): the scattering intensity as a function of the momentum transfer Q.

Invariant total is the sum of the invariant calculated from datas q range and
the invariant resulting from extrapolation at low q range and at high q range 
if considered.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Reference:

References
----------

Chapter 2 in O. Glatter and O. Kratky, "Small Angle X-Ray Scattering", Academic 
Press, New York, 1982

http://physchem.kfunigraz.ac.at/sm/

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _How_to_Use:

How to Use
----------

1. Loading data to the panel: Open the data file from File in the menu bar. 
Select loaded data from a plot panel by highlighting that it until its color 
turns yellow. Then right click on that the data and selects the option Compute 
Invariant. The application automatically computes the invariant value if the 
data loaded is valid.

2. To subtract a background or/and to rescale the data, type the values in 
Customized Input box.

3. If you want to calculate the volume fraction and the specific surface 
area, type the optional inputs in the customized input box, and then press 
'Compute' button.

4. The invariant can also be calculated including the outside of the data Q 
range:  To include the lower Q and/or the higher Q range, check in the enable 
extrapolation check box in 'Extrapolation' box. If the power low is chosen,
the power (exponent) can be either held or fitted by checking the 
corresponding radio button.  The Npts that is being used for the extrapolation 
can be specified.

5. If the invariant calculated from the extrapolated region is too large, it 
will be warn in red at the top of the panel, which means that your data is not 
proper to calculate the invariant.

6. The details of the calculation is available by clicking the 'Details'
button in the middle of the panel.

.. image:: image005.gif
