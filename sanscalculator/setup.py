"""
    Setup for Calculator plug-in
"""
from distutils.core import setup

setup(
    name="sanscalculator",
    version = "1.0.0",
    description = "Python module for sld  calculation",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",

    # Use the pure python modules
    package_dir = {"sans":"src/sans",
                   "sans.calculator":"src/sans/calculator"},
    packages = ["sans", "sans.calculator"],
    )
