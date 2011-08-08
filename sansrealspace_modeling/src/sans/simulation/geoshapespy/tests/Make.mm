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

PROJECT = geoshapespy
PACKAGE = tests

PROJ_CLEAN += $(PROJ_CPPTESTS)

PROJ_CXX_INCLUDES += ../../iqPy/libiqPy   \
                     ../../iqPy/libiqPy/tnt \
                     ../libgeoshapespy   \
		     ../../pointsmodelpy/libpointsmodelpy

PROJ_PYTESTS = 
PROJ_CPPTESTS = testpoint

PROJ_TESTS = $(PROJ_PYTESTS) $(PROJ_CPPTESTS)
PROJ_LIBRARIES = -L$(BLD_LIBDIR) -lgeoshapespy -liqPy -lpointsmodelpy


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

testshapes: testshapes.cc $(BLD_LIBDIR)/libgeoshapespy.$(EXT_SAR)
	$(CXX) $(CXXFLAGS) $(LCXXFLAGS) -o $@ testshapes.cc $(PROJ_LIBRARIES)

testpoint: testPoint.cc $(BLD_LIBDIR)/libgeoshapespy.$(EXT_SAR)
	$(CXX) $(CXXFLAGS) $(LCXXFLAGS) -o $@ testPoint.cc $(PROJ_LIBRARIES)

testtransformation:  testtransformation.cc $(BLD_LIBDIR)/libgeoshapespy.$(EXT_SAR)
	$(CXX) $(CXXFLAGS) $(LCXXFLAGS) -o $@ testtransformation.cc $(PROJ_LIBRARIES)

# version
# $Id$

# End of file
