"""
Creates documentation from .py files
"""
import logging
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from sasmodels.core import list_models

from sas.system.user import (
    DOC_LOG,
    HELP_DIRECTORY_LOCATION,
    MAIN_BUILD_SRC,
    MAIN_DOC_SRC,
    MAIN_PY_SRC,
    PATH_LIKE,
    PLUGIN_PY_SRC,
    create_user_files_if_needed,
)

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

def generate_html(single_files: PATH_LIKE | list[PATH_LIKE] = "", rst: bool = False, output_path: PATH_LIKE = "") -> subprocess.Popen[bytes]:
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
