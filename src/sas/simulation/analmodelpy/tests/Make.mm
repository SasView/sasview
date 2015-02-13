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

PROJ_CXX_INCLUDES += ../../iqPy/libiqPy    \
		     ../../iqPy/libiqPy/tnt  \
		     ../libanalmodelpy    \
		     ../../geoshapespy/libgeoshapespy

PROJECT = SASsimulation
PACKAGE = tests

PROJ_CLEAN += $(PROJ_CPPTESTS)

PROJ_PYTESTS = testanal_model.py
PROJ_CPPTESTS = testanalytical_model
PROJ_TESTS = $(PROJ_PYTESTS) $(PROJ_CPPTESTS)
PROJ_LIBRARIES = -L$(BLD_LIBDIR) -lanalmodelpy -liqPy -lgeoshapespy


#--------------------------------------------------------------------------
#

all: $(PROJ_TESTS)

test:
	for test in $(PROJ_TESTS) ; do $${test}; done

release: tidy
	cvs release .

update: clean
	cvs update .

#--------------------------------------------------------------------------
#

testanalytical_model: testanalytical_model.cc $(BLD_LIBDIR)/libanalmodelpy.$(EXT_SAR)
	$(CXX) $(CXXFLAGS) $(LCXXFLAGS) -o $@ testanalytical_model.cc $(PROJ_LIBRARIES) 

# version
# $Id$

# End of file
