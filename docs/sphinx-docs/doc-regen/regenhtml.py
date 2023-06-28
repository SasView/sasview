"""
Generates 'weak' (read: not pretty) html using rst2html.py found in sasmodels directory.
Does NOT utilize sphinx in order minimize dependencies &ect
Therefore does not generate nice-looking output but does make HTML.
Making output pretty >> future project.
"""

import sys
from os import environ
from os.path import basename, dirname, realpath, join as joinpath, exists, sep
import argparse

# Can be removed if moved to sasmodels directory
sys.path.insert(0, realpath(joinpath(dirname(__file__), '..')))
from sasmodels import rst2html, compare
from sasmodels.generate import make_html
from sasmodels.kernel import KernelModel
from sasmodels.modelinfo import ModelInfo

# Target directory for HTML output
HTML_OUT = "../build/html/user/models/"

def define_model_info():
    from sasmodels import core, kernel
    from sasmodels.custom import load_custom_kernel_module
    plugin_path = environ.get('SAS_MODELPATH', None)
    if plugin_path is not None:
                file_name = model_name.split(sep)[-1]
                model_name = plugin_path + sep + file_name + ".py"
                kernel_module = load_custom_kernel_module(model_name)
    py_file = args.file

    #define model_info
    model_info = core.load_model_info(model_name)
    if model_info.basefile is None:
        model_info.basefile = py_file
    if args.html == "html":
        buildhtml()

def buildhtml(model_info):
    from sasmodels import generate, core
    generate.make_html(model_info)

def argument_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('html', nargs='?')
    parser.add_argument('file', type=argparse.FileType('r'))
    global args
    args = parser.parse_args()


if __name__ == "__main__":
   argument_parse()
   define_model_info()


