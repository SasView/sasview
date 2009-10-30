#!/usr/bin/env python

#
# The setup to create a Windows executable.
# Inno Setup can then be used with the installer.iss file 
# in the top source directory to create an installer. 
#
# Setuptools clashes with py2exe 0.6.8 (and probably later too).
# For that reason, most of the code needs to have direct imports
# that are not going through pkg_resources. 
#
# Attention should be paid to dynamic imports. Data files can
# be added to the distribution directory for that purpose.
# See for example the 'images' directory below.

import os, sys
    
from distutils.core import setup
from distutils.filelist import findall
import matplotlib
import py2exe

manifest = """
   <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
   <assembly xmlns="urn:schemas-microsoft-com:asm.v1"
   manifestVersion="1.0">
   <assemblyIdentity
       version="0.64.1.0"
       processorArchitecture="x86"
       name="Controls"
       type="win32"
   />
   <description>SansView</description>
   <dependency>
       <dependentAssembly>
           <assemblyIdentity
               type="win32"
               name="Microsoft.Windows.Common-Controls"
               version="6.0.0.0"
               processorArchitecture="X86"
               publicKeyToken="6595b64144ccf1df"
               language="*"
           />
       </dependentAssembly>
   </dependency>
   </assembly>
  """

    
class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "0.9.1"
        self.company_name = "U Tennessee"
        self.copyright = "copyright 2009"
        self.name = "SansView"
        
#
# Adapted from http://www.py2exe.org/index.cgi/MatPlotLib
# to use the MatPlotLib.
#
matplotlibdatadir = matplotlib.get_data_path()
matplotlibdata = findall(matplotlibdatadir)
data_files = []
# Copying SLD data
import periodictable
import logging

data_files += periodictable.data_files()


for f in matplotlibdata:
    dirname = os.path.join('mpl-data', f[len(matplotlibdatadir)+1:])
    data_files.append((os.path.split(dirname)[0], [f]))

# Copy the settings file for the DataLoader file extension associations
import DataLoader.readers
f = os.path.join(DataLoader.readers.get_data_path(),'defaults.xml')
if os.path.isfile(f):
    data_files.append(('.', [f]))

# Copying the images directory to the distribution directory.
for f in findall('images'):
    if os.path.split(f)[0].count('.svn')==0:
        data_files.append((os.path.split(f)[0], [f]))

# Copying the HTML help docs
for f in findall('doc'):
    if os.path.split(f)[0].count('.svn')==0:
        data_files.append((os.path.split(f)[0], [f]))

# Copying the sample data user data
for f in findall('test'):
    if os.path.split(f)[0].count('.svn')==0:
        data_files.append((os.path.split(f)[0], [f]))
        
# Copying the sample data user data
for f in findall('plugins'):
    if os.path.split(f)[0].count('.svn')==0:
        data_files.append((os.path.split(f)[0], [f]))

    
#
# packages
#
packages = ['matplotlib', 'pytz','encodings']
includes = []
excludes = [] 

dll_excludes = [
    'libgdk_pixbuf-2.0-0.dll', 
    'libgobject-2.0-0.dll',
    'libgdk-win32-2.0-0.dll',
    ]

target_wx_client = Target(
    description = 'SansView',
    script = 'sansview.py',
    icon_resources = [(1, "images/ball.ico")],
    other_resources = [(24,1,manifest)],
    dest_base = "SansView"
    )



setup(
    windows=[target_wx_client],
    console=[],
    
    options={
        'py2exe': {
            'dll_excludes': dll_excludes,
            'packages' : packages,
            'includes':includes,
            'excludes':excludes,
            "compressed": 1,
            "optimize": 0,
            "bundle_files":2,
            },
    },
    data_files=data_files,
    
)


