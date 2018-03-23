import sys
import unittest
import logging

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# set up import paths
import sas.qtgui.path_prepare

from UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Utilities.ModelEditor import ModelEditor
from sas.qtgui.Utilities.PythonSyntax import PythonHighlighter

if not QApplication.instance():
    app = QApplication(sys.argv)

class ModelEditorTest(unittest.TestCase):
    def setUp(self):
        """
        Prepare the editor
        """
        self.widget = ModelEditor(None)

    def tearDown(self):
        """Destroy the DataOperationUtility"""
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertIsInstance(self.widget.highlight, PythonHighlighter)

    def testEdit(self):
        """Test that a signal is emitted on edit"""
        spy_signal = QtSignalSpy(self.widget, self.widget.modelModified)

        # Edit text
        text = "test"
        self.widget.txtEditor.setPlainText(text)

        # Assure the signal got emitted
        self.assertEqual(spy_signal.count(), 1)

        # Assure getModel() returns right content
        self.assertTrue(text, self.widget.txtEditor.toPlainText())


