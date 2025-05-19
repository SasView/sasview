import os
from packaging.version import Version
import shutil
from pathlib import Path
from platformdirs import PlatformDirs
from sas.system.version import __version__


sasview_version = Version(__version__).base_version

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


def get_dir_and_create_if_needed(path: PATH_TYPE, create_if_nonexistent: bool = True) -> Path:
    """Returns the requested directory as a pathlib.Path object, creating the directory if it does not already exist."""
    path = Path(path)
    if create_if_nonexistent and not os.path.exists(path):
        path.mkdir(parents=True, exist_ok=True)
    return path


def _get_user_dir(create_if_nonexistent: bool = False) -> Path:
    """**DEPRECATED** Do not use this function to create new files.

    v6.1.0: This is only used to move files from previous version locations to new locations
    """
    global _USER_DIR
    return get_dir_and_create_if_needed(_USER_DIR, create_if_nonexistent)


def get_config_dir(create_if_nonexistent: bool = True) -> Path:
    """The directory where os-specific configurations are stored.

    Returns the directory as a pathlib.Path object, creating the directory if it does not already exist.
    """
    global _CONFIG_DIR
    return get_dir_and_create_if_needed(_CONFIG_DIR, create_if_nonexistent)


def get_app_dir(create_if_nonexistent: bool = True) -> Path:
    """The directory where the os-specific app data is stored.

    Returns the directory as a pathlib.Path object, creating the directory if it does not already exist.
    """
    global _APP_DATA_DIR
    return get_dir_and_create_if_needed(_APP_DATA_DIR, create_if_nonexistent)


def get_app_dir_versioned(create_if_nonexistent: bool = True) -> Path:
    """The directory where the version-dependent, os-specific app data is stored.

    Returns the directory as a pathlib.Path object, creating the directory if it does not already exist.
    """
    global _APP_VERS_DIR
    return get_dir_and_create_if_needed(_APP_VERS_DIR, create_if_nonexistent)


def get_log_dir(create_if_nonexistent: bool = True) -> Path:
    """The directory where the os-specific logs are stored.

    Returns the directory as a pathlib.Path object, creating the directory if it does not already exist.
    """
    global _LOG_DIR
    return get_dir_and_create_if_needed(_LOG_DIR, create_if_nonexistent)


def get_cache_dir(create_if_nonexistent: bool = True) -> Path:
    """The directory where the os-specific cache is stored.

    Returns the directory as a pathlib.Path object, creating the directory if it does not already exist.
    """
    global _CACHE_DIR
    return get_dir_and_create_if_needed(_CACHE_DIR, create_if_nonexistent)


def get_plugin_dir(create_if_nonexistent: bool = True) -> Path:
    """The directory where the os-specific cache for plugin models is stored.

    Returns the directory as a pathlib.Path object, creating the directory if it does not already exist.
    """
    app_dir = get_app_dir(create_if_nonexistent)
    return get_dir_and_create_if_needed(Path(app_dir, 'plugin_models'), create_if_nonexistent)


def copy_old_files_to_new_location():
    """**Only run at app startup**
    A check to see if files in the old user locations exist and move them if they haven't already been moved."""

    # Get the user directory location and original .sasview directory
    user_dir = Path(_get_user_dir())
    old_sasview_usr_dir = user_dir / '.sasview'

    # Values used multiple times that need to be defined
    config_name = f'config-{sasview_version.split(".")[0]}'
    old_plugins = old_sasview_usr_dir / 'plugin_models'
    if old_plugins.exists():
        plugin_files = [f for f in os.listdir(old_plugins) if os.path.isfile(os.path.join(old_plugins, f))]
    else:
        plugin_files = []

    # Create a dictionary mapping old file locations to their respective new locations and populate it with
    #  the log and config file locations.
    location_map = {
        user_dir / 'sasview.log': Path(get_log_dir()) / 'sasview.log',  # Log file
        old_sasview_usr_dir / config_name: Path(get_config_dir()) / config_name  # Configuration file
    }
    # Add any existing plugin files
    location_map.update({old_plugins / f_name: Path(get_plugin_dir()) / f_name for f_name in plugin_files})

    # Iterate through dictionary, check if new files exist, and move files that haven't already been created
    for old_path, new_path in location_map.items():
        if old_path.exists() and not new_path.exists():
            shutil.copy2(old_path, new_path)

