"""
    Setup for invariant
"""

import sys
if len(sys.argv) == 1:
    sys.argv.append('install')
# Then build and install the modules
from distutils.core import setup

setup(
    name="sans.Invariant",
    version = "0.1",
    description = "Python module for fitting",
    author = "University of Tennessee",
    #author_email = "",
    url = "http://danse.chem.utk.edu",
    
    # Use the pure python modules
    package_dir = {"sans.Invariant":"."},
    
    packages = ["sans.Invariant"]
    )
        