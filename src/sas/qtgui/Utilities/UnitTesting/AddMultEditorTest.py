import os
import tempfile
import webbrowser

import pytest
from PySide6 import QtGui, QtWidgets

from sas.qtgui.Utilities.GuiUtils import Communicate

# Local
from sas.qtgui.Utilities.ModelEditors.AddMultEditor.AddMultEditor import AddMultEditor


class AddMultEditorTest:
    """ Test the simple AddMultEditor dialog """

    @pytest.fixture(autouse=True)
    def widget(self, qapp, mocker):
        '''Create/Destroy the AddMultEditor'''
        class dummy_manager:
            HELP_DIRECTORY_LOCATION = "html"
            communicate = Communicate()
            _parent = QtWidgets.QDialog()

        # mock models from plugin folder
        mocker.patch.object(AddMultEditor, 'readModels',
            return_value=[
                'cylinder', 'rpa',
                'core_shell_cylinder', 'sphere'
            ])

        w = AddMultEditor(dummy_manager())
        yield w
        w.close()

    #@patch.object(AddMultEditor, 'readModels')

    def testDefaults(self, widget):
        """ Test the GUI in its default state """

        assert isinstance(widget, QtWidgets.QDialog)

        assert widget.sizePolicy().verticalPolicy() == 0
        assert widget.sizePolicy().horizontalPolicy() == 5

        # Default title
        assert widget.windowTitle() == "Easy Add/Multiply Editor"

        # Default types
        assert isinstance(widget.cbOperator, QtWidgets.QComboBox)
        assert isinstance(widget.cbModel1, QtWidgets.QComboBox)
        assert isinstance(widget.cbModel2, QtWidgets.QComboBox)

        # Modal window
        assert not widget.isModal()

        # Checkbox not tristate, not checked
        assert not widget.chkOverwrite.isTristate()
        assert not widget.chkOverwrite.isChecked()

        # Push buttons disabled
        assert not widget.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).isEnabled()

        # Text of labels...
        assert widget.chkOverwrite.text() == \
                         "Overwrite existing model"

        # Allowed operators
        assert [str(widget.cbOperator.itemText(i)) for i in
                              range(widget.cbOperator.count())] == \
                             ['+', '*', '@']

        # Default operator
        assert widget.cbOperator.currentText() == '+'

        # checkbox unchecked
        assert not widget.chkOverwrite.isChecked()

        # Default 'good_name' flag, name for plugin file and plugin dir
        assert not widget.good_name
        assert widget.plugin_filename is None

        # default content of displayed equation (to create the new model)
        #assert widget.lblEquation.text() == (
                         #"<html><head/><body><p>Plugin_model = "
                         #"scale_factor * (model_1 + model_2) + background"
                         #"</p></body></html>"
        #)

        # Tooltips
        assert widget.cbOperator.toolTip() == \
                         "Add: +\nMultiply: *"
        assert widget.txtName.toolTip() == \
                         "Sum / Multiply model function name."
        widget.chkOverwrite.setChecked(True)

        assert len(widget.chkOverwrite.toolTip()) != 0

    def testOnModelComboboxes(self, widget):
        """ Test on Model1 and Model2 comboboxes """

        # content of model_1 and model_2 comboboxes
        # same content for the two comboboxes
        assert widget.cbModel1.count() == \
                         widget.cbModel2.count()

        assert widget.cbModel1.count() == 4

        # default of cbModel1 and cbModel2
        assert widget.cbModel1.currentText() == 'sphere'
        assert widget.cbModel2.currentText() == 'cylinder'

    def testValidateName(self, widget):
        """ Test validity of output name (syntax only) """

        # Invalid plugin name
        widget.txtName.setText('+++')

        state = widget.txtName.validator().validate(widget.txtName.text(), 0)[0]
        assert state == QtGui.QValidator.Invalid

        # Valid new plugin name
        widget.txtName.setText('cylinder_test_case')
        state = \
        widget.txtName.validator().validate(widget.txtName.text(),
                                                 0)[0]
        assert state == QtGui.QValidator.Acceptable

    def testOnApply(self, widget, mocker):
        """ Test onApply """

        widget.txtName.setText("new_model")
        mocker.patch.object(widget, 'updateModels')

        # make sure the flag is set correctly
        widget.is_modified = True

        # Mock self.write_new_model_to_file
        widget.plugin_dir = tempfile.gettempdir()
        widget.plugin_filename = \
            os.path.join(widget.plugin_dir, 'new_model.py')

        mocker.patch.object(widget, 'write_new_mode_to_file', create=True)

        # invoke the tested method
        widget.onApply()

        assert widget.write_new_mode_to_file.called_once_with(
        os.path.join(widget.plugin_dir, 'new_model.py'),
        widget.cbModel1.currentText(),
        widget.cbModel2.currentText(),
        widget.cbOperator.currentText())

        assert widget.updateModels.called_once()

    def testWriteNewModelToFile(self, widget):
        """ Test content of generated plugin"""

        dummy_file_path = os.path.join(tempfile.gettempdir(),
                                       "test_datafile.py")

        # prepare data to create file and check its content: names of 2 models,
        # operator and description (default or not)
        model1_name = widget.cbModel1.currentText()
        model2_name = widget.cbModel2.currentText()
        symbol_operator = widget.cbOperator.currentText()

        # default description
        desc_line = f"{model1_name} {symbol_operator} {model2_name}"

        widget.write_new_model_to_file(dummy_file_path, model1_name,
                                            model2_name, symbol_operator)
        # check content of dummy file path
        with open(dummy_file_path) as f_in:
            lines_from_generated_file = [line.strip() for line in f_in]

        # SUM_TEMPLATE with updated entries
        completed_template = ["from sasmodels.core import load_model_info",
                        "from sasmodels.sasview_model import make_model_from_info",
                        f"model_info = load_model_info('{model1_name}{symbol_operator}{model2_name}')",
                        "model_info.name = '{}'".format("test_datafile"),
                        f"model_info.description = '{desc_line}'",
                        "Model = make_model_from_info(model_info)"]

        for item in completed_template:
            assert item in lines_from_generated_file

        # check content with description entered by user
        widget.txtDescription.setText('New description for test  ')

        new_desc_line = "model_info.description = '{}'".format('New description for test')

        # re-run function to test
        widget.write_new_model_to_file(dummy_file_path, model1_name,
                                            model2_name, symbol_operator)

        # check content of dummy file path
        with open(dummy_file_path) as f_in:
            lines_from_generated_file = [line.strip() for line in f_in]

        # update completed template
        completed_template[4] = new_desc_line

        # check content of generated file
        for item in completed_template:
            assert item in lines_from_generated_file

    def testOnOperatorChange(self, widget):
        """
        Test modification of displayed equation
        when selected operator is changed
        """

        # check default
        assert widget.cbOperator.currentText() in \
                      widget.lblEquation.text()

        # change operator
        if widget.cbOperator.currentIndex() == 0:
            widget.cbOperator.setCurrentIndex(1)
        else:
            widget.cbOperator.setCurrentIndex(0)

        assert widget.cbOperator.currentText() in \
                      widget.lblEquation.text()

    def testOnHelp(self, widget, mocker):
        """ Test the default help renderer """

        mocker.patch.object(webbrowser, 'open', create=True)

        # invoke the tested method
        widget.onHelp()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called()

    def testOnNameCheck(self, widget, mocker):
        """ Test onNameCheck """

        # Enter plugin name already present in list of existing models
        widget.txtName.setText("cylinder")

        # Scenario 1
        # overwrite not checked -> message box should appear
        # and good_name set to False, 'Apply' button disabled

        # mock QMessageBox
        mocker.patch.object(QtWidgets.QMessageBox, 'critical')

        widget.chkOverwrite.setChecked(False)
        widget.txtName.editingFinished.emit()
        assert not widget.good_name
        assert not widget.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).isEnabled()

        assert QtWidgets.QMessageBox.critical.called_once()

        msg = "Plugin with specified name already exists.\n"
        msg += "Please specify different filename or allow file overwrite."

        assert 'Plugin Error' in QtWidgets.QMessageBox.critical.call_args[0][1]
        assert msg in QtWidgets.QMessageBox.critical.call_args[0][2]

        # Scenario 2
        # overwrite checked -> no message box displayed
        # and good_name set to True, Apply button enabled, output name created

        # mock QMessageBox
        mocker.patch.object(QtWidgets.QMessageBox, 'critical')
        # create dummy plugin_dir for output file
        widget.plugin_dir = tempfile.gettempdir()

        widget.chkOverwrite.setChecked(True)
        widget.txtName.editingFinished.emit()
        assert widget.good_name
        assert widget.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).isEnabled()

        assert not QtWidgets.QMessageBox.critical.called

        assert 'cylinder.py' in widget.plugin_filename

        # Scenario 3 Enter valid new plugin name -> filename created and Apply
        # button enabled
        # forbidding overwriting should not change anything
        # since it's a new name
        widget.txtName.setText("   cylinder0   ")
        widget.chkOverwrite.setChecked(False)
        widget.txtName.editingFinished.emit()
        assert "cylinder0.py" in widget.plugin_filename
        assert widget.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).isEnabled()

    def testOnUpdateModels(self, widget, mocker):
        """ Test onUpdateModels """

        ini_count_models = widget.cbModel1.count()

        mocker.patch.object(AddMultEditor, 'readModels',
            return_value=[
                'cylinder', 'rpa',
                'core_shell_cylinder', 'sphere',
                'cylinder0',
            ])

        widget.updateModels()
        # check that the number of models in the comboboxes
        # has been incremented by 1
        assert widget.cbModel1.count() == ini_count_models + 1
        assert widget.cbModel2.count() == ini_count_models + 1

        # check that the new model is in the list
        combobox = widget.cbModel1
        assert 'cylinder0' in [combobox.itemText(indx)
                                    for indx in range(combobox.count())]

    def testOnReadModels(self, widget):
        """ The output of ReadModels is the return value of MagicMock defined
        in the SetUp of these tests. """

        assert widget.list_models == ['cylinder', 'rpa',
                                                   'core_shell_cylinder',
                                                   'sphere']

    def testCheckModel(self, widget):
        """ Test CheckModel"""

        # TODO first: solve problem with empty 'test'
        pass
