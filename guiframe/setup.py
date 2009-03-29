"""
    Installs the guiframe package
"""
import sys

if len(sys.argv) == 1:
    sys.argv.append('install')

from distutils.core import setup, Extension

setup(
    name="guiframe",
    version = "0.1",
    description = "Python module for SANS gui framework",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    
    package_dir = { "sans.guiframe":".",
                    "sans.guiframe.local_perspectives":"local_perspectives",
                    "sans.guiframe.local_perspectives.plotting":"local_perspectives/plotting"},
    
    packages = ["sans.guiframe", 
                "sans.guiframe.local_perspectives",
                "sans.guiframe.local_perspectives.plotting"],
    
    package_data={"sans.guiframe": ['images/*']},
    )
        