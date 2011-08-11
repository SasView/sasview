"""
     Installation script for DANSE P(r) inversion perspective for SansView
"""
import os
from distutils.core import setup
currpath = os.path.split(os.getcwd())[0]

setup(
      version="0.9.1",
      name="inversionview",
      description="P(r) inversion perspective for SansView",
      package_dir={"sans":"src/sans",
                   "sans.perspectives":"src/sans/perspectives",
                   "sans.perspectives.pr":"src/sans/perspectives/pr"},
      packages=["sans.perspectives","sans",
                "sans.perspectives.pr"],
      package_data={"sans.perspectives.pr":['images/*']},
      #scripts= [os.path.join(currpath, "scripts", "PrView.py")]
    )

