import sys
import os
from os.path import exists, expanduser, dirname, realpath, join as joinpath


def dirn(path, n):
    path = realpath(path)
    for _ in range(n):
        path = dirname(path)
    return path

# Set up config directories
def make_user_folder():
    path = joinpath(expanduser("~"),'.sasview')
    if not exists(path):
        os.mkdir(path)
    return path


def find_app_folder():
    # We are starting out with the following info:
    #     __file__ = .../sas/sasgui/__init__.pyc
    # Check if the sister path .../sas/sasview exists, and use it as the
    # app directory.  This will only be the case if the app is not frozen.
    path = joinpath(dirn(__file__, 2), 'sasview')
    if exists(path):
        return path

    # If we are running frozen, then root is a parent directory
    if sys.platform == 'darwin':
        # Here is the path to the file on the mac:
        #     .../Sasview.app/Contents/Resources/lib/python2.7/site-packages.zip/sas/sasgui/__init__.pyc
        # We want the path to the Resources directory.
        path = dirn(__file__, 6)
    elif os.name == 'nt':
        # Here is the path to the file on windows:
        #     ../Sasview/library.zip/sas/sasgui/__init__.pyc
        # We want the path to the Sasview directory.
        path = dirn(__file__, 4)
    else:
        raise RuntimeError("Couldn't find the app directory")
    return path

USER_FOLDER = make_user_folder()
APP_FOLDER = find_app_folder()


def get_app_dir():
    return APP_FOLDER

def get_user_dir():
    return USER_FOLDER

def get_custom_config_path():
    dirname = os.path.join(get_user_dir(), 'config')
    # If the directory doesn't exist, create it
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    path = os.path.join(dirname, "custom_config.py")
    return path

_config_cache = None
def get_local_config():
    global _config_cache
    if not _config_cache:
        _config_cache = _load_config()
    return _config_cache

def _load_config():
    import os
    import sys
    import logging
    from sasmodels.custom import load_module_from_path

    logger = logging.getLogger(__name__)
    dirname = get_app_dir()
    filename = 'local_config.py'
    path = os.path.join(dirname, filename)
    try:
        module = load_module_from_path('sas.sasgui.local_config', path)
        logger.info("GuiManager loaded %s", path)
        return module
    except Exception as exc:
        logger.critical("Error loading %s: %s", path, exc)
        sys.exit()
