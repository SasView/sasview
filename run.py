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

    # Put supporting packages on the path if they are not already available.
    for sibling in ('periodictable', 'bumps', 'sasdata', 'sasmodels'):
        # run.py is only used by developers. The sibling directory should be the priority over installed packages.
        #   This allows developers to modify and use separate packages simultaneously.
        devel_path = joinpath(root, '..', sibling)
        if os.path.exists(devel_path):
            addpath(devel_path)
        else:
            try:
                import_module(sibling)
            except ImportError:
                raise ImportError(f"The {sibling} module is not available. Either pip install it in your environment or"
                                  f" clone the repository into a directory level with the sasview directory.")


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

    from sas.qtgui.convertUI import rebuild_new_ui
    rebuild_new_ui()

    import sas.cli
    sys.exit(sas.cli.main(logging="development"))
