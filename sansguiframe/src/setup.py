
"""
Installs the guiframe package
"""

from distutils.core import setup
import os

path = os.path.join(os.getcwd(), "sans", "guiframe",'local_perspectives')
package_dir = {"sans.guiframe":os.path.join("sans", "guiframe"),
               "sans.guiframe.local_perspectives":os.path.join("sans",
                                                        "guiframe",
                                                        "local_perspectives"),}

package_data = {"sans.guiframe": ['images/*', 'media/*']}
packages = ["sans.guiframe", 
            "sans.guiframe.local_perspectives"]
# build local plugin
for dir in os.listdir(path):
    if dir not in ['.svn','__init__.py', '__init__.pyc']:
        package_name = "sans.guiframe.local_perspectives." + dir
        packages.append(package_name)
        package_dir[package_name] = os.path.join("sans", 
                                                 "guiframe",
                                                 "local_perspectives" , dir)


setup(
    name="sans.guiframe",
    version = "0.9.1",
    description = "Python module for SANS gui framework",
    author = "University of Tennessee",
    url = "http://danse.chem.utk.edu",
    package_dir = package_dir,
    packages = packages,
    package_data = package_data,
    )