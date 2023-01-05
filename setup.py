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

from setuptools import setup, Command

# Manage version number ######################################
version_file = os.path.join("src", "sas", "system", "version.py")
with open(version_file) as fid:
    for line in fid:
        if line.startswith('__version__'):
            VERSION = line.split('"')[1]
            break
    else:
        raise ValueError(f"Could not find version in {version_file}")
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

# # TODO: build step should not be messing with existing installation!!
# sas_dir = os.path.join(os.path.expanduser("~"), '.sasview')
# if os.path.isdir(sas_dir):
#     f_path = os.path.join(sas_dir, "sasview.log")
#     if os.path.isfile(f_path):
#         os.remove(f_path)
#     #f_path = os.path.join(sas_dir, "categories.json")
#     #if os.path.isfile(f_path):
#     #    os.remove(f_path)
#     f_path = os.path.join(sas_dir, 'sasview', "custom_config.py")
#     if os.path.isfile(f_path):
#         os.remove(f_path)
#     #f_path = os.path.join(sas_dir, 'plugin_models')
#     # if os.path.isdir(f_path):
#     #     for f in os.listdir(f_path):
#     #         if f in plugin_model_list:
#     #             file_path =  os.path.join(f_path, f)
#     #             os.remove(file_path)


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


# _standard_ commands which should trigger the Qt build
build_commands = [
    'install', 'build', 'build_py', 'bdist', 'bdist_egg', 'bdist_rpm',
    'bdist_wheel', 'develop', 'test'
]
# determine if this run requires building of Qt GUI ui->py
build_qt = any(c in sys.argv for c in build_commands)

if build_qt:
    _ = subprocess.call([sys.executable, "src/sas/sasview/convertUI.py"])

# sas module
package_dir["sas"] = os.path.join("src", "sas")
packages.append("sas")

# sas module
# qt module
package_dir["sas.sasview"] = os.path.join("src", "sas", "sasview")
packages.append("sas.sasview")

# sas module
package_dir["sas.sascalc"] = os.path.join("src", "sas", "sascalc")
packages.append("sas.sascalc")

# sas.sascalc.invariant
package_dir["sas.sascalc.invariant"] = os.path.join(
    "src", "sas", "sascalc", "invariant")
packages.extend(["sas.sascalc.invariant"])


# sas.sascalc.calculator
package_dir["sas.sascalc.calculator"] = os.path.join(
    "src", "sas", "sascalc", "calculator")
packages.append("sas.sascalc.calculator")


# sas.sascalc.pr
package_dir["sas.sascalc.pr"] = os.path.join("src", "sas", "sascalc", "pr")
packages.append("sas.sascalc.pr")

# sas.sascalc.corfunc
package_dir["sas.sascalc.corfunc"] = os.path.join(
    "src", "sas", "sascalc", "corfunc")
packages.append("sas.sascalc.corfunc")

# sas.sascalc.fit
package_dir["sas.sascalc.fit"] = os.path.join("src", "sas", "sascalc", "fit")
packages.append("sas.sascalc.fit")

# Data util
package_dir["sas.sascalc.data_util"] = os.path.join(
    "src", "sas", "sascalc", "data_util")
packages.append("sas.sascalc.data_util")

# sasview
## UI
package_dir["sas.sasview.UI"] = os.path.join(
    "src", "sas", "sasview", "UI")
packages.append("sas.sasview.UI")

## UnitTesting
package_dir["sas.sasview.UnitTesting"] = os.path.join(
    "src", "sas", "sasview", "UnitTesting")
packages.append("sas.sasview.UnitTesting")

## Utilities
package_dir["sas.sasview.Utilities"] = os.path.join(
    "src", "sas", "sasview", "Utilities")
packages.append("sas.sasview.Utilities")
package_dir["sas.sasview.Utilities.UI"] = os.path.join(
    "src", "sas", "sasview", "Utilities", "UI")
packages.append("sas.sasview.Utilities.UI")

package_dir["sas.sasview.Utilities.Reports"] = os.path.join(
    "src", "sas", "sasview", "Utilities", "Reports")
packages.append("sas.sasview.Utilities.Reports")
package_dir["sas.sasview.Utilities.Reports.UI"] = os.path.join(
    "src", "sas", "sasview", "Utilities", "Reports", "UI")
packages.append("sas.sasview.Utilities.Reports.UI")

package_dir["sas.sasview.Utilities.Preferences}"] = os.path.join(
    "src", "sas", "sasview", "Utilities", "Preferences")
packages.append("sas.sasview.Utilities.Preferences")
package_dir["sas.sasview.Utilities.Preferences.UI"] = os.path.join(
    "src", "sas", "sasview", "Utilities", "Preferences", "UI")
packages.append("sas.sasview.Utilities.Preferences.UI")

package_dir["sas.sasview.Calculators"] = os.path.join(
    "src", "sas", "sasview", "Calculators")
package_dir["sas.sasview.Calculators.UI"] = os.path.join(
    "src", "sas", "sasview", "Calculators", "UI")
packages.extend(["sas.sasview.Calculators", "sas.sasview.Calculators.UI"])

package_dir["sas.sasview.MainWindow"] = os.path.join(
    "src", "sas", "sasview", "MainWindow")
package_dir["sas.sasview.MainWindow.UI"] = os.path.join(
    "src", "sas", "sasview", "MainWindow", "UI")
packages.extend(["sas.sasview.MainWindow", "sas.sasview.MainWindow.UI"])

## Perspectives
package_dir["sas.sasview.Perspectives"] = os.path.join(
    "src", "sas", "sasview", "Perspectives")
packages.append("sas.sasview.Perspectives")

package_dir["sas.sasview.Perspectives.Invariant"] = os.path.join(
    "src", "sas", "sasview", "Perspectives", "Invariant")
package_dir["sas.sasview.Perspectives.Invariant.UI"] = os.path.join(
    "src", "sas", "sasview", "Perspectives", "Invariant", "UI")
packages.extend(["sas.sasview.Perspectives.Invariant", "sas.sasview.Perspectives.Invariant.UI"])

package_dir["sas.sasview.Perspectives.Fitting"] = os.path.join(
    "src", "sas", "sasview", "Perspectives", "Fitting")
package_dir["sas.sasview.Perspectives.Fitting.UI"] = os.path.join(
    "src", "sas", "sasview", "Perspectives", "Fitting", "UI")
packages.extend(["sas.sasview.Perspectives.Fitting", "sas.sasview.Perspectives.Fitting.UI"])

package_dir["sas.sasview.Perspectives.Inversion"] = os.path.join(
    "src", "sas", "sasview", "Perspectives", "Inversion")
package_dir["sas.sasview.Perspectives.Inversion.UI"] = os.path.join(
    "src", "sas", "sasview", "Perspectives", "Inversion", "UI")
packages.extend(["sas.sasview.Perspectives.Inversion", "sas.sasview.Perspectives.Inversion.UI"])

package_dir["sas.sasview.Perspectives.Corfunc"] = os.path.join(
    "src", "sas", "sasview", "Perspectives", "Corfunc")
package_dir["sas.sasview.Perspectives.Corfunc.UI"] = os.path.join(
    "src", "sas", "sasview", "Perspectives", "Corfunc", "UI")
packages.extend(["sas.sasview.Perspectives.Corfunc", "sas.sasview.Perspectives.Corfunc.UI"])


package_dir["sas.sasview.images"] = os.path.join(
    "src", "sas", "sasview", "images")
packages.append("sas.sasview.images")

## Plotting
package_dir["sas.sasview.Plotting"] = os.path.join(
    "src", "sas", "sasview", "Plotting")
package_dir["sas.sasview.Plotting.UI"] = os.path.join(
    "src", "sas", "sasview", "Plotting", "UI")
package_dir["sas.sasview.Plotting.Slicers"] = os.path.join(
    "src", "sas", "sasview", "Plotting", "Slicers")
package_dir["sas.sasview.Plotting.Masks"] = os.path.join(
    "src", "sas", "sasview", "Plotting", "Masks")
packages.extend(["sas.sasview.Plotting", "sas.sasview.Plotting.UI",
                 "sas.sasview.Plotting.Slicers", "sas.sasview.Plotting.Masks"])

# SasView
package_data['sas.sasview'] = ['media/*']

package_data["sas.example_data"] = [
                               '*.txt',
                               '1d_data/*',
                               '2d_data/*',
                               'convertible_files/*',
                               'coordinate_data/*',
                               'image_data/*',
                               'media/*',
                               'other_files/*',
                               'save_states/*',
                               'sesans_data/*',
                               'upcoming_formats/*',
                               ]
packages.append("sas.sasview")

package_data["sas.system"] = ["*",
                              "config/*"]
packages.append("sas.system")

package_data['sas.sasview'] = ['images/*',
                             'Calculators/UI/*',
                             'MainWindow/UI/*',
                             'Perspectives/Corfunc/UI/*',
                             'Perspectives/Fitting/UI/*',
                             'Perspectives/Invariant/UI/*',
                             'Perspectives/Inversion/UI/*',
                             'Plotting/UI/*',
                             'Utilities/UI/*',
                             'Utilities/Reports/UI/*',
                             'Utilities/Reports/*.css',
                             'Utilities/Preferences/UI/*',
                             'UI/*',
                             'UI/res/*',
                             ]
packages.append("sas.sasview")


required = [
    'bumps>=0.7.5.9', 'periodictable>=1.5.0', 'pyparsing>=2.0.0',
    'lxml', 'h5py',
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
            "sasview=sas.sasview.MainWindow.MainWindow:run_sasview",
        ]
    },
    cmdclass={'docs': BuildSphinxCommand},
)
