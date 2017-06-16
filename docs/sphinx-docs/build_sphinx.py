#!/usr/bin/env python
"""
Functions for building sphinx docs.

For more information on the invocation of sphinx see:
http://sphinx-doc.org/invocation.html
"""
from __future__ import print_function

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
SASVIEW_TOC_SOURCE = os.path.join(CURRENT_SCRIPT_DIR, "source")

# Need to slurp in the new sasmodels model definitions to replace the old model_functions.rst
# We are currently here:
#/sasview-local-trunk/docs/sphinx-docs/build_sphinx.py
SASMODELS_SOURCE_PROLOG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc")
SASMODELS_SOURCE_GPU = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "ref", "gpu")
SASMODELS_SOURCE_SESANS = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "ref", "sesans")
SASMODELS_SOURCE_SESANSIMG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "ref", "sesans", "sesans_img")
SASMODELS_SOURCE_MAGNETISM = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "ref", "magnetism")
SASMODELS_SOURCE_MAGIMG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "ref", "magnetism", "mag_img")
SASMODELS_SOURCE_REF_MODELS = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "ref", "models")
SASMODELS_SOURCE_MODELS = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "model")
SASMODELS_SOURCE_IMG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "model", "img")
SASMODELS_SOURCE_AUTOIMG = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..", "sasmodels", "doc", "_build", "html","_images")
## Don't do assemble-in-place
## Assemble the docs in a temporary folder
SASMODELS_DEST_PROLOG = os.path.join(CURRENT_SCRIPT_DIR, "source-temp")
SASMODELS_DEST_REF_MODELS = os.path.join(SASMODELS_DEST_PROLOG, "user")
SASMODELS_DEST_MODELS = os.path.join(SASMODELS_DEST_PROLOG, "user", "models")
SASMODELS_DEST_IMG = os.path.join(SASMODELS_DEST_PROLOG, "user", "model-imgs", "new-models")
SASMODELS_DEST_MAGIMG = os.path.join(SASMODELS_DEST_PROLOG, "user", "mag_img")
SASMODELS_DEST_SESANSIMG = os.path.join(SASMODELS_DEST_PROLOG, "user", "sesans_img")
SASMODELS_DEST_BUILDIMG = os.path.join(SASMODELS_DEST_PROLOG, "user", "models", "img")


SPHINX_BUILD = os.path.join(CURRENT_SCRIPT_DIR, "build")
SPHINX_SOURCE = os.path.join(CURRENT_SCRIPT_DIR, "source-temp")
SPHINX_SOURCE_API = os.path.join(SPHINX_SOURCE, "dev", "api")
SPHINX_SOURCE_GUIFRAME = os.path.join(SPHINX_SOURCE, "user", "sasgui", "guiframe")
SPHINX_SOURCE_MODELS = os.path.join(SPHINX_SOURCE, "user", "models")
SPHINX_SOURCE_PERSPECTIVES = os.path.join(SPHINX_SOURCE, "user", "sasgui", "perspectives")
SPHINX_SOURCE_TEST = os.path.join(SPHINX_SOURCE, "test")
SPHINX_SOURCE_USER = os.path.join(SPHINX_SOURCE, "user")

BUMPS_DOCS = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "..",
                          "bumps", "doc", "guide")
BUMPS_TARGET = os.path.join(SPHINX_SOURCE_PERSPECTIVES, "fitting")

def inplace_change(filename, old_string, new_string):
# Thanks to http://stackoverflow.com/questions/4128144/replace-string-within-file-contents
        s=open(filename).read()
        if old_string in s:
                print('Changing "{old_string}" to "{new_string}"'.format(**locals()))
                s=s.replace(old_string, new_string)
                f=open(filename, 'w')
                f.write(s)
                f.flush()
                f.close()
        else:
                print('No occurences of "{old_string}" found.'.format(**locals()))

def _remove_dir(dir_path):
    """Removes the given directory."""
    if os.path.isdir(dir_path):
        print("Removing \"%s\"... " % dir_path)
        shutil.rmtree(dir_path)

def clean():
    """
    Clean the sphinx build directory.
    """
    print("=== Cleaning Sphinx Build ===")
    _remove_dir(SASVIEW_DOCS)
    _remove_dir(SPHINX_BUILD)
    _remove_dir(SPHINX_SOURCE)
    #_remove_dir(SPHINX_SOURCE_GUIFRAME)
    #_remove_dir(SPHINX_SOURCE_MODELS)
    #_remove_dir(SPHINX_SOURCE_PERSPECTIVES)
    #_remove_dir(SPHINX_SOURCE_TEST)

def setup_source_temp():
    """
    Copy the source toctrees to new folder for assembling the sphinx-docs
    """
    print("=== Copying Source toctrees ===")
    if os.path.exists(SASVIEW_TOC_SOURCE):
       print("Found docs folder at", SASVIEW_TOC_SOURCE)
       shutil.copytree(SASVIEW_TOC_SOURCE, SPHINX_SOURCE)

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
    print("=== Retrieve User Docs ===")

    # Copy documentation files from their "source" to their "destination".
    for root, dirnames, _ in os.walk(SASVIEW_SRC):
        for dirname in fnmatch.filter(dirnames, 'media'):

            docs = os.path.abspath(os.path.join(root, dirname))
            print("Found docs folder at \"%s\"." % docs)

            dest_dir_part = os.path.dirname(os.path.relpath(docs, SASVIEW_SRC))
            if os.sep in dest_dir_part:
                dest_dir_part = dest_dir_part[dest_dir_part.index(os.sep) + 1:]
            dest_dir = os.path.join(SPHINX_SOURCE, "user", dest_dir_part)

            copy_tree(docs, dest_dir)

    # Now pickup testdata_help.rst
    print("=== Including Test Data Docs ===")
    if os.path.exists(SASVIEW_TEST):
       print("Found docs folder at", SASVIEW_TEST)
       shutil.copytree(SASVIEW_TEST, SPHINX_SOURCE_TEST)

    print("=== And the Sasmodels Docs ===")
    # Make sure we have the relevant images for the new sasmodels documentation
    # First(!) we'll make a local reference copy for SasView (/new-models will be cleaned each build)
    if os.path.exists(SASMODELS_SOURCE_IMG):
        print("Found img folder SASMODELS_SOURCE_IMG at", SASMODELS_SOURCE_IMG)
        if not os.path.exists(SASMODELS_DEST_IMG):
            print("Missing docs folder SASMODELS_DEST_IMG at", SASMODELS_DEST_IMG)
            os.makedirs(SASMODELS_DEST_IMG)
            print("created SASMODELS_DEST_BUILDIMG at", SASMODELS_DEST_BUILDIMG)
        else:
            print("Found img folder SASMODELS_DEST_IMG at", SASMODELS_DEST_IMG)
        print("Copying sasmodels model image files...")
        for files in os.listdir(SASMODELS_SOURCE_IMG):
            fromhere=os.path.join(SASMODELS_SOURCE_IMG,files)
            tohere=os.path.join(SASMODELS_DEST_IMG,files)
            shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_IMG,"was found")

    if os.path.exists(SASMODELS_SOURCE_AUTOIMG):
        print("Found img folder SASMODELS_SOURCE_AUTOIMG at", SASMODELS_SOURCE_AUTOIMG)
        if not os.path.exists(SASMODELS_DEST_IMG):
            print("Missing docs folder SASMODELS_DEST_IMG at", SASMODELS_DEST_IMG)
            os.makedirs(SASMODELS_DEST_BUILDIMG)
            print("created SASMODELS_DEST_BUILDIMG at", SASMODELS_DEST_BUILDIMG)
        print("Copying sasmodels model auto-generated image files...")
        for files in os.listdir(SASMODELS_SOURCE_AUTOIMG):
            fromhere=os.path.join(SASMODELS_SOURCE_AUTOIMG,files)
            tohere=os.path.join(SASMODELS_DEST_IMG,files)
            shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_AUTOIMG ,"was found")

    # And the rst prolog with the unit substitutions
    if os.path.exists(SASMODELS_SOURCE_PROLOG):
        print("Found prolog folder SASMODELS_SOURCE_PROLOG at", SASMODELS_SOURCE_PROLOG)
        if os.path.exists(SASMODELS_DEST_PROLOG):
            print("Found docs folder SASMODELS_DEST_PROLOG at", SASMODELS_DEST_PROLOG)
            print("Copying sasmodels rst_prolog file...")
            for files in os.listdir(SASMODELS_SOURCE_PROLOG):
                if files.startswith("rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_PROLOG,files)
                    tohere=os.path.join(SASMODELS_DEST_PROLOG,files)
                    shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_PROLOG, "was found")

    if os.path.exists(SASMODELS_SOURCE_GPU):
        print("Found docs folder SASMODELS_SOURCE_GPU at", SASMODELS_SOURCE_GPU)
        if os.path.exists(SPHINX_SOURCE_USER):
            print("Found docs folder SPHINX_SOURCE_USER at", SPHINX_SOURCE_USER)
            print("Copying sasmodels gpu files...")
            for files in os.listdir(SASMODELS_SOURCE_GPU):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_GPU,files)
                    tohere=os.path.join(SPHINX_SOURCE_USER,files)
                    shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_GPU,"was found")

    if os.path.exists(SASMODELS_SOURCE_SESANS):
        print("Found docs folder SASMODELS_SOURCE_SESANS at", SASMODELS_SOURCE_SESANS)
        if os.path.exists(SPHINX_SOURCE_USER):
            print("Found docs folder SPHINX_SOURCE_USER at", SPHINX_SOURCE_USER)
            print("Copying sasmodels sesans files...")
            for files in os.listdir(SASMODELS_SOURCE_SESANS):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_SESANS,files)
                    tohere=os.path.join(SPHINX_SOURCE_USER,files)
                    shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_SESANS,"was found")

    if os.path.exists(SASMODELS_SOURCE_MAGNETISM):
        print("Found docs folder SASMODELS_SOURCE_MAGNETISM at", SASMODELS_SOURCE_MAGNETISM)
        if os.path.exists(SASMODELS_DEST_REF_MODELS):
            print("Found docs folder SASMODELS_DEST_REF_MODELS at", SASMODELS_DEST_REF_MODELS)
            print("Copying sasmodels model toctree files...")
            for files in os.listdir(SASMODELS_SOURCE_MAGNETISM):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_MAGNETISM,files)
                    tohere=os.path.join(SASMODELS_DEST_REF_MODELS,files)
                    shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_MAGNETISM,"was found")

    if os.path.exists(SASMODELS_SOURCE_MAGIMG):
        print("Found img folder SASMODELS_SOURCE_MAGIMG   at", SASMODELS_SOURCE_MAGIMG)
        if not os.path.exists(SASMODELS_DEST_MAGIMG):
            print("Missing img folder SASMODELS_DEST_MAGIMG at", SASMODELS_DEST_MAGIMG)
            os.makedirs(SASMODELS_DEST_MAGIMG)
            print("created SASMODELS_DEST_MAGIMG at", SASMODELS_DEST_MAGIMG)
        print("Copying sasmodels mag image files...")
        for files in os.listdir(SASMODELS_SOURCE_MAGIMG):
            fromhere=os.path.join(SASMODELS_SOURCE_MAGIMG,files)
            tohere=os.path.join(SASMODELS_DEST_MAGIMG,files)
            shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_MAGIMG ,"was found")

    if os.path.exists(SASMODELS_SOURCE_SESANSIMG):
        print("Found img folder SASMODELS_SOURCE_SESANSIMG at", SASMODELS_SOURCE_SESANSIMG)
        if not os.path.exists(SASMODELS_DEST_SESANSIMG):
            print("Missing img folder SASMODELS_DEST_SESANSIMG at", SASMODELS_DEST_SESANSIMG)
            os.makedirs(SASMODELS_DEST_SESANSIMG)
            print("created SASMODELS_DEST_SESANSIMG at", SASMODELS_DEST_SESANSIMG)
        print("Copying sasmodels sesans image files...")
        for files in os.listdir(SASMODELS_SOURCE_SESANSIMG):
            fromhere=os.path.join(SASMODELS_SOURCE_SESANSIMG,files)
            tohere=os.path.join(SASMODELS_DEST_SESANSIMG,files)
            shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_SESANSIMG ,"was found")

    if os.path.exists(SASMODELS_SOURCE_REF_MODELS):
        print("Found docs folder SASMODELS_SOURCE_REF_MODELS at", SASMODELS_SOURCE_REF_MODELS)
        if os.path.exists(SASMODELS_DEST_REF_MODELS):
            print("Found docs folder SASMODELS_DEST_REF_MODELS at", SASMODELS_DEST_REF_MODELS)
            print("Copying sasmodels model toctree files...")
            for files in os.listdir(SASMODELS_SOURCE_REF_MODELS):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_REF_MODELS,files)
                    tohere=os.path.join(SASMODELS_DEST_REF_MODELS,files)
                    shutil.copy(fromhere,tohere)
            # But need to change the path to the model docs in the tocs
            for files in os.listdir(SASMODELS_DEST_REF_MODELS):
        #        print files
                if files.startswith("shape"):
                    print("Changing toc paths in", files)
                    inplace_change(os.path.join(SASMODELS_DEST_REF_MODELS,files), "../../model/", "models/")
                if files.startswith("sphere"):
                    print("Changing toc paths in", files)
                    inplace_change(os.path.join(SASMODELS_DEST_REF_MODELS,files), "../../model/", "models/")
                if files.startswith("custom"):
                    print("Changing toc paths in", files)
                    inplace_change(os.path.join(SASMODELS_DEST_REF_MODELS,files), "../../model/", "models/")
                if files.startswith("structure"):
                    print("Changing toc paths in", files)
                    inplace_change(os.path.join(SASMODELS_DEST_REF_MODELS,files), "../../model/", "models/")
    else:
        print("no source directory",SASMODELS_SOURCE_REF_MODELS," was found")

    if os.path.exists(SASMODELS_SOURCE_MODELS):
        print("Found docs folder SASMODELS_SOURCE_MODELS at", SASMODELS_SOURCE_MODELS)
        if os.path.exists(SASMODELS_DEST_MODELS):
            print("Found docs folder SASMODELS_DEST_MODELS at", SASMODELS_DEST_MODELS)
            print("Copying sasmodels model files...")
            for files in os.listdir(SASMODELS_SOURCE_MODELS):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_MODELS,files)
                    tohere=os.path.join(SASMODELS_DEST_MODELS,files)
                    shutil.copy(fromhere,tohere)
        else:
            print("Missing docs folder SASMODELS_DEST_MODELS at", SASMODELS_DEST_MODELS)
            os.makedirs(SASMODELS_DEST_MODELS)
            if not os.path.exists(SASMODELS_DEST_BUILDIMG):
                os.makedirs(SASMODELS_DEST_BUILDIMG)
            print("Created docs folder SASMODELS_DEST_MODELS at", SASMODELS_DEST_MODELS)
            print("Copying model files for build...")
            for files in os.listdir(SASMODELS_SOURCE_MODELS):
                if files.endswith(".rst"):
                    fromhere=os.path.join(SASMODELS_SOURCE_MODELS,files)
                    tohere=os.path.join(SASMODELS_DEST_MODELS,files)
                    shutil.copy(fromhere,tohere)
            # No choice but to do this because model files are all coded for images in /models/img
            print("Copying image files for build...")
            for files in os.listdir(SASMODELS_DEST_IMG):
                fromhere=os.path.join(SASMODELS_DEST_IMG,files)
                tohere=os.path.join(SASMODELS_DEST_BUILDIMG,files)
                shutil.copy(fromhere,tohere)
    else:
        print("no source directory",SASMODELS_SOURCE_MODELS,"was found.")
        print("!!!!NO MODEL DOCS WILL BE BUILT!!!!")

def fetch_katex(version, destination="_static"):
    from zipfile import ZipFile
    import urllib2
    url = "https://github.com/Khan/KaTeX/releases/download/%s/katex.zip" % version
    cache_path = "katex_%s.zip" % version
    if not os.path.exists(cache_path):
        try:
            fd_in = urllib2.urlopen(url)
            with open(cache_path, "wb") as fd_out:
                fd_out.write(fd_in.read())
        finally:
            fd_in.close()
    with ZipFile(cache_path) as zip:
        zip.extractall(destination)

def retrieve_bumps_docs():
    """
    Copies select files from the bumps documentation into fitting perspective
    """
    if os.path.exists(BUMPS_DOCS):
        print("=== Retrieve BUMPS Docs ===")
        filenames = [os.path.join(BUMPS_DOCS, "optimizer.rst")]
        filenames += glob(os.path.join(BUMPS_DOCS, "dream-*.png"))
        filenames += glob(os.path.join(BUMPS_DOCS, "fit-*.png"))
        for f in filenames:
            print("Copying file", f)
            shutil.copy(f, BUMPS_TARGET)
    else:
        print("""
======= Error =======
missing directory %s
The documentation will not include the optimizer selection section.
Checkout the bumps source tree and rebuild the docs.
""" % BUMPS_DOCS)

def apidoc():
    """
    Runs sphinx-apidoc to generate .rst files from the docstrings in .py files
    in the SasView build directory.
    """
    print("=== Generate API Rest Files ===")

    # Clean directory before generating a new version.
    _remove_dir(SPHINX_SOURCE_API)

    subprocess.call(["sphinx-apidoc",
                     "-o", SPHINX_SOURCE_API, # Output dir.
                     "-d", "8", # Max depth of TOC.
                     SASVIEW_BUILD])

def build_pdf():
    """
    Runs sphinx-build for pdf.  Reads in all .rst files and spits out the final html.
    """
    print("=== Build PDF Docs from ReST Files ===")
    subprocess.call(["sphinx-build",
                     "-b", "latex", # Builder name. TODO: accept as arg to setup.py.
                     "-d", os.path.join(SPHINX_BUILD, "doctrees"),
                     SPHINX_SOURCE,
                     os.path.join(SPHINX_BUILD, "latex")])

    LATEXDIR = os.path.join(SPHINX_BUILD, "latex")
    def pdflatex():
        subprocess.call(["pdflatex", "Sasview.tex"], cwd=LATEXDIR)
    pdflatex()
    pdflatex()
    pdflatex()
    subprocess.call(["makeindex", "-s", "python.ist", "Sasview.idx"], cwd=LATEXDIR)
    pdflatex()
    pdflatex()

    print("=== Copy PDF to HTML Directory ===")
    source = os.path.join(LATEXDIR, "Sasview.pdf")
    target = os.path.join(SASVIEW_DOCS, "Sasview.pdf")
    shutil.copyfile(source, target)

def build():
    """
    Runs sphinx-build.  Reads in all .rst files and spits out the final html.
    """
    print("=== Build HTML Docs from ReST Files ===")
    subprocess.call(["sphinx-build",
                     "-b", "html", # Builder name. TODO: accept as arg to setup.py.
                     "-d", os.path.join(SPHINX_BUILD, "doctrees"),
                     SPHINX_SOURCE,
                     os.path.join(SPHINX_BUILD, "html")])

    print("=== Copy HTML Docs to Build Directory ===")
    html = os.path.join(SPHINX_BUILD, "html")
    copy_tree(html, SASVIEW_DOCS)

def convert_katex():
    print("=== Preprocess HTML, converting latex to html ===")
    subprocess.call(["node", "convertKaTex.js", SASVIEW_DOCS])

def rebuild():
    clean()
    setup_source_temp()
    retrieve_user_docs()
    retrieve_bumps_docs()
    fetch_katex(version=KATEX_VERSION, destination=KATEX_PARENT)
    apidoc()
    build()
    #build_pdf()
    #convert_katex()

    print("=== Done ===")

if __name__ == "__main__":
    rebuild()
