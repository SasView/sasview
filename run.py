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

import os
import sys
import imp
import logging
import logging.config

from contextlib import contextmanager
from os.path import abspath, dirname, join as joinpath


LOGGER_CONFIG_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'sasview/logging.ini')
logging.config.fileConfig(LOGGER_CONFIG_FILE, disable_existing_loggers=True)
logger = logging.getLogger(__name__)

def update_all_logs_to_debug(logger):
    '''
    This updates all loggers and respective handlers to DEBUG
    '''
    for handler in logger.handlers or logger.parent.handlers:
        handler.setLevel(logging.DEBUG)
    for name,_ in logging.Logger.manager.loggerDict.items():
        logging.getLogger(name).setLevel(logging.DEBUG)
        
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
    mod = imp.load_source(modname, abspath(joinpath(path,'__init__.py')))
    sys.modules[modname] = mod
    mod.__path__ = [abspath(path)]
    return mod

def import_dll(modname, build_path):
    """Import a DLL from the build directory"""
    import sysconfig
    ext = sysconfig.get_config_var('SO')
    # build_path comes from context
    path = joinpath(build_path, *modname.split('.'))+ext
    #print "importing", modname, "from", path
    return imp.load_dynamic(modname, path)

def prepare():
    # Don't create *.pyc files
    sys.dont_write_bytecode = True

    # Debug numpy warnings
    #import numpy; numpy.seterr(all='raise')

    # find the directories for the source and build
    from distutils.util import get_platform
    root = abspath(dirname(__file__))
    platform = '%s-%s'%(get_platform(),sys.version[:3])
    build_path = joinpath(root, 'build','lib.'+platform)

    # Notify the help menu that the Sphinx documentation is in a different
    # place than it otherwise would be.
    os.environ['SASVIEW_DOC_PATH'] = joinpath(build_path, "doc")

    # Make sure that we have a private version of mplconfig
    #mplconfig = joinpath(abspath(dirname(__file__)), '.mplconfig')
    #os.environ['MPLCONFIGDIR'] = mplconfig
    #if not os.path.exists(mplconfig): os.mkdir(mplconfig)
    #import matplotlib
    #matplotlib.use('Agg')
    #print matplotlib.__file__
    #import pylab; pylab.hold(False)
    # add periodictable to the path
    try: import periodictable
    except: addpath(joinpath(root, '..','periodictable'))

    try: import bumps
    except: addpath(joinpath(root, '..','bumps'))

    # select wx version
    #addpath(os.path.join(root, '..','wxPython-src-3.0.0.0','wxPython'))

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
    import sas
    sas.sasview = import_package('sas.sasview', joinpath(root,'sasview'))

    # The sas.models package Compiled Model files should be pulled in from the build directory even though
    # the source is stored in src/sas/models.

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

    #print "\n".join(sys.path)

if __name__ == "__main__":
    update_all_logs_to_debug(logger)
    prepare()
    from sas.sasview.sasview import run
    run()
    
