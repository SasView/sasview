"""
     Installation script for DANSE calculator perspective for SansView
"""
import os
from distutils.core import setup

setup(
    name="invariant",
    description = "Invariant perspective for SansView",
    package_dir = {"sans.perspectives":"perspectives",
                   "sans.perspectives.invariant":"perspectives/invariant",
                   "sans.perspectives.invariant.media":"media"},
    package_data={'sans.perspectives.invariant.media': ['*']},
    packages = ["sans.perspectives",
                "sans.perspectives.invariant",
                "sans.perspectives.invariant.media"],
    )

