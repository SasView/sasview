.. gsc_ex_customModel_data.rst

.. _gsc_ex_customModel_data:

Example: Fit the experimental data using the calculated $P(Q)$ from a PDB file 
==================================

In this example, the custom model function, custom_apoferritinLong, is written by the Generic Scattering Calculator using a PDB file for apoferritin.
(The apoferritin PDB in this example can be accessed at https://www.rcsb.org/structure/6z6u )

This custerom model returns the normalized form factor, $\tilde{P}(Q)$, and $\beta(Q)$ caculated using the PDB file. 
(Note that $\beta(Q)$ is only used if one needs to fit the data with the inter-particle structure factor, $S(Q)$, with the static decoupling approximation.)

The fitting GUI is shown in the following.

.. figure:: gsc_ex_customModel_data_Fig1.jpg

The scattering pattern, $I(Q)$, is calcualted as

.. math::
    I(\mathbf{Q}) = \frac{scale}{V}(SLD - SLD\_solvent)^2V_{protein} \tilde{P}(Q\alpha) + background

$SLD$ is the scattering length density of the protein (or particle). And $SLD\_solvent$ is the scatteirng length density of solvent. 

$V_{protein}$ is the protein volume. If the scattering length density and protein volume are assigned with correct values, $scale$ is the volume fraction of the protein ( or particle).

$\alpha$ is the swelling factor. In general, $\alpha$ should be one (or close to one). The parameter is introduced just in case that there is a slight swelling of the particle.

The following figure shows the comparison between one experimental apoferritin protein SANS data with the calculated $I(Q)$ using this model.

.. figure:: gsc_ex_customModel_data_Fig2.jpg


*Document History*

| 2023-10-30 Yun Liu

