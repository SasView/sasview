"""
KernelBuilder.layout against the tables FittingWidget builds today (FW-MVC-DESIGN.md, Phase 1).

For a range of selections, in 1D and 2D, the three item models of a real
FittingWidget are compared with the layout, row by row: labels, row kinds,
checkboxes, values and bounds. This covers combinations the golden cases do
not (shells with polydispersity and magnetism, 2D orientation, products).
"""
import math

import pytest
from PySide6 import QtCore

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.model.document import FitPageDocument
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.kernel import KernelBuilder
from sas.qtgui.Perspectives.Fitting.model.parameters import DataRef, ModelSelection, PageIdentity, RowKind, Table
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g

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


def _number(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return text


def _text_of(value):
    return "" if value is None else value


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr(FittingUtilities, "checkConstraints", lambda *a, **kw: None)


@pytest.mark.parametrize("two_d", [False, True], ids=["1D", "2D"])
@pytest.mark.parametrize("category,model,structure", SELECTIONS)
def testLayoutMatchesWidgetTables(category, model, structure, two_d):
    data = g.make_data2d("d2", "d2") if two_d else g.make_data1d("d1", "d1")
    page = g.new_page(data=data)
    g.select_model(page, category, model or None, structure or None)
    shells = page.logic.current_shell_displayed if page.logic.kernel_module.is_multiplicity_model else None
    selection = ModelSelection(category, model, structure if page.cbStructureFactor.isEnabled() else "",
                               category == "Plugin Models", shells or None)
    # A document applies the derived rules (e.g. radius_effective editability) to the layout
    doc = FitPageDocument(PageIdentity(1, 1), strict=True)
    with doc.transaction(Origin.LOAD) as tx:
        tx.set_datasets([DataRef(data.id, data.name, data)])
        tx.set_selection(selection)
        tx.set_parameters(KernelBuilder(page.models).layout(selection, two_d))
    layout = doc.parameters

    # Main table: one item row per layout row, in order
    main = page._model_model
    assert main.rowCount() == len(layout.rows)
    for row, entry in enumerate(layout.rows):
        items = [main.item(row, c) for c in range(5)]
        if entry.kind is RowKind.HEADING:
            assert (items[0].text(), items[0].isCheckable()) == (entry.name, False)
            continue
        p = layout[entry.name]
        assert items[0].text() == p.label
        assert items[0].isCheckable() == p.fittable, p.key
        if entry.kind is RowKind.MULTIPLICITY:
            assert page._n_shells_row == row
        elif p.choices is None:
            assert _number(items[1].text()) == pytest.approx(float(p.value)), p.key
        assert _number(items[2].text()) == _number(_text_of(p.min)), p.key
        assert _number(items[3].text()) == _number(_text_of(p.max)), p.key

    # Polydispersity table
    poly = page.polydispersity_widget.poly_model
    expected = layout.by_table(Table.POLY)
    assert [poly.item(r, 0).text() for r in range(poly.rowCount())] == [p.label for p in expected]
    for r, p in enumerate(expected):
        assert poly.item(r, 0).data(QtCore.Qt.UserRole) == p.key
        assert _number(poly.item(r, 1).text()) == pytest.approx(p.value)
        assert (_number(poly.item(r, 4).text()), _number(poly.item(r, 5).text())) == \
            (p.dispersion.npts, p.dispersion.nsigmas)

    # Magnetism table
    magnet = page.magnetism_widget._magnet_model
    expected = layout.by_table(Table.MAGNET)
    assert [magnet.item(r, 0).text() for r in range(magnet.rowCount())] == [p.key for p in expected]
    for r, p in enumerate(expected):
        value = _number(magnet.item(r, 1).text())
        assert value == pytest.approx(p.value) or (math.isinf(value) and value == p.value)

    assert layout.capabilities.magnetic == (len(page.logic.kernel_module.magnetic_params) > 0)
    page.close()
