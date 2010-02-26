"""
     Installation script for DANSE calculator perspective for SansView
"""

from distutils.core import setup

setup(
    name="invariant",
    description = "Invariant perspective for SansView",
    package_dir = {"sans.perspectives":"perspectives",
                   "sans.perspectives.invariant":"perspectives/invariant"},
    packages = ["sans.perspectives",
                "sans.perspectives.invariant"],
    )

