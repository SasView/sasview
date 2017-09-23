# Setup and find Custom config dir
from __future__ import print_function

import os.path
import logging
import shutil

from sasmodels.custom import load_module_from_path

from sas.sasgui import get_custom_config_path, get_app_dir

logger = logging.getLogger(__name__)

_config_cache = None
def setup_custom_config():
    """
    Setup the custom config dir and cat file
    """
    global _config_cache
    if not _config_cache:
        _config_cache = _setup_custom_config()
    return _config_cache


def _setup_custom_config():
    path = get_custom_config_path()
    if not os.path.isfile(path):
        try:
            # if the custom config file does not exist, copy the default from
            # the app dir
            shutil.copyfile(os.path.join(get_app_dir(), "custom_config.py"),
                            path)
        except Exception:
            logger.error("Could not copy default custom config.")

    #Adding SAS_OPENCL if it doesn't exist in the config file
    # - to support backcompability
    if not "SAS_OPENCL" in open(path).read():
        try:
            open(config_file, "a+").write("SAS_OPENCL = \"None\"\n")
        except Exception:
            logger.error("Could not update custom config with SAS_OPENCL.")

    custom_config = _load_config(path)
    return custom_config


def _load_config(path):
    if os.path.exists(path):
        try:
            module = load_module_from_path('sas.sasview.custom_config', path)
            logger.info("GuiManager loaded %s", path)
            return module
        except Exception as exc:
            logger.error("Error loading %s: %s", path, exc)

    from sas.sasview import custom_config
    logger.info("GuiManager custom_config defaults to sas.sasview.custom_config")
    return custom_config
