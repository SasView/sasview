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

from distutils.dir_util import copy_tree
from distutils.util import get_platform

platform = '.%s-%s'%(get_platform(),sys.version[:3])

CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

run = imp.load_source('run', os.path.join(CURRENT_SCRIPT_DIR, '..', '..', 'run.py'))
run.prepare()

SASVIEW_SRC = os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "src")
SASVIEW_BUILD = os.path.abspath(os.path.join(CURRENT_SCRIPT_DIR, "..", "..", "build", "lib"+platform))
SASVIEW_DOCS = os.path.join(SASVIEW_BUILD, "doc")

SPHINX_BUILD = os.path.join(CURRENT_SCRIPT_DIR, "build")
SPHINX_SOURCE = os.path.join(CURRENT_SCRIPT_DIR, "source")
SPHINX_SOURCE_API = os.path.join(SPHINX_SOURCE, "dev", "api")

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

if __name__ == "__main__":
    clean()
    retrieve_user_docs()
    apidoc()
    build()
	
    print "=== Done ==="