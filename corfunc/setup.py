"""
    Setup for Corfunc perspective
"""
from distutils.core import setup

setup(
    name="corfunc",
    version = "1.0.0",
    description = "Python module for corfunc",
    author = "CCP13",
    url = "http://www.ccp13.ac.uk/",

    # Use the pure python modules
    package_dir = {"sans.corfunc":"src/sans/corfunc"},
    packages = ["sans.corfunc", "src/sans"],
    )
