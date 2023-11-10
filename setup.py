# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
    Setup for SasView
    TODO: Add checks to see that all the dependencies are on the system
"""

from typing import List
import os
import subprocess
import shutil
import sys

from setuptools import setup, Command, find_packages


# Manage version number
version_file = os.path.join("src", "sas", "system", "version.py")
with open(version_file) as fid:
    for line in fid:
        if line.startswith('__version__'):
            VERSION = line.split('"')[1]
            break
    else:
        raise ValueError(f"Could not find version in {version_file}")

CURRENT_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SASVIEW_BUILD = os.path.join(CURRENT_SCRIPT_DIR, "build")


# Optionally clean before build.
dont_clean = 'update' in sys.argv
if dont_clean:
    sys.argv.remove('update')
elif os.path.exists(SASVIEW_BUILD):
    print("Removing existing build directory", SASVIEW_BUILD, "for a clean build")
    shutil.rmtree(SASVIEW_BUILD)

# Class that manages the sphinx build stuff
class BuildSphinxCommand(Command):
    description = "Build Sphinx documentation."
    user_options = []

    def initialize_options(self):
        self.cwd = None

    def finalize_options(self):
        self.cwd = os.getcwd()

    def run(self):
        """
        First builds the sasmodels documentation if the directory
        is present. Then builds the sasview docs.
        """

        SASMODELS_DOCPATH = os.path.abspath(os.path.join(os.getcwd(), '..', 'sasmodels', 'doc'))
        print("========= check for sasmodels at", SASMODELS_DOCPATH, "============")
        if os.path.exists(SASMODELS_DOCPATH):
            if os.path.isdir(SASMODELS_DOCPATH):
                # if available, build sasmodels docs
                print("============= Building sasmodels model documentation ===============")
                try:
                    smdocbuild = subprocess.call([
                        "make",
                        "PYTHON=%s" % sys.executable,
                        "-C", SASMODELS_DOCPATH,
                        "html"
                    ])
                except Exception as e:
                    print(e)
                    print("build failed, maybe you don't have make")
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

print(sys.argv)

# determine if this run requires building of Qt GUI ui->py
build_qt = any(c in sys.argv for c in build_commands)
force_rebuild = "-f" if 'rebuild_ui' in sys.argv or 'clean' in sys.argv else ""
if 'rebuild_ui' in sys.argv:
    sys.argv.remove('rebuild_ui')

if build_qt:
    _ = subprocess.call([sys.executable, "src/sas/qtgui/convertUI.py", force_rebuild])


# Required packages
required = [
    'bumps>=0.7.5.9', 'periodictable>=1.5.0', 'pyparsing>=2.0.0',
    'lxml',
]

if os.name == 'nt':
    required.extend(['html5lib', 'reportlab'])
else:
    # 'pil' is now called 'pillow'
    required.extend(['pillow'])

# Run setup
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
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    ext_modules=[],
    install_requires=required,
    zip_safe=False,
    include_package_data=True,
    entry_points={
        'console_scripts': [
            "sasview=sas.qtgui.MainWindow.MainWindow:run_sasview",
        ]
    },
    cmdclass={'docs': BuildSphinxCommand},
)
