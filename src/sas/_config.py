# Setup and find Custom config_system dir
from __future__ import print_function

import sys
import os
from os.path import exists, expanduser, dirname, realpath, join as joinpath
import logging
import shutil

from sasmodels.custom import load_module_from_path

logger = logging.getLogger(__name__)


def make_custom_config_path(user_dir):
    """
    The location of the cusstom config_system file.

    Returns ~/.sasview/config_system/custom_config.py
    """
    dirname = os.path.join(user_dir, 'config_system')
    # If the directory doesn't exist, create it
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    path = os.path.join(dirname, "custom_config.py")
    return path

def setup_custom_config(app_dir, user_dir):
    path = make_custom_config_path(user_dir)
    if not os.path.isfile(path):
        try:
            # if the custom config_system file does not exist, copy the default from
            # the app dir
            shutil.copyfile(os.path.join(app_dir, "custom_config.py"), path)
        except Exception:
            logger.error("Could not copy default custom config_system.")

    #Adding SAS_OPENCL if it doesn't exist in the config_system file
    # - to support backcompability
    if not "SAS_OPENCL" in open(path).read():
        try:
            open(path, "a+").write("SAS_OPENCL = \"None\"\n")
        except Exception:
            logger.error("Could not update custom config_system with SAS_OPENCL.")

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