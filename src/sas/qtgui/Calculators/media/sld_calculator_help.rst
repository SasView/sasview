.. sld_calculator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.
..
    There is periodictable syntax for including density of components in the molecular formula field that does not appear to be implemented in SASview.
..
    For compounds, such as biomolecules, with exchangeable hydrogens, H[1] is used to denote the labile hydrogens. The reported contrast match point for the molecule takes into account the ratio of exchanged hydrogens.
    This feature is not currently enabled in Sasview but is available on the NIST webpage.

SLD Calculator Tool
===================

Description
-----------
This tool calculates the neutron and x-ray scattering length densities (SLD) and some other useful scattering parameters of a wide range of materials including, molecules, solutions/mixtures, isotopic mixtures, and biomolecules.
This SLD calculator utilizes the periodictable python package\ :sup:`1`, which is an extensible periodic table populated with values useful for neutron and x-ray experiments.

User Inputs
----------------------------
**Molecular Formula** (required)
    This field defines the material for which you are calculating the SLD. The section "Specifying Materials or Mixtures in the Molecular Formula Field" offers further guidance on how to enter molecules, biomolecules, and more complex mixtures.

**Mass Density** |g/cm^3| (required)
    This field defines the density of the material for which you are calculating the SLD of your material. Density uncertainty is likely the largest source of error in the SLD calculator.

**Neutron Wavelength** (|Ang|) (optional)
    Wavelength is used to calculate the scattering cross-section and 1/e length. It is not required for SLD calculation. If left blank wavelength is assumed to be 6 |Ang|.

**X-ray Wavelength** (|Ang|) (required)
    X-ray scattering length density is energy dependent thus wavelength is a required field for x-ray SLD calculation.

Calculator Output
----------------------------
**Neutron SLD** (|Ang^-2|)

   A measure of the neutron scattering power of the material. A required input for most scattering models using in neutron scattering experiments.

**X-ray SLD** (|Ang^-2|)

    A measure of the x-ray scattering power of the material.  A required input for most scattering models using in x-ray scattering experiments.

**Neutron Incoherent Cross-section** (cm\ :sup:`-1`)

    A measure of the probability that the neutron will scatter incoherently.

**Neutron Absorption Cross-Section** (cm\ :sup:`-1`)

    A measure of the probability that a neutron will be absorbed by the material.

**Neutron 1/e length** (cm)

    The sample thickness required to reduce the transmission to 36.8% (1/e).

Specifying Materials or Mixtures in the Molecular Formula Field
----------------------------
**Molecular formulas** can be entered intuitively with atoms being represented by their atomic symbol. For example, calcium carbonate (CaCO\ :sub:`3`):

    CaCO3

**Multipart species** can be constructed by as a single molecular formula, or by separating the components with a + or a space. For example, consider the hexahydrate of calcium carbonate, ikaite, (CaCO\ :sub:`3` |cdot| 6(H\ :sub:`2`\O)) which can be denoted as:

    CaCO3(H2O)6

    CaCO3 6H2O

    CaCO3+6H2O

**Isotopes** are represented as the element symbol followed by its mass number in square brackets, for example C[12] and C[13]. A special exception to this are isotopes of hydrogen which an also be represented as H = H[1], D = H[2], and T=H[3].

**Isotopic Mixtures** can be entered in several ways. Take, for example a mixture of 30% H2O and 70% D2O (mole fraction). It can be entered as:

    H3D7O5

    H[1]3H[2]7O5

    3H2O+7D2O

*For isotopic substitution you must also adjust the density for your mixture.* There is a density calculator in SASview that may be useful.

**Mass Fraction** can be entered with each component of the mixture written as XX%wt "component" and each component separated with //. The mass fraction of the last component does not need to be specified as the sum of the fractions must add to 100. For example:

    50%wt Co // Ti

    1%wtNaCl // 50%wtD2O // H2O

**Volume Fraction** can be entered in the same way by substituting *%vol* for *%wt* (note: vol% and wt% will are syntax errors).

    50%vol H2O // D2O

These can be combined for more complicated solutions. For example, if you have a 10wt% sodium chloride in water solution and you dilute 20 mL of this solution to 100 mL with D2O this can be represented as:

    20%vol (10%wt NaCl // H2O) // D2O

For even more complicated solutions parenthesis can be nested, and number of atoms can be integer or decimal (eg (HO0.5)2 is equivalent to H2O).

**Solution Composition with Mass and Volume** can be specified in units of mass and volume:

    5g NaCl // 50 g H2O

**Reminder** the solution density is the largest source of error for these calculations. Measure the solution density for an accurate result. For example:

    A brine solution containing 10.44 g Al(NO\ :sub:`3`)3 |cdot| 9H\ :sub:`2`O and 27.51 g D\ :sub:`2`O was prepared for a wormlike micelle experiments. The solution density was measured with a density meter and found to be 1.22 |g/cm^3|. Using the scattering lenth density calculator we enter:

    10.44g Al(NO3)3(H2O)9 // 27.5126g D2O
    and density = 1.22 |g/cm^3|

    The SLD is calculated to be 5.46e-06 (|Ang^-2|)

**Biomolecules**

DNA, Peptides, RNA can be described using the FASTA format.\ :sup:`2, 3` When using this format density will be estimated automatically and the SLD will be calculated for the biomolecule with all exchangeable hydrogens as H.
Use the following codes:

    "aa" - amino acid sequences
    A=Alanine, R=Arginine, L= Leucine

    "dna" - DNA sequences
    A = adenosine, C = cytidine, G = guanine, T = thymidine

    "rna" - RNA sequences
    U = uridine

For example, the amino acid sequence for {beta}-casein can be written as:

    aa: RELEELNVPGEIVESLSSSEESITRINKKIEKFQSEEQQQTEDELQDKIHPFA
        QTQSLVYPFPGPIPNSLPQNIPPLTQTPVVVPPFLQPEVMGVSKVKEAMAPKH
        KEMPFPKYPVEPFTESQSLTLTDVENLHLPLPLLQSWMHQPHQPLPPTVMFPP
        QSVLSLSQSKVLPVPQKAVPYPQRDMPIQAFLLYQEPVLGPVRGPFPIIV

**References:**

[1] Kienzle, P. A. (2008-2019). Extensible periodic table (v1.5.2). Computer Software. https://periodictable.readthedocs.io. [calculator source, web service source]

[2] Pearson WR, Lipman DJ (April 1988). "Improved tools for biological sequence comparison". Proceedings of the National Academy of Sciences of the United States of America. 85 (8): 2444–8. doi:10.1073/pnas.85.8.2444.

[3] https://zhanggroup.org/FASTA/  (helpful explanation of FASTA syntax)

.. note::  This help document was last changed by Katie Weigandt, 01Jan2024

