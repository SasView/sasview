import os

import pytest
from pyausaxs.gui.core import script as rbscript
from PySide6 import QtWidgets

import sas.qtgui.Calculators.RigidbodyRefinement as RigidbodyRefinement

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "test", "sascalculator", "data")
PDB, DAT = os.path.abspath(os.path.join(DATA, "LAR1-2.pdb")), os.path.abspath(os.path.join(DATA, "LAR1-2.dat"))


class RigidbodyRefinementTest:
    """Test the rigid-body refinement calculator"""

    @pytest.fixture(autouse=True)
    def calculator(self, qapp, tmp_path, monkeypatch):
        """Create/Destroy the calculator, with its script cache and output directory kept out of the user's own"""
        monkeypatch.setattr(RigidbodyRefinement.RigidBodyRefinement, "_scriptCachePath", staticmethod(lambda: str(tmp_path / "script.txt")))
        monkeypatch.setattr(RigidbodyRefinement, "get_app_dir", lambda: tmp_path)
        c = RigidbodyRefinement.RigidBodyRefinement(None)

        yield c

        c.gui.close()

    def testDefaults(self, calculator, tmp_path):
        """The default script writes its output under the app directory, with an empty load block"""
        text = calculator.gui.getText()
        assert calculator.gui.windowTitle() == "Rigid-body refinement"
        assert rbscript.LOAD_BLOCK_RE.search(text)
        output = rbscript.unquote_script_value(rbscript.OUTPUT_RE.search(text).group(2))
        assert output == os.path.join(str(tmp_path), "rigidbody") + os.sep
        assert calculator.gui.structureField.text() == ""

    def testInputsWriteTheLoadBlock(self, calculator):
        """Each input field rewrites only its own line of the load block, and a structure finds its SAXS data"""
        calculator.gui.structureField.edit.setText(PDB)
        calculator.gui.structureField.edit.editingFinished.emit()
        text = calculator.gui.getText()
        assert rbscript.load_value(text, "pdb") == PDB
        assert rbscript.load_value(text, "saxs") == DAT  # found next to the structure
        assert calculator.gui.saxsField.text() == DAT

        calculator.gui.txtSplits.textEdited.emit("9, 99")
        assert rbscript.load_value(calculator.gui.getText(), "split") == "9, 99"
        assert calculator.gui.getText().endswith(text[text.index("save initial_state.pdb"):])

    def testEditingTheFieldsIsUndoable(self, calculator):
        """A rewrite of the load block is one undoable edit"""
        before = calculator.gui.getText()
        calculator.gui.txtSplits.textEdited.emit("50")
        calculator.gui.editor.undo()
        assert calculator.gui.getText() == before

    def testReset(self, calculator, mocker):
        """Reset restores the default script but keeps the load block"""
        calculator.gui.txtSplits.textEdited.emit("50")
        calculator.gui.replaceText(calculator.gui.getText() + "\nsymmetry c2\n")
        mocker.patch.object(QtWidgets.QMessageBox, "question", return_value=QtWidgets.QMessageBox.StandardButton.Yes)
        calculator.onResetScript()
        text = calculator.gui.getText()
        assert "symmetry c2" not in text
        assert rbscript.load_value(text, "split") == "50"

    def testScriptIsRestoredNextSession(self, calculator, qapp):
        """The script is kept across sessions"""
        calculator.gui.txtSplits.textEdited.emit("42")
        calculator.gui.close()
        again = RigidbodyRefinement.RigidBodyRefinement(None)
        assert rbscript.load_value(again.gui.getText(), "split") == "42"
        assert again.gui.txtSplits.text() == "42"
        again.gui.close()

    def testHighlighting(self, calculator):
        """Unknown first tokens are flagged once the vocabulary is known, and scope openers pair with their end"""
        calculator.gui.highlighter.set_vocabulary({"load", "print"}, {"pdb"})
        calculator.gui.replaceText("loop\n    bogus\nend\n")
        block = calculator.gui.editor.document().findBlockByNumber(1)
        formats = block.layout().formats()
        assert any(f.format.foreground().color().name() == "#ff0000" for f in formats)
        assert block.previous().userState() == 1

    def testValidateAndRun(self, calculator, qtbot, mocker):
        """Validation and a short refinement run on a worker thread, and the fit is plotted and sent to the Data Explorer"""
        send = mocker.patch.object(calculator, "_sendResultsToDataExplorer")
        calculator.show()
        calculator.onStructureCommitted(PDB)
        calculator.gui.txtSplits.textEdited.emit("9 99")
        calculator.gui.replaceText(calculator.gui.getText().replace("iterations 100", "iterations 10"))

        calculator.onValidate()
        assert calculator.worker.running()
        qtbot.waitUntil(lambda: not calculator.worker.running(), timeout=60000)
        assert "Validation successful." in calculator.gui.outputPane.toPlainText()

        calculator.onRun()
        assert not calculator.gui.btnStop.isHidden()
        qtbot.waitUntil(lambda: not calculator.worker.running(), timeout=120000)
        output = calculator.gui.outputPane.toPlainText()
        assert "Refinement completed." in output, output
        assert len(calculator.gui._fitTabs) == 2
        send.assert_called_once()
        assert calculator.gui.btnStop.isHidden() and calculator.gui.btnRun.isEnabled()

    def testStructurePreview(self, calculator):
        """The structure tab draws the script's bodies, and is only rebuilt for structural edits"""
        calculator.onStructureCommitted(PDB)
        calculator.gui.txtSplits.textEdited.emit("9 99")
        calculator._updatePreview()
        data = calculator.preview.data
        assert data is not None
        assert len(set(data["body"].tolist())) == 3
        calculator.gui.replaceText(calculator.gui.getText().replace("iterations 100", "iterations 7"))
        calculator._updatePreview()
        assert calculator.preview.data is data

    def testStop(self, calculator, qtbot, mocker):
        """Stopping a refinement ends it early, still reporting the best conformation found so far"""
        mocker.patch.object(calculator, "_sendResultsToDataExplorer")
        calculator.show()
        calculator.onStructureCommitted(PDB)
        calculator.gui.txtSplits.textEdited.emit("9 99")
        calculator.gui.replaceText(calculator.gui.getText().replace("iterations 100", "iterations 100000"))
        calculator.onRun()
        qtbot.waitUntil(lambda: "Initial chi2" in calculator.gui.outputPane.toPlainText(), timeout=60000)
        calculator.onStop()
        assert not calculator.gui.btnStop.isEnabled()
        qtbot.waitUntil(lambda: not calculator.worker.running(), timeout=60000)
        assert "Refinement stopped." in calculator.gui.outputPane.toPlainText()
        assert len(calculator.gui._fitTabs) == 2
