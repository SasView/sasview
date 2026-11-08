"""
Reverse synchronization (FW-MVC-DESIGN.md §6, Phases 4 and 5): a change written to the document
first reaches the legacy item models (ParameterTableAdapter), the legacy kernel (LegacyKernelSync)
and the settings widgets (SettingsSync).

Each test writes the document directly, as the Phase 5 intents will. The shadow invariant
(``ShadowChecker``, after every commit and at teardown) is the oracle: the legacy rows, the
three item models, the kernel and the legacy readers must all agree with the document.
"""
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.model.events import Origin
from sas.qtgui.Perspectives.Fitting.model.parameters import Constraint, Dispersion, ValueKind
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g
from sas.qtgui.Perspectives.Fitting.view.ParameterTableAdapter import ParameterTableAdapter


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())
    monkeypatch.setattr(FittingUtilities, "checkConstraints", lambda *a, **kw: None)


@pytest.fixture
def case(request):
    """The golden case named by the test's parameter, checked and closed at teardown."""
    pages = g.CASES[request.param]()
    page = pages[0]
    page.undo_depth = len(page.undo_stack._undo_stack)
    yield page
    for p in pages:
        p.shadow_checker.assert_ok()
        p.close()
    # Document-first changes are not recorded by the legacy slots: the guard mutes them
    assert len(page.undo_stack._undo_stack) == page.undo_depth


def write(page, key, **fields):
    with page.document.transaction(Origin.USER) as tx:
        tx.set_parameter(key, **fields)


def cell(item_model, name, column):
    return item_model.item(g.find_row(item_model, name), column).text()


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testValueAndBoundsReachTableAndKernel(case):
    write(case, "radius", value=33.25, min=1.0, max=500.0)
    assert [cell(case._model_model, "radius", c) for c in (1, 2, 3)] == ["33.25", "1.0", "500.0"]
    assert case.logic.kernel_module.getParam("radius") == 33.25
    assert case.logic.kernel_module.details["radius"][1:] == [1.0, 500.0]


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testUnchangedNumbersKeepTheirSpelling(case):
    g.set_cell(case._model_model, "length", 1, "400.00")
    case.undo_depth = len(case.undo_stack._undo_stack)
    write(case, "length", value=400.0, min=0.0)
    assert cell(case._model_model, "length", 1) == "400.00"


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testFitFlagReachesCheckboxAndFitLists(case):
    write(case, "length", fit=True)
    row = g.find_row(case._model_model, "length")
    assert case._model_model.item(row, 0).checkState() == QtCore.Qt.Checked
    assert case.main_params_to_fit == ["scale", "radius", "length"]
    assert case.cmdFit.isEnabled()


@pytest.mark.parametrize("case", ["polydispersity"], indirect=True)
def testErrorsInsertAndRemoveTheErrorColumns(case):
    write(case, "length.width", error=0.01)
    poly = case.polydispersity_widget
    assert (case.has_error_column, poly.has_poly_error_column) == (True, True)
    assert cell(poly.poly_model, "Distribution of length", 2) == "0.01"
    assert cell(case._model_model, "radius", 2) == ""
    assert case.lstParams.itemDelegate().param_value == 1 and case.lstParams.itemDelegate().param_min == 3
    write(case, "length.width", error=None)
    assert (case.has_error_column, poly.has_poly_error_column) == (False, False)
    assert case.lstParams.itemDelegate().param_min == 2


@pytest.mark.parametrize("case", ["polydispersity"], indirect=True)
def testDispersionReachesPolyTableKernelAndMainSubRow(case):
    write(case, "length.width", value=0.2, dispersion=Dispersion(npts=21, nsigmas=2.5, type="rectangle"))
    poly = case.polydispersity_widget
    assert [cell(poly.poly_model, "Distribution of length", c) for c in (1, 4, 5)] == ["0.2", "21", "2.5"]
    kernel = case.logic.kernel_module
    assert kernel.dispersion["length"]["type"] == "rectangle"
    assert (kernel.getParam("length.npts"), kernel.getParam("length.nsigmas")) == (21, 2.5)
    assert poly.poly_params["length.width"] == 0.2
    # The width is also shown under 'length' in the main table
    sub = case._model_model.item(g.find_row(case._model_model, "length"), 0).child(0)
    assert (sub.child(0, 1).text(), sub.child(0, 4).text()) == ("0.200", "rectangle")


@pytest.mark.parametrize("case", ["magnetism_2d"], indirect=True)
def testMagnetValueReachesTableAndDict(case):
    write(case, "sld_M0", value=3.5, fit=False)
    assert cell(case.magnetism_widget._magnet_model, "sld_M0", 1) == "3.5"
    assert case.magnetism_widget.magnet_params["sld_M0"] == 3.5
    assert case.magnetism_widget.magnet_params_to_fit == []


@pytest.mark.parametrize("case", ["fixed_choice"], indirect=True)
def testChoiceSetsTheComboAndTheDerivedEditability(case):
    write(case, "radius_effective_mode", value=1)
    row = g.find_row(case._model_model, "radius_effective")
    assert not case._model_model.item(row, 1).isEditable()
    assert not case._model_model.item(row, 0).isCheckable()
    write(case, "radius_effective_mode", value=0)
    assert case._model_model.item(row, 1).isEditable()


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testConstraintBecomesTheHiddenChildItem(case):
    constraint = Constraint(param="length", func="2*M1.radius", value_ex="2*M1.radius")
    with case.document.transaction(Origin.USER) as tx:
        tx.set_constraint("length", constraint)
        tx.set_parameter("length", fit=True)
    row = g.find_row(case._model_model, "length")
    stored = case.getConstraintForRow(row)
    assert stored is not constraint and stored.func == "2*M1.radius"
    assert not case._model_model.item(row, 1).isEditable()
    assert case.getComplexConstraintsForModel("standard") == [("length", "2*M1.radius")]
    with case.document.transaction(Origin.USER) as tx:
        tx.set_constraint("length", None)
    assert case.getConstraintForRow(row) is None
    assert case._model_model.item(row, 1).isEditable()


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testMnemonicNamesTheKernel(case):
    with case.document.transaction(Origin.USER) as tx:
        tx.set_mnemonic("sample")
    assert case.logic.kernel_module.name == "sample"


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testRestoringASnapshotPatchesEveryRow(case):
    before = case.document.snapshot()
    g.set_cell(case._model_model, "radius", 1, "50.0")
    g.set_checked(case._model_model, "length")
    case.undo_depth = len(case.undo_stack._undo_stack)
    case.document.restore_undo_state(before)
    assert cell(case._model_model, "radius", 1) == "35.5"
    assert case.logic.kernel_module.getParam("radius") == 35.5
    assert "length" not in case.main_params_to_fit


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testLegacyWritersAreNotSyncedBack(case, monkeypatch):
    """A legacy writer's change reaches the document through the shadow's read-back only."""
    patched = []
    monkeypatch.setattr(ParameterTableAdapter, "_patch", lambda self, *a: patched.append(a))
    with case.shadow.operation("parameters"):
        case._model_model.item(g.find_row(case._model_model, "radius"), 1).setText("37")
    assert patched == []
    assert case.document.parameters["radius"].value == 37.0 == case.logic.kernel_module.getParam("radius")


@pytest.mark.parametrize("case", ["cylinder"], indirect=True)
def testUserEditIsDocumentFirstAndKeepsItsSpelling(case):
    """Phase 5: a cell edit is an intent; the cell keeps what was typed."""
    g.set_cell(case._model_model, "radius", 1, "36")
    assert case.document.parameters["radius"].value == 36.0 == case.logic.kernel_module.getParam("radius")
    assert cell(case._model_model, "radius", 1) == "36"
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
