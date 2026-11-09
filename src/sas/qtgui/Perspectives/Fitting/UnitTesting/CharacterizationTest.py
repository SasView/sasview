"""
Behaviour characterization of the fit page (FW-MVC-DESIGN.md, Phase 0).

These tests pin today's behaviour, including behaviour that is questionable,
so that the refactor can show it changes nothing by accident. Each test names
the design section it characterizes. A deliberate change of behaviour updates
the test in the same PR as the decision-register entry.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from PySide6 import QtCore, QtWidgets

from sas.qtgui.Perspectives.Fitting.model.commands import SnapshotCommand
from sas.qtgui.Perspectives.Fitting.services import fit as fit_service
from sas.qtgui.Perspectives.Fitting.UnitTesting import golden_support as g


@pytest.fixture(autouse=True)
def _quiet(qapp, monkeypatch):
    monkeypatch.setattr("sas.qtgui.Perspectives.UndoRedo.QtWidgets.QMessageBox", MagicMock())


@pytest.fixture
def page(request):
    p = g.new_page(data=g.make_data1d("d1", "data1"))
    g.select_model(p, "Cylinder", "cylinder")
    yield p
    p.shadow_checker.assert_ok(request)
    p.close()


def rows(page) -> dict:
    """The legacy rows by key; numbers are written in the canonical format (register R-6)."""
    return {r[0]: r for r in page.getFitPage() + page.getFitModel()}


def table_text(item_model) -> list[list[str]]:
    return [[item_model.item(r, c).text() if item_model.item(r, c) else None
             for c in range(item_model.columnCount())] for r in range(item_model.rowCount())]


def requests_during(page, action) -> int:
    before = len(page.theory_requests)
    action()
    QtWidgets.QApplication.processEvents()
    return len(page.theory_requests) - before


def fake_fit(page, fitted: dict, chi2: float = 1.5):
    """Complete a single fit with *fitted* = {name: (value, error)}, as fitComplete sees it."""
    page.fit_service.outcome = lambda res: fitted
    page.onPlot = lambda: None
    page.fitComplete(([[SimpleNamespace(fitness=chi2)]], 0.5))


class TheoryTriggerTest:
    """§3.1 / register R-1: which actions request a theory calculation.

    Only the set is pinned (zero versus at least one request). How many
    requests one action issues is an implementation detail; the controller
    coalesces them to one per transaction.
    """

    def testValueAndBoundEditsDoNotRecalculate(self, page):
        assert requests_during(page, lambda: g.set_cell(page._model_model, "radius", 1, "33")) == 0
        assert requests_during(page, lambda: g.set_cell(page._model_model, "radius", 2, "1")) == 0
        assert requests_during(page, lambda: g.set_cell(page._model_model, "radius", 3, "99")) == 0

    def testFitFlagDoesNotRecalculate(self, page):
        assert requests_during(page, lambda: g.set_checked(page._model_model, "radius")) == 0

    def testUndoRedoOfValuesRecalculates(self, page):
        g.set_cell(page._model_model, "radius", 1, "33")
        g.set_cell(page._model_model, "length", 2, "1")
        assert requests_during(page, page.undo_stack.undo) > 0
        assert requests_during(page, page.undo_stack.undo) > 0
        assert requests_during(page, page.undo_stack.redo) > 0

    def testModelSelectionRecalculates(self, page):
        assert requests_during(page, lambda: g.select_model(page, "Cylinder", "hollow_cylinder")) > 0
        sq = page.cbStructureFactor.findText("hardsphere")
        assert requests_during(page, lambda: page.cbStructureFactor.setCurrentIndex(sq)) > 0

    def testOptionsAndSmearingRecalculate(self, page):
        assert requests_during(page, lambda: page.options_widget.updateMinQ(0.01)) > 0
        assert requests_during(page, lambda: page.smearing_widget.cbSmearing.setCurrentIndex(2)) > 0

    def testPolydispersityToggleRecalculates(self, page):
        """Not in the design's list in §3.1: toggling polydispersity requests theory today."""
        assert requests_during(page, lambda: page.chkPolydispersity.setChecked(True)) > 0

    def testComputeAndFitCompletionRecalculate(self, page):
        assert requests_during(page, page.onPlot) > 0
        g.set_checked(page._model_model, "radius")
        page.fit_service.outcome = lambda res: {"radius": (25.0, 0.5)}
        fit = lambda: page.fitComplete(([[SimpleNamespace(fitness=1.0)]], 0.5))  # noqa: E731
        assert requests_during(page, fit) > 0


class RetentionTest:
    """§2.6: what survives a layout change today.

    onSelectModel re-reads the whole table only when a theory has been
    computed (``model_data``), which is the normal state in the application.
    The tests mock the computation, so they set ``model_data`` themselves.
    """

    @pytest.fixture
    def computed(self, page):
        page.model_data = MagicMock()
        return page

    def testModelSwitchKeepsMainValuesBoundsAndFitFlags(self, computed):
        page = computed
        g.set_cell(page._model_model, "radius", 1, "33.0")
        g.set_cell(page._model_model, "radius", 2, "5.0")
        g.set_cell(page._model_model, "radius", 3, "90.0")
        g.set_checked(page._model_model, "radius")
        g.set_cell(page._model_model, "sld", 1, "2.5")
        g.set_checked(page._model_model, "length")
        g.select_model(page, "Cylinder", "hollow_cylinder")
        assert rows(page)["radius"][:6] == ["radius", "True", "33.0", None, "5.0", "90.0"]
        assert rows(page)["sld"][2] == "2.5"
        assert rows(page)["length"][1] == "True"
        assert page.kernel().details["radius"][1:] == [5.0, 90.0]

    def testModelSwitchKeepsPolydispersity(self, computed):
        page = computed
        page.chkPolydispersity.setChecked(True)
        poly = page.polydispersity_widget.poly_model
        g.set_cell(poly, "Distribution of radius", 1, "0.2")
        g.set_checked(poly, "Distribution of radius")
        g.select_model(page, "Cylinder", "hollow_cylinder")
        assert page.chkPolydispersity.isChecked()
        assert rows(page)["radius.width"][1:3] == ["True", "0.2"]
        assert page.kernel().getParam("radius.width") == pytest.approx(0.2)

    def testWithoutTheoryEverythingIsRetained(self, page):
        """Register R-9, changed in Phase 5: retention reads the document's current state, so
        fit-flag and polydispersity edits are kept also before any theory has been computed
        (before, only the snapshot taken at the last main-table value edit was)."""
        g.set_cell(page._model_model, "radius", 1, "33.0")
        g.set_checked(page._model_model, "length")
        page.chkPolydispersity.setChecked(True)
        g.set_cell(page.polydispersity_widget.poly_model, "Distribution of radius", 1, "0.2")
        g.select_model(page, "Cylinder", "hollow_cylinder")
        assert rows(page)["radius"][2] == "33.0"
        assert rows(page)["length"][1] == "True"
        assert page.kernel().getParam("radius.width") == pytest.approx(0.2)

    def testUndoOfAModelSwitchRestoresTheModelAndItsValues(self, page):
        g.set_cell(page._model_model, "radius", 1, "33.0")
        g.select_model(page, "Cylinder", "hollow_cylinder")
        g.set_cell(page._model_model, "radius", 1, "44.0")
        page.undo_stack.undo()          # the value edit
        page.undo_stack.undo()          # the model switch
        assert page.cbModel.currentText() == "cylinder"
        assert rows(page)["radius"][2] == "33.0"
        page.undo_stack.redo()
        assert page.cbModel.currentText() == "hollow_cylinder"
        assert rows(page)["radius"][2] == "33.0"

    def testModelSwitchClearsErrors(self, computed):
        page = computed
        g.set_checked(page._model_model, "radius")
        fake_fit(page, {"radius": (25.5, 0.75)})
        assert page.has_error_column
        g.select_model(page, "Cylinder", "hollow_cylinder")
        assert not page.has_error_column
        assert rows(page)["radius"][:4] == ["radius", "True", "25.5", None]

    def testStructureFactorSwitchKeepsValues(self, page):
        g.set_cell(page._model_model, "radius", 1, "33.0")
        page.cbStructureFactor.setCurrentIndex(page.cbStructureFactor.findText("hardsphere"))
        assert rows(page)["radius"][2] == "33.0"
        assert page.kernel().getParam("radius") == 33.0

    def testShrunkShellsComeBackWithDefaults(self):
        p = g.new_page(data=g.make_data1d("d1", "data1"))
        g.select_model(p, "Sphere", "core_multi_shell")
        g.set_multiplicity(p, 3)
        g.set_cell(p._model_model, "thickness3", 1, "77.0")
        g.set_cell(p._model_model, "radius", 1, "66.0")
        g.set_multiplicity(p, 2)
        g.set_multiplicity(p, 3)
        assert rows(p)["thickness3"][2] == "40.0"
        assert rows(p)["radius"][2] == "66.0"
        p.close()


class PasteAndLoadTest:
    """§2.3: paste applies onto the current model; project load selects the saved model."""

    @pytest.fixture
    def cylinder_text(self, page):
        g.set_cell(page._model_model, "radius", 1, "44.0")
        return page.full_copy_data()

    @pytest.fixture
    def message_box(self, monkeypatch):
        box = MagicMock()
        monkeypatch.setattr("sas.qtgui.Perspectives.Fitting.FittingWidget.QtWidgets.QMessageBox", box)
        return box

    @pytest.fixture
    def sphere_page(self):
        p = g.new_page(data=g.make_data1d("d2", "data2"))
        g.select_model(p, "Sphere", "sphere")
        yield p
        p.close()

    def testPasteOntoOtherModelAsksFirstAndCancelChangesNothing(self, cylinder_text, message_box, sphere_page):
        message_box.return_value.exec_.return_value = QtWidgets.QMessageBox.Cancel
        before = rows(sphere_page)
        QtWidgets.QApplication.clipboard().setText(cylinder_text)
        sphere_page.clipboard_paste()
        assert message_box.called
        assert rows(sphere_page) == before

    def testPasteKeepsCurrentModelAndRecordsOneCommand(self, cylinder_text, message_box, sphere_page):
        """Register R-7, changed in Phase 5: a paste is one undoable step (§2.3)."""
        message_box.return_value.exec_.return_value = QtWidgets.QMessageBox.Ok
        depth = len(sphere_page.undo_stack._undo_stack)
        before = rows(sphere_page)
        QtWidgets.QApplication.clipboard().setText(cylinder_text)
        sphere_page.clipboard_paste()
        assert sphere_page.cbModel.currentText() == "sphere"
        assert rows(sphere_page)["radius"][2] == "44.0"
        pushed = sphere_page.undo_stack._undo_stack[depth:]
        assert [type(cmd) for cmd in pushed] == [SnapshotCommand]
        sphere_page.undo_stack.undo()
        assert rows(sphere_page) == before

    def testProjectLoadSelectsModelAndKeepsTabName(self, cylinder_text):
        line_dict = {}
        for line in cylinder_text.replace("tab_name,M1", "tab_name,renamed").split(":")[1:]:
            content = line.split(",")
            if len(content) > 1:
                line_dict[content[0]] = content[1:]
        p = g.new_page(tab_id=3, data=g.make_data1d("d3", "data3"))
        p.createPageForParameters(line_dict)
        assert p.cbModel.currentText() == "cylinder"
        assert rows(p)["radius"][2] == "44.0"
        # The page takes the saved name, and saves it again (R-3, changed in Phase 3a)
        assert p.kernel().name == "renamed"
        assert rows(p)["tab_name"] == ["tab_name", "renamed"]
        # Register R-8, changed in Phase 5: a project load clears the history (§2.3)
        assert not p.undo_stack.can_undo()
        p.close()


class FitUndoTest:
    """§3.7 / register R-2: undo and redo of a single fit."""

    def testUndoAndRedoBothClearErrorsAndKeepChi2(self, page):
        g.set_checked(page._model_model, "radius")
        fake_fit(page, {"radius": (25.5, 0.75)}, chi2=1.5)
        assert rows(page)["radius"][2:4] == ["25.5", "0.75"]
        assert page.lblChi2Value.text() == "1.5"

        page.undo_stack.undo()
        assert rows(page)["radius"][2:4] == ["20.0", None]
        assert not page.has_error_column
        assert page.lblChi2Value.text() == "1.5"

        page.undo_stack.redo()
        assert rows(page)["radius"][2:4] == ["25.5", None]
        assert not page.has_error_column
        assert page.chi2 == 1.5


class BatchCompletionTest:
    """Register B-1: a batch fit does not change the page and is not undoable. B-4: its outcomes are
    routed by dataset id."""

    def testBatchCompletionLeavesParametersUnchanged(self):
        p = g.new_page(data=[g.make_data1d("b1", "same"), g.make_data1d("b2", "same")])
        g.select_model(p, "Cylinder", "cylinder")
        g.set_checked(p._model_model, "radius")
        p.undo_stack.clear()
        before = table_text(p._model_model)
        p.fit_service.outcome = lambda res: {"radius": (31.0, 0.5)}
        results = [[SimpleNamespace(fitness=1.0)], [SimpleNamespace(fitness=2.0)]]
        p.batchFitComplete((results, 0.5))
        assert table_text(p._model_model) == before
        assert p.kernel().getParam("radius") == 20.0
        assert not p.undo_stack.can_undo()
        # Fixed in Phase 7 (B-4): the page stays on its dataset
        assert p.data_index == 0
        # One theory per dataset, each from that dataset's fitted kernel, routed by its id
        batch_requests = p.theory_requests[-2:]
        assert [r.kernel.getParam("radius") for r in batch_requests] == [31.0, 31.0]
        assert [r.dataset_id for r in batch_requests] == p.document.dataset_order
        assert [r.data for r in batch_requests] == [p.document.datasets[i].data for i in p.document.dataset_order]
        p.close()


class LiveDefectRegressionTest:
    """Phase 0 defect fixes (FW-REFACTOR-DESIGN.md §1.2)."""

    def testOneContextMenuHandlerPerTable(self, page):
        signal = QtCore.SIGNAL("customContextMenuRequested(QPoint)")
        for view in (page.lstParams, page.lstPoly, page.lstMagnetic):
            assert view.receivers(signal) == 1

    def testAFitRunsOnItsOwnKernel(self, page, monkeypatch):
        """Since Phase 6 the fitter gets a new engine instance built from the document, so a failed
        fit cannot leave the live kernel corrupted (the Phase 0 fix restored a copy)."""
        models = []

        class Recording(g._RecordingFit):
            def set_model(self, model, *args, **kwargs):
                models.append(model)
                super().set_model(model, *args, **kwargs)

        monkeypatch.setattr(fit_service, "Fit", Recording)
        g.set_checked(page._model_model, "radius")
        page.controller.prepare_fitters()
        assert models and models[0] is not page.kernel()
        assert models[0].getParam("radius") == page.kernel().getParam("radius") == 20.0
        page.fitComplete(None)
        assert page.kernel().getParam("radius") == 20.0
        assert not hasattr(page, "kernel_module")
