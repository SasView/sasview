"""
     Installation script for DANSE calculator perspective for SansView
"""
import os
from distutils.core import setup
setup(
    version = "0.9",
    name="invariant",
    description = "Invariant perspective for SansView",
    package_dir = {"sans.perspectives":"sans/perspectives",
                   "sans.perspectives.invariant":"sans/perspectives/invariant",
                   "sans.perspectives.invariant.media":
                   "sans/perspectives/invariant/media"},
    package_data={'sans.perspectives.invariant.media': ['*']},
    packages = ["sans.perspectives",
                "sans.perspectives.invariant",
                "sans.perspectives.invariant.media"],
    )

