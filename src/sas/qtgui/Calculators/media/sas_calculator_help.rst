.. sas_calculator_help.rst

.. This is a port of the original SasView html help file to ReSTructured text
.. by S King, ISIS, during SasView CodeCamp-III in Feb 2015.

.. _SANS_Calculator_Tool:

Generic SANS Calculator Tool
============================

Description
-----------

This tool attempts to simulate the SANS expected from a specified
shape/structure or scattering length density profile. The tool can
handle both nuclear and magnetic contributions to the scattering.

Theory
------

A SANS sample can be described (for the purposes of this calculator) in two
different ways, either by rectangular pixels (grid type data), or 
by finite elements (element type data), which can be many shapes, such as 
tetrahedra, cubes or hexahedra.

The scattering length density (SLD) of each pixel or element, where the SLD is
uniform, is a combination of the nuclear and magnetic SLDs and depends on the spin
states of the neutrons as described in the Magnetic Scattering section.


Grid Type Data
^^^^^^^^^^^^^^

In general, a particle with a volume $V$ can be described by an ensemble
containing $N$ 3-dimensional rectangular pixels where each pixel is much
smaller than $V$.

Assuming that all the pixel sizes are the same, the elastic scattering
intensity from the particle is defined as

.. math::

    I(\mathbf{Q}) = \frac{1}{V}\left\lvert\sum_j^N v_j\beta_j\exp(i\mathbf{Q}\cdot\mathbf{r_j})\right\rvert^2\tag{Eq. 1}

where $\beta_j$ and $\mathbf{r_j}$ are the scattering length density and
the position of the $j^\text{th}$ pixel respectively.

The total volume $V$ is equal to

.. math::

    V = \sum_j^N v_j

for $\beta_j \ne 0$ where $v_j$ is the volume of the $j^\text{th}$
pixel or the $j^\text{th}$ natural atomic volume. For atomic structures 
$v_j \beta_j \equiv b_j$ is the scattering length of the $j^\text{th}$ atom and the natural atomic
volume is given by:

   $\frac{\text{atomic mass}}{\text{natural molar density}\times\text{Avogadro number}}$

$V$ can be corrected by users (input parameter *Total volume*). This correction
is useful especially for an atomic structure (such as taken from a PDB file)
to get the right normalization.

*NOTE!* $\beta_j$ *displayed in the GUI may be incorrect (input parameter* solvent_SLD *)
but this will not affect the scattering computation if the
correction of the total volume V is made.*

Element Type Data
^^^^^^^^^^^^^^

The simulation box can be described by a collection of finite elements, forming a
mesh. Each element occupying space $V_j$ has an associated scattering length density 
($\beta_j$) and the elastic scattering intensity is calculated as

.. math::

    I(\mathbf{Q}) = \frac{1}{V}\left\lvert\sum_j^N \beta_j\iiint\limits_{V_j}\exp(i\mathbf{Q}\cdot\mathbf{r_j})\text{d}V\right\rvert^2\tag{Eq. 2}


That is to say a full fourier transform is calculated over each element - allowing
regions of space with little variation in $\beta$ to have larger finite elements,
and other regions to have much smaller finite elements, and hence more detail.

In Sasview this fourier transform is calculated using the divergence theorem, in an
algorithm heavily based on that given by Maranville [#MARANVILLE1]_

Magnetic Scattering
^^^^^^^^^^^^^^^^^^^

For information about polarised and magnetic scattering, see
the :ref:`magnetism` documentation.


.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

Using The Tool
--------------

.. figure:: gen_gui_help.png

   ..

   1) Load .sld, .pdb, .omf or .vtk datafile. Further description of each file type is below.
      The program can load in up to two files - one to describe the nuclear SLDs and one to
      describe the magnetic SLDs. The checkboxes can be used to enable or disable a loaded file.
      If both files are enabled they must describe the same pixels/elements in real space - this is
      verified by the program.
   2) Select default shape of sample.
   3) Draw magnetisation with arrows (not recommended for a large number of
      pixels/elements).
   4) Variables describing the instrument setup for polarisation. These options are only enabled
      when magnetic SLDs are non-zero - because otherwise they have no effect.
       * up_frac_in describes the fraction of neutrons polarised up (+/total) before the sample
       * up_frac_out describes the fraction of neutrons polarised up (+/total) after the analyser
       * up_theta is the polar angle of the polarisation in degrees from z axis to x-y plane
       * up_phi is the azimuthal angle of the polarisation in degrees around the x-y plane
   5) The background intensity of the detector.
   6) A relative scaling factor for the output intensity.
   7) The SLD of the solvent for the sample.
   8) The default volume calculated from the pixel info
      (or natural density of pdb file).
   9) Set the resolution of the scattering pattern.
       * No. of Qx (Qy) bins is the number of 'pixels' (bins) in Q space on each axis
       * Qx (Qy) Max is the maximum value of Q to calculate on each axis
      In some circumstances these textboxes will be highlighted orange, a warning that with
      the values chosen numerical artifacts may appear due to the Nyquist criterion, or simulation box
      size.
   10) The number of pixels/elements under consideration.
   11) The mean SLD, both nuclear SLD and all 3 components of the magnetic SLD. If a nuclear/magnetic file
       is enabled then the nuclear/magnetic SLD textboxes are read only. If no file is enabled then the
       respective textboxes can be edited - and the value supplied is taken to be a constant across all
       pixels/elements.
   12) For grid type data these values specify the number of pixels in the x,y and z directions respectively.
   13) For grid type data these values specify the spacing between pixels in the x,y and z directions.
   14) Draw the pixels/atoms without magnetisation arrows.
   15) Save the current data into a .sld file. This combines the currently enabled files with any values altered
       in the GUI, and saves it to a file for later reuse. This functionality only works with grid type data.
   16) Whether to compute the full 2D scattering pattern, or calculate the average intensity at magnitude Q. Note
       that the ability to directly produce a 1D average plot with this tool is only available for grid type data 
       with no magnetic SLD.
   17) Compute the scattering pattern.
   18) Reset GUI to initial state.
   
   
For example the default starting values with no files enabled (as shown) specify a rectangular grid of 10x10x10 pixels, with 
each pixel being $6x6x6\require{unicode}\unicode{x212B}$. Each pixel has a constant nuclear SLD of $6.97\times10^{-6}\require{unicode}\unicode{x212B}^{-2}$
and no magnetic SLD.

.. After computation the result will appear in the *Theory* box in the SasView *Data Explorer* panel.

*Up_frac_in* and *Up_frac_out* are the ratio

   $\frac{\text{spin up}}{\text{spin up} + \text{spin down}}$

of neutrons before the sample and at the analyzer, respectively.

*NOTE 1. The values of Up_frac_in and Up_frac_out must be in the range
0.0 to 1.0. Both values are 0.5 for unpolarized neutrons.*

*NOTE 2. This computation is totally based on the pixel (or atomic) data fixed
in xyz coordinates. No angular orientational averaging is considered.*

*NOTE 3. For the nuclear scattering length density, only the real component
is taken into account.*

*NOTE 4. When 1D averaging is enabled (Eq. 1) above is replaced by the Debye equation
(Eq. 3).*

.. math::

   I(\left\lvert\mathbf{Q}\right\rvert) = \frac{1}{V}\sum_j^N v_j\beta_j \sum_k^N v_k\beta_k 
   \frac{\sin\left(\left\lvert\mathbf{Q}\right\rvert\left\lvert\mathbf{r_j}-\mathbf{r_k}\right\rvert\right)}
   {\left\lvert\mathbf{Q}\right\rvert\left\lvert\mathbf{r_j}-\mathbf{r_k}\right\rvert}\tag{Eq. 3}

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

File Types
--------------------------

SLD Files
^^^^^^^^^

An SLD file is a text file format capable of storing grid type data with both nuclear and magnetic
SLDs. The file format for an SLD file is as follows:

   * One line of header information - this is unused by the program and can contain any information
   * N lines describing N pixels, of 4, 6, 7 or 8 columns, separated by whitespace. All lines must 
      have the same number of columns, and the data in each column must be castable to a float.
       * 4 columns describe *x position*, *y position*, *z position*, *nuclear SLD*
       * 6 columns describe *x position*, *y position*, *z position*, *magnetic SLD (x, y, z components)*
       * 7 columns describe *x position*, *y position*, *z position*, *nuclear SLD*, *magnetic SLD (x, y, z components)*
       * 8 columns describe *x position*, *y position*, *z position*, *nuclear SLD*, *magnetic SLD (x, y, z components)*, *pixel volume*

The file specification does not guarantee that the pixels form a rectangular grid - however this is required for
the output of the scattering calculator to be correct. The program does NOT check this.

PDB Files
^^^^^^^^^

A PDB file is a text file format which can store atomic structure data. The specification is given
`here <https://www.wwpdb.org/documentation/file-format>`_. This format is read as grid type data and can be used
to create nuclear SLDs only.

Note that Sasview only reads ATOM and CONECT records from these files. ATOM records are used to create
suitable nuclear SLDs and pixel volumes using data from the `periodictable <https://pypi.org/project/periodictable/>`_ 
python package. CONECT records are only used when drawing the structure.

OMF Files
^^^^^^^^^

An OMF file is a file format capable of storing spatial fields for grid type data. The specification can be found
`here <https://math.nist.gov/oommf/doc/userguide20a2/userguide/Vector_Field_File_Format_OV.html>`_. While the OVF 2.0
format could technically store both nuclear and magnetic sld data, Sasview currently reads all OMF files as if they were 
OVF 1.0 or lower, and as such OMF files can only be used to read in data to create magnetic SLDs. Unlike SLD files, OMF
files are expected to store the magnetisation vector $\mathbf{M}$, not the magentic SLD. 

While there is no explicit check within the program only OMF files with meshtype: rectangular can be read into the program 
correctly. Additionally the data must be stored as 'Text' (ASCII format), Sasview cannot read in binary data.

VTK Files
^^^^^^^^^

The VTK file format is a very broad set of file formats, specifically Sasview currently reads in "legacy" .vtk files,
up to version 3.0.
The file specification is available `here <https://vtk.org/wp-content/uploads/2015/04/file-formats.pdf>`_. Currently
Sasview only reads in the 'unstructured grid' dataset format, and while any file of this form can be loaded, only
files in which all cells are of the same type (type=10 (tetrahedron), 11 (voxel), 12 (hexahedron)) can be used to
compute scattering patterns. While this may seem restrictive it merely requires that every element has the same number
of faces, and every face the same number of vertices.

VTK files are treated as element type data - and can contain magnetic and/or nuclear SLDs. The nuclear SLD is identified
with a set of SCALAR data with one component. The magnetic SLD is identified with a set of SCALAR data with three
components or as a set of VECTOR data. If the data is provided to the points of the mesh and not the cells, a weighted
average is taken to find an estimate for the SLD at the centre of each element. This weighted average is given by:

.. math::

   \bar{\beta} = \frac{\sum\limits_j^n \beta_j r_j^{\prime -2}}{\sum\limits_j^n r_j^{\prime -2}}

Where $\bar{\beta}$ is the estimated SLD for an element and $\beta_j$, $r'_j$ are the SLDs and distances from the
centre of the element of each of the n vertices of the element respectively. $r'_j$ is taken as:

.. math::

   r^\prime_j = \left\lvert \mathbf{r_j} - \frac{1}{n}\sum_k^n \mathbf{r_k} \right\rvert

where $\mathbf{r_k}$ are the position vectors of the n vertices of the element.

References 
----------

    .. [#MARANVILLE1] An implementation of an efficient direct Fourier transform of polygonal areas and volumes
         (2021) `arXiv:2104.08309 <https://arxiv.org/abs/2104.08309>`_

.. ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ

.. note::  This help document was last changed by Robert Bourne, 12 August 2021
