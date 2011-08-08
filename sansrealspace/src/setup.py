"""
 Installation script for SANS models

  - To compile and install:
      python setup.py install
  - To create distribution:
      python setup.py bdist_wininst

"""
#TODO: this should be part of realSpaceModeling

from distutils.core import setup, Extension

setup(
    name="sans.realspace",
    version = "0.1",
    description = "Python module for SANS scattering models",
    url = "http://danse.us/trac/sans",
    
    # Use the pure python modules
    package_dir = {"sans.realspace":"realspace", "sans.realspace.test":"realspace/test"},
    
    packages = ["sans.realspace", "sans.realspace.test"]
    )
        