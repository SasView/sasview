import os

import pytest
from pyausaxs.gui.core import script as rbscript
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtTest import QTest

import sas.qtgui.Calculators.RigidbodyRefinement as RigidbodyRefinement
from sas.qtgui.Calculators.RigidbodyStructure import ScriptDiffDialog, StructurePane

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "test", "sascalculator", "data")
PDB = os.path.abspath(os.path.join(DATA, "LAR1-2.pdb"))


class RigidbodyStructureTest:
    """Test the structure manager of the rigid-body refinement calculator"""

    @pytest.fixture(autouse=True)
    def calculator(self, qapp, tmp_path, monkeypatch):
        """A calculator with a structure split into three bodies, its script cache and output directory kept out of the user's own"""
        monkeypatch.setattr(RigidbodyRefinement.RigidBodyRefinement, "_scriptCachePath", staticmethod(lambda: str(tmp_path / "script.txt")))
        monkeypatch.setattr(RigidbodyRefinement, "get_app_dir", lambda: tmp_path)
        c = RigidbodyRefinement.RigidBodyRefinement(None)
        c.gui.structureField.edit.setText(PDB)
        c.gui.structureField.edit.editingFinished.emit()
        c.gui.txtSplits.setText("9 99")
        c.gui.txtSplits.textEdited.emit("9 99")

        yield c

        c.gui.close()

    @pytest.fixture
    def pane(self, calculator) -> StructurePane:
        calculator.onViewStructure()
        return calculator.structurePane

    @staticmethod
    def names(pane) -> list[str]:
        return [pane.bodyTree.topLevelItem(i).text(0) for i in range(pane.bodyTree.topLevelItemCount())]

    @staticmethod
    def click(pane, row: int, modifier=QtCore.Qt.KeyboardModifier.NoModifier):
        item = pane.bodyTree.topLevelItem(row)
        QTest.mouseClick(pane.bodyTree.viewport(), QtCore.Qt.MouseButton.LeftButton, modifier,
                         pane.bodyTree.visualItemRect(item).center())

    def testOpensAsATab(self, calculator):
        """View opens the structure as a closable tab listing its bodies, and reuses it for the same structure"""
        assert calculator.gui.structureField.viewButton.isEnabled()
        calculator.gui.structureField.viewButton.click()
        pane = calculator.structurePane
        assert calculator.gui.tabs.currentWidget() is pane
        assert calculator.gui.tabs.tabText(1) == "Structure: LAR1-2"
        assert self.names(pane) == ["b1", "b2", "b3"]
        assert pane.btnRefresh.isHidden()

        calculator.gui.showRefinementTab()
        calculator.onViewStructure()
        assert calculator.structurePane is pane and calculator.gui.tabs.count() == 2

        calculator._onTabCloseRequested(1)
        assert calculator.structurePane is None and calculator.gui.tabs.count() == 1

    def testMergeSelectedBodies(self, pane, qapp):
        """Clicking and ctrl-clicking rows selects bodies, which an empty Merge field then stands in for"""
        pane.show()
        self.click(pane, 0)
        self.click(pane, 2, QtCore.Qt.KeyboardModifier.ControlModifier)
        assert pane.model.highlighted == {(0, None), (2, None)}
        assert pane.rowMerge.isReady()  # lit up: applying it would merge the selection
        assert pane.btnClearSelection.isVisibleTo(pane) or pane._redrawTimer.isActive()

        pane.rowMerge.apply.trigger()
        assert pane.model.elements == ["merge b1 b3"]
        assert self.names(pane) == ["b1", "b2"]
        assert pane.appliedTree.topLevelItemCount() == 1
        assert pane.lblStatus.text() == "Applied: merge b1 b3"

        pane._removeElement(0)
        assert pane.model.elements == [] and self.names(pane) == ["b1", "b2", "b3"]

    def testRejectedActionKeepsTheField(self, pane):
        """An action the backend refuses leaves the structure and the typed text alone, and says why"""
        pane.rowMerge.edit.setText("b1 nonexistent")
        pane.rowMerge.apply.trigger()
        assert pane.model.elements == []
        assert pane.rowMerge.text() == "b1 nonexistent"
        assert pane.lblStatus.text().startswith("Rejected")

    def testRenameInPlace(self, pane, qapp):
        """Double-clicking a body's name renames it in place, leaving the selection as it was"""
        pane.show()
        item = pane.bodyTree.topLevelItem(1)
        pane._onBodyClicked(item, 0)  # a double-click's first press selects the row; the double-click undoes that
        pane._onBodyDoubleClicked(item, 0)
        editor = pane.bodyTree.viewport().findChild(QtWidgets.QLineEdit)
        assert editor is not None and editor.text() == "b2"
        editor.setText("core")
        QTest.keyClick(editor, QtCore.Qt.Key.Key_Return)
        qapp.processEvents()  # the delegate commits and closes its editor through a queued call
        assert pane.model.elements == ["rename b2 core"]
        assert self.names(pane) == ["b1", "core", "b3"]
        assert pane.model.highlighted == set()

    def testResidueSelectionSplitsABody(self, pane):
        """Clicked residues stand in for the residues of a per-body split"""
        assert not pane.rowBodySplit.isReady()
        pane._toggleSelectedResidue(1, 50)  # b2 spans residues 9-98
        assert pane.rowBodySplit.isReady()
        pane.rowBodySplit.apply.trigger()
        assert pane.model.elements == ["split b2 50"]
        assert len(self.names(pane)) == 4
        assert pane.model.selected_residues == set()

    def testResplitWholeStructure(self, pane):
        """The splits field re-splits the whole structure, and a bad value is reverted"""
        pane.rowSplits.edit.setText("50")
        pane.rowSplits.apply.trigger()
        assert self.names(pane) == ["b1", "b2"]
        pane.rowSplits.edit.setText("not a residue")
        pane.rowSplits.apply.trigger()
        assert pane.rowSplits.text() == "50"
        assert self.names(pane) == ["b1", "b2"]

    def testSendToScript(self, calculator, pane, mocker):
        """Staged changes reach the script only once the diff is confirmed, and then return to the refinement"""
        assert not pane.btnSend.isEnabled()  # nothing staged yet
        pane.rowMerge.edit.setText("b1 b2")
        pane.rowMerge.apply.trigger()
        assert pane.btnSend.isEnabled()
        before = calculator.gui.getText()

        mocker.patch.object(pane, "_confirmChange", return_value=False)
        pane.btnSend.click()
        assert calculator.gui.getText() == before and pane.model.elements

        pane._confirmChange.return_value = True
        pane.btnSend.click()
        assert "merge b1 b2" in calculator.gui.getText()
        assert calculator.gui.tabs.currentWidget() is calculator.gui.refinementTab
        assert pane.model.elements == [] and self.names(pane) == ["b1", "b3"]

        assert not pane.btnSend.isEnabled()  # sent, so nothing is left to send

    def testSentSplitsReachTheSplitsField(self, calculator, pane, mocker):
        """A re-split sent to the script shows up in the calculator's Splits field"""
        mocker.patch.object(pane, "_confirmChange", return_value=True)
        pane.rowSplits.edit.setText("50")
        pane.rowSplits.apply.trigger()
        pane.btnSend.click()
        assert rbscript.load_value(calculator.gui.getText(), "split") == "50"
        assert calculator.gui.txtSplits.text() == "50"

    def testStaleAfterScriptEdit(self, calculator, pane, mocker):
        """Editing the script flags the view as stale when switching back to it; refreshing discards the staged changes after asking"""
        pane.rowDelete.edit.setText("b3")
        pane.rowDelete.apply.trigger()
        calculator.gui.showRefinementTab()
        calculator.gui.txtSplits.textEdited.emit("50")
        calculator.gui.tabs.setCurrentWidget(pane)
        assert not pane.btnRefresh.isHidden()

        ask = mocker.patch.object(QtWidgets.QMessageBox, "question", return_value=QtWidgets.QMessageBox.StandardButton.Yes)
        pane.btnRefresh.click()
        ask.assert_called_once()
        assert pane.btnRefresh.isHidden()
        assert pane.model.elements == [] and self.names(pane) == ["b1", "b2"]
        assert pane.rowSplits.text() == "50"

    def testCameraFollowsTabSwitches(self, calculator, pane):
        """The structure manager adopts the preview's camera angle when switched to, and hands its own back"""
        calculator.gui.showRefinementTab()
        calculator.gui.structureAxes.view_init(elev=10, azim=20, roll=0)
        calculator.gui.tabs.setCurrentWidget(pane)
        assert pane.cameraOrientation()[:2] == (10, 20)
        pane.setCameraOrientation((30, 40, 0))
        calculator.gui.showRefinementTab()
        assert (calculator.gui.structureAxes.elev, calculator.gui.structureAxes.azim) == (30, 40)

    def testLockedWhileRunning(self, calculator, pane):
        """The controls are locked while a refinement owns the backend"""
        calculator.gui.setRunning(True)
        pane.setBusy(True)
        assert not calculator.gui.structureField.viewButton.isEnabled()
        assert not pane.rowMerge.isEnabled()
        pane.setBusy(False)
        calculator.gui.setRunning(False)
        assert pane.rowMerge.isEnabled() and calculator.gui.structureField.viewButton.isEnabled()

    def testClosingWithStagedChangesAsks(self, calculator, pane, mocker):
        """Closing the tab with unsent changes asks first"""
        pane.rowDelete.edit.setText("b3")
        pane.rowDelete.apply.trigger()
        mocker.patch.object(QtWidgets.QMessageBox, "question", return_value=QtWidgets.QMessageBox.StandardButton.No)
        calculator._onTabCloseRequested(1)
        assert calculator.structurePane is pane

    def testViewBarAndFoldedSettings(self, pane):
        """The backbone toggle only applies once atoms are drawn, and the fit's tolerance stays folded away until asked for"""
        assert not pane.chipBackbone.isEnabled()
        pane.chipAtoms.setChecked(True)
        assert pane.chipBackbone.isEnabled()
        pane._homeView()

        assert not pane.txtTolerance.isVisibleTo(pane)
        pane.btnTolerance.click()
        assert pane.txtTolerance.isVisibleTo(pane)

    def testViewIsPacedForDragging(self, pane, qtbot):
        """A burst of redraw requests renders once, and the hover readout waits until no button is held"""
        canvas = pane.canvas
        draws = []
        canvas.mpl_connect("draw_event", lambda _e: draws.append(1))
        qtbot.wait(50)
        draws.clear()
        for _ in range(20):
            canvas.draw_idle()
        qtbot.waitUntil(lambda: bool(draws), timeout=1000)
        qtbot.wait(50)
        assert len(draws) == 1

        hovered = []
        canvas.hovered.connect(hovered.append)
        centre = QtCore.QPointF(canvas.width() / 2, canvas.height() / 2)

        def move(buttons):
            event = QtGui.QMouseEvent(QtCore.QEvent.Type.MouseMove, centre, canvas.mapToGlobal(centre), QtCore.Qt.MouseButton.NoButton,
                                      buttons, QtCore.Qt.KeyboardModifier.NoModifier)
            QtWidgets.QApplication.sendEvent(canvas, event)

        move(QtCore.Qt.MouseButton.LeftButton)
        qtbot.wait(80)
        assert hovered == []
        move(QtCore.Qt.MouseButton.NoButton)
        qtbot.waitUntil(lambda: bool(hovered), timeout=1000)

    def testDiffDialog(self, qapp):
        """The diff shows both scripts row-aligned, with the changed lines marked on each side"""
        dialog = ScriptDiffDialog("a\nb\nc\n", "a\nB\nextra\nc\n")
        assert dialog.original.toPlainText().split("\n") == ["a", "b", "", "c"]
        assert dialog.changed.toPlainText().split("\n") == ["a", "B", "extra", "c"]
        assert len(dialog.original.extraSelections()) == 1
        assert len(dialog.changed.extraSelections()) == 2
        dialog.close()
