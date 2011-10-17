"""
     Installation script for DANSE P(r) inversion perspective for SansView
"""

from distutils.core import setup

setup(
      version="1.0.0",
      name="inversionview",
      description="P(r) inversion perspective for SansView",
      package_dir={"sans":"src/sans",
                   "sans.perspectives":"src/sans/perspectives",
                   "sans.perspectives.pr":"src/sans/perspectives/pr"},
      packages=["sans.perspectives","sans",
                "sans.perspectives.pr"],
      package_data={"sans.perspectives.pr":['images/*']},
    )

