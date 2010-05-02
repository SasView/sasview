"""
     Installation script for DANSE calculator perspective for SansView
"""

import os
  
from distutils.core import setup
from distutils.sysconfig import get_python_lib
from distutils.filelist import findall

setup(
    name="calculator",
    version = "0.1",
    description="calculator perspective for SansView",
    package_dir={"sans.perspectives":"perspectives",
                 "sans.perspectives.calculator":"perspectives/calculator",
                 "sans.perspectives.calculator.media":"media"},
    package_data={'sans.perspectives.calculator.media': ['*']},
    packages=["sans.perspectives",
              "sans.perspectives.calculator",
              "sans.perspectives.calculator.media"],
    )

