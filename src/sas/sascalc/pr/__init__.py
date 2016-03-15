"""
    P(r) inversion for SAS
"""
## \mainpage P(r) inversion for SAS
#
# \section intro_sec Introduction
# This module provides calculations to transform scattering intensity data 
# I(q) into distance distribution function P(r). A description of the 
# technique can be found elsewhere [1-5]. The module is useable as a 
# standalone application but its functionality is meant to be presented 
# to end-users through the user interface developed as part of the SAS 
# flagship application. 
#
# Procedure: We will follow the procedure of Moore [1].
# 
# [1] P.B. Moore, J.Appl. Cryst (1980) 13, 168-175.
#
# [2] O. Glatter, J.Appl. Cryst (1977) 10, 415-421.
#
# [3] D.I. Svergun, J.Appl. Cryst (1991) 24, 485-492.
#
# [4] D.I. Svergun, J.Appl. Cryst (1992) 25, 495-503.
#
# [5] S. Hansen and J. Skov Pedersen, J.Appl. Cryst (1991) 24, 541-548.
#
## \subsection class Class Diagram:
# The following shows a partial class diagram with the main attributes
# and methods of the invertor.
#
# \image html architecture.png
#
# \section install_sec Installation
#
# \subsection obtain Obtaining the Code
#
# The code is available here:
# \verbatim
#$ svn co svn://danse.us/sas/pr_inversion
# \endverbatim
#
# \subsection depends External Dependencies
# scipy, numpy
#
# \subsection build Building the code
# The standard python package can be built with distutils.
# \verbatim
#$ python setup.py build
#$ python setup.py install
# \endverbatim
#
#
# \subsection Tutorial
# To create an inversion object:
# \verbatim
#from sas.sascalc.pr.invertor import Invertor
#    invertor = Invertor()
# \endverbatim
#
# To set the maximum distance between any two points:
# \verbatim
#    invertor.d_max = 160.0
# \endverbatim
#
# To set the regularization constant:
# \verbatim
#    invertor.alpha = 0.0007
# \endverbatim
#
# To set the q, I(q) and error on I(q):
# \verbatim
#    invertor.x = q_vector
#    invertor.y = Iq_vector
#    invertor.err = dIq_vector
# \endverbatim
#
# To perform the inversion. In this example, we choose
# a P(r) expension wit 10 base functions.
# \verbatim
#    c_out, c_cov = invertor.invert(10)
# \endverbatim
# The c_out and c_cov are the set of coefficients and the covariance 
# matrix for those coefficients, respectively.
#
# To get P(r):
# \verbatim
#    r = 10.0
#    pr = invertor.pr(c_out, r)
# \endverbatim
# Alternatively, one can get P(r) with the error on P(r):
# \verbatim
#    r = 10.0
#    pr, dpr = invertor.pr_err(c_out, c_cov, r)
# \endverbatim
#
# To get the output I(q) from the set of coefficients found:
# \verbatim
#    q = 0.001
#    iq = invertor.iq(c_out, q)
# \endverbatim
#
# Examples are available as unit tests under sas.pr_inversion.test.
#
# \section help_sec Contact Info
# Code and Documentation produced as part of the DANSE project.

__author__ = 'University of Tennessee'
