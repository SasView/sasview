"""
    Installs the guiframe package
"""

    
from distutils.core import setup, Extension

from distutils.sysconfig import get_python_lib
import os, sys

package_dir = { "sans.guiframe":".",
                "sans.guiframe.local_perspectives":"local_perspectives",
                "sans.guiframe.local_perspectives.plotting":"local_perspectives/plotting"}

packages = ["sans.guiframe", 
            "sans.guiframe.local_perspectives",
            "sans.guiframe.local_perspectives.plotting"]

# Check whether the sans module exists,
# if not, make sure a default __init__ is created
if 'install' in sys.argv:
    try:
        lib_dir = get_python_lib()
        danse_init = os.path.join(lib_dir, 'sans', '__init__.py')
        if not os.path.isfile(danse_init):
            if not os.path.isdir("tmp_sans"):
                os.mkdir("tmp_sans")
            f = open("tmp_sans/__init__.py",'w')
            f.close()
            package_dir['sans'] = "tmp_sans"
            packages.append("sans")
    except:
        print "Couldn't create sans/__init__.py\n  %s" % sys.exc_value

setup(
    name="guiframe",
    version = "0.1",
    description = "Python module for SANS gui framework",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    
    package_dir = package_dir,

    packages = packages,
    
    package_data={"sans.guiframe": ['images/*']},
    )
        