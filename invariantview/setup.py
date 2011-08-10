"""
     Installation script for DANSE calculator perspective for SansView
"""
import os
import sys
if len(sys.argv) == 1:
    sys.argv.append('install')
from distutils.core import setup
setup(
    version = "0.9",
    name="invariant",
    description = "Invariant perspective for SansView",
    package_dir = {"sans":"src/sans",
                   "sans.perspectives":"src/sans/perspectives",
                   "sans.perspectives.invariant":"src/sans/perspectives/invariant",
                   "sans.perspectives.invariant.media":
                   "src/sans/perspectives/invariant/media"},
    package_data={'sans.perspectives.invariant.media': ['*']},
    packages = ["sans.perspectives",
                "sans",
                "sans.perspectives.invariant",
                "sans.perspectives.invariant.media"],
    )

