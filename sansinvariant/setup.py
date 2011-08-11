"""
    Setup for invariant
"""
from distutils.core import setup

setup(
    name="sansinvariant",
    version = "0.9",
    description = "Python module for invariant calculation",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",

    # Use the pure python modules
    package_dir = {"sans.invariant":"src/sans/invariant"},
    packages = ["sans.invariant", "src/sans"],
    )
