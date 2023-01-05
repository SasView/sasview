import sys
import logging

import pytest

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from sas.sasview.UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.sasview.Utilities.ModelEditor import ModelEditor
from sas.sasview.Utilities.PythonSyntax import PythonHighlighter


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


