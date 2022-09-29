import os
import sys
import logging

import pytest

from unittest.mock import MagicMock

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

from sas.qtgui.UnitTesting.TestUtils import QtSignalSpy

# Local
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Utilities.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.ModelEditor import ModelEditor



class TabbedModelEditorTest:
    @pytest.fixture(autouse=True)
    def widget(self, qapp):
        '''Create/Destroy the editor'''
        class dummy_manager:
            _parent = QWidget()
            communicate = GuiUtils.Communicate()

        w = TabbedModelEditor(parent=dummy_manager)

        yield w

        QMessageBox.exec = MagicMock(return_value=QMessageBox.Discard)
        w.close()

    @pytest.fixture(autouse=True)
    def widget_edit(self, qapp):
        '''Create/Destroy the editor'''
        class dummy_manager:
            _parent = QWidget()
            communicate = GuiUtils.Communicate()

        w = TabbedModelEditor(parent=dummy_manager, edit_only=True)

        yield w

        QMessageBox.exec = MagicMock(return_value=QMessageBox.Discard)
        w.close()
        widget_edit = TabbedModelEditor(parent=dummy_manager, edit_only=True)

    def testDefaults(self, widget, widget_edit):
        """Test the GUI in its default state"""
        assert widget.filename == ""
        assert widget.window_title == "Model Editor"
        assert not widget.is_modified
        assert not widget.edit_only
        assert widget_edit.edit_only

        # Add model
        #self.assertFalse(widget.cmdLoad.isVisible())
        #self.assertTrue(widget_edit.cmdLoad.isVisible())
        assert isinstance(widget.plugin_widget, PluginDefinition)
        assert isinstance(widget.editor_widget, ModelEditor)
        # tabs
        assert widget.tabWidget.count() == 2
        assert not widget.editor_widget.isEnabled()
        assert widget_edit.tabWidget.count() == 1
        assert not widget_edit.editor_widget.isEnabled()

        #buttons
        assert not widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled()
        assert widget.buttonBox.button(QDialogButtonBox.Apply).text() == "Apply"
        assert widget_edit.buttonBox.button(QDialogButtonBox.Apply).text() == "Save"

    def testSetPluginActive(self, widget):
        """ Enables the plugin editor """
        # by default it is on
        assert widget.plugin_widget.isEnabled()
        # Let's disable it
        widget.setPluginActive(False)
        assert not widget.plugin_widget.isEnabled()
        # and back to enabled
        widget.setPluginActive(True)
        assert widget.plugin_widget.isEnabled()

    def notestCloseEvent(self, widget):
        """Test the close event wrt. saving info"""
        event = QObject()
        event.accept = MagicMock()

        # 1. no changes to document - straightforward exit
        widget.is_modified = False
        widget.closeEvent(event)
        assert event.accept.called_once()

        # 2. document changed, cancelled
        widget.is_modified = True
        QMessageBox.exec = MagicMock(return_value=QMessageBox.Cancel)
        widget.closeEvent(event)
        assert QMessageBox.exec.called_once()
        # no additional calls to event accept
        assert event.accept.called_once()

        # 3. document changed, save
        QMessageBox.exec = MagicMock(return_value=QMessageBox.Save)
        widget.filename = "random string #8"
        widget.updateFromEditor = MagicMock()
        widget.closeEvent(event)
        assert QMessageBox.exec.called_once()
        # no additional calls to event accept
        assert event.accept.called_once()
        assert widget.updateFromEditor.called_once()

    def testOnApply(self, widget):
        """Test the Apply/Save event"""
        # name the plugin
        widget.plugin_widget.txtName.setText("Uncharacteristically eloquent filename")
        widget.plugin_widget.txtName.editingFinished.emit()

        # make sure the flag is set correctly
        assert widget.is_modified

        # default tab
        widget.updateFromPlugin = MagicMock()
        widget.onApply()
        assert widget.updateFromPlugin.called_once()

        # switch tabs
        widget.tabWidget.setCurrentIndex(1)
        widget.updateFromEditor = MagicMock()
        widget.onApply()
        assert widget.updateFromEditor.called_once()

    def testEditorModelModified(self, widget):
         """Test reaction to direct edit in the editor """
         # Switch to the Editor tab
         widget.tabWidget.setCurrentIndex(1)
         assert not widget.is_modified

         # add some text. This invokes tested method
         widget.editor_widget.txtEditor.setPlainText("Plain Text")

         # assure relevant functionality is invoked
         assert widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled()
         assert widget.is_modified
         assert "*" in widget.windowTitle()


    def testpluginTitleSet(self, widget):
        """Test reaction to direct edit in plugin wizard"""
        assert not widget.is_modified

        # Call the tested method with no filename defined
        widget.pluginTitleSet()

        # Assure the apply button is disabled
        assert not widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled()

        # Modify plugin name
        new_name = "NAME"
        widget.plugin_widget.txtName.setText(new_name)
        widget.plugin_widget.txtName.editingFinished.emit()

        # Assure relevant functionality is invoked
        assert "*" in widget.windowTitle()
        assert new_name in widget.windowTitle()
        assert widget.buttonBox.button(QDialogButtonBox.Apply).isEnabled()
        assert widget.is_modified

    def testSetTabEdited(self, widget):
        """
        Test the simple string update method
        """
        title = "title"
        title_star = "title*"
        widget.setWindowTitle(title)

        # 1. -> edited
        widget.setTabEdited(True)
        assert "*" in widget.windowTitle()
        # make sure we don't get another star
        widget.setWindowTitle(title_star)
        widget.setTabEdited(True)
        assert title_star == widget.windowTitle()

        # 2. -> not edited
        widget.setWindowTitle(title_star)
        widget.setTabEdited(False)
        assert title == widget.windowTitle()
        # No changes when no star in title
        widget.setWindowTitle(title)
        widget.setTabEdited(False)
        assert title == widget.windowTitle()

    @pytest.mark.xfail(reason="2022-09 already broken")
    def testUpdateFromEditor(self, widget):
        """
        Test the behaviour on editor window being updated
        """
        # Assure the test rises when no filename present
        widget.filename = ""
        with pytest.raises(Exception):
            widget.updateFromEditor()

        # change the filename
        widget.filename="testfile.py"
        widget.writeFile = MagicMock()
        boring_text = "so bored with unit tests"
        widget.editor_widget.txtEditor.toPlainText = MagicMock(return_value=boring_text)
        widget.writeFile = MagicMock()
        widget.plugin_widget.is_python = MagicMock()
        #invoke the method
        widget.updateFromEditor()

        # Test the behaviour
        assert widget.writeFile.called_once()
        assert widget.writeFile.called_with('testfile.py', boring_text)

    def testCanWriteModel(self, widget):
        """
        Test if the model can be written to a file, given initial conditions
        """
        test_model = {'overwrite':False,
                      'text':"return"}
        test_path = "test.py"

        with pytest.raises(Exception):
            widget.canWriteModel()

        with pytest.raises(Exception):
            widget.canWriteModel(model=test_model)

        with pytest.raises(Exception):
            widget.canWriteModel(full_path=test_path)

        # 1. Overwrite box unchecked, file exists
        os.path.isfile = MagicMock(return_value=True)
        QMessageBox.critical = MagicMock()

        ret = widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Plugin with specified name already exists' in QMessageBox.critical.call_args[0][2]

        # 2. Overwrite box checked, file exists, empty model
        os.path.isfile = MagicMock(return_value=True)
        test_model['overwrite']=True
        test_model['text'] = ""
        QMessageBox.critical = MagicMock()

        ret = widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Error: Function is not defined' in QMessageBox.critical.call_args[0][2]

        # 3. Overwrite box unchecked, file doesn't exists, model with no 'return'
        os.path.isfile = MagicMock(return_value=False)
        test_model['overwrite']=False
        test_model['text'] = "I am a simple model"
        QMessageBox.critical = MagicMock()

        ret = widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Error: The func(x) must' in QMessageBox.critical.call_args[0][2]

        # 4. Overwrite box unchecked, file doesnt exist, good model
        os.path.isfile = MagicMock(return_value=False)
        test_model['text'] = "return"
        ret = widget.canWriteModel(model=test_model, full_path=test_path)
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

    def testStrFromParamDict(self, widget):
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

        test_str = widget.strFromParamDict(test_dict)
        assert "" in test_str
