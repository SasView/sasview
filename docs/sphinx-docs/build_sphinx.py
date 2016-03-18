#!/usr/bin/env python
"""
Functions for building sphinx docs.

For more information on the invocation of sphinx see:
http://sphinx-doc.org/invocation.html
"""
import subprocess
import os
import sys
import fnmatch
import shutil
import imp
from glob import glob

from distutils.dir_util import copy_tree
from distutils.util import get_platform
from shutil import copyfile

platform = '.%s-%s'%(get_platform(),sys.version[:3])

CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

run = imp.load_source('run', os.path.join(CURRENT_SCRIPT_DIR, '..', '..', 'run.py'))
run.prepare()

SASVIEW_SRC = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "src")
SASVIEW_BUILD = os.path.abspath(os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "build", "lib"+platform))
SASVIEW_DOCS = os.path.join(SASVIEW_BUILD, "doc")
SASVIEW_TEST = os.path.join(SASVIEW_SRC, "..", "sasview", "test", "media")

# Need to slurp in the new sasmodels model definitions to replace the old model_functions.rst
# We are currently here:
#/sasview-local-trunk/docs/sphinx-docs/build_sphinx.py
SASMODELS_SOURCE_MODELS = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "sasmodels", "models")
SASMODELS_SOURCE_IMG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "sasmodels", "models", "img")
SASMODELS_DEST_MODELS = os.path.join(CURRENT_SCRIPT_DIR, "source", "user", "models")
SASMODELS_DEST_IMG = os.path.join(CURRENT_SCRIPT_DIR, "source", "user", "models", "img")

#print SASMODELS_SOURCE_MODELS
#print SASMODELS_SOURCE_IMG
#print SASMODELS_DEST_MODELS
#print SASMODELS_DEST_IMG

SPHINX_BUILD = os.path.join(CURRENT_SCRIPT_DIR, "build")
SPHINX_SOURCE = os.path.join(CURRENT_SCRIPT_DIR, "source")
SPHINX_SOURCE_API = os.path.join(SPHINX_SOURCE, "dev", "api")
SPHINX_SOURCE_GUIFRAME = os.path.join(SPHINX_SOURCE, "user", "sasgui", "guiframe")
SPHINX_SOURCE_MODELS = os.path.join(SPHINX_SOURCE, "user", "models")
SPHINX_SOURCE_PERSPECTIVES = os.path.join(SPHINX_SOURCE, "user", "sasgui", "perspectives")
SPHINX_SOURCE_TEST = os.path.join(SPHINX_SOURCE, "test")

BUMPS_DOCS = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..",
                          "bumps", "doc", "guide")
BUMPS_TARGET = os.path.join(SPHINX_SOURCE_PERSPECTIVES, "fitting")

def _remove_dir(dir_path):
    """Removes the given directory."""
    if os.path.isdir(dir_path):
        print "Removing \"%s\"... " % dir_path
        shutil.rmtree(dir_path)

def clean():
    """
    Clean the sphinx build directory.
    """
    print "=== Cleaning Sphinx Build ==="
    _remove_dir(SASVIEW_DOCS)
    _remove_dir(SPHINX_BUILD)
    _remove_dir(SPHINX_SOURCE_GUIFRAME)
    _remove_dir(SPHINX_SOURCE_MODELS)
    _remove_dir(SPHINX_SOURCE_PERSPECTIVES)
    _remove_dir(SPHINX_SOURCE_TEST)

def retrieve_user_docs():
    """
    Copies across the contents of any media/ directories in src/, and puts them
    in an appropriately named directory of docs/sphinx-docs/source/. For
    example:

        sas/../[MODULE]/media/dir/A.rst
        sas/../[MODULE]/media/B.rst

    gets copied to a new location:

        docs/sphinx-docs/source/user/[MODULE]/dir/A.rst
        docs/sphinx-docs/source/user/[MODULE]/B.rst

    so that Sphinx may pick it up when generating the documentation.
    """
    print "=== Retrieve User Docs ==="

    # Copy documentation files from their "source" to their "destination".
    for root, dirnames, _ in os.walk(SASVIEW_SRC):
        for dirname in fnmatch.filter(dirnames, 'media'):

            docs = os.path.abspath(os.path.join(root, dirname))
            print "Found docs folder at \"%s\"." % docs

            dest_dir_part = os.path.dirname(os.path.relpath(docs, SASVIEW_SRC))
            if os.sep in dest_dir_part:
                dest_dir_part = dest_dir_part[dest_dir_part.index(os.sep) + 1:]
            dest_dir = os.path.join(SPHINX_SOURCE, "user", dest_dir_part)

            copy_tree(docs, dest_dir)
            
    # Now pickup testdata_help.rst
#    print os.path.abspath(SASVIEW_TEST)
#    print os.path.abspath(SPHINX_SOURCE_TEST)
    if os.path.exists(SASVIEW_TEST):
       print "Found docs folder at ", SASVIEW_TEST
       shutil.copytree(SASVIEW_TEST, SPHINX_SOURCE_TEST)       
       
    # Make sure we have the relevant images for the new sasmodels documentation
    copyfile(SASMODELS_SOURCE_IMG, SASMODELS_DEST_IMG)

    sys.exit()


def retrieve_bumps_docs():
    """
    Copies select files from the bumps documentation into fitting perspective
    """
    if os.path.exists(BUMPS_DOCS):
        print "=== Retrieve BUMPS Docs ==="
        filenames = [os.path.join(BUMPS_DOCS, "optimizer.rst")]
        filenames += glob(os.path.join(BUMPS_DOCS, "dream-*.png"))
        filenames += glob(os.path.join(BUMPS_DOCS, "fit-*.png"))
        for f in filenames:
            print "Copying file", f
            shutil.copy(f, BUMPS_TARGET)
    else:
        print """
*** Error *** missing directory %s
The documentation will not include the optimizer selection section.
Checkout the bumps source tree and rebuild the docs.


""" % BUMPS_DOCS

def apidoc():
    """
    Runs sphinx-apidoc to generate .rst files from the docstrings in .py files
    in the SasView build directory.
    """
    print "=== Generate API Rest Files ==="

    # Clean directory before generating a new version.
    _remove_dir(SPHINX_SOURCE_API)

    subprocess.call(["sphinx-apidoc",
                     "-o", SPHINX_SOURCE_API, # Output dir.
                     "-d", "8", # Max depth of TOC.
                     SASVIEW_BUILD])

def build():
    """
    Runs sphinx-build.  Reads in all .rst files and spits out the final html.
    """
    print "=== Build HTML Docs from Rest Files ==="
    subprocess.call(["sphinx-build",
                     "-b", "html", # Builder name. TODO: accept as arg to setup.py.
                     "-d", os.path.join(SPHINX_BUILD, "doctrees"),
                     SPHINX_SOURCE,
                     os.path.join(SPHINX_BUILD, "html")])

    print "=== Copy HTML Docs to Build Directory ==="
    html = os.path.join(SPHINX_BUILD, "html")
    copy_tree(html, SASVIEW_DOCS)

def rebuild():
    clean()
    retrieve_user_docs()
    retrieve_bumps_docs()
    apidoc()
    build()

    print "=== Done ==="

if __name__ == "__main__":
    rebuild()
