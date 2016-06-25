import os

# Set up config directories
def make_user_folder():
    path = os.path.join(os.path.expanduser("~"),'.sasview')
    if not os.path.exists(path):
        os.mkdir(path)
    return path

def find_app_folder():
    # If the directory containing sasview.py exists, then we are not running
    # frozen and the current path is the app path.
    root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    path = os.path.join(root, 'sasview')
    if os.path.exists(path):
        return path

    # If we are running frozen, then skip from:
    #    library.zip/sas/sasview
    path = os.path.dirname(os.path.dirname(root))
    return path

USER_FOLDER = make_user_folder()
APP_FOLDER = find_app_folder()



def get_app_dir():
    if APP_FOLDER is None:
        raise RuntimeError("Need to initialize sas.sasgui.USER_FOLDER")
    return APP_FOLDER

def get_user_dir():
    if USER_FOLDER is None:
        raise RuntimeError("Need to initialize sas.sasgui.USER_FOLDER")
    return USER_FOLDER

_config_cache = None
def get_local_config():
    global _config_cache
    if not _config_cache:
        _config_cache = _load_config()
    return _config_cache

def _load_config():
    import os
    import sys
    import imp
    import logging

    dirname = get_app_dir()
    filename = 'local_config.py'
    path = os.path.join(dirname, filename)
    if os.path.exists(path):
        try:
            fObj = None
            fObj, config_path, descr = imp.find_module('local_config', [APP_FOLDER])
            config = imp.load_module('local_config', fObj, config_path, descr)
            logging.info("GuiManager loaded %s" % config_path)
            return config
        except Exception:
            import traceback; logging.error(traceback.format_exc())
            logging.error("Error loading %s: %s" % (path, sys.exc_value))
        finally:
            if fObj is not None:
                fObj.close()
    from sas.sasgui.guiframe import config
    logging.info("GuiManager config defaults to sas.sasgui.guiframe")
    return config
