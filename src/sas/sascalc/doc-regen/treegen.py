# Checks if new directory is needed for Sphinx doctrees and builds if not found

import os
from os import mkdir, rmdir
from os.path import join as joinpath, abspath

DOCTREE_LOCATION = abspath(joinpath(__file__, '..', '..', '..', '..', '..', 'docs', 'sphinx-docs', 'source-temp', 'user', 'doctrees'))

def build_doctree_folder():
    try:
        mkdir(DOCTREE_LOCATION)
    except:
        pass
    
    try:
        rmdir(DOCTREE_LOCATION)
    except:
        pass

if __name__ == "__main__":
    build_doctree_folder()