import ast
import logging
import os
import pathlib
import re
import traceback

from PySide6 import QtWidgets, QtCore, QtGui

from sas.sascalc.fit.models import find_plugins_dir

from sas.qtgui.Utilities import GuiUtils
from sas.qtgui.Utilities.UI.ReparameterizationEditorUI import Ui_ReparameterizationEditor
from sas.qtgui.Utilities.ModelSelector import ModelSelector
from sas.qtgui.Utilities.ParameterEditDialog import ParameterEditDialog

logger = logging.getLogger(__name__)

class ReparameterizationEditor(QtWidgets.QDialog, Ui_ReparameterizationEditor):

    def __init__(self, parent=None):
        super(ReparameterizationEditor, self).__init__(parent._parent)

        self.parent = parent

        self.setupUi(self)

        self.addSignals()

        self.onLoad()

        self.newParamTreeEditable = False
        self.old_model_name = None # Name of the model to be reparameterized
        self.new_params_dict = {} # Dictionary of new parameters to be added to the model
        self.is_modified = False
    
    def addSignals(self):
        self.selectModelButton.clicked.connect(self.onSelectModel)
        self.cmdCancel.clicked.connect(self.close)
        self.cmdApply.clicked.connect(self.onApply)
        self.cmdAddParam.clicked.connect(self.onAddParam)
        self.cmdDeleteParam.clicked.connect(self.onDeleteParam)
        self.cmdEditSelected.clicked.connect(self.editSelected)
        self.txtNewModelName.textChanged.connect(self.editorModelModified)
        self.txtFunction.textChanged.connect(self.editorModelModified)
    
    def onLoad(self):

        # Disable `Apply` button
        self.cmdApply.setEnabled(False)

        self.oldParamTree.setDisabledText("Load a model to display")
        self.newParamTree.setDisabledText("Add a parameter to display")
        self.oldParamTree.setEnabled(False)
        self.newParamTree.setEnabled(False)
        
        self.addTooltips()

        text = \
""""""
        self.txtFunction.insertPlainText(text)
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
        self.model_selector.returnModelParamsSignal.connect(lambda model_name, params: self.loadParams(params, self.oldParamTree, model_name))
        self.model_selector.show()

    def loadParams(self, params, tree, model_name=None, append=False):
        """
        Load parameters from the selected model into a tree widget
        :param param: sasmodels.modelinfo.Parameter class
        :param tree: the tree widget to load the parameters into
        :param model_name: the name of the model that the parameters are from
        """
        if tree == self.oldParamTree:
            tree.clear() # Clear the tree widget
        
        if not tree.isEnabled():
            # Enable tree if necessary
            tree.setEnabled(True)

        # Add parameters to the tree
        for param in params:
            item = QtWidgets.QTreeWidgetItem(tree)
            item.setText(0, param.name)
            tree.addTopLevelItem(item)
            self.addSubItems(param, item, append=append)
        
        if tree == self.oldParamTree:
            if tree.topLevelItemCount() == 0:
                # If no parameters were found, disable the tree
                tree.setDisabledText("No parameters found in model")
                tree.setEnabled(False)
            # Once model is loaded sucessfully, update txtSelectModelInfo to reflect the model name
            self.old_model_name = model_name
            self.lblSelectModelInfo.setText("Model <b>%s</b> loaded successfully" % self.old_model_name)
        
        self.setWindowEdited(True)

    def onAddParam(self):
        """
        Add parameter to "New parameters box" by invoking parameter editor dialog
        """
        self.param_creator = ParameterEditDialog(self)
        self.param_creator.returnNewParamsSignal.connect(lambda params: self.loadParams(params, self.newParamTree, append=True))
        self.param_creator.show()
    
    def onDeleteParam(self):
        """
        Delete the selected parameter from the newParamTree
        """
        delete_sucessful = False # Track whether the delete action was sucessful or not

        # Get selected item
        selected_item = self.newParamTree.currentItem()
        param_to_delete = self.getParameterSelection(selected_item)

        # Find the parameter item by using param_to_delete
        for i in range(self.newParamTree.topLevelItemCount()):
            param = self.newParamTree.topLevelItem(i)
            if param.text(0) == param_to_delete:
                # Remove the parameter from the tree
                self.newParamTree.takeTopLevelItem(i)
                # Remove the parameter from the dictionary
                self.new_params_dict.pop(param_to_delete)
                delete_sucessful = True
        
        if self.newParamTree.topLevelItemCount() == 0:
            # If there are no parameters left, disable the tree
            self.newParamTree.setEnabled(False)
        
        if not delete_sucessful:
            return logger.warning("Could not find parameter to delete: %s" % param_to_delete)
    
    def editSelected(self):
        """
        Edit the selected parameter in a new parameter editor dialog
        """
        # Get selected item
        selected_item = self.newParamTree.currentItem()
        param_to_open = self.getParameterSelection(selected_item)
        
        highlighted_property = selected_item.text(0) # What the user wants to edit specifically
        
        # Find the parameter item by using param_to_open and format as a dictionary
        param_properties = self.getParamProperties(self.newParamTree, param_to_open)
        param_properties['highlighted_property'] = highlighted_property # Which property the cursor will start on
        self.param_editor = ParameterEditDialog(self, param_properties)
        self.param_editor.returnEditedParamSignal.connect(self.updateParam)
        self.param_editor.show()
    
    def getParamProperties(self, tree, param_name):
        """
        Return a dictionary of property name: value pairs for the given parameter name
        """
        properties = {}
        for param in range(tree.topLevelItemCount()): # Iterate over all top-level items (parameters)
            param_item = tree.topLevelItem(param)
            if param_item.text(0) == param_name: # If the parameter name is the one the user selected
                properties['name'] = param_item.text(0)
                for property in range(param_item.childCount()): # Iterate over all properties (children) of the parameter and add them to dict
                    if param_item.child(property).text(0) == 'description':
                        # Access the description text, which is in another sub-item
                        prop_item = param_item.child(property).child(0)
                        properties['description'] = prop_item.text(1)
                    else:
                        prop_item = param_item.child(property)
                        properties[prop_item.text(0)] = prop_item.text(1)
                break
        return properties
    
    def updateParam(self, updated_param, old_name):
        """
        Update given parameter in the newParamTree with the updated properties
        :param updated_param: Sasview Parameter class with updated properties
        :param old_name: the old name of the parameter (so we can detect which parameter to update)
        """
        unpacked_param = updated_param[0] # updated_param is sent as a list but will only have one item. Unpack it.

        for i in range(self.newParamTree.topLevelItemCount()):
            param = self.newParamTree.topLevelItem(i)
            if param.text(0) == old_name:
                self.new_params_dict.pop(old_name) # Remove the old parameter from the dictionary
                # Delete all sub-items of the parameter
                while param.childCount() > 0:
                    sub_item = param.child(0)
                    param.removeChild(sub_item)

                # Now add all the updated properties
                self.addSubItems(unpacked_param, param, append=True)
                # Make sure to update the name of the parameter
                param.setText(0, unpacked_param.name)
    
    def onApply(self):
        """
        Generate output reparameterized model and write to file
        """
        # Get the name of the new model
        model_name = self.txtNewModelName.text()
        overwrite_plugin = self.chkOverwrite.isChecked()
        user_plugin_dir = pathlib.Path(find_plugins_dir())
        output_file_path = user_plugin_dir / (model_name + ".py")

        # Check if the file already exists
        if os.path.exists(output_file_path) and not overwrite_plugin:
            return logger.warning("File already exists and overwrite is not checked. Aborting.") # TODO Replace with a a dialog box

        # Write the new model to the file
        model_text = self.generateModelText()
        self.writeModel(output_file_path, model_text)

        # Test the model for errors (file must be generated first)
        error_line = self.checkModel(output_file_path)
        if error_line > 0:
            return

        self.txtFunction.setStyleSheet("")
        self.addTooltips() # Reset the tooltips

        # Notify user that model was written sucessfully
        msg = "Reparameterized model "+ model_name + " successfully created."
        self.parent.communicate.statusBarUpdateSignal.emit(msg)
        logger.info(msg)
    
        if self.is_modified:
            self.is_modified = False
            self.setWindowEdited(False)
            self.cmdApply.setEnabled(False)
    
    def generateModelText(self) -> str:
        """
        Generate the output model text
        """
        output = "" # TODO: Define the output model text, this is just a placeholder function for now
        translation_text = self.txtFunction.toPlainText()
        old_model_name = self.old_model_name
        parameters_text = ""
        for param_name, param_properties in self.new_params_dict.items():
            parameters_text += f"\n\t['{param_name}', '{param_properties['units']}', {param_properties['default']}, [{param_properties['min']}, {param_properties['max']}], '{param_properties['type']}', '{param_properties['description']}'],"
        output = REPARAMETARIZED_MODEL_TEMPLATE.format(parameters=parameters_text, translation=translation_text, old_model_name=old_model_name)
        return output

    def addSubItems(self, param, top_item, append=False):
        """
        Add sub-items to the given top-level item for the given parameter
        :param param: the Sasmodels Parameter class that contains properties to add
        :param top_item: the top-level item to add the properties to (QTreeWidgetItem)
        :param append: Whether or not to include parameter when exporting to model file
        """
        # Create list of properties: (display name, property name)
        properties_index = [ ("default", "default"),
                    ("min", "limits[0]"),
                    ("max", "limits[1]"),
                    ("units", "units"),
                    ("type", "type")
                    ]
        output_properties = {} # Dictionary of properties used in generating the output model text
        for prop in properties_index:
            sub_item = QtWidgets.QTreeWidgetItem(top_item)
            sub_item.setText(0, prop[0]) # First column is display name
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
            output_properties[prop[0]] = value # Add property to output dictionary

        # Now add the description as a collapsed item, separate from the other properties
        sub_item = QtWidgets.QTreeWidgetItem(top_item)
        sub_item.setText(0, "description")
        sub_sub_item = QtWidgets.QTreeWidgetItem(sub_item)
        description = str(param.description)
        sub_sub_item.setText(1, description)
        output_properties['description'] = description # Add description to output dictionary

        if append:
            # If the item is in the newParamTree, add the output properties to the dictionary
            self.new_params_dict[param.name] = output_properties
    
    def setWindowEdited(self, is_edited):
            """
            Change the widget name to indicate unsaved state
            Unsaved state: add "*" to filename display
            saved state: remove "*" from filename display
            """
            current_text = self.windowTitle()

            if is_edited:
                if current_text[-1] != "*":
                    current_text += "*"
            else:
                if current_text[-1] == "*":
                    current_text = current_text[:-1]
            self.setWindowTitle(current_text)
    
    def editorModelModified(self):
        """
        User modified the model in the Model Editor.
        Disable the plugin editor and show that the model is changed.
        """
        self.setWindowEdited(True)
        self.cmdApply.setEnabled(True)
        self.is_modified = True
    
    def checkModel(self, full_path):
        """
        Run ast and model checks
        Attempt to return the line number of the error if any
        :param full_path: full path to the model file
        :param translation_text: the text within
        """
        # successfulCheck = True
        error_line = 0
        try:
            with open(full_path, 'r', encoding="utf-8") as plugin:
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
                if ('File' in line and 'line' in line):
                    # If model check fails (not syntax) then 'line' and 'File' will be in adjacent lines
                    error_line = re.split('line ', line)[1]
                    try:
                        error_line = int(error_line)
                        break
                    except ValueError:
                        # Sometimes the line number is followed by more text
                        try:
                            error_line = error_line.split(',')[0]
                            error_line = int(error_line)
                            break
                        except ValueError:
                            error_line = 0

        return error_line

    ### CLASS METHODS ###
    
    @classmethod
    def getParameterSelection(cls, selected_item) -> str:
        """
        Return the text of the parameter's name even if selected_item is a 'property' item
        :param selected_item: QTreeWidgetItem that represents either a parameter or a property
        """
        if selected_item.parent() == None:
            # User selected a parametery, not a property
            param_to_open = selected_item.text(0)
        elif selected_item.parent().parent() != None:
            # User selected the description text
            param_to_open = selected_item.parent().parent().text(0)
        else:
            # User selected a property, not a parameter
            param_to_open = selected_item.parent().text(0)
        return param_to_open

    ### STATIC METHODS ###

    @staticmethod
    def writeModel(output_file_path, model_text):
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

    def closeEvent(self, event):
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