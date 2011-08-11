"""
     Installation script for DANSE P(r) inversion perspective for SansView
"""
import os
from distutils.core import setup
setup(
    version = "0.9.1",
    name="fittingview",
    description = "Fitting module  for SansView",
    package_dir = {"sans":os.path.join("src", "sans"),
                   "sans.perspectives":os.path.join("src",
                                                    "sans", "perspectives"),
                   "sans.perspectives.pr":os.path.join("src",
                                                       "sans",
                                                       "perspectives",
                                                       "fitting")},
    package_data={'sans.perspectives.fitting': ['media/*']},
    packages = ["sans.perspectives", 'sans',
                "sans.perspectives.fitting"],
    )

