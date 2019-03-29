.. fitting_sq.rst

.. Much of the following text was scraped from product.py

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _Product Models:

Fitting Models with Structure Factors
-------------------------------------

.. note::

   This help document is under development

*Product models*, $P@S$ models for short, multiply the structure factor $S(q)$ by
the form factor $P(q)$, modulated by the *effective radius* of the form factor.

Many of the parameters in $P@S$ models take on specific meanings so that they
can be handled correctly inside SasView:

* *scale*:

  The *scale* for $P@S$ models should usually be set to 1.0.

* *volfraction*:

  For hollow shapes, *volfraction* represents the volume fraction of
  material but the $S(q)$ calculation needs the volume fraction *enclosed by*
  *the shape.* SasView scales the user-specified volume fraction by the ratio
  form:shell computed from the average form volume and average shell volume
  returned from the $P(q)$ calculation (the original *volfraction* is divided
  by *shell_volume* to compute the number density, and then $P@S$ is scaled
  by that to get the absolute scaling on the final $I(q)$).

* *radius_effective*:

  If part of the $S(q)$ calculation, the value of *radius_effective* may be
  polydisperse. If it is calculated by $P(q)$, then it will be the weighted
  average of the effective radii computed for the polydisperse shape
  parameters.

* *structure_factor_mode*:

  If the $P@S$ model supports the $\beta(q)$ *correction* [1] then
  *structure_factor_mode* will appear in the parameter table after the $S(q)$
  parameters. This mode may be 0 for the local monodisperse approximation:

    $I = (scale / volume)$ x $P$ x $S + background$

    or 1 for the beta correction:

    $I = (scale$ x $volfraction / volume)$ x $( <FF>$ + $<F>^2 (S-1) ) + background$

    where $F$

  More options may appear here in future as more complicated operations are
  added.

References
^^^^^^^^^^

.. [#] Kotlarchyk, M.; Chen, S.-H. *J. Chem. Phys.*, 1983, 79, 2461

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

*Document History*

| 2019-03-29 Paul Kienzle & Steve King
