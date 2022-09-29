import os
import sys
import unittest
import logging

import pytest

from unittest.mock import MagicMock

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# set up import paths
import sas.qtgui.path_prepare

from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

# Local
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Utilities.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.ModelEditor import ModelEditor


if not QApplication.instance():
    app = QApplication(sys.argv)

class TabbedModelEditorTest(unittest.TestCase):
    def setUp(self):
        """
        Prepare the editors
        """
        class dummy_manager(object):
            _parent = QWidget()
            communicate = GuiUtils.Communicate()

        self.widget = TabbedModelEditor(parent=dummy_manager)
        self.widget_edit = TabbedModelEditor(parent=dummy_manager, edit_only=True)

    def tearDown(self):
        """Destroy the DataOperationUtility"""
        QMessageBox.exec = MagicMock(return_value=QMessageBox.Discard)
        self.widget.close()
        self.widget = None
        self.widget_edit.close()
        self.widget_edit = None

    def testDefaults(self):
        """Test the GUI in its default state"""
        assert self.widget.filename == ""
        assert self.widget.window_title == "Model Editor"
        assert not self.widget.is_modified
        assert not self.widget.edit_only
        assert self.widget_edit.edit_only

        # Add model
        #self.assertFalse(self.widget.cmdLoad.isVisible())
        #self.assertTrue(self.widget_edit.cmdLoad.isVisible())
        assert isinstance(self.widget.plugin_widget, PluginDefinition)
        assert isinstance(self.widget.editor_widget, ModelEditor)
        # tabs
        assert self.widget.tabWidget.count() == 2
        assert not self.widget.editor_widget.isEnabled()
        assert self.widget_edit.tabWidget.count() == 1
        assert not self.widget_edit.editor_widget.isEnabled()

        #buttons
        assert not self.widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled()
        assert self.widget.buttonBox.button(QDialogButtonBox.Apply).text() == "Apply"
        assert self.widget_edit.buttonBox.button(QDialogButtonBox.Apply).text() == "Save"

    def testSetPluginActive(self):
        """ Enables the plugin editor """
        # by default it is on
        assert self.widget.plugin_widget.isEnabled()
        # Let's disable it
        self.widget.setPluginActive(False)
        assert not self.widget.plugin_widget.isEnabled()
        # and back to enabled
        self.widget.setPluginActive(True)
        assert self.widget.plugin_widget.isEnabled()

    def notestCloseEvent(self):
        """Test the close event wrt. saving info"""
        event = QObject()
        event.accept = MagicMock()

        # 1. no changes to document - straightforward exit
        self.widget.is_modified = False
        self.widget.closeEvent(event)
        assert event.accept.called_once()

        # 2. document changed, cancelled
        self.widget.is_modified = True
        QMessageBox.exec = MagicMock(return_value=QMessageBox.Cancel)
        self.widget.closeEvent(event)
        assert QMessageBox.exec.called_once()
        # no additional calls to event accept
        assert event.accept.called_once()

        # 3. document changed, save
        QMessageBox.exec = MagicMock(return_value=QMessageBox.Save)
        self.widget.filename = "random string #8"
        self.widget.updateFromEditor = MagicMock()
        self.widget.closeEvent(event)
        assert QMessageBox.exec.called_once()
        # no additional calls to event accept
        assert event.accept.called_once()
        assert self.widget.updateFromEditor.called_once()

    def testOnApply(self):
        """Test the Apply/Save event"""
        # name the plugin
        self.widget.plugin_widget.txtName.setText("Uncharacteristically eloquent filename")
        self.widget.plugin_widget.txtName.editingFinished.emit()

        # make sure the flag is set correctly
        assert self.widget.is_modified

        # default tab
        self.widget.updateFromPlugin = MagicMock()
        self.widget.onApply()
        assert self.widget.updateFromPlugin.called_once()

        # switch tabs
        self.widget.tabWidget.setCurrentIndex(1)
        self.widget.updateFromEditor = MagicMock()
        self.widget.onApply()
        assert self.widget.updateFromEditor.called_once()

    def testEditorModelModified(self):
         """Test reaction to direct edit in the editor """
         # Switch to the Editor tab
         self.widget.tabWidget.setCurrentIndex(1)
         assert not self.widget.is_modified

         # add some text. This invokes tested method
         self.widget.editor_widget.txtEditor.setPlainText("Plain Text")

         # assure relevant functionality is invoked
         assert self.widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled()
         assert self.widget.is_modified
         assert "*" in self.widget.windowTitle()


    def testpluginTitleSet(self):
        """Test reaction to direct edit in plugin wizard"""
        assert not self.widget.is_modified

        # Call the tested method with no filename defined
        self.widget.pluginTitleSet()

        # Assure the apply button is disabled
        assert not self.widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled()

        # Modify plugin name
        new_name = "NAME"
        self.widget.plugin_widget.txtName.setText(new_name)
        self.widget.plugin_widget.txtName.editingFinished.emit()

        # Assure relevant functionality is invoked
        assert "*" in self.widget.windowTitle()
        assert new_name in self.widget.windowTitle()
        assert self.widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled()
        assert self.widget.is_modified

    def testSetTabEdited(self):
        """
        Test the simple string update method
        """
        title = "title"
        title_star = "title*"
        self.widget.setWindowTitle(title)

        # 1. -> edited
        self.widget.setTabEdited(True)
        assert "*" in self.widget.windowTitle()
        # make sure we don't get another star
        self.widget.setWindowTitle(title_star)
        self.widget.setTabEdited(True)
        assert title_star == self.widget.windowTitle()

        # 2. -> not edited
        self.widget.setWindowTitle(title_star)
        self.widget.setTabEdited(False)
        assert title == self.widget.windowTitle()
        # No changes when no star in title
        self.widget.setWindowTitle(title)
        self.widget.setTabEdited(False)
        assert title == self.widget.windowTitle()

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testUpdateFromEditor(self):
        """
        Test the behaviour on editor window being updated
        """
        # Assure the test rises when no filename present
        self.widget.filename = ""
        with pytest.raises(Exception):
            self.widget.updateFromEditor()

        # change the filename
        self.widget.filename="testfile.py"
        self.widget.writeFile = MagicMock()
        boring_text = "so bored with unit tests"
        self.widget.editor_widget.txtEditor.toPlainText = MagicMock(return_value=boring_text)
        self.widget.writeFile = MagicMock()
        self.widget.plugin_widget.is_python = MagicMock()
        #invoke the method
        self.widget.updateFromEditor()

        # Test the behaviour
        assert self.widget.writeFile.called_once()
        assert self.widget.writeFile.called_with('testfile.py', boring_text)

    def testCanWriteModel(self):
        """
        Test if the model can be written to a file, given initial conditions
        """
        test_model = {'overwrite':False,
                      'text':"return"}
        test_path = "test.py"

        with pytest.raises(Exception):
            self.widget.canWriteModel()

        with pytest.raises(Exception):
            self.widget.canWriteModel(model=test_model)

        with pytest.raises(Exception):
            self.widget.canWriteModel(full_path=test_path)

        # 1. Overwrite box unchecked, file exists
        os.path.isfile = MagicMock(return_value=True)
        QMessageBox.critical = MagicMock()

        ret = self.widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Plugin with specified name already exists' in QMessageBox.critical.call_args[0][2]

        # 2. Overwrite box checked, file exists, empty model
        os.path.isfile = MagicMock(return_value=True)
        test_model['overwrite']=True
        test_model['text'] = ""
        QMessageBox.critical = MagicMock()

        ret = self.widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Error: Function is not defined' in QMessageBox.critical.call_args[0][2]

        # 3. Overwrite box unchecked, file doesn't exists, model with no 'return'
        os.path.isfile = MagicMock(return_value=False)
        test_model['overwrite']=False
        test_model['text'] = "I am a simple model"
        QMessageBox.critical = MagicMock()

        ret = self.widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Error: The func(x) must' in QMessageBox.critical.call_args[0][2]

        # 4. Overwrite box unchecked, file doesnt exist, good model
        os.path.isfile = MagicMock(return_value=False)
        test_model['text'] = "return"
        ret = self.widget.canWriteModel(model=test_model, full_path=test_path)
        assert ret

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
        assert "" in test_str

