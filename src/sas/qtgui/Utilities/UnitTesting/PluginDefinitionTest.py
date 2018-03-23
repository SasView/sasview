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
from sas.qtgui.Utilities.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.PythonSyntax import PythonHighlighter

#if not QApplication.instance():
#    app = QApplication(sys.argv)
app = QApplication(sys.argv)

class PluginDefinitionTest(unittest.TestCase):
    def setUp(self):
        """
        Prepare the editor
        """
        self.widget = PluginDefinition(None)

    def tearDown(self):
        """Destroy the DataOperationUtility"""
        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertIsInstance(self.widget.highlight, PythonHighlighter)
        self.assertIsInstance(self.widget.parameter_dict, dict)
        self.assertIsInstance(self.widget.pd_parameter_dict, dict)

        self.assertEqual(len(self.widget.model), 6)
        self.assertIn("filename", self.widget.model.keys())
        self.assertIn("overwrite", self.widget.model.keys())
        self.assertIn("description", self.widget.model.keys())
        self.assertIn("parameters", self.widget.model.keys())
        self.assertIn("pd_parameters", self.widget.model.keys())
        self.assertIn("text", self.widget.model.keys())

    def testOnOverwrite(self):
        """See what happens when the overwrite checkbox is selected"""
        spy_signal = QtSignalSpy(self.widget, self.widget.modelModified)

        # check the default
        self.assertFalse(self.widget.chkOverwrite.isChecked())

        # Change the state
        self.widget.chkOverwrite.setChecked(True)

        # Check the signal
        self.assertEqual(spy_signal.count(), 1)

        # model dict updated
        self.assertTrue(self.widget.model['overwrite'])

    def testOnPluginNameChanged(self):
        """See what happens when the name of the plugin changes"""
        spy_signal = QtSignalSpy(self.widget, self.widget.modelModified)

        # Change the name
        new_text = "Duck season"
        self.widget.txtName.setText(new_text)
        self.widget.txtName.editingFinished.emit()

        # Check the signal
        self.assertEqual(spy_signal.count(), 1)

        # model dict updated
        self.assertTrue(self.widget.model['filename'] == new_text)

    def testOnDescriptionChanged(self):
        """See what happens when the description of the plugin changes"""
        spy_signal = QtSignalSpy(self.widget, self.widget.modelModified)

        # Change the name
        new_text = "Rabbit season"
        self.widget.txtDescription.setText(new_text)
        self.widget.txtDescription.editingFinished.emit()

        # Check the signal
        self.assertEqual(spy_signal.count(), 1)

        # model dict updated
        self.assertTrue(self.widget.model['description'] == new_text)

    def testOnParamsChanged(self):
        """See what happens when parameters change"""
        spy_signal = QtSignalSpy(self.widget, self.widget.modelModified)

        # number of rows. default=1
        self.assertEqual(self.widget.tblParams.rowCount(), 1)

        # number of columns. default=2
        self.assertEqual(self.widget.tblParams.columnCount(), 2)

        # Change the param
        new_param = "shoot"
        self.widget.tblParams.setItem(0,0,QTableWidgetItem(new_param))
        #self.widget.tblParams.editingFinished.emit()


        # Check the signal
        self.assertEqual(spy_signal.count(), 1)

        # model dict updated
        self.assertEqual(self.widget.model['parameters'], {0: (new_param, None)})

        # Change the value
        new_value = "BOOM"
        self.widget.tblParams.setItem(0,1,QTableWidgetItem(new_value))

        # Check the signal
        self.assertEqual(spy_signal.count(), 2)

        # model dict updated
        self.assertEqual(self.widget.model['parameters'], {0: (new_param, new_value)})

        # See that the number of rows increased
        self.assertEqual(self.widget.tblParams.rowCount(), 2)

    def testOnPDParamsChanged(self):
        """See what happens when pd parameters change"""
        spy_signal = QtSignalSpy(self.widget, self.widget.modelModified)

        # number of rows. default=1
        self.assertEqual(self.widget.tblParamsPD.rowCount(), 1)

        # number of columns. default=2
        self.assertEqual(self.widget.tblParamsPD.columnCount(), 2)

        # Change the param
        new_param = "shoot"
        self.widget.tblParamsPD.setItem(0,0,QTableWidgetItem(new_param))

        # Check the signal
        self.assertEqual(spy_signal.count(), 1)

        # model dict updated
        self.assertEqual(self.widget.model['pd_parameters'], {0: (new_param, None)})

        # Change the value
        new_value = "BOOM"
        self.widget.tblParamsPD.setItem(0,1,QTableWidgetItem(new_value))

        # Check the signal
        self.assertEqual(spy_signal.count(), 2)

        # model dict updated
        self.assertTrue(self.widget.model['pd_parameters'] == {0: (new_param, new_value)})

        # See that the number of rows increased
        self.assertEqual(self.widget.tblParamsPD.rowCount(), 2)

    def testOnFunctionChanged(self):
        """See what happens when the model text changes"""
        spy_signal = QtSignalSpy(self.widget, self.widget.modelModified)

        # Change the text
        new_model = "1\n2\n"
        self.widget.txtFunction.setPlainText(new_model)

        # Check the signal
        self.assertEqual(spy_signal.count(), 1)

        # model dict updated
        self.assertEqual(self.widget.model['text'], new_model.rstrip())

