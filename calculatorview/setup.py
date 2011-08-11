"""
     Installation script for DANSE calculator perspective for SansView
"""
import os
from distutils.core import setup
cal_dir = os.path.join("src", "sans", "perspectives", "calculator")
setup(
    name="calculatorview",
    version = "0.9",
    description="calculator perspective for SansView",
    package_dir={"sans":"src/sans",
                 "sans.perspectives":"src/sans/perspectives",
                 "sans.perspectives.calculator":cal_dir},
    package_data={'sans.perspectives.calculator': ['images/*', 'media/*']},
    packages=["sans.perspectives", "sans",
              "sans.perspectives.calculator"],
    )

