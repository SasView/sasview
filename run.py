#!/usr/bin/env python
# -*- coding: utf-8 -*-
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
from __future__ import print_function

import imp
import os
import sys
from contextlib import contextmanager
from os.path import join as joinpath
from os.path import abspath, dirname

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
    # print "importing", modname, "from", path
    return imp.load_dynamic(modname, path)


def prepare(rebuild=True):
    # Don't create *.pyc files
    sys.dont_write_bytecode = True

    # Debug numpy warnings
    #import numpy; numpy.seterr(all='raise')

    # find the directories for the source and build
    from distutils.util import get_platform
    root = abspath(dirname(__file__))
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

    try:
        import tinycc
    except ImportError:
        addpath(joinpath(root, '../tinycc/build/lib'))

    # select wx version
    #addpath(os.path.join(root, '..','wxPython-src-3.0.0.0','wxPython'))

    # Put the sas source tree on the path
    addpath(joinpath(root, 'src'))

    # Put sasmodels on the path
    addpath(joinpath(root, '../sasmodels/'))

    # Check if the C extensions are already built
    try:
        from sas.sascalc.pr import _pr_inversion
        from sas.sascalc.calculator import _sld2i
        from sas.sascalc.file_converter import _bsl_loader
    except ImportError:
        rebuild = True

    # Build C extensions if necessary.  Do an inplace build to simplify path.
    if rebuild:
        import subprocess
        build_cmd = [sys.executable, "setup.py", "build_ext", "--inplace", "update"]
        if os.name == 'nt':
            build_cmd.append('--compiler=tinycc')
        # need shell=True on windows to keep console box from popping up
        shell = (os.name == 'nt')
        with cd(root):
            subprocess.call(build_cmd, shell=shell)

    set_git_tag()
    # print "\n".join(sys.path)

def set_git_tag():
    try:
        import subprocess
        import os
        import platform
        FNULL = open(os.devnull, 'w')
        if platform.system() == "Windows":
            args = ['git', 'describe', '--tags']
        else:
            args = ['git describe --tags']
        git_revision = subprocess.check_output(args, stderr=FNULL, shell=True)
        import sas.sasview
        sas.sasview.__build__ = str(git_revision).strip()
    except subprocess.CalledProcessError as cpe:
        get_logger().warning("Error while determining build number\n  Using command:\n %s \n Output:\n %s"% (cpe.cmd,cpe.output))

_logger = None
def get_logger():
    global _logger
    if _logger is None:
        from sas.logger_config import SetupLogger
        _logger = SetupLogger(__name__).config_development()
    return _logger

if __name__ == "__main__":
    # Need to add absolute path before actual prepare call,
    # so logging can be done during initialization process too
    root = abspath(dirname(__file__))
    addpath(joinpath(root, 'src'))

    get_logger().debug("Starting SASVIEW in debug mode.")
    prepare()
    from sas.sasview.sasview import run_cli, run_gui
    if len(sys.argv) == 1:
        run_gui()
    else:
        run_cli()
    get_logger().debug("Ending SASVIEW in debug mode.")
