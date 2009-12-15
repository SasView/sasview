"""
     Installation script for DANSE calculator perspective for SansView
"""

from distutils.core import setup

setup(
    name="calculator",
    description = "calculator perspective for SansView",
    package_dir = {"sans.perspectives":"perspectives",
                   "sans.perspectives.calculator":"perspectives/calculator"},
    packages = ["sans.perspectives",
                "sans.perspectives.calculator"],
    )

