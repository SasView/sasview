import ast
import logging
import os
import pathlib
import re
import traceback

from numpy import inf
from PySide6 import QtCore, QtGui, QtWidgets

from sasmodels.modelinfo import Parameter

from sas.qtgui.Utilities import GuiUtils
from sas.qtgui.Utilities.ModelEditors.Dialogs.ModelSelector import ModelSelector
from sas.qtgui.Utilities.ModelEditors.Dialogs.ParameterEditDialog import ParameterEditDialog
from sas.qtgui.Utilities.ModelEditors.ReparamEditor.UI.ReparameterizationEditorUI import Ui_ReparameterizationEditor
from sas.system.user import find_plugins_dir

logger = logging.getLogger(__name__)


class ReparameterizationEditor(QtWidgets.QDialog, Ui_ReparameterizationEditor):

    def __init__(self, parent=None):
        super(ReparameterizationEditor, self).__init__(parent._parent)

        self.parent = parent

        self.setupUi(self)

        self.addSignals()

        self.onLoad()

        # Initialize instance parameters
        self.model_selector = None
        self.param_editor = None
        self.highlight = None
        self.loaded_model_name = None
        self.is_modified = False
        self.old_model_name = None

    def addSignals(self):
        self.selectModelButton.clicked.connect(self.onSelectModel)
        self.cmdCancel.clicked.connect(self.close)
        self.cmdApply.clicked.connect(self.onApply)
        self.cmdAddParam.clicked.connect(self.onAddParam)
        self.cmdDeleteParam.clicked.connect(self.onDeleteParam)
        self.cmdEditSelected.clicked.connect(self.editSelected)
        self.txtNewModelName.textChanged.connect(self.editorModelModified)
        self.txtFunction.textChanged.connect(self.editorModelModified)
        self.newParamTree.doubleClicked.connect(self.editSelected)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.cmdModelHelp.clicked.connect(self.onModelHelp)

    def onLoad(self):

        # Disable `Apply` button
        self.cmdApply.setEnabled(False)

        self.oldParamTree.setDisabledText("Load a model to display")
        self.newParamTree.setDisabledText("Add a parameter to display")
        self.oldParamTree.setEnabled(False)
        self.newParamTree.setEnabled(False)

        self.addTooltips()

        self.txtFunction.setText(DEFAULT_EDITOR_TEXT)
        self.txtFunction.setFont(GuiUtils.getMonospaceFont())

        # Validators
        rx = QtCore.QRegularExpression("^[A-Za-z0-9_]*$")

        txt_validator = QtGui.QRegularExpressionValidator(rx)
        self.txtNewModelName.setValidator(txt_validator)
        # Weird import location - workaround for a bug in Sphinx choking on
        # importing QSyntaxHighlighter
        # DO NOT MOVE TO TOP
        from sas.qtgui.Utilities.PythonSyntax import PythonHighlighter
        self.highlight = PythonHighlighter(self.txtFunction.document())

    def addTooltips(self):
        """
        Add the default tooltips to the text field
        """
        hint_function = "Example:\n\n"
        hint_function += "helper_constant = new_parameter1 * M_PI\n"
        hint_function += "old_parameter1 = helper_constant\n"
        hint_function += "old_parameter2 = helper_constant / new_parameter2\n"
        self.txtFunction.setToolTip(hint_function)

    def onSelectModel(self):
        """
        Launch model selection dialog
        """
        self.model_selector = ModelSelector(self)
        self.model_selector.returnModelParamsSignal.connect(
            lambda model_name, params: self.loadParams(params, self.oldParamTree, model_name))
        self.model_selector.show()

    def loadParams(self, params: [Parameter], tree: QtWidgets.QTreeWidget, model_name: str | None = None):
        """
        Load parameters from the selected model into a tree widget
        :param params: sasmodels.modelinfo.Parameter class
        :param tree: the tree widget to load the parameters into
        :param model_name: the name of the model that the parameters are from
        """
        if tree == self.oldParamTree:
            tree.clear()  # Clear the tree widget
            self.loaded_model_name = model_name

        if not tree.isEnabled():
            # Enable tree if necessary
            tree.setEnabled(True)

        # Add parameters to the tree
        for param in params:
            item = QtWidgets.QTreeWidgetItem(tree)
            item.setText(0, param.name)
            tree.addTopLevelItem(item)
            self.addSubItems(param, item)
            self.badPropsCheck(item)

        if tree == self.oldParamTree:
            if tree.topLevelItemCount() == 0:
                # If no parameters were found, disable the tree
                tree.setDisabledText("No parameters found in model")
                tree.setEnabled(False)
            # Once model is loaded sucessfully, update txtSelectModelInfo to reflect the model name
            self.old_model_name = model_name
            self.lblSelectModelInfo.setText("Model <b>%s</b> loaded successfully" % self.old_model_name)
            self.selectModelButton.setText("Change...")

        # Resize all columns to fit loaded content
        for i in range(tree.columnCount()):
            tree.resizeColumnToContents(i)

        self.editorModelModified()

        # Check for duplicate parameter names
        self.checkDuplicates(tree)

    def onAddParam(self):
        """
        Add parameter to "New parameters box" by invoking parameter editor dialog
        """
        self.param_editor = ParameterEditDialog(self)
        self.param_editor.returnNewParamsSignal.connect(lambda params: self.loadParams(params, self.newParamTree))
        self.param_editor.show()

    def onDeleteParam(self):
        """
        Delete the selected parameter from the newParamTree
        """
        delete_successful = False  # Track whether the delete action was successful or not

        # Get selected item
        selected_item = self.newParamTree.currentItem()
        param_to_delete = self.getParameterSelection(selected_item)

        # Find the parameter item by using param_to_delete
        for i in range(self.newParamTree.topLevelItemCount()):
            param = self.newParamTree.topLevelItem(i)
            if param == param_to_delete:
                # Remove the parameter from the tree
                self.newParamTree.takeTopLevelItem(i)
                delete_successful = True

        if self.newParamTree.topLevelItemCount() == 0:
            # If there are no parameters left, disable the tree
            self.newParamTree.setEnabled(False)

        if not delete_successful:
            return logger.warning("Could not find parameter to delete: %s" % param_to_delete.text(0))
        else:
            self.editorModelModified()

    def editSelected(self):
        """
        Edit the selected parameter in a new parameter editor dialog
        """
        # Get selected item
        selected_item = self.newParamTree.currentItem()  # The item that the user selected (could be a sub-item)
        if not selected_item:
            # User has no current selection in newParamTree. Throw a warning dialog and return.
            msg = "No parameter selected. Please select a parameter to edit."
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            msgBox.setWindowTitle("No Parameter Selected")
            msgBox.setText(msg)
            msgBox.addButton("OK", QtWidgets.QMessageBox.AcceptRole)
            return msgBox.exec_()

        param_to_open = self.getParameterSelection(selected_item) # The top-level item to open

        highlighted_property = selected_item.text(0) # What the user wants to edit specifically

        # Find the parameter item by using param_to_open and format as a dictionary
        param_properties = self.getParamProperties(param_to_open)
        self.onAddParam()
        # Populate the editor with the parameter values
        if self.param_editor:
            self.param_editor.properties = param_properties
            self.param_editor.qtree_item = param_to_open # Item to edit is always the parent of the selected_item!
            self.param_editor.onLoad()
            self.param_editor.returnEditedParamSignal.connect(self.updateParam)

    def getParamProperties(self, param: QtWidgets.QTreeWidgetItem) -> dict:
        """
        Return a dictionary of property name: value pairs for the given parameter
        :param param: the parameter to get properties for (QTreeWidgetItem)
        """
        properties = {'name': param.text(0)}
        # Iterate over all properties (children) of the parameter and add them to dict
        for prop in range(param.childCount()):
            if param.child(prop).text(0) == 'description':
                # Access the description text, which is in another sub-item
                prop_item = param.child(prop).child(0)
                properties['description'] = prop_item.text(1)
            else:
                prop_item = param.child(prop)
                properties[prop_item.text(0)] = prop_item.text(1)
        return properties

    def updateParam(self, updated_param: [Parameter], qtree_item: QtWidgets.QTreeWidgetItem):
        """
        Update given parameter in the newParamTree with the updated properties
        :param updated_param: Sasview Parameter class with updated properties
        :param qtree_item: the qtree_item to update
        """
        unpacked_param = updated_param[0]  # updated_param is sent as a list but will only have one item. Unpack it.

        # Delete all sub-items of the parameter
        while qtree_item.childCount() > 0:
            sub_item = qtree_item.child(0)
            qtree_item.removeChild(sub_item)

        # Now add all the updated properties
        self.addSubItems(unpacked_param, qtree_item)
        # Make sure to update the name of the parameter
        qtree_item.setText(0, unpacked_param.name)
        self.badPropsCheck(qtree_item)  # Check for bad parameter properties
        self.checkDuplicates(self.newParamTree)  # Check for duplicate parameter names

    def _can_be_saved_or_give_error(self):
        """Check to see if a model name exists and everything can be written"""
        model_name = self.txtNewModelName.text()
        overwrite_plugin = self.chkOverwrite.isChecked()
        user_plugin_dir = pathlib.Path(find_plugins_dir())
        output_file_path = user_plugin_dir / (model_name + ".py")

        # Check if the file already exists
        if os.path.exists(output_file_path) and not overwrite_plugin:
            msg = "File with specified name already exists.\n"
            msg += "Please specify different filename or allow file overwrite."
            QtWidgets.QMessageBox.critical(self, "Overwrite Error", msg)
            return False
        # Check if the model name is empty
        if not model_name:
            msg = "No model name specified.\n"
            msg += "Please specify a name before continuing."
            QtWidgets.QMessageBox.critical(self, "Model Error", msg)
            return False
        return True

    def onApply(self):
        """
        Generate output reparameterized model and write to file
        """
        # Get the name of the new model
        model_name = self.txtNewModelName.text()
        user_plugin_dir = pathlib.Path(find_plugins_dir())
        output_file_path = user_plugin_dir / (model_name + ".py")

        # Check if the file already exists
        if not self._can_be_saved_or_give_error():
            return

        # Check if there are model warnings
        for i in range(self.newParamTree.topLevelItemCount()):
            param = self.newParamTree.topLevelItem(i)
            if param.toolTip(1) != "":
                msgBox = QtWidgets.QMessageBox(self)
                msgBox.setIcon(QtWidgets.QMessageBox.Warning)
                msgBox.setWindowTitle("Model Warning")
                msgBox.setText("Some of your parameters contain warnings.\n"
                               "This could cause errors or unexpected behavior in the model.")
                msgBox.addButton("Continue anyways", QtWidgets.QMessageBox.AcceptRole)
                cancelButton = msgBox.addButton(QtWidgets.QMessageBox.Cancel)
                msgBox.exec_()
                # Check which button was clicked
                if msgBox.clickedButton() == cancelButton:
                    # Cancel button clicked
                    return

        # Write the new model to the file
        model_text = self.generateModelText()
        self.writeModel(output_file_path, model_text)
        self.parent.communicate.customModelDirectoryChanged.emit()  # Refresh the list of custom models

        # Test the model for errors (file must be generated first)
        error_line = self.checkModel(output_file_path)
        if error_line > 0:
            return

        self.txtFunction.setStyleSheet("")
        self.addTooltips()  # Reset the tooltips

        # Notify user that model was written sucessfully
        msg = f"Reparameterized model {model_name} successfully created."
        self.parent.communicate.statusBarUpdateSignal.emit(msg)
        logger.info(msg)

        self.is_modified = False
        self.setWindowEdited(False)
        self.cmdApply.setEnabled(False)

    def generateModelText(self) -> str:
        """
        Generate the output model text
        """
        translation_text = self.txtFunction.toPlainText()
        old_model_name = self.old_model_name
        parameters_text = ""
        # Order in this list MATTERS! Don't change or the order of properties in the output model will be wrong.
        output_properties = [
            "name",
            "units",
            "default",
            "min",
            "max",
            "type",
            "description"
        ]

        # Format the parameters into text for the output file
        for i in range(self.newParamTree.topLevelItemCount()):
            param = self.newParamTree.topLevelItem(i)
            param_properties = self.getParamProperties(param)
            parameters_text += "\n\t[ "
            for output_property in output_properties:
                if output_property not in ('min', 'max'):
                    # Add the property to the output text
                    parameters_text += f"{param_properties[output_property]}, " if output_property == "default" \
                        else f"'{param_properties[output_property]}', "
                # min and max must be formatted together as a list in the output, so we need to handle them separately
                elif output_property == 'min':
                    parameters_text += f"[{param_properties[output_property]}, "
                elif output_property == 'max':
                    parameters_text += f"{param_properties[output_property]}], "

            parameters_text = parameters_text[:-2] # Remove trailing comma and space
            parameters_text += "],"
        output = REPARAMETARIZED_MODEL_TEMPLATE.format(
            parameters=parameters_text, translation=translation_text, old_model_name=old_model_name)
        return output

    def addSubItems(self, param: Parameter, top_item: QtWidgets.QTreeWidgetItem):
        """
        Add sub-items to the given top-level item for the given parameter
        :param param: the Sasmodels Parameter class that contains properties to add
        :param top_item: the top-level item to add the properties to (QTreeWidgetItem)
        """
        # Create list of properties: (display name, property name)
        properties_index = [("default", "default"),
                            ("min", "limits[0]"),
                            ("max", "limits[1]"),
                            ("units", "units"),
                            ("type", "type")
                            ]
        output_properties = {}  # Dictionary of properties used in generating the output model text
        for prop in properties_index:
            sub_item = QtWidgets.QTreeWidgetItem(top_item)
            sub_item.setText(0, prop[0])  # First column is display name
            if '[' in prop[1]:
                # Limit properties have an index, so we need to extract it
                prop_name, index = prop[1].split('[')
                index = int(index[:-1])  # Remove the closing ']' and convert to int
                # Use getattr to get the property, then index into it
                value = getattr(param, prop_name)[index]
                sub_item.setText(1, str(value))
            else:
                value = getattr(param, prop[1])
                sub_item.setText(1, str(value))
            output_properties[prop[0]] = value  # Add property to output dictionary

        # Now add the description as a collapsed item, separate from the other properties
        sub_item = QtWidgets.QTreeWidgetItem(top_item)
        sub_item.setText(0, "description")
        sub_sub_item = QtWidgets.QTreeWidgetItem(sub_item)
        description = str(param.description)
        sub_sub_item.setText(1, description)
        output_properties['name'] = param.name  # Add name to output dictionary
        output_properties['description'] = description  # Add description to output dictionary

    def setWindowEdited(self, is_edited: bool):
            """
            Change the widget name to indicate modified state
            Modified - add "*" to filename display
            saved - remove "*" from filename display
            """
            current_text = self.windowTitle()
            # Remove any asterisks from the end of the name
            current_text = current_text.rstrip("*")

            # Add one if the model has been edited but not saved
            if is_edited:
                current_text += "*"

            self.setWindowTitle(current_text)

    def editorModelModified(self):
        """
        User modified the model in the Model Editor.
        Disable the plugin editor and show that the model is changed.
        """
        # Check to see if model was edited back into original state
        f_box = True if self.txtFunction.toPlainText() in ["", DEFAULT_EDITOR_TEXT] else False
        n_box = True if self.txtNewModelName.text() == "" else False
        p_boxes = True if not self.newParamTree.isEnabled() and not self.oldParamTree.isEnabled() else False

        if all([f_box, n_box, p_boxes]):
            # Model was edited back into default state, so no need to prompt user to save before exiting
            self.setWindowEdited(False)
            self.cmdApply.setEnabled(False)
            self.is_modified = False
        else:
            # Otherwise, model was edited and needs to be saved before exiting
            self.setWindowEdited(True)
            self.cmdApply.setEnabled(True)
            self.is_modified = True

    def checkModel(self, full_path: str | pathlib.Path) -> int:
        """
        Run ast and model checks and attempt to return the line number of the error if any
        :param full_path: full path to the model file
        """
        error_line = 0
        try:
            with open(full_path, encoding="utf-8") as plugin:
                model_str = plugin.read()
            ast.parse(model_str)
            GuiUtils.checkModel(full_path)

        except Exception as ex:
            msg = "Error building model: " + str(ex)
            logging.error(msg)
            # print four last lines of the stack trace
            # this will point out the exact line failing
            all_lines = traceback.format_exc().split('\n')
            last_lines = all_lines[-4:]
            traceback_to_show = '\n'.join(last_lines)
            logging.error(traceback_to_show)

            # Set the status bar message
            # GuiUtils.Communicate.statusBarUpdateSignal.emit("Model check failed")
            self.parent.communicate.statusBarUpdateSignal.emit("Model check failed")

            # Format text box with error indicators
            self.txtFunction.setStyleSheet("border: 5px solid red")
            # last_lines = traceback.format_exc().split('\n')[-4:]
            traceback_to_show = '\n'.join(last_lines)
            self.txtFunction.setToolTip(traceback_to_show)

            # attempt to find the failing command line number, usually the last line with
            # `File ... line` syntax
            reversed_error_text = list(reversed(all_lines))
            for line in reversed_error_text:
                if "File" in line and "line" in line:
                    # If model check fails (not syntax) then 'line' and 'File' will be in adjacent lines
                    error_line = re.match("(.*)line (?P<line_number>[0-9]*)(,?)(.*)", line)
                    try:
                        error_line = int(error_line.group("line_number"))
                        break
                    except ValueError:
                        # Sometimes the line number is followed by more text
                        error_line = 0

        return error_line

    def badPropsCheck(self, param_item: QtWidgets.QTreeWidgetItem):
        """
        Check a parameter for bad properties.
        :param param_item: the parameter to check (QTreeWidgetItem)
        """
        self.removeParameterWarning(param_item)

        # Get dictionary form of properties for easy manipulation
        error_message = ""
        properties = {'name': param_item.text(0)}
        for i in range(param_item.childCount()):
            prop = param_item.child(i)
            properties[prop.text(0)] = prop.text(1)

        # Ensure the name is not empty
        if properties['name'] == "":
            error_message += "Parameter name cannot be empty\n"

        # List of properties to convert to floats
        conversion_list = ['min', 'max', 'default']

        # Ensure that there is at least min, max, and default properties
        macro_set = {'M_PI', 'M_PI_2', 'M_PI_4', 'M_SQRT1_2', 'M_E', 'M_PI_180', 'M_4PI_3', inf, -inf}
        for to_convert in conversion_list:
            if to_convert not in properties or properties[to_convert] == "":
                error_message += f"Missing '{to_convert}' property\n"
                continue  # Do not convert this property
            elif properties[to_convert] in macro_set:
                # Skip if the value is a macro
                continue
            try:
                properties[to_convert] = float(properties.get(to_convert))
            except ValueError:
                error_message += f"'{to_convert}' contains invalid value\n"

        # Check if min is less than max
        if 'min' not in error_message and 'max' not in error_message and properties['min'] >= properties['max']:
            error_message += "Minimum value must be less than maximum value\n"

        # Ensure that units and type are not numbers
        for item in ['units', 'type']:
            try:
                float(properties.get(item, None))
                error_message += f"'{item}' must be a string or left blank.\n"
            except ValueError:
                pass

        error_message = error_message.strip()  # Remove trailing newline
        if error_message != "":
            # If there are any errors, display a warning icon
            self.parameterWarning(param_item, error_message)

    def checkDuplicates(self, tree: QtWidgets.QTreeWidget):
        """
        Check for parameters with the same name and display caution icons if found.
        NOTE: This method MUST come after badPropsCheck, as badPropsCheck overrides existing tooltip text,
        while this method will add to it if needed.
        :param tree: the QTreeWidget to check for duplicates.
        """
        # If more than one parameter in the tree is the same, display warning icon
        name_list = []
        duplicates = []
        for i in range(tree.topLevelItemCount()):
            item = tree.topLevelItem(i)
            item_name = item.text(0)
            current_tooltip = item.toolTip(1)
            if item_name not in name_list:
                name_list.append(item_name)
            else:
                duplicates.append(item_name)

            duplicate_warning = "Cannot use duplicate parameter names"
            if current_tooltip == duplicate_warning:
                # If tooltip is already displaying the warning, clear it and then check if it needs to be re-added
                # Therefore, we can avoid adding the same warning multiple times
                self.removeParameterWarning(item)

            if item.text(0) in duplicates:
                updated_tooltip = current_tooltip + "\n" + duplicate_warning
                self.parameterWarning(item, updated_tooltip)

    def parameterWarning(self, table_item: QtWidgets.QTreeWidgetItem, tool_tip_text: str):
        """
        Display a warning icon on a parameter and set tooltip.
        :param table_item: The QTreeWidgetItem to add the icon to
        :param tool_tip_text: The tooltip text to display when the user hovers over the warning
        """
        icon = self.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
        table_item.setToolTip(1, tool_tip_text)
        table_item.setIcon(1, icon)

    def onHelp(self):
        """
        Show the "Reparameterization" section of help
        """
        tree_location = "/user/qtgui/Perspectives/Fitting/fitting_help.html#reparameterization-editor"
        self.parent.showHelp(tree_location)

    def onModelHelp(self):
        """
        Show the help page of the loaded model in the OldParamTree
        """
        tree_base = "/user/models/"
        if (self.loaded_model_name is not None
                and self.loaded_model_name not in list(self.model_selector.custom_models.values())):
            tree_location = tree_base + f"{self.loaded_model_name}.html"
            self.parent.showHelp(tree_location)
        else:
            logging.info("No model detected to have been loaded. Showing default help page.")
            self.onHelp()

    ### CLASS METHODS ###

    @classmethod
    def removeParameterWarning(cls, table_item: QtWidgets.QTreeWidgetItem):
        """
        Remove the warning icon from a parameter
        :param table_item: The QTreeWidgetItem to remove the icon from
        """
        table_item.setToolTip(1, "")
        table_item.setIcon(1, QtGui.QIcon())

    @classmethod
    def getParameterSelection(cls, selected_item: QtWidgets.QTreeWidgetItem) -> QtWidgets.QTreeWidgetItem:
        """
        Return the QTreeWidgetItem of the parameter even if selected_item is a 'property' (sub) item
        :param selected_item: QTreeWidgetItem that represents either a parameter or a property
        """
        if selected_item.parent() is None:
            # User selected a parameter, not a property
            param_to_open = selected_item
        elif selected_item.parent().parent() is not None:
            # User selected the description text
            param_to_open = selected_item.parent().parent()
        else:
            # User selected a property, not a parameter
            param_to_open = selected_item.parent()
        return param_to_open

    ### STATIC METHODS ###

    @staticmethod
    def writeModel(output_file_path: str | pathlib.Path, model_text: str):
        """
        Write the new model to the given file
        :param output_file_path: pathlib.Path object pointing to output file location
        :param model_text: str of the model text to write
        """
        try:
            with open(output_file_path, 'w') as f:
                f.write(model_text)
        except Exception as ex:
            logger.error("Error writing model to file: %s" % ex)

    ### OVERRIDES ###
    # Functions that overwrite the default behavior of the parent class

    def closeEvent(self, event: QtCore.QEvent):

        if self.is_modified:
            # Display a warning allowing the user to cancel or continue
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            msgBox.setWindowTitle("Unsaved Changes")
            msgBox.setText("You have unsaved changes. Are you sure you want to close?")
            msgBox.addButton("Close without saving", QtWidgets.QMessageBox.AcceptRole)
            cancelButton = msgBox.addButton(QtWidgets.QMessageBox.Cancel)

            msgBox.exec_()
            if msgBox.clickedButton() == cancelButton:
                # Cancel button clicked
                event.ignore()
                return

        self.close()
        self.deleteLater()  # Schedule the window for deletion


REPARAMETARIZED_MODEL_TEMPLATE = '''\
from numpy import inf

from sasmodels.core import reparameterize
from sasmodels.special import *

parameters = [
    # name, units, default, [min, max], type, description{parameters}
]

translation = """
    {translation}
"""

model_info = reparameterize('{old_model_name}', parameters, translation, __file__)

'''

DEFAULT_EDITOR_TEXT = """
# EXAMPLE TEXT
# Change the ellipsoid model, replacing the polar and equatorial radii with the particle volume and eccentricity factor

# Re - new equatorial radius calculation using new parameters - cbrt is the cube root
Re = cbrt(volume/eccentricity/M_4PI_3)
# Replace polar radius with eccentricity
radius_polar = eccentricity*Re
# Replace radius_equatorial with Re
radius_equatorial = Re
"""
