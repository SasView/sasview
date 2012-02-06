"""
     Installation script for DANSE plot tools
"""
import os
# Then build and install the modules
#from setuptools import setup, find_packages
from distutils.core import setup

setup(
    name="plottools",
    version = "1.1.0",
    description = "Python plotting tools for wx",

    # We are living in the danse.common namespace, but there may be
    # other packages there, so declare ourselves to be a namespace package.
    #namespace_packages = ['danse.common'],
    package_dir = {"danse.common.plottools":os.path.join("src", "danse",
                                                         "common",
                                                         "plottools"),
                   "danse":os.path.join("src", "danse"),
                   "danse.common":os.path.join("src", "danse", "common")},
    packages = ["danse.common.plottools",
                "danse",
                "danse.common"],
    )

