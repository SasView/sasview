"""
     Installation script for DANSE calculator perspective for SansView
"""

import os

    
from distutils.core import setup
from distutils.sysconfig import get_python_lib
from distutils.filelist import findall
new_path = os.path.join(get_python_lib(),"sans","perspectives","calculator","media")
path = "media"
data_files = []
for f in findall(path):
    if os.path.split(f)[0].count('.svn')==0:
        data_files.append((new_path, [f]))
setup(
    name="calculator",
    description="calculator perspective for SansView",
    package_dir={"sans.perspectives":"perspectives",
                   "sans.perspectives.calculator":"perspectives/calculator"},
    data_files=data_files,
    packages=["sans.perspectives",
                "sans.perspectives.calculator"],
    )

