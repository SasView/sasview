"""
The fit page intents (FitPageController, FW-MVC-DESIGN.md §3.1, Phase 5) as the user reaches them:
an edit in a table or a tab writes the document first, records an undoable command where the
change is undoable, and the tables, the kernel and the widgets follow.

The shadow invariant (``ShadowChecker``) checks the legacy stores against the document after
every commit and at teardown.
"""
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.model.commands import SetParameterCommand, SnapshotCommand
from sas.qtgui.Perspectives.Fitting.model.parameters import ArrayDistribution
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g
from sas.qtgui.Utilities import GuiUtils


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())
    monkeypatch.setattr(FittingUtilities, "checkConstraints", lambda *a, **kw: None)


@pytest.fixture
def page():
    p = g.new_page(data=g.make_data1d("d1", "data1"))
    g.select_model(p, "Cylinder", "cylinder")
    p.undo_stack.clear()
    yield p
    p.shadow_checker.assert_ok()
    p.close()


@pytest.fixture
def messages():
    seen = []
    GuiUtils.communicator.statusBarUpdateSignal.connect(seen.append)
    yield seen
    GuiUtils.communicator.statusBarUpdateSignal.disconnect(seen.append)


def cell(item_model, name, column):
    return item_model.item(g.find_row(item_model, name), column).text()


def test_typed_values_keep_double_precision(page):
    """Register R-12, changed in Phase 5: no longer rounded to single precision."""
    g.set_cell(page._model_model, "radius", 1, "20.123456789")
    assert page.document.parameters["radius"].value == 20.123456789
    assert page.logic.kernel_module.getParam("radius") == 20.123456789


def test_a_rejected_edit_is_reported_and_the_cell_shows_the_document_again(page, messages):
    g.set_cell(page._model_model, "radius", 3, "-1.0")            # max below min
    assert page.document.parameters["radius"].max == float("inf")
    assert cell(page._model_model, "radius", 3) == "inf"
    assert any("greater than max" in m for m in messages)
    assert not page.undo_stack.can_undo()


def test_npts_and_distribution_edits_are_undoable(page):
    page.chkPolydispersity.setChecked(True)
    poly = page.polydispersity_widget
    g.set_cell(poly.poly_model, "Distribution of radius", 4, "21")
    assert page.logic.kernel_module.getParam("radius.npts") == 21
    poly.onPolyComboIndexChange("rectangle", g.find_row(poly.poly_model, "Distribution of radius"))
    assert page.logic.kernel_module.dispersion["radius"]["type"] == "rectangle"
    assert page.document.parameters["radius.width"].dispersion.npts == 35   # the distribution's default
    page.undo_stack.undo()
    assert page.logic.kernel_module.dispersion["radius"]["type"] == "gaussian"
    assert cell(poly.poly_model, "Distribution of radius", 4) == "21"
    page.undo_stack.undo()
    assert page.logic.kernel_module.getParam("radius.npts") == 35


def test_an_array_distribution_unfits_and_disables_the_row_and_undo_restores_it(page, monkeypatch):
    page.chkPolydispersity.setChecked(True)
    poly = page.polydispersity_widget
    row = g.find_row(poly.poly_model, "Distribution of radius")
    g.set_checked(poly.poly_model, "Distribution of radius")
    monkeypatch.setattr(poly, "loadPolydispArray", lambda r: ArrayDistribution((10.0, 20.0), (0.4, 0.6), "w.txt"))
    poly.onPolyComboIndexChange("array", row)
    p = page.document.parameters["radius.width"]
    assert (p.dispersion.type, p.fit) == ("array", False)
    assert not poly.poly_model.item(row, 1).isEnabled() and poly.poly_model.item(row, 7).text() == "w.txt"
    assert list(page.logic.kernel_module.dispersion["radius"]["values"]) == [10.0, 20.0]
    page.undo_stack.undo()
    assert page.document.parameters["radius.width"].fit
    assert poly.poly_model.item(row, 1).isEnabled() and poly.poly_model.item(row, 7).text() == ""


def test_a_cancelled_array_file_keeps_the_current_distribution(page, monkeypatch):
    page.chkPolydispersity.setChecked(True)
    poly = page.polydispersity_widget
    row = g.find_row(poly.poly_model, "Distribution of radius")

    def cancelled(r):
        raise OSError

    monkeypatch.setattr(poly, "loadPolydispArray", cancelled)
    depth = len(page.undo_stack._undo_stack)
    poly.onPolyComboIndexChange("array", row)
    combo = poly.lstPoly.indexWidget(poly.poly_model.index(row, 6))
    assert combo.currentText() == "gaussian" and len(page.undo_stack._undo_stack) == depth


def test_constraints_are_document_first_and_not_undoable(page):
    row = g.find_row(page._model_model, "length")
    page.addConstraintToRow(Constraint(param="length", func="2*M1.radius", value_ex="2*M1.radius"), row)
    assert page.document.parameters["length"].constraint.func == "2*M1.radius"
    assert page.document.parameters["length"].fit
    assert not page.undo_stack.can_undo()
    page.deleteConstraintOnParameter("length")
    assert page.document.parameters["length"].constraint is None


def test_deleting_a_simple_constraint_restores_its_bounds(page):
    page.lstParams.selectionModel().select(page._model_model.index(g.find_row(page._model_model, "radius"), 0),
                                           QtCore.QItemSelectionModel.Select | QtCore.QItemSelectionModel.Rows)
    page.addSimpleConstraint()
    assert page.document.parameters["radius"].min == pytest.approx(20.0 - 20.0 / 10000.0)
    page.deleteConstraintOnParameter("radius")
    p = page.document.parameters["radius"]
    assert (p.min, p.max, p.constraint) == (0.0, float("inf"), None)


def test_a_model_switch_keeps_constraints_that_still_resolve(page, messages):
    row = g.find_row(page._model_model, "length")
    page.addConstraintToRow(Constraint(param="length", func="2*M1.radius", value_ex="2*M1.radius"), row)
    g.select_model(page, "Cylinder", "hollow_cylinder")
    assert page.document.parameters["length"].constraint.func == "2*M1.radius"
    assert page.getConstraintsForAllModels() == [("length", "2*M1.radius")]


def test_a_model_switch_drops_constraints_that_no_longer_resolve(page, messages):
    row = g.find_row(page._model_model, "radius")
    page.addConstraintToRow(Constraint(param="radius", func="M1.length/20", value_ex="M1.length/20"), row)
    g.select_model(page, "Sphere", "sphere")
    assert page.document.parameters["radius"].constraint is None
    assert any("Constraints on radius removed" in m for m in messages)


def test_shell_count_changes_are_undoable_and_keep_the_other_values():
    p = g.new_page(data=g.make_data1d("d1", "data1"))
    g.select_model(p, "Sphere", "core_multi_shell")
    g.set_cell(p._model_model, "radius", 1, "66.0")
    g.set_multiplicity(p, 3)
    assert isinstance(p.undo_stack._undo_stack[-1], SnapshotCommand)
    assert p.document.parameters["radius"].value == 66.0
    p.undo_stack.undo()
    assert p.document.selection.multiplicity == 1 and "thickness3" not in p.document.parameters
    assert p.document.parameters["radius"].value == 66.0
    p.undo_stack.redo()
    assert p.document.selection.multiplicity == 3 and "thickness3" in p.document.parameters
    p.shadow_checker.assert_ok()
    p.close()


def test_value_edits_of_one_parameter_coalesce(page):
    g.set_cell(page._model_model, "radius", 1, "21.0")
    g.set_cell(page._model_model, "radius", 1, "22.0")
    assert [type(c) for c in page.undo_stack._undo_stack] == [SetParameterCommand]
    page.undo_stack.undo()
    assert page.document.parameters["radius"].value == 20.0
