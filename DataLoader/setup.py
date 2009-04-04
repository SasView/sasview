"""
     Installation script for SANS DataLoader
"""
import os

# Then build and install the modules
from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib


setup(
    name="DataLoader",
    version = "0.1",
    description = "Python module for loading",
    author = "University of Tennessee",
    #author_email = "",
    url = "http://danse.chem.utk.edu",
    
    # Use the pure python modules
    package_dir = {"DataLoader":"."},
    
    packages = ["DataLoader","DataLoader.readers"],
    data_files=[(os.path.join(get_python_lib(),"DataLoader","readers"), ["readers/defaults.xml"])]
    )
        