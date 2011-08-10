"""
    Setup script for the P(r) inversion module
"""
import sys
import os

# Then build and install the modules
from distutils.core import setup, Extension
from numpy.distutils.misc_util import get_numpy_include_dirs
numpy_incl_path = os.path.join(get_numpy_include_dirs()[0], "numpy")
#numpy_incl = "Lib\site-packages\numpy\core\include\numpy"
#numpy_incl_path = os.path.join(sys.prefix, "Lib", "site-packages", "numpy", "core", "include", "numpy")
#print "NUMPY", numpy_incl_path

# Build the module name
srcdir  = os.path.join("src", "sans", "pr", "c_extensions")

setup(
    name="pr_inversion",
    version = "0.9",
    description = "Python module inversion of the scattering intensity to P(r)",
    author = "University of Tennessee",
    url = "danse.chem.utk.edu",
    
    # Use the pure python modules
    package_dir = {"sans":"src/sans",
                   "sans.pr.core":srcdir,
                   "sans.pr": os.path.join("src","sans", "pr")},
    
    packages = ["sans", "sans.pr","sans.pr.core"],
    
    ext_modules = [ Extension("sans.pr.core.pr_inversion",
     sources = [ os.path.join(srcdir, "Cinvertor.c"),
                os.path.join(srcdir, "invertor.c"),
            ],
         include_dirs=[numpy_incl_path]
     
     
     )])
        