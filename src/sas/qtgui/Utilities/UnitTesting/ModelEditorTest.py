import pytest

from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.ModelEditor import ModelEditor
from sas.qtgui.Utilities.PythonSyntax import PythonHighlighter


class ModelEditorTest:

    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the editor'''
        w = ModelEditor(None)
        yield w
        w.close()

    def testDefaults(self, widget):
        """Test the GUI in its default state"""
        assert isinstance(widget.highlight, PythonHighlighter)

    def testEdit(self, widget):
        """Test that a signal is emitted on edit"""
        spy_signal = QtSignalSpy(widget, widget.modelModified)

        # Edit text
        text = "test"
        widget.txtEditor.setPlainText(text)

        # Assure the signal got emitted
        assert spy_signal.count() == 1

        # Assure getModel() returns right content
        assert text, widget.txtEditor.toPlainText()


