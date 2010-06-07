"""
     Installation script for DANSE Fitting perspective for SansView
"""
import sys
if len(sys.argv) == 1:
    sys.argv.append('install')
from distutils.core import setup

setup(
    name="fitting",
    description = "Fitting perspective for SansView",
    package_dir = {"sans.perspectives":"perspectives",
                   "sans.perspectives.fitting":"perspectives/fitting"},
    packages = ["sans.perspectives",
                "sans.perspectives.fitting"],
    )

