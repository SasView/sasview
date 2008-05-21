"""
    P(r) inversion for SANS
"""
## \mainpage P(r) inversion for SANS
#
# \section intro_sec Introduction
# This module provides calculations to transform scattering intensity data 
# I(q) into distance distribution function P(r). A description of the 
# technique can be found elsewhere [1-5]. The module is useable as a 
# standalone application but its functionality is meant to be presented 
# to end-users through the user interface developed as part of the SANS 
# flagship application. 
#
# Procedure: We will follow the procedure of Moore [1].
# 
# [1] P.B. Moore, J.Appl. Cryst (1980) 13, 168-175.
# [2] O. Glatter, J.Appl. Cryst (1977) 10, 415-421.
# [3] D.I. Svergun, J.Appl. Cryst (1991) 24, 485-492.
# [4] D.I. Svergun, J.Appl. Cryst (1992) 25, 495-503.
# [5] S. Hansen and J. Skov Pedersen, J.Appl. Cryst (1991) 24, 541-548.
#
#
# \section install_sec Installation
#
# \subsection obtain Obtaining the Code
#
# The code is available here:
# \verbatim
#$ svn co svn://danse.us/sans/pr_inversion
# \endverbatim
#
# \subsection depends External Dependencies
# scipy, numpy, pylab
#
# \subsection build Building the code
# The standard python package can be built with distutils.
# \verbatim
#$ python setup.py build
#$ python setup.py install
# \endverbatim
#
#
# Examples are available as unit tests under sans.pr_inversion.test.
#
# \section help_sec Contact Info
# Code and Documentation produced as part of the DANSE project.

__author__ = 'University of Tennessee'
