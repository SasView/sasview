"""
    Setup script for the P(r) inversion module
"""
import sys, os

# Then build and install the modules
from distutils.core import setup, Extension

from numpy.distutils.misc_util import get_numpy_include_dirs
numpy_incl_path = os.path.join(get_numpy_include_dirs()[0], "numpy")
#numpy_incl = "Lib\site-packages\numpy\core\include\numpy"
#numpy_incl_path = os.path.join(sys.prefix, "Lib", "site-packages", "numpy", "core", "include", "numpy")
print "NUMPY", numpy_incl_path

# Build the module name
srcdir  = "c_extensions"

setup(
    name="pr_inversion",
    version = "0.9",
    description = "Python module inversion of the scattering intensity to P(r)",
    author = "University of Tennessee",
    url = "danse.chem.utk.edu",
    
    # Use the pure python modules
    package_dir = {"sans.pr.core":"c_extensions",
                   "sans.pr": "."},
    
    packages = ["sans.pr","sans.pr.core"],
    
    ext_modules = [ Extension("sans.pr.core.pr_inversion",
     sources = [
        srcdir+"/Cinvertor.c",
        srcdir+"/invertor.c",
            ],
         include_dirs=[numpy_incl_path]
     
     
     )])
        