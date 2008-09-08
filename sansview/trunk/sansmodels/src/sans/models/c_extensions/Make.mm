# -*- Makefile -*-
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#                               Michael A.G. Aivazis
#                        California Institute of Technology
#                        (C) 1998-2004  All Rights Reserved
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#

include local.def

PROJECT = sans
PACKAGE = libsansmodels

PROJ_SAR = $(BLD_LIBDIR)/$(PACKAGE).$(EXT_SAR)
PROJ_DLL = $(BLD_BINDIR)/$(PACKAGE).$(EXT_SO)
PROJ_TMPDIR = $(BLD_TMPDIR)/$(PROJECT)/$(PACKAGE)
PROJ_CLEAN += $(PROJ_SAR) $(PROJ_DLL)

PROJ_SRCS = \
	core_shell.c \
	core_shell_cylinder.c \
	cylinder.c \
	ellipsoid.c \
	elliptical_cylinder.c \
	gaussian.c \
	lorentzian.c \
	sphere.c \


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# build the library

all: $(PROJ_SAR) export

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

ifeq (Win32, ${findstring Win32, $(PLATFORM_ID)})

# build the shared object
$(PROJ_SAR): product_dirs $(PROJ_OBJS)
	$(CXX) $(LCXXFLAGS) -o $(PROJ_DLL) \
	-Wl,--out-implib=$(PROJ_SAR) $(PROJ_OBJS)

# export
export:: export-headers export-libraries export-binaries

else

# build the shared object
$(PROJ_SAR): product_dirs $(PROJ_OBJS)
	$(CXX) $(LCXXFLAGS) -o $(PROJ_SAR) $(PROJ_OBJS)


# export
export:: export-headers export-libraries 

endif

EXPORT_HEADERS = \
	core_shell.h \
	core_shell_cylinder.h \
	cylinder.h \
	ellipsoid.h \
	elliptical_cylinder.h \
	gaussian.h \
	lorentzian.h \
	sphere.h \


EXPORT_LIBS = $(PROJ_SAR)
EXPORT_BINS = $(PROJ_DLL)



#include doxygen/default.def
#docs: export-doxygen-docs


# version
# $Id: Make.mm 1444 2007-11-16 16:46:15Z linjiao $

#
# End of file
