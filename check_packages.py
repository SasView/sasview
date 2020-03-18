"""
Checking and reinstalling the external packages
"""
from __future__ import print_function

import sys
import yaml

from colorama import Fore, Back, Style


if sys.platform == 'win32':
    file_location = 'build_tools/conda/ymls/sasview-env-build_win.yml'
elif sys.platform == 'darwin':
    file_location = 'build_tools/conda/ymls/sasview-env-build_osx.yml'
else:
    file_location = 'build_tools/conda/ymls/sasview-env-build_linux.yml'

with open(file_location, 'r') as stream:
    try:
        yaml_dict = yaml.load(stream, Loader=yaml.SafeLoader)
        print(yaml_dict)
        common_required_package_list = yaml_dict['dependencies']
    except Exception as e:
        print(e)

print(Style.RESET_ALL)
print("CHECKING REQUIRED PACKAGES....")

for yaml_name in common_required_package_list:
    text_split = yaml_name.split('=')
    package_name = text_split[0]
    package_version = text_split[1]

    print(Style.RESET_ALL)
    try:
        i = __import__(package_name, fromlist=[''])
        if package_version is None:
            print("%s Installed (Unknown version)" % package_name)
        elif package_name == 'lxml':
            verstring = str(getattr(i, 'LXML_VERSION'))
            print("%s Version Installed: %s" % (package_name, verstring.replace(', ', '.').lstrip('(').rstrip(')')))
        else:
            print("%s Version Installed: %s" % (package_name, getattr(i, '__version__')))
    except AttributeError:
        print("%s Installed (Unknown version)" % package_name)
    except ImportError:
        print(Fore.BLACK + Back.WHITE + '%s NOT INSTALLED' % package_name)

print(Style.RESET_ALL)
