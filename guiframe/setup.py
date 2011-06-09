
"""
    Installs the guiframe package
"""

    
from distutils.core import setup, Extension

from distutils.sysconfig import get_python_lib
import os
import sys
import glob

    
path = os.path.join(os.getcwd(), 'local_perspectives')
package_dir = { "sans.guiframe":".",
                "sans.guiframe.local_perspectives":"local_perspectives",
                #"sans.guiframe.images":"images",
               # "sans.guiframe.media":"media",
                }
#package_data = {"sans.guiframe": ['images/*'],
#                "sans.guiframe":'media/*']}
package_data = {"sans.guiframe": ['images/*', 'media/*']}
packages = ["sans.guiframe", 
            "sans.guiframe.local_perspectives"]
# build local plugin
for dir in os.listdir(path):
    if dir not in ['.svn','__init__.py', '__init__.pyc']:
        package_name = "sans.guiframe.local_perspectives." + dir
        packages.append(package_name)
        package_dir[package_name] = "local_perspectives/" + dir
               
# Check whether the sans module exists,
# if not, make sure a default __init__ is created
if 'install' in sys.argv:
    try:
        lib_dir = get_python_lib()
        danse_init = os.path.join(lib_dir, 'sans', '__init__.py')
        if not os.path.isfile(danse_init):
            if not os.path.isdir("tmp_sans"):
                os.mkdir("tmp_sans")
            f = open("tmp_sans/__init__.py",'w')
            f.close()
            package_dir['sans'] = "tmp_sans"
            packages.append("sans")
    except:
        print "Couldn't create sans/__init__.py\n  %s" % sys.exc_value

setup(
    name="guiframe",
    version = "0.9",
    description = "Python module for SANS gui framework",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    
    package_dir = package_dir,

    packages = packages,
    package_data = package_data,

    )
if 'sdist' in sys.argv:
    import zipfile
    from distutils.filelist import findall
    filename = "guiframe-0.9"
    cwd = os.getcwd()
    for f in findall(cwd):
        if os.path.basename(f).count(filename) == 1:
            if zipfile.is_zipfile(f):
                zfile = zipfile.ZipFile(f, "a")
                for image_file in glob.glob(os.path.join("images","*")):
                    print "Adding %s to %s\n" % (image_file, os.path.basename(f))
                    zfile.write(image_file, os.path.join(filename, image_file))
                for media_file in glob.glob(os.path.join("media","*")):
                    print "Adding %s to %s\n" % (media_file, os.path.basename(f))
                    zfile.write(media_file, os.path.join(filename, media_file))
                zfile.close()
                break
                    