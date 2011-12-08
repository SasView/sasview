"""
    Setup for SansView
    #TODO: Add checks to see that all the dependencies are on the system
"""
import sys
import os
#from distutils.core import setup, Extension
from setuptools import setup, Extension, find_packages
try:
    from numpy.distutils.misc_util import get_numpy_include_dirs
    NUMPY_INC = get_numpy_include_dirs()[0]
except:
    try:
        import numpy
        NUMPY_INC = os.path.join(os.path.split(numpy.__file__)[0],"core","include")
    except:
        print "\nNumpy is needed to build SansView. Try easy_install numpy.\n  %s" % str(sys.exc_value)
        sys.exit(0)

package_dir = {}
package_data = {}
packages = []
ext_modules = []

# TODO check for sans/__init__.py

# Enable OpenMP
extra_compile_args = []
extra_link_args = []
if not os.name=='nt':
    extra_compile_args = ['-fopenmp']
    extra_link_args = ['-lgomp']

# sans.invariant
package_dir["sans.invariant"] = "sansinvariant/src/sans/invariant"
packages.extend(["sans.invariant"])

# sans.guiframe
guiframe_path = os.path.join("sansguiframe", "src", "sans", "guiframe")
package_dir["sans.guiframe"] = guiframe_path
package_dir["sans.guiframe.local_perspectives"] = os.path.join(guiframe_path, "local_perspectives")
package_data["sans.guiframe"] = ['images/*', 'media/*']
packages.extend(["sans.guiframe", "sans.guiframe.local_perspectives"])
# build local plugin
for dir in os.listdir(os.path.join(guiframe_path, "local_perspectives")):
    if dir not in ['.svn','__init__.py', '__init__.pyc']:
        package_name = "sans.guiframe.local_perspectives." + dir
        packages.append(package_name)
        package_dir[package_name] = os.path.join(guiframe_path, "local_perspectives", dir)

# sans.dataloader
package_dir["sans.dataloader"] = os.path.join("sansdataloader", "src", "sans", "dataloader")
package_data["sans.dataloader.readers"] = ['defaults.xml']
packages.extend(["sans.dataloader","sans.dataloader.readers"])

# sans.calculator
package_dir["sans.calculator"] = "sanscalculator/src/sans/calculator"
packages.extend(["sans.calculator"])
    
# sans.pr
numpy_incl_path = os.path.join(NUMPY_INC, "numpy")
srcdir  = os.path.join("pr_inversion", "src", "sans", "pr", "c_extensions")


    
package_dir["sans.pr.core"] = srcdir
package_dir["sans.pr"] = os.path.join("pr_inversion", "src","sans", "pr")
packages.extend(["sans.pr","sans.pr.core"])
ext_modules.append( Extension("sans.pr.core.pr_inversion",
                              sources = [ os.path.join(srcdir, "Cinvertor.c"),
                                         os.path.join(srcdir, "invertor.c"),
                                         ],
                              include_dirs=[numpy_incl_path],
                              extra_compile_args=extra_compile_args,
                              extra_link_args=extra_link_args                              
                              ) )
        
# sans.fit (park integration)
package_dir["sans.fit"] = "park_integration/src/sans/fit"
packages.append("sans.fit")

# inversion view
package_dir["sans.perspectives"] = "inversionview/src/sans/perspectives"
package_dir["sans.perspectives.pr"] = "inversionview/src/sans/perspectives/pr"
packages.extend(["sans.perspectives","sans.perspectives.pr"])
package_data["sans.perspectives.pr"] = ['images/*']

# Invariant view
package_dir["sans.perspectives"] = os.path.join("invariantview", "src", "sans", "perspectives")
package_dir["sans.perspectives.invariant"] = os.path.join("invariantview", "src", "sans", "perspectives", "invariant")
                
package_data['sans.perspectives.invariant'] = [os.path.join("media",'*')]
packages.extend(["sans.perspectives","sans.perspectives.invariant"]) 

# Fitting view
package_dir["sans.perspectives"] = os.path.join("fittingview", "src", "sans", "perspectives"),
package_dir["sans.perspectives.fitting"] = os.path.join("fittingview", "src", "sans", "perspectives", "fitting")
package_data['sans.perspectives.fitting'] = ['media/*']
packages.extend(["sans.perspectives", "sans.perspectives.fitting"])

# Calculator view
package_dir["sans.perspectives"] = "calculatorview/src/sans/perspectives"
package_dir["sans.perspectives.calculator"] = os.path.join("calculatorview", "src", "sans", "perspectives", "calculator")
package_data['sans.perspectives.calculator'] = ['images/*', 'media/*']
packages.extend(["sans.perspectives", "sans.perspectives.calculator"])
     
# Data util
package_dir["data_util"] = "sansutil"
packages.extend(["data_util"])

# Plottools
package_dir["danse"] = os.path.join("plottools", "src", "danse")
package_dir["danse.common"] = os.path.join("plottools", "src", "danse", "common")
package_dir["danse.common.plottools"] = os.path.join("plottools", "src", "danse", "common", "plottools")
packages.extend(["danse", "danse.common", "danse.common.plottools"])

# Park 1.2.1
package_dir["park"]="park-1.2.1/park"
packages.extend(["park"])
package_data["park"] = ['park-1.2.1/*.txt', 'park-1.2.1/park.epydoc']
ext_modules.append( Extension("park._modeling",
                              sources = [ os.path.join("park-1.2.1", "park", "lib", "modeling.cc"),
                                         os.path.join("park-1.2.1", "park", "lib", "resolution.c"),
                                         ],
                              extra_compile_args=extra_compile_args,
                              extra_link_args=extra_link_args
                              ) )

# Sans models
srcdir  = os.path.join("sansmodels", "src", "sans", "models", "c_extensions")
igordir = os.path.join("sansmodels", "src","sans", "models", "libigor")
c_model_dir = os.path.join("sansmodels", "src", "sans", "models", "c_models")
smear_dir  = os.path.join("sansmodels", "src", "sans", "models", "c_smearer")

IGNORED_FILES = ["a.exe",
                 "__init__.py"
                 ".svn",
                   "lineparser.py",
                   "run.py",
                   "CGaussian.cpp",
                   "CLogNormal.cpp",
                   "CLorentzian.cpp",
                   "CSchulz.cpp",
                   "WrapperGenerator.py",
                   "wrapping.py"
                   ]

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
append_file(file_list=model_sources, dir_path=srcdir)
append_file(file_list=model_sources, dir_path=igordir)
append_file(file_list=model_sources, dir_path=c_model_dir)
smear_sources = []
append_file(file_list=smear_sources, dir_path=smear_dir)


package_dir["sans"] = os.path.join("sansmodels", "src", "sans")
package_dir["sans.models"] = os.path.join("sansmodels", "src", "sans", "models")
package_dir["sans.models.sans_extension"] = srcdir
            
package_data['sans.models'] = [os.path.join('media', "*")]
packages.extend(["sans","sans.models","sans.models.sans_extension"])
    
smearer_sources = [os.path.join(smear_dir, "smearer.cpp"),
                  os.path.join(smear_dir, "smearer_module.cpp")]

if os.name=='nt':
    smearer_sources.append(os.path.join(igordir, "winFuncs.c"))

ext_modules.extend( [ Extension("sans.models.sans_extension.c_models",
                                sources=model_sources,                 
                                include_dirs=[igordir, srcdir, c_model_dir, numpy_incl_path],
                                extra_compile_args=extra_compile_args,
                                extra_link_args=extra_link_args
                                ),       
                    # Smearer extension
                    Extension("sans.models.sans_extension.smearer",
                              sources = smearer_sources,
                              include_dirs=[igordir, smear_dir, numpy_incl_path],
                              extra_compile_args=extra_compile_args,
                              extra_link_args=extra_link_args
                              ),
                    
                    Extension("sans.models.sans_extension.smearer2d_helper",
                              sources = [os.path.join(smear_dir, 
                                                      "smearer2d_helper_module.cpp"),
                                         os.path.join(smear_dir, "smearer2d_helper.cpp"),],
                              include_dirs=[smear_dir,numpy_incl_path],
                              extra_compile_args=extra_compile_args,
                              extra_link_args=extra_link_args
                              )
                    ] )
        
# SansView
package_dir["sans.sansview"] = "sansview"
package_data['sans.sansview'] = ['images/*', 'media/*', 'plugins/*', 'test/*']
packages.append("sans.sansview")

#required = ['lxml>=2.2.2', 'numpy>=1.4.1', 'matplotlib>=0.99.1.1', 'wxPython>=2.8.11',
#            'pil','periodictable>=1.3.0', 'scipy>=0.7.2']
required = ['lxml','periodictable>=1.3.0', 'unittest-xml-reporting']

if os.name=='nt':
    #required.extend(['comtypes', 'pisa', 'html5lib', 'reportlab'])
    required.extend(['comtypes', 'pisa', 'html5lib'])
else:
    required.extend(['pil'])
   
 # Set up SansView    
setup(
    name="sansview",
    version = "2.0.1",
    description = "SansView application",
    author = "University of Tennessee",
    author_email = "sansdanse@gmail.com",
    url = "http://danse.chem.utk.edu",
    license = "PSF",
    keywords = "small-angle neutron scattering analysis",
    download_url = "https://sourceforge.net/projects/sansviewproject/files/",
    package_dir = package_dir,
    packages = packages,
    package_data = package_data,
    ext_modules = ext_modules,
    install_requires = required,
    zip_safe = False,
    entry_points = {
                    'console_scripts':[
                                       "sansview = sans.sansview.sansview:run",
                                       ]
                    }
    )   
