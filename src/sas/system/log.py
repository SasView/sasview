from __future__ import print_function

import logging
import logging.config
import os
import sys
import os.path

import importlib.resources

'''
Module that manages the global logging
'''

#BASE_LOGGER = 'sasview'
TRACED_PACKAGES = ('sas', 'sasmodels', 'sasdata', 'bumps', 'periodictable')
IGNORED_PACKAGES = {
    'matplotlib': 'ERROR',
    'numba': 'WARN',
    'h5py': 'ERROR',
    'ipykernel': 'CRITICAL',
}

def setup_logging(level=logging.INFO):
    # Setup the defaults
    logging.captureWarnings(True)
    for package in TRACED_PACKAGES:
        logging.getLogger(package).setLevel(level)
    for package, package_level in IGNORED_PACKAGES.items():
        logging.getLogger(package).setLevel(package_level)

    # SasView is often using the root logger to emit error messages. Until
    # that is fixed we need to set the level of the root logger to the target
    # level. Unfortunately that means that all broken third party packages
    # (i.e., those that use the root logger rather than __name__) will also
    # be set to that level, which is why we have to explicitly override them
    # with the 'IGNORED_PACKAGES' list. The following regex will find most of
    # the culprits:
    #    grep -R "logg\(ing\|er\)" src | grep -v .pyc | less
    # TODO: use __name__ as the logger for all sasview log messages
    logging.root.setLevel(level)

    # Apply the logging config after setting the defaults
    try:
        fd = importlib.resources.open_text('sas.system', 'log.ini')
        logging.config.fileConfig(fd)
    except FileNotFoundError:
        print(f"ERROR: Log config '{fd.name}' not found...", file=sys.stderr)

    #print_config()

def production():
    setup_logging('INFO')

def development():
    setup_logging('DEBUG')

def print_config(msg="Logger config:"):
    """
    When debugging the logging configuration it is handy to see exactly how
    it is configured. To do so you will need to pip install the logging_tree
    package and add *log.print_config()* at choice points in the code.
    """
    try:
        from logging_tree import printout
    except ImportError:
        print("log.print_config requires the logging_tree package from PyPI")
        return
    print(msg)
    printout()
