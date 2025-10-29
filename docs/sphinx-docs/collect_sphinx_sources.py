#!/usr/bin/env python
"""
Script to collect sphinx sources for building
"""
import os
import shutil
from pathlib import Path

# sphinx paths for the document
BASE = Path(__file__).parent
SPHINX_BUILD = BASE / "build"
SPHINX_SOURCE = BASE / "source-temp"

# user ui docs
PERSPECTIVES_TARGET = SPHINX_SOURCE / "user" / "qtgui" / "Perspectives"

# sasview paths
SASVIEW_SRC = (BASE.parent.parent / "src").resolve()
SASVIEW_DOCS = BASE / "source"
SASVIEW_MEDIA_SOURCE = SASVIEW_SRC / "sas"

# sasmodels paths
SASMODELS_DOCS = BASE / "tmp" / "sasmodels" / "docs"
SASMODELS_MODEL_SOURCE = SASMODELS_DOCS / "model"
SASMODELS_MODEL_TARGET = SPHINX_SOURCE / "user" / "models"
SASMODELS_API_SOURCE = SASMODELS_DOCS / "api"
SASMODELS_API_TARGET = SPHINX_SOURCE / "dev" / "sasmodels-api"
SASMODELS_DEV_SOURCE = SASMODELS_DOCS / "developer"
SASMODELS_DEV_TARGET = SPHINX_SOURCE / "dev" / "sasmodels-dev"
SASMODELS_GUIDE_SOURCE = SASMODELS_DOCS / "guide"
SASMODELS_GUIDE_TARGET = PERSPECTIVES_TARGET / "Fitting"
SASMODELS_GUIDE_EXCLUDE = [
    "index.rst", "install.rst", "intro.rst",
]

# sasdata paths
SASDATA_DOCS = BASE / "tmp" / "sasdata" / "docs"
SASDATA_DEV_SOURCE = SASDATA_DOCS / "dev"
SASDATA_DEV_TARGET = SPHINX_SOURCE / "dev" / "sasdata-dev"
SASDATA_GUIDE_SOURCE = SASDATA_DOCS / "user"
SASDATA_GUIDE_TARGET = SPHINX_SOURCE / "user" / "data"


def inplace_change(filename, old_string, new_string):

    with open(filename, encoding="UTF-8") as f:
        s = f.read()

    if old_string in s:

        print(f'Changing "{old_string}" to "{new_string}" in {filename}')

        s = s.replace(old_string, new_string)
        with open(filename, 'w', encoding="UTF-8") as f:
            f.write(s)

    else:
        print(f'No occurrences of "{old_string}" found in {filename}.')


def _remove_dir(dir_path):
    """Removes the given directory."""
    if dir_path.is_dir():
        print(f"Removing \"{dir_path}\"... ")
        shutil.rmtree(dir_path)


def clean():
    """
    Clean the sphinx build directory.
    """
    print("=== Cleaning Sphinx Build ===")
    _remove_dir(SPHINX_BUILD)
    _remove_dir(SPHINX_SOURCE)


def setup_source_temp():
    """
    Copy the source toctrees to new folder for assembling the sphinx-docs
    """
    print("=== Copying Source toctrees ===")
    shutil.copytree(SASVIEW_DOCS, SPHINX_SOURCE)


def retrieve_user_docs():
    """
    Copies across the contents of any media/ directories in src/, and puts them
    in an appropriately named directory of docs/sphinx-docs/source/. For
    example:

        sas/../[MODULE]/media/dir/A.rst
        sas/../[MODULE]/media/B.rst

    gets copied to a new location:

        docs/sphinx-docs/source-temp/user/[MODULE]/dir/A.rst
        docs/sphinx-docs/source-temp/user/[MODULE]/B.rst

    so that Sphinx may pick it up when generating the documentation.
    """
    print("=== Retrieve User Docs ===")

    # Copy documentation files from sas/.../media to the sphinx directory
    for root, dirs, _ in os.walk(SASVIEW_MEDIA_SOURCE):
        # CRUFT: from 3.12, use SASVIEW_MEDIA_SOURCE.walk()
        if 'media' in dirs:
            source_dir = (Path(root) / "media").resolve()
            relative = source_dir.relative_to(SASVIEW_MEDIA_SOURCE).parent
            dest_dir = SPHINX_SOURCE / "user" / relative

            print(f"Found sasview docs folder at \"{relative}\".")
            shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)

    print("=== Sasmodels Docs ===")
    shutil.copy(SASMODELS_DOCS / "rst_prolog", SPHINX_SOURCE)
    shutil.copytree(SASMODELS_MODEL_SOURCE, SASMODELS_MODEL_TARGET, dirs_exist_ok=True)
    shutil.copytree(SASMODELS_API_SOURCE, SASMODELS_API_TARGET, dirs_exist_ok=True)
    shutil.copytree(SASMODELS_DEV_SOURCE, SASMODELS_DEV_TARGET, dirs_exist_ok=True)
    shutil.copytree(SASMODELS_GUIDE_SOURCE, SASMODELS_GUIDE_TARGET, dirs_exist_ok=True)
    for filename in SASMODELS_GUIDE_EXCLUDE:
        (SASMODELS_GUIDE_TARGET / filename).unlink()

    # Model category files reference the model as ../../model/name.rst.  Since
    # we are rearranging the tree, we need to update each of these links.
    catdir = SASMODELS_GUIDE_TARGET / "models"
    for filename in catdir.iterdir():
        inplace_change(catdir / filename, "../../model/", "/user/models/")


def retrieve_sasdata_docs():
    """
        Copies select files from the bumps documentation into fitting perspective
    """
    print("=== Sasdata Docs ===")
    shutil.copytree(SASDATA_DEV_SOURCE, SASDATA_DEV_TARGET, dirs_exist_ok=True)
    shutil.copytree(SASDATA_GUIDE_SOURCE, SASDATA_GUIDE_TARGET, dirs_exist_ok=True)


def collect():
    clean()
    setup_source_temp()
    retrieve_user_docs()
    retrieve_sasdata_docs()
    print("=== Done ===")

if __name__ == "__main__":
    collect()
