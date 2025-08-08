"""
Widget for simple add / multiply editor.
"""
# numpy methods required for the validator! Don't remove.
# pylint: disable=unused-import,unused-wildcard-import,redefined-builtin
import logging
import os
import traceback

from numpy import *
from PySide6 import QtCore, QtGui, QtWidgets

from sasmodels.sasview_model import load_standard_models

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting.FittingWidget import SUPPRESSED_MODELS

# Local UI
from sas.qtgui.Utilities.ModelEditors.AddMultEditor.UI.AddMultEditorUI import Ui_AddMultEditorUI
from sas.sascalc.fit import models

# Template for the output plugin file
SUM_TEMPLATE = """
from sasmodels.core import load_model_info
from sasmodels.sasview_model import make_model_from_info

model_info = load_model_info('{model1}{operator}{model2}')
model_info.name = '{name}'
model_info.description = '{desc_line}'
Model = make_model_from_info(model_info)
"""

# Color of backgrounds to underline valid or invalid input
BG_WHITE = "background-color: rgb(255, 255, 255);"
BG_RED = "background-color: rgb(244, 170, 164);"

# Default model names for combo boxes
CB1_DEFAULT = 'sphere'
CB2_DEFAULT = 'cylinder'


class AddMultEditor(QtWidgets.QDialog, Ui_AddMultEditorUI):
    """
       Dialog for easy custom composite models.  Provides a Dialog panel
       to choose two existing models (including pre-existing Plugin Models which
       may themselves be composite models) as well as an operation on those models
       (add or multiply) the resulting model will add a scale parameter and a
       background parameter.
       The user can also give a brief help for the model in the description box and
       must provide a unique name which is verified before the new model is saved.
    """
    def __init__(self, parent=None):
        super(AddMultEditor, self).__init__(parent._parent)

        self.parent = parent

        self.setupUi(self)

        #  uncheck self.chkOverwrite
        self.chkOverwrite.setChecked(False)
        self.canOverwriteName = False

        # Disabled Apply button until input of valid output plugin name
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)

        # Flag for correctness of resulting name
        self.good_name = False

        # Create a base list of layered models that will include plugin models
        self.layered_models = []
        # Create base model lists
        self.list_models = self.readModels()
        self.list_standard_models = self.readModels(std_only=True)
        # Fill models combo boxes
        self.setupModels()

        # Set signals after model combo boxes are populated
        self.setupSignals()

        self.setFixedSize(self.minimumSizeHint())

        # Name and directory for saving new plugin model
        self.plugin_filename = None
        self.plugin_dir = models.find_plugins_dir()

        # Validators
        rx = QtCore.QRegularExpression("^[A-Za-z0-9_]*$")
        txt_validator = QtGui.QRegularExpressionValidator(rx)
        self.txtName.setValidator(txt_validator)

    def setupModels(self):
        """ Add list of models to 'Model1' and 'Model2' comboboxes """
        # Load the model dict
        self.cbModel1.addItems(self.list_standard_models)
        self.cbModel2.addItems(self.list_standard_models)

        # set the default initial value of Model1 and Model2
        index_ini_model1 = self.cbModel1.findText(CB1_DEFAULT, QtCore.Qt.MatchFixedString)
        self.cbModel1.setCurrentIndex(index_ini_model1 if index_ini_model1 >= 0 else 0)
        index_ini_model2 = self.cbModel2.findText(CB2_DEFAULT, QtCore.Qt.MatchFixedString)
        self.cbModel2.setCurrentIndex(index_ini_model2 if index_ini_model2 >= 0 else 0)

    def readModels(self, std_only=False):
        """ Generate list of all models """
        s_models = load_standard_models()
        models_dict = {}
        for model in s_models:
            # Check if plugin model is a layered model
            self._checkIfLayered(model)
            # Do not include uncategorized models or suppressed models
            if model.category is None or (std_only and 'custom' in model.category) or model.name in SUPPRESSED_MODELS:
                continue
            models_dict[model.name] = model
        return sorted(models_dict)

    def setupSignals(self):
        """ Signals from various elements """
        # check existence of output filename when entering name
        # or when overwriting not allowed
        self.txtName.editingFinished.connect(self.onNameCheck)
        self.chkOverwrite.stateChanged.connect(self.onOverwrite)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.onApply)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Help).clicked.connect(self.onHelp)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.close)

        # Update model lists when new model selected in case one of the items selected is in self.layered_models
        self.cbModel1.currentIndexChanged.connect(self.updateModels)
        self.cbModel2.currentIndexChanged.connect(self.updateModels)

        # change displayed equation when changing operator
        self.cbOperator.currentIndexChanged.connect(self.onOperatorChange)

    def onOverwrite(self):
        """
        Modify state on checkbox change
        """
        self.canOverwriteName = self.chkOverwrite.isChecked()
        # State changed -> allow Apply
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)

    def onNameCheck(self):
        """
        Check if proposed new model name does not already exists
        (if the overwriting is not allowed).
        If not an error message not show error message is displayed
        """

        # Get the function/file name
        title = self.txtName.text().lstrip().rstrip()

        filename = title + '.py'

        if self.canOverwriteName:
            # allow overwriting -> only valid name needs to be checked
            # (done with validator in __init__ above)
            self.good_name = True
            self.txtName.setStyleSheet(BG_WHITE)
            self.plugin_filename = os.path.join(self.plugin_dir, filename)
        else:
            # No overwriting -> check existence of filename
            # Create list of existing model names for comparison
            # fake existing regular model name list
            models_list = [item + '.py' for item in self.list_models]
            if filename in models_list:
                self.good_name = False
                self.txtName.setStyleSheet(BG_RED)
                msg = "Plugin with specified name already exists.\n"
                msg += "Please specify different filename or allow file overwrite."
                logging.warning(msg)
                QtWidgets.QMessageBox.critical(self, 'Plugin Error', msg)
            else:
                s_title = title
                if len(title) > 20:
                    s_title = title[0:19] + '...'
                logging.info(f"Model function ({str(s_title)}) has been set!\n")
                self.good_name = True
                self.txtName.setStyleSheet(BG_WHITE)
                self.plugin_filename = os.path.join(self.plugin_dir, filename)

        # Enable Apply push button only if valid name
        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).setEnabled(self.good_name)

    def onOperatorChange(self, index):
        """ Respond to operator combo box changes """

        self.lblEquation.setText('<html><head/><body><p><span style=" font-weight:600;">'
                                 'Plugin_model = scale_factor * '
                                 f'(model_1 {self.cbOperator.currentText()} model_2) + background</span></p><p>'
                                 '<p>To add/multiply plugin models, or combine more than two models, '
                                 'please check Help below.<br/></p></body></html>')

    def onApply(self):
        """ Validity check, save model to file """

        # Set the button enablement, so no double clicks can be made
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)

        # Check the name/overwrite combination again, in case we managed to confuse the UI
        self.onNameCheck()
        if not self.good_name:
            return

        self.write_new_model_to_file(self.plugin_filename,
                                     self.cbModel1.currentText(),
                                     self.cbModel2.currentText(),
                                     self.cbOperator.currentText())

        try:
            success = GuiUtils.checkModel(self.plugin_filename)
        except Exception as ex:
            # broad exception from sasmodels
            msg = "Error building model: "+ str(ex)
            logging.error(msg)
            #print three last lines of the stack trace
            # this will point out the exact line failing
            last_lines = traceback.format_exc().split('\n')[-4:]
            traceback_to_show = '\n'.join(last_lines)
            logging.error(traceback_to_show)

            # Set the status bar message
            self.parent.communicate.statusBarUpdateSignal.emit("Model check failed")
            return

        if not success:
            return

        # Update list of models in FittingWidget and AddMultEditor
        self.parent.communicate.customModelDirectoryChanged.emit()
        self.updateModels()

        # Notify the user
        title = self.txtName.text().lstrip().rstrip()
        msg = "Custom model "+title + " successfully created."
        self.parent.communicate.statusBarUpdateSignal.emit(msg)
        logging.info(msg)

    def write_new_model_to_file(self, fname, model1_name, model2_name, operator):
        """ Write and Save file """

        description = self.txtDescription.text().lstrip().rstrip()
        if description.strip() != '':
            # Sasmodels generates a description for us. If the user provides
            # their own description, add a line to overwrite the sasmodels one
            desc_line = description
        else:
            desc_line = f"{model1_name} {operator} {model2_name}"

        name = os.path.splitext(os.path.basename(fname))[0]
        output = SUM_TEMPLATE.format(name=name,
                                     model1=model1_name,
                                     model2=model2_name,
                                     operator=operator,
                                     desc_line=desc_line)

        with open(fname, 'w') as out_f:
            out_f.write(output)

    def updateModels(self):
        """ Update contents of combo boxes with new plugin models """
        # Supress signals to prevent infinite loop
        self.cbModel1.blockSignals(True)
        self.cbModel2.blockSignals(True)

        # Re-read the model list so the new model is included
        self.list_models = self.readModels()
        self._updateModelLists()

        self.cbModel2.blockSignals(False)
        self.cbModel1.blockSignals(False)

    def _updateModelLists(self):
        """Update the combo boxes for both lists of models. The models in layered_models can only be included a single
        time in a plugin model. The two combo boxes could be different if a layered model is selected."""
        # Keep pointers to the current indices, so we can show the combo boxes with original selection
        model_1 = self.cbModel1.currentText()
        model_2 = self.cbModel2.currentText()
        self.cbModel1.clear()
        self.cbModel2.clear()
        # Retrieve the list of models
        no_layers_list = [model for model in self.list_models if model not in self.layered_models]
        # Make copies of the original list to allow for list-specific changes
        model_list_1 = no_layers_list if model_2 in self.layered_models else self.list_models
        model_list_2 = no_layers_list if model_1 in self.layered_models else self.list_models

        # Populate the models combo boxes
        self.cbModel1.addItems(model_list_1)
        self.cbModel2.addItems(model_list_2)

        # Reset the model position
        model1_index = self.cbModel1.findText(model_1)
        model1_default = self.cbModel1.findText(CB1_DEFAULT)
        model2_index = self.cbModel2.findText(model_2)
        model2_default = self.cbModel2.findText(CB2_DEFAULT)
        index1 = model1_index if model1_index >= 0 else model1_default if model1_default >= 0 else 0
        index2 = model2_index if model2_index >= 0 else model2_default if model2_default >= 0 else 0

        self.cbModel1.setCurrentIndex(index1)
        self.cbModel2.setCurrentIndex(index2)

    def _checkIfLayered(self, model):
        """Check models for layered or conditional parameters. Add them to self.layered_models if criteria is met."""
        if model.is_multiplicity_model:
            self.layered_models.append(model.name)

    def onHelp(self):
        """ Display related help section """

        help_location = "/user/qtgui/Perspectives/Fitting/fitting_help.html#add-multiply-models"
        self.parent.showHelp(help_location)

