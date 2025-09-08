import os

import pytest
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QDialogButtonBox, QMessageBox, QWidget

# Local
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.ModelEditor import ModelEditor
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.TabbedModelEditor import TabbedModelEditor


class TabbedModelEditorTest:
    @pytest.fixture(autouse=True)
    def widget(self, qapp, mocker):
        '''Create/Destroy the editor'''
        class dummy_manager:
            _parent = QWidget()
            communicate = GuiUtils.Communicate()

        w = TabbedModelEditor(parent=dummy_manager)

        yield w

        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Discard)
        w.close()

    @pytest.fixture(autouse=True)
    def widget_edit(self, qapp, mocker):
        '''Create/Destroy the editor'''
        class dummy_manager:
            _parent = QWidget()
            communicate = GuiUtils.Communicate()

        w = TabbedModelEditor(parent=dummy_manager, edit_only=True)

        yield w

        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Discard)
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
        #assert widget.cmdLoad.isVisible()
        #assert widget_edit.cmdLoad.isVisible()
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

    def notestCloseEvent(self, widget, mocker):
        """Test the close event wrt. saving info"""
        event = QObject()
        mocker.patch.object(event, 'accept')

        # 1. no changes to document - straightforward exit
        widget.is_modified = False
        widget.closeEvent(event)
        assert event.accept.called_once()

        # 2. document changed, cancelled
        widget.is_modified = True
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Cancel)
        widget.closeEvent(event)
        assert QMessageBox.exec.called_once()
        # no additional calls to event accept
        assert event.accept.called_once()

        # 3. document changed, save
        mocker.patch.object(QMessageBox, 'exec', return_value=QMessageBox.Save)
        widget.filename = "random string #8"
        mocker.patch.object(widget, 'updateFromEditor')
        widget.closeEvent(event)
        assert QMessageBox.exec.called_once()
        # no additional calls to event accept
        assert event.accept.called_once()
        assert widget.updateFromEditor.called_once()

    def testOnApply(self, widget, mocker):
        """Test the Apply/Save event"""
        # name the plugin
        widget.plugin_widget.txtName.setText("Uncharacteristically eloquent filename")
        widget.plugin_widget.txtName.editingFinished.emit()

        # make sure the flag is set correctly
        assert widget.is_modified

        # default tab
        mocker.patch.object(widget, 'updateFromPlugin')
        widget.onApply()
        assert widget.updateFromPlugin.called_once()

        # switch tabs
        widget.tabWidget.setCurrentIndex(1)
        mocker.patch.object(widget, 'updateFromEditor')
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
    def testUpdateFromEditor(self, widget, mocker):
        """
        Test the behaviour on editor window being updated
        """
        # Assure the test rises when no filename present
        widget.filename = ""
        with pytest.raises(Exception):
            widget.updateFromEditor()

        # change the filename
        widget.filename="testfile.py"
        mocker.patch.object(widget, 'writeFile')
        boring_text = "so bored with unit tests"
        mocker.patch.object(widget.editor_widget.txtEditor, 'toPlainText', return_value=boring_text)
        mocker.patch.object(widget, 'writeFile')
        mocker.patch.object(widget.plugin_widget, 'is_python')
        #invoke the method
        widget.updateFromEditor()

        # Test the behaviour
        assert widget.writeFile.called_once()
        assert widget.writeFile.called_with('testfile.py', boring_text)

    def testCanWriteModel(self, widget, mocker):
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
        mocker.patch.object(os.path, 'isfile', return_value=True)
        mocker.patch.object(QMessageBox, 'critical')

        ret = widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Plugin with specified name already exists' in QMessageBox.critical.call_args[0][2]

        # 2. Overwrite box checked, file exists, empty model
        mocker.patch.object(os.path, 'isfile', return_value=True)
        test_model['overwrite']=True
        test_model['text'] = ""
        mocker.patch.object(QMessageBox, 'critical')

        ret = widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Error: Function is not defined' in QMessageBox.critical.call_args[0][2]

        # 3. Overwrite box unchecked, file doesn't exists, model with no 'return'
        mocker.patch.object(os.path, 'isfile', return_value=False)
        test_model['overwrite']=False
        test_model['text'] = "I am a simple model"
        mocker.patch.object(QMessageBox, 'critical')

        ret = widget.canWriteModel(model=test_model, full_path=test_path)
        assert not ret
        assert QMessageBox.critical.called_once()
        assert 'Plugin Error' in QMessageBox.critical.call_args[0][1]
        assert 'Error: The func(x) must' in QMessageBox.critical.call_args[0][2]

        # 4. Overwrite box unchecked, file doesnt exist, good model
        mocker.patch.object(os.path, 'isfile', return_value=False)
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
