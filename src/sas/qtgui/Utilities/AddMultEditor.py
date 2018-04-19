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
       The user also gives a brief help for the model in a description box and
       must provide a unique name which is verified as unique before the new
    """
    def __init__(self, parent=None):
        super(AddMultEditor, self).__init__()

        self.parent = parent

        self.setupUi(self)

        #  uncheck self.chkOverwrite
        self.chkOverwrite.setChecked(False)

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
        self.chkOverwrite.stateChanged.connect(self.onNameCheck)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.onApply)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Help).clicked.connect(self.onHelp)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Close).clicked.connect(self.close)

        # change displayed equation when changing operator
        self.cbOperator.currentIndexChanged.connect(self.onOperatorChange)

    def onNameCheck(self):
        """
        Check if proposed new model name does not already exists
        (if the overwriting is not allowed).
        If not an error message not show error message is displayed
        """

        # Get the function/file name
        title = self.txtName.text().lstrip().rstrip()

        filename = title + '.py'

        if self.chkOverwrite.isChecked():
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

        return self.good_name

    def onOperatorChange(self, index):
        """ Respond to operator combo box changes """

        self.lblEquation.setText("Plugin_model = scale_factor * "
                                 "(model_1 {} model_2) + background".
                                 format(self.cbOperator.currentText()))

    def onApply(self):
        """ Validity check, save model to file """

        # if name OK write file and test
        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply).setEnabled(False)

        self.write_new_model_to_file(self.plugin_filename,
                                     self.cbModel1.currentText(),
                                     self.cbModel2.currentText(),
                                     self.cbOperator.currentText())

        success = self.checkModel(self.plugin_filename)

        if success:
            # Update list of models in FittingWidget and AddMultEditor
            self.parent.communicate.customModelDirectoryChanged.emit()
            self.updateModels()

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

    # same version as in TabbedModelEditor
    @classmethod
    def checkModel(cls, path):
        """ Check that the model saved in file 'path' can run. """

        # try running the model
        from sasmodels.sasview_model import load_custom_model
        Model = load_custom_model(path)
        model = Model()
        q = np.array([0.01, 0.1])
        _ = model.evalDistribution(q)
        qx, qy = np.array([0.01, 0.01]), np.array([0.1, 0.1])
        _ = model.evalDistribution([qx, qy])
        # check the model's unit tests run
        from sasmodels.model_test import run_one
        # TODO see comments in TabbedModelEditor
        # result = run_one(path)
        result = True  # to be commented out
        return result

    def updateModels(self):
        """ Update contents of comboboxes with new plugin models """

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

    def onHelp(self):
        """ Display related help section """

        try:
            help_location = GuiUtils.HELP_DIRECTORY_LOCATION + \
                            "/user/sasgui/perspectives/fitting/fitting_help.html#sum-multi-p1-p2"
            webbrowser.open('file://' + os.path.realpath(help_location))
        except AttributeError:
            # No manager defined - testing and standalone runs
            pass
