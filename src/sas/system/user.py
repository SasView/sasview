import os
from platformdirs import PlatformDirs
from sas.system.version import __version__ as sasview_version

# Create separate versioned and unversioned file locations
PLATFORM_DIRS_VERSIONED = PlatformDirs("SasView", "sasview", version=sasview_version)
PLATFORM_DIRS_UNVERSIONED = PlatformDirs("SasView", "sasview")
# Deprecated path
_USER_DIR = Path(os.path.join(os.path.expanduser("~")))
# OS agnostic pathing
_APP_DATA_DIR = PLATFORM_DIRS_UNVERSIONED.user_data_dir
_APP_VERS_DIR = PLATFORM_DIRS_VERSIONED.user_data_dir
_CACHE_DIR = PLATFORM_DIRS_VERSIONED.user_cache_dir
_CONFIG_DIR = PLATFORM_DIRS_UNVERSIONED.user_config_dir
_LOG_DIR = PLATFORM_DIRS_UNVERSIONED.user_log_dir
_CACHE_DIR = PLATFORM_DIRS_VERSIONED.user_cache_dir


def get_dir_and_create_if_needed(dir, create_if_nonexistent=True, ):
    if create_if_nonexistent and not os.path.exists(dir):
        os.makedirs(dir, mode=777, exist_ok=True)
    return dir


def get_user_dir(create_if_nonexistent=False):
    """**DEPRECATED** Do not use this function to create new files. This is only used to move files from previous
    version locations to new locations
    """
    global _USER_DIR
    return get_dir_and_create_if_needed(create_if_nonexistent, _USER_DIR)


def get_config_dir(create_if_nonexistent=True):
    """
    The directory where os-specific configurations are stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _CONFIG_DIR
    return get_dir_and_create_if_needed(create_if_nonexistent, _CONFIG_DIR)


def get_app_dir(create_if_nonexistent=True):
    """
    The directory where the os-specific app data is stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _APP_DATA_DIR
    return get_dir_and_create_if_needed(create_if_nonexistent, _APP_DATA_DIR)


def get_log_dir(create_if_nonexistent=True):
    """
    The directory where the os-specific logs are stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _LOG_DIR
    return get_dir_and_create_if_needed(create_if_nonexistent, _LOG_DIR)


def get_cache_dir(create_if_nonexistent=True):
    """
    The directory where the os-specific cache is stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _CACHE_DIR
    return get_dir_and_create_if_needed(create_if_nonexistent, _CACHE_DIR)


def copy_old_user_files_to_new_locations():
    # TODO: Should we copy previous items over? Also, should plugin and compiled models be
    old_user_dir = get_user_dir()
    if os.path.exists(old_user_dir):
        log_location = get_log_dir()
        config_location = get_config_dir()
    # TODO: copy plugin models, config files, and
    pass
