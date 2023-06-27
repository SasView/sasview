"""
Generates 'weak' (read: not pretty) html using rst2html.py found in sasmodels directory.
Does NOT utilize sphinx in order minimize dependencies &ect
Therefore does not generate nice-looking output but does make HTML.
Making output pretty >> future project.
"""

import sys
import os
from os.path import basename, dirname, realpath, join as joinpath, exists
from argparse import ArgumentParser

# Can be removed if moved to sasmodels directory
sys.path.insert(0, realpath(joinpath(dirname(__file__), '..')))
from sasmodels import rst2html, compare
from sasmodels.generate import make_html
from sasmodels.kernel import KernelModel
from sasmodels.modelinfo import ModelInfo

# Target directory for HTML output
HTML_OUT = "../build/html/user/models/"

def buildhtml(model_info):
    from sasmodels import generate
    generate.make_html(model_info)

def argument_parse():
    parser = ArgumentParser()
    parser.add_argument('html', nargs='?')
    args = parser.parse_args()
    if args.html == "html":
        buildhtml()


if __name__ == "__main__":
   argument_parse()


