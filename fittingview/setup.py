"""
     Installation script for DANSE P(r) inversion perspective for SansView
"""

from distutils.core import setup
setup(
    version = "0.9.1",
    name="fittingview",
    description = "Fitting module  for SansView",
    package_dir = {"sans.perspectives":"src/sans/perspectives",
                   "sans.perspectives.pr":"src/sans/perspectives/fitting"},
    packages = ["sans.perspectives", "src/sans",
                "sans.perspectives.fitting"],
    )

