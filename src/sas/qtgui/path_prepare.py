"""
Prepare python system path to point to right locations
"""
import imp
import os
import sys

def exe_run():
    """
    Check if the process is run as .exe or as .py
    Primitive extension check of the name of the running process
    """
    # Could be checking for .exe, but on mac/linux this wouldn't work well
    return os.path.splitext(sys.argv[0])[1].lower() != ".py"

def addpath(path):
    """
    Add a directory to the python path environment, and to the PYTHONPATH
    environment variable for subprocesses.
    """
    path = os.path.abspath(path)
    if 'PYTHONPATH' in os.environ:
        PYTHONPATH = path + os.pathsep + os.environ['PYTHONPATH']
    else:
        PYTHONPATH = path
    os.environ['PYTHONPATH'] = PYTHONPATH
    sys.path.insert(0, path)

def import_package(modname, path):
    """Import a package into a particular point in the python namespace"""
    mod = imp.load_source(modname, os.path.abspath(os.path.join(path,'__init__.py')))
    sys.modules[modname] = mod
    mod.__path__ = [os.path.abspath(path)]
    return mod

root = ""
if exe_run():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    addpath(os.path.join(root, 'src'))
    addpath('src')
else:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    #addpath(os.path.join(root, 'src'))
    #addpath('src')
    # Add the local build directory to PYTHONPATH
    from distutils.util import get_platform
    platform = '%s-%s'%(get_platform(),sys.version[:3])
    build_path = os.path.join(root, 'build','lib.'+platform)
    sys.path.append(build_path)

