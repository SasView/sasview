# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
Run sasview in place.  This allows sasview to use the python
files in the source tree without having to call setup.py install
first.  A rebuild is still necessary when working on sas models
or c modules.

Usage:

./run.py [(module|script) args...]

Without arguments run.py runs sasview.  With arguments, run.py will run
the given module or script.
"""

import sys
import os
from os.path import abspath, dirname, realpath, join as joinpath
from contextlib import contextmanager
from importlib import import_module

def addpath(path):
    """
    Add a directory to the python path environment, and to the PYTHONPATH
    environment variable for subprocesses.
    """
    path = abspath(path)
    if 'PYTHONPATH' in os.environ:
        PYTHONPATH = path + os.pathsep + os.environ['PYTHONPATH']
    else:
        PYTHONPATH = path
    os.environ['PYTHONPATH'] = PYTHONPATH
    sys.path.insert(0, path)

@contextmanager
def cd(path):
    """
    Change directory for duration of "with" context.
    """
    old_dir = os.getcwd()
    os.chdir(path)
    yield
    os.chdir(old_dir)

def prepare():
    # Don't create *.pyc files
    sys.dont_write_bytecode = True

    # Turn numpy warnings into errors
    #import numpy; numpy.seterr(all='raise')

    # Find the directories for the source and build
    root = abspath(dirname(realpath(__file__)))

    # TODO: Do we prioritize the sibling repo or the installed package?
    # TODO: Can we use sasview/run.py from a distributed sasview.exe?
    # Put supporting packages on the path if they are not already available.
    for sibling in ('periodictable', 'bumps', 'sasdata', 'sasmodels'):
        try:
            import_module(sibling)
        except:
            addpath(joinpath(root, '..', sibling))

    # Put the source trees on the path
    addpath(joinpath(root, 'src'))

    # == no more C sources so no need to build project to run it ==
    # Leave this snippet around in case we add a compile step later.
    #from distutils.util import get_platform
    #platform = '%s-%s' % (get_platform(), sys.version[:3])
    #build_path = joinpath(root, 'build', 'lib.' + platform)
    ## Build project if the build directory does not already exist.
    #if not os.path.exists(build_path):
    #    import subprocess
    #    with cd(root):
    #        subprocess.call((sys.executable, "setup.py", "build"), shell=False)

    # Notify the help menu that the Sphinx documentation is in a different
    # place than it otherwise would be.
    docpath = joinpath(root, 'docs', 'sphinx-docs', '_build', 'html')
    os.environ['SASVIEW_DOC_PATH'] = docpath

if __name__ == "__main__":
    prepare()
    import sas.cli
    sys.exit(sas.cli.main(logging="development"))
