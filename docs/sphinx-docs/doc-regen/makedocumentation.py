"""
Creates documentation from .py files
"""
import os
import sys
from os.path import join, abspath, dirname, basename
import subprocess

MAIN_PY_SRC = "../source-temp/user/models/src/"
ABSOLUTE_TARGET_MAIN = abspath(join(dirname(__file__), MAIN_PY_SRC))
PLUGIN_PY_SRC = "../../../../.sasview/plugin_models/"
ABSOLUTE_TARGET_PLUGINS = abspath(join(dirname(__file__), PLUGIN_PY_SRC))

def get_py(directory):
    for root, dirs, files in os.walk(directory):
        # Only include python files not starting in '_' (pycache not included)
        PY_FILES = [join(directory, string) for string in files if not string.startswith("_") and string.endswith(".py")]
        return PY_FILES

def get_main_docs():
    """
Generates string of .py files to be passed into compiling functions
Future reference: move to main() function?
    """
    TARGETS = get_py(ABSOLUTE_TARGET_MAIN) + get_py(ABSOLUTE_TARGET_PLUGINS)
    base_targets = [basename(string) for string in TARGETS]
    for file in TARGETS:
        if base_targets.count(basename(file)) >= 2:
            TARGETS.remove(file)
            base_targets.remove(basename(file))
    return TARGETS

def call_regenmodel(filepath, regen_py):
    """
    Runs regenmodel.py/regentoc.py (specified in parameter regen_py) with all found PY_FILES
    """
    REGENMODEL = abspath(regen_py)
    # Initialize command to be executed
    command = [
        sys.executable,
        REGENMODEL,
    ]
    # Append each filepath to command individually if passed in many files
    if type(filepath) == list:
        for string in filepath:
            command.append(string)
    else:
        command.append(filepath)
    subprocess.run(command)

def generate_html():
    # based off of syntax provided in Makefile found under /sasmodels/doc/
    DOCTREES = "../build/doctrees/"
    SPHINX_SOURCE = "../source-temp/"
    HTML_TARGET = "../build/html/"
    command = [
        sys.executable,
        "-m",
        "sphinx",
        "-d",
        DOCTREES,
        "-D",
        "latex_elements.papersize=letter",
        SPHINX_SOURCE,
        HTML_TARGET,
    ]
    subprocess.check_call(command)

def main():
    TARGETS = get_main_docs()
    for file in TARGETS:
        #  easiest for regenmodel.py if files are passed in individually
        call_regenmodel(file, "regenmodel.py")
    # regentoc.py requires files to be passed in bulk or else LOTS of unexpected behavior
    call_regenmodel(TARGETS, "regentoc.py")
    generate_html()

if __name__ == "__main__":
    main()