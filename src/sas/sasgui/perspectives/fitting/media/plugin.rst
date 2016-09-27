.. _Writing_a_Plugin:

Writing a Plugin Model
======================

Overview
^^^^^^^^

You can write your own model and save it to the the SasView
*plugin_models* folder

  *C:\\Users\\[username]\\.sasview\\plugin_models* (on Windows)

The next time SasView is started it will compile the plugin and add
it to the list of *Customized Models* in a FitPage.  It is recommended that an
existing model be used as a template.

SasView has three ways of writing models:

- As a pure python model : Example -
  `broadpeak.py <https://github.com/SasView/sasmodels/blob/master/sasmodels/models/broad_peak.py>`_
- As a python model with embedded C : Example -
  `sphere.py <https://github.com/SasView/sasmodels/blob/master/sasmodels/models/sphere.py>`_
- As a python wrapper with separate C code : Example -
  `cylinder.py <https://github.com/SasView/sasmodels/blob/master/sasmodels/models/cylinder.py>`_,
  `cylinder.c <https://github.com/SasView/sasmodels/blob/master/sasmodels/models/cylinder.c>`_

The built-in modules are available in the *sasmodels-data\\models* subdirectory
of your SasView installation folder.  On Windows, this will be something like
*C:\\Program Files (x86)\\SasView\\sasmodels-data\\models*.  On Mac OSX, these will be within
the application bundle as
*/Applications/SasView 4.0.app/Contents/Resources/sasmodels-data/models*.

Other models are available for download from our
`Model Marketplace <http://marketplace.sasview.org/>`_. You can contribute your own models to the 
Marketplace aswell.

Create New Model Files
^^^^^^^^^^^^^^^^^^^^^^

In the *~\\.sasview\\plugin_models* directory, copy the appropriate files
(using the examples above as templates) to mymodel.py (and mymodel.c, etc)
as required, where "mymodel" is the name for the model you are creating.

*Please follow these naming rules:*

- No capitalization and thus no CamelCase
- If necessary use underscore to separate words (i.e. barbell not BarBell or
  broad_peak not BroadPeak)
- Do not include “model” in the name (i.e. barbell not BarBellModel)


Edit New Model Files
^^^^^^^^^^^^^^^^^^^^

Model Contents
..............

The model interface definition is in the .py file.  This file contains:

- a **model name**:
   - this is the **name** string in the *.py* file
   - titles should be:

    - all in *lower* case
    - without spaces (use underscores to separate words instead)
    - without any capitalization or CamelCase
    - without incorporating the word "model"
    - examples: *barbell* **not** *BarBell*; *broad_peak* **not** *BroadPeak*; 
      *barbell* **not** *BarBellModel*

- a **model title**:
   - this is the **title** string in the *.py* file
   - this is a one or two line description of the model, which will appear
     at the start of the model documentation and as a tooltip in the SasView GUI

- a **short discription**:
   - this is the **description** string in the *.py* file
   - this is a medium length description which appears when you click
     *Description* on the model FitPage

- a **parameter table**:
   - this will be auto-generated from the *parameters* in the *.py* file

- a **long description**:
   - this is ReStructuredText enclosed between the r""" and """ delimiters
     at the top of the *.py* file
   - what you write here is abstracted into the SasView help documentation
   - this is what other users will refer to when they want to know what your model does; 
     so please be helpful!

- a **definition** of the model:
   - as part of the **long description**

- a **formula** defining the function the model calculates:
   - as part of the **long description**

- an **explanation of the parameters**:
   - as part of the **long description**
   - explaining how the symbols in the formula map to the model parameters

- a **plot** of the function, with a **figure caption**:
   - this is automatically generated from your default parameters

- at least one **reference**:
   - as part of the **long description**
   - specifying where the reader can obtain more information about the model

- the **name of the author**
   - as part of the **long description**
   - the *.py* file should also contain a comment identifying *who*
     converted/created the model file

Models that do not conform to these requirements will *never* be incorporated 
into the built-in library.

More complete documentation for the sasmodels package can be found at
`<http://www.sasview.org/sasmodels>`_. In particular,
`<http://www.sasview.org/sasmodels/api/generate.html#module-sasmodels.generate>`_
describes the structure of a model.


Model Documentation
...................

The *.py* file starts with an r (for raw) and three sets of quotes
to start the doc string and ends with a second set of three quotes.
For example::

    r"""
    Definition
    ----------

    The 1D scattering intensity of the sphere is calculated in the following
    way (Guinier, 1955)

    .. math::

        I(q) = \frac{\text{scale}}{V} \cdot \left[
            3V(\Delta\rho) \cdot \frac{\sin(qr) - qr\cos(qr))}{(qr)^3}
            \right]^2 + \text{background}

    where *scale* is a volume fraction, $V$ is the volume of the scatterer,
    $r$ is the radius of the sphere and *background* is the background level.
    *sld* and *sld_solvent* are the scattering length densities (SLDs) of the
    scatterer and the solvent respectively, whose difference is $\Delta\rho$.

    You can included figures in your documentation, as in the following
    figure for the cylinder model.

    .. figure:: img/cylinder_angle_definition.jpg

        Definition of the angles for oriented cylinders.

    References
    ----------

    A Guinier, G Fournet, *Small-Angle Scattering of X-Rays*,
    John Wiley and Sons, New York, (1955)
    """

This is where the FULL documentation for the model goes (to be picked up by
the automatic documentation system).  Although it feels odd, you
should start the documentation immediately with the **definition**---the model
name, a brief description and the parameter table are automatically inserted
above the definition, and the a plot of the model is automatically inserted
before the **reference**.

Figures can be included using the *figure* command, with the name
of the *.png* file containing the figure and a caption to appear below the
figure.  Figure numbers will be added automatically.

See this `Sphinx cheat sheet <http://matplotlib.org/sampledoc/cheatsheet.html>`_
for a quick guide to the documentation layout commands, or the
`Sphinx Documentation <http://www.sphinx-doc.org/en/stable/>`_ for
complete details.

The model should include a **formula** written using LaTeX markup.
The example above uses the *math* command to make a displayed equation.  You
can also use *\$formula\$* for an inline formula. This is handy for defining
the relationship between the model parameters and formula variables, such
as the phrase "\$r\$ is the radius" used above.  The live demo MathJax
page `<http://www.mathjax.org/>`_ is handy for checking that the equations
will look like you intend.

Math layout uses the `amsmath <http://www.ams.org/publications/authors/tex/amslatex>`_
package for aligning equations (see amsldoc.pdf on that page for complete documentation).
You will automatically be in an aligned environment, with blank lines separating
the lines of the equation.  Place an ampersand before the operator on which to
align.  For example::

    .. math::

      x + y &= 1 \\
      y &= x - 1

produces

.. math::

      x + y &= 1 \\
      y &= x - 1

If you need more control, use::

    .. math::
        :nowrap:


Model Definition
................

Following the documentation string, there are a series of definitions::

    name = "sphere"  # optional: defaults to the filename without .py

    title = "Spheres with uniform scattering length density"

    description = """\
    P(q)=(scale/V)*[3V(sld-sld_solvent)*(sin(qr)-qr cos(qr))
                    /(qr)^3]^2 + background
        r: radius of sphere
        V: The volume of the scatter
        sld: the SLD of the sphere
        sld_solvent: the SLD of the solvent
    """

    category = "shape:sphere"

    single = True   # optional: defaults to True

    opencl = False  # optional: defaults to False

    structure_factor = False  # optional: defaults to False

**name = "mymodel"** defines the name of the model that is shown to the user.
If it is not provided, it will use the name of the model file, with '_'
replaced by spaces and the parts capitalized.  So *adsorbed_layer.py* will
become *Adsorbed Layer*.  The predefined models all use the name of the
model file as the name of the model, so the default may be changed.

**title = "short description"** is short description of the model which
is included after the model name in the automatically generated documentation.
The title can also be used for a tooltip.

**description = """doc string"""** is a longer description of the model. It
shows up when you press the "Description" button of the SasView FitPage.
It should give a brief description of the equation and the parameters
without the need to read the entire model documentation. The triple quotes
allow you to write the description over multiple lines. Keep the lines
short since the GUI will wrap each one separately if they are too long.
**Make sure the parameter names in the description match the model definition!**

**category = "shape:sphere"** defines where the model will appear in the
model documentation.  In this example, the model will appear alphabetically
in the list of spheroid models in the *Shape* category.

**single = True** indicates that the model can be run using single
precision floating point values.  Set it to False if the numerical
calculation for the model is unstable, which is the case for about 20 of
the built in models.  It is worthwhile modifying the calculation to support
single precision, allowing models to run up to 10 times faster.  The
section `Test_Your_New_Model`_  describes how to compare model values for
single vs. double precision so you can decide if you need to set
single to False.

**opencl = False** indicates that the model should not be run using OpenCL.
This may be because the model definition includes code that cannot be
compiled for the GPU (for example, goto statements).  It can also be used
for large models which can't run on most GPUs.  This flag has not been
used on any of the built in models; models which were failing were
streamlined so this flag was not necessary.

**structure_factor = True** indicates that the model can be used as a
structure factor to account for interactions between particles.  See
`Form_Factors`_ for more details.

Model Parameters
................

Next comes the parameter table.  For example::

    # pylint: disable=bad-whitespace, line-too-long
    #   ["name",        "units", default, [min, max], "type",    "description"],
    parameters = [
        ["sld",         "1e-6/Ang^2",  1, [-inf, inf], "sld",    "Layer scattering length density"],
        ["sld_solvent", "1e-6/Ang^2",  6, [-inf, inf], "sld",    "Solvent scattering length density"],
        ["radius",      "Ang",        50, [0, inf],    "volume", "Sphere radius"],
    ]
    # pylint: enable=bad-whitespace, line-too-long

**parameters = [["name", "units", default, [min,max], "type", "tooltip"],...]**
defines the parameters that form the model.

**Note: The order of the parameters in the definition will be the order of the 
parameters in the user interface and the order of the parameters in Iq(), 
Iqxy() and form_volume(). And** *scale* **and** *background* **parameters are 
implicit to all models, so they do not need to be included in the parameter table.**

- **"name"** is the name of the parameter shown on the FitPage.

  - parameter names should follow the mathematical convention; e.g.,
    *radius_core* not *core_radius*, or *sld_solvent* not *solvent_sld*.

  - model parameter names should be consistent between different models,
    so *sld_solvent*, for example, should have exactly the same name
    in every model.

  - to see all the parameter names currently in use, type the following in the
    python shell/editor under the Tools menu::

       import sasmodels.list_pars
       sasmodels.list_pars.list_pars()

    *re-use* as many as possible!!!

  - use "name[n]" for multiplicity parameters, where *n* is the name of
    the parameter defining the number of shells/layers/segments, etc.

- **"units"** are displayed along with the parameter name

  - every parameter should have units; use "None" if there are no units.

  - **sld's should be given in units of 1e-6/Ang^2, and not simply
    1/Ang^2 to be consistent with the builtin models.  Adjust your formulas
    appropriately.**

  - fancy units markup is available for some units, including::

        Ang, 1/Ang, 1/Ang^2, 1e-6/Ang^2, degrees, 1/cm, Ang/cm, g/cm^3, mg/m^2

  - the list of units is defined in the variable *RST_UNITS* within
    `sasmodels/generate.py <https://github.com/SasView/sasmodels/tree/master/sasmodels/generate.py>`_

    - new units can be added using the macros defined in *doc/rst_prolog*
      in the sasmodels source.
    - units should be properly formatted using sub-/super-scripts
      and using negative exponents instead of the / operator, though
      the unit name should use the / operator for consistency.
    - please post a message to the SasView developers mailing list with your changes.

- **default** is the initial value for the parameter.

  - **the parameter default values are used to auto-generate a plot of
    the model function in the documentation.**

- **[min, max]** are the lower and upper limits on the parameter.

  - lower and upper limits can be any number, or *-inf* or *inf*.

  - the limits will show up as the default limits for the fit making it easy,
    for example, to force the radius to always be greater than zero.

- **"type"** can be one of: "", "sld", "volume", or "orientation".

  - "sld" parameters can have magnetic moments when fitting magnetic models;
    depending on the spin polarization of the beam and the $q$ value being
    examined, the effective sld for that material will be used to compute the
    scattered intensity.

  - "volume" parameters are passed to Iq(), Iqxy(), and form_volume(), and
    have polydispersity loops generated automatically.

  - "orientation" parameters are only passed to Iqxy(), and have angular
    dispersion.


Model Computation
.................

Models can be defined as pure python models, or they can be a mixture of
python and C models.  C models are run on the GPU if it is available,
otherwise they are compiled and run on the CPU.

Models are defined by the scattering kernel, which takes a set of parameter
values defining the shape, orientation and material, and returns the
expected scattering. Polydispersity and angular dispersion are defined
by the computational infrastructure.  Any parameters defined as "volume"
parameters are polydisperse, with polydispersity defined in proportion
to their value.  "orientation" parameters use angular dispersion defined
in degrees, and are not relative to the current angle.

Based on a weighting function $G(x)$ and a number of points $n$, the
computed value is

.. math::

     \hat I(q)
     = \frac{\int G(x) I(q, x)\,dx}{\int G(x) V(x)\,dx}
     \approx \frac{\sum_{i=1}^n G(x_i) I(q,x_i)}{\sum_{i=1}^n G(x_i) V(x_i)}

That is, the indivdual models do not need to include polydispersity
calculations, but instead rely on numerical integration to compute the
appropriately smeared pattern.   Angular dispersion values over polar angle
$\theta$ requires an additional $\cos \theta$ weighting due to decreased
arc length for the equatorial angle $\phi$ with increasing latitude.

Python Models
.............

For pure python models, define the *Iq* function::

      import numpy as np
      from numpy import cos, sin, ...

      def Iq(q, par1, par2, ...):
          return I(q, par1, par2, ...)
      Iq.vectorized = True

The parameters *par1, par2, ...* are the list of non-orientation parameters
to the model in the order that they appear in the parameter table.
**Note that the autogenerated model file uses** *x* **rather than** *q*.

The *.py* file should import trigonometric and exponential functions from
numpy rather than from math.  This lets us evaluate the model for the whole
range of $q$ values at once rather than looping over each $q$ separately in
python.  With $q$ as a vector, you cannot use if statements, but must instead
do tricks like

::

     a = x*q*(q>0) + y*q*(q<=0)

or

::

     a = np.empty_like(q)
     index = q>0
     a[index] = x*q[index]
     a[~index] = y*q[~index]

which sets $a$ to $q \cdot x$ if $q$ is positive or $q \cdot y$ if $q$
is zero or negative. If you have not converted your function to use $q$
vectors, you can set the following and it will only receive one $q$
value at a time::

    Iq.vectorized = False

Return np.NaN if the parameters are not valid (e.g., cap_radius < radius in
barbell).  If I(q; pars) is NaN for any $q$, then those parameters will be
ignored, and not included in the calculation of the weighted polydispersity.

Similar to *Iq*, you can define *Iqxy(qx, qy, par1, par2, ...)* where the
parameter list includes any orientation parameters.  If *Iqxy* is not defined,
then it will default to *Iqxy = Iq(sqrt(qx**2+qy**2), par1, par2, ...)*.

Models should define *form_volume(par1, par2, ...)* where the parameter
list includes the *volume* parameters in order.  This is used for a weighted
volume normalization so that scattering is on an absolute scale.  If
*form_volume* is not defined, then the default *form_volume = 1.0* will be
used.

Embedded C Models
.................

Like pure python models, inline C models need to define an *Iq* function::

    Iq = """
        return I(q, par1, par2, ...);
    """

This expands into the equivalent C code::

    #include <math.h>
    double Iq(double q, double par1, double par2, ...);
    double Iq(double q, double par1, double par2, ...)
    {
        return I(q, par1, par2, ...);
    }

The C model operates on a single $q$ value at a time.  The code will be
run in parallel across different $q$ values, either on the graphics card
or the processor.

Rather than returning NAN from Iq, you must define the *INVALID(v)*.  The
*v* parameter lets you access all the parameters in the model using
*v.par1*, *v.par2*, etc. For example::

    #define INVALID(v) (v.bell_radius < v.radius)

*Iqxy* is similar to *Iq*, except it uses parameters *qx, qy* instead of *q*,
and it includes orientation parameters. As in python models, *form_volume*
includes only the volume parameters.  *Iqxy* will default to
*Iq(sqrt(qx**2 + qy**2), par1, ...)* and *form_volume* will default to 1.0.

The C code follows the C99 standard, including the usual math functions,
as defined in
`OpenCL <https://www.khronos.org/registry/cl/sdk/1.1/docs/man/xhtml/mathFunctions.html>`_.

The standard constants and functions include the following::

    M_PI = pi
    M_PI_2 = pi/2
    M_PI_4 = pi/4
    M_E = e
    M_SQRT1_2 = 1/sqrt(2)
    NAN = NaN
    INFINITY = 1/0
    erf(x) = error function
    erfc(x) = 1-erf(x)
    expm1(x) = exp(x) - 1
    tgamma(x) = gamma function

Some non-standard constants and functions are also provided::

    M_PI_180 = pi/180
    M_4PI_3 = 4pi/3
    square(x) = x*x
    cube(x) = x*x*x
    sinc(x) = sin(x)/x, with sin(0)/0 -> 1
    SINCOS(x, s, c) sets s=sin(angle) and c=cos(angle)
    powr(x, y) = x^y for x >= 0
    pown(x, n) = x^n for n integer

**source=['lib/fn.c', ...]** includes the listed C source files in the
program before *Iq* and *Iqxy* are defined. This allows you to extend the
library of available C functions. Additional special functions and
scattering calculations are defined in
`sasmodels/models/lib <https://github.com/SasView/sasmodels/tree/master/sasmodels/models/lib>`_,
including::

    sph_j1c(x) = 3 j1(x)/x = 3 (sin(x) - x cos(x))/x^3  [spherical bessel function]
    sas_J1c(x) = 2 J1(x)/x  [bessel function of the first kind]
    sas_gamma(x) = gamma function  [tgamma is unstable below 1]
    sas_erf(x) = error function [erf is broken on some Intel OpenCL drivers]
    sas_erfc(x) = 1-erf(x)
    sas_J0(x) = J0(x)
    sas_J1(x) = J1(x)
    sas_JN(x) = JN(x)
    Si(x) = integral sin(z)/z from 0 to x
    Gauss76Wt = gaussian quadrature weights for 76 point integral
    Gauss76Z = gaussian quadrature values for 76 point integral

These functions have been tuned to be fast and numerically stable down
to $q=0$ even in single precision.  In some cases they work around bugs
which appear on some platforms but not others. So use them where needed!!!

Models are defined using double precision declarations for the
parameters and return values.  Declarations and constants will be converted
to float or long double depending on the precision requested.

**Floating point constants must include the decimal point.**  This allows us
to convert values such as 1.0 (double precision) to 1.0f (single precision)
so that expressions that use these values are not promoted to double precision
expressions.  Some graphics card drivers are confused when functions
that expect floating point values are passed integers, such as 4*atan(1); it
is safest to not use integers in floating point expressions.  Even better,
use the builtin constant M_PI rather than 4*atan(1); it is faster and smaller!

FLOAT_SIZE is the number of bytes in the converted variables. If your
algorithm depends on precision (which is not uncommon for numerical
algorithms), use the following::

    #if FLOAT_SIZE>4
    ... code for double precision ...
    #else
    ... code for single precision ...
    #endif

A value defined as SAS_DOUBLE will stay double precision; this should
not be used since some graphics cards do not support double precision.


External C Models
.................

External C models are very much like embedded C models, except that
*Iq*, *Iqxy* and *form_volume* are defined in an external source file
loaded using the *source=[...]*  method. You need to supply the function
declarations for each of these that you need instead of building them
automatically from the parameter table.


.. _Form_Factors:

Form Factors
............

Away from the dilute limit you can estimate scattering including
particle-particle interactions using $I(q) = P(q)*S(q)$ where $P(q)$
is the form factor and $S(q)$ is the structure factor.  The simplest
structure factor is the *hardsphere* interaction, which
uses the effective radius of the form factor as an input to the structure
factor model.  The effective radius is the average radius of the
form averaged over all the polydispersity values.

::

    def ER(radius, thickness):
        """Effective radius of a core-shell sphere."""
        return radius + thickness

Now consider the *core_shell_sphere*, which has a simple effective radius
equal to the radius of the core plus the thickness of the shell, as
shown above. Given polydispersity over *(r1, r2, ..., rm)* in radius and
*(t1, t2, ..., tn)* in thickness, *ER* is called with a mesh
grid covering all possible combinations of radius and thickness.
That is, *radius* is *(r1, r2, ..., rm, r1, r2, ..., rm, ...)*
and *thickness* is *(t1, t1, ... t1, t2, t2, ..., t2, ...)*.
The *ER* function returns one effective radius for each combination.
The effective radius calculator weights each of these according to
the polydispersity distributions and calls the structure factor
with the average *ER*.

::

    def VR(radius, thickness):
        """Sphere and shell volumes for a core-shell sphere."""
        whole = 4.0/3.0 * pi * (radius + thickness)**3
        core = 4.0/3.0 * pi * radius**3
        return whole, whole - core

Core-shell type models have an additional volume ratio which scales
the structure factor.  The *VR* function returns the volume of
the whole sphere and the volume of the shell. Like *ER*, there is
one return value for each point in the mesh grid.

*NOTE: we may be removing or modifying this feature soon. As of the 
time of writing, core-shell sphere returns (1., 1.) for VR, giving a volume
ratio of 1.0.*

Unit Tests
..........

THESE ARE VERY IMPORTANT. Include at least one test for each model and
PLEASE make sure that the answer value is correct (i.e. not a random number).

::

    tests = [
        [{}, 0.2, 0.726362],
        [{"scale": 1., "background": 0., "sld": 6., "sld_solvent": 1.,
          "radius": 120., "radius_pd": 0.2, "radius_pd_n":45},
         0.2, 0.228843],
        [{"radius": 120., "radius_pd": 0.2, "radius_pd_n":45}, "ER", 120.],
        [{"radius": 120., "radius_pd": 0.2, "radius_pd_n":45}, "VR", 1.],
    ]


**tests=[[{parameters}, q, result], ...]** is a list of lists.
Each list is one test and contains, in order:

- a dictionary of parameter values. This can be {} using the default
  parameters, or filled with some parameters that will be different
  from the default, such as {‘radius’:10.0, ‘sld’:4}. Unlisted parameters
  will be given the default values.
- the input $q$ value or tuple of $(q_x, q_y)$ values.
- the output $I(q)$ or $I(q_x,q_y)$ expected of the model for the parameters
  and input value given.
- input and output values can themselves be lists if you have several
  $q$ values to test for the same model parameters.
- for testing *ER* and *VR*, give the inputs as "ER" and "VR" respectively;
  the output for *VR* should be the sphere/shell ratio, not the individual
  sphere and shell values.

.. _Test_Your_New_Model:

Test Your New Model
^^^^^^^^^^^^^^^^^^^

Installed SasView
.................

If you are editing your model from the SasView GUI, you can test it
by selecting *Run > Compile* from the *Model Editor* menu bar. An
*Info* box will appear with the results of the compilation and a
check that the model runs.


Built SasView
.............

If the model compiles and runs, you can next run the unit tests that
you have added using the **test =** values. Switch to the *Shell* tab
and type the following::

    from sasmodels.model_test import run_one
    run_one("~/.sasview/plugin_models/model.py")

This should print::

    test_model_python (sasmodels.model_test.ModelTestCase) ... ok

To check whether single precision is good enough, type the following::

    from sasmodels.compare import main
    main("~/.sasview/plugin_models/model.py")

This will pop up a plot showing the difference between single precision
and double precision on a range of $q$ values.

::

  demo = dict(scale=1, background=0,
              sld=6, sld_solvent=1,
              radius=120,
              radius_pd=.2, radius_pd_n=45)

**demo={'par': value, ...}** in the model file sets the default values for
the comparison. You can include polydispersity parameters such as
*radius_pd=0.2, radius_pd_n=45* which would otherwise be zero.

The options to compare are quite extensive; type the following for help::

    main()

Options will need to be passed as separate strings.
For example to run your model with a random set of parameters::

    main("-random", "-pars", "~/.sasview/plugin_models/model.py")

For the random models,

- *sld* will be in the range (-0.5,10.5),
- angles (*theta, phi, psi*) will be in the range (-180,180),
- angular dispersion will be in the range (0,45),
- polydispersity will be in the range (0,1)
- other values will be in the range (0, 2\ *v*), where *v* is the value of the parameter in demo.

Dispersion parameters *n*\, *sigma* and *type* will be unchanged from demo so that
run times are predictable.

If your model has 2D orientational calculation, then you should also
test with::

    main("-2d", "~/.sasview/plugin_models/model.py")


Clean Lint - (Developer Version Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**NB: For now we are not providing pylint with the installer version of SasView; 
so unless you have a SasView build environment available, you can ignore this section!**

Run the lint check with::

    python -m pylint --rcfile=extra/pylint.rc ~/.sasview/plugin_models/model.py

We are not aiming for zero lint just yet, only keeping it to a minimum.
For now, don't worry too much about *invalid-name*. If you really want a
variable name *Rg* for example because $R_g$ is the right name for the model
parameter then ignore the lint errors.  Also, ignore *missing-docstring*
for standard model functions *Iq*, *Iqxy*, etc.

We will have delinting sessions at the SasView Code Camps, where we can
decide on standards for model files, parameter names, etc.

For now, you can tell pylint to ignore things.  For example, to align your
parameters in blocks::

    # pylint: disable=bad-whitespace,line-too-long
    #   ["name",                  "units", default, [lower, upper], "type", "description"],
    parameters = [
        ["contrast_factor",       "barns",    10.0,  [-inf, inf], "", "Contrast factor of the polymer"],
        ["bjerrum_length",        "Ang",       7.1,  [0, inf],    "", "Bjerrum length"],
        ["virial_param",          "1/Ang^2",  12.0,  [-inf, inf], "", "Virial parameter"],
        ["monomer_length",        "Ang",      10.0,  [0, inf],    "", "Monomer length"],
        ["salt_concentration",    "mol/L",     0.0,  [-inf, inf], "", "Concentration of monovalent salt"],
        ["ionization_degree",     "",          0.05, [0, inf],    "", "Degree of ionization"],
        ["polymer_concentration", "mol/L",     0.7,  [0, inf],    "", "Polymer molar concentration"],
        ]
    # pylint: enable=bad-whitespace,line-too-long

Don't put in too many pylint statements, though, since they make the code ugly.

Check The Docs - (Developer Version Only)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can get a rough idea of how the documentation will look using the
following::

    from sasmodels.generate import view_html
    view_html('~/.sasview/plugin_models/model.py')

This does not use the same styling as the SasView docs, but it will allow
you to check that your ReStructuredText and LaTeX formatting.  Here are
some tools to help with the inevitable syntax errors:

- `Sphinx cheat sheet <http://matplotlib.org/sampledoc/cheatsheet.html>`_
- `Sphinx Documentation <http://www.sphinx-doc.org/en/stable/>`_
- `MathJax <http://www.mathjax.org/>`_
- `amsmath <http://www.ams.org/publications/authors/tex/amslatex>`_

There is also a neat online WYSIWYG ReStructuredText editor at http://rst.ninjs.org\ .

Share Your Model!
^^^^^^^^^^^^^^^^^

Once compare and the unit test(s) pass properly and everything is done,
consider adding your model to the
`Model Marketplace <http://marketplace.sasview.org/>`_ so that others may use it!
