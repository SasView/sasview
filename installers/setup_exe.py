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
from __future__ import print_function

import os
import sys
from glob import glob
import warnings
import shutil

from distutils.util import get_platform
from distutils.core import setup
from distutils.filelist import findall
from distutils.sysconfig import get_python_lib

#from idlelib.PyShell import warning_stream

# Need the installer dir on the python path to find helper modules
installer_dir = os.path.abspath(os.path.dirname(__file__))
if installer_dir != os.path.abspath(os.getcwd()):
    raise RuntimeError("Must run setup_exe from the installers directory")
sys.path.append(installer_dir)

# Need the installer dir on the python path to find helper modules
if os.path.abspath(os.path.dirname(__file__)) != os.path.abspath(os.getcwd()):
    raise RuntimeError("Must run setup_exe from the installers directory")
sys.path.append(installer_dir)

# put the build directory at the front of the path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
platform = '%s-%s'%(get_platform(), sys.version[:3])
doc_path = os.path.join(root, 'build', 'lib.'+platform, 'doc')
build_path = os.path.join(root, 'sasview-install', 'Lib', 'site-packages')
sys.path.insert(0, build_path)

from installer_generator import generate_installer

import matplotlib
try:
    import tinycc
except ImportError:
    warnings.warn("TinyCC package is not available and will not be included")
    tinycc = None

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
except Exception:
    print("Error processing extra python path needed to build SasView\n  %s" %
          sys.exc_value)

from sas import get_local_config
local_config = get_local_config()

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

# Remove the build folder
shutil.rmtree("build", ignore_errors=True)
# do the same for dist folder
shutil.rmtree("dist", ignore_errors=True)

is_64bits = sys.maxsize > 2**32
arch = "amd64" if is_64bits else "x86"
manifest = """
    <?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
      <assemblyIdentity
        version="5.0.0.0"
        processorArchitecture="%(arch)s"
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
            processorArchitecture="%(arch)s"
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
            processorArchitecture="%(arch)s"
            publicKeyToken="6595b64144ccf1df"
            language="*">
          </assemblyIdentity>
        </dependentAssembly>
      </dependency>
    </assembly>
    """%{'arch': arch}

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)
        # for the versioninfo resources
        self.version = local_config.__version__
        self.company_name = "SasView.org"
        self.copyright = "copyright 2009 - 2016"
        self.name = "SasView"

data_files = []

if tinycc:
    data_files += tinycc.data_files()

# Include data for supporting packages
import periodictable
data_files += periodictable.data_files()

#
# Adapted from http://www.py2exe.org/index.cgi/MatPlotLib
# to use the MatPlotLib.
#
mpl_dir = matplotlib.get_data_path()
for dirpath, dirnames, filenames in os.walk(mpl_dir):
    target_dir = os.path.join("mpl-data", os.path.relpath(dirpath, mpl_dir))
    source_files = [os.path.join(dirpath, f) for f in filenames]
    data_files.append((target_dir, source_files))

import sasmodels
data_files += sasmodels.data_files()

# precompile sas models into the sasview build path; doesn't matter too much
# where it is so long as it is a place that will get cleaned up afterwards.
import sasmodels.core
dll_path = os.path.join(build_path, 'compiled_models')
compiled_dlls = sasmodels.core.precompile_dlls(dll_path, dtype='double')

# include the compiled models as data; coordinate the target path for the
# data with installer_generator.py
data_files.append(('compiled_models', compiled_dlls))

# Data files for the different perspectives
from sas.sasgui.perspectives import fitting
data_files += fitting.data_files()

from sas.sasgui.perspectives import calculator
data_files += calculator.data_files()

from sas.sasgui.perspectives import invariant
data_files += invariant.data_files()

from sas.sasgui import guiframe
data_files += guiframe.data_files()

# Copy the config files
sasview_path = os.path.join('..', 'src', 'sas', 'sasview')
data_files.append(('.', [os.path.join(sasview_path, 'custom_config.py')]))
data_files.append(('config', [os.path.join(sasview_path, 'custom_config.py')]))
data_files.append(('.', [os.path.join(sasview_path, 'local_config.py')]))

# Copy the logging config
sas_path = os.path.join('..', 'src', 'sas')
data_files.append(('.', [os.path.join(sas_path, 'logging.ini')]))

if os.path.isfile("BUILD_NUMBER"):
    data_files.append(('.', ["BUILD_NUMBER"]))

# Copying the images directory to the distribution directory.
data_files.append(("images", findall(local_config.icon_path)))

# Copying the HTML help docs
data_files.append(("media", findall(local_config.media_path)))

# Copying the sample data user data
test_dir = local_config.test_path
for dirpath, dirnames, filenames in os.walk(test_dir):
    target_dir = os.path.join("test", os.path.relpath(dirpath, test_dir))
    source_files = [os.path.join(dirpath, f) for f in filenames]
    data_files.append((target_dir, source_files))

# See if the documentation has been built, and if so include it.
if os.path.exists(doc_path):
    for dirpath, dirnames, filenames in os.walk(doc_path):
        target_dir = os.path.join("doc", os.path.relpath(dirpath, doc_path))
        source_files = [os.path.join(dirpath, f) for f in filenames]
        data_files.append((target_dir, source_files))
else:
    raise Exception("You must first build the documentation before creating an installer.")

# Copying opencl include files
opencl_source = os.path.join(get_python_lib(), "pyopencl", "cl")
opencl_target = os.path.join("includes", "pyopencl")
data_files.append((opencl_target, findall(opencl_source)))

# Numerical libraries
python_root = os.path.dirname(os.path.abspath(sys.executable))
def dll_check(dll_path, dlls):
    dll_includes = [os.path.join(dll_path, dll+'.dll') for dll in dlls]
    return [dll for dll in dll_includes if os.path.exists(dll)]

# Check for ATLAS
numpy_path = os.path.join(python_root, 'lib', 'site-packages', 'numpy', 'core')
atlas_dlls = dll_check(numpy_path, ['numpy-atlas'])

# Check for MKL
mkl_path = os.path.join(python_root, 'Library', 'bin')
mkl_dlls = dll_check(mkl_path, ['mkl_core', 'mkl_def', 'libiomp5md'])

if mkl_dlls:
    data_files.append(('.', mkl_dlls))
if atlas_dlls:
    data_files.append(('.', atlas_dlls))

if is_64bits:
    msvcrtdll = glob(r"C:\Program Files\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\*.*")
else:
    msvcrtdll = glob(r"C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\redist\x86\Microsoft.VC90.CRT\*.*")
if msvcrtdll:
    # install the MSVC 9 runtime dll's into the application folder
    data_files.append(("Microsoft.VC90.CRT", msvcrtdll))

# NOTE:
#  need an empty __init__.py in site-packages/numpy/distutils/tests and site-packages/mpl_toolkits

# packages
#
packages = [
    'matplotlib', 'scipy', 'encodings', 'comtypes', 'h5py',
    'win32com', 'xhtml2pdf', 'bumps', 'sasmodels', 'sas',
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

# For the interactive interpreter SasViewCom make sure ipython is available
#packages.extend(['IPython', 'pyreadline', 'pyreadline.unicode_helper'])

# individual models
includes = ['site', 'lxml._elementpath', 'lxml.etree']

if tinycc:
    packages.append('tinycc')

# Exclude packages that are not needed but are often found on build systems
excludes = ['Tkinter', 'PyQt4', '_tkagg', 'sip', 'pytz', 'sympy']

dll_excludes = [
    # Various matplotlib backends we are not using
    'libgdk_pixbuf-2.0-0.dll', 'libgobject-2.0-0.dll', 'libgdk-win32-2.0-0.dll',
    'tcl84.dll', 'tk84.dll', 'QtGui4.dll', 'QtCore4.dll',
    # numpy 1.8 openmp bindings (still seems to use all the cores without them)
    # ... but we seem to need them when building from anaconda, so don't exclude ...
    #'libiomp5md.dll', 'libifcoremd.dll', 'libmmd.dll', 'svml_dispmd.dll','libifportMD.dll',
    'numpy-atlas.dll',
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
    description='SasView',
    script='sasview_gui.py',
    icon_resources=[(1, local_config.SetupIconFile_win)],
    other_resources=[(24, 1, manifest)],
    dest_base="SasView"
)

target_console_client = Target(
    description='SasView console',
    script='sasview_console.py',
    icon_resources=[(1, local_config.SetupIconFile_win)],
    other_resources=[(24, 1, manifest)],
    dest_base="SasViewCom"
)

#bundle_option = 3 if is_64bits else 2
bundle_option = 3
generate_installer()
#initialize category stuff
#from sas.sasgui.guiframe.CategoryInstaller import CategoryInstaller
#CategoryInstaller.check_install(s)

#import pprint; pprint.pprint(data_files); sys.exit()

import py2exe
setup(
    windows=[target_wx_client],
    console=[target_console_client],
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
