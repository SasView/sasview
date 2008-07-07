"""
     Installation script for SANS DataLoader
"""

# Then build and install the modules
from distutils.core import setup, Extension


setup(
    name="DataLoader",
    version = "0.1",
    description = "Python module for loading",
    author = "University of Tennessee",
    #author_email = "",
    url = "http://danse.chem.utk.edu",
    
    # Use the pure python modules
    package_dir = {"DataLoader":"."},
    
    packages = ["DataLoader","DataLoader.readers"]
    )
        