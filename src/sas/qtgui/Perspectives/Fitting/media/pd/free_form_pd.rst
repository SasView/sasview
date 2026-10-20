.. free_form_pd.rst

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. _free_form_pd:

Free-Form Polydispersity Inversion
===================================

.. note:: In Windows use [Alt]-[Cursor left] to return to the previous page

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Overview
^^^^^^^^

Small Angle Scattering (SAS) — from both X-ray (SAXS) and neutron (SANS)
sources — is used to probe the nanoscale structure of materials. A SAS
experiment records the scattered intensity :math:`I(q)` as a function of the
scattering vector

.. math::

   q = \frac{4\pi}{\lambda}\sin\left(\frac{\theta}{2}\right)

where :math:`\lambda` is the radiation wavelength and :math:`\theta` is the
scattering angle. For small angles this simplifies to
:math:`q \approx \frac {2\pi} \lambda \theta`, i.e. the deflection angle normalised by
the wavelength.

**Form factors (Green's functions)**

The *form factor* :math:`F(q)` describes the intensity scattered by a *single*
nanoparticle across the full q-range — its SAS fingerprint. For a sphere of
radius :math:`r` the form factor is

.. math::
   F(q, r) = \left[ V(r)\Delta\rho \dfrac{3j_1(qr)}{qr} \right]^2

where :math:`j_1` is the spherical Bessel function of the first kind,
:math:`V(r)` the sphere volume, and
:math:`\Delta\rho = \rho_\text{particle} - \rho_\text{solvent}` the
scattering length density contrast.

**Polydispersity**

In a real experiment the sample contains a *population* of nanoparticles whose
sizes (and possibly shapes) vary. This is called *polydispersity*. The
measured intensity is then an average over the distribution :math:`w(r)`:

.. math::

   I(q) = \int F(q, r)\, w(r)\, dr


.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Supported Models
^^^^^^^^^^^^^^^^

Free-form inversion is currently available for the following models:

* **sphere** — recovers the number-size distribution :math:`f(r)` over radius :math:`r`
* **cylinder** — recovers the joint distribution :math:`f(r, L)` over radius :math:`r`
  and length :math:`L`
* **ellipsoid** — recovers the joint distribution :math:`f(r_p, r_e)` over the polar
  radius :math:`r_p` and equatorial radius :math:`r_e`

For all models, the contrast
:math:`\Delta\rho = \rho_\text{particle} - \rho_\text{solvent}` must be
non-zero (i.e. ``sld`` and ``sld_solvent`` must differ).

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

How to Use
^^^^^^^^^^

1. **Load data and select a model** as usual in the Fitting panel. The
   free-form tool supports the models listed above; choose one from the Model
   dropdown.

2. **Set contrast parameters.** In the *Parameters* tab, ensure that ``sld``
   and ``sld_solvent`` have different values. The inversion uses the contrast
   :math:`\Delta\rho` to return ``scale`` as a SasView volume fraction. Other
   model parameters (e.g. background) start from whatever values are shown in
   the table.

3. **Enable free-form mode.** In the *Options* panel (right-hand side of the
   Fitting tab), check the **Free Form** checkbox. Checking *Free Form* automatically
   enables and locks the *Polydispersity* checkbox, and switches the *Polydispersity* tab into free-form mode.

4. **Configure the distribution grid** in the *Polydispersity* tab. In
   free-form mode the table shows only three editable columns for each
   geometric parameter:

   ============  ================================================================
   **Min**       Lower bound of the size grid (in Å)
   **Max**       Upper bound of the size grid (in Å)
   **N bins**    Number of discretization bins across [Min, Max]
   ============  ================================================================

   Set Min and Max to bracket the expected size range. More bins give a finer
   distribution but increase computation time.


5. **Set the smoothness regularization weight** in the **Smoothness**
   (:math:`\lambda`) field below the distribution table. The default value of
   0.25 is a reasonable starting point. Increase :math:`\lambda` for a
   smoother (broader) distribution; decrease it to allow sharper features (at
   the risk of over-fitting noise).

6. **Click Fit.** The inversion runs using the GALAHAD optimizer. On
   completion:

   * ``scale`` and ``background`` in the *Parameters* table are updated with
     the values returned by the inversion.
   * The fitted theory curve is overlaid on the data plot.
   * A residuals plot is produced in the usual way.
   * One or more **distribution plots** appear, showing :math:`f(r)`.
.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Notes and Caveats
^^^^^^^^^^^^^^^^^

**Smoothness regularization**
   In Free-form inversion many distributions can
   explain the data equally well within the measurement uncertainties. The
   smoothness parameter :math:`\lambda` stabilizes the solution by penalizing
   rapidly varying distributions. Choosing :math:`\lambda` is a trade-off:

   * Too large — the recovered distribution is over-smoothed and broad, masking
     real features.
   * Too small — the distribution becomes noisy and may fit measurement artefacts.

   A chi-squared value near 1 indicates a good fit.

**Resolution smearing**
   If a resolution function has been set on the *Resolution* tab, it is
   applied to the Green's tensor before inversion (exactly as for a standard
   fit). No additional steps are required.

**GPU acceleration**
   The ``ffsi`` package uses GPU-accelerated linear algebra (via CuPy) when
   a compatible GPU and CuPy are available in the environment, and falls back to NumPy on CPU
   otherwise. No configuration is required; the backend is selected
   automatically at run time. We have not added cupy as a dependency as it would
   increase the bundle size by a lot. Enabling this GPU features on install requires further work.

**1D data only**
   Free-form inversion currently supports 1D averaged :math:`I(q)`
   data. 2D support is coming soon.

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

| 2026-10-06 Yugal Khanal, STFC SCD
