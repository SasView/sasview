"""
    Setup script to build a Mac app
"""
from setuptools import setup
import DataLoader.readers 
import os

#Data reader data files

RESOURCES_FILES = os.path.join(DataLoader.readers.get_data_path(),'defaults.xml')

# Locate libxml2 library
lib_locs = ['/usr/local/lib', '/usr/lib']
libxml_path = None
for item in lib_locs:
    libxml_path_test = '%s/libxml2.2.dylib' % item
    if os.path.isfile(libxml_path_test): 
        libxml_path = libxml_path_test
if libxml_path == None:
    raise RuntimeError, "Could not find libxml2 on the system"

APP = ['PrView.py']
DATA_FILES = ['images', 'test', 'plugins']
OPTIONS = {'argv_emulation': True,
           'packages': ['lxml'],
           'iconfile': 'images/ball.icns',
           'frameworks':[libxml_path],
           'resources': RESOURCES_FILES
           }

setup(
    app=APP,
    data_files=DATA_FILES,
    include_package_data= True,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
