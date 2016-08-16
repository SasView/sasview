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
from shutil import copy
from os import listdir

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
SASMODELS_SOURCE_PROLOG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc")
SASMODELS_SOURCE_MAGNETISM = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "ref", "magnetism")
SASMODELS_SOURCE_REF_MODELS = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "ref", "models")
SASMODELS_SOURCE_MODELS = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "model")
SASMODELS_SOURCE_IMG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "model", "img")
SASMODELS_SOURCE_AUTOIMG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "_build", "html","_images")
SASMODELS_DEST_PROLOG = os.path.join(CURRENT_SCRIPT_DIR, "source")
SASMODELS_DEST_REF_MODELS = os.path.join(CURRENT_SCRIPT_DIR, "source", "user")
SASMODELS_DEST_MODELS = os.path.join(CURRENT_SCRIPT_DIR, "source", "user", "models")
SASMODELS_DEST_IMG = os.path.join(CURRENT_SCRIPT_DIR,  "source", "user", "model-imgs", "new-models")
SASMODELS_DEST_BUILDIMG = os.path.join(CURRENT_SCRIPT_DIR,  "source", "user", "models", "img")

#if os.path.exists(SASMODELS_SOURCE_PROLOG):
#    print "Found models prolog folder at ", SASMODELS_SOURCE_PROLOG
#if os.path.exists(SASMODELS_SOURCE_REF_MODELS):
#    print "Found models ref folder at ", SASMODELS_SOURCE_REF_MODELS
#if os.path.exists(SASMODELS_SOURCE_MODELS):
#    print "Found models folder at ", SASMODELS_SOURCE_MODELS
#if os.path.exists(SASMODELS_SOURCE_IMG):
#    print "Found img folder at ", SASMODELS_SOURCE_IMG
#if os.path.exists(SASMODELS_DEST_REF_MODELS):
#    print "Found models ref folder at ", SASMODELS_DEST_REF_MODELS
#if os.path.exists(SASMODELS_DEST_MODELS):
#    print "Found models folder at ", SASMODELS_DEST_MODELS
#if os.path.exists(SASMODELS_DEST_IMG):
#    print "Found img folder at ", SASMODELS_DEST_IMG
#sys.exit()

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

def inplace_change(filename, old_string, new_string):
# Thanks to http://stackoverflow.com/questions/4128144/replace-string-within-file-contents
        s=open(filename).read()
        if old_string in s:
                print 'Changing "{old_string}" to "{new_string}"'.format(**locals())
                s=s.replace(old_string, new_string)
                f=open(filename, 'w')
                f.write(s)
                f.flush()
                f.close()
        else:
                print 'No occurences of "{old_string}" found.'.format(**locals())

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
    print "=== Including Test Data Docs ==="
    if os.path.exists(SASVIEW_TEST):
       print "Found docs folder at ", SASVIEW_TEST
       shutil.copytree(SASVIEW_TEST, SPHINX_SOURCE_TEST)       

    print "=== And the Sasmodels Docs ===" 
    # Make sure we have the relevant images for the new sasmodels documentation
    # First(!) we'll make a local reference copy for SasView (/new-models will be cleaned each build)
    if os.path.exists(SASMODELS_SOURCE_IMG):
        print "Found img  folder SASMODELS_SOURCE_IMG    at ", SASMODELS_SOURCE_IMG
        if not os.path.exists(SASMODELS_DEST_IMG):
            print "Missing docs folder SASMODELS_DEST_IMG at ", SASMODELS_DEST_IMG
            os.makedirs(SASMODELS_DEST_IMG)
            print "created SASMODELS_DEST_BUILDIMG at ", SASMODELS_DEST_BUILDIMG
        else: print "Found img  folder SASMODELS_DEST_IMG      at ", SASMODELS_DEST_IMG
        print "Copying sasmodels model image files..."
        for files in os.listdir(SASMODELS_SOURCE_IMG):
            fromhere=os.path.join(SASMODELS_SOURCE_IMG,files)
            tohere=os.path.join(SASMODELS_DEST_IMG,files)
            shutil.copy(fromhere,tohere)
    else: print "cannot find SASMODELS_SOURCE_IMG", SASMODELS_SOURCE_IMG

    if os.path.exists(SASMODELS_SOURCE_AUTOIMG):
        print "Found img  folder SASMODELS_SOURCE_AUTOIMG    at ", SASMODELS_SOURCE_AUTOIMG
        if not os.path.exists(SASMODELS_DEST_IMG):
            print "Missing docs folder SASMODELS_DEST_IMG at ", SASMODELS_DEST_IMG
            os.makedirs(SASMODELS_DEST_BUILDIMG)
            print "created SASMODELS_DEST_BUILDIMG at ", SASMODELS_DEST_BUILDIMG
        print "Copying sasmodels model auto-generated image files..."
        for files in os.listdir(SASMODELS_SOURCE_AUTOIMG):
            fromhere=os.path.join(SASMODELS_SOURCE_AUTOIMG,files)
            tohere=os.path.join(SASMODELS_DEST_IMG,files)
            shutil.copy(fromhere,tohere)
        else: print "no source directorty",SASMODELS_SOURCE_AUTOIMG ,"was found"
    
    # And the rst prolog with the unit substitutions
    if os.path.exists(SASMODELS_SOURCE_PROLOG):
        print "Found prolog folder SASMODELS_SOURCE_PROLOG at ", SASMODELS_SOURCE_PROLOG
        if os.path.exists(SASMODELS_DEST_PROLOG):
            print "Found docs folder SASMODELS_DEST_PROLOG   at ", SASMODELS_DEST_PROLOG
            print "Copying sasmodels rst_prolog file..."
            for files in os.listdir(SASMODELS_SOURCE_PROLOG):
                if files.startswith("rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_PROLOG,files)
                    tohere=os.path.join(SASMODELS_DEST_PROLOG,files)
                    shutil.copy(fromhere,tohere)

    if os.path.exists(SASMODELS_SOURCE_MAGNETISM):
        print "Found docs folder SASMODELS_SOURCE_MAGNETISM at ", SASMODELS_SOURCE_MAGNETISM
        if os.path.exists(SASMODELS_DEST_REF_MODELS):
            print "Found docs folder SASMODELS_DEST_REF_MODELS   at ", SASMODELS_DEST_REF_MODELS
            print "Copying sasmodels model toctree files..."
            for files in os.listdir(SASMODELS_SOURCE_MAGNETISM):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_MAGNETISM,files)
                    tohere=os.path.join(SASMODELS_DEST_REF_MODELS,files)
                    shutil.copy(fromhere,tohere)

    if os.path.exists(SASMODELS_SOURCE_REF_MODELS):
        print "Found docs folder SASMODELS_SOURCE_REF_MODELS at ", SASMODELS_SOURCE_REF_MODELS
        if os.path.exists(SASMODELS_DEST_REF_MODELS):
            print "Found docs folder SASMODELS_DEST_REF_MODELS   at ", SASMODELS_DEST_REF_MODELS
            print "Copying sasmodels model toctree files..."
            for files in os.listdir(SASMODELS_SOURCE_REF_MODELS):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_REF_MODELS,files)
                    tohere=os.path.join(SASMODELS_DEST_REF_MODELS,files)
                    shutil.copy(fromhere,tohere)
    # But need to change the path to the model docs in the tocs
    for files in os.listdir(SASMODELS_DEST_REF_MODELS):
#        print files
        if files.startswith("shape"):
            print "Changing toc paths in", files
            inplace_change(os.path.join(SASMODELS_DEST_REF_MODELS,files), "../../model/", "models/")
        if files.startswith("sphere"):
            print "Changing toc paths in", files
            inplace_change(os.path.join(SASMODELS_DEST_REF_MODELS,files), "../../model/", "models/")
        if files.startswith("custom"):
            print "Changing toc paths in", files
            inplace_change(os.path.join(SASMODELS_DEST_REF_MODELS,files), "../../model/", "models/")
        if files.startswith("structure"):
            print "Changing toc paths in", files
            inplace_change(os.path.join(SASMODELS_DEST_REF_MODELS,files), "../../model/", "models/")

    if os.path.exists(SASMODELS_SOURCE_MODELS):
        print "Found docs folder SASMODELS_SOURCE_MODELS at ", SASMODELS_SOURCE_MODELS
        if os.path.exists(SASMODELS_DEST_MODELS):
            print "Found docs folder SASMODELS_DEST_MODELS   at ", SASMODELS_DEST_MODELS
            print "Copying sasmodels model files..."
            for files in os.listdir(SASMODELS_SOURCE_MODELS):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_MODELS,files)
                    tohere=os.path.join(SASMODELS_DEST_MODELS,files)
                    shutil.copy(fromhere,tohere)
        else:
            print "Missing docs folder SASMODELS_DEST_MODELS at ", SASMODELS_DEST_MODELS
            os.makedirs(SASMODELS_DEST_MODELS)
            if not os.path.exists(SASMODELS_DEST_BUILDIMG):
                os.makedirs(SASMODELS_DEST_BUILDIMG)
            print "Created docs folder SASMODELS_DEST_MODELS at ", SASMODELS_DEST_MODELS
            print "Copying model files for build..."
            for files in os.listdir(SASMODELS_SOURCE_MODELS):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_MODELS,files)
                    tohere=os.path.join(SASMODELS_DEST_MODELS,files)
                    shutil.copy(fromhere,tohere)
            # No choice but to do this because model files are all coded for images in /models/img
            print "Copying image files for build..."
            for files in os.listdir(SASMODELS_DEST_IMG):
                fromhere=os.path.join(SASMODELS_DEST_IMG,files)
                tohere=os.path.join(SASMODELS_DEST_BUILDIMG,files)
                shutil.copy(fromhere,tohere)


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
