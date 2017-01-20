Test data sets are included as a convenience to our users. The data sets are organized based on their data structure; 1D data (ie, I(Q)), 2D data (ie, I(Qx,Qy)), coordinate data (eg, PDB files), image data (eg, TIFF files), SasView saved states, SESANS data, and data in formats that are not yet implemented but which are in the works for future releases.

1D data sets EITHER a) have at least two columns of data with I(abs. units) on the y-axis and Q on the x-axis, OR b) have I and Q in separate files. Data in the latter format (/convertible_files) need to be converted to a single file format with the File Converter tool before SasView will analyse them.

2D data sets are data sets that give the deduced intensity for each detector pixel. Depending on the file extension, uncertainty and metadata may also be available.

Coordinate data sets are designed to be read by the Generic Scattering Calculator tool.

Image data sets are designed to be read by the Image Viewer tool.

Save states are projects and analyses saved by the SASVIEW program. A single analysis file contains the data and parameters for a single fit (.fit), p(r) inversion (.pr), or invariant calculation (.inv). A project file (.svs) contains the results for every active analysis.

SESANS data sets primarily contain the neutron polarisation as a function of the spin-echo length.
