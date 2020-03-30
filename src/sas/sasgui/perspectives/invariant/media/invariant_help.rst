.. invariant_help.rst

.. This help file was ported from the original HTML to ReSTructured text by
.. S King, ISIS, during SasView CodeCamp-III in Feb 2015. It was subsequently
.. updated in January 2020 following the realisation that there were issues
.. with both the text below and the underlying calculation. See SasView GitHub
.. Issues #1434 and #1461.

.. set up some substitutions
.. |Ang^-1| replace:: |Ang|\ :sup:`-1`

Invariant Calculation
=====================

Principle
---------

For any multi-phase system, i.e. any system that contains regions whith
different scattering length denisties (SLD), the integral over all $q$ (or
$4\pi$ in scattering angle) of the appropriately dimensionally-weighted 
cattering cross-section (ie, 'intensity', $I(q)$ in absolute units) is a
*constant* directly proportional to the mean-square average fluctuation (SLD)
and the phase composition. Usefully, this value is *independent* of the sizes,
shapes, or interations, or, more generally, the arrangement, of the phase
domains (i.e. it is **invariant**). For purposes of this discussion, a phase is
any portion of the material which has a SLD that is distinctly different from
the average SLD of the material. This constant is known as the
*Scattering Invariant*, the *Porod Invariant*, or simply as the *Invariant*,
$Q^*$. 

.. note::
   In this document we shall denote the invariant by the often encountered
   symbol $Q^*$. But the reader should be aware that other symbols can be
   encountered in the literature. Glatter & Kratky\ [#Glatter_Kratky]_, and
   Stribeck\ [#Stribeck]_, for example,both use $Q$, the same symbol we use to
   denote the scattering vector in SasView(!), whilst
   Melnichenko\ [#Melnichenko]_ uses $Z$. Other variations include $Q_I$.

As the invariant is a fundamental law of scattering, it can be used for sanity
checks (for example, scattering patterns that look very different often
**SHOULD** have the same invariant **IF** the hypothesis of what is going on is
correct), can be used to cross-calibrate different SAS instruments, and, as
explained below, can yield an independent estimate of volume fractions or
contrast terms.


Implementation
--------------

Calculation
^^^^^^^^^^^
Assuming isotropic scattering, the invariant integral can be computed on one
dimensional reduced data as:

.. math::

    Q^* = \int_0^\infty q^2I(q)\,dq

.. warning:: SasView, and to our knowlege most, if not all, other implentations,
    does not include the effects of instrumental resolution to the above
    equation. This means that for data with very significant resolution
    smearing, more likely to be encountered with SANS vs SAXS data, the
    calculated invariant will be distorted (too high).

In the extreme case of "infinite" slit smearing, the above equation reduces to:

.. math::

    Q^* = \Delta q_v \int_0^\infty qI(q)\,dq

where $\Delta q_v$ is the slit height, and should be valid as long as $\Delta
q_v$ is large enough to include most, if not all, the scattering. This limit is
applicable for example to most data taken on Bonse-Hart type instruments.
SasView does implement this limit so that, interestingly, in this case, the
Invariant calculated from such slit smeared data could be more accurate than
for normal pihole SANS data which typically has sigificant $\Delta q / q$.

The slit smeared expression above has also been used to compute the invariant
from unidirectional cuts through 2D scattering patterns such as, for example,
those arising from oriented fibers (see the Crawshaw\ [#Crawshaw]_ and
Shioya\ [#Shioya]_ references).However, in order to use the Invariant analysis
window to do this, it would first be necessary to put the cuts in a data format
that SasView recognises as slit-smeared by properly including the value of
$q_v$ in the data file.

.. note::

    Currently SasView will only account for slit smearing if the data being
    processed by the invariant are recognized as slit smeared. It does not 
    allow for manually inputing a slit value. Currently only the canSAS and
    NIST \*.ABS formats include slit smeared data. The easiest way to include
    $\Delta q_v$ in simple ASCII column data in a way recognizable by
    SasView is to mimic the \*.ABS format. The data mus follow the normal rules
    for general ASCII reader but include 6 columns. The general ASCII reader
    assumes the first four are $q$, $I(q)$, $dI$, $\sigma(q)$. If the data does
    not contain any $dI$ information, these can be faked by making them ~1%
    (or less) of the data column. The fourth column **must** contain the $q_v$
    value, in |Ang^-1|, as a **NEGATIVE** number. Each row should have the same
    value. The 5th column **must** be a duplicate of column 1. Column 6 can
    have any value but cannot be empty. Finally the line immediately preceding
    the actual columnar data **must** begin with: "The 6 columns". For an
    example, see the data set 1umSlitSmearSphere.ABS in the
    *\\test\\1d* folder).

Data Extrapolation
^^^^^^^^^^^^^^^^^^
The difficulty with using $Q^*$  arises from the fact that experimental data is
never measured over the range $0 \le q \le \infty$ and it is thus usually
necessary to extrapolate the experimental data to both low and high $q$.
Currently, SasView allows extrapolation to a fixed low and high $q$ such that
$10^{-5} \le q \le 10$ |Ang^-1|. 

Low-\ $q$ region (<= $q_{min}$ in data):

*  The Guinier function $I_0.exp(-q^2 R_g^2/3)$ can be used, where $I_0$
   and $R_g$ are obtained by fitting the data within the range $q_{min}$ to
   $q_{min+j}$ where $j$ is the user chosen number of points from which to
   extrapolate. The default is the first 10 points. Alternatively a power
   law, similar to the high $q$ extrapolation, can be used but is not
   recommended! Because the integrals above are weighted by $q^2$ or $q$
   the low-$q$ extrapolation generally only contributes a small proportion,
   say <3%, to the value of $Q^*$.
   
High-\ $q$ region (>= $q_{max}$ in data):

*  The power law function $A/q^m$ is used where the power law constant
   $m$ can be fixed to some value by the user or fit along with the constant
   $A$. $m$ should typically be between -3 and -4 with -4 indicating sharp
   interfaces. The fitted constant(s) $A$ ($m$) is/are obtained by
   fitting the data within the range $q_{max-j}$ to $q_{max}$ 
   where again $j$ is the user chosen number of points from which to
   extrapoloate, the default again being the last 10 points. This extrapolation
   typically contributes 3 - 20% of the value of $Q^*$ so having data measured
   to as large a value of $q_{max}$ as possible is generally much more
   important.

.. warning:: While the high $q$ power should generally be close to -4 for the
    assumptions underlying the extraction of other parameters to be correct,
    in the special case of slit smearing that power law should be -3 for the
    same sharp interfaces.

Invariant
^^^^^^^^^
SasView Implements the calculations for a two-phase system(or pseudo two phase),
the most commonly encountered situation, for which the Invariant is

.. math::

    Q^* = {2 \pi^2 (\Delta\rho)^2 \phi_1 \phi_2}

where $\Delta\rho = (\rho_1 - \rho_2)$ is the SLD contrast and $\phi_1$ and
$\phi_2$ are the volume fractions of the two phases ($\phi_1 + \phi_2 = 1$).
Thus from the Invariant one can either calculate the volume fractions of the
two phases given the contrast or, given the volume fraction calculate the
contrast.  However, the current implementation in SasView only allows for
extracting the volume fraction given a known contrast factor.

.. warning:: The Invariant analysis window always tries to return the volume
    fraction using the default SLD of 1e-6 |Ang^-1|. The user **MUST**
    provide the **correct** SLD for their system and click on compute before
    examining the Invariant value.

Volume Fraction
^^^^^^^^^^^^^^^
In some cases, particularly in non particulate systems for whcih no good
analytical model exists (the scale factor of such a model returning the volume
fraction information), the contrast term can be reasonably estimated but it
would be helpful to know the volume fraction. This is true for example for
Geosciences and other materials studies where the amount of porosity (the
second phase) is of vital interest.

Rearranging the above expression for $Q^*$ yields

.. math::

    \phi_1 \phi_2 = \frac{Q^*}{2 \pi^2 (\Delta\rho)^2} \equiv A

and thus, if $\phi_1 < \phi_2$

.. math::

    &\phi_1 = \frac{1 - \sqrt{1 - 4A}}{2} \\
    &\phi_2 = \frac{1 + \sqrt{1-4A}}{2}

where $\phi_1$ (the volume fraction of the *minority phase*) is reported as the
the volume fraction in the Invariant analysis window.

.. note::

    If A<0.25 then the program is obviously unable to compute :math:`\phi_1`.
    In these circumstances the Invariant window will show the volume fraction
    as ERROR. Possible reasons for this are that the contrast has been
    incorrectly entered, or that the dataset is simply not suitable for
    invariant analysis.

Specific Surface Area
^^^^^^^^^^^^^^^^^^^^^

The total surface area/unit volume is an important quantity for a variety of
applications, particularly in porous materials, for example to understand the
aborption capacity, reactivity, or catalytic activity of a material. This value,
known as the specific surface area $S_v$, is reflected in the scattering of the
material. Indeed, any interfaces in the material separating regions of
different scattering length densities contribute to the overall scattering.

For a two phase system, the $S_v$ can be computed from the scattering data as:

.. math::

    S_v = \frac{C_p}{2 \pi (\Delta\rho)^2}

where $C_p$, the *Porod Constant*, is given by Porod's Law:

.. math::

    Cp = \lim_{q \to \infty}I(q) q^4
 
which can be estimated from a Porod model fit to the an appropriately high $q$
portion of the data or from the intercept of a linear fit to the hig $q$
portion of a Porod Plot: $I(q)*q^4$ vs. $q^4$ (see the Porod model
documentation in the models documentation section for more details).

This calculation is unrelated to the Invariant other than to obtain the
contrast term if it isn't known (and the volume fraction is known), depending
only on the two provided values of the contrast and Porod Constant.

Extension to Three or More Phases
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
In principle, as suggested in the introduction, the invariant is a
completely general concept and not limited to two phases.  Extending the
theories to more phases, so that useful information can be extracted from the
Invariant, is however more difficult.  

However we note here that in the generalized form the contrast term is
replaced by the SLD fluctuation, $\eta$, which represents the deviation in SLD
from the weighted-average value, $\langle (\rho^*) \rangle$, at any given point
in the system. More correctly, in the special case of a two phase system the
SLD fluctuation terms reduce to the contrast terms.

The mean-square average of the SLD fluctuations, $<\eta^2>$, is given by:

.. math::

    \langle \eta^2 \rangle = \langle (\rho^*)^2 \rangle -
    \langle (\rho^*) \rangle^2

where for the special case of the two phase system

.. math::

    \langle (\rho^*)^2 \rangle = \phi_1 \rho_1^2 + \phi_2 \rho_2^2

.. math::
    
    \langle (\rho^*) \rangle = \phi_1 \rho_1 + \phi_2 \rho_2

and thus setting

.. math::

    \eta_1 = \phi_2 (\rho_1 - \rho_2)
    
.. math::

    \eta_2 = \phi_1 (\rho_2 - \rho_1)

yielding for the two phase system:

.. math::

    \langle \eta^2 \rangle = \langle (\rho^*)^2 \rangle - \langle (\rho^*)
    \rangle^2 = \phi_1 \eta_1^2 + \phi_2 \eta_2^2 \equiv \phi_1 \phi_2
    (\rho_1 - \rho_2)^2

Thus leading to the expected result for the two phase system:

.. math::

    Q^* = {2 \pi^2 \langle \eta^2 \rangle} \equiv 
          {2 \pi^2 (\Delta\rho)^2 \phi_1 \phi_2}

.. note:: For a fuller discussion of the extension of Invariant Analysis to
    three phases, see the Melnichenko reference\ [#Melnichenko]_, Chapter 6,
    Section 6.9, and the Shioya reference\ [#Crawshaw]_.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using invariant analysis
------------------------

1) Load some data with the *Data Explorer*.

   Select a dataset and use the *Send To* button on the *Data Explorer* to load
   the dataset into the *Invariant* panel. Or select *Invariant* from the
   *Analysis* category in the menu bar.
   
   A first estimate of $Q^*$ should be computed automatically. If not, click on
   the *Compute* button.

2) Use the *Customised Inputs* boxes on the *Invariant* panel to subtract
   any background, specify the contrast (i.e. difference in SLDs: note this
   must be specified for the eventual value of $Q^*$ to be on an absolute scale
   and to therefore have any meaning), or to rescale the data.

3) (Optional) If known, a value for $C_p$ can also be specified.

4) Adjust the extrapolation ranges and extrapolation types as necessary. In
   most cases the default values will suffice. Click the *Compute* button.

   To adjust the lower and/or higher $Q$ ranges, check the relevant *Enable
   Extrapolate* check boxes.

   If power law extrapolations are chosen, the exponent can be either held
   fixed or fitted. The number of points, $Npts$, to be used for the basis of
   the extrapolation can also be specified.

5) If the value of $Q^*$ calculated with the extrapolated regions is invalid, a
   red warning will appear at the top of the *Invariant* panel. Strictly
   speaking this is simply a warning that more than 10% of the computed $Q^*$
   value comes from the area under the extrapolated curves suggesting a high
   level of reliance on the high accuracy of those extrapolations. Proceed
   with caution.

   The details of the calculation are available by clicking the *Details*
   button in the middle of the panel.

.. image:: image005.png


.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

References
----------

.. [#Glatter_Kratky] O. Glatter and O. Kratky Chapter 2 and Chapter 14 in
    *Small Angle X-Ray Scattering*; Academic Press, New York, 1982.
    Available at:
    http://web.archive.org/web/20110824105537/http://physchem.kfunigraz.ac.at/sm/Service/Glatter_Kratky_SAXS_1982.zip.

.. [#Stribeck] N. Stribeck Chapter 8 in *X-Ray Scattering of Soft Matter*
    Springer, 2007.

.. [#Melnichenko] Y.B. Melnichenko Chapter 6 in *Small-Angle Scattering from 
    Confined and Interfacial Fluids*; Springer, 2016.

.. [#Crawshaw] J. Crawshaw, M.E. Vickers, N.P. Briggs, R.K. Heenan,
    R.E. Cameron *Polymer*, 41 1873-1881 (2000).

.. [#Shioya] M. Shioya and A. Takaku *J. Appl. Phys.*, 58 4074  (1985).

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed (completely re-written) by Paul
    Butler and Steve King, 29 Mar2020
