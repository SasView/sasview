"""
Qt-free builders of fit page documents for the model tests (FW-MVC-DESIGN.md, Phase 1).
"""
import glob
import math
import os

import pytest

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


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------

def _as_number(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def same(actual, expected, path="") -> None:
    """Assert equality, with numbers (and number text) compared numerically to 1e-6."""
    if isinstance(expected, dict):
        assert isinstance(actual, dict) and set(actual) == set(expected), f"{path}: keys differ"
        for k in expected:
            same(actual[k], expected[k], f"{path}.{k}")
        return
    if isinstance(expected, (list, tuple)):
        assert isinstance(actual, (list, tuple)) and len(actual) == len(expected), \
            f"{path}: {actual!r} != {expected!r}"
        for i, (a, e) in enumerate(zip(actual, expected)):
            same(a, e, f"{path}[{i}]")
        return
    a, e = _as_number(actual), _as_number(expected)
    if a is not None and e is not None:
        assert a == pytest.approx(e, rel=1e-6, abs=1e-12) or (math.isinf(a) and a == e), \
            f"{path}: {actual!r} != {expected!r}"
        return
    assert actual == expected, f"{path}: {actual!r} != {expected!r}"


def jsonable(value):
    """Rows hold tuples and None; the goldens hold lists."""
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value
