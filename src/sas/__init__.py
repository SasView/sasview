
import os
import sys
from sas.config_system import configuration as config

__all__ = ['get_app_dir', 'get_user_dir', 'config']
__version__ = "5.0.5"

# Load the config file
config.load()


_APP_DIR = None
def get_app_dir():
    """
    The directory where the sasview application is found.

    Returns the path to sasview if running in place or installed with setup.
    If the application is frozen, returns the parent directory of the
    application resources such as test files and images.
    """
    global _APP_DIR
    if not _APP_DIR:
        _APP_DIR = find_app_dir()
    return _APP_DIR

# TODO: Replace with more idomatic version
def dirn(path, n):
    """
    Return the directory n up from the current path
    """
    path = os.path.realpath(path)
    for _ in range(n):
        path = os.path.dirname(path)
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
    path = os.path.join(os.path.dirname(__file__), 'sasview')
    if os.path.exists(path):
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
    path = os.path.join(os.path.expanduser("~"),'.sasview')
    if not os.path.exists(path):
        os.mkdir(path)
    return path


_USER_DIR = None
def get_user_dir():
    """
    The directory where the per-user configuration is stored.

    Returns ~/.sasview, creating it if it does not already exist.
    """
    global _USER_DIR
    if not _USER_DIR:
        _USER_DIR = make_user_dir()
    return _USER_DIR
