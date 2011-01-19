"""
     Installation script for DANSE P(r) inversion perspective for SansView
"""
import sys
if len(sys.argv) == 1:
    sys.argv.append('install')
from distutils.core import setup

setup(
    name="SansView",
    description = "SansView description",
    package_dir = {"sans.perspectives":"perspectives",
                   "sans.perspectives.fitting":"perspectives/fitting"},
    packages = ["sans.perspectives",
                "sans.perspectives.fitting"],
    )

