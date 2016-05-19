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

import os
import sys

# put the build directory at the front of the path
if os.path.abspath(os.path.dirname(__file__)) != os.path.abspath(os.getcwd()):
    raise RuntimeError("Must run setup_exe from the sasview directory")
from distutils.util import get_platform
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
platform = '%s-%s'%(get_platform(), sys.version[:3])
build_path = os.path.join(root, 'build', 'lib.'+platform)
sys.path.insert(0, build_path)

import local_config

if len(sys.argv) == 1:
    sys.argv.append('py2exe')
# When using the SasView build script, we need to be able to pass
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
    print "Error processing extra python path needed to build SasView\n  %s" % \
                sys.exc_value

from distutils.core import setup
from distutils.filelist import findall
import matplotlib

# Solution taken from here: http://www.py2exe.org/index.cgi/win32com.shell
# ModuleFinder can't handle runtime changes to __path__, but win32com uses them
win32_folder = "win32comext"
try:
    # py2exe 0.6.4 introduced a replacement modulefinder.
    # This means we have to add package paths there, not to the built-in
    # one.  If this new modulefinder gets integrated into Python, then
    # we might be able to revert this some day.
    # if this doesn't work, try import modulefinder
    try:
        import py2exe.mf as modulefinder
    except ImportError:
        import modulefinder
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath(win32_folder, p)
    for extra in ["win32com.shell", "win32com.adsi", "win32com.axcontrol",
                    "win32com.axscript", "win32com.bits", "win32com.ifilter",
                    "win32com.internet", "win32com.mapi", "win32com.propsys",
                    "win32com.taskscheduler"]:
        
            __import__(extra)
            m = sys.modules[extra]
            for p in m.__path__[1:]:
                modulefinder.AddPackagePath(extra, p)

except ImportError:
    # no build path setup, no worries.
    pass

import py2exe
import shutil
# Remove the build folder
shutil.rmtree("build", ignore_errors=True)
# do the same for dist folder
shutil.rmtree("dist", ignore_errors=True)

if sys.version_info < (2, 6):
    is_64bits = False 
    origIsSystemDLL = py2exe.build_exe.isSystemDLL
    def isSystemDLL(pathname):
            if os.path.basename(pathname).lower() in ("msvcp71.dll", "comctl32.dll"):
                    return 0
            return origIsSystemDLL(pathname)
    py2exe.build_exe.isSystemDLL = isSystemDLL
else:
    is_64bits = sys.maxsize > 2**32

if is_64bits and sys.version_info >= (2, 6):
    manifest = """
       <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
       <assembly xmlns="urn:schemas-microsoft-com:asm.v1"
       manifestVersion="1.0">
       <assemblyIdentity
           version="0.64.1.0"
           processorArchitecture="amd64"
           name="Controls"
           type="win32"
       />
       <description>SasView</description>
       <dependency>
           <dependentAssembly>
               <assemblyIdentity
                   type="win32"
                   name="Microsoft.Windows.Common-Controls"
                   version="6.0.0.0"
                   processorArchitecture="amd64"
                   publicKeyToken="6595b64144ccf1df"
                   language="*"
               />
           </dependentAssembly>
       </dependency>
       </assembly>
      """
else:
    manifest_for_python26 = """
        <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
        <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
          <assemblyIdentity
            version="5.0.0.0"
            processorArchitecture="x86"
            name="SasView"
            type="win32">
          </assemblyIdentity>
          <description>SasView</description>
          <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
            <security>
              <requestedPrivileges>
                <requestedExecutionLevel
                  level="asInvoker"
                  uiAccess="false">
                </requestedExecutionLevel>
              </requestedPrivileges>
            </security>
          </trustInfo>
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
          <dependency>
            <dependentAssembly>
              <assemblyIdentity
                type="win32"
                name="Microsoft.Windows.Common-Controls"
                version="6.0.0.0"
                processorArchitecture="x86"
                publicKeyToken="6595b64144ccf1df"
                language="*">
              </assemblyIdentity>
            </dependentAssembly>
          </dependency>
        </assembly>
        """
    manifest_for_python25 = """
       <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
       <assembly xmlns="urn:schemas-microsoft-com:asm.v1"
       manifestVersion="1.0">
       <assemblyIdentity
           version="0.64.1.0"
           processorArchitecture="x86"
           name="Controls"
           type="win32"
       />
       <description>SasView</description>
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

# Select the appropriate manifest to use.
py26MSdll_x86 = None
if sys.version_info >= (3, 0) or sys.version_info < (2, 6):
    print "*** This script only works with Python 2.6 or 2.7."
    sys.exit()
elif sys.version_info >= (2, 6):
    manifest = manifest_for_python26
    from glob import glob
    py26MSdll = glob(r"C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\*.*")
    try:
        py26MSdll_x86 = glob(r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\*.*")
    except:
        pass


class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = local_config.__version__
        self.company_name = "SasView.org"
        self.copyright = "copyright 2009 - 2013"
        self.name = "SasView"
        
#
# Adapted from http://www.py2exe.org/index.cgi/MatPlotLib
# to use the MatPlotLib.
#
path = os.getcwd()

media_dir = os.path.join(path, "media")
images_dir = os.path.join(path, "images")
test_dir = os.path.join(path, "test")
test_1d_dir = os.path.join(path, "test\\1d_data")
test_2d_dir = os.path.join(path, "test\\2d_data")
test_save_dir = os.path.join(path, "test\\save_states")
test_upcoming_dir = os.path.join(path, "test\\upcoming_formats")

matplotlibdatadir = matplotlib.get_data_path()
matplotlibdata = findall(matplotlibdatadir)
data_files = []
# Copying SLD data
import periodictable
import logging
data_files += periodictable.data_files()

import sas.sasgui.perspectives.fitting as fitting
data_files += fitting.data_files()

import sas.sasgui.perspectives.calculator as calculator
data_files += calculator.data_files()

import sas.sasgui.perspectives.invariant as invariant
data_files += invariant.data_files()

import sas.sasgui.guiframe as guiframe
data_files += guiframe.data_files()

# precompile sas models into the sasview build path; doesn't matter too much
# where it is so long as it is a place that will get cleaned up afterwards.
import sasmodels.core
dll_path = os.path.join(build_path, 'compiled_models')
compiled_dlls = sasmodels.core.precompile_dlls(dll_path, dtype='double')

# include the compiled models as data; coordinate the target path for the
# data with installer_generator.py
data_files.append(('compiled_models', compiled_dlls))

import sasmodels
data_files += sasmodels.data_files()

for f in matplotlibdata:
    dirname = os.path.join('mpl-data', f[len(matplotlibdatadir)+1:])
    data_files.append((os.path.split(dirname)[0], [f]))

# Copy the settings file for the sas.dataloader file extension associations
import sas.sascalc.dataloader.readers
f = os.path.join(sas.sascalc.dataloader.readers.get_data_path(), 'defaults.json')
if os.path.isfile(f):
    data_files.append(('.', [f]))
f = 'custom_config.py'
if os.path.isfile(f):
    data_files.append(('.', [f]))
    data_files.append(('config', [f]))
f = 'local_config.py'
if os.path.isfile(f):
    data_files.append(('.', [f]))

f = 'default_categories.json'
if os.path.isfile(f):
    data_files.append(('.', [f]))
    
if os.path.isfile("BUILD_NUMBER"):
    data_files.append(('.', ["BUILD_NUMBER"]))

# Copying the images directory to the distribution directory.
for f in findall(images_dir):
    if not ".svn" in f:
        data_files.append(("images", [f]))

# Copying the HTML help docs
for f in findall(media_dir):
    if not ".svn" in f:
        data_files.append(("media", [f]))

# Copying the sample data user data
for f in findall(test_1d_dir):
    if not ".svn" in f:
        data_files.append(("test\\1d_data", [f]))

# Copying the sample data user data
for f in findall(test_2d_dir):
    if not ".svn" in f:
        data_files.append(("test\\2d_data", [f]))

# Copying the sample data user data
for f in findall(test_save_dir):
    if not ".svn" in f:
        data_files.append(("test\\save_states", [f]))

# Copying the sample data user data
for f in findall(test_upcoming_dir):
    if not ".svn" in f:
        data_files.append(("test\\upcoming_formats", [f]))


# See if the documentation has been built, and if so include it.
doc_path = os.path.join(build_path, "doc")
if os.path.exists(doc_path):
    for dirpath, dirnames, filenames in os.walk(doc_path):
        for filename in filenames:
            sub_dir = os.path.join("doc", os.path.relpath(dirpath, doc_path))
            data_files.append((sub_dir, [os.path.join(dirpath, filename)]))
else:
    raise Exception("You must first build the documentation before creating an installer.")

if py26MSdll is not None:
    # install the MSVC 9 runtime dll's into the application folder
    data_files.append(("Microsoft.VC90.CRT", py26MSdll))
if py26MSdll_x86 is not None:
    # install the MSVC 9 runtime dll's into the application folder
    data_files.append(("Microsoft.VC90.CRT", py26MSdll_x86))

# NOTE:
#  need an empty __init__.py in site-packages/numpy/distutils/tests and site-packages/mpl_toolkits

# packages
#
packages = [
    'matplotlib', 'scipy', 'encodings', 'comtypes',
    'win32com', 'xhtml2pdf', 'bumps','sasmodels', 'sas',
    ]
packages.extend([
    'reportlab',
    'reportlab.graphics.charts',
    'reportlab.graphics.samples',
    'reportlab.graphics.widgets',
    'reportlab.graphics.barcode',
    'reportlab.graphics',
    'reportlab.lib',
    'reportlab.pdfbase',
    'reportlab.pdfgen',
    'reportlab.platypus',
    ])
packages.append('periodictable.core') # not found automatically
#packages.append('IPython')
includes = ['site', 'lxml._elementpath', 'lxml.etree']

# Exclude packages that are not needed but are often found on build systems
excludes = ['Tkinter', 'PyQt4', '_tkagg', 'sip', 'pytz']


dll_excludes = [
    # Various matplotlib backends we are not using
    'libgdk_pixbuf-2.0-0.dll', 'libgobject-2.0-0.dll', 'libgdk-win32-2.0-0.dll',
    'tcl84.dll', 'tk84.dll', 'QtGui4.dll', 'QtCore4.dll',
    # numpy 1.8 openmp bindings (still seems to use all the cores without them)
    'libiomp5md.dll', 'libifcoremd.dll', 'libmmd.dll', 'svml_dispmd.dll','libifportMD.dll',
    # microsoft C runtime (not allowed to ship with the app; need to ship vcredist
    'msvcp90.dll',
    # 32-bit windows console piping
    'w9xpopen.exe',
    # accidental links to msys/cygwin binaries; shouldn't be needed
    'cygwin1.dll',
    # no need to distribute OpenCL.dll - users should have their own copy
    'OpenCL.dll'
    ]

target_wx_client = Target(
    description = 'SasView',
    script = 'sasview.py',
    icon_resources = [(1, os.path.join(images_dir, "ball.ico"))],
    other_resources = [(24, 1, manifest)],
    dest_base = "SasView"
    )

bundle_option = 2
if is_64bits:
    bundle_option = 3
import installer_generator as gen
gen.generate_installer()
#initialize category stuff
#from sas.sasgui.guiframe.CategoryInstaller import CategoryInstaller
#CategoryInstaller.check_install(s)

setup(
    windows=[target_wx_client],
    console=[],
    options={
        'py2exe': {
            'dll_excludes': dll_excludes,
            'packages': packages,
            'includes': includes,
            'excludes': excludes,
            "compressed": 1,
            "optimize": 0,
            "bundle_files": bundle_option,
            },
    },
    data_files=data_files,
)
