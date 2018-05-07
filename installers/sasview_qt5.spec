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
datas = [('../src/sas/sasview/images', 'images')]

datas.append(('../src/sas/sasview/media','media'))
datas.append(('../src/sas/sasview/test','test'))
datas.append(('../src/sas/sasview/custom_config.py','.'))
datas.append(('../src/sas/sasview/local_config.py','.'))
datas.append(('../src/sas/sasview/wxcruft.py','.'))
datas.append(('../src/sas/logger_config.py','.'))

# pyinstaller gets mightily confused by upper/lower case,
# so some modules need to be copied explicitly to avoid
# messages like
# WARNING: Attempted to add Python module twice with different upper/lowercases
datas.append((os.path.join(PYTHON_LOC,'Lib','SocketServer.py'),'.'))
datas.append((os.path.join(PYTHON_LOC,'Lib','Queue.py'),'.'))

# TODO
# NEED BETTER WAY TO DEAL WITH THESE RELATIVE PATHS
datas.append((os.path.join('..', '..','sasmodels','sasmodels'),'sasmodels'))
datas.append((os.path.join('..', 'src','sas','sasgui','perspectives','fitting','plugin_models'),'plugin_models'))
datas.append((os.path.join(PYTHON_LOC,'Library','plugins','platforms'),'platforms'))
datas.append((os.path.join(PYTHON_LOC,'Lib','site-packages','zmq','libzmq.cp36-win_amd64.pyd'),'.'))

# These depend on whether we have MKL or Atlas numpy
if os.path.exists(os.path.join(LIBLOC, LIBPREFIX + 'mkl_core.' + LIBSUFFIX)):
    datas.append(add_binary(LIBPREFIX + 'mkl_avx2.' + LIBSUFFIX))
    datas.append(add_binary(LIBPREFIX + 'mkl_def.' + LIBSUFFIX))
elif os.path.exists(os.path.join(LIBLOC, LIBPREFIX + 'numpy-atlas.' + LIBSUFFIX)):
    datas.append(add_binary(LIBPREFIX + 'numpy-atlas.' + LIBSUFFIX))
else:
    raise Exception("No numerical library for numpy found.")

#import sas.sascalc.dataloader.readers
#f = os.path.join(sas.sascalc.dataloader.readers.get_data_path(), 'defaults.json')
#datas.append((f, '.'))

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

# Need to explicitly exclude sasmodels here!!
excludes.append('sasmodels')

# HIDDEN MODULES ############################################################
hiddenimports = [
 'PyQt5',
 'periodictable.core',
 'sasmodels.core',
 'pyopencl',
 'tinycc',
 'SocketServer',
 'logging',
 'logging.config',
 'ipykernel', 'ipykernel.datapub',
 'pygments', 'pygments.lexers','pygments.lexers.python',
 'pygments.styles','pygments.styles.default',
 'atexit', 'cython', 'sip', 'xhtml2pdf',
 'zmq', 'zmq.utils', 'zmq.utils.strtypes',
 'zmq.utils.jsonapi','zmq.utils.garbage',
 'zmq.backend.cython','zmq.backend.cffi',
 'site','lxml._elementpath','lxml.etree',
 'scipy._lib.messagestream',
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
          icon=os.path.join("../src/sas/sasview/images","ball.ico"),
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
        icon='../src/sas/sasview/images/ball.ico',
        bundle_identifier=None)

