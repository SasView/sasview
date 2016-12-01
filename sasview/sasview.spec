# -*- mode: python -*-
# Modifiable location
import sys
import os
import platform

import warnings
from distutils.filelist import findall

PYTHON_LOC = sys.exec_prefix
# Portability settings
if os.name == 'posix':
    LIBPREFIX='lib'
    LIBSUFFIX='so'
    LIBLOC = os.path.join(PYTHON_LOC,'lib')
    # Darwin needs UPX=False, Linux actually builds with both...
    if platform.system() == 'Darwin':
        UPX=False
    else:
        UPX=True
else:
    LIBPREFIX=''
    LIBSUFFIX='dll'
    LIBLOC = os.path.join(PYTHON_LOC,'Library','bin')
    UPX=True

SCRIPT_TO_SOURCE = 'sasview.py'

# Warning! pyinstaller/py2exe etc. don't have the __file__ attribute
# WORK_DIR = os.path.dirname(os.path.realpath(__file__))
WORK_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

#### LOCAL METHODS
def add_data(data):
    for component in data:
        target = component[0]
        for filename in component[1]:
           datas.append((filename, target))

def add_binary(binary):
    return (os.path.join(LIBLOC,binary),'.')

# ADDITIONAL DATA ############################################################
datas = [('images', 'images')]

datas.append(('media','media'))
datas.append(('test','test'))
datas.append(('custom_config.py','.'))
datas.append(('local_config.py','.'))
datas.append(('wxcruft.py','.'))
datas.append(('welcome_panel.py','.'))

# TODO
# NEED BETTER WAY TO DEAL WITH THESE RELATIVE PATHS
datas.append((os.path.join('..','..','sasmodels','sasmodels'),'sasmodels'))
datas.append((os.path.join('..','src','sas','sasgui','perspectives','fitting','plugin_models'),'plugin_models'))

# precompile sas models into the sasview build path; doesn't matter too much
# where it is so long as it is a place that will get cleaned up afterwards.
import sasmodels.core
dll_path = 'compiled_models'
if not (os.path.exists(dll_path)):
    os.mkdir(dll_path)
dll_path2 = os.path.join(dll_path, dll_path)
if not (os.path.exists(dll_path2)):
    os.mkdir(dll_path2)

compiled_dlls = sasmodels.core.precompile_dlls(dll_path, dtype='double')

# include the compiled models as data; coordinate the target path for the
# data with installer_generator.py
datas.append((os.path.join('compiled_models','compiled_models'),'compiled_models'))

# These depend on whether we have MKL or Atlas numpy
if os.path.exists(os.path.join(LIBLOC, LIBPREFIX + 'mkl_core.' + LIBSUFFIX)):
    datas.append(add_binary(LIBPREFIX + 'mkl_avx2.' + LIBSUFFIX))
    datas.append(add_binary(LIBPREFIX + 'mkl_def.' + LIBSUFFIX))
elif os.path.exists(os.path.join(LIBLOC, LIBPREFIX + 'numpy-atlas.' + LIBSUFFIX)):
    datas.append(add_binary(LIBPREFIX + 'numpy-atlas.' + LIBSUFFIX))
else:
    raise Exception("No numerical library for numpy found.")

import sas.sascalc.dataloader.readers
f = os.path.join(sas.sascalc.dataloader.readers.get_data_path(), 'defaults.json')
datas.append((f, '.'))

# Add a custom pyopencl hook, as described in
# https://github.com/pyinstaller/pyinstaller/issues/2130
from PyInstaller.utils.hooks import copy_metadata
datas.append(copy_metadata('pyopencl')[0])

import sasmodels
add_data(sasmodels.data_files())

try:
    import tinycc
    add_data(tinycc.data_files())
except ImportError:
    warnings.warn("TinyCC package is not available and will not be included")

import periodictable
add_data(periodictable.data_files())

import matplotlib
matplotlibdatadir = matplotlib.get_data_path()
matplotlibdata = findall(matplotlibdatadir)
for f in matplotlibdata:
    dirname = os.path.join('mpl-data', f[len(matplotlibdatadir)+1:])
    datas.append((f, os.path.split(dirname)[0]))

binaries = []

# EXCLUDED FILES ############################################################
# Spelled out to enable easier editing
excludes = []
excludes.append('libzmq')
excludes.append('IPython')
excludes.append('PyQt4')
excludes.append('PySide')
excludes.append('Qt4')
excludes.append('Tkinter')
excludes.append('tk')
excludes.append('tcl')
# Seems we cannot build on Linux without bundling sip
if not platform.system() == 'Linux':
    excludes.append('sip')
excludes.append('sympy')
excludes.append('pytz')
excludes.append('sklearn')
excludes.append('zmq')

# Need to explicitly exclude sasmodels here!!
excludes.append('sasmodels')

# HIDDEN MODULES ############################################################
hiddenimports = [
 'periodictable.core',
 'sasmodels.core',
 'pyopencl',
 'tinycc'
]

a = Analysis([SCRIPT_TO_SOURCE],
             pathex=[WORK_DIR],
             binaries=binaries,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=excludes,
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=None)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='sasview',
          debug=False,
          upx=UPX,
          icon=os.path.join("images","ball.ico"),
          version="version.txt",
          console=False )

# COLLECT creates a directory instead of a single file.
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=UPX,
               name='sasview')

if platform.system() == 'Darwin':
    app = BUNDLE(exe,
        name='SasView.app',
        icon='images/ball.ico',
        bundle_identifier=None)

