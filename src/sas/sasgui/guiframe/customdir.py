# Setup and find Custom config dir
import sys
import imp
import os.path
import logging
import shutil

from sas.sasgui.guiframe.CategoryInstaller import CategoryInstaller
from sas.sasgui import get_user_dir, get_app_dir

def get_custom_config_path():
    dirname = os.path.join(get_user_dir(), 'config')
    # If the directory doesn't exist, create it
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    path = os.path.join(dirname, "custom_config.py")
    return path


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
        # if the custom config file does not exist, copy the default from
        # the app dir
        try:
            shutil.copyfile(os.path.join(get_app_dir(), "custom_config.py"),
                            path)
        except Exception:
            #import traceback; logging.error(traceback.format_exc())
            logging.error("Could not copy default custom config.")

    custom_config = _load_config(path)

    cat_file = CategoryInstaller.get_user_file()
    # If the user category file doesn't exist copy the default to
    # the user directory
    if not os.path.isfile(cat_file):
        try:
            default_cat_file = CategoryInstaller.get_default_file()
            if os.path.isfile(default_cat_file):
                shutil.copyfile(default_cat_file, cat_file)
            else:
                logging.error("Unable to find/copy default cat file")
        except Exception:
            logging.error("Unable to copy default cat file to the user dir.")

    return custom_config


def _load_config(path):
    if os.path.exists(path):
        try:
            fObj = None
            fObj, config_path, descr = imp.find_module('custom_config', [os.path.dirname(path)])
            custom_config = imp.load_module('custom_config', fObj, config_path, descr)
            logging.info("GuiManager loaded %s" % config_path)
            return custom_config
        except Exception:
            logging.error("Error loading %s: %s" % (path, sys.exc_value))
        finally:
            if fObj is not None:
                fObj.close()
    from sas.sasview import custom_config
    logging.info("GuiManager custom_config defaults to sas.sasview.custom_config")
    return custom_config
