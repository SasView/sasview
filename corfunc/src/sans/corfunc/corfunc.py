################################################################################
#SasView was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE) project 
#funded by the US National Science Foundation.
#copyright 2008, University of Tennessee
################################################################################
#The set of routines that comprise this CORFUNC module were originally written 
#in 1994 at the behest of Anthony (Tony) Ryan by Thomas (Tom) Nye whilst an 
#undergraduate in Applied Mathematics at the University of Cambridge, and are 
#based on the earlier work of Gert Strobl (Universitat Freiburg) and co-workers 
#in the 1980's. The polydispersity analysis was proposed later by Guy Eeckhaut 
#(ICI).
#
#The original UNIX source was ported to the Windows environment (and given 
#a Java GUI) as part of Collaborative Computational Project #13, funded by the 
#UK Biotechnology & Biological Sciences Research Council and Engineering & 
#Physical Sciences Research Council, by CCP13 Post-Doctoral workers Richard 
#Denny and Mark Shotton in 1999.
#
#The alternative Hilbert transform (volume fraction profile) analysis of 
#Trevor Crowley (Salford University) and co-workers was suggested by Stephen 
#(Steve) King (ISIS Facility). Its incorporation was started by CCP13 Post-
#Doctoral worker Matthew Rodman and finally implemented in 2004 by Steve King 
#and Damian Flannery (ISIS Facility), with help from Richard Heenan (ISIS 
#Facility).
#
#Copyright 2013, UK Science & Technology Facilities Council
################################################################################

"""
This module implements correlation function analysis or calculates volume 
fraction profiles.

:author: Steve King/ISIS

"""
import math 
import numpy

from sans.dataloader.data_info import Data1D as LoaderData1D



# SUBROUTINE tailfit
# (filename, qaxname, sigmodel, limit1, limit2, realtime, ndata, numiteration, 
# results, best, bestchannel, param, static)

retcode = sasview_corfunc.tailfit(a, b, c, d, e, f, g, h, i, j, k, l, k)



# SUBROUTINE tailjoin
# (filename, qaxname, param, channel, ndata, qzero, backex, datastart, 
# realtime, limit2, static)

retcode = sasview_corfunc.tailjoin(a, b, c, d, e, f, g, h, i, j, k)



# PROGRAM extrapolate

retcode = sasview_corfunc.extrapolate()



# PROGRAM ftransform

retcode = sasview_corfunc.fttransform()



# PROGRAM extract_par

retcode = sasview_corfunc.extract_par()



# PROGRAM TROPUS4

retcode = sasview_corfunc.tropus4()
