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

PROJECT = pointsmodelpy
PACKAGE = tests

PROJ_CLEAN += $(PROJ_CPPTESTS)

PROJ_CXX_INCLUDES += ../../iqPy/libiqPy   \
                     ../../iqPy/libiqPy/tnt \
                     ../../geoshapespy/libgeoshapespy   \
                     ../../analmodelpy/libanalmodelpy   \
		     ../libpointsmodelpy

PROJ_PYTESTS = signon.py
PROJ_CPPTESTS = testlores \
                testpdb  \
                testcomplexmodel
PROJ_TESTS = $(PROJ_PYTESTS) $(PROJ_CPPTESTS)
PROJ_LIBRARIES = -L$(BLD_LIBDIR) -lpointsmodelpy -lgeoshapespy -liqPy


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

testlores: testlores.cc $(BLD_LIBDIR)/libpointsmodelpy.$(EXT_SAR)
	$(CXX) $(CXXFLAGS) $(LCXXFLAGS) -g -o $@ testlores.cc $(PROJ_LIBRARIES)

testpdb: testpdb.cc $(BLD_LIBDIR)/libpointsmodelpy.$(EXT_SAR)
	$(CXX) $(CXXFLAGS) $(LCXXFLAGS) -g -o $@ testpdb.cc $(PROJ_LIBRARIES)

testcomplexmodel: testcomplexmodel.cc $(BLD_LIBDIR)/libpointsmodelpy.$(EXT_SAR)
	$(CXX) $(CXXFLAGS) $(LCXXFLAGS) -g -o $@ testcomplexmodel.cc $(PROJ_LIBRARIES)

# version
# $Id$

# End of file
