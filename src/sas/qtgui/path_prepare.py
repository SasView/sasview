"""
Prepare python system path to point to right locations
"""
import imp
import os
import sys
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

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
addpath(os.path.join(root, 'src'))
#addpath(os.path.join(root, '../sasmodels/'))
import sas
from distutils.util import get_platform
sas.sasview = import_package('sas.sasview', os.path.join(root,'sasview'))
platform = '%s-%s'%(get_platform(),sys.version[:3])
build_path = os.path.join(root, 'build','lib.'+platform)
sys.path.append(build_path)
