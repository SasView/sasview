.. mumag_help.rst

MuMag Tool
==========

format of data files
--------------------

The experimental magnetic SANS data is expected to be stored in a separat folder for example named ExperimentalSANSData. Several informations of the experimental data must be given through the file names stored in the folder ExperimentalSANSData, as seen in the following:

	expected filenames:

		- 1_0_1340_10.csv
		- 2_20_1340_10.csv
		- 3_35_1340_10.csv
		- 4_50_1340_10.csv
		- ...

   1. Identifier: Index of the files (e.g. 1, 2, 3, 4, ...)
   2. Identifier: Externally applied magnetic field μ_0 H_0 in mT (e.g. 0, 20, 25, 50, ...)
   3. Identifier: Saturation magnetization μ_0 M_s in mT (e.g. 1340, 1340, 1340, 1340, ...)
   4. Identifier: Demagnetization field μ_0 H_d in mT (e.g. 10, 10, 10, 10, 10, ...)

	(All these values could also be written as float number with dot separator e.g. 10.4345)

Format of the data files:

+------------+------------+------------+
| q [1/nm]   |  I(q)      |  std       |
+============+============+============+
|3.62523e-2  |2.85917e+3  |2.28223e+1  |
+------------+------------+------------+
|4.07000e-2  |1.03769e+3  |1.39076e+1  |
+------------+------------+------------+
|4.51118e-2  |4.61741e+2  |9.64427e+1  |
+------------+------------+------------+
|4.95924e-2  |2.83047e+2  |7.65175e+1  |
+------------+------------+------------+

Each of the files must have the same length and got to be sorted from the lowest to the highest q-value. In the files only the numerical data is stored, no headers.

