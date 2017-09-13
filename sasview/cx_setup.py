import os
import sys
import scipy
import matplotlib
import cython

import zmq.libzmq
import periodictable
import sasmodels
import sasmodels.core

from cx_Freeze import setup
from cx_Freeze import Executable
from distutils.filelist import findall
from distutils.sysconfig import get_python_lib
from distutils.filelist import findall
from distutils.util import get_platform

try:
    import tinycc
except ImportError:
    warnings.warn("TinyCC package is not available and will not be included")
    tinycc = None

# Full path to sasview/build/lib.<platform>-2.7
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
platform = '%s-%s'%(get_platform(), sys.version[:3])
build_path = os.path.join(root, 'build', 'lib.'+platform)
sys.path.insert(0, build_path)
python_root = os.path.dirname(os.path.abspath(sys.executable))


# Excluded packages
excl = ['collections.sys', 'collections._weakref', 'Tkinter']

# Explicityl included modules
incl = [
'pygments', 'pygments.lexers','pygments.lexers.python',
'pygments.styles','pygments.styles.default',
'ipykernel', 'ipykernel.datapub',
'atexit', 'cython', 'sip', 'xhtml2pdf',
'zmq', 'zmq.utils', 'zmq.utils.strtypes',
'zmq.utils.jsonapi','zmq.utils.garbage',
'zmq.backend.cython','zmq.backend.cffi',
'site','lxml._elementpath','lxml.etree',
]

# Extra packages
packs = [
'periodictable.core',
'matplotlib',
'encodings',
'comtypes',
'bumps',
'sasmodels',
'win32com',
]

if tinycc:
    packs.append('tinycc')


# Holder for extra files
data_files = []

data_files.append(zmq.libzmq.__file__)
data_files.append("local_config.py")
data_files.append("custom_config.py")
data_files.append("logging.ini")
data_files.append("media/")
data_files.append("images/")
data_files.append("test/")
data_files.append("plugin_models/")
data_files.append("compiled_models/")

def append_data(tups):
    # Convert py2exe tuple into cx_freeze tuple
    for tup in tups:
      target = tup[0]
      files = tup[1]
      for file in files:
         basename = os.path.basename(file)
         t = os.path.join(target, basename)
         data_files.append((file, t))

# Documents
doc_source = os.path.join(build_path, 'doc/')
data_files.append((doc_source, 'doc/'))

# OPENCL
site_loc = get_python_lib()
opencl_include_dir = os.path.join(site_loc, "pyopencl", "cl")
for f in findall(opencl_include_dir):
    target = os.path.join("includes", "pyopencl", os.path.basename(f))
    data_files.append((f, target))


append_data(periodictable.data_files())
append_data(sasmodels.data_files())
if tinycc:
    append_data(tinycc.data_files())

# MATPLOTLIB
matplotlibdatadir = matplotlib.get_data_path()
matplotlibdata = findall(matplotlibdatadir)
for f in matplotlibdata:
    dirname = os.path.join('mpl-data', f[len(matplotlibdatadir)+1:])
    target = os.path.join(dirname, os.path.basename(f))
    data_files.append((f, dirname))

# Numerical libraries
def dll_check(dll_path, dlls):
    dll_includes = [os.path.join(dll_path, dll+'.dll') for dll in dlls]
    return [dll for dll in dll_includes if os.path.exists(dll)]

# Check for ATLAS
dll_path = os.path.join(python_root, 'lib', 'site-packages', 'numpy', 'core')
dlls = ['numpy-atlas']
atlas_dlls = dll_check(dll_path, dlls)

# Check for MKL
dll_path = os.path.join(python_root, 'Library', 'bin')
dlls = ['mkl_core', 'mkl_def', 'libiomp5md', 'libmmd',
        'libmmdd', 'libiomp5md', 'libifcoremd', 'libifcoremdd']
mkl_dlls = dll_check(dll_path, dlls)

to_include = mkl_dlls
if atlas_dlls:
    to_include = atlas_dlls

for library in to_include:
    target = os.path.basename(library)
    data_files.append((library, target))


# Precompile models and add them
dll_path = os.path.join(build_path, 'compiled_models')
#compiled_dlls = sasmodels.core.precompile_dlls(dll_path, dtype='double')
#for library in compiled_dlls:
#    target = os.path.join('compiled_models', os.path.basename(library))
#    data_files.append((library, target))

# Extra logic for scipy
scipy_path = os.path.dirname(scipy.__file__)
data_files.append(scipy_path)


buildOptions = dict(packages = packs, excludes = excl, includes = incl,
                    include_files = data_files)


base = 'Win32GUI' if sys.platform=='win32' else None

icon = os.path.join('images','ball.ico')

executables = [
    Executable('sasview.py', 
	       icon=icon,
	       base=base)
]

setup(
    name='sasview',
    version = '5.0',
    description = 'SasviewQt Program',
    options = dict(build_exe = buildOptions),
    executables = executables
)


