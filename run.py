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

PLUGIN_MODEL_DIR = 'plugin_models'

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

def setup_sasmodels():
    """
    Prepare sasmodels for running within sasview.
    """
    # Set SAS_MODELPATH so sasmodels can find our custom models

    from sas.system.user import get_user_dir
    plugin_dir = os.path.join(get_user_dir(), PLUGIN_MODEL_DIR)
    os.environ['SAS_MODELPATH'] = plugin_dir

def prepare():
    # Don't create *.pyc files
    sys.dont_write_bytecode = True

    # find the directories for the source and build
    from distutils.util import get_platform
    root = abspath(dirname(realpath(__file__)))

    platform = '%s-%s' % (get_platform(), sys.version[:3])
    build_path = joinpath(root, 'build', 'lib.' + platform)

    # Notify the help menu that the Sphinx documentation is in a different
    # place than it otherwise would be.
    os.environ['SASVIEW_DOC_PATH'] = joinpath(build_path, "doc")

    try:
        import periodictable
    except ImportError:
        addpath(joinpath(root, '..', 'periodictable'))

    try:
        import bumps
    except ImportError:
        addpath(joinpath(root, '..', 'bumps'))

    # Put the source trees on the path
    addpath(joinpath(root, 'src'))

    # sasmodels on the path
    addpath(joinpath(root, '../sasmodels/'))



if __name__ == "__main__":
    # Need to add absolute path before actual prepare call,
    # so logging can be done during initialization process too
    root = abspath(dirname(realpath(sys.argv[0])))

    addpath(joinpath(root, 'src'))
    prepare()

    # Run the UI conversion tool when executed from script.  This has to
    # happen after prepare() so that sas.qtgui is on the path.
    import sas.qtgui.convertUI
    setup_sasmodels()

    from sas.qtgui.MainWindow.MainWindow import run_sasview
    run_sasview()
    #logger.debug("Ending SASVIEW in debug mode.")
