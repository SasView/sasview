import os
import shutil
import sys
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

PATH_LIKE = [Path, os.path, str]

# Path constants related to the directories and files used in documentation regeneration processes
USER_DOC_BASE = Path(_APP_DATA_DIR) / "doc"
USER_DOC_SRC = USER_DOC_BASE
USER_DOC_LOG = USER_DOC_SRC / 'log'
DOC_LOG = USER_DOC_LOG / 'output.log'
MAIN_DOC_SRC = USER_DOC_SRC / "source-temp"
MAIN_BUILD_SRC = USER_DOC_SRC / "build"
MAIN_PY_SRC = MAIN_DOC_SRC / "user" / "models" / "src"
ABSOLUTE_TARGET_MAIN = Path(MAIN_DOC_SRC)

HELP_DIRECTORY_LOCATION = MAIN_BUILD_SRC / "html"
RECOMPILE_DOC_LOCATION = HELP_DIRECTORY_LOCATION
IMAGES_DIRECTORY_LOCATION = HELP_DIRECTORY_LOCATION / "_images"
SAS_DIR = Path(sys.argv[0]).parent

# Find the original documentation location, depending on where the files originate from
if os.path.exists(SAS_DIR / "doc"):
    # This is the directory structure for the installed version of SasView (primary for times when both exist)
    BASE_DIR = SAS_DIR
    BASE_DOC_DIR = SAS_DIR / "doc"
    ORIGINAL_DOCS_SRC = BASE_DOC_DIR / "source"
elif os.path.exists(SAS_DIR / '..' / 'Frameworks' / 'doc'):
    # In the MacOS bundle, the executable and packages are in parallel directories
    BASE_DIR = SAS_DIR / '..' / 'Frameworks'
    BASE_DOC_DIR = SAS_DIR / "doc" / "sphinx-docs"
    ORIGINAL_DOCS_SRC = BASE_DOC_DIR / "source"
else:
    # This is the directory structure for developers
    BASE_DIR = SAS_DIR
    BASE_DOC_DIR = SAS_DIR / "docs" / "sphinx-docs"
    ORIGINAL_DOCS_SRC = BASE_DOC_DIR / "source-temp"

ORIGINAL_DOC_BUILD = BASE_DIR / "build"
ORIGINAL_EXAMPLE_DATA_DIR = BASE_DIR / "example_data"


def get_dir_and_create_if_needed(path: PATH_LIKE, create_if_nonexistent: bool = True) -> Path:
    """Returns the requested directory as a pathlib.Path object, creating the directory if it does not already exist."""
    path = Path(path)
    if create_if_nonexistent and not os.path.exists(path):
        path.mkdir(parents=True, exist_ok=True)
    return path


def copy_dir_to_new_path(install_path: PATH_LIKE, user_path: PATH_LIKE, create_if_nonexistent: bool = True) -> Path:
    """Returns the requested directory as a pathlib.Path object, creating the directory if it does not already exist."""
    path = Path(user_path)
    if create_if_nonexistent and not os.path.exists(path):
        path.mkdir(parents=True, exist_ok=True)
    if Path(install_path).exists():
        shutil.copytree(install_path, path)


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


def create_user_files_if_needed():
    """Create user documentation and example data directories if necessary and copy installation files to new dir."""
    # User docs folder and file generation routines
    get_dir_and_create_if_needed(USER_DOC_BASE)
    get_dir_and_create_if_needed(USER_DOC_SRC)
    get_dir_and_create_if_needed(USER_DOC_LOG)
    if not DOC_LOG.exists():
        with open(DOC_LOG, "w") as f:
            # Write an empty file to eliminate any potential future file creation conflicts
            pass
    copy_dir_to_new_path(ORIGINAL_DOCS_SRC, MAIN_DOC_SRC)
    copy_dir_to_new_path(ORIGINAL_DOC_BUILD, MAIN_BUILD_SRC)

    # Example data generation routines
    user_example_data = get_dir_and_create_if_needed(Path(get_app_dir() / 'example_data'))
    copy_dir_to_new_path(ORIGINAL_EXAMPLE_DATA_DIR, user_example_data)


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

