"""
    Real-Space Modeling for SAS
"""
## \mainpage Real-Space Modeling for SAS
#
# \section intro_sec Introduction
# This module provides SAS scattering intensity simulation
# based on real-space modeling.
#
# Documentation can be found here:
#    http://danse.us/trac/sas/wiki/RealSpaceModeling
#
# \section install_sec Installation
#
# \subsection obtain Obtaining the Code
#
# The code is available here:
# \verbatim
#$ svn co svn://danse.us/sas/realSpaceModeling
#$ svn co svn://danse.us/sas/RealSpaceTopLayer
# \endverbatim
#
# \subsection depends External Dependencies
# None
#
# \subsection build Building the code
# The standard python package can be built with distutils.
# From the realSpaceModeling directory:
# \verbatim
#$ python setup.py install
# \endverbatim
#
# From the RealSpaceTopLayer/src directory:
# \verbatim
#$ python setup.py install
# \endverbatim
#
# \section overview_sec Package Overview
#
# \subsection class Class Diagram:
# \image html real-space-class-diagram.png
#
# \subsection behav Behavior Enumeration:
# \image html enum.png
#
# \subsection Tutorial
# To create an empty canvas:
# \verbatim
#import sas.realspace.VolumeCanvas as VolumeCanvas
#    canvas = VolumeCanvas.VolumeCanvas()
# \endverbatim
#
# To set the simulation point density:
# \verbatim
#    canvas.setParam('lores_density', 0.01)
# \endverbatim
#
# To add an object:
# \verbatim
#    sphare = VolumeCanvas.SphereDescriptor()
#    handle = canvas.addObject(sphere)
#    canvas.setParam('%s.radius' % handle, 15.0)
# \endverbatim
#
# To evaluate the scattering intensity at a given q:
# \verbatim
#    output, error = canvas.getIqError(q=0.1)
#    output, error = canvas.getIq2DError(qx=0.1, qy=0.1)
# \endverbatim
#
# To get the value of a parameter:
# \verbatim
#    canvas.getParam('scale')
# \endverbatim
#
# Examples are available as unit tests under sas.realspace.test.
#
# \section help_sec Contact Info
# Code and Documentation by Jing Zhou as part of the DANSE project.
