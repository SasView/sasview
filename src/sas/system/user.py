import os
import shutil
from pathlib import Path
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

PATH_TYPE = [Path, os.path, str]


def get_dir_and_create_if_needed(path: PATH_TYPE, create_if_nonexistent: bool = True):
    if create_if_nonexistent and not os.path.exists(path):
        os.makedirs(path, mode=777, exist_ok=True)
    return path


def _get_user_dir(create_if_nonexistent: bool = False) -> PATH_TYPE:
    """**DEPRECATED** Do not use this function to create new files. This is only used to move files from previous
    version locations to new locations
    """
    global _USER_DIR
    return get_dir_and_create_if_needed(_USER_DIR, create_if_nonexistent)


def get_config_dir(create_if_nonexistent: bool = True) -> PATH_TYPE:
    """
    The directory where os-specific configurations are stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _CONFIG_DIR
    return get_dir_and_create_if_needed(_CONFIG_DIR, create_if_nonexistent)


def get_app_dir(create_if_nonexistent: bool = True) -> PATH_TYPE:
    """
    The directory where the os-specific app data is stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _APP_DATA_DIR
    return get_dir_and_create_if_needed(_APP_DATA_DIR, create_if_nonexistent)


def get_app_dir_versioned(create_if_nonexistent: bool = True) -> PATH_TYPE:
    """
    The directory where the os-specific app data is stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _APP_VERS_DIR
    return get_dir_and_create_if_needed(_APP_VERS_DIR, create_if_nonexistent)


def get_log_dir(create_if_nonexistent: bool = True) -> PATH_TYPE:
    """
    The directory where the os-specific logs are stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _LOG_DIR
    return get_dir_and_create_if_needed(_LOG_DIR, create_if_nonexistent)


def get_cache_dir(create_if_nonexistent: bool = True) -> PATH_TYPE:
    """
    The directory where the os-specific cache is stored.

    Returns the directory string, creating it if it does not already exist.
    """
    global _CACHE_DIR
    return get_dir_and_create_if_needed(_CACHE_DIR, create_if_nonexistent)


def get_plugin_dir(create_if_nonexistent: bool = True) -> PATH_TYPE:
    """
    The directory where the os-specific cache is stored.

    Returns the directory string, creating it if it does not already exist.
    """
    app_dir = get_app_dir(create_if_nonexistent)
    return get_dir_and_create_if_needed(Path(app_dir, 'plugin_models'), create_if_nonexistent)


def copy_old_files_to_new_location():
    """Run at startup, check to see if files in the old locations exist and move them if they haven't already."""
    # Copy the old log to the new location
    user_dir = Path(_get_user_dir())
    old_sasview_usr_dir = user_dir / '.sasview'
    old_log = user_dir / 'sasview.log'
    new_log = Path(get_log_dir()) / 'sasview.log'
    if old_log.exists() and not new_log.exists():
        shutil.copy2(old_log, new_log)
    # Copy plugin models to new location
    old_plugins = old_sasview_usr_dir / 'plugin_models'
    new_plugins = Path(get_plugin_dir())
    if old_plugins.exists():
        files = [f for f in os.listdir(old_plugins) if os.path.isfile(os.path.join(old_plugins, f))]
        for file in files:
            if not Path(new_plugins, file).exists():
                shutil.copy2(Path(old_plugins, file), Path(new_plugins, file))
    # Copy config file over
    new_config_dir = Path(get_config_dir())
    config_name = f'config-{sasview_version.split(".")[0]}'
    old_config = old_sasview_usr_dir / config_name
    new_config = new_config_dir / config_name
    print(old_config.exists())
    if not new_config.exists() and old_config.exists():
        shutil.copy2(old_config, new_config)
