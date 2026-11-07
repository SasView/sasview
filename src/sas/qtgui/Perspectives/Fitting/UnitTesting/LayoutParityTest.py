"""
KernelBuilder.layout against the tables FittingWidget builds today (FW-MVC-DESIGN.md, Phases 1–2).

For a range of selections, in 1D and 2D, the page's shadow document (whose
layout comes from ``KernelBuilder.layout``) is checked against the page's three
item models: row order, labels, checkboxes, values, bounds, editability. This
covers combinations the golden cases do not (shells with polydispersity and
magnetism, 2D orientation, products).
"""
import pytest

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.model.kernel import KernelBuilder
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g
from sas.qtgui.Perspectives.Fitting.UnitTesting.shadow_invariant import check_shadow

SELECTIONS = [
    ("Cylinder", "cylinder", ""),
    ("Cylinder", "hollow_cylinder", "hayter_msa"),
    ("Sphere", "core_multi_shell", ""),
    ("Sphere", "onion", ""),
    ("Sphere", "sphere", "hardsphere"),
    ("Sphere", "vesicle", "squarewell"),
    ("Shape Independent", "unified_power_Rg", ""),
    ("Ellipsoid", "triaxial_ellipsoid", ""),
    ("Plugin Models", "plugin_template", ""),
    ("Structure Factor", "", "stickyhardsphere"),
]


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr(FittingUtilities, "checkConstraints", lambda *a, **kw: None)


@pytest.mark.parametrize("two_d", [False, True], ids=["1D", "2D"])
@pytest.mark.parametrize("category,model,structure", SELECTIONS)
def testLayoutMatchesWidgetTables(category, model, structure, two_d):
    data = g.make_data2d("d2", "d2") if two_d else g.make_data1d("d1", "d1")
    page = g.new_page(data=data)
    g.select_model(page, category, model or None, structure or None)
    doc = page.document
    assert len(doc.parameters)
    assert doc.parameters.same_layout(KernelBuilder(page.models).layout(doc.selection, two_d))
    assert doc.parameters.capabilities.magnetic == (len(page.logic.kernel_module.magnetic_params) > 0)
    check_shadow(page)
    page.shadow_checker.assert_ok()
    page.close()
