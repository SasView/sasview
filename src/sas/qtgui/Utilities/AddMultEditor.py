"""
Widget for simple add / multiply editor.
"""
# numpy methods required for the validator! Don't remove.
# pylint: disable=unused-import,unused-wildcard-import,redefined-builtin
from numpy import *

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
import webbrowser

import os
import numpy as np
import re
import logging
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sasmodels.sasview_model import load_standard_models
from sas.qtgui.Perspectives.Fitting import ModelUtilities

# Local UI
from sas.qtgui.Utilities.UI.AddMultEditorUI import Ui_AddMultEditorUI

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

        self.setupSignals()

        self.list_models = self.readModels()

        # Fill models' comboboxes
        self.setupModels()

        self.setFixedSize(self.minimumSizeHint())

        # Name and directory for saving new plugin model
        self.plugin_filename = None
        self.plugin_dir = ModelUtilities.find_plugins_dir()

        # Validators
        rx = QtCore.QRegExp("^[A-Za-z0-9_]*$")
        txt_validator = QtGui.QRegExpValidator(rx)
        self.txtName.setValidator(txt_validator)

    def setupModels(self):
        """ Add list of models to 'Model1' and 'Model2' comboboxes """
        # Load the model dict
        self.cbModel1.addItems(self.list_models)
        self.cbModel2.addItems(self.list_models)

        # set the default initial value of Model1 and Model2
        index_ini_model1 = self.cbModel1.findText('sphere', QtCore.Qt.MatchFixedString)

        if index_ini_model1 >= 0:
            self.cbModel1.setCurrentIndex(index_ini_model1)
        else:
            self.cbModel1.setCurrentIndex(0)

        index_ini_model2 = self.cbModel2.findText('cylinder',
                                                  QtCore.Qt.MatchFixedString)
        if index_ini_model2 >= 0:
            self.cbModel2.setCurrentIndex(index_ini_model2)
        else:
            self.cbModel2.setCurrentIndex(0)

    def readModels(self):
        """ Generate list of models """
        models = load_standard_models()
        models_dict = {}
        for model in models:
            models_dict[model.name] = model

        return sorted([model_name for model_name in models_dict])

    def setupSignals(self):
        """ Signals from various elements """
        # check existence of output filename when entering name
        # or when overwriting not allowed
        self.txtName.editingFinished.connect(self.onNameCheck)
        self.chkOverwrite.stateChanged.connect(self.onOverwrite)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.onApply)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Help).clicked.connect(self.onHelp)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.close)

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
                logging.info("Model function ({}) has been set!\n".
                                format(str(s_title)))
                self.good_name = True
                self.txtName.setStyleSheet(BG_WHITE)
                self.plugin_filename = os.path.join(self.plugin_dir, filename)

        # Enable Apply push button only if valid name
        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).setEnabled(self.good_name)

    def onOperatorChange(self, index):
        """ Respond to operator combo box changes """

        self.lblEquation.setText("Plugin_model = scale_factor * "
                                 "(model_1 {} model_2) + background".
                                 format(self.cbOperator.currentText()))

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

        success = GuiUtils.checkModel(self.plugin_filename)

        if not success:
            return

        # Update list of models in FittingWidget and AddMultEditor
        self.parent.communicate.customModelDirectoryChanged.emit()
        # Re-read the model list so the new model is included
        self.list_models = self.readModels()
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
            desc_line = "{} {} {}".format(model1_name,
                                          operator,
                                          model2_name)

        name = os.path.splitext(os.path.basename(fname))[0]
        output = SUM_TEMPLATE.format(name=name,
                                     model1=model1_name,
                                     model2=model2_name,
                                     operator=operator,
                                     desc_line=desc_line)

        with open(fname, 'w') as out_f:
            out_f.write(output)

    def updateModels(self):
        """ Update contents of comboboxes with new plugin models """

        # Keep pointers to the current indices so we can show the comboboxes with
        # original selection
        model_1 = self.cbModel1.currentText()
        model_2 = self.cbModel2.currentText()

        self.cbModel1.blockSignals(True)
        self.cbModel1.clear()
        self.cbModel1.blockSignals(False)

        self.cbModel2.blockSignals(True)
        self.cbModel2.clear()
        self.cbModel2.blockSignals(False)
        # Retrieve the list of models
        model_list = self.readModels()
        # Populate the models comboboxes
        self.cbModel1.addItems(model_list)
        self.cbModel2.addItems(model_list)

        # Scroll back to the user chosen models
        self.cbModel1.setCurrentIndex(self.cbModel1.findText(model_1))
        self.cbModel2.setCurrentIndex(self.cbModel2.findText(model_2))

    def onHelp(self):
        """ Display related help section """

        try:
            help_location = GuiUtils.HELP_DIRECTORY_LOCATION + \
                            "/user/qtgui/Perspectives/Fitting/fitting_help.html#sum-multi-p1-p2"
            webbrowser.open('file://' + os.path.realpath(help_location))
        except AttributeError:
            # No manager defined - testing and standalone runs
            pass
