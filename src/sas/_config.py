# Setup and find Custom config dir
from __future__ import print_function

import sys
import os
from os.path import exists, expanduser, dirname, realpath, join as joinpath
import logging
import shutil

from sasmodels.custom import load_module_from_path

logger = logging.getLogger(__name__)

def dirn(path, n):
    """
    Return the directory n up from the current path
    """
    path = realpath(path)
    for _ in range(n):
        path = dirname(path)
    return path

def find_app_dir():
    """
    Locate the parent directory of the sasview resources.  For the normal
    application this will be the directory containing sasview.py.  For the
    frozen application this will be the path where the resources are installed.
    """
    # We are starting out with the following info:
    #     __file__ = .../sas/__init__.pyc
    # Check if the path .../sas/sasview exists, and use it as the
    # app directory.  This will only be the case if the app is not frozen.
    path = joinpath(dirname(__file__), 'sasview')
    if exists(path):
        return path

    # If we are running frozen, then root is a parent directory
    if sys.platform == 'darwin':
        # Here is the path to the file on the mac:
        #     .../Sasview.app/Contents/Resources/lib/python2.7/site-packages.zip/sas/__init__.pyc
        # We want the path to the Resources directory.
        path = dirn(__file__, 5)
    elif os.name == 'nt':
        # Here is the path to the file on windows:
        #     ../Sasview/library.zip/sas/__init__.pyc
        # We want the path to the Sasview directory.
        path = dirn(__file__, 3)
    else:
        raise RuntimeError("Couldn't find the app directory")
    return path

def make_user_dir():
    """
    Create the user directory ~/.sasview if it doesn't already exist.
    """
    path = joinpath(expanduser("~"),'.sasview')
    if not exists(path):
        os.mkdir(path)
    return path

def load_local_config(app_dir):
    logger = logging.getLogger(__name__)
    filename = 'local_config.py'
    path = os.path.join(app_dir, filename)
    try:
        module = load_module_from_path('sas.local_config', path)
        #logger.info("GuiManager loaded %s", path)
        return module
    except Exception as exc:
        #logger.critical("Error loading %s: %s", path, exc)
        sys.exit()

def make_custom_config_path(user_dir):
    """
    The location of the cusstom config file.

    Returns ~/.sasview/config/custom_config.py
    """
    dirname = os.path.join(user_dir, 'config')
    # If the directory doesn't exist, create it
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    path = os.path.join(dirname, "custom_config.py")
    return path

def setup_custom_config(app_dir, user_dir):
    path = make_custom_config_path(user_dir)
    if not os.path.isfile(path):
        try:
            # if the custom config file does not exist, copy the default from
            # the app dir
            shutil.copyfile(os.path.join(app_dir, "custom_config.py"), path)
        except Exception:
            logger.error("Could not copy default custom config.")

    #Adding SAS_OPENCL if it doesn't exist in the config file
    # - to support backcompability
    if not "SAS_OPENCL" in open(path).read():
        try:
            open(config_file, "a+").write("SAS_OPENCL = \"None\"\n")
        except Exception:
            logger.error("Could not update custom config with SAS_OPENCL.")

    custom_config = load_custom_config(path)
    return custom_config


def load_custom_config(path):
    if os.path.exists(path):
        try:
            module = load_module_from_path('sas.custom_config', path)
            #logger.info("GuiManager loaded %s", path)
            return module
        except Exception as exc:
            logger.error("Error loading %s: %s", path, exc)

    from sas.sasview import custom_config
    logger.info("GuiManager custom_config defaults to sas.sasview.custom_config")
    return custom_config