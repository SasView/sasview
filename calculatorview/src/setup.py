"""
     Installation script for DANSE calculator perspective for SansView
"""

from distutils.core import setup

setup(
    name="calculator",
    version = "0.9",
    description="calculator perspective for SansView",
    package_dir={"sans.perspectives":"perspectives",
                 "sans.perspectives.calculator":"perspectives/calculator",
                 "sans.perspectives.calculator.media":"media"},
    package_data={'sans.perspectives.calculator.media': ['*']},
    packages=["sans.perspectives",
              "sans.perspectives.calculator",
              "sans.perspectives.calculator.media"],
    )

