"""
     Installation script for DANSE data handling utilities
"""

# Then build and install the modules
from distutils.core import setup, Extension


setup(
    name="data_util",
    version = "1.0.0",
    description = "Utilities to handle data",
    
    package_dir = {"data_util":"."},
    packages = ["data_util"]
)
        