import os
import sys
import unittest
import logging

from unittest.mock import MagicMock

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# set up import paths
import sas.qtgui.path_prepare

from UnitTesting.TestUtils import QtSignalSpy

# Local
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Utilities.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.ModelEditor import ModelEditor


#if not QApplication.instance():
#    app = QApplication(sys.argv)
app = QApplication(sys.argv)

class TabbedModelEditorTest(unittest.TestCase):
    def setUp(self):
        """
        Prepare the editors
        """
        self.widget = TabbedModelEditor(None)
        self.widget_edit = TabbedModelEditor(None, edit_only=True)

    def tearDown(self):
        """Destroy the DataOperationUtility"""
        QMessageBox.exec = MagicMock(return_value=QMessageBox.Discard)
        self.widget.close()
        self.widget = None
        self.widget_edit.close()
        self.widget_edit = None

    def testDefaults(self):
        """Test the GUI in its default state"""
        self.assertEqual(self.widget.filename, "")
        self.assertEqual(self.widget.window_title, "Model Editor")
        self.assertFalse(self.widget.is_modified)
        self.assertFalse(self.widget.edit_only)
        self.assertTrue(self.widget_edit.edit_only)

        # Add model
        #self.assertFalse(self.widget.cmdLoad.isVisible())
        #self.assertTrue(self.widget_edit.cmdLoad.isVisible())
        self.assertIsInstance(self.widget.plugin_widget, PluginDefinition)
        self.assertIsInstance(self.widget.editor_widget, ModelEditor)
        # tabs
        self.assertEqual(self.widget.tabWidget.count(), 2)
        self.assertFalse(self.widget.editor_widget.isEnabled())
        self.assertEqual(self.widget_edit.tabWidget.count(), 1)
        self.assertFalse(self.widget_edit.editor_widget.isEnabled())

        #buttons
        self.assertFalse(self.widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled())
        self.assertEqual(self.widget.buttonBox.button(QDialogButtonBox.Apply).text(), "Apply")
        self.assertEqual(self.widget_edit.buttonBox.button(QDialogButtonBox.Apply).text(), "Save")

    def testSetPluginActive(self):
        """ Enables the plugin editor """
        # by default it is on
        self.assertTrue(self.widget.plugin_widget.isEnabled())
        # Let's disable it
        self.widget.setPluginActive(False)
        self.assertFalse(self.widget.plugin_widget.isEnabled())
        # and back to enabled
        self.widget.setPluginActive(True)
        self.assertTrue(self.widget.plugin_widget.isEnabled())

    def notestCloseEvent(self):
        """Test the close event wrt. saving info"""
        event = QObject()
        event.accept = MagicMock()

        # 1. no changes to document - straightforward exit
        self.widget.is_modified = False
        self.widget.closeEvent(event)
        self.assertTrue(event.accept.called_once())

        # 2. document changed, cancelled
        self.widget.is_modified = True
        QMessageBox.exec = MagicMock(return_value=QMessageBox.Cancel)
        self.widget.closeEvent(event)
        self.assertTrue(QMessageBox.exec.called_once())
        # no additional calls to event accept
        self.assertTrue(event.accept.called_once())

        # 3. document changed, save
        QMessageBox.exec = MagicMock(return_value=QMessageBox.Save)
        self.widget.filename = "random string #8"
        self.widget.updateFromEditor = MagicMock()
        self.widget.closeEvent(event)
        self.assertTrue(QMessageBox.exec.called_once())
        # no additional calls to event accept
        self.assertTrue(event.accept.called_once())
        self.assertTrue(self.widget.updateFromEditor.called_once())

    def testOnApply(self):
        """Test the Apply/Save event"""
        # name the plugin
        self.widget.plugin_widget.txtName.setText("Uncharacteristically eloquent filename")
        self.widget.plugin_widget.txtName.editingFinished.emit()

        # make sure the flag is set correctly
        self.assertTrue(self.widget.is_modified)

        # default tab
        self.widget.updateFromPlugin = MagicMock()
        self.widget.onApply()
        self.assertTrue(self.widget.updateFromPlugin.called_once())

        # switch tabs
        self.widget.tabWidget.setCurrentIndex(1)
        self.widget.updateFromEditor = MagicMock()
        self.widget.onApply()
        self.assertTrue(self.widget.updateFromEditor.called_once())

    def testEditorModelModified(self):
         """Test reaction to direct edit in the editor """
         # Switch to the Editor tab
         self.widget.tabWidget.setCurrentIndex(1)
         self.assertFalse(self.widget.is_modified)

         # add some text. This invokes tested method
         self.widget.editor_widget.txtEditor.setPlainText("Plain Text")

         # assure relevant functionality is invoked
         self.assertTrue(self.widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled())
         self.assertTrue(self.widget.is_modified)
         self.assertIn("*", self.widget.windowTitle())


    def testPluginModelModified(self):
        """Test reaction to direct edit in plugin wizard"""
        self.assertFalse(self.widget.is_modified)

        # Call the tested method with no filename defined
        self.widget.pluginModelModified()

        # Assure the apply button is disabled
        self.assertFalse(self.widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled())

        # Modify plugin name
        new_name = "NAME"
        self.widget.plugin_widget.txtName.setText(new_name)
        self.widget.plugin_widget.txtName.editingFinished.emit()

        # Assure relevant functionality is invoked
        self.assertIn("*", self.widget.windowTitle())
        self.assertIn(new_name, self.widget.windowTitle())
        self.assertTrue(self.widget.editor_widget.isEnabled())
        self.assertTrue(self.widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled())
        self.assertTrue(self.widget.is_modified)

    def testSetTabEdited(self):
        """
        Test the simple string update method
        """
        title = "title"
        title_star = "title*"
        self.widget.setWindowTitle(title)

        # 1. -> edited
        self.widget.setTabEdited(True)
        self.assertIn("*", self.widget.windowTitle())
        # make sure we don't get another star
        self.widget.setWindowTitle(title_star)
        self.widget.setTabEdited(True)
        self.assertEqual(title_star, self.widget.windowTitle())

        # 2. -> not edited
        self.widget.setWindowTitle(title_star)
        self.widget.setTabEdited(False)
        self.assertEqual(title, self.widget.windowTitle())
        # No changes when no star in title
        self.widget.setWindowTitle(title)
        self.widget.setTabEdited(False)
        self.assertEqual(title, self.widget.windowTitle())

    def testUpdateFromEditor(self):
        """
        Test the behaviour on editor window being updated
        """
        # Assure the test rises when no filename present
        self.widget.filename = ""
        with self.assertRaises(Exception):
            self.widget.updateFromEditor()

        # change the filename
        self.widget.filename="testfile.py"
        self.widget.writeFile = MagicMock()
        boring_text = "so bored with unit tests"
        self.widget.editor_widget.txtEditor.toPlainText = MagicMock(return_value=boring_text)
        self.widget.writeFile = MagicMock()
        #invoke the method
        self.widget.updateFromEditor()

        # Test the behaviour
        self.assertTrue(self.widget.writeFile.called_once())
        self.assertTrue(self.widget.writeFile.called_with('testfile.py', boring_text))

    def testCanWriteModel(self):
        """
        Test if the model can be written to a file, given initial conditions
        """
        test_model = {'overwrite':False,
                      'text':"return"}
        test_path = "test.py"

        with self.assertRaises(Exception):
            self.widget.canWriteModel()

        with self.assertRaises(Exception):
            self.widget.canWriteModel(model=test_model)

        with self.assertRaises(Exception):
            self.widget.canWriteModel(full_path=test_path)

        # 1. Overwrite box unchecked, file exists
        os.path.isfile = MagicMock(return_value=True)
        QMessageBox.critical = MagicMock()

        ret = self.widget.canWriteModel(model=test_model, full_path=test_path)
        self.assertFalse(ret)
        self.assertTrue(QMessageBox.critical.called_once())
        self.assertIn('Plugin Error', QMessageBox.critical.call_args[0][1])
        self.assertIn('Plugin with specified name already exists', QMessageBox.critical.call_args[0][2])

        # 2. Overwrite box checked, file exists, empty model
        os.path.isfile = MagicMock(return_value=True)
        test_model['overwrite']=True
        test_model['text'] = ""
        QMessageBox.critical = MagicMock()

        ret = self.widget.canWriteModel(model=test_model, full_path=test_path)
        self.assertFalse(ret)
        self.assertTrue(QMessageBox.critical.called_once())
        self.assertIn('Plugin Error', QMessageBox.critical.call_args[0][1])
        self.assertIn('Error: Function is not defined', QMessageBox.critical.call_args[0][2])

        # 3. Overwrite box unchecked, file doesn't exists, model with no 'return'
        os.path.isfile = MagicMock(return_value=False)
        test_model['overwrite']=False
        test_model['text'] = "I am a simple model"
        QMessageBox.critical = MagicMock()

        ret = self.widget.canWriteModel(model=test_model, full_path=test_path)
        self.assertFalse(ret)
        self.assertTrue(QMessageBox.critical.called_once())
        self.assertIn('Plugin Error', QMessageBox.critical.call_args[0][1])
        self.assertIn('Error: The func(x) must', QMessageBox.critical.call_args[0][2])

        # 4. Overwrite box unchecked, file doesnt exist, good model
        os.path.isfile = MagicMock(return_value=False)
        test_model['text'] = "return"
        ret = self.widget.canWriteModel(model=test_model, full_path=test_path)
        self.assertTrue(ret)

    def testGenerateModel(self):
        """
        Test the model text creation from the dictionary
        """
        pass

    def notestCheckModel(self):
        """test the sasmodel model checker """
        pass

    def testGetParamHelper(self):
        """
        Test the convenience method for converting 
        GUI parameter representation into sasmodel comprehensible string
        """
        pass

    def testStrFromParamDict(self):
        """
        Test Conversion from dict to param string
        """
        test_dict = {0: ('a', '1'),
                     1: ('eee',''),
                     2: ('bob', None),
                     3: ('',-1),
                     4: (None, None)}

        #{0: ('variable','value'),
        # 1: ('variable','value'),

        test_str = self.widget.strFromParamDict(test_dict)
        self.assertIn("", test_str)

