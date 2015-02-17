"""
    Setup for SasView
    #TODO: Add checks to see that all the dependencies are on the system
"""
import sys
import os
from setuptools import setup, Extension
from distutils.command.build_ext import build_ext
from distutils.core import Command

try:
    from numpy.distutils.misc_util import get_numpy_include_dirs
    NUMPY_INC = get_numpy_include_dirs()[0]
except:
    try:
        import numpy
        NUMPY_INC = os.path.join(os.path.split(numpy.__file__)[0], 
                                 "core","include")
    except:
        msg = "\nNumpy is needed to build SasView. "
        print msg, "Try easy_install numpy.\n  %s" % str(sys.exc_value)
        sys.exit(0)

# Manage version number ######################################
import sasview
VERSION = sasview.__version__
##############################################################

package_dir = {}
package_data = {}
packages = []
ext_modules = []

# Remove all files that should be updated by this setup
# We do this here because application updates these files from .sasview
# except when there is no such file
# Todo : make this list generic
plugin_model_list = ['polynominal5.py', 'sph_bessel_jn.py', 
                     'sum_Ap1_1_Ap2.py', 'sum_p1_p2.py', 
                     'testmodel_2.py', 'testmodel.py',
                     'polynominal5.pyc', 'sph_bessel_jn.pyc', 
                     'sum_Ap1_1_Ap2.pyc', 'sum_p1_p2.pyc', 
                     'testmodel_2.pyc', 'testmodel.pyc', 'plugins.log']
sas_dir = os.path.join(os.path.expanduser("~"),'.sasview')
if os.path.isdir(sas_dir):
    f_path = os.path.join(sas_dir, "sasview.log")
    if os.path.isfile(f_path):
        os.remove(f_path)
    f_path = os.path.join(sas_dir, "serialized_cat.json")
    if os.path.isfile(f_path):
        os.remove(f_path)
    f_path = os.path.join(sas_dir, 'config', "custom_config.py")
    if os.path.isfile(f_path):
        os.remove(f_path)
    f_path = os.path.join(sas_dir, 'plugin_models')
    if os.path.isdir(f_path):
        for f in os.listdir(f_path): 
            if f in plugin_model_list:
                file_path =  os.path.join(f_path, f)
                os.remove(file_path)
                    
# 'sys.maxsize' and 64bit: Not supported for python2.5
is_64bits = False
if sys.version_info >= (2, 6):
    is_64bits = sys.maxsize > 2**32
    
enable_openmp = False

if sys.platform =='darwin':
    if not is_64bits:
        # Disable OpenMP
        enable_openmp = False
    else:
        # Newer versions of Darwin don't support openmp
        try:
            darwin_ver = int(os.uname()[2].split('.')[0])
            if darwin_ver >= 12:
                enable_openmp = False
        except:
            print "PROBLEM determining Darwin version"

# Options to enable OpenMP
copt =  {'msvc': ['/openmp'],
         'mingw32' : ['-fopenmp'],
         'unix' : ['-fopenmp']}
lopt =  {'msvc': ['/MANIFEST'],
         'mingw32' : ['-fopenmp'],
         'unix' : ['-lgomp']}

# Platform-specific link options
platform_lopt = {'msvc' : ['/MANIFEST']}
platform_copt = {}

# Set copts to get compile working on OS X >= 10.9 using clang
if sys.platform =='darwin':
    try:
        darwin_ver = int(os.uname()[2].split('.')[0])
        if darwin_ver >= 13:
            platform_copt = {'unix' : ['-Wno-error=unused-command-line-argument-hard-error-in-future']}
    except:
        print "PROBLEM determining Darwin version"

class DisableOpenMPCommand(Command):
    description = "The version of MinGW that comes with Anaconda does not come with OpenMP :( "\
                  "This commands means we can turn off compiling with OpenMP for this or any "\
                  "other reason."
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()
        global enable_openmp
        enable_openmp = False

    def run(self):
        pass

class build_ext_subclass( build_ext ):
    def build_extensions(self):
        # Get 64-bitness
        c = self.compiler.compiler_type
        print "Compiling with %s (64bit=%s)" % (c, str(is_64bits))
        
        # OpenMP build options
        if enable_openmp:
            if copt.has_key(c):
                for e in self.extensions:
                    e.extra_compile_args = copt[ c ]
            if lopt.has_key(c):
                for e in self.extensions:
                    e.extra_link_args = lopt[ c ]
                    
        # Platform-specific build options
        if platform_lopt.has_key(c):
            for e in self.extensions:
                e.extra_link_args = platform_lopt[ c ]

        if platform_copt.has_key(c):
            for e in self.extensions:
                e.extra_compile_args = platform_copt[ c ]


        build_ext.build_extensions(self)

class BuildSphinxCommand(Command):
    description = "Build Sphinx documentation."
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        sys.path.append("docs/sphinx-docs")
        import build_sphinx

        build_sphinx.clean()
        build_sphinx.retrieve_user_docs()
        build_sphinx.apidoc()
        build_sphinx.build()

# sas module
package_dir["sas"] = os.path.join("src", "sas")
packages.append("sas")

# sas.invariant
package_dir["sas.invariant"] = os.path.join("src", "sas", "invariant")
packages.extend(["sas.invariant"])

# sas.guiframe
guiframe_path = os.path.join("src", "sas", "guiframe")
package_dir["sas.guiframe"] = guiframe_path
package_dir["sas.guiframe.local_perspectives"] = os.path.join(os.path.join(guiframe_path, "local_perspectives"))
package_data["sas.guiframe"] = ['images/*', 'media/*']
packages.extend(["sas.guiframe", "sas.guiframe.local_perspectives"])
# build local plugin
for d in os.listdir(os.path.join(guiframe_path, "local_perspectives")):
    if d not in ['.svn','__init__.py', '__init__.pyc']:
        package_name = "sas.guiframe.local_perspectives." + d
        packages.append(package_name)
        package_dir[package_name] = os.path.join(guiframe_path, "local_perspectives", d)

# sas.dataloader
package_dir["sas.dataloader"] = os.path.join("src", "sas", "dataloader")
package_data["sas.dataloader.readers"] = ['defaults.xml','schema/*.xsd']
packages.extend(["sas.dataloader","sas.dataloader.readers","sas.dataloader.readers.schema"])

# sas.calculator
package_dir["sas.calculator"] =os.path.join("src", "sas", "calculator")
packages.extend(["sas.calculator"])
    
# sas.pr
numpy_incl_path = os.path.join(NUMPY_INC, "numpy")
srcdir  = os.path.join("src", "sas", "pr", "c_extensions")
package_dir["sas.pr.core"] = srcdir
package_dir["sas.pr"] = os.path.join("src","sas", "pr")
packages.extend(["sas.pr","sas.pr.core"])
ext_modules.append( Extension("sas.pr.core.pr_inversion",
                              sources = [os.path.join(srcdir, "Cinvertor.c"),
                                         os.path.join(srcdir, "invertor.c"),
                                         ],
                              include_dirs=[numpy_incl_path],
                              ) )
        
# sas.fit (park integration)
package_dir["sas.fit"] = os.path.join("src", "sas", "fit")
packages.append("sas.fit")

# Perspectives
package_dir["sas.perspectives"] = os.path.join("src", "sas", "perspectives")
package_dir["sas.perspectives.pr"] = os.path.join("src", "sas", "perspectives", "pr")
packages.extend(["sas.perspectives","sas.perspectives.pr"])
package_data["sas.perspectives.pr"] = ['images/*']

package_dir["sas.perspectives.invariant"] = os.path.join("src", "sas", "perspectives", "invariant")
packages.extend(["sas.perspectives.invariant"])
package_data['sas.perspectives.invariant'] = [os.path.join("media",'*')]

package_dir["sas.perspectives.fitting"] = os.path.join("src", "sas", "perspectives", "fitting")
package_dir["sas.perspectives.fitting.plugin_models"] = os.path.join("src", "sas", "perspectives", "fitting", "plugin_models")
packages.extend(["sas.perspectives.fitting", 
                 "sas.perspectives.fitting.plugin_models"])
package_data['sas.perspectives.fitting'] = ['media/*','plugin_models/*']

packages.extend(["sas.perspectives", "sas.perspectives.calculator"])    
package_data['sas.perspectives.calculator'] = ['images/*', 'media/*']
    
# Data util
package_dir["data_util"] = os.path.join("src", "sas", "data_util")
packages.append("sas.data_util")

# Plottools
package_dir["sas.plottools"] = os.path.join("src", "sas", "plottools")
packages.append("sas.plottools")

# Park 1.2.1
package_dir["park"]="park-1.2.1/park"
packages.extend(["park"])
package_data["park"] = ['park-1.2.1/*.txt', 'park-1.2.1/park.epydoc']
ext_modules.append( Extension("park._modeling",
                              sources = [ os.path.join("park-1.2.1", 
                                                "park", "lib", "modeling.cc"),
                                         os.path.join("park-1.2.1", 
                                                "park", "lib", "resolution.c"),
                                         ],
                              ) )

# sas models
includedir  = os.path.join("src", "sas", "models", "include")
igordir = os.path.join("src", "sas", "models", "c_extension", "libigor")
cephes_dir = os.path.join("src", "sas", "models", "c_extension", "cephes")
c_model_dir = os.path.join("src", "sas", "models", "c_extension", "c_models")
smear_dir  = os.path.join("src", "sas", "models", "c_extension", "c_smearer")
gen_dir  = os.path.join("src", "sas", "models", "c_extension", "c_gen")
wrapper_dir  = os.path.join("src", "sas", "models", "c_extension", "python_wrapper", "generated")
model_dir = os.path.join("src", "sas","models")

if os.path.isdir(wrapper_dir):
    for file in os.listdir(wrapper_dir): 
        file_path =  os.path.join(wrapper_dir, file)
        os.remove(file_path)
else:
    os.makedirs(wrapper_dir)
sys.path.append(os.path.join("src", "sas", "models", "c_extension", "python_wrapper"))
from wrapping import generate_wrappers
generate_wrappers(header_dir = includedir, 
                  output_dir = model_dir,
                  c_wrapper_dir = wrapper_dir)

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
        
package_dir["sas.models"] = model_dir
package_dir["sas.models.sas_extension"] = os.path.join("src", "sas", "models", "sas_extension")
package_data['sas.models'] = [os.path.join('media', "*.*")]
package_data['sas.models'] += [os.path.join('media','img', "*.*")]
packages.extend(["sas.models","sas.models.sas_extension"])
    
smearer_sources = [os.path.join(smear_dir, "smearer.cpp"),
                  os.path.join(smear_dir, "smearer_module.cpp")]
geni_sources = [os.path.join(gen_dir, "sld2i_module.cpp")]
if os.name=='nt':
    smearer_sources.append(os.path.join(igordir, "winFuncs.c"))
    geni_sources.append(os.path.join(igordir, "winFuncs.c"))

c_models = [ 
    Extension("sas.models.sas_extension.c_models",
        sources=model_sources,                 
        include_dirs=[
            igordir, includedir, c_model_dir, numpy_incl_path, cephes_dir
        ],
    ),

    # Smearer extension
    Extension("sas.models.sas_extension.smearer",
        sources = smearer_sources,
        include_dirs=[igordir,  smear_dir, numpy_incl_path],
    ),
                    
    Extension("sas.models.sas_extension.smearer2d_helper",
        sources = [
            os.path.join(smear_dir, "smearer2d_helper_module.cpp"),
            os.path.join(smear_dir, "smearer2d_helper.cpp"),
            os.path.join(igordir, "winFuncs.c"),
        ],
        include_dirs=[smear_dir, numpy_incl_path],
    ),
                    
    Extension("sas.models.sas_extension.sld2i",
        sources = [
            os.path.join(gen_dir, "sld2i_module.cpp"),
            os.path.join(gen_dir, "sld2i.cpp"),
            os.path.join(c_model_dir, "libfunc.c"),
            os.path.join(c_model_dir, "librefl.c"),
            os.path.join(igordir, "winFuncs.c"),
        ],
        include_dirs=[gen_dir, includedir,  c_model_dir, numpy_incl_path],
    ),
]

# Comment out the following to avoid rebuilding all the models
ext_modules.extend(c_models)

# SasView

package_dir["sas.sasview"] = "sasview"
package_data['sas.sasview'] = ['images/*', 'media/*', 'test/*', 
                                 'default_categories.json']
packages.append("sas.sasview")

required = [
    'bumps>=0.7.5.4', 'periodictable>=1.3.1', 'pyparsing<2.0.0',

    # 'lxml>=2.2.2',
    'lxml', 

    ## The following dependecies won't install automatically, so assume them
    ## The numbers should be bumped up for matplotlib and wxPython as well.
    # 'numpy>=1.4.1', 'scipy>=0.7.2', 'matplotlib>=0.99.1.1',
    # 'wxPython>=2.8.11', 'pil',
    ]

if os.name=='nt':
    required.extend(['html5lib', 'reportlab'])
else:
    required.extend(['pil'])
   
# Set up SasView    
setup(
    name="sasview",
    version = VERSION,
    description = "SasView application",
    author = "University of Tennessee",
    author_email = "sansdanse@gmail.com",
    url = "http://sasview.org",
    license = "PSF",
    keywords = "small-angle x-ray and neutron scattering analysis",
    download_url = "https://sourceforge.net/projects/sansviewproject/files/",
    package_dir = package_dir,
    packages = packages,
    package_data = package_data,
    ext_modules = ext_modules,
    install_requires = required,
    zip_safe = False,
    entry_points = {
                    'console_scripts':[
                                       "sasview = sas.sasview.sasview:run",
                                       ]
                    },
    cmdclass = {'build_ext': build_ext_subclass,
                'docs': BuildSphinxCommand,
                'disable_openmp': DisableOpenMPCommand}
    )   
