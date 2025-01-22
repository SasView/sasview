.. mumag_help.rst

MuMag Tool
==========

Introduction
------------

MuMag is an analysis tool for calculating exchange stiffness constants, residual scattering, anisotropy field
and longitudinal magnetization based on unpolarized 1D SANS experiments with applied magnetic fields. The theory
behind this has been published `here <https://doi.org/10.1107/S1600576722005349>`_.

Given some scattering curve recorded at different applied field intensities, :math:`I(q, H)`, MuMag will break
down these curves into two (in the case of parallel magnetic fields) and three, components (
for perpendicular fields relative to the beam). In the perpendicular case, the resulting linear
decomposition has the following form:

:math:`I(q, H) = I_res(q) + S_H(q) R_H(q, H) + S_M(q) R_M(q, H)`

Where :math:`R_H` and :math:`R_M` are known magnetic response functions (see the paper above), and :math:`I_res`,
:math:`S_H` and :math:`S_M` are non-field dependent terms: the residual scattering function,
the anisotropy field scattering function and the longitudinal magnetisation scattering function respectively.

In the parallel case :math:`S_M` and :math:`R_M` are zero.


Loading data
------------

To load data click on the `Import Data` button. This will give you a file chooser that allows you to select a
**directory**. This directory should contain multiple files for measurements taken with different applied magnetic fields.

Currently, *the magnetic field and other information is expected to be in the filename with a format as described below*

Form of Data Files
..................

The experimental magnetic SANS data for a given analysis is expected to be stored as CSV files in a single folder.
Information about each SANS scattering curve  must be given through the file names, like in the following example:

Example filenames:

- 1_0_1340_10.csv
- 2_20_1340_10.csv
- 3_35_1340_10.csv
- 4_50_1340_10.csv
- ...

The fields separated by underscores have the following meaning

1. Index of the files (e.g. 1, 2, 3, 4, ...) - (not used by SasView's MuMag, but is used by the MATLAB version)
2. Externally applied magnetic field :math:`μ_0 H_0` in mT (e.g. 0, 20, 25, 50, ...)
3. Saturation magnetization :math:`μ_0 M_s` in mT (e.g. 1340, 1340, 1340, 1340, ...)
4. Demagnetization field :math:`μ_0 H_d` in mT (e.g. 10, 10, 10, 10, 10, ...)

(All these values could also be written as float number with dot separator e.g. 10.4345)

The CSV files are expected have three columns: momentum transfer :math:`q` in nm :math:`^{-1}`,
scattering intensity :math:`I(q)`, and the standard error corresponding to `I(q)`.

Each of the files must have the same length and be sorted from lowest to highest q-value.
In the files only the numerical data is stored, no headers.

Running MuMag
-------------

To run MuMag, load the data, set the parameters below, and click `Fit`.

Parameters
..........

* **Analysis method** - This chooses one of two experiment types. Perpendicular is where the applied field is perpendicular to the beam (e.g. beam in x direction and field in z), and parallel where the applied field is parallel.
* **Maximum q** - MuMag has the ability to exclude q values beyond a given value, specified here
* **Applied field** - MuMag will use only data with applied field strengths above this value. MuMag requires the sample to be at (or close to) saturation, use this field to specify where this is.
* **Scan range** - When calculating the exchange stiffness constant A, MuMag's minimisation step has two components. (1) A brute for search, then (2) a refinement. These three values that describe the values for which the brute force search will take place (start, stop and step), as well as the values used for related plots.

Results
.......

* **A value** - The estimated exchange stiffness constant (A)
* **A uncertainty** - An estimate of the uncertainty associated with it

Plots
.....


When you load data the `data` plot will be populated. When you click `fit` the rest will be.

* **Data** - A plot of all the loaded data
* **Fit Results**
    * :math:`\chi^2` - figure of merit used by MuMag to calculate the best A value, across different values of A (currently mean squared). This plot is useful to checking your problem is well conditioned.
    * :math:`I_res` - The *residual intensity* - the part of the scattering that doesn't respond to applied field changes, inferred from the data (see above for details)
    * :math:`S_H` - Anisotropy field scattering function
    * :math:`S_M` - Scattering function of the longitudinal magnetization
* **Comparison** - Crosses show original data, lines show scattering curves reconstructed based on :math:`I_res`, :math:`S_H` and :math:`S_M`
