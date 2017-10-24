__all__ = ['get_app_dir', 'get_user_dir',
           'get_local_config', 'get_custom_config']

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
        from ._config import find_app_dir
        _APP_DIR = find_app_dir()
    return _APP_DIR

_USER_DIR = None
def get_user_dir():
    """
    The directory where the per-user configuration is stored.

    Returns ~/.sasview, creating it if it does not already exist.
    """
    global _USER_DIR
    if not _USER_DIR:
        from ._config import make_user_dir
        _USER_DIR = make_user_dir()
    return _USER_DIR

def make_custom_config_path():
    from ._config import make_custom_config_path as _make_path
    return _make_path(get_user_dir())

_CUSTOM_CONFIG = None
def get_custom_config():
    """
    Setup the custom config dir and cat file
    """
    global _CUSTOM_CONFIG
    if not _CUSTOM_CONFIG:
        from ._config import setup_custom_config
        _CUSTOM_CONFIG = setup_custom_config(get_app_dir(), get_user_dir())
    return _CUSTOM_CONFIG


_LOCAL_CONFIG = None
def get_local_config():
    """
    Loads the local config file.
    """
    global _LOCAL_CONFIG
    if not _LOCAL_CONFIG:
        from ._config import load_local_config
        _LOCAL_CONFIG = load_local_config(get_app_dir())
    return _LOCAL_CONFIG
