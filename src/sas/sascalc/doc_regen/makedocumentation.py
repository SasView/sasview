"""
Creates documentation from .py files
"""
import importlib.resources
import logging
import os
import sys
import subprocess
import shutil

from pathlib import Path
from typing import Sequence, Union

from sas.sascalc.fit import models
from sas.system.user import get_app_dir_versioned

from sasmodels.core import list_models


PATH_LIKE = Union[Path, str, os.PathLike[str]]


# Path constants related to the directories and files used in documentation regeneration processes
APP_DIRECTORY = Path(get_app_dir_versioned())
USER_DOC_BASE = APP_DIRECTORY / "doc"
USER_DOC_SRC = USER_DOC_BASE
USER_DOC_LOG = USER_DOC_SRC / 'log'
DOC_LOG = USER_DOC_LOG / 'output.log'
MAIN_DOC_SRC = USER_DOC_SRC / "source-temp"
MAIN_BUILD_SRC = USER_DOC_SRC / "build"
MAIN_PY_SRC = MAIN_DOC_SRC / "user" / "models" / "src"
ABSOLUTE_TARGET_MAIN = Path(MAIN_DOC_SRC)
PLUGIN_PY_SRC = Path(models.find_plugins_dir())

HELP_DIRECTORY_LOCATION = MAIN_BUILD_SRC / "html"
RECOMPILE_DOC_LOCATION = HELP_DIRECTORY_LOCATION
IMAGES_DIRECTORY_LOCATION = HELP_DIRECTORY_LOCATION / "_images"


# logging.debug("""
# APP_DIRECTORY = %s
# USER_DOC_BASE = %s
# USER_DOC_SRC = %s
# USER_DOC_LOG = %s
# DOC_LOG = %s
# MAIN_DOC_SRC = %s
# MAIN_BUILD_SRC = %s
# MAIN_PY_SRC = %s
# ABSOLUTE_TARGET_MAIN = %s
# PLUGIN_PY_SRC = %s
# HELP_DIRECTORY_LOCATION = %s
# RECOMPILE_DOC_LOCATION = %s
# IMAGES_DIRECTORY_LOCATION = %s
# """,
#     APP_DIRECTORY,
#     USER_DOC_BASE,
#     USER_DOC_SRC,
#     USER_DOC_LOG,
#     DOC_LOG,
#     MAIN_DOC_SRC,
#     MAIN_BUILD_SRC,
#     MAIN_PY_SRC,
#     ABSOLUTE_TARGET_MAIN,
#     PLUGIN_PY_SRC,
#     HELP_DIRECTORY_LOCATION,
#     RECOMPILE_DOC_LOCATION,
#     IMAGES_DIRECTORY_LOCATION,
# )

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
    # Fast path out - everything already exists
    if MAIN_DOC_SRC.exists() and MAIN_BUILD_SRC.exists():
        return

    if copy_module_resources():
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


def copy_module_resources() -> bool:
    """Obtain the source and build output from within the installed sas module"""

    # Look in the module for the resources. We know that there is a conf.py
    # for sphinx so check that it exists; checking that the file exists and
    # not just the directory protects against empty directories
    if importlib.resources.files("sas").joinpath("docs-source/conf.py").is_file():
        logging.info("Extracting docs from sas module")
        if not MAIN_DOC_SRC.exists():
            module_copytree("sas", "docs-source", MAIN_DOC_SRC)
        if not MAIN_BUILD_SRC.exists():
            module_copytree("sas", "docs", MAIN_BUILD_SRC / "html")
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
        if "__pycache__" in resource.name:
            continue

        if resource.is_dir():
            # recurse into the directory
            module_copytree(module, spth / resource.name, dpth / resource.name)
        elif resource.is_file():
            logging.debug("Copied: %s", spth / resource.name)
            with open(dpth / resource.name, "wb") as dh:
                dh.write(resource.read_bytes())
        else:
            logging.warning("Skipping %s (unknown type)", spth / resource.name)


def create_user_files_if_needed() -> None:
    """Create user documentation directories if necessary and copy built docs there."""
    if not USER_DOC_BASE.exists():
        os.mkdir(USER_DOC_BASE)
    if not USER_DOC_SRC.exists():
        os.mkdir(USER_DOC_SRC)
    if not USER_DOC_LOG.exists():
        os.mkdir(USER_DOC_LOG)
    if not DOC_LOG.exists():
        with open(DOC_LOG, "wb") as f:
            # Write an empty file to eliminate any potential future file creation conflicts
            pass
    copy_resources()


def get_py(directory: Path) -> list[Path]:
    """Find all python files within a directory that are meant for sphinx and return those file-paths as a list.

    :param directory: A file path-like object to find all python files contained there-in.
    :return: A list of python files found.
    """
    for root, dirs, files in os.walk(directory):
        # Only include python files not starting in '_' (pycache not included)
        py_files = [Path(directory) / string for string in files if not string.startswith("_") and string.endswith(".py")]
        return py_files
    return []


def get_main_docs() -> list[Path]:
    """Generates a list of all .py files to be passed into compiling functions found in the main source code, as well as
    in the user plugin model directory.

    :return: A list of python files """
    # The order in which these are added is important. if ABSOLUTE_TARGET_PLUGINS goes first, then we're not compiling the .py file stored in .sasview/plugin_models
    targets = get_py(MAIN_PY_SRC) + get_py(PLUGIN_PY_SRC)
    base_targets = [p.name for p in targets]

    # Removes duplicate instances of the same file copied from plugins folder to source-temp/user/models/src/
    for p in targets:
        if base_targets.count(p.name) >= 2:
            targets.remove(p)
            base_targets.remove(p.name)

    return targets

def sync_plugin_models() -> list[Path]:
    """
    Remove deleted plugin models from source-temp/user/models/src/
    """
    removed_files = []
    list_of_models = list_models()
    for file in [Path(path) for path in get_py(MAIN_PY_SRC)]:
        if file.stem not in list_of_models:
            # Remove the model from the source-temp/user/models/src/ directory
            os.remove(file)
            removed_files.append(file)
    return removed_files

def call_regenmodel(filepaths: Sequence[PATH_LIKE]) -> list[Path]:
    """Runs regenmodel.py or regentoc.py (specified in parameter regen_py) with all found PY_FILES.

    :param filepath: A file-path like object or list of file-path like objects to regenerate.

    :return removed_files: A list of src files that were removed during the regeneration process.
    """
    create_user_files_if_needed()
    from sas.sascalc.doc_regen.regenmodel import process_model
    paths = [Path(path) for path in filepaths]
    removed_files = sync_plugin_models()
    for py_file in paths:
        process_model(py_file, True)
    return removed_files

def generate_html(single_files: Union[PATH_LIKE, list[PATH_LIKE]] = "", rst: bool = False, output_path: PATH_LIKE = "") -> subprocess.Popen[bytes]:
    """Generates HTML from an RST using a subprocess. Based off of syntax provided in Makefile found in /sasmodels/doc/

    :param single_file: A file name that needs the html regenerated.
     NOTE: passing in this parameter will result in ONLY the specified file being regenerated.
     The TOC will not be updated correctly, and as such, this arg should only be passed when 'preview'
     documentation generation is supported in a later version.
    :param rst: Boolean to declare the rile an rst-like file.
    """
    if output_path:
        html_directory = Path(output_path)
    else:
        html_directory = HELP_DIRECTORY_LOCATION
    force_rebuild = "" # Empty if we are not forcing a full rebuild of docs
    doctrees = MAIN_BUILD_SRC / "doctrees"

    # Process the single_files parameter into a list of Path objects referring to rst files
    paths: list[Path] = []
    if isinstance(single_files, str) and single_files:
        # User has passed in a single file as a string
        paths = [Path(single_files)]
    elif rst is False and isinstance(single_files, list):
        # User has passed in a list of python pathnames: we need to pass in the corresponding .rst file
        paths = [(MAIN_DOC_SRC / "user" / "models" / single_file).with_suffix(".rst") for single_file in single_files]
    elif not single_files:
        # User wants a complete regeneration of documentation
        force_rebuild = "-E"
    os.environ['SAS_NO_HIGHLIGHT'] = '1'
    command: list[str | Path] = [
        sys.executable,
        "-m",
        "sphinx",
        force_rebuild, # If forcing a full rebuild: this is necessary to ensure that the TOC is updated
        "-d",
        doctrees,
        "-D",
        "latex_elements.papersize=letter",
        MAIN_DOC_SRC,
        html_directory,
    ]
    if paths:
        # If the user has passed in a single file, we only want to regenerate that file
        command.extend(paths)
    # Try removing empty arguments
    command = [arg for arg in command if arg]
    with open(DOC_LOG, "wb") as f:
        runner = subprocess.Popen(command, stdout=f, stderr=f)
    return runner


def call_all_files() -> None:
    """A master method to regenerate all known documentation."""
    from sas.sascalc.doc_regen.regentoc import generate_toc
    targets = get_main_docs()
    for file in targets:
        #  easiest for regenmodel.py if files are passed in individually
        removed_files = call_regenmodel([file])
        # Don't try to add user files to the TOC if they were deleted
        for file in removed_files:
            if file in targets:
                targets.remove(file)
    # regentoc.py requires files to be passed in bulk or else LOTS of unexpected behavior
    generate_toc(targets)


def call_one_file(file: PATH_LIKE) -> None:
    """A master method to regenerate a single file that is passed to the method.

    :param file: A file name that needs the html regenerated.
    """
    from sas.sascalc.doc_regen.regentoc import generate_toc
    targets = get_main_docs()
    model_target = MAIN_PY_SRC / file
    plugin_target = PLUGIN_PY_SRC / file
    # Determines if a model's source .py file from /user/models/src/ should be used or if the file from /plugin-models/ should be used
    if model_target.exists() and plugin_target.exists():
        # Model name collision between built-in models and plugin models: Choose the most recent
        file_call_path = model_target if plugin_target.stat().st_mtime < model_target.stat().st_mtime else plugin_target
    elif not plugin_target.exists():
        file_call_path = model_target
    else:
        file_call_path = plugin_target
    removed_files = call_regenmodel([file_call_path])

    # Don't try to add user files to the TOC if they were deleted
    for filename in removed_files:
        if filename in targets:
            targets.remove(filename)

    # Generate the TOC
    breakpoint()
    generate_toc(targets)


def make_documentation(target: PATH_LIKE = ".") -> subprocess.Popen[bytes]:
    """Similar to call_one_file, but will fall back to calling all files and regenerating everything if an error occurs.

    :param target: A file name that needs the html regenerated.
    """
    create_user_files_if_needed()
    # Clear existing log file
    if DOC_LOG.exists():
        with open(DOC_LOG, "rb+") as f:
            f.truncate(0)
    # Ensure target is a path object
    target = Path(target)
    try:
        if ".rst" in target.name:
            # Generate only HTML if passed in file is an RST
            return generate_html(target, rst=True)

        # Tries to generate reST file for only one doc, if no doc is specified then will try to regenerate all reST
        # files. Time saving measure.
        call_one_file(target)
        return generate_html()
    except Exception as e:
        logging.warning("Error in generating documentation for %s: %s\nRegenerating all model documentation...", target, e)
        call_all_files()  # Regenerate all RSTs
        return generate_html()  # Regenerate all HTML


if __name__ == "__main__":
    create_user_files_if_needed()
    target = sys.argv[1]
    make_documentation(target)
