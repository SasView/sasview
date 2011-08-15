"""
     Installation script for SANS gui tools
"""
import os
# Then build and install the modules
from distutils.core import setup
setup(
    name="simulationview",
    version = "0.1.1",
    description = "Python module for SANS SimView",
    author = "University of Tennessee",
    #author_email = "",
    url = "http://danse.chem.utk.edu",
    
    # Place this module under the sans package
    #ext_package = "sans",
    
    # Use the pure python modules
    package_dir = {"sans":".",
                   "sans.perspectives":os.path.join("src", "sans",
                                          "perspectives"),
                   "sans.perspectives.simulation":os.path.join("src", "sans",
                                          "perspectives",
                                          "simulation")},
    
    packages = ["sans", "sans.perspectives", "sans.perspectives.simulation"]
    )
        