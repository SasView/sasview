# Makefile for regenerating Sphinx documentation
# Will be moved to \build\html folder by build_sphinx.py
# To be packaged with release

PYTHON          ?= python
SPHINXOPTS       = -W --keep-going
SPHINXBUILD      = "$(PYTHON)" -m sphinx
PAPER           ?= letter
BUILD_CHECK      = ../../../../.github
PY_SRC           = ../../../../docs/sphinx-docs/source-temp/user/models/src/
DOC_DST          = ../../../../docs/sphinx-docs/build/doctrees/
RST_SRC          = ../../../../docs/sphinx-docs/source-temp/
HTML_BUILD_DST   = ../../../../docs/sphinx-docs/build/html/
 
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
ALLSPHINXOPTS   = -d $(DOC_DST) $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) $(RST_SRC)

MODELS_PY = $(wildcard $(PY_SRC)[a-z]*.py)

help:
	@echo "Please use \`make <target>' where <target> is `html' or `rst'"

.PHONY: help rst html

rst: regentoc.py regenmodel.py $(MODELS_PY)
	"$(PYTHON)" regenmodel.py $(MODELS_PY)
	"$(PYTHON)" regentoc.py $(MODELS_PY)

doctree-loc: treegen.py
# Currently does nothing--see referenced python script for details
	"$(PYTHON)" treegen.py
	@echo "This command is currently unused in the final build. Did you mean to call `html' or `rst'?"

html: rst
	$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) $(HTML_BUILD_DST)
	@echo
	@echo "Build finished. The HTML pages are in ../../../../docs/sphinx-docs/build/html/"