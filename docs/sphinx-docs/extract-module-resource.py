#!/usr/bin/python3
"""Extract all resources from a tree inside a Python module

Python modules can have resources such as icons or source code within them.
This utility extracts all the resources under a source name and saves the
hierarchy to the nominated directory.

Usage:
    extract-module-resource.py module source dest

where
    module: the Python name of the module
    source: the path within the module to be extracted
    dest: the path on disk into which the resources should be saved

Works with modules that are in zip/wheel form as well as on-disk.

"""

import importlib.resources
import sys
from pathlib import Path

VERBOSE = False


def copytree(module: str, src: str | Path, dest: str | Path):
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
        if not allowed(resource.name):
            continue

        if resource.is_dir():
            # recurse into the directory
            copytree(module, spth / resource.name, dpth / resource.name)
        elif resource.is_file():
            if VERBOSE:
                print(spth / resource.name)
            with open(dpth / resource.name, "wb") as dh:
                dh.write(resource.read_bytes())
        else:
            print(f"Skipping {spth / resource.name} (unknown type)")


def allowed(name: str):
    """Check an allow-list of names to avoid copying

    So far, only __pycache__ is seen in the list and needs to be avoided
    """
    if "__pycache__" in name:
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: extract-module-resource.py module source dest")
        sys.exit(1)

    modname = sys.argv[1]
    sourcename = sys.argv[2]
    destdir = sys.argv[3]
    copytree(modname, sourcename, destdir)
