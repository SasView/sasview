"""
     Installation script for DANSE P(r) inversion perspective for SansView
"""
import os
from distutils.core import setup
setup(
      version="0.9.1",
      name="prview",
      description="P(r) inversion perspective for SansView",
      package_dir={"sans.perspectives":"sans/perspectives",
                   "sans.perspectives.pr":"sans/perspectives/pr"},
      packages=["sans.perspectives","sans",
                "sans.perspectives.pr"],
      package_data={"sans.perspectives.pr":['images/*']},
      scripts= [os.path.join("bin", "PrView.py")],
    )

