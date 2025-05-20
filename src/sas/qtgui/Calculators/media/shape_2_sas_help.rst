.. shape_2_sas_help.rst

.. by J Krzywon, NIST, May 2025

.. _Shape2SAS_Tool:

Shape2SAS
=========

Description
-----------

This tool allows the user to build particles from a series of predefined shapes. By allowing particles to be placed in
any location, or orientation relative to an origin, many unique structures can be constructed. Once a structure is
created, the user can generate a theoretical data set that can be analysed, or an empirical fitting model can be
generated to compare the structure to real data.

Please note, the particles are constructed from a series of 'atoms' randomly distributed within the defined shape.
Because of this randomness, creating the same particle two different times may result in subtle differences between
scattering curves and slight differences in the resulting empirical models.

The base shapes available to the user include spheres, cylinders, ellipsoids, elliptical cylinders, disks, cubes, cuboids,
hollow spheres, hollow cubes, and cylindrical rings. Each of the particles can be individually modified in all dimensions,
can be shifted relative to the origin, rotated relative to the particle centroid, and rotated relative to the coordinate
volume origin. The scattering length density, relative to the medium the particle is in, can also be defined. If the
particle is in air, this should be considered the scattering length density of the particle material.

Using the Tool
--------------

.. image:: main_window.png

When the tool is first selected from the menu option, the 'Build Model' tab will open. The user can select a shape and
'Add' it to the table in the center of the window. The first row of the table is the particle shape, the second row is
the scattering length density relative to the solvent, the next three rows are particle dimensions which vary between
shapes, the sixth through eighth rows are to position the particle in space, the ninth through eleventh rows are for
particle rotation about the particle centroid, and 12th through 15th rows are to rotate the particle relative to the
coordinate origin, and the last row defines the particle color.

Once a series of shapes is defined, the 3D rendering and predicted SAS scattering can be calculated by clicking Plot.
The 'Include Scattering' checkbox must be selected for the SAS data calculation. If the resulting image does not look
as expected, modify the shape table and rerun the calculation until everything is as desired. By default, any overlap in
shapes is ignored in the shape construction and scattering calculation. To change this, uncheck the 'Exclude overlap'
option to account for any differences in SLD in the overlap region and visualize the particle overlap.

Parameter list for each shape particle

+----------------+-------------------+-------------------+
| Row | Parameter | Description |
+================+===================+===================+
|| 1 || Particle name || The shape selected from the predefined shapes in the combobox |
|| 2 || ΔSLD || The SLD of the particle relative to the medium surrounding it. Defaults to 1.0 |
|| 3, 4, and 5 || Size Definitions || The sizes for each major axis of the particle, in Å. The actual values will vary based on the shape. |
|| 6 || COMX || The relative offset along the X axis of the particle centroid from the coordinate origin, in Å. |
|| 7 || COMY || The relative offset along the Y axis of the particle centroid from the coordinate origin, in Å. |
|| 8 || COMZ || The relative offset along the Z axis of the particle centroid from the coordinate origin, in Å. |
|| 9 || RPX || The center of rotation of the particle, along the X axis, relative to the coordinate origin, in Å. |
|| 10 || RPY || The center of rotation of the particle, along the Y axis, relative to the coordinate origin, in Å. |
|| 11 || RPZ || The center of rotation of the particle, along the Z axis, relative to the coordinate origin, in Å. |
|| 12 || α || The rotation of the particle, around the X axis, relative to RPX, in degrees. |
|| 13 || β || The rotation of the particle, around the Y axis, relative to RPX, in degrees. |
|| 14 || γ || The rotation of the particle, around the Z axis, relative to RPX, in degrees. |


.. image:: saxs_virtual_experiment.png

Once the particle is of the expected form, a few more options are available. The first is the option to generate an
empirical model based on the scattering pattern using the 'To plugin model' button. This will generate a plugin model that
can be used to fit real data. The second option is to run a 'Virtual SAXS Experiment' in the second tab of the window.
In the second tab, set the Q range, the number of Q points, the number of P(r) points, the number of simulated points
within the 3D volume, and any structure factor contributions that may arise. The resulting theoretical curve can be sent
to the data explorer where the data set may be treated as any other data set loaded from a file.

References
----------

This tool has been adapted from the tool available at https://somo.chem.utk.edu/shape2sas/, which is based on the paper
by Larsen, et. al. https://scripts.iucr.org/cgi-bin/paper?jl5064.