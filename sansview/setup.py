"""
     Installation script for DANSE P(r) inversion perspective for SansView
"""

from distutils.core import setup

setup(
    version = "1.9",
    name="SansView",
    description = "SansView description",
    package_dir = {"sans.perspectives":"perspectives",
                   "sans.perspectives.fitting":"perspectives/fitting"},
    packages = ["sans.perspectives",
                "sans.perspectives.fitting"],
    )

