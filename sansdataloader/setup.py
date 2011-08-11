"""
     Installation script for SANS DataLoader
"""
import os


# Then build and install the modules
from distutils.core import setup#, Extension
#from numpy.distutils.misc_util import get_numpy_include_dirs
#numpy_incl_path = os.path.join(get_numpy_include_dirs()[0], "numpy")
setup(
    name="sansdataloader",
    version = "0.9.1",
    description = "Python module for loading",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    
    package_dir = {"sans": os.path.join("src", "sans"),
                   "sans.dataloader":os.path.join("src",
                                                  "sans", "dataloader")},
    package_data={"sans.dataloader.readers": ['defaults.xml']},
    packages = ["sans.dataloader","sans", "sans.dataloader.readers"]
    )
        