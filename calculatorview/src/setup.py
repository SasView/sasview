"""
     Installation script for DANSE calculator perspective for SansView
"""

from distutils.core import setup
import sys
if len(sys.argv) == 1:
    sys.argv.append('install')
setup(
    name="sans.calculatorview",
    version = "0.9",
    description="calculator perspective for SansView",
    package_dir={"sans.perspectives":"sans/perspectives",
                 "sans.perspectives.calculator":"sans/perspectives/calculator"},
    package_data={'sans.perspectives.calculator': ['images/*', 'media/*']},
    packages=["sans.perspectives",
              "sans.perspectives.calculator"],
    )

