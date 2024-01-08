"""
Creates documentation from .py files
"""
import os
import sys
import subprocess
import shutil

from os.path import join, abspath, dirname, basename
from pathlib import  Path

from sas.sascalc.fit import models
from sas.sascalc.doc_regen.regentoc import generate_toc
from sas.system.version import __version__
from sas.system.user import get_user_dir


USER_DIRECTORY = Path(get_user_dir())
USER_DOC_BASE = USER_DIRECTORY / "doc"
USER_DOC_SRC = USER_DOC_BASE / str(__version__)
MAIN_DOC_SRC = USER_DOC_SRC / "source-temp"
MAIN_BUILD_SRC = USER_DOC_SRC / "build"
MAIN_PY_SRC = MAIN_DOC_SRC / "user" / "models" / "src"
ABSOLUTE_TARGET_MAIN = Path(MAIN_DOC_SRC)
PLUGIN_PY_SRC = Path(models.find_plugins_dir())

HELP_DIRECTORY_LOCATION = MAIN_BUILD_SRC / "html"
RECOMPILE_DOC_LOCATION = HELP_DIRECTORY_LOCATION
IMAGES_DIRECTORY_LOCATION = HELP_DIRECTORY_LOCATION / "_images"
SAS_DIR = Path(sys.argv[0]).parent
print(SAS_DIR)

if not USER_DOC_BASE.exists():
    os.mkdir(USER_DOC_BASE)
if not USER_DOC_SRC.exists():
    os.mkdir(USER_DOC_SRC)

if os.path.exists(SAS_DIR / "doc"):
    BASE_DIR = SAS_DIR / "doc"
else:
    BASE_DIR = SAS_DIR / "docs" / "sphinx-docs"

ORIGINAL_DOCS_SRC = BASE_DIR / "source-temp"
ORIGINAL_DOC_BUILD = BASE_DIR / "build"

# Create the user directories if necessary
if not MAIN_DOC_SRC.exists():
    shutil.copytree(ORIGINAL_DOCS_SRC, MAIN_DOC_SRC)
if not MAIN_BUILD_SRC.exists():
    shutil.copytree(ORIGINAL_DOC_BUILD, MAIN_BUILD_SRC)


def get_py(directory):
    for root, dirs, files in os.walk(directory):
        # Only include python files not starting in '_' (pycache not included)
        PY_FILES = [join(directory, string) for string in files if not string.startswith("_") and string.endswith(".py")]
        return PY_FILES


def get_main_docs():
    """
    Generates string of .py files to be passed into compiling functions
    """
    # The order in which these are added is important. if ABSOLUTE_TARGET_PLUGINS goes first, then we're not compiling the .py file stored in .sasview/plugin_models
    TARGETS = get_py(ABSOLUTE_TARGET_MAIN) + get_py(PLUGIN_PY_SRC)
    base_targets = [basename(string) for string in TARGETS]

    # Removes duplicate instances of the same file copied from plugins folder to source-temp/user/models/src/
    for file in TARGETS:
        if base_targets.count(basename(file)) >= 2:
            TARGETS.remove(file)
            base_targets.remove(basename(file))

    return TARGETS


def call_regenmodel(filepath, regen_py):
    """
    Runs regenmodel.py/regentoc.py (specified in parameter regen_py) with all found PY_FILES
    """
    REGENMODEL = abspath(dirname(__file__)) + "/" + regen_py
    # Initialize command to be executed
    command = [
        sys.executable,
        REGENMODEL,
    ]
    # Append each filepath to command individually if passed in many files
    if isinstance(filepath, list):
        for string in filepath:
            command.append(string)
    else:
        command.append(filepath)
    subprocess.run(command)


def generate_html(single_file="", rst=False):
    """
    Generates HTML from an RST using a subprocess. Based off of syntax provided in Makefile found under /sasmodels/doc/
    """

    DOCTREES = MAIN_BUILD_SRC / "doctrees"
    if rst is False:
        single_rst = USER_DOC_SRC / "user" / "models" / single_file.replace('.py', '.rst')
    else:
        single_rst = Path(single_file)
    rst_path = single_rst.parts
    for path in MAIN_DOC_SRC.parts:
        # Remove inital path parts from rst_path for overlap
        if path != rst_path[0]:
            break
        del(rst_path[0])
    rst_str = "/".join(list(rst_path)) + "/" + single_rst.name
    if rst_str.endswith("models/") or rst_str.endswith("user/"):
        # (re)sets value to empty string if nothing was entered
        single_rst = ""
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
        subprocess.check_call(command)
    except Exception as e:
        print(e)


def call_all_files():
    TARGETS = get_main_docs()
    for file in TARGETS:
        #  easiest for regenmodel.py if files are passed in individually
        call_regenmodel(file, "regenmodel.py")
    # regentoc.py requires files to be passed in bulk or else LOTS of unexpected behavior
    generate_toc(TARGETS)


def call_one_file(file):
    TARGETS = get_main_docs()
    NORM_TARGET = join(ABSOLUTE_TARGET_MAIN, file)
    MODEL_TARGET = join(MAIN_PY_SRC, file)
    # Determines if a model's source .py file from /user/models/src/ should be used or if the file from /plugin-models/ should be used
    if os.path.exists(NORM_TARGET) and os.path.exists(MODEL_TARGET):
        if os.path.getmtime(NORM_TARGET) < os.path.getmtime(MODEL_TARGET):
            file_call_path = MODEL_TARGET
        else:
            file_call_path = NORM_TARGET
    elif not os.path.exists(NORM_TARGET):
        file_call_path = MODEL_TARGET
    else:
        file_call_path = NORM_TARGET
    call_regenmodel(file_call_path, "regenmodel.py")  # There might be a cleaner way to do this but this approach seems to work and is fairly minimal
    generate_toc(TARGETS)


def make_documentation(target="."):
    # Ensure target is a path object
    if target:
        target = Path(target)
    try:
        print(f"{target.parent}/{target.name}")
        if ".rst" in target.name:
            # Generate only HTML if passed in file is an RST
            generate_html(target, rst=True)
        else:
            call_one_file(target)  # Tries to generate reST file for only one doc, if no doc is specified then will try to regenerate all reST files. Timesaving measure.
            generate_html(target)
    except Exception as e:
        call_all_files() # Regenerate all RSTs
        generate_html() # Regenerate all HTML


if __name__ == "__main__":
    target = sys.argv[1]
    make_documentation(target)
