"""
Checking and reinstalling the external packages
"""
from __future__ import print_function

import sys

# Fix for error: hash-collision-3-both-1-and-1/
# See http://jaredforsyth.com/blog/2010/apr/28/accessinit-hash-collision-3-both-1-and-1/
try:
    import PIL.Image
except ImportError:
    pass
else:
    sys.modules['Image'] = PIL.Image

if sys.version_info[0] > 2:
    print("To use the sasview GUI you must use Python 2\n")

common_required_package_list = {
    'setuptools': {'version': '0.6c11', 'import_name': 'setuptools', 'test': '__version__'},
    'pyparsing': {'version': '1.5.5', 'import_name': 'pyparsing', 'test': '__version__'},
    'html5lib': {'version': '0.95', 'import_name': 'html5lib', 'test': '__version__'},
    'reportlab': {'version': '2.5', 'import_name': 'reportlab', 'test': 'Version'},
    'h5py': {'version': '2.9', 'import_name': 'h5py', 'test': '__version__'},
    'lxml': {'version': '4.3', 'import_name': 'lxml.etree', 'test': 'LXML_VERSION'},
    'PIL': {'version': '1.1.7', 'import_name': 'Image', 'test': 'VERSION'},
    'pylint': {'version': None, 'import_name': 'pylint', 'test': None},
    'periodictable': {'version': '1.5.0', 'import_name': 'periodictable', 'test': '__version__'},
    'bumps': {'version': '0.7.11', 'import_name': 'bumps', 'test': '__version__'},
    'numpy': {'version': '1.7.1', 'import_name': 'numpy', 'test': '__version__'},
    'scipy': {'version': '1.2.0', 'import_name': 'scipy', 'test': '__version__'},
    'pyqt': {'version': '5.6', 'import_name': 'PyQt5.QtCore', 'test': 'PYQT_VERSION_STR'},
    'matplotlib': {'version': '2.2.0', 'import_name': 'matplotlib', 'test': '__version__'},
    'xhtml2pdf': {'version': '3.0.33', 'import_name': 'xhtml2pdf', 'test': '__version__'},
    'sphinx': {'version': '1.2.1', 'import_name': 'sphinx', 'test': '__version__'},
    'pyopencl': {'version': '2018.2', 'import_name': 'pyopencl', 'test': 'VERSION_TEXT'},
    'ipykernel': {'version': '4.9.0', 'import_name': 'ipykernel', 'test': '__version__'},
    'ipython': {'version': '6.5.0', 'import_name': 'IPython', 'test': '__version__'},
    'jupyter': {'version': '1.0.0', 'import_name': 'jupyter', 'test': '__version__'},
    'twisted': {'version': '18.9.0', 'import_name': 'twisted', 'test': '__version__'},
    'pytest': {'version': '4.2.0', 'import_name': 'pytest', 'test': '__version__'},
}
win_required_package_list = {
}

deprecated_package_list = {
}

print("Checking Required Package Versions....\n")
print("Common Packages")

for package_name, test_vals in common_required_package_list.items():
    try:
        i = __import__(test_vals['import_name'], fromlist=[''])
        if test_vals['test'] is None:
            print("%s Installed (Unknown version)" % package_name)
        elif package_name == 'lxml':
            verstring = str(getattr(i, 'LXML_VERSION'))
            print("%s Version Installed: %s"% (package_name, verstring.replace(', ', '.').lstrip('(').rstrip(')')))
        else:
            print("%s Version Installed: %s"% (package_name, getattr(i, test_vals['test'])))
    except ImportError:
        print('%s NOT INSTALLED'% package_name)

if sys.platform == 'win32':
    print("")
    print("Windows Specific Packages:")
    for package_name, test_vals in win_required_package_list.items():
        try:
            i = __import__(test_vals['import_name'], fromlist=[''])
            print("%s Version Installed: %s"% (package_name, getattr(i, test_vals['test'], "unknown")))
        except ImportError:
            print('%s NOT INSTALLED'% package_name)

if sys.platform == 'darwin':
    print("")
    print("MacOS Specific Packages:")
    for package_name, test_vals in mac_required_package_list.items():
        try:
            i = __import__(test_vals['import_name'], fromlist=[''])
            print("%s Version Installed: %s"% (package_name, getattr(i, test_vals['test'])))
        except ImportError:
            print('%s NOT INSTALLED'% package_name)


print("")
print("Deprecated Packages")
print("You can remove these unless you need them for other reasons!")
for package_name, test_vals in deprecated_package_list.items():
    try:
        i = __import__(test_vals['import_name'], fromlist=[''])
        if package_name == 'pyPdf':
            # pyPdf doesn't have the version number internally
            print('pyPDF Installed (Version unknown)')
        else:
            print("%s Version Installed: %s"% (package_name, getattr(i, test_vals['test'])))
    except ImportError:
        print('%s NOT INSTALLED'% package_name)
