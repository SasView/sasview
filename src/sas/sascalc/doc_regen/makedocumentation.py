"""
Creates documentation from .py files
"""
import os
import sys
import subprocess
import shutil

from os.path import join, basename
from pathlib import Path
from typing import Union

from sas.sascalc.fit import models
from sas.system.version import __version__
from sas.system.user import get_user_dir

# Path constants related to the directories and files used in documentation regeneration processes
USER_DIRECTORY = Path(get_user_dir())
USER_DOC_BASE = USER_DIRECTORY / "doc"
USER_DOC_SRC = USER_DOC_BASE / str(__version__)
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
SAS_DIR = Path(sys.argv[0]).parent

# Find the original documentation location, depending on where the files originate from
if os.path.exists(SAS_DIR / "doc"):
    # This is the directory structure for the installed version of SasView (primary for times when both exist)
    BASE_DIR = SAS_DIR / "doc"
    ORIGINAL_DOCS_SRC = BASE_DIR / "source"
else:
    # This is the directory structure for developers
    BASE_DIR = SAS_DIR / "docs" / "sphinx-docs"
    ORIGINAL_DOCS_SRC = BASE_DIR / "source-temp"

ORIGINAL_DOC_BUILD = BASE_DIR / "build"


def create_user_files_if_needed():
    """Create user documentation directories if necessary and copy built docs there."""
    if not USER_DOC_BASE.exists():
        os.mkdir(USER_DOC_BASE)
    if not USER_DOC_SRC.exists():
        os.mkdir(USER_DOC_SRC)
    if not USER_DOC_LOG.exists():
        os.mkdir(USER_DOC_LOG)
    if not DOC_LOG.exists():
        with open(DOC_LOG, "w") as f:
            # Write an empty file to eliminate any potential future file creation conflicts
            pass
    if not MAIN_DOC_SRC.exists() and ORIGINAL_DOCS_SRC.exists():
        shutil.copytree(ORIGINAL_DOCS_SRC, MAIN_DOC_SRC)
    if not MAIN_BUILD_SRC.exists() and ORIGINAL_DOC_BUILD.exists():
        shutil.copytree(ORIGINAL_DOC_BUILD, MAIN_BUILD_SRC)


def get_py(directory: Union[Path, os.path, str]) -> list[Union[Path, os.path, str]]:
    """Find all python files within a directory that are meant for sphinx and return those file-paths as a list.

    :param directory: A file path-like object to find all python files contained there-in.
    :return: A list of python files found.
    """
    for root, dirs, files in os.walk(directory):
        # Only include python files not starting in '_' (pycache not included)
        PY_FILES = [join(directory, string) for string in files if not string.startswith("_") and string.endswith(".py")]
        return PY_FILES


def get_main_docs() -> list[Union[Path, os.path, str]]:
    """Generates a list of all .py files to be passed into compiling functions found in the main source code, as well as
    in the user plugin model directory.

    :return: A list of python files """
    # The order in which these are added is important. if ABSOLUTE_TARGET_PLUGINS goes first, then we're not compiling the .py file stored in .sasview/plugin_models
    TARGETS = get_py(MAIN_PY_SRC) + get_py(PLUGIN_PY_SRC)
    base_targets = [basename(string) for string in TARGETS]

    # Removes duplicate instances of the same file copied from plugins folder to source-temp/user/models/src/
    for file in TARGETS:
        if base_targets.count(basename(file)) >= 2:
            TARGETS.remove(file)
            base_targets.remove(basename(file))

    return TARGETS


def call_regenmodel(filepath: list[Union[Path, os.path, str]]):
    """Runs regenmodel.py or regentoc.py (specified in parameter regen_py) with all found PY_FILES.

    :param filepath: A file-path like object or list of file-path like objects to regenerate.
    """
    from sas.sascalc.doc_regen.regenmodel import run_sphinx, process_model
    filepaths = [Path(path) for path in filepath]
    rst_files = [Path(process_model(py_file, True)) for py_file in filepaths]
    output_path = MAIN_BUILD_SRC / "user" / "models"
    run_sphinx(rst_files, output_path)


def generate_html(single_file: Union[Path, os.path, str, list] = "", rst: bool = False):
    """Generates HTML from an RST using a subprocess. Based off of syntax provided in Makefile found in /sasmodels/doc/

    :param single_file: A file name that needs the html regenerated.
    :param rst: Boolean to declare the rile an rst-like file.
    """
    # Clear existing log file
    if DOC_LOG.exists():
        with open(DOC_LOG, "r+") as f:
            f.truncate(0)
    DOCTREES = MAIN_BUILD_SRC / "doctrees"
    if rst is False:
        single_rst = MAIN_DOC_SRC / "user" / "models" / single_file.name.replace('.py', '.rst')
    else:
        single_rst = Path(single_file)
    os.environ['SAS_NO_HIGHLIGHT'] = '1'
    command = [
        sys.executable,
        "-m",
        "sphinx",
        "-d",
        DOCTREES,
        "-D",
        "latex_elements.papersize=letter",
        MAIN_DOC_SRC,
        HELP_DIRECTORY_LOCATION,
        single_rst,
    ]
    try:
        # Try removing empty arguments
        command.remove("")
    except:
        pass
    try:
        with open(DOC_LOG, "w") as f:
            subprocess.check_call(command, stdout=f)
    except Exception as e:
        # Logging debug
        print(e)


def call_all_files():
    """A master method to regenerate all known documentation."""
    from sas.sascalc.doc_regen.regentoc import generate_toc
    TARGETS = get_main_docs()
    for file in TARGETS:
        #  easiest for regenmodel.py if files are passed in individually
        call_regenmodel([file])
    # regentoc.py requires files to be passed in bulk or else LOTS of unexpected behavior
    generate_toc(TARGETS)


def call_one_file(file: Union[Path, os.path, str]):
    """A master method to regenerate a single file that is passed to the method.

    :param file: A file name that needs the html regenerated.
    """
    from sas.sascalc.doc_regen.regentoc import generate_toc
    TARGETS = get_main_docs()
    MODEL_TARGET = MAIN_PY_SRC / file
    PLUGIN_TARGET = PLUGIN_PY_SRC / file
    # Determines if a model's source .py file from /user/models/src/ should be used or if the file from /plugin-models/ should be used
    if os.path.exists(MODEL_TARGET) and os.path.exists(PLUGIN_TARGET):
        # Model name collision between built-in models and plugin models: Choose the most recent
        file_call_path = MODEL_TARGET if os.path.getmtime(PLUGIN_TARGET) < os.path.getmtime(MODEL_TARGET) else PLUGIN_TARGET
    elif not os.path.exists(PLUGIN_TARGET):
        file_call_path = MODEL_TARGET
    else:
        file_call_path = PLUGIN_TARGET
    call_regenmodel([file_call_path])
    generate_toc(TARGETS)


def make_documentation(target: Union[Path, os.path, str] = "."):
    """Similar to call_one_file, but will fall back to calling all files and regenerating everything if an error occurs.

    :param target: A file name that needs the html regenerated.
    """
    # Ensure target is a path object
    if target:
        target = Path(target)
    try:
        if ".rst" in target.name:
            # Generate only HTML if passed in file is an RST
            generate_html(target, rst=True)
        else:
            # Tries to generate reST file for only one doc, if no doc is specified then will try to regenerate all reST
            # files. Time saving measure.
            call_one_file(target)
            generate_html(target)
    except Exception as e:
        call_all_files()  # Regenerate all RSTs
        generate_html()  # Regenerate all HTML


if __name__ == "__main__":
    create_user_files_if_needed()
    target = sys.argv[1]
    make_documentation(target)
