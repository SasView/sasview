"""
 Installation script for SAS models
"""

import sys
import os
import platform
from numpy.distutils.misc_util import get_numpy_include_dirs
numpy_incl_path = os.path.join(get_numpy_include_dirs()[0], "numpy")
   
# Then build and install the modules
from distutils.core import Extension, setup
from distutils.command.build_ext import build_ext

# Manage version number ######################################
sys.path.append(os.path.join("src", "sas"))
import models
VERSION = models.__version__
print "Building models v%s" % VERSION
##############################################################

# Options to enable OpenMP
copt =  {'msvc': ['/openmp'],
         'mingw32' : ['-fopenmp'],
         'unix' : ['-fopenmp']}
lopt =  {'msvc': ['/MANIFEST'],
         'mingw32' : ['-fopenmp'],
         'unix' : ['-lgomp']}

# Options for non-openmp builds. MSVC always needs MANIFEST
if sys.argv[-1] == "-nomp":
    copt = {}
    lopt = {'msvc': ['/MANIFEST']}

class build_ext_subclass( build_ext ):
    def build_extensions(self):
        # Get 64-bitness
        if sys.version_info >= (2, 6):
            is_64bits = sys.maxsize > 2**32
        else:
            # 'sys.maxsize' and 64bit: Not supported for python2.5
            is_64bits = False
        c = self.compiler.compiler_type
        print "Compiling with %s (64bit=%s)" % (c, str(is_64bits))
        
        if not (sys.platform=='darwin' and not is_64bits):
            if copt.has_key(c):
               for e in self.extensions:
                   e.extra_compile_args = copt[ c ]
            if lopt.has_key(c):
                for e in self.extensions:
                    e.extra_link_args = lopt[ c ]
                    
        build_ext.build_extensions(self)

# Build the module name
includedir  = "include"
igordir = os.path.join("src", "libigor")
c_model_dir = os.path.join("src", "c_models")
smear_dir  = os.path.join("src", "c_smearer")
wrapper_dir  = os.path.join("src", "python_wrapper", "generated")
if not os.path.isdir(wrapper_dir):
    os.makedirs(wrapper_dir)

sys.path.append(os.path.join("src", "python_wrapper"))
from wrapping import generate_wrappers
generate_wrappers(header_dir=includedir, 
                  output_dir=os.path.join("src", "sas", "models"), 
                  c_wrapper_dir=wrapper_dir)

IGNORED_FILES = [".svn"]
if not os.name=='nt':
    IGNORED_FILES.extend(["gamma_win.c","winFuncs.c"])

EXTENSIONS = [".c", ".cpp"]

def append_file(file_list, dir_path):
    """
    Add sources file to sources
    """
    for f in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, f)):
            _, ext = os.path.splitext(f)
            if ext.lower() in EXTENSIONS and f not in IGNORED_FILES:
                file_list.append(os.path.join(dir_path, f)) 
        elif os.path.isdir(os.path.join(dir_path, f)) and \
                not f.startswith("."):
            sub_dir = os.path.join(dir_path, f)
            for new_f in os.listdir(sub_dir):
                if os.path.isfile(os.path.join(sub_dir, new_f)):
                    _, ext = os.path.splitext(new_f)
                    if ext.lower() in EXTENSIONS and\
                         new_f not in IGNORED_FILES:
                        file_list.append(os.path.join(sub_dir, new_f)) 
        
model_sources = []
append_file(file_list=model_sources, dir_path=igordir)
append_file(file_list=model_sources, dir_path=c_model_dir)
append_file(file_list=model_sources, dir_path=wrapper_dir)
smear_sources = []
append_file(file_list=smear_sources, dir_path=smear_dir)


smearer_sources = [os.path.join(smear_dir, "smearer.cpp"),
                  os.path.join(smear_dir, "smearer_module.cpp")]
if os.name=='nt':
    smearer_sources.append(os.path.join(igordir, "winFuncs.c"))

dist = setup(
    name="sasmodels",
    version = VERSION,
    description = "Python module for SAS scattering models",
    author = "SasView Team",
    author_email = "developers@sasview.org",
    url = "https://github.com/SasView/sasview.git",
    
    # Place this module under the sas package
    #ext_package = "sas",
    
    # Use the pure python modules
    package_dir = {"sas":os.path.join("src", "sas"),
                   "sas.models":os.path.join("src", "sas", "models"),
                   "sas.models.sas_extension":os.path.join("src", "sas", "models", "sas_extension"),
                  },
    package_data={'sas.models': [os.path.join('media', "*")]},
    packages = ["sas","sas.models",
                "sas.models.sas_extension",],
    
    ext_modules = [ 
                   
        Extension("sas.models.sas_extension.c_models",
                    sources=model_sources,                 
                    include_dirs=[igordir, includedir, c_model_dir, numpy_incl_path],   
                    ),

        # Smearer extension
        Extension("sas.models.sas_extension.smearer",
                   sources = smearer_sources,
                   include_dirs=[igordir, smear_dir, numpy_incl_path],
                   ),
                   
        Extension("sas.models.sas_extension.smearer2d_helper",
                  sources = [os.path.join(smear_dir, 
                                          "smearer2d_helper_module.cpp"),
                             os.path.join(smear_dir, "smearer2d_helper.cpp"),],
                  include_dirs=[smear_dir,numpy_incl_path],
                  )
        ],
    cmdclass = {'build_ext': build_ext_subclass }
    )
        
