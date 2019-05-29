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

    # find the directories for the source and build
    from distutils.util import get_platform
    root = joinpath(abspath(dirname(sys.argv[0])), '..')

    platform = '%s-%s' % (get_platform(), sys.version[:3])
    build_path = joinpath(root, 'build', 'lib.' + platform)

    # Notify the help menu that the Sphinx documentation is in a different
    # place than it otherwise would be.
    os.environ['SASVIEW_DOC_PATH'] = joinpath(build_path, "doc")

    # add periodictable to the path
    try:
        import periodictable
    except:
        addpath(joinpath(root, '..', 'periodictable'))

    try:
        import bumps
    except:
        addpath(joinpath(root, '..', 'bumps'))

    # Put the source trees on the path
    addpath(joinpath(root, 'src'))

    # sasmodels on the path
    addpath(joinpath(root, '../sasmodels/'))

    from sas.sascalc.dataloader.readers import (
        abs_reader, anton_paar_saxs_reader, ascii_reader, cansas_reader_HDF5,
        cansas_reader, danse_reader, red2d_reader, sesans_reader, tiff_reader,
        xml_reader,
    )

    sys.path.append(build_path)

if __name__ == "__main__":
    # Need to add absolute path before actual prepare call,
    # so logging can be done during initialization process too
    root = abspath(dirname(realpath(sys.argv[0])))
    addpath(joinpath(root, '..', 'src','sas'))

    prepare()
    from sas.qtgui.MainWindow.MainWindow import run_sasview
    run_sasview()

