"""
Document to view (FW-MVC-DESIGN.md §6, Phases 4 to 10): a change written to the document is shown
by the tables (``ParameterItemModel``, which read the document) and the settings widgets
(``SettingsSync``), and every engine instance built from it (``KernelBuilder.build``) has the
document's effective state.

Each test writes the document directly, as the intents do.
"""
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.parameters import Constraint, Dispersion, Table, ValueKind
from sas.qtgui.Perspectives.Fitting.model.serializer import format_number
from sas.qtgui.Perspectives.Fitting.services import constraints as constraint_service
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())


@pytest.fixture
def case(request):
    """The golden case named by the test's parameter, checked and closed at teardown."""
    pages = g.CASES[request.param]()
    page = pages[0]
    page.undo_depth = len(page.undo_stack._undo_stack)
    yield page
    for p in pages:
        p.close()
    # Document-first changes are not recorded by the legacy slots: the guard mutes them
    assert len(page.undo_stack._undo_stack) == page.undo_depth


def write(page, key, **fields):
    with page.document.transaction(Origin.USER) as tx:
        tx.set_parameter(key, **fields)


def cell(item_model, name, column):
    return item_model.index(g.find_row(item_model, name), column).data()


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testValueAndBoundsReachTableAndKernel(case):
    write(case, "radius", value=33.25, min=1.0, max=500.0)
    assert [cell(case._model_model, "radius", c) for c in (1, 2, 3)] == ["33.25", "1.0", "500.0"]
    assert case.kernel().getParam("radius") == 33.25
    assert case.kernel().details["radius"][1:] == [1.0, 500.0]


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testNumbersAreShownInTheCanonicalFormat(case):
    """Register R-22 (Phase 10): the table shows the document's number, not the spelling typed."""
    g.set_cell(case._model_model, "length", 1, "400.00")
    case.undo_depth = len(case.undo_stack._undo_stack)
    assert cell(case._model_model, "length", 1) == "400.0"


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testFitFlagReachesCheckboxAndFitLists(case):
    write(case, "length", fit=True)
    row = g.find_row(case._model_model, "length")
    assert case._model_model.index(row, 0).data(QtCore.Qt.CheckStateRole) == QtCore.Qt.Checked
    assert constraint_service.fitted_names(case.document) == ["scale", "radius", "length"]
    assert case.cmdFit.isEnabled()


@pytest.mark.parametrize("case", ["polydispersity"], indirect=True)
def testErrorsInsertAndRemoveTheErrorColumns(case):
    write(case, "length.width", error=0.01)
    poly = case.polydispersity_widget
    assert (case._model_model.has_error_column, poly.poly_model.has_error_column) == (True, True)
    assert cell(poly.poly_model, "Distribution of length", 2) == "0.01"
    assert cell(case._model_model, "radius", 2) == ""
    assert (case._model_model.column("value"), case._model_model.column("min")) == (1, 3)
    write(case, "length.width", error=None)
    assert (case._model_model.has_error_column, poly.poly_model.has_error_column) == (False, False)
    assert case._model_model.column("min") == 2


@pytest.mark.parametrize("case", ["polydispersity"], indirect=True)
def testDispersionReachesPolyTableKernelAndMainSubRow(case):
    write(case, "length.width", value=0.2, dispersion=Dispersion(npts=21, nsigmas=2.5, type="rectangle"))
    poly = case.polydispersity_widget
    assert [cell(poly.poly_model, "Distribution of length", c) for c in (1, 4, 5)] == ["0.2", "21", "2.5"]
    kernel = case.kernel()
    assert kernel.dispersion["length"]["type"] == "rectangle"
    assert (kernel.getParam("length.npts"), kernel.getParam("length.nsigmas")) == (21, 2.5)
    assert kernel.getParam("length.width") == 0.2
    # The width is also shown under 'length' in the main table
    model = case._model_model
    sub = model.index(0, 0, model.index(g.find_row(model, "length"), 0))
    assert sub.data() == "Polydispersity"
    assert (model.index(0, 1, sub).data(), model.index(0, 4, sub).data()) == ("0.200", "rectangle")


@pytest.mark.parametrize("case", ["magnetism_2d"], indirect=True)
def testMagnetValueReachesTableAndDict(case):
    write(case, "sld_M0", value=3.5, fit=False)
    assert cell(case.magnetism_widget._magnet_model, "sld_M0", 1) == "3.5"
    assert case.kernel().getParam("sld_M0") == 3.5


@pytest.mark.parametrize("case", ["fixed_choice"], indirect=True)
def testChoiceSetsTheComboAndTheDerivedEditability(case):
    write(case, "radius_effective_mode", value=1)
    row = g.find_row(case._model_model, "radius_effective")
    assert not bool(case._model_model.flags(case._model_model.index(row, 1)) & QtCore.Qt.ItemIsEditable)
    assert not bool(case._model_model.flags(case._model_model.index(row, 0)) & QtCore.Qt.ItemIsUserCheckable)
    write(case, "radius_effective_mode", value=0)
    assert bool(case._model_model.flags(case._model_model.index(row, 1)) & QtCore.Qt.ItemIsEditable)


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testAConstraintLocksTheRow(case):
    constraint = Constraint(param="length", func="2*M1.radius", value_ex="2*M1.radius")
    with case.document.transaction(Origin.USER) as tx:
        tx.set_constraint("length", constraint)
        tx.set_parameter("length", fit=True)
    row = g.find_row(case._model_model, "length")
    assert not bool(case._model_model.flags(case._model_model.index(row, 1)) & QtCore.Qt.ItemIsEditable)
    assert constraint_service.complex_constraints(case.document, Table.MAIN) == [("length", "2*M1.radius")]
    with case.document.transaction(Origin.USER) as tx:
        tx.set_constraint("length", None)
    assert case.getConstraintForRow(row) is None
    assert bool(case._model_model.flags(case._model_model.index(row, 1)) & QtCore.Qt.ItemIsEditable)


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testMnemonicNamesTheKernel(case):
    with case.document.transaction(Origin.USER) as tx:
        tx.set_mnemonic("sample")
    assert case.kernel().name == "sample"


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testRestoringASnapshotPatchesEveryRow(case):
    before = case.document.snapshot()
    g.set_cell(case._model_model, "radius", 1, "50.0")
    g.set_checked(case._model_model, "length")
    case.undo_depth = len(case.undo_stack._undo_stack)
    case.document.restore_undo_state(before)
    assert cell(case._model_model, "radius", 1) == "35.5"
    assert case.kernel().getParam("radius") == 35.5
    assert "length" not in constraint_service.fitted_names(case.document)


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testUserEditIsDocumentFirstAndKeepsItsSpelling(case):
    """Phase 5: a cell edit is an intent; the cell shows the document (R-22)."""
    g.set_cell(case._model_model, "radius", 1, "36")
    assert case.document.parameters["radius"].value == 36.0 == case.kernel().getParam("radius")
    assert cell(case._model_model, "radius", 1) == "36.0"
    assert case.undo_stack._undo_stack[-1].new == {"value": 36.0}
    case.undo_depth += 1


@pytest.mark.parametrize("case", sorted(g.CASES), indirect=True)
def testEveryParameterOfEveryCase(case):
    """One transaction changes every float value, bound and error, and flips every fit flag of the page."""
    with case.document.transaction(Origin.USER) as tx:
        for p in case.document.parameters:
            fields = {"fit": not p.fit, "error": 0.5} if p.fittable else {}
            if p.kind is ValueKind.FLOAT and p.editable:
                fields["value"] = p.value * 1.5 + 1.0
                if p.min is not None:
                    fields.update(min=p.min - 1.0, max=p.max + 1.0)
            if fields:
                tx.set_parameter(p.key, **fields)
    # Every table shows the new state
    for model in case.tables.values():
        for row in range(model.rowCount()):
            key = model.key_at(row)
            p = case.document.parameters[key] if key is not None else None
            if p is not None and p.kind is ValueKind.FLOAT:
                assert model.index(row, model.column("value")).data() == format_number(p.value)
