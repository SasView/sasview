import importlib.resources
import logging
import os
import shutil
import sys
from pathlib import Path

from packaging.version import Version
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
EXAMPLE_DATA_DIR = Path(_APP_DATA_DIR) / "example_data"

PATH_LIKE = Path | str | os.PathLike[str]


def get_dir_and_create_if_needed(path: PATH_LIKE, create_if_nonexistent: bool = True) -> Path:
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


def find_plugins_dir() -> str:
    """A helper function that returns a string representation of the plugins directory as defined by sas.system.user.
    """
    return str(get_plugin_dir())


PLUGIN_PY_SRC = Path(find_plugins_dir())


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
            # Move the file to the new location instead of copying (fixes future issues)
            shutil.move(old_path, new_path)
        if old_path.exists() and new_path.exists():
            # Files copied to the new location in previous versions may still exist. Attempt to delete them.
            try:
                os.remove(old_path)
            except Exception as e:
                logging.error(f"Failed to remove {old_path}: {e}")


def module_copytree(module: str, src: PATH_LIKE, dest: PATH_LIKE) -> None:
    """Copy the tree from a module to the specified directory

    module: name of the Python module (the "anchor" for importlib.resources)
    src: source name of the resource inside the module
    dest: destination directory for the resources to be copied into; will be
        created if it doesn't exist
    """
    spth = Path(src)
    src = str(spth)

    dpth = Path(dest)
    dpth.mkdir(exist_ok=True, parents=True)

    for resource in importlib.resources.files(module).joinpath(src).iterdir():
        f_name = dpth / resource.name
        s_name = spth / resource.name
        if "__pycache__" in resource.name:
            continue

        if resource.is_dir():
            # recurse into the directory
            module_copytree(module, s_name, f_name)
        elif resource.is_file() and not f_name.exists():
            logging.debug("Copied: %s", s_name)
            with open(f_name, "wb") as dh:
                dh.write(resource.read_bytes())
        else:
            logging.warning("Skipping %s (unknown type)", str(s_name))


def is_copy_successful() -> bool:
    """Obtain the source and build output from within the installed sas module"""

    # Look in the module for the resources. We know that there is a conf.py
    # for sphinx so check that it exists; checking that the file exists and
    # not just the directory protects against empty directories
    if importlib.resources.files("sas").joinpath("docs-source/conf.py").is_file():
        logging.info("Extracting docs from sas module")
        module_copytree("sas", "docs-source", MAIN_DOC_SRC)
        module_copytree("sas", "docs", MAIN_BUILD_SRC / "html")
        module_copytree("sas", "example_data", EXAMPLE_DATA_DIR)
        return True

    return False


def locate_unpacked_resources() -> tuple[Path, Path]:
    """Locate the resources unpacked on disk"""
    # Look near where sasview executable sits - if it's from the pyinstaller
    # bundle or from run.py then the doc source will be close by. Note that
    # this won't be true for POSIX-like installations where the executable
    # is in /usr/bin, ~/.local/bin, or .../venv/bin.
    exe_dir = Path(sys.argv[0]).parent

    if (exe_dir / "doc").exists():
        # This is the directory structure for the installed version of SasView
        # such as when installed from the pyinstaller bundle prior to v6.1
        source_dir = exe_dir / "doc" / "source"
        build_dir = exe_dir / "doc" / "build"

    elif (exe_dir.parent / "Frameworks" / "doc").exists():
        # In the MacOS bundle, the executable and packages are in parallel directories
        source_dir = exe_dir.parent / "Frameworks" / "doc" / "source"
        build_dir = exe_dir.parent / "Frameworks" / "doc" / "build"

    else:
        # This is the directory structure for developers
        source_dir = exe_dir / "docs" / "sphinx-docs" / "source-temp"
        build_dir = exe_dir / "build" / "doc"

    logging.info(
        "Extracting docs from on-disk locations: source=%s, build=%s",
        source_dir, build_dir
    )
    return source_dir, build_dir


def copy_resources() -> None:
    """Find the original documentation location (source and built)

    The source and built docs for SasView could be in a number of locations.
    Search for them in the following locations:
    1. installed within the module
    2. unpacked next to the source
    3. in legacy paths from older installation approaches

    Installed versions are prioritised over uninstalled versions to make sure
    that inconveniently named local directories don't cause issues.
    """
    if is_copy_successful():
        return

    source_dir, build_dir = locate_unpacked_resources()
    if not MAIN_DOC_SRC.exists():
        if source_dir.exists():
            shutil.copytree(source_dir, MAIN_DOC_SRC)
        else:
            logging.error("Could not find source for documentation")

    if not MAIN_BUILD_SRC.exists():
        if build_dir.exists():
            shutil.copytree(build_dir, MAIN_BUILD_SRC)
        else:
            logging.error("Could not find pre-built documentation")


def create_user_files_if_needed() -> None:
    """Create user documentation directories if necessary and copy built docs there."""
    USER_DOC_BASE.mkdir(exist_ok=True)
    USER_DOC_SRC.mkdir(exist_ok=True)
    USER_DOC_LOG.mkdir(exist_ok=True)
    EXAMPLE_DATA_DIR.mkdir(exist_ok=True)
    with open(DOC_LOG, "wb"):
        # If the file doesn't exist, write an empty file to eliminate any potential future file creation conflicts
        pass
    copy_resources()


# Path constants related to the directories and files used in documentation regeneration processes
USER_DOC_BASE = Path(get_app_dir_versioned()) / "doc"
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
