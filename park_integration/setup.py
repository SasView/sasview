"""
     Installation script for SANS fitting
"""

# Then build and install the modules
from distutils.core import setup, Extension


setup(
    name="park_integration",
    version = "0.9.1",
    description = "Python module for fitting",
    author = "University of Tennessee",
    #author_email = "",
    url = "http://danse.chem.utk.edu",
    
    # Use the pure python modules
    package_dir = {"sans.fit":"src/sans/fit"},
    
    packages = ["sans.fit", "src/sans"]
    )
        