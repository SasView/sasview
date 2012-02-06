"""
     Installation script for DANSE P(r) inversion perspective for SansView
"""
import os

from distutils.core import setup
setup(
    version = "1.1.0",
    name="fittingview",
    description = "Fitting module  for SansView",
    package_dir = {"sans":os.path.join("src", "sans"),
                   "sans.perspectives":os.path.join("src",
                                                    "sans", "perspectives"),
                   "sans.perspectives.fitting":os.path.join("src",
                                                       "sans",
                                                       "perspectives",
                                                       "fitting"),
                   "sans.perspectives.fitting.plugin_models":os.path.join("src",
                                                       "sans",
                                                       "perspectives",
                                                       "fitting",
                                                       "plugin_models")},
    package_data={'sans.perspectives.fitting': ['media/*']},
    packages = ["sans.perspectives", 'sans',
                "sans.perspectives.fitting",
                "sans.perspectives.fitting.plugin_models"],
    )

