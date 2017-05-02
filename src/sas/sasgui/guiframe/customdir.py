# Setup and find Custom config dir
import os.path
import logging
import shutil
import imp

from sas.sasgui import get_custom_config_path

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
    try:
        if not os.path.isfile(path):
            # if the custom config file does not exist, copy the default from
            # the app dir
            shutil.copyfile(os.path.join(get_app_dir(), "custom_config.py"),
                            path)
        #Adding SAS_OPENCL if it doesn't exist in the config file
        # - to support backcompability
        if not "SAS_OPENCL" in open(path).read():
            open(config_file, "a+").write("SAS_OPENCL = \"None\"\n")
    except Exception:
        #import traceback; logging.error(traceback.format_exc())
        logger.error("Could not copy default custom config.")

    custom_config = _load_config(path)
    return custom_config

def _load_config(path):
    if os.path.exists(path):
        try:
            fObj = None
            fObj, config_path, descr = imp.find_module('custom_config', [os.path.dirname(path)])
            custom_config = imp.load_module('custom_config', fObj, config_path, descr)
            logger.info("GuiManager loaded %s" % config_path)
            return custom_config
        except Exception:
            logger.error("Error loading %s: %s" % (path, sys.exc_value))
        finally:
            if fObj is not None:
                fObj.close()
    from sas.sasview import custom_config
    logging.info("GuiManager custom_config defaults to sas.sasview.custom_config")
    return custom_config
