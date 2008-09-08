"""
    1D Modeling for SANS
"""
## \mainpage Analytical Modeling for SANS
#
# \section intro_sec Introduction
# This module provides theoretical models for the scattering 
# intensity for SANS. 
#
# Documentation can be found here: 
#    http://danse.us/trac/sans/wiki/8_2_2_1DModelFitting
#    http://danse.us/trac/sans/wiki/8_2_3_2DModeling
#
# \section install_sec Installation
#
# \subsection obtain Obtaining the Code
#
# The code is available here:
# \verbatim
#$ svn co svn://danse.us/sans/sansmodels
# \endverbatim
#
# \subsection depends External Dependencies
# None
#
# \subsection build Building the code
# The standard python package can be built with distutils.
# \verbatim
#$ python setup.py build
#$ python setup.py install
# \endverbatim
#
# \section overview_sec Package Overview
# 
# \subsection class Class Diagram:
# \image html class_diag.png
# Note that the CCylinderModel is written as C code. 
# CylinderModel acts as an adaptor class for the C extension.
# Most model classes will be written that way.
#
# \subsection behav Behavior enumeration for pyre-level architecture:
# \image html behavior_pyre.png
#
# \subsection behav Behavior enumeration for under-lying architecture:
# \image html behavior.jpg
#
# \subsection Tutorial
# To create a model:
# \verbatim
#from sans.models.ModelFactory import ModelFactory
#    cyl = ModelFactory().getModel('CylinderModel')
# \endverbatim
#
# To evaluate a model (at x=0.1 in this example):
# \verbatim
#    output = cyl.run(0.1)
# \endverbatim
#
# To change a parameter:
# \verbatim
#    cyl.setParam('scale', 0.1)
# \endverbatim
#
# To get the value of a parameter:
# \verbatim
#    cyl.getParam('scale')
# \endverbatim
#
# Other examples are available as unit tests under sans.models.test.
#
# \section help_sec Contact Info
# Code and Documentation by Mathieu Doucet as part of the DANSE project.

__author__ = 'Mathieu Doucet'
