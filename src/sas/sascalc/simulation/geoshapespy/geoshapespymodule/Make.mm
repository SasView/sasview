# -*- Makefile -*-
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#                               Michael A.G. Aivazis
#                        California Institute of Technology
#                        (C) 1998-2005  All Rights Reserved
#
# <LicenseText>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#

PROJECT = SASsimulation
PACKAGE = geoshapespymodule
MODULE = geoshapespy

include std-pythonmodule.def
include local.def

PROJ_CXX_SRCLIB = -lgeoshapespy

PROJ_SRCS = \
    bindings.cc \
    exceptions.cc \
    misc.cc


# version
# $Id$

# End of file
