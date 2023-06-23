# Makefile for regenerating Sphinx documentation
# Will be moved to \build\html folder by build_sphinx.py
# To be packaged with release

PYTHON       ?= python
SPHINXOPTS    =
SPHINXBUILD   = "$(PYTHON)" -m sphinx

ifdef ComSpec
    RMDIR   = rmdir /s/q
    CPDIR   = xcopy /q/e/i
    MKDIR   = mkdir
    PATHSEP = $(strip \)
    COPY    = copy
else
    RMDIR   = rm -rf
    CPDIR   = cp -rp
    MKDIR   = mkdir -p
    PATHSEP = $(strip /)
    COPY    = cp
endif

MODELS_PY = $(wildcard ../../../sasmodels/models/[a-z]*.py)

help:
	@echo "Please use \`make <target>' where <target> is `html'"

.PHONY: help build ref/models/index.rst

ref/models/index.rst: regentoc.py regenmodel.py $(MODELS_PY)
	"$(PYTHON)" regenmodel.py $(MODELS_PY)
	"$(PYTHON)" regentoc.py $(MODELS_PY)

build: ref/models/index.rst

html: build
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) ../models/html
	@echo
	@echo "Build finished. The HTML pages are in ../models/html."





