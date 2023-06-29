"""
Creates documentation from .py files
"""
import os
import sys
from os.path import join, abspath, dirname
import re
import subprocess

MAIN_PY_SRC = "../source-temp/user/models/src/"
ABSOLUTE_TARGET_MAIN = abspath(join(dirname(__file__), MAIN_PY_SRC))
USER_PY_SRC = "../../../../.sasview/plugin_models/"
ABSOLUTE_TARGET_USER = abspath(join(dirname(__file__), USER_PY_SRC))

def get_py(directory):
    for root, dirs, files in os.walk(directory):
        # Only include python files not starting in '_' (pycache not included)
        regex = re.compile('[$^_][a-z]*.py$')
        PY_FILES = [join(directory, string) for string in files if re.findall(regex, string)]
        return PY_FILES

def get_main_docs():
    """
Generates string of .py files to be passed into compiling functions
    """
    TARGETS = get_py(ABSOLUTE_TARGET_MAIN) + get_py(ABSOLUTE_TARGET_USER)
    return TARGETS

def call_regenmodel(filepath, regen_py):
    """
    Runs regenmodel.py/regentoc.py with all found PY_FILES
    """
    REGENMODEL = abspath(regen_py)
    command = [
        sys.executable,
        REGENMODEL,
        filepath,
    ]
    subprocess.run(command)

def main():
    TARGETS = get_main_docs()
    print(TARGETS)
    for file in TARGETS:
        call_regenmodel(file, "regenmodel.py")
        call_regenmodel(file, "regentoc.py")

if __name__ == "__main__":
    main()