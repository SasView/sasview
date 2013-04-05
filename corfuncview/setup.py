"""
     Installation script for CCP13 CORFUNC perspective for SansView
"""
import os

from distutils.core import setup
setup(
    version = "1.1.0",
    name="corfuncview",
    description = "Corfunc perspective for SansView",
    package_dir = {"sans":os.path.join("src", "sans"),
                   "sans.perspectives":os.path.join("src", "sans",
                                                    "perspectives"),
                   "sans.perspectives.corfunc":os.path.join("src",
                                                            "sans",
                                                            "perspectives",
                                                            "corfunc"),
                   },
    package_data={'sans.perspectives.corfunc': [os.path.join("media",
                                                               '*')]},
    packages = ["sans.perspectives",
                "sans",
                "sans.perspectives.corfunc",],
    )

