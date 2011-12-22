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
if len(sys.argv) == 1:
    sys.argv.append('py2exe')
# When using the SansView build script, we need to be able to pass
# an extra path to be added to the python path. The extra arguments
# should be removed from the list so that the setup processing doesn't
# fail.
try:
    if sys.argv.count('--extrapath'):
        path_flag_idx = sys.argv.index('--extrapath')
        extra_path = sys.argv[path_flag_idx+1]
        sys.path.insert(0, extra_path)
        del sys.argv[path_flag_idx+1]
        sys.argv.remove('--extrapath')
except:
    print "Error processing extra python path needed to build SansView\n  %s" % sys.exc_value

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
             name="Microsoft.VC90.CRT"
           version="9.0.21022.8"
            processorArchitecture="x86"
            publicKeyToken="1fc8b3b9a1e18e3b">
      </assemblyIdentity>
    </dependentAssembly>
   </dependency>
   </assembly>
  """

    
class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = "1.0"
        self.company_name = "U Tennessee"
        self.copyright = "copyright 2009"
        self.name = "SansViewTool"
        
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

import sans.perspectives.calculator as calculator
data_files += calculator.data_files()

for f in matplotlibdata:
    dirname = os.path.join('mpl-data', f[len(matplotlibdatadir)+1:])
    data_files.append((os.path.split(dirname)[0], [f]))

# Copying the images directory to the distribution directory.
import sans.perspectives.calculator as cal
path = cal.get_data_path('images')
for f in findall(path):
    if os.path.split(f)[0].count('.svn')==0:
        data_files.append(('images', [f]))
import sans.guiframe as guiframe
data_files += guiframe.data_files()
# Copy the settings file for the DataLoader file extension associations
import sans.dataloader.readers
f = os.path.join(sans.dataloader.readers.get_data_path(),'defaults.xml')
if os.path.isfile(f):
    data_files.append(('.', [f]))
f = 'custom_config.py'
if os.path.isfile(f):
    data_files.append(('.', [f]))
f = 'local_config.py'
if os.path.isfile(f):
    data_files.append(('.', [f]))
# Copying the HTML help docs
path = cal.get_data_path('media')
for f in findall(path):
    if os.path.split(f)[0].count('.svn')==0:
        data_files.append((os.path.split(f)[0], [f]))

from glob import glob
py26MSdll = glob(r"C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\*.*")
# install the MSVC 9 runtime dll's into the application folder
#data_files += [("", py26MSdll),]
data_files.append(("Microsoft.VC90.CRT", py26MSdll))
#                        ("lib\Microsoft.VC90.CRT", py26MSdll)]
#sys.path.append("Microsoft.VC90.CRT")

mfcdir = "C:\Python27\Lib\site-packages\pythonwin"
mfcfiles = [os.path.join(mfcdir, i) for i in ["mfc90.dll", "mfc90u.dll", "mfcm90.dll", "mfcm90u.dll", "Microsoft.VC90.MFC.manifest"]]
data_files.append(("Microsoft.VC90.MFC", mfcfiles))

    
#
# packages
#
packages = ['matplotlib', 'pytz','encodings', 'scipy']
includes = ['site']

excludes = ['Tkinter', 'PyQt4', '_ssl', '_tkagg']

dll_excludes = ['libgdk_pixbuf-2.0-0.dll',
                'libgobject-2.0-0.dll',
                'libgdk-win32-2.0-0.dll',
                'tcl84.dll',
                'tk84.dll',
                'QtGui4.dll',
                'QtCore4.dll',
                'w9xpopen.exe',
                'cygwin1.dll']

target_wx_client = Target(
    description = 'SansViewTool',
    script = 'sansviewtool.py',
    #icon_resources = [(1, "images/ball.ico")],
    other_resources = [(24,1,manifest)],
    dest_base = "SansViewTool"
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


