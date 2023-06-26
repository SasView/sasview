# Makefile for regenerating Sphinx documentation
# Will be moved to \build\html folder by build_sphinx.py
# To be packaged with release

PYTHON          ?= python
SPHINXOPTS       =
SPHINXBUILD      = "$(PYTHON)" -m sphinx
PAPER           ?= letter
PY_SRC           = ../../../../docs/sphinx-docs/source-temp/user/models/src/
HTML_BUILD_DIR   = 

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

# Internal variables.
PAPEROPT_a4     = -D latex_elements.papersize=a4
PAPEROPT_letter = -D latex_elements.papersize=letter
ALLSPHINXOPTS   = -d _build/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) .

MODELS_PY = $(wildcard $(PY_SRC)[a-z]*.py)

help:
	@echo "Please use \`make <target>' where <target> is `html' or `rst'"

.PHONY: help rst html

rst: regentoc.py regenmodel.py $(MODELS_PY)
	"$(PYTHON)" regenmodel.py $(MODELS_PY)
	"$(PYTHON)" regentoc.py $(MODELS_PY)

html: rst
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) ../../../../docs/sphinx-docs/source-temp/user/models/src
	@echo
	@echo "Build finished. The HTML pages are in ../../../../docs/sphinx-docs/source-temp/user/models/src."