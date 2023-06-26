from __future__ import print_function

import sys
# make sure sasmodels is on the path
sys.path.append('..')

from os import mkdir
from os.path import basename, exists, join as joinpath
from sasmodels.core import load_model_info

try:
    from typing import Optional, BinaryIO, List, Dict
except ImportError:
    pass
else:
    from sasmodels.modelinfo import ModelInfo

TEMPLATE = """\
..
    Generated from src/sas/sascalc/doc-regen/regentoc.py -- DO NOT EDIT --

.. _%(label)s:

%(bar)s
%(title)s
%(bar)s

.. toctree::

"""

MODEL_TOC_PATH = "../../../../docs/sphinx-docs/source-temp/user/qtgui/Perspectives/Fitting/models"

def _make_category(category_name, label, title, parent=None):
    # type: (str, str, str, Optional[BinaryIO]) -> BinaryIO
    file = open(joinpath(MODEL_TOC_PATH, category_name+".rst"), "w")
    file.write(TEMPLATE%{'label':label, 'title':title, 'bar':'*'*len(title)})
    if parent:
        _add_subcategory(category_name, parent)
    return file

def _add_subcategory(category_name, parent):
    # type: (str, BinaryIO) -> None
    parent.write("    %s.rst\n"%category_name)

def _add_model(file, model_name):
    # type: (IO[str], str) -> None
    file.write("    /user/models/%s.rst\n"%model_name)

def _maybe_make_category(category, models, cat_files, model_toc):
    # type: (str, List[str], Dict[str, BinaryIO], BinaryIO) -> None
    if category not in cat_files:
        print("Unexpected category %s containing"%category, models, file=sys.stderr)
        title = category.capitalize()+" Functions"
        cat_files[category] = _make_category(category, category, title, model_toc)

def generate_toc(model_files):
    # type: (List[str]) -> None
    if not model_files:
        print("gentoc needs a list of model files", file=sys.stderr)

    # find all categories
    category = {} # type: Dict[str, List[str]]
    for item in model_files:
        # assume model is in sasmodels/models/name.py, and ignore the full path
        model_name = basename(item)[:-3]
        if model_name.startswith('_'):
            continue
        model_info = load_model_info(model_name)
        if model_info.category is None:
            print("Missing category for", item, file=sys.stderr)
        else:
            category.setdefault(model_info.category, []).append(model_name)

    # Check category names
    for k, v in category.items():
        if len(v) == 1:
            print("Category %s contains only %s"%(k, v[0]), file=sys.stderr)

    # Generate category files for the table of contents.
    # Initially we had "shape functions" as an additional TOC level, but we
    # have revised it so that the individual shape categories now go at
    # the top level.  Judicious rearrangement of comments will make the
    # "shape functions" level reappear.
    # We are forcing shape-independent, structure-factor and custom-models
    # to come at the end of the TOC.  All other categories will come in
    # alphabetical order before them.

    if not exists(MODEL_TOC_PATH):
        mkdir(MODEL_TOC_PATH)
    model_toc = _make_category(
        'index', 'Models', 'Model Functions')
    #shape_toc = _make_category(
    #    'shape',  'Shapes', 'Shape Functions', model_toc)
    free_toc = _make_category(
        'shape-independent', 'Shape-independent',
        'Shape-Independent Functions')
    struct_toc = _make_category(
        'structure-factor', 'Structure-factor', 'Structure Factors')
    #custom_toc = _make_category(
    #    'custom-models', 'Custom-models', 'Custom Models')

    # remember to top level categories
    cat_files = {
        #'shape':shape_toc,
        'shape':model_toc,
        'shape-independent':free_toc,
        'structure-factor': struct_toc,
        #'custom': custom_toc,
        }

    # Process the model lists
    for k, v in sorted(category.items()):
        if ':' in k:
            cat, subcat = k.split(':')
            _maybe_make_category(cat, v, cat_files, model_toc)
            cat_file = cat_files[cat]
            label = "-".join((cat, subcat))
            filename = label
            title = subcat.capitalize() + " Functions"
            sub_toc = _make_category(filename, label, title, cat_file)
            for model in sorted(v):
                _add_model(sub_toc, model)
            sub_toc.close()
        else:
            _maybe_make_category(k, v, cat_files, model_toc)
            cat_file = cat_files[k]
            for model in sorted(v):
                _add_model(cat_file, model)

    #_add_subcategory('shape', model_toc)
    _add_subcategory('shape-independent', model_toc)
    _add_subcategory('structure-factor', model_toc)
    #_add_subcategory('custom-models', model_toc)

    # Close the top-level category files
    #model_toc.close()
    for f in cat_files.values():
        f.close()


if __name__ == "__main__":
    generate_toc(sys.argv[1:])
