"""
Golden-file support for the FitPageDocument refactor (FW-MVC-DESIGN.md, Phase 0).

Each case builds one or more fit pages programmatically, with fixed tab ids
and data ids, and ``capture`` records every legacy output of a page:

- ``rows``        getFitPage() + getFitModel()
- ``clipboard``   clipboard text (full_copy_data)
- ``excel``       Excel text
- ``latex``       LaTeX text
- ``serialized``  FittingPerspective.getSerializedFitpage (the project dict)
- ``fit_state``   getCurrentFitState, written into a plain namespace
- ``symbols``     the document's symbol table
- ``report``      report HTML, normalized (timestamp, versions and images masked)
- ``theory_inputs`` the effective kernel state passed to Calc1D/Calc2D
- ``fit_inputs``  the arguments passed to Fit.set_model / Fit.set_data, if the page can fit

``GoldenFilesTest`` compares these against ``goldens/<case>.json``. The
goldens are regenerated with ``SASVIEW_UPDATE_GOLDENS=1``.
"""
import json
import math
import re
import tempfile
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.FittingPerspective import FittingWindow
from sas.qtgui.Perspectives.Fitting.model.parameters import PageMode
from sas.qtgui.Perspectives.Fitting.ReportPageLogic import ReportPageLogic
from sas.qtgui.Perspectives.Fitting.services import fit as fit_service
from sas.qtgui.Perspectives.Fitting.UnitTesting.fitting_test_support import FittingWidgetMod, dummy_manager
from sas.qtgui.Perspectives.Fitting.UnitTesting.golden_data import (  # noqa: F401 (re-exported)
    GOLDEN_DIR,
    golden_path,
    load_golden,
    make_data1d,
    make_data2d,
)
from sas.qtgui.Utilities import GuiUtils


def data_items(datasets: list) -> tuple[QtGui.QStandardItemModel, list[QtGui.QStandardItem]]:
    """Data Explorer items for *datasets*, held in one item model (the caller keeps it alive)."""
    explorer = QtGui.QStandardItemModel()
    items = []
    for data in datasets:
        item = GuiUtils.HashableStandardItem(data.name)
        GuiUtils.updateModelItem(item, data, data.name)
        explorer.appendRow(item)
        items.append(item)
    return explorer, items


# ---------------------------------------------------------------------------
# Page construction and manipulation
# ---------------------------------------------------------------------------

def new_page(tab_id: int = 1, data=None):
    """A FittingWidget whose theory requests are recorded instead of computed (each completes at
    once, without a result)."""
    page = FittingWidgetMod(dummy_manager(), tab_id=tab_id)
    page.theory_requests = []

    def record(request, complete, use_threads=True):
        page.theory_requests.append(request)
        complete(None)
    page.theory_service.runner = record
    if data is not None:
        page.explorer_model, items = data_items(data if isinstance(data, list) else [data])
        page.dataFromItems(items if isinstance(data, list) else items[0])
    return page


def select_model(page, category: str, model: str | None = None, structure: str | None = None):
    page.cbCategory.setCurrentIndex(page.cbCategory.findText(category))
    if model is not None:
        page.cbModel.setCurrentIndex(page.cbModel.findText(model))
    if structure is not None:
        page.cbStructureFactor.setCurrentIndex(page.cbStructureFactor.findText(structure))
    QtWidgets.QApplication.processEvents()


def find_row(item_model, name: str) -> int:
    """The row of the table showing *name* in its first column."""
    for row in range(item_model.rowCount()):
        if item_model.index(row, 0).data() == name:
            return row
    raise KeyError(name)


def cell(item_model, name: str, column: int) -> str:
    """The text of cell (*name*, *column*)."""
    return item_model.index(find_row(item_model, name), column).data()


def set_cell(item_model, name: str, column: int, text: str):
    """The user types *text* into cell (*name*, *column*)."""
    item_model.setData(item_model.index(find_row(item_model, name), column), text, QtCore.Qt.EditRole)


def set_checked(item_model, name: str, checked: bool = True):
    state = QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked
    item_model.setData(item_model.index(find_row(item_model, name), 0), state, QtCore.Qt.CheckStateRole)


def checked(item_model, name: str) -> bool:
    return item_model.index(find_row(item_model, name), 0).data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked


def set_combo(page, view, item_model, name: str, column: int, index: int):
    """Choose entry *index* in the combo box shown in cell (name, column)."""
    widget = view.indexWidget(item_model.index(find_row(item_model, name), column))
    widget.setCurrentIndex(index)


def set_multiplicity(page, count: int):
    model = page._model_model
    widget = page.lstParams.indexWidget(model.index(model.shell_row, 1))
    widget.setCurrentText(str(count))


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def jsonable(value):
    """Convert legacy outputs to JSON values (tuples become lists, numpy scalars become floats)."""
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return [jsonable(v) for v in value.tolist()]
    if isinstance(value, (bool, type(None), str)):
        return value
    if isinstance(value, (int, np.integer)):
        return int(value)
    if isinstance(value, (float, np.floating)):
        value = float(value)
        return value if math.isfinite(value) else str(value)
    return f"<{type(value).__name__}>"


_REPORT_MASKS = [
    (re.compile(r"\[\d\d:\d\d[AP]M, \w+ \d\d, \d{4}\]"), "[TIMESTAMP]"),
    (re.compile(r"SasView version: [^<]*"), "SasView version: [MASKED]"),
    (re.compile(r"SasModels version: [^<]*"), "SasModels version: [MASKED]"),
]


def _report(page) -> str:
    original = (ReportPageLogic.getImages, ReportPageLogic.getBatchResults)
    ReportPageLogic.getImages = lambda self: []
    ReportPageLogic.getBatchResults = lambda self: "[BATCH TABLE]" if page.document.mode is PageMode.BATCH else ""
    try:
        html = page.getReport().html
    finally:
        ReportPageLogic.getImages, ReportPageLogic.getBatchResults = original
    for pattern, replacement in _REPORT_MASKS:
        html = pattern.sub(replacement, html)
    return html


def _fit_state(page) -> dict:
    state = SimpleNamespace()
    page.getCurrentFitState(state)
    result = vars(state)
    result["data"] = None if state.data is None else [type(state.data).__name__, state.data.id]
    return jsonable(result)


def _kernel_state(kernel) -> dict:
    return jsonable({
        "name": kernel.name,
        "params": dict(kernel.params),
        "details": {k: list(v) for k, v in kernel.details.items()},
        "dispersion": {k: dict(v) for k, v in kernel.dispersion.items()},
    })


def _theory_inputs(page) -> dict | None:
    if not len(page.document.parameters) or page.document.active_id is None:
        return None
    # A theory request holds the effective state (KernelBuilder.build) and its own smearer
    request = page.controller.prepare_theory()
    result = _kernel_state(request.kernel)
    result["smearer"] = type(request.smearer).__name__
    return result


class _RecordingFit:
    """Stands in for BumpsFit in FitService.prepare and records its inputs."""
    calls: list = []

    def __init__(self):
        self.fitter_id = None

    def set_model(self, model, fit_id, params_to_fit, data=None, constraints=None):
        _RecordingFit.calls.append({"model": _kernel_state(model), "fit_id": fit_id,
                                    "params_to_fit": list(params_to_fit),
                                    "constraints": jsonable(constraints),
                                    "data": data.id})

    def set_data(self, data, id, smearer=None, qmin=None, qmax=None):
        _RecordingFit.calls[-1].update(smearer=type(smearer).__name__, qmin=jsonable(qmin), qmax=jsonable(qmax))

    def select_problem_for_fit(self, id, value):
        pass

    def set_weight_increase(self, fit_id, weight_increase):
        pass


def _fit_inputs(page) -> list | None:
    """Prepare the page's fit with a recording Fit."""
    if not page.document.can_fit():
        return None
    original = fit_service.Fit
    fit_service.Fit = _RecordingFit
    _RecordingFit.calls = []
    try:
        page.controller.prepare_fitters()
    finally:
        fit_service.Fit = original
    return _RecordingFit.calls


def capture(page) -> dict:
    """All legacy outputs of a page, as JSON values. Order matters: fit_inputs mutates the kernel."""
    result = {
        "rows": jsonable(page.getFitPage() + page.getFitModel()),
        "clipboard": page.full_copy_data(),
        "excel": page.excel_copy_data(),
        "latex": page.latex_copy_data(),
        "serialized": jsonable(FittingWindow.getSerializedFitpage(None, page)),
        "fit_state": _fit_state(page),
        "symbols": jsonable(page.document.symbol_table()),
        "report": _report(page),
        "theory_inputs": _theory_inputs(page),
    }
    result["fit_inputs"] = _fit_inputs(page)
    return result


# ---------------------------------------------------------------------------
# Cases. Each returns the list of pages to capture.
# ---------------------------------------------------------------------------

def case_cylinder():
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Cylinder", "cylinder")
    set_cell(page._model_model, "radius", 1, "35.5")
    set_cell(page._model_model, "length", 3, "1000.0")
    set_checked(page._model_model, "radius")
    set_checked(page._model_model, "scale")
    return [page]


def case_core_multi_shell():
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Sphere", "core_multi_shell")
    set_multiplicity(page, 4)
    set_cell(page._model_model, "thickness2", 1, "12.0")
    set_checked(page._model_model, "thickness2")
    set_multiplicity(page, 3)
    return [page]


def case_sphere_hardsphere():
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Sphere", "sphere", "hardsphere")
    set_cell(page._model_model, "volfraction", 1, "0.3")
    set_checked(page._model_model, "radius")
    return [page]


def case_vesicle_hardsphere():
    """P and S both have volfraction: the S(Q) copy is dropped from the product."""
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Sphere", "vesicle", "hardsphere")
    set_cell(page._model_model, "volfraction", 1, "0.25")
    return [page]


def case_plugin():
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Plugin Models", "plugin_template")
    set_checked(page._model_model, "scale")
    return [page]


def case_magnetism_2d():
    page = new_page(data=make_data2d("d2", "data2d"))
    select_model(page, "Sphere", "sphere")
    page.chkMagnetism.setChecked(True)
    magnet = page.magnetism_widget._magnet_model
    set_cell(magnet, "sld_M0", 1, "2.5")
    set_checked(magnet, "sld_M0")
    set_checked(page._model_model, "radius")
    return [page]


def case_fixed_choice():
    """radius_effective_mode = 0 (unconstrained): radius_effective becomes editable and fittable."""
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Sphere", "sphere", "hardsphere")
    set_combo(page, page.lstParams, page._model_model, "radius_effective_mode", 1, 0)
    set_cell(page._model_model, "radius_effective", 1, "45.0")
    return [page]


def case_disabled_parameter():
    """A fitted parameter that becomes disabled: radius_effective under radius_effective_mode > 0."""
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Sphere", "sphere", "hardsphere")
    set_combo(page, page.lstParams, page._model_model, "radius_effective_mode", 1, 0)
    set_checked(page._model_model, "radius_effective")
    set_combo(page, page.lstParams, page._model_model, "radius_effective_mode", 1, 1)
    return [page]


def load_array_distribution(page, name: str, samples: str = "10 0.2\n20 0.5\n30 0.3\n"):
    """Choose 'array' for poly row *name*, answering the file dialog with a weights file."""
    poly = page.polydispersity_widget
    original = QtWidgets.QFileDialog.getOpenFileName
    with tempfile.TemporaryDirectory() as tmp:
        weights = Path(tmp) / "weights.txt"
        weights.write_text(samples)
        QtWidgets.QFileDialog.getOpenFileName = staticmethod(lambda *a, **kw: (str(weights), ""))
        try:
            poly.onPolyComboIndexChange("array", find_row(poly.poly_model, name))
        finally:
            QtWidgets.QFileDialog.getOpenFileName = original


def case_polydispersity():
    """Gaussian on length, array distribution on radius."""
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Cylinder", "cylinder")
    page.chkPolydispersity.setChecked(True)
    poly = page.polydispersity_widget
    set_cell(poly.poly_model, "Distribution of length", 1, "0.1")
    set_checked(poly.poly_model, "Distribution of length")
    load_array_distribution(page, "Distribution of radius")
    set_checked(page._model_model, "scale")
    return [page]


def case_fit_errors():
    """The state after a (simulated) single fit: error column present, chi2 set."""
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Cylinder", "cylinder")
    set_checked(page._model_model, "radius")
    set_checked(page._model_model, "scale")
    fitted = {"radius": (25.5, 0.75), "scale": (0.95, 0.02)}
    page.fit_service.outcome = lambda res: fitted
    page.onPlot = lambda: None
    res = SimpleNamespace(fitness=1.234)
    page.fitComplete(([[res]], 0.5))
    return [page]


def case_sesans():
    page = new_page(data=make_data1d("ds", "sesans", sesans=True))
    select_model(page, "Sphere", "sphere")
    set_checked(page._model_model, "radius")
    return [page]


def case_structure_only():
    page = new_page(data=make_data1d("d1", "data1"))
    select_model(page, "Structure Factor", structure="hardsphere")
    set_checked(page._model_model, "volfraction")
    return [page]


def case_batch_one():
    page = new_page(data=[make_data1d("b1", "batch1")])
    select_model(page, "Cylinder", "cylinder")
    set_checked(page._model_model, "radius")
    return [page]


def case_batch_two():
    """Two datasets that share a name; everything must be addressed by id."""
    page = new_page(data=[make_data1d("b1", "same"), make_data1d("b2", "same")])
    select_model(page, "Cylinder", "cylinder")
    set_checked(page._model_model, "radius")
    return [page]


def case_two_pages():
    """Page 1 renamed to 'sample'; page 2's radius constrained to sample.radius."""
    first = new_page(tab_id=1, data=make_data1d("d1", "data1"))
    select_model(first, "Cylinder", "cylinder")
    second = new_page(tab_id=2, data=make_data1d("d2", "data2"))
    select_model(second, "Cylinder", "cylinder")
    # Both in one perspective; what ConstraintWidget.onTabCellEdit does on a rename
    second.parent = first.parent
    first.parent.perspective().fit_tabs += [first, second]
    first.coordinator.rename(first, "sample")
    second.addConstraint(Constraint(param="radius", func="sample.radius", value_ex="sample.radius"))
    set_checked(second._model_model, "length")
    return [first, second]


def case_theory_only():
    """No data loaded: a synthetic default dataset."""
    page = new_page()
    select_model(page, "Cylinder", "cylinder")
    set_cell(page._model_model, "radius", 1, "40.0")
    return [page]


CASES = {name[len("case_"):]: fn for name, fn in sorted(globals().items()) if name.startswith("case_")}


def build_and_capture(name: str) -> list[dict]:
    """Build case *name* and capture its pages."""
    pages = []
    try:
        pages = CASES[name]()
        return [capture(page) for page in pages]
    finally:
        for page in pages:
            page.close()


def write_golden(name: str, pages: list[dict]) -> None:
    GOLDEN_DIR.mkdir(exist_ok=True)
    with open(golden_path(name), "w", encoding="utf-8", newline="\n") as f:
        json.dump(pages, f, indent=1, sort_keys=False)
        f.write("\n")
