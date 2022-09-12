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
    import sas
    plugin_dir = os.path.join(sas.get_user_dir(), PLUGIN_MODEL_DIR)
    os.environ['SAS_MODELPATH'] = plugin_dir

def prepare():
    # Don't create *.pyc files
    sys.dont_write_bytecode = True

    # Debug numpy warnings
    #import numpy; numpy.seterr(all='raise')

    # find the directories for the source and build
    from distutils.util import get_platform
    root = abspath(dirname(realpath(__file__)))

    platform = '%s-%s' % (get_platform(), sys.version[:3])
    build_path = joinpath(root, 'build', 'lib.' + platform)

    # Notify the help menu that the Sphinx documentation is in a different
    # place than it otherwise would be.
    os.environ['SASVIEW_DOC_PATH'] = joinpath(build_path, "doc")

    # Make sure that we have a private version of mplconfig
    #mplconfig = joinpath(abspath(dirname(__file__)), '.mplconfig')
    #os.environ['MPLCONFIGDIR'] = mplconfig
    #if not os.path.exists(mplconfig): os.mkdir(mplconfig)
    #import matplotlib
    # matplotlib.use('Agg')
    # print matplotlib.__file__
    #import pylab; pylab.hold(False)
    # add periodictable to the path
    try:
        import periodictable
    except ImportError:
        addpath(joinpath(root, '..', 'periodictable'))

    try:
        import bumps
    except ImportError:
        addpath(joinpath(root, '..', 'bumps'))

    # == no more C sources so no need to build project to run it ==
    ## Build project if the build directory does not already exist.
    #if not os.path.exists(build_path):
    #    import subprocess
    #    with cd(root):
    #        subprocess.call((sys.executable, "setup.py", "build"), shell=False)

    # Put the source trees on the path
    addpath(joinpath(root, 'src'))

    # sasmodels on the path
    addpath(joinpath(root, '../sasmodels/'))

    # Note: only needed when running gui so suppress for now.
    ## Run the UI conversion tool.
    #import sas.qtgui.convertUI

    # initialize OpenCL setting
    import sas
    SAS_OPENCL = sas.config.SAS_OPENCL
    if SAS_OPENCL and "SAS_OPENCL" not in os.environ:
        os.environ["SAS_OPENCL"] = SAS_OPENCL


if __name__ == "__main__":
    # Need to add absolute path before actual prepare call,
    # so logging can be done during initialization process too
    root = abspath(dirname(realpath(sys.argv[0])))

    addpath(joinpath(root, 'src'))
    # addpath(joinpath(root, joinpath('..', 'sasmodels'))) # dependency (for loading custom_config.py during log setup)

    #from sas.logger_config import SetupLogger
    #logger = SetupLogger(__name__).config_development()

    #logger.debug("Starting SASVIEW in debug mode.")
    prepare()
    # Run the UI conversion tool when executed from script.  This has to
    # happen after prepare() so that sas.qtgui is on the path.
    import sas.qtgui.convertUI
    setup_sasmodels()

    from sas.qtgui.MainWindow.MainWindow import run_sasview
    run_sasview()
    #logger.debug("Ending SASVIEW in debug mode.")
