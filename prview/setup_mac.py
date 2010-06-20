"""
    Setup script to build a Mac app
"""
from setuptools import setup

APP = ['PrView.py']
DATA_FILES = ['images', 'test']
OPTIONS = {'argv_emulation': True,
           #'plist': dict(LSPrefersPPC=True)
           }

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
