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

import imp
import os
import sys
from contextlib import contextmanager
from os.path import join as joinpath
from os.path import abspath, dirname, realpath


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


def import_package(modname, path):
    """Import a package into a particular point in the python namespace"""
    #logger.debug("Dynamicly importing: %s", path)
    mod = imp.load_source(modname, abspath(joinpath(path, '__init__.py')))
    sys.modules[modname] = mod
    mod.__path__ = [abspath(path)]
    return mod


def import_dll(modname, build_path):
    """Import a DLL from the build directory"""
    import sysconfig
    ext = sysconfig.get_config_var('SO')
    # build_path comes from context
    path = joinpath(build_path, *modname.split('.')) + ext
    return imp.load_dynamic(modname, path)


def prepare():
    # Don't create *.pyc files
    sys.dont_write_bytecode = True

    # Debug numpy warnings
    #import numpy; numpy.seterr(all='raise')

    # find the directories for the source and build
    from distutils.util import get_platform
    root = abspath(dirname(sys.argv[0]))

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
    except:
        addpath(joinpath(root, '..', 'periodictable'))

    try:
        import bumps
    except:
        addpath(joinpath(root, '..', 'bumps'))

    # Build project if the build directory does not already exist.
    if not os.path.exists(build_path):
        import subprocess
        with cd(root):
            subprocess.call((sys.executable, "setup.py", "build"), shell=False)

    # Put the source trees on the path
    addpath(joinpath(root, 'src'))

    # sasmodels on the path
    addpath(joinpath(root, '../sasmodels/'))

    # Import the sasview package from root/sasview as sas.sasview.  It would
    # be better to just store the package in src/sas/sasview.
    #import sas
    #sas.sasview = import_package('sas.sasview', joinpath(root, 'src','sas','sasview'))

    # Compiled modules need to be pulled from the build directory.
    # Some packages are not where they are needed, so load them explicitly.
    import sas.sascalc.pr
    sas.sascalc.pr.core = import_package('sas.sascalc.pr.core',
                                         joinpath(build_path, 'sas', 'sascalc', 'pr', 'core'))

    # Compiled modules need to be pulled from the build directory.
    # Some packages are not where they are needed, so load them explicitly.
    import sas.sascalc.file_converter
    sas.sascalc.file_converter.core = import_package('sas.sascalc.file_converter.core',
                                                     joinpath(build_path, 'sas', 'sascalc', 'file_converter', 'core'))

    # Compiled modules need to be pulled from the build directory.
    # Some packages are not where they are needed, so load them explicitly.
    import sas.sascalc.calculator
    sas.sascalc.calculator.core = import_package('sas.sascalc.calculator.core',
                                  joinpath(build_path, 'sas', 'sascalc', 'calculator', 'core'))

    sys.path.append(build_path)

if __name__ == "__main__":
    # Need to add absolute path before actual prepare call,
    # so logging can be done during initialization process too
    root = abspath(dirname(realpath(sys.argv[0])))
    addpath(joinpath(root, 'src','sas'))
    from logger_config import SetupLogger
    logger = SetupLogger(__name__).config_development()

    logger.debug("Starting SASVIEW in debug mode.")
    prepare()
    from sas.qtgui.MainWindow.MainWindow import run
    run()
    logger.debug("Ending SASVIEW in debug mode.")
