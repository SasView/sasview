"""
    Setup for Calculator plug-in
"""
import sys
if len(sys.argv) == 1:
    sys.argv.append('install')
    
from distutils.core import setup

setup(
    name="sans.calculator",
    version = "0.1",
    description = "Python module for sld  calculation",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    
    # Use the pure python modules
    package_dir = {"sans.calculator":"."},
    
    packages = ["sans.calculator"]
    )
        