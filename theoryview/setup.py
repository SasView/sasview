"""
     Installation script for DANSE calculator perspective for SansView
"""

from distutils.core import setup

setup(
    name="theory",
    description = "theory perspective for SansView",
    package_dir = {"sans.perspectives":"perspectives",
                   "sans.perspectives.theory":"perspectives/theory"},
    packages = ["sans.perspectives",
                "sans.perspectives.theory"],
    )

