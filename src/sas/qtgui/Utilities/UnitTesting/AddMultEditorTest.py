import sys
import os
import unittest
import webbrowser
import tempfile
from unittest.mock import MagicMock, patch

from PyQt5 import QtGui
from PyQt5 import QtWidgets

# set up import paths
import path_prepare

from sas.qtgui.Utilities.GuiUtils import Communicate

# Local
from sas.qtgui.Utilities.AddMultEditor import AddMultEditor

if not QtWidgets.QApplication.instance():
    app = QtWidgets.QApplication(sys.argv)

class dummy_manager(object):
    HELP_DIRECTORY_LOCATION = "html"
    communicate = Communicate()
    _parent = QtWidgets.QDialog()

class AddMultEditorTest(unittest.TestCase):
    """ Test the simple AddMultEditor dialog """
    @patch.object(AddMultEditor, 'readModels')
    def setUp(self, mock_list_models):
        """ Create AddMultEditor dialog """

        # mock models from plugin folder
        mock_list_models.return_value = ['cylinder', 'rpa',
                                         'core_shell_cylinder', 'sphere']

        self.widget = AddMultEditor(dummy_manager())

    def tearDown(self):
        """ Destroy the GUI """

        self.widget.close()
        self.widget = None

    def testDefaults(self):
        """ Test the GUI in its default state """

        self.assertIsInstance(self.widget, QtWidgets.QDialog)

        self.assertEqual(self.widget.sizePolicy().verticalPolicy(), 0)
        self.assertEqual(self.widget.sizePolicy().horizontalPolicy(), 5)

        # Default title
        self.assertEqual(self.widget.windowTitle(), "Easy Add/Multiply Editor")

        # Default types
        self.assertIsInstance(self.widget.cbOperator, QtWidgets.QComboBox)
        self.assertIsInstance(self.widget.cbModel1, QtWidgets.QComboBox)
        self.assertIsInstance(self.widget.cbModel2, QtWidgets.QComboBox)

        # Modal window
        self.assertFalse(self.widget.isModal())

        # Checkbox not tristate, not checked
        self.assertFalse(self.widget.chkOverwrite.isTristate())
        self.assertFalse(self.widget.chkOverwrite.isChecked())

        # Push buttons disabled
        self.assertFalse(self.widget.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).isEnabled())

        # Text of labels...
        self.assertEqual(self.widget.chkOverwrite.text(),
                         "Overwrite existing model")

        # Allowed operators
        self.assertListEqual([str(self.widget.cbOperator.itemText(i)) for i in
                              range(self.widget.cbOperator.count())],
                             ['+', '*'])

        # Default operator
        self.assertEqual(self.widget.cbOperator.currentText(), '+')

        # checkbox unchecked
        self.assertFalse(self.widget.chkOverwrite.isChecked())

        # Default 'good_name' flag, name for plugin file and plugin dir
        self.assertFalse(self.widget.good_name)
        self.assertIsNone(self.widget.plugin_filename)

        # default content of displayed equation (to create the new model)
        self.assertEqual(self.widget.lblEquation.text(),
                         "<html><head/><body><p>Plugin_model = "
                         "scale_factor * (model_1 + model_2) + background"
                         "</p></body></html>")

        # Tooltips
        self.assertEqual(self.widget.cbOperator.toolTip(),
                         "Add: +\nMultiply: *")
        self.assertEqual(self.widget.txtName.toolTip(),
                         "Sum / Multiply model function name.")
        self.widget.chkOverwrite.setChecked(True)

        self.assertNotEqual(len(self.widget.chkOverwrite.toolTip()), 0)

    def testOnModelComboboxes(self):
        """ Test on Model1 and Model2 comboboxes """

        # content of model_1 and model_2 comboboxes
        # same content for the two comboboxes
        self.assertEqual(self.widget.cbModel1.count(),
                         self.widget.cbModel2.count())

        self.assertEqual(self.widget.cbModel1.count(), 4)

        # default of cbModel1 and cbModel2
        self.assertEqual(self.widget.cbModel1.currentText(), 'sphere')
        self.assertEqual(self.widget.cbModel2.currentText(), 'cylinder')

    def testValidateName(self):
        """ Test validity of output name (syntax only) """

        # Invalid plugin name
        self.widget.txtName.setText('+++')

        state = self.widget.txtName.validator().validate(self.widget.txtName.text(), 0)[0]
        self.assertEqual(state, QtGui.QValidator.Invalid)

        # Valid new plugin name
        self.widget.txtName.setText('cylinder_test_case')
        state = \
        self.widget.txtName.validator().validate(self.widget.txtName.text(),
                                                 0)[0]
        self.assertEqual(state, QtGui.QValidator.Acceptable)

    def testOnApply(self):
        """ Test onApply """

        self.widget.txtName.setText("new_model")
        self.widget.updateModels = MagicMock()

        # make sure the flag is set correctly
        self.widget.is_modified = True

        # Mock self.write_new_model_to_file
        self.widget.plugin_dir = tempfile.gettempdir()
        self.widget.plugin_filename = \
            os.path.join(self.widget.plugin_dir, 'new_model.py')

        self.widget.write_new_mode_to_file = MagicMock()

        # invoke the tested method
        self.widget.onApply()

        self.assertTrue(self.widget.write_new_mode_to_file.called_once_with(
        os.path.join(self.widget.plugin_dir, 'new_model.py'),
        self.widget.cbModel1.currentText(),
        self.widget.cbModel2.currentText(),
        self.widget.cbOperator.currentText()))

        self.assertTrue(self.widget.updateModels.called_once())

    def testWriteNewModelToFile(self):
        """ Test content of generated plugin"""

        dummy_file_path = os.path.join(tempfile.gettempdir(),
                                       "test_datafile.py")

        # prepare data to create file and check its content: names of 2 models,
        # operator and description (default or not)
        model1_name = self.widget.cbModel1.currentText()
        model2_name = self.widget.cbModel2.currentText()
        symbol_operator = self.widget.cbOperator.currentText()

        # default description
        desc_line = "{} {} {}".format(model1_name,
                                      symbol_operator,
                                      model2_name)

        self.widget.write_new_model_to_file(dummy_file_path, model1_name,
                                            model2_name, symbol_operator)
        # check content of dummy file path
        with open(dummy_file_path, 'r') as f_in:
            lines_from_generated_file = [line.strip() for line in f_in]

        # SUM_TEMPLATE with updated entries
        completed_template = ["from sasmodels.core import load_model_info",
                        "from sasmodels.sasview_model import make_model_from_info",
                        "model_info = load_model_info('{model1}{operator}{model2}')".
                            format(model1=model1_name,
                                   operator=symbol_operator,
                                   model2=model2_name),
                        "model_info.name = '{}'".format("test_datafile"),
                        "model_info.description = '{}'".format(desc_line),
                        "Model = make_model_from_info(model_info)"]

        for item in completed_template:
            self.assertIn(item, lines_from_generated_file)

        # check content with description entered by user
        self.widget.txtDescription.setText('New description for test  ')

        new_desc_line = "model_info.description = '{}'".format('New description for test')

        # re-run function to test
        self.widget.write_new_model_to_file(dummy_file_path, model1_name,
                                            model2_name, symbol_operator)

        # check content of dummy file path
        with open(dummy_file_path, 'r') as f_in:
            lines_from_generated_file = [line.strip() for line in f_in]

        # update completed template
        completed_template[4] = new_desc_line

        # check content of generated file
        for item in completed_template:
            self.assertIn(item, lines_from_generated_file)

    def testOnOperatorChange(self):
        """
        Test modification of displayed equation
        when selected operator is changed
        """

        # check default
        self.assertIn(self.widget.cbOperator.currentText(),
                      self.widget.lblEquation.text())

        # change operator
        if self.widget.cbOperator.currentIndex() == 0:
            self.widget.cbOperator.setCurrentIndex(1)
        else:
            self.widget.cbOperator.setCurrentIndex(0)

        self.assertIn(self.widget.cbOperator.currentText(),
                      self.widget.lblEquation.text())

    def testOnHelp(self):
        """ Test the default help renderer """

        webbrowser.open = MagicMock()

        # invoke the tested method
        self.widget.onHelp()

        # see that webbrowser open was attempted
        webbrowser.open.assert_called()

    def testOnNameCheck(self):
        """ Test onNameCheck """

        # Enter plugin name already present in list of existing models
        self.widget.txtName.setText("cylinder")

        # Scenario 1
        # overwrite not checked -> message box should appear
        # and good_name set to False, 'Apply' button disabled

        # mock QMessageBox
        QtWidgets.QMessageBox.critical = MagicMock()

        self.widget.chkOverwrite.setChecked(False)
        self.widget.txtName.editingFinished.emit()
        self.assertFalse(self.widget.good_name)
        self.assertFalse(self.widget.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).isEnabled())

        self.assertTrue(QtWidgets.QMessageBox.critical.called_once())

        msg = "Plugin with specified name already exists.\n"
        msg += "Please specify different filename or allow file overwrite."

        self.assertIn('Plugin Error', QtWidgets.QMessageBox.critical.call_args[0][1])
        self.assertIn(msg, QtWidgets.QMessageBox.critical.call_args[0][2])

        # Scenario 2
        # overwrite checked -> no message box displayed
        # and good_name set to True, Apply button enabled, output name created

        # mock QMessageBox
        QtWidgets.QMessageBox.critical = MagicMock()
        # create dummy plugin_dir for output file
        self.widget.plugin_dir = tempfile.gettempdir()

        self.widget.chkOverwrite.setChecked(True)
        self.widget.txtName.editingFinished.emit()
        self.assertTrue(self.widget.good_name)
        self.assertTrue(self.widget.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).isEnabled())

        self.assertFalse(QtWidgets.QMessageBox.critical.called)

        self.assertIn('cylinder.py', self.widget.plugin_filename)

        # Scenario 3 Enter valid new plugin name -> filename created and Apply
        # button enabled
        # forbidding overwriting should not change anything
        # since it's a new name
        self.widget.txtName.setText("   cylinder0   ")
        self.widget.chkOverwrite.setChecked(False)
        self.widget.txtName.editingFinished.emit()
        self.assertIn("cylinder0.py", self.widget.plugin_filename)
        self.assertTrue(self.widget.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).isEnabled())

    @patch.object(AddMultEditor, 'readModels')
    def testOnUpdateModels(self, mock_new_list_models):
        """ Test onUpdateModels """

        ini_count_models = self.widget.cbModel1.count()

        mock_new_list_models.return_value = ['cylinder', 'rpa',
                                             'core_shell_cylinder', 'sphere',
                                             'cylinder0']

        self.widget.updateModels()
        # check that the number of models in the comboboxes
        # has been incremented by 1
        self.assertEqual(self.widget.cbModel1.count(), ini_count_models + 1)
        self.assertEqual(self.widget.cbModel2.count(), ini_count_models + 1)

        # check that the new model is in the list
        combobox = self.widget.cbModel1
        self.assertIn('cylinder0', [combobox.itemText(indx)
                                    for indx in range(combobox.count())])

    def testOnReadModels(self):
        """ The output of ReadModels is the return value of MagicMock defined
        in the SetUp of these tests. """

        self.assertEqual(self.widget.list_models, ['cylinder', 'rpa',
                                                   'core_shell_cylinder',
                                                   'sphere'])

    def testCheckModel(self):
        """ Test CheckModel"""

        # TODO first: solve problem with empty 'test'
        pass
