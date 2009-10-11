"""
     Installation script for SANS DataLoader
"""
import os, sys
    
# Then build and install the modules
from distutils.core import setup, Extension
from distutils.sysconfig import get_python_lib
numpy_incl_path = os.path.join(sys.prefix, "Lib", "site-packages", "numpy", "core", "include", "numpy")

setup(
    name="DataLoader",
    version = "0.1",
    description = "Python module for loading",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    
    package_dir = {"DataLoader":".",
                   "DataLoader.extensions":"extensions"},
    
    data_files=[(os.path.join(get_python_lib(),"DataLoader","readers"), ["readers/defaults.xml"])],
    packages = ["DataLoader","DataLoader.readers","DataLoader.extensions"],
    
    ext_modules = [ Extension("DataLoader.extensions.smearer",
     sources = [
        "extensions/smearer_module.cpp",
        "extensions/smearer.cpp",
            ],
         include_dirs=["extensions", numpy_incl_path]
     
     
     )])
        