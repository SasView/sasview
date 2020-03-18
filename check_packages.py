"""
Checking and reinstalling the external packages
"""
from __future__ import print_function

import sys
import yaml

from colorama import Fore, Back, Style


if sys.platform == 'win32':
    file_location = './build_tools/conda/ymls/sasview-env-build_win.yml'
elif sys.platform == 'darwin':
    file_location = './build_tools/conda/ymls/sasview-env-build_osx.yml'
else:
    file_location = './build_tools/conda/ymls/sasview-env-build_linux.yml'

with open(file_location, 'r') as stream:
    try:
        yaml_dict = yaml.load(stream, Loader=yaml.SafeLoader)
        common_required_package_list = yaml_dict['dependencies']
    except Exception as e:
        print(e)

print("")
print(Style.RESET_ALL +
      "....COMPARING PACKAGES LISTED IN {0} to INSTALLED PACKAGES....".format(
          file_location))
print("")

for yaml_name in common_required_package_list:
    try:
        text_split = yaml_name.split('=')
    except AttributeError as e:
        # Continue for tiered files including pip installs
        continue
    package_name = text_split[0]
    package_version = text_split[1]

    try:
        if package_name == 'python':
            full_version = sys.version.split()
            installed_version = full_version[0]
        else:
            i = __import__(package_name, fromlist=[''])
            installed_version = getattr(i, '__version__')
        if package_version == installed_version:
            print(Style.RESET_ALL + "{0} - Expected Version Installed: {1}".format(package_name, installed_version))
        else:
            print(Fore.LIGHTYELLOW_EX + "{0} - Version Mismatch - Installed: {1}, Expected: {2}".format(package_name, installed_version, package_version))
    except AttributeError:
        print(Fore.YELLOW + "{0} - Version Cannot Be Determined - Expected: {1}".format(package_name, package_version))
    except ImportError:
        print(Fore.LIGHTRED_EX + '{0} NOT INSTALLED'.format(package_name))

print(Style.RESET_ALL)
