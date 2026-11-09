"""
Numerical baseline for SasView's model calculation path (SasView/sasview#4216).

Each test sets up a model on a real fit page, the way a user would (choose the model, type values
into the parameter table, pick the resolution and q range), lets SasView compute the theory curve,
and compares the result with sasmodels called directly (``DirectModel``). The reference parameters
are written in sasmodels' own names and never pass through SasView code, so a mistake anywhere
between the fit page and the kernel shows up as a mismatch.

These tests are meant to stay after the sasmodels "SasView shim" is removed (SasView/sasview#4214):
SasView will still have to turn what is on the fit page into sasmodels parameters.
"""

import numpy as np
import pytest

from sasmodels.core import build_model, load_model_info
from sasmodels.data import Data1D as RefData1D
from sasmodels.data import Data2D as RefData2D
from sasmodels.direct_model import DirectModel

from sas.qtgui.Perspectives.Fitting import FittingWidget
from sas.qtgui.Perspectives.Fitting.OptionsWidget import OptionsWidget
from sas.qtgui.Perspectives.Fitting.UnitTesting.FittingWidgetTest import dummy_manager
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D
from sas.qtgui.Utilities import GuiUtils
from sas.qtgui.Utilities.CategoryInstaller import USER_FILE, CategoryInstaller
from sas.sascalc.fit.models import ModelManager

# Both sides run in double precision on the CPU. The measured agreement is about 1e-10 or better,
# so a relative difference above this is a real difference, not rounding.
RTOL = 1e-9

SPHERE = ("Sphere", "sphere", {"scale": 0.5, "background": 0.015625, "radius": 120.0,
                               "sld": 2.5, "sld_solvent": 6.25})
CYLINDER = ("Cylinder", "cylinder", {"scale": 0.25, "background": 0.03125, "radius": 20.0,
                                     "length": 400.0, "sld": 4.0, "sld_solvent": 1.0})
# The fit page shows orientation parameters only for 2D data.
ORIENTATION = {"sphere": {}, "cylinder": {"theta": 60.0, "phi": 45.0}}

Q = np.logspace(-3, -0.5, 50)
DQ = 0.05 * Q


@pytest.fixture(autouse=True)
def cpu_double_precision(monkeypatch):
    """Run sasmodels on the CPU, as the reference does."""
    monkeypatch.setenv("SAS_OPENCL", "none")


@pytest.fixture(autouse=True)
def model_categories(monkeypatch, tmp_path):
    """Give the fit page its own freshly built categories.json.

    The fit page cannot be created without one, and a new CI machine has none. Building our own
    also keeps these tests independent of test order and of the user's own category settings.
    """
    CategoryInstaller.check_install(homedir=str(tmp_path),
                                    model_list=ModelManager().cat_model_list())
    monkeypatch.setattr(CategoryInstaller, "get_user_file",
                        staticmethod(lambda: str(tmp_path / USER_FILE)))


def fit_page(data, category, model, pars):
    """Open a fit page on *data*, choose *model* and type *pars* into the parameter table."""
    item = GuiUtils.createModelItemWithPlot(data, name="baseline")
    page = FittingWidget.FittingWidget(dummy_manager(), data=item)
    page.cbCategory.setCurrentIndex(page.cbCategory.findText(category))
    page.cbModel.setCurrentIndex(page.cbModel.findText(model))
    assert page.cbModel.currentText() == model
    for name, value in pars.items():
        set_param(page, name, value)
    return page


def set_param(page, name, value):
    """Type *value* into the parameter table row for *name*."""
    table = page._model_model
    for row in range(table.rowCount()):
        if table.item(row, 0).text() == name:
            table.item(row, 1).setText(str(value))
            return
    raise KeyError(f"no parameter {name!r} on the fit page")


def set_resolution(page, choice):
    """Choose a resolution option ("None", "Use dQ Data", ...) on the fit page."""
    combo = page.smearing_widget.cbSmearing
    index = combo.findText(choice)
    assert index >= 0, f"no resolution option {choice!r}"
    combo.setCurrentIndex(index)


def set_q_range(page, qmin, qmax):
    """Type the q range into the Options tab."""
    options = page.options_widget
    options.model.item(OptionsWidget.MODEL.index('MIN_RANGE')).setText(str(qmin))
    options.model.item(OptionsWidget.MODEL.index('MAX_RANGE')).setText(str(qmax))
    assert (page.q_range_min, page.q_range_max) == (qmin, qmax)


def compute(page):
    """Run the fit page's calculation without a thread and return its result."""
    results = []
    # The calculation reports its result, then calculateQGridForModelExt reports None again.
    page.calculateQGridForModelExt(
        completefn=lambda result: results.append(result) if result is not None else None,
        use_threads=False)
    assert len(results) == 1
    kernel = type(page.logic.kernel_module)._model
    assert kernel.dtype == np.float64, "SasView did not calculate in double precision"
    return results[0]


def reference_model(model):
    return build_model(load_model_info(model), dtype="double", platform="dll")


def reference_1d(model, pars, dq=None, qmin=Q[0], qmax=Q[-1]):
    """I(q) from sasmodels, for the points of Q between *qmin* and *qmax*."""
    data = RefData1D(x=Q, y=np.ones_like(Q), dx=dq, dy=0.1 * np.ones_like(Q))
    # SasView builds the resolution from all of the data's q points, so near qmin/qmax it uses the
    # model calculated at the data's q values outside the range, rather than extending q past it.
    # So smear over all of the data, then keep the chosen range. (How much the two conventions
    # differ depends on point spacing relative to dQ; see SasView/sasmodels#263.)
    data.qmin, data.qmax = Q[0], Q[-1]
    iq = DirectModel(data, reference_model(model))(**pars)
    q = data.x
    keep = (q >= qmin) & (q <= qmax)
    return q[keep], iq[keep]


@pytest.mark.parametrize("category, model, pars", [SPHERE, CYLINDER], ids=["sphere", "cylinder"])
class Calculation1DTest:
    """1D theory curves from the fit page against sasmodels."""

    @pytest.fixture
    def page(self, qapp, category, model, pars):
        data = Data1D(x=Q, y=np.ones_like(Q), dx=DQ, dy=0.1 * np.ones_like(Q))
        page = fit_page(data, category, model, pars)
        yield page
        page.close()

    def test_no_resolution(self, page, model, pars):
        set_resolution(page, "None")
        result = compute(page)
        q, expected = reference_1d(model, pars)
        np.testing.assert_array_equal(result["x"], q)
        np.testing.assert_allclose(result["y"], expected, rtol=RTOL)

    def test_pinhole(self, page, model, pars):
        set_resolution(page, "Use dQ Data")
        result = compute(page)
        q, expected = reference_1d(model, pars, dq=DQ)
        np.testing.assert_array_equal(result["x"], q)
        np.testing.assert_allclose(result["y"], expected, rtol=RTOL)

    def test_pinhole_inside_data_range(self, page, model, pars):
        """qmin and qmax cut into the data, so the resolution uses points outside the range."""
        set_resolution(page, "Use dQ Data")
        set_q_range(page, 0.003, 0.1)
        result = compute(page)
        q, expected = reference_1d(model, pars, dq=DQ, qmin=0.003, qmax=0.1)
        np.testing.assert_array_equal(result["x"], q)
        np.testing.assert_allclose(result["y"], expected, rtol=RTOL)


@pytest.mark.parametrize("category, model, pars", [SPHERE, CYLINDER], ids=["sphere", "cylinder"])
def test_2d_no_resolution(qapp, category, model, pars):
    """2D theory image from the fit page against sasmodels, without resolution."""
    qx, qy = np.meshgrid(np.linspace(-0.2, 0.2, 21), np.linspace(-0.2, 0.2, 21))
    qx, qy = qx.ravel(), qy.ravel()
    data = Data2D(image=np.ones_like(qx), err_image=np.ones_like(qx), qx_data=qx, qy_data=qy,
                  q_data=np.sqrt(qx**2 + qy**2), mask=np.ones_like(qx, dtype=bool))
    # Set after construction: Data2D's second base-class __init__ resets them.
    data.xmin, data.xmax, data.ymin, data.ymax = -0.2, 0.2, -0.2, 0.2
    pars = {**pars, **ORIENTATION[model]}
    page = fit_page(data, category, model, pars)
    try:
        result = compute(page)
    finally:
        page.close()

    reference = RefData2D(x=qx, y=qy, z=np.ones_like(qx), dz=np.ones_like(qx))
    reference.qmin, reference.qmax = result["qmin"], result["qmax"]
    expected = DirectModel(reference, reference_model(model))(**pars)

    index = result["index"]
    np.testing.assert_array_equal(index, np.ones_like(qx, dtype=bool))
    np.testing.assert_allclose(result["image"][index], expected, rtol=RTOL)


def test_typed_value_reaches_kernel_unrounded(qapp):
    """A value typed into the parameter table reaches the model unchanged (#4234)."""
    data = Data1D(x=Q, y=np.ones_like(Q), dy=0.1 * np.ones_like(Q))
    page = fit_page(data, *SPHERE[:2], {"radius": "123.456789123"})
    try:
        assert page.logic.kernel_module.getParam("radius") == 123.456789123
    finally:
        page.close()
