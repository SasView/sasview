"""
     Installation script for SANS DataLoader
"""
import os
import sys

# Then build and install the modules
from distutils.core import setup#, Extension
#from numpy.distutils.misc_util import get_numpy_include_dirs
#numpy_incl_path = os.path.join(get_numpy_include_dirs()[0], "numpy")
setup(
    name="DataLoader",
    version = "0.2",
    description = "Python module for loading",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    
    package_dir = {"DataLoader":"."},
    package_data={"DataLoader.readers": ['defaults.xml']},
    packages = ["DataLoader","DataLoader.readers"]
    )
        