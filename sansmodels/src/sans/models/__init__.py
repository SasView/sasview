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
#PLUGIN_ID = "models plug-in 0.4"
from sans.models import *

import os
from distutils.filelist import findall

def get_data_path(media):
    """
    """
    # Check for data path in the package
    path = os.path.join(os.path.dirname(__file__), media)
    if os.path.isdir(path):
        return path

    # Check for data path next to exe/zip file.
    # If we are inside a py2exe zip file, we need to go up
    # to get to the directory containing 
    # the media for this module
    path = os.path.dirname(__file__)
    #Look for maximum n_dir up of the current dir to find media
    n_dir = 12
    for i in range(n_dir):
        path, _ = os.path.split(path)
        media_path = os.path.join(path, media)
        if os.path.isdir(media_path):
            module_media_path = os.path.join(media_path, 'models_media')
            if os.path.isdir(module_media_path):
                return module_media_path
            return media_path
   
    raise RuntimeError('Could not find models media files')

def data_files():
    """
    Return the data files associated with media.
    
    The format is a list of (directory, [files...]) pairs which can be
    used directly in setup(...,data_files=...) for setup.py.

    """
    data_files = []
    path = get_data_path(media="media")
    for f in findall(path):
        data_files.append(('media/models_media', [f]))
    return data_files
