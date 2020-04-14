# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
    Setup for SasView
    TODO: Add checks to see that all the dependencies are on the system
"""
import os
import subprocess
import shutil
import sys
from distutils.core import Command

from setuptools import setup

# Manage version number ######################################
with open(os.path.join("src", "sas", "sasview", "__init__.py")) as fid:
    for line in fid:
        if line.startswith('__version__'):
            VERSION = line.split('"')[1]
            break
    else:
        raise ValueError("Could not find version in src/sas/sasview/__init__.py")
##############################################################

package_dir = {}
package_data = {}
packages = []
ext_modules = []

# Remove all files that should be updated by this setup
# We do this here because application updates these files from .sasview
# except when there is no such file
# Todo : make this list generic
# plugin_model_list = ['polynominal5.py', 'sph_bessel_jn.py',
#                      'sum_Ap1_1_Ap2.py', 'sum_p1_p2.py',
#                      'testmodel_2.py', 'testmodel.py',
#                      'polynominal5.pyc', 'sph_bessel_jn.pyc',
#                      'sum_Ap1_1_Ap2.pyc', 'sum_p1_p2.pyc',
#                      'testmodel_2.pyc', 'testmodel.pyc', 'plugins.log']

CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SASVIEW_BUILD = os.path.join(CURRENT_SCRIPT_DIR, "build")

# TODO: build step should not be messing with existing installation!!
sas_dir = os.path.join(os.path.expanduser("~"), '.sasview')
if os.path.isdir(sas_dir):
    f_path = os.path.join(sas_dir, "sasview.log")
    if os.path.isfile(f_path):
        os.remove(f_path)
    #f_path = os.path.join(sas_dir, "categories.json")
    #if os.path.isfile(f_path):
    #    os.remove(f_path)
    f_path = os.path.join(sas_dir, 'config', "custom_config.py")
    if os.path.isfile(f_path):
        os.remove(f_path)
    #f_path = os.path.join(sas_dir, 'plugin_models')
    # if os.path.isdir(f_path):
    #     for f in os.listdir(f_path):
    #         if f in plugin_model_list:
    #             file_path =  os.path.join(f_path, f)
    #             os.remove(file_path)


# Optionally clean before build.
dont_clean = 'update' in sys.argv
if dont_clean:
    sys.argv.remove('update')
elif os.path.exists(SASVIEW_BUILD):
    print("Removing existing build directory", SASVIEW_BUILD, "for a clean build")
    shutil.rmtree(SASVIEW_BUILD)

class BuildSphinxCommand(Command):
    description = "Build Sphinx documentation."
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        ''' First builds the sasmodels documentation if the directory
        is present. Then builds the sasview docs.
        '''
        ### AJJ - Add code for building sasmodels docs here:
        # check for doc path
        SASMODELS_DOCPATH = os.path.abspath(os.path.join(os.getcwd(), '..', 'sasmodels', 'doc'))
        print("========= check for sasmodels at", SASMODELS_DOCPATH, "============")
        if os.path.exists(SASMODELS_DOCPATH):
            if os.path.isdir(SASMODELS_DOCPATH):
                # if available, build sasmodels docs
                print("============= Building sasmodels model documentation ===============")
                smdocbuild = subprocess.call([
                    "make",
                    "PYTHON=%s" % sys.executable,
                    "-C", SASMODELS_DOCPATH,
                    "html"
                ])
        else:
            # if not available warning message
            print("== !!WARNING!! sasmodels directory not found. Cannot build model docs. ==")

        #Now build sasview (+sasmodels) docs
        sys.path.append("docs/sphinx-docs")
        import build_sphinx
        build_sphinx.rebuild()

if 'clean' not in sys.argv:
    _ = subprocess.call([sys.executable, "src/sas/qtgui/convertUI.py"])

# sas module
package_dir["sas"] = os.path.join("src", "sas")
packages.append("sas")

# sas module
# qt module
package_dir["sas.qtgui"] = os.path.join("src", "sas", "qtgui")
packages.append("sas.qtgui")

# sas module
package_dir["sas.sascalc"] = os.path.join("src", "sas", "sascalc")
packages.append("sas.sascalc")

# sas.sascalc.invariant
package_dir["sas.sascalc.invariant"] = os.path.join(
    "src", "sas", "sascalc", "invariant")
packages.extend(["sas.sascalc.invariant"])


# sas.sascalc.dataloader
package_dir["sas.sascalc.dataloader"] = os.path.join(
    "src", "sas", "sascalc", "dataloader")
package_data["sas.sascalc.dataloader.readers"] = ['schema/*.xsd']
packages.extend(["sas.sascalc.dataloader", "sas.sascalc.dataloader.readers",
                 "sas.sascalc.dataloader.readers.schema"])


# sas.sascalc.calculator
package_dir["sas.sascalc.calculator"] = os.path.join(
    "src", "sas", "sascalc", "calculator")
packages.append("sas.sascalc.calculator")


# sas.sascalc.pr
package_dir["sas.sascalc.pr"] = os.path.join("src", "sas", "sascalc", "pr")
packages.append("sas.sascalc.pr")


# sas.sascalc.file_converter
package_dir["sas.sascalc.file_converter"] = os.path.join(
    "src", "sas", "sascalc", "file_converter")
packages.append("sas.sascalc.file_converter")

# sas.sascalc.corfunc
package_dir["sas.sascalc.corfunc"] = os.path.join(
    "src", "sas", "sascalc", "corfunc")
packages.append("sas.sascalc.corfunc")

# sas.sascalc.fit
package_dir["sas.sascalc.fit"] = os.path.join("src", "sas", "sascalc", "fit")
packages.append("sas.sascalc.fit")

# Perspectives
# package_dir["sas.sasgui.perspectives"] = os.path.join(
#     "src", "sas", "sasgui", "perspectives")
# package_dir["sas.sasgui.perspectives.pr"] = os.path.join(
#     "src", "sas", "sasgui", "perspectives", "pr")
# packages.extend(["sas.sasgui.perspectives", "sas.sasgui.perspectives.pr"])
# package_data["sas.sasgui.perspectives.pr"] = ['media/*']

# package_dir["sas.sasgui.perspectives.invariant"] = os.path.join(
#     "src", "sas", "sasgui", "perspectives", "invariant")
# packages.extend(["sas.sasgui.perspectives.invariant"])
# package_data['sas.sasgui.perspectives.invariant'] = [
#     os.path.join("media", '*')]

# package_dir["sas.sasgui.perspectives.fitting"] = os.path.join(
#     "src", "sas", "sasgui", "perspectives", "fitting")
# package_dir["sas.sasgui.perspectives.fitting.plugin_models"] = os.path.join(
#     "src", "sas", "sasgui", "perspectives", "fitting", "plugin_models")
# packages.extend(["sas.sasgui.perspectives.fitting",
#                  "sas.sasgui.perspectives.fitting.plugin_models"])
# package_data['sas.sasgui.perspectives.fitting'] = [
#     'media/*', 'plugin_models/*']

# packages.extend(["sas.sasgui.perspectives",
#                  "sas.sasgui.perspectives.calculator"])
# package_data['sas.sasgui.perspectives.calculator'] = ['images/*', 'media/*']

# package_dir["sas.sasgui.perspectives.corfunc"] = os.path.join(
#     "src", "sas", "sasgui", "perspectives", "corfunc")
# packages.extend(["sas.sasgui.perspectives.corfunc"])
# package_data['sas.sasgui.perspectives.corfunc'] = ['media/*']

# package_dir["sas.sasgui.perspectives.file_converter"] = os.path.join(
#     "src", "sas", "sasgui", "perspectives", "file_converter")
# packages.extend(["sas.sasgui.perspectives.file_converter"])
# package_data['sas.sasgui.perspectives.file_converter'] = ['media/*']

# Data util
package_dir["sas.sascalc.data_util"] = os.path.join(
    "src", "sas", "sascalc", "data_util")
packages.append("sas.sascalc.data_util")

# # Plottools
# package_dir["sas.sasgui.plottools"] = os.path.join(
#     "src", "sas", "sasgui", "plottools")
# packages.append("sas.sasgui.plottools")

# QTGUI
## UI
package_dir["sas.qtgui.UI"] = os.path.join(
    "src", "sas", "qtgui", "UI")
packages.append("sas.qtgui.UI")

## UnitTesting
package_dir["sas.qtgui.UnitTesting"] = os.path.join(
    "src", "sas", "qtgui", "UnitTesting")
packages.append("sas.qtgui.UnitTesting")

## Utilities
package_dir["sas.qtgui.Utilities"] = os.path.join(
    "src", "sas", "qtgui", "Utilities")
packages.append("sas.qtgui.Utilities")
package_dir["sas.qtgui.UtilitiesUI"] = os.path.join(
    "src", "sas", "qtgui", "Utilities","UI")
packages.append("sas.qtgui.Utilities.UI")

package_dir["sas.qtgui.Calculators"] = os.path.join(
    "src", "sas", "qtgui", "Calculators")
package_dir["sas.qtgui.Calculators.UI"] = os.path.join(
    "src", "sas", "qtgui", "Calculators", "UI")
packages.extend(["sas.qtgui.Calculators", "sas.qtgui.Calculators.UI"])

package_dir["sas.qtgui.MainWindow"] = os.path.join(
    "src", "sas", "qtgui", "MainWindow")
package_dir["sas.qtgui.MainWindow.UI"] = os.path.join(
    "src", "sas", "qtgui", "MainWindow", "UI")
packages.extend(["sas.qtgui.MainWindow", "sas.qtgui.MainWindow.UI"])

## Perspectives
package_dir["sas.qtgui.Perspectives"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives")
packages.append("sas.qtgui.Perspectives")

package_dir["sas.qtgui.Perspectives.Invariant"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Invariant")
package_dir["sas.qtgui.Perspectives.Invariant.UI"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Invariant", "UI")
packages.extend(["sas.qtgui.Perspectives.Invariant", "sas.qtgui.Perspectives.Invariant.UI"])

package_dir["sas.qtgui.Perspectives.Fitting"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Fitting")
package_dir["sas.qtgui.Perspectives.Fitting.UI"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Fitting", "UI")
packages.extend(["sas.qtgui.Perspectives.Fitting", "sas.qtgui.Perspectives.Fitting.UI"])

package_dir["sas.qtgui.Perspectives.Inversion"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Inversion")
package_dir["sas.qtgui.Perspectives.Inversion.UI"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Inversion", "UI")
packages.extend(["sas.qtgui.Perspectives.Inversion", "sas.qtgui.Perspectives.Inversion.UI"])

package_dir["sas.qtgui.Perspectives.Corfunc"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Corfunc")
package_dir["sas.qtgui.Perspectives.Corfunc.UI"] = os.path.join(
    "src", "sas", "qtgui", "Perspectives", "Corfunc", "UI")
packages.extend(["sas.qtgui.Perspectives.Corfunc", "sas.qtgui.Perspectives.Corfunc.UI"])

## Plotting
package_dir["sas.qtgui.Plotting"] = os.path.join(
    "src", "sas", "qtgui", "Plotting")
package_dir["sas.qtgui.Plotting.UI"] = os.path.join(
    "src", "sas", "qtgui", "Plotting", "UI")
package_dir["sas.qtgui.Plotting.Slicers"] = os.path.join(
    "src", "sas", "qtgui", "Plotting", "Slicers")
package_dir["sas.qtgui.Plotting.Masks"] = os.path.join(
    "src", "sas", "qtgui", "Plotting", "Masks")
packages.extend(["sas.qtgui.Plotting", "sas.qtgui.Plotting.UI",
                 "sas.qtgui.Plotting.Slicers", "sas.qtgui.Plotting.Masks"])

# # Last of the sas.models
# package_dir["sas.models"] = os.path.join("src", "sas", "models")
# packages.append("sas.models")

# Wojtek's hacky way to add doc files while bundling egg
# def add_doc_files(directory):
#    paths = []
#    for (path, directories, filenames) in os.walk(directory):
#        for filename in filenames:
#            paths.append(os.path.join(path, filename))
#    return paths

#doc_files = add_doc_files('doc')

# SasView
package_data['sas'] = ['logging.ini']
package_data['sas.sasview'] = ['images/*',
                               'media/*',
                               'test/*.txt',
                               'test/1d_data/*',
                               'test/2d_data/*',
                               'test/convertible_files/*',
                               'test/coordinate_data/*',
                               'test/image_data/*',
                               'test/media/*',
                               'test/other_files/*',
                               'test/save_states/*',
                               'test/sesans_data/*',
                               'test/upcoming_formats/*',
                               ]
packages.append("sas.sasview")
package_data['sas.qtgui'] = ['Calculators/UI/*',
                             'MainWindow/UI/*',
                             'Perspectives/Corfunc/UI/*',
                             'Perspectives/Fitting/UI/*',
                             'Perspectives/Invariant/UI/*',
                             'Perspectives/Inversion/UI/*',
                             'Plotting/UI/*',
                             'Utilities/UI/*',
                             'UI/*',
                             'UI/res/*',
                             ]
packages.append("sas.qtgui")

required = [
    'bumps>=0.7.5.9', 'periodictable>=1.5.0', 'pyparsing>=2.0.0',
    'lxml', 'h5py',

    # The following dependecies won't install automatically, so assume them
    # The numbers should be bumped up for matplotlib and wxPython as well.
    # 'numpy>=1.4.1', 'scipy>=0.7.2', 'matplotlib>=0.99.1.1',
    # 'wxPython>=2.8.11', 'pil',
]

if os.name == 'nt':
    required.extend(['html5lib', 'reportlab'])
else:
    # 'pil' is now called 'pillow'
    required.extend(['pillow'])

# Set up SasView
setup(
    name="sasview",
    version=VERSION,
    description="SasView application",
    author="SasView Team",
    author_email="developers@sasview.org",
    url="http://sasview.org",
    license="PSF",
    keywords="small-angle x-ray and neutron scattering analysis",
    download_url="https://github.com/SasView/sasview.git",
    package_dir=package_dir,
    packages=packages,
    package_data=package_data,
    ext_modules=ext_modules,
    install_requires=required,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            "sasview=sas.qtgui.MainWindow.MainWindow:run_sasview",
        ]
    },
    cmdclass={'docs': BuildSphinxCommand},
)
