"""
     Installation script for SANS gui tools
"""

# Then build and install the modules
from distutils.core import setup, Extension


setup(
    name="guitools",
    version = "0.1",
    description = "Python module for SANS gui tools",
    author = "University of Tennessee",
    #author_email = "",
    url = "http://danse.chem.utk.edu",
    
    # Place this module under the sans package
    #ext_package = "sans",
    
    # Use the pure python modules
    package_dir = {"sans.guitools":"."},
    
    packages = ["sans.guitools"]
    )
        