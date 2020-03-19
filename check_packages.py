"""
Check the existing environment against expected values
"""
from __future__ import print_function

import sys
import yaml
import subprocess

from colorama import Fore, Style


# Output strings
CORRECT = Style.RESET_ALL + "{0} - Expected Version Installed: {1}"
VERSION_MISMATCH = Fore.LIGHTYELLOW_EX +\
          "{0} - Version Mismatch - Installed: {1}, Expected: {2}"
VERSION_UNKNOWN = Fore.YELLOW +\
                  "{0} - Version Cannot Be Determined - Expected: {1}"
NOT_INSTALLED = Fore.LIGHTRED_EX + '{0} NOT INSTALLED'

# Location of yaml files
if sys.platform == 'win32':
    file_location = './build_tools/conda/ymls/sasview-env-build_win.yml'
elif sys.platform == 'darwin':
    file_location = './build_tools/conda/ymls/sasview-env-build_osx.yml'
else:
    file_location = './build_tools/conda/ymls/sasview-env-build_linux.yml'

# Open yaml and get packages
with open(file_location, 'r') as stream:
    try:
        yaml_dict = yaml.load(stream, Loader=yaml.SafeLoader)
        common_required_package_list = yaml_dict['dependencies']
    except Exception as e:
        print(e)

# Get list of system packages (conda or pip)
isConda = True
try:
    reqs = subprocess.check_output(['conda', 'list'])
except Exception:
    reqs = subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'])
    isConda = False

packages_installed = []
versions_installed = []

if isConda:
    for r in reqs.splitlines():
        if r.decode().split()[0] == "#" or len(r.decode().split()) < 2:
            continue
        package = r.decode().split()[0].lower()
        version = r.decode().split()[1]
        packages_installed.append(package)
        versions_installed.append(version)
else:
    packages_installed = [r.decode().split('==')[0].lower() for r in
                          reqs.split()]
    versions_installed = [r.decode().split('==')[1] for r in reqs.split()]

print("")
print(Style.RESET_ALL +
      "....COMPARING PACKAGES LISTED IN {0} to INSTALLED PACKAGES....".format(
          file_location))
print("")

# Step through each yaml package and check its version against system
for yaml_name in common_required_package_list:
    try:
        text_split = yaml_name.split('=')
    except AttributeError as e:
        # Continue for tiered files including pip installs
        continue
    package_name = text_split[0].lower()
    package_version = text_split[1]

    try:
        if package_name == 'python':
            full_version = sys.version.split()
            installed_version = full_version[0]
        else:
            i = packages_installed.index(package_name)
            installed_version = versions_installed[i]
        if package_version == installed_version:
            print(CORRECT.format(package_name, installed_version))
        else:
            print(VERSION_MISMATCH.format(package_name, installed_version,
                                          package_version))
    except AttributeError:
        print(VERSION_UNKNOWN.format(package_name, package_version))
    except ValueError:
        print(NOT_INSTALLED.format(package_name))

print(Style.RESET_ALL)
