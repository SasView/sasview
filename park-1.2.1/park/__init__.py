# This program is public domain
"""
PARK fitting service.

The PARK fitting service is a set of python packages to support
fitting in datasets.  Using common python infrastructure such
as scipy optimizers, numpy arrays, and matplotlib plotting, park
allows you to define models, associate them with datasets and
simultaneously fit them.  Park provides a simple job queue to
manage multiple fits using separate processes or running across
the network on separate machines.

Installation
============

The latest version of Park is available from 
http://www.reflectometry.org/danse/park.


Currently this is supplied as source from a zip file.  You can
also retrieve the latest version from svn::

    svn co svn://danse.us/park/branches/park-1.2

If you are installing from source, you will need a python
environment with numpy and scipy.  For the GUI version, you
will also need matplotlib and wx.

You will need a C compiler to build the resolution convolution 
function.  On Windows this may require installing MinGW and
adding distutils.cfg to your distutils directory::

    [build]
    compiler = mingw

Once you have the required supporting packages, use the following
to build and install::

    python setup.py install
    
Usage
=====

To get started with park, you will need to first define the
models that you are using.  These can be very basic models, 
listing all possible fitting parameters.  When setting up the 
fit later, you will be able to combine models, using
parameter expressions to relate the values in one model with
those in another.  See `park.model` for details.

Once your models are constructed you can use them in a fit.
See `park.fit` for details.

Important classes and functions:
`park.model.Model`, `park.parameter.ParameterSet`, `park.fit.Fit`

:group models: model, assembly, parameter, data
:group examples: peaks
:group optimizer: fit, fitresult, fitmc, simplex
:group support: expression, deps, version, setup, serial
:group server: fitservice
"""

#from fitservice import *
from parameter import *
from data import *
from model import *
from assembly import *
import fit

