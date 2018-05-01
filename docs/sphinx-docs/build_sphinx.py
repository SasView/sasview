#!/usr/bin/env python
"""
Functions for building sphinx docs.

For more information on the invocation of sphinx see:
http://sphinx-doc.org/invocation.html
"""
from __future__ import print_function

import subprocess
import os
from os.path import join as joinpath, abspath, dirname, isdir, exists, relpath
import sys
import fnmatch
import shutil
import imp

from glob import glob
from distutils.dir_util import copy_tree
from distutils.util import get_platform
from distutils.spawn import find_executable

from shutil import copy
from os import listdir

platform = '.%s-%s'%(get_platform(),sys.version[:3])

# sphinx paths
SPHINX_ROOT = dirname(abspath(__file__))
SPHINX_BUILD = joinpath(SPHINX_ROOT, "build")
SPHINX_SOURCE = joinpath(SPHINX_ROOT, "source-temp")
SPHINX_PERSPECTIVES = joinpath(SPHINX_SOURCE, "user", "qtgui", "perspectives")

# sasview paths
SASVIEW_ROOT = joinpath(SPHINX_ROOT, '..', '..')
SASVIEW_DOCS = joinpath(SPHINX_ROOT, "source")
SASVIEW_BUILD = abspath(joinpath(SASVIEW_ROOT, "build", "lib"+platform))
SASVIEW_MEDIA_SOURCE = joinpath(SASVIEW_ROOT, "src", "sas")
SASVIEW_DOC_TARGET = joinpath(SASVIEW_BUILD, "doc")
SASVIEW_API_TARGET = joinpath(SPHINX_SOURCE, "dev", "sasview-api")

# sasmodels paths
SASMODELS_ROOT = joinpath(SASVIEW_ROOT, "..", "sasmodels")
SASMODELS_DOCS = joinpath(SASMODELS_ROOT, "doc")
SASMODELS_BUILD = joinpath(SASMODELS_ROOT, "build", "lib")
SASMODELS_MODEL_SOURCE = joinpath(SASMODELS_DOCS, "model")
SASMODELS_MODEL_TARGET = joinpath(SPHINX_SOURCE, "user", "models")
#SASMODELS_API_SOURCE = joinpath(SASMODELS_DOCS, "api")
SASMODELS_API_TARGET = joinpath(SPHINX_SOURCE, "dev", "sasmodels-api")
SASMODELS_DEV_SOURCE = joinpath(SASMODELS_DOCS, "developer")
SASMODELS_DEV_TARGET = joinpath(SPHINX_SOURCE, "dev", "sasmodels-dev")
SASMODELS_GUIDE_SOURCE = joinpath(SASMODELS_DOCS, "guide")
SASMODELS_GUIDE_TARGET = joinpath(SPHINX_PERSPECTIVES, "fitting")
SASMODELS_GUIDE_EXCLUDE = [
    "index.rst", "install.rst", "intro.rst",
]

# bumps paths
BUMPS_DOCS = joinpath(SASVIEW_ROOT, "..", "bumps", "doc")
BUMPS_SOURCE = joinpath(BUMPS_DOCS, "guide")
BUMPS_TARGET = joinpath(SPHINX_PERSPECTIVES, "fitting")

run = imp.load_source('run', joinpath(SASVIEW_ROOT, 'run.py'))
run.prepare()

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
    if isdir(dir_path):
        print("Removing \"%s\"... " % dir_path)
        shutil.rmtree(dir_path)

def clean():
    """
    Clean the sphinx build directory.
    """
    print("=== Cleaning Sphinx Build ===")
    _remove_dir(SASVIEW_DOC_TARGET)
    _remove_dir(SPHINX_BUILD)
    _remove_dir(SPHINX_SOURCE)

def setup_source_temp():
    """
    Copy the source toctrees to new folder for assembling the sphinx-docs
    """
    print("=== Copying Source toctrees ===")
    shutil.copytree(SASVIEW_DOCS, SPHINX_SOURCE)

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

    # Copy documentation files from sas/.../media to the sphinx directory
    for root, dirs, _ in os.walk(SASVIEW_MEDIA_SOURCE):
        if 'media' in dirs:
            source_dir = abspath(joinpath(root, "media"))
            relative = dirname(relpath(source_dir, SASVIEW_MEDIA_SOURCE))
            dest_dir = joinpath(SPHINX_SOURCE, "user", relative)

            print("Found sasview docs folder at \"%s\"." % relative)
            copy_tree(source_dir, dest_dir)

    print("=== Sasmodels Docs ===")
    shutil.copy(joinpath(SASMODELS_DOCS, "rst_prolog"), SPHINX_SOURCE)
    copy_tree(SASMODELS_MODEL_SOURCE, SASMODELS_MODEL_TARGET)
    #copy_tree(SASMODELS_API_SOURCE, SASMODELS_API_TARGET)
    copy_tree(SASMODELS_DEV_SOURCE, SASMODELS_DEV_TARGET)
    copy_tree(SASMODELS_GUIDE_SOURCE, SASMODELS_GUIDE_TARGET)
    for filename in SASMODELS_GUIDE_EXCLUDE:
        os.unlink(joinpath(SASMODELS_GUIDE_TARGET, filename))

    # Model category files reference the model as ../../model/name.rst.  Since
    # we are rearranging the tree, we need to update each of these links.
    catdir = joinpath(SASMODELS_GUIDE_TARGET, "models")
    for filename in os.listdir(catdir):
        inplace_change(joinpath(catdir, filename), "../../model/", "/user/models/")


def retrieve_bumps_docs():
    """
    Copies select files from the bumps documentation into fitting perspective
    """
    if exists(BUMPS_SOURCE):
        print("=== Retrieve BUMPS Docs ===")
        filenames = [joinpath(BUMPS_SOURCE, "optimizer.rst")]
        filenames += glob(joinpath(BUMPS_SOURCE, "dream-*.png"))
        filenames += glob(joinpath(BUMPS_SOURCE, "fit-*.png"))
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
    #_remove_dir(SASVIEW_API_TARGET)

    subprocess.call(["sphinx-apidoc",
                     "-o", SASVIEW_API_TARGET, # Output dir.
                     "-d", "8", # Max depth of TOC.
                     "-H", "SasView", # Package header
                     SASVIEW_BUILD])

    subprocess.call(["sphinx-apidoc",
                     "-o", SASMODELS_API_TARGET, # Output dir.
                     "-d", "8", # Max depth of TOC.
                     "-H", "sasmodels", # Package header
                     SASMODELS_BUILD,
                     joinpath(SASMODELS_BUILD, "sasmodels", "models"), # exclude
                     ])

def build_pdf():
    """
    Runs sphinx-build for pdf.  Reads in all .rst files and spits out the final html.
    """
    print("=== Build PDF Docs from ReST Files ===")
    subprocess.call(["sphinx-build",
                     "-b", "latex", # Builder name. TODO: accept as arg to setup.py.
                     "-d", joinpath(SPHINX_BUILD, "doctrees"),
                     SPHINX_SOURCE,
                     joinpath(SPHINX_BUILD, "latex")])

    LATEXDIR = joinpath(SPHINX_BUILD, "latex")
    #TODO: Does it need to be done so many time?
    def pdflatex():
        subprocess.call(["pdflatex", "SasView.tex"], cwd=LATEXDIR)
    pdflatex()
    pdflatex()
    pdflatex()
    subprocess.call(["makeindex", "-s", "python.ist", "SasView.idx"], cwd=LATEXDIR)
    pdflatex()
    pdflatex()

    print("=== Copy PDF to HTML Directory ===")
    source = joinpath(LATEXDIR, "SasView.pdf")
    target = joinpath(SASVIEW_DOC_TARGET, "SasView.pdf")
    shutil.copyfile(source, target)

def build():
    """
    Runs sphinx-build.  Reads in all .rst files and spits out the final html.
    """
    print("=== Build HTML Docs from ReST Files ===")
    subprocess.call(["sphinx-build",
                     "-b", "qthelp", # Builder name. TODO: accept as arg to setup.py.
                     "-d", joinpath(SPHINX_BUILD, "doctrees"),
                     SPHINX_SOURCE,
                     joinpath(SPHINX_BUILD, "html")])

    print("=== Copy HTML Docs to Build Directory ===")
    html = joinpath(SPHINX_BUILD, "html")
    copy_tree(html, SASVIEW_DOC_TARGET)

def fetch_katex(version, destination="_static"):
    from zipfile import ZipFile
    import urllib2
    url = "https://github.com/Khan/KaTeX/releases/download/%s/katex.zip" % version
    cache_path = "katex_%s.zip" % version
    if not exists(cache_path):
        try:
            fd_in = urllib2.urlopen(url)
            with open(cache_path, "wb") as fd_out:
                fd_out.write(fd_in.read())
        finally:
            fd_in.close()
    with ZipFile(cache_path) as zip:
        zip.extractall(destination)

def convert_katex():
    print("=== Preprocess HTML, converting latex to html ===")
    subprocess.call(["node", "convertKaTex.js", SASVIEW_DOC_TARGET])

def convert_mathjax():
    print("=== Preprocess HTML, converting latex to html ===")
    subprocess.call(["node", "convertMathJax.js", SASVIEW_DOC_TARGET])

def fetch_mathjax():
    subprocess.call(["npm", "install", "mathjax-node-page"])
    # TODO: copy fonts from node_modules/mathjax/fonts/HTML-CSS/Tex into static

def rebuild():
    clean()
    setup_source_temp()
    retrieve_user_docs()
    retrieve_bumps_docs()
    #fetch_katex(version=KATEX_VERSION, destination=KATEX_PARENT)
    #fetch_mathjax()
    apidoc()
    build()
    if find_executable('latex'):
        build_pdf()
    #convert_katex()
    #convert_mathjax()

    print("=== Done ===")

if __name__ == "__main__":
    rebuild()
