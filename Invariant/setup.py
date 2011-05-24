"""
    Setup for invariant
"""
from distutils.core import setup

setup(
    name="sans.invariant",
    version = "0.9",
    description = "Python module for invariant calculation",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    
    # Use the pure python modules
    package_dir = {"sans.invariant":"."},
    
    packages = ["sans.invariant"]
    )
        