"""
 Installation script for SANS models

  - To compile and install:
      python setup.py install
  - To create distribution:
      python setup.py bdist_wininst

"""

from distutils.core import setup, Extension


# Build the module name
srcdir  = "src"
igordir = "../../../libigor"
extdir  = "../c_extensions"

print "Installing SANS models"

setup(
    name="models",
    version = "0.1",
    description = "Python module for various tests of SANS scattering models",
    author = "Mathieu Doucet",
    author_email = "doucet@nist.gov",
    url = "http://danse.us/trac/sans",
    
    # Place this module under the sans package
    #ext_package = "sans",
    
    # Use the pure python modules
    package_dir = {"sans_extension.prototypes":"."},
    
    packages = ["sans_extension.prototypes"],
    
    ext_modules = [ Extension("sans_extension.prototypes.c_models",
     sources = [
        srcdir+"/c_models.c",
        "../../../igor_wrapper/c_disperser.c",
        srcdir+"/disperse_cylinder.c",
        srcdir+"/CDispCylinderModel.c",
        srcdir+"/CSimCylinderF.c",
        srcdir+"/simcylinder_fast.c",
        srcdir+"/CSimSphereF.c",
        srcdir+"/sphere_fast.c",
        srcdir+"/CTestSphere2.c",
        srcdir+"/testsphere.c",
        srcdir+"/CSimCylinder.c",
        srcdir+"/simcylinder.c",
        srcdir+"/modelCalculations.c",
        srcdir+"/CSmearCylinderModel.c",
        srcdir+"/smeared_cylinder.c",
        igordir+"/libCylinder.c",
        igordir+"/libSphere.c",
        extdir+"/cylinder.c",
        srcdir+"/CCanvas.c",
        srcdir+"/canvas.c"
            ],
         include_dirs=[igordir, extdir])])
        