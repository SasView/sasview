"""
The Phase 2 shadow document (FW-MVC-DESIGN.md §6): how legacy writers reach FittingWidget.document.
"""
from unittest.mock import MagicMock

import pytest
from PySide6 import QtGui

from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.Constraint import Constraint
from sas.qtgui.Perspectives.Fitting.DocumentShadow import mirrors
from sas.qtgui.Perspectives.Fitting.model.events import (
    ConstraintsChanged,
    FlagsChanged,
    ModelChanged,
    OptionsChanged,
    ParametersChanged,
)
from sas.qtgui.Perspectives.Fitting.model.parameters import PageMode
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())
    monkeypatch.setattr(FittingUtilities, "checkConstraints", lambda *a, **kw: None)


@pytest.fixture
def page():
    p = g.new_page(data=g.make_data1d("d1", "data1"))
    g.select_model(p, "Cylinder", "cylinder")
    p.changes = []
    p.document.subscribe(p.changes.append)
    yield p
    p.shadow_checker.assert_ok()
    p.close()


def testSeededAtConstruction():
    page = g.new_page()
    assert page.document.revision > 0 and page.document.identity.mnemonic == "M1"
    assert not page.document.is_loaded()
    page.close()


def testModelSelectionReseeds(page):
    assert page.document.selection.model == "cylinder"
    g.select_model(page, "Cylinder", "hollow_cylinder")
    assert page.document.selection.model == "hollow_cylinder"
    assert "thickness" in page.document.parameters
    assert any(c.get(ModelChanged) for c in page.changes)


def testValueEditIsOneFineGrainedTransaction(page):
    g.set_cell(page._model_model, "radius", 1, "33.0")
    assert len(page.changes) == 1
    change = page.changes[0]
    assert change.get(ParametersChanged) == ParametersChanged(frozenset({"radius"}), frozenset({"value"}))
    assert change.get(ModelChanged) is None
    assert page.document.parameters["radius"].value == 33.0


def testFitFlagBoundsAndPoly(page):
    g.set_checked(page._model_model, "length")
    g.set_cell(page._model_model, "length", 3, "900.0")
    page.chkPolydispersity.setChecked(True)
    g.set_cell(page.polydispersity_widget.poly_model, "Distribution of radius", 1, "0.25")
    doc = page.document
    assert doc.parameters["length"].fit and doc.parameters["length"].max == 900.0
    assert doc.flags.polydispersity and doc.parameters["radius.width"].value == 0.25
    assert any(c.get(FlagsChanged) for c in page.changes)


def testOptionsAndConstraint(page):
    page.options_widget.updateMinQ(0.01)
    assert page.document.options.qmin == 0.01
    assert any(c.get(OptionsChanged) for c in page.changes)
    page.addConstraintToRow(Constraint(param="radius", func="M1.length/10"), g.find_row(page._model_model, "radius"))
    assert page.document.parameters["radius"].constraint.func == "M1.length/10"
    assert page.changes[-1].get(ConstraintsChanged).keys == {"radius"}


def testRenameReachesIdentity(page):
    with page.shadow.operation("identity"):
        page.logic.kernel_module.name = "sample"
    assert page.document.identity.mnemonic == "sample"
    assert "sample.radius" in page.document.symbol_table()


def testBatchPage():
    page = g.new_page(data=[g.make_data1d("b1", "same"), g.make_data1d("b2", "same")])
    g.select_model(page, "Cylinder", "cylinder")
    doc = page.document
    assert doc.mode is PageMode.BATCH and doc.dataset_order == ["b1", "b2"]
    page.onSelectBatchFilename(1)
    assert doc.active_id == "b2"
    page.shadow_checker.assert_ok()
    page.close()


def testUndoRedoAreMirrored(page):
    g.set_cell(page._model_model, "radius", 1, "33.0")
    page.undo_stack.undo()
    assert page.document.parameters["radius"].value == 20.0
    page.undo_stack.redo()
    assert page.document.parameters["radius"].value == 33.0


def testNestedOperationsCommitOnce(page):
    revision = page.document.revision
    with page.shadow.operation("parameters"):
        g.set_cell(page._model_model, "radius", 1, "31.0")
        g.set_cell(page._model_model, "length", 1, "401.0")
        assert page.document.revision == revision      # nothing committed yet
    assert page.document.revision == revision + 1
    assert page.changes[-1].get(ParametersChanged).keys == {"radius", "length"}


def testDataLoadIsMirrored():
    page = g.new_page()
    g.select_model(page, "Cylinder", "cylinder")
    explorer, items = g.data_items([g.make_data1d("d9", "late")])
    page.dataFromItems(items[0])
    assert page.document.is_loaded() and page.document.active_id == "d9"
    assert page.document.options.qmin == 0.005
    page.shadow_checker.assert_ok()
    page.close()


def testUnmirroredWriteIsCaught(page):
    """A legacy write that bypasses the shadow is reported by the invariant."""
    cell = page._model_model.item(g.find_row(page._model_model, "radius"), 1)
    page._model_model.blockSignals(True)
    cell.setText("77.0")
    with pytest.raises(AssertionError, match="77"):
        page.shadow_checker.assert_ok()
    cell.setText("20")                                  # undo it, so the fixture's check passes
    page._model_model.blockSignals(False)


def testReadBackFailureIsRecordedNotRaised(page):
    page._model_model.appendRow([QtGui.QStandardItem("junk")])
    with page.shadow.operation("parameters"):
        pass
    assert page.shadow.errors and "ShadowError" in page.shadow.errors[0]
    page.shadow.errors.clear()
    page._model_model.removeRow(page._model_model.rowCount() - 1)


def testDecoratorPassesOnlyAcceptedSignalArguments():
    class Owner:
        shadow = None
        calls = []

        @mirrors("parameters")
        def slot(self, top, bottom):
            self.calls.append((top, bottom))

    Owner().slot(1, 2, ["roles"])
    assert Owner.calls == [(1, 2)]
