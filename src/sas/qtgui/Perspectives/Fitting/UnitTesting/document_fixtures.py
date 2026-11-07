"""
Qt-free builders of fit page documents for the model tests (FW-MVC-DESIGN.md, Phase 1).
"""
import glob
import math
import os

from sasmodels.sasview_model import load_custom_model, load_standard_models

from sas.qtgui.Perspectives.Fitting.model.document import FitPageDocument
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.kernel import KernelBuilder
from sas.qtgui.Perspectives.Fitting.model.parameters import (
    DataRef,
    FitOptions,
    ModelSelection,
    PageIdentity,
    PageMode,
)
from sas.qtgui.Perspectives.Fitting.UnitTesting.golden_data import make_data1d


def _models() -> dict:
    models = {m.name: m for m in load_standard_models()}
    plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugin_models")
    for path in glob.glob(os.path.join(plugin_dir, "plugin_*.py")):
        model = load_custom_model(path)
        models[model.name] = model
    return models


BUILDER = KernelBuilder(_models())


# ---------------------------------------------------------------------------
# Building documents
# ---------------------------------------------------------------------------

def options_for(data) -> FitOptions:
    """The Q range a data load sets (FittingLogic.computeRangeFromData), with weighting 1 as after a load."""
    if hasattr(data, "qx_data") and data.qx_data is not None:
        x = max(abs(data.xmin), abs(data.xmax))
        y = max(abs(data.ymin), abs(data.ymax))
        return FitOptions(0.0, math.sqrt(x * x + y * y), len(data.data), True, 1, 1)
    return FitOptions(min(data.x), max(data.x), len(data.x), True, 1, 1)


def page(category, model="", structure="", data=(), tab_id=1, batch=False, multiplicity=None,
         resolution=None) -> FitPageDocument:
    doc = FitPageDocument(PageIdentity(tab_id, tab_id), PageMode.BATCH if batch else PageMode.SINGLE,
                          strict=True)
    selection = ModelSelection(category, model, structure, category == "Plugin Models", multiplicity)
    with doc.transaction(Origin.LOAD) as tx:
        if data:
            tx.set_datasets([DataRef(d.id, d.name, d, resolution=resolution) for d in data])
            tx.set_options(options_for(data[0]))
        tx.set_selection(selection)
        tx.set_parameters(BUILDER.layout(selection, doc.is2D()))
    return doc


def edit(doc, key, **fields):
    with doc.transaction(Origin.USER) as tx:
        tx.set_parameter(key, **fields)


def flags(doc, **values):
    with doc.transaction(Origin.USER) as tx:
        tx.set_flags(**values)


def d1(i="d1", name="data1", **kw):
    return make_data1d(i, name, **kw)
