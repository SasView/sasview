"""
     Installation script for DANSE calculator perspective for SansView
"""

from distutils.core import setup

setup(
    name="calculator",
    description = "P(r) inversion perspective for SansView",
    package_dir = {"sans.perspectives":"perspectives",
                   "sans.perspectives.calculator":"perspectives/calculator"},
    packages = ["sans.perspectives",
                "sans.perspectives.calculator"],
    )

