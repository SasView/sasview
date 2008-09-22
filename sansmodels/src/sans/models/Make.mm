# -*- Makefile -*-
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#                                   Jiao Lin
#                        California Institute of Technology
#                           (C) 2008  All Rights Reserved
#
# <LicenseText>
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

PROJECT = sans

BUILD_DIRS = \
	c_extensions \

RECURSE_DIRS = $(BUILD_DIRS)

PACKAGE = models

#--------------------------------------------------------------------------
#

all: export
	BLD_ACTION="all" $(MM) recurse

tidy::
	BLD_ACTION="tidy" $(MM) recurse



#--------------------------------------------------------------------------
#
# export

EXPORT_PYTHON_MODULES = \
	AddComponent.py \
	BEPolyelectrolyte.py \
	BaseComponent.py \
	Constant.py \
	CoreShellCylinderModel.py \
	CoreShellModel.py \
	Cos.py \
	CylinderModel.py \
	DABModel.py \
	DebyeModel.py \
	DisperseModel.py \
	DivComponent.py \
	EllipsoidModel.py \
	EllipticalCylinderModel.py \
	FractalModel.py \
	Gaussian.py \
	GuinierModel.py \
	LorentzModel.py \
	Lorentzian.py \
	ModelFactory.py \
	ModelIO.py \
	MulComponent.py \
	PorodModel.py \
	PowerLawModel.py \
	Sin.py \
	SphereModel.py \
	SubComponent.py \
	TeubnerStreyModel.py \
	__init__.py \
	dispersion_models.py \


export:: export-package-python-modules 
	BLD_ACTION="export" $(MM) recurse



# version
# $Id: Make.mm 1404 2007-08-29 15:43:42Z linjiao $

# End of file

