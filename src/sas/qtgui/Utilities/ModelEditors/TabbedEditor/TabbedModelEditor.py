# global
import ast
import datetime
import importlib.util
import logging
import os
import re
import traceback
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.CustomGUI.CodeEditor import QCodeEditor
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.ModelEditor import ModelEditor
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.UI.TabbedModelEditor import Ui_TabbedModelEditor
from sas.sascalc.fit import models
from sas.system.user import MAIN_DOC_SRC, find_plugins_dir


class TabbedModelEditor(QtWidgets.QDialog, Ui_TabbedModelEditor):
    """
    Model editor "container" class describing interaction between
    plugin definition widget and model editor widget.
    Once the model is defined, it can be saved as a plugin.
    """
    # Signals for intertab communication plugin -> editor
    applySignal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget = None, edit_only: bool = False, model: bool = False,
                 load_file: str | None = None):
        super(TabbedModelEditor, self).__init__(parent._parent)

        self.parent = parent

        self.setupUi(self)

        # globals
        self.filename_py = ""
        self.filename_c = ""
        self.is_python = True
        self.is_documentation = False
        self.window_title = self.windowTitle()
        self.edit_only = edit_only
        self.load_file = load_file.lstrip("//") if load_file else None
        self.model = model
        self.is_modified = False
        self.showNoCompileWarning = True
        self.label = None
        self.file_to_regenerate = ""
        self.include_polydisperse = False

        self.addWidgets()

        self.addSignals()

        if self.load_file is not None:
            self.onLoad(at_launch=True)

    def addWidgets(self):
        """
        Populate tabs with widgets
        """
        # Set up widget enablement/visibility
        self.cmdLoad.setVisible(self.edit_only)

        # Add tabs
        # Plugin definition widget
        self.plugin_widget = PluginDefinition(self)
        self.tabWidget.addTab(self.plugin_widget, "Plugin Definition")
        self.setPluginActive(True)

        self.editor_widget = ModelEditor(self)
        self.c_editor_widget = ModelEditor(self)
        # Initially, nothing in the editors
        self.editor_widget.setEnabled(False)
        self.c_editor_widget.setEnabled(False)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)


        # Initially hide form function box
        self.plugin_widget.formFunctionBox.setVisible(False)

        if self.edit_only:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setText("Save")
            # Hide signals from the plugin widget
            self.plugin_widget.blockSignals(True)
            # and hide the tab/widget itself
            self.tabWidget.removeTab(0)
            self.addTab("python", "Model Editor")

        if self.model is not None:
            self.cmdLoad.setText("Load file...")

    def addSignals(self):
        """
        Define slots for common widget signals
        """
        # buttons
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(self.onApply)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.onCancel)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Help).clicked.connect(self.onHelp)
        self.cmdLoad.clicked.connect(self.onLoad)
        # signals from tabs
        self.plugin_widget.modelModified.connect(self.editorModelModified)
        self.editor_widget.modelModified.connect(self.editorModelModified)
        self.c_editor_widget.modelModified.connect(self.editorModelModified)
        self.plugin_widget.txtName.editingFinished.connect(self.pluginTitleSet)
        self.plugin_widget.includePolydisperseFuncsSignal.connect(self.includePolydisperseFuncs)
        self.plugin_widget.omitPolydisperseFuncsSignal.connect(self.omitPolydisperseFuncs)
        # locally emitted signals
        self.applySignal.connect(self._onApply)

    def setPluginActive(self, is_active: bool = True):
        """
        Enablement control for all the controls on the simple plugin editor
        """
        self.plugin_widget.setEnabled(is_active)

    def saveClose(self) -> bool:
        """
        Check if file needs saving before closing or model reloading
        """
        saveCancelled = False
        ret = self.onModifiedExit()
        if ret == QtWidgets.QMessageBox.Cancel:
            saveCancelled = True
        elif ret == QtWidgets.QMessageBox.Save:
            self.updateFromEditor()
        return saveCancelled

    def closeEvent(self, event: QtCore.QEvent):
        """
        Overwrite the close even to assure intent
        """
        if self.is_modified and self.saveClose():
            return
        event.accept()

    def onLoad(self, at_launch: bool = False):
        """
        Loads a model plugin file. at_launch is value of whether to attempt a load of a file from launch of the widget or not
        """
        self.is_python = True # By default assume the file you load is python

        if self.is_modified and self.saveClose():
            return
        elif self.is_modified:
            self.is_modified = False

        # If we are loading in a file at the launch of the editor instead of letting the user pick, we need to process the HTML location from
        # the documentation viewer into the filepath for its corresponding RST
        if at_launch:
            user_models = find_plugins_dir()
            user_model_name = user_models + self.load_file + ".py"

            if self.model is True:
                # Find location of model .py files and load from that location
                filename = user_model_name if os.path.isfile(user_model_name) \
                    else MAIN_DOC_SRC / "user" / "models" / "src" / (self.load_file + ".py")
            else:
                filename = MAIN_DOC_SRC / self.load_file.replace(".html", ".rst")
                self.is_python = False
                self.is_documentation = True
        else:
            plugin_location = find_plugins_dir()
            filename = QtWidgets.QFileDialog.getOpenFileName(
                                            self,
                                            'Open Plugin',
                                            plugin_location,
                                            'SasView Plugin Model (*.py)',
                                            None)[0]

        # Load the file
        if not filename:
            logging.info("No data file chosen.")
            return

        # remove c-plugin tab, if present.
        if self.tabWidget.count() > 1:
            self.tabWidget.removeTab(1)
        self.file_to_regenerate = filename
        self.loadFile(str(filename))

    def allBuiltinModels(self) -> [str]:
        """
        create a list of all builtin models
        """
        from sas.sascalc.fit.models import ModelManager

        model_list = ModelManager().cat_model_list()
        model_names = [model.name for model in model_list]
        return model_names

    def loadFile(self, filename: str | Path):
        """
        Performs the load operation and updates the view
        """
        self.editor_widget.blockSignals(True)
        plugin_text = ""
        with open(filename, encoding="utf-8") as plugin:
            plugin_text = plugin.read()
            self.editor_widget.txtEditor.setPlainText(plugin_text)
        self.editor_widget.setEnabled(True)
        self.editor_widget.blockSignals(False)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
        self.filename_py = Path(filename)
        display_name = self.filename_py.stem
        if not self.model:
            self.setWindowTitle(self.window_title + " - " + display_name)
        else:
            self.setWindowTitle("Documentation Editor" + " - " + display_name)
        # Name the tab with .py filename
        self.tabWidget.setTabText(0, display_name)

        # In case previous model was incorrect, change the frame colours back
        self.editor_widget.txtEditor.setStyleSheet("")
        self.editor_widget.txtEditor.setToolTip("")

        # Check the validity of loaded model if the model is python
        if self.is_python:
            error_line = self.findFirstError(self.filename_py)
            if error_line >= 0:
                # select bad line
                cursor = QtGui.QTextCursor(self.editor_widget.txtEditor.document().findBlockByLineNumber(error_line-1))
                self.editor_widget.txtEditor.setTextCursor(cursor)
                # Do not return because we still want to load C file if it exists
                QtWidgets.QMessageBox.warning(self, "Model check failed", "The loaded model contains errors. Please correct all errors before using model.")

        # See if there is filename.c present
        self.filename_c = self.filename_py.parent / self.filename_py.name.replace(".py", ".c")
        if not self.filename_c.exists() or ".rst" in self.filename_c.name:
            return
        # add a tab with the same highlighting
        c_display_name = self.filename_c.name
        self.c_editor_widget = ModelEditor(self, is_python=False)
        self.tabWidget.addTab(self.c_editor_widget, c_display_name)
        # Read in the file and set in on the widget
        with open(self.filename_c, encoding="utf-8") as plugin:
            self.c_editor_widget.txtEditor.setPlainText(plugin.read())
        self.c_editor_widget.modelModified.connect(self.editorModelModified)

    def onModifiedExit(self) -> int:
        msg_box = QtWidgets.QMessageBox(self)
        msg_box.setWindowTitle("SasView Model Editor")
        msg_box.setText("The document has been modified.")
        msg_box.setInformativeText("Do you want to save your changes?")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.Save)
        return msg_box.exec()

    def onCancel(self):
        """
        Accept if document not modified, confirm intent otherwise.
        """
        if not (self.is_modified and self.saveClose()):
            self.reject()

    def onApply(self):
        """
        Write the plugin and update the model editor if plugin editor open
        Write/overwrite the plugin if model editor open
        """
        # Ensure focus leaves any inputs currently being edited and allow their signals to trigger
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setFocus()
        # Send out a new signal that is queued after input change signals from any input
        self.applySignal.emit()

    def _onApply(self):
        if isinstance(self.tabWidget.currentWidget(), PluginDefinition):
            self.updateFromPlugin()
        else:
            self.updateFromEditor()
        self.is_modified = False

    def editorModelModified(self):
        """
        User modified the model in the Model Editor.
        Disable the plugin editor and show that the model is changed.
        """
        self.setTabEdited(True)
        self.plugin_widget.txtFunction.setStyleSheet("")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
        self.is_modified = True

    def omitPolydisperseFuncs(self):
        """
        User has no polydisperse parameters.
        Omit polydisperse-only functions from model text.
        Note that this is necessary because Form Volume Function text box does not clear its text when it disappears.
        """
        self.include_polydisperse = False

    def includePolydisperseFuncs(self):
        """
        User has defined polydisperse parameters.
        Include polydisperse-only functions from model text.
        By default these are not included even if text exists in Form Volume Function text box.
        """
        self.include_polydisperse = True

    def pluginTitleSet(self):
        """
        User modified the model name.
        Display the model name in the window title
        and allow for model save.
        """
        # Ensure plugin name is non-empty
        model = self.getModel()
        if "filename" in model and model["filename"]:
            self.setWindowTitle(self.window_title + " - " + model["filename"])
            self.setTabEdited(True)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
            self.is_modified = True
        else:
            # the model name is empty - disable Apply and clear the editor
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
            self.editor_widget.blockSignals(True)
            self.editor_widget.txtEditor.setPlainText("")
            self.editor_widget.blockSignals(False)
            self.editor_widget.setEnabled(False)

    def setTabEdited(self, is_edited: bool):
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

    def updateFromPlugin(self):
        """Write the plugin and update the model editor"""
        # get current model
        model = self.getModel()

        # get required filename
        filename = model.get("filename", None)
        if not filename:
            # If No filename given
            QtWidgets.QMessageBox.critical(self, "Plugin Error", "Please specify a filename.")
            return

        # check if file exists
        plugin_location = models.find_plugins_dir()

        # Generate the full path of the python path for the model and ensure the extension is .py
        full_path = Path(plugin_location) / filename
        full_path_py = full_path.with_suffix(".py")
        full_path_c = full_path.with_suffix(".c")

        if model["gen_python"]:
            # Update the global path definition
            self.filename_py = full_path_py
            if not self.canWriteModel(model, full_path_py):
                return
            # generate the model representation as string
            model_str = self.generatePyModel(model, full_path_py)
            self.writeFile(full_path_py, model_str)

            # Add a tab to TabbedModelEditor for the Python model if not already open
            self.createOrUpdateTab(self.filename_py, self.editor_widget)
            self.populateWidgetTextBox(self.editor_widget, model_str)

        if model["gen_c"]:
            # Update the global path definition
            self.filename_c = full_path_c
            if not self.canWriteModel(model, self.filename_c):
                return
            # generate the model representation as string
            c_model_str = self.generateCModel(model, self.filename_c)
            self.writeFile(self.filename_c, c_model_str)

            # Add a tab to TabbedModelEditor for the C model if not already open
            self.createOrUpdateTab(self.filename_c, self.c_editor_widget)
            self.populateWidgetTextBox(self.c_editor_widget, c_model_str)

        # Run the model test in sasmodels and check model syntax. Returns error line if checks fail.
        if full_path_py.exists():
            if self.findFirstError(full_path_py) > 0:
                return
        elif self.showNoCompileWarning:
            # Show message box that tells user no model checks will be run until a python file of the same name is created in the plugins directory.
            self.noModelCheckWarning()

        # disable "Apply"
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)

        # Allow user to toggle 'Generate Python model' checkbox
        self.plugin_widget.enablePyCheckboxSignal.emit()

        self.editor_widget.setEnabled(True)

        # Set the widget title
        self.setTabEdited(False)

        # Notify listeners
        self.parent.communicate.customModelDirectoryChanged.emit()

        # Notify the user
        msg = "Custom model " + filename + " successfully created."
        self.parent.communicate.statusBarUpdateSignal.emit(msg)
        logging.info(msg)

    def createOrUpdateTab(self, filename: str | Path, widget: QtWidgets.QWidget):
        """Check if the widget is already included in the list of tabs. Add it, if it isn't already present
        otherwise update the tab.

        :param filename: A file path like object where the file displayed in the widget was loaded
        :param widget: A QWidget to either update or add to the tabbed structure
        :param model_str: The model text to be added to the widget object
        """
        # Add a tab to TabbedModelEditor for the C model if not already open
        file_path = Path(filename)
        if not self.isWidgetInTab(self.tabWidget, widget):
            self.addTab(file_path.suffix, file_path.name)
        elif self.tabWidget.tabText(self.tabWidget.indexOf(widget)) != file_path.name:
            # If title of tab is not what the filename is, update the tab title
            self.tabWidget.setTabText(self.tabWidget.indexOf(widget), file_path.name)

    def populateWidgetTextBox(self, widget: QtWidgets.QWidget, model_str: str):
        """Populate a widget text editor without emitting signals.

        **addTab() creates a fresh widget everytime it is called, so this cannot be combined with createOrUpdateTab()**

        :param widget: A QWidget to either update or add to the tabbed structure
        :param model_str: The model text to be added to the widget object
        """
        # Update the editor
        widget.blockSignals(True)
        widget.txtEditor.setPlainText(model_str)
        widget.blockSignals(False)

    def findFirstError(self, full_path: str | Path) -> int:
        """
        Run ast and model checks
        Attempt to return the line number of the error if any
        :param full_path: full path to the model file
        """
        try:
            with open(full_path, encoding="utf-8") as plugin:
                model_str = plugin.read()
            ast.parse(model_str)
            GuiUtils.checkModel(full_path)
            # If no errors occur, return early
            return -1

        except Exception as ex:
            msg = "Error building model: " + str(ex)
            logging.error(msg)
            # print four last lines of the stack trace
            # this will point out the exact line failing
            all_lines = traceback.format_exc().split("\n")
            last_lines = all_lines[-4:]
            traceback_to_show = "\n".join(last_lines)
            logging.error(traceback_to_show)

            # Set the status bar message
            # GuiUtils.Communicate.statusBarUpdateSignal.emit("Model check failed")
            self.parent.communicate.statusBarUpdateSignal.emit("Model check failed")

            # Find all QTextBrowser and QCodeEditor children
            text_browsers = self.tabWidget.currentWidget().findChildren(QtWidgets.QTextBrowser)
            code_editors = self.tabWidget.currentWidget().findChildren(QCodeEditor)

            # Combine the lists and apply the stylesheet
            for child in text_browsers + code_editors:
                child.setStyleSheet("border: 5px solid red")
                traceback_to_show = "\n".join(last_lines)
                child.setToolTip(traceback_to_show)

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
                        error_line = 0

        return error_line

    def updateFromEditor(self):
        """
        Save the current state of the Model Editor
        """
        clear_error_formatting = True # Assume we will clear error formating (if any) after saving
        w = self.tabWidget.currentWidget()
        filename = self.filename_py if w.is_python else self.filename_c
        # make sure we have the file handle ready
        if not filename:
            logging.error("No file name was provided for your plugin model. No file was written.")
            return

        # Retrieve model string
        model_str = self.getModel()['text']
        # Save the file
        self.writeFile(filename, model_str)

        # Get model filepath
        plugin_location = models.find_plugins_dir()
        full_path = Path(plugin_location) / filename

        error_line = self.findFirstError(full_path.with_suffix(".py"))
        if self.is_python and error_line >= 0:
            # select bad line
            cursor = QtGui.QTextCursor(w.txtEditor.document().findBlockByLineNumber(error_line-1))
            w.txtEditor.setTextCursor(cursor)

            # Ask the user if they want to save the file with errors or continue editing
            if not self.saveOverrideWarning(filename, model_str):
                # If the user decides to continue editing without saving, return
                return
            else:
                clear_error_formatting = False

        if clear_error_formatting:
            # change the frame colours back, if errors were fixed
            try:
                self.c_editor_widget.txtEditor.setStyleSheet("")
                self.c_editor_widget.txtEditor.setToolTip("")
            except AttributeError:
                pass
            self.editor_widget.txtEditor.setStyleSheet("")
            self.editor_widget.txtEditor.setToolTip("")

        # Update the tab title
        self.setTabEdited(False)

        # Notify listeners, since the plugin name might have changed
        self.parent.communicate.customModelDirectoryChanged.emit()

        if self.isWidgetInTab(self.tabWidget, self.plugin_widget):
            # Attempt to update the plugin widget with updated model information
            self.updateToPlugin(full_path)

        # notify the user
        msg = f"{str(filename)} successfully saved."
        self.parent.communicate.statusBarUpdateSignal.emit(msg)
        logging.info(msg)
        if self.is_documentation:
            self.regenerateDocumentation()

    def regenerateDocumentation(self):
        """
        Defer to subprocess the documentation regeneration process
        """
        # TODO: Move the doc regen methods out of the documentation window - this forces the window to remain open
        #  in order for the documentation regeneration process to run.
        # The regen method is part of the documentation window. If the window is closed, the method no longer exists.
        if hasattr(self.parent, "helpWindow"):
            self.parent.helpWindow.regenerateHtml(self.filename_py)

    def noModelCheckWarning(self):
        """
        Throw popup informing the user that no model checks will be run on a pure C model.
        Ask user to acknowledge and give option to not display again.
        """
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText("No model checks will be run on your C file until a python file of the same name is created in your plugin directory.")
        msgBox.setWindowTitle("No Python File Detected")
        doNotShowAgainCheckbox = QtWidgets.QCheckBox("Do not show again")
        msgBox.setCheckBox(doNotShowAgainCheckbox)

        msgBox.exec()

        if doNotShowAgainCheckbox.isChecked():
            # Update flag to not show popup again while this instance of TabbedModelEditor is open
            self.showNoCompileWarning = False

    def saveOverrideWarning(self, filename: str | Path, model_str: str):
        """
        Throw popup asking user if they want to save the model despite a bad model check.
        Save model if user chooses to save, and do nothing if the user chooses to continue editing.

        Returns True if user wanted to save file anyways, False if user wanted to continue editing without saving
        """
        msgBox = QtWidgets.QMessageBox(self)
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setText("Model check failed. Do you want to save the file anyways?")
        msgBox.setWindowTitle("Model Error")

        # Add buttons
        buttonContinue = msgBox.addButton("Continue editing", QtWidgets.QMessageBox.NoRole)
        buttonSave = msgBox.addButton("Save anyways", QtWidgets.QMessageBox.AcceptRole)
        # Set default button
        msgBox.setDefaultButton(buttonContinue)

        # Execute the message box and wait for the user's response
        msgBox.exec()

        # Check which button was clicked and execute the corresponding code
        if msgBox.clickedButton() == buttonSave:
            # Save files anyways
            py_file = os.path.splitext(filename)[0] + ".py"
            c_file = os.path.splitext(filename)[0] + ".c"
            py_tab_open = self.isWidgetInTab(self.tabWidget, self.editor_widget)
            c_tab_open = self.isWidgetInTab(self.tabWidget, self.c_editor_widget)

            # Check to see if we have a certain model type open, and if so, write models
            if py_tab_open:
                self.writeFile(py_file, self.editor_widget.getModel()["text"])
            if c_tab_open:
                self.writeFile(c_file, self.c_editor_widget.getModel()["text"])
            return True
        else:
            # Cancel button or Esc/Enter Keys pressed
            return False

    def canWriteModel(self, model: dict = None, full_path: str | Path = "") -> bool:
        """
        Determine if the current plugin can be written to file
        """
        assert isinstance(model, dict)
        assert full_path != ""

        # Make sure we can overwrite the file if it exists
        if os.path.isfile(full_path) and not model["overwrite"]:
            # notify the viewer
            msg = "Plugin with specified name already exists.\n"
            msg += "Please specify different filename or allow file overwrite."
            QtWidgets.QMessageBox.critical(self, "Plugin Error", msg)
            # Don't accept but return
            return False

        if model["filename"].casefold() in (
            built_in.casefold() for built_in in self.allBuiltinModels()
        ):
            # notify the viewer
            msg = "Built-in model with specified name already exists.\n"
            msg += "Please specify different filename."
            QtWidgets.QMessageBox.critical(self, "Plugin Error", msg)
            # Don't accept but return
            return False

        # Update model editor if plugin definition changed
        func_str = model["func_text"]
        form_vol_str = model["form_volume_text"]
        msg = self._checkForErrorsInModelStrs(func_str, form_vol_str)
        if msg:
            QtWidgets.QMessageBox.critical(self, "Plugin Error", msg)
            return False
        return True

    def _checkForErrorsInModelStrs(self, func_str: str, form_vol_str: str) -> str | None:
        """Helper method to check for errors and returns an error string, if necessary"""
        msg = None
        if func_str and "return" not in func_str:
            msg = "Error: The func(x) must 'return' a value at least.\n"
            msg += "For example: \n\nreturn 2*x"
        elif form_vol_str and "return" not in form_vol_str:
            msg = "Error: The form_volume() must 'return' a value at least.\n"
            msg += "For example: \n\nreturn 0.0"
        elif not func_str and not form_vol_str:
            msg = "Error: Function is not defined."
        return msg

    def onHelp(self):
        """
        Bring up the Model Editor Documentation whenever
        the HELP button is clicked.
        Calls Documentation Window with the path of the location within the
        documentation tree (after /doc/ ....".
        """
        location = "/user/qtgui/Perspectives/Fitting/plugin.html"
        self.parent.showHelp(location)

    def getModel(self):
        """
        Retrieves plugin model from the currently open tab
        """
        return self.tabWidget.currentWidget().getModel()

    def addTab(self, filetype: str, name: str):
        """
        Add a tab to the tab widget
        :param filetype: filetype of tab to add: "python" or "c"
        :param name: name to display on tab
        """
        if filetype in ["python", "py", ".py"]:
            self.editor_widget = ModelEditor(self, is_python=True)
            self.tabWidget.addTab(self.editor_widget, name)
            self.editor_widget.modelModified.connect(self.editorModelModified)
        elif filetype in ["c", ".c"]:
            self.c_editor_widget = ModelEditor(self, is_python=False)
            self.tabWidget.addTab(self.c_editor_widget, name)
            self.c_editor_widget.modelModified.connect(self.editorModelModified)

    def updateToPlugin(self, full_path: str | Path):
        """
        Update the plugin tab with new info from the model editor
        """
        self.model = self.getModel()
        model_text = self.model["text"]

        spec = importlib.util.spec_from_file_location("model", full_path) # Easier to import than use regex
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        description = module.description
        parameters = module.parameters
        iq_text = self.extractFunctionBody(model_text, "Iq")
        form_volume_text = self.extractFunctionBody(model_text, "form_volume")

        slim_param_list = []
        for param in parameters:
            if param[0]:
                # Extract parameter name, default value, and whether "volume" parameter
                slim_param_list.append([param[0], param[2], param[4]])

        # Send parameters in a list of lists format to listening widget
        self.plugin_widget.sendNewParamSignal.emit(slim_param_list)
        self.plugin_widget.sendNewDescriptionSignal.emit(description)
        self.plugin_widget.sendNewIqSignal.emit(iq_text)
        self.plugin_widget.sendNewFormVolumeSignal.emit(form_volume_text)

    @classmethod
    def isWidgetInTab(cls, tabWidget: QtWidgets.QTabWidget, widget_to_check: QtWidgets.QWidget) -> bool:
        """
        Check to see if a `widget_to_check` is a tab in the `tabWidget`
        """
        for i in range(tabWidget.count()):
            if tabWidget.widget(i) == widget_to_check:
                return True
        return False

    @classmethod
    def writeFile(cls, fname: str | Path, model_str: str = ""):
        """
        Write model content to file "fname"
        """
        with open(fname, "w", encoding="utf-8") as out_f:
            out_f.write(model_str)

    def generateCModel(self, model: dict, fname: str | Path) -> str:
        """
        Generate C model from the current plugin state
        :param model: plugin model
        :param fname: filename
        """

        model_text = C_COMMENT_TEMPLATE

        param_names = []
        pd_param_names = []
        param_str = self.strFromParamDict(model["parameters"])
        pd_param_str = self.strFromParamDict(model["pd_parameters"])
        for pname, _, _ in self.getParamHelper(param_str):
            param_names.append("double " + pname)
        for pd_pname, _, _ in self.getParamHelper(pd_param_str):
            pd_param_names.append("double " + pd_pname)

        # Format Python into comments to be put into I(Q) section
        iq_text: str = model["func_text"]
        iq_lines = iq_text.splitlines()
        commented_lines = ["//" + line for line in iq_lines]
        commented_iq_function = "\n    ".join(commented_lines)

        # Add polydisperse-dependent functions if polydisperse parameters are present
        if pd_param_names != []:
            model_text += C_PD_TEMPLATE.format(
                poly_args=", ".join(pd_param_names),
                poly_arg1=pd_param_names[0].split(" ")[1],
            )  # Remove 'double' from the first argument
        # Add all other function templates
        model_text += C_TEMPLATE.format(
            args=",\n".join(param_names), Iq=commented_iq_function
        )
        return model_text


    def generatePyModel(self, model: dict, fname: str | Path) -> str:
        """
        generate model from the current plugin state
        """

        def formatPythonFlags() -> str:
            """Get python flags for model and format into text"""
            checkbox_values = {
                'chkSingle': self.plugin_widget.chkSingle.isChecked(),
                'chkOpenCL': self.plugin_widget.chkOpenCL.isChecked(),
                'chkStructure': self.plugin_widget.chkStructure.isChecked(),
                'chkFQ': self.plugin_widget.chkFQ.isChecked(),
            }
            # Get the values of the checkboxes
            flag_string = FLAG_TEMPLATE.format(**checkbox_values)
            return flag_string

        name = model["filename"]
        if not name:
            model["filename"] = fname
            name = fname
        desc_str = model["description"]
        param_str = self.strFromParamDict(model["parameters"])
        pd_param_str = self.strFromParamDict(model["pd_parameters"])
        func_str = model["func_text"]
        form_vol_str = model["form_volume_text"]
        model_text = CUSTOM_TEMPLATE.format(name=name,
                                            title='User model for ' + name,
                                            description=desc_str,
                                            date=datetime.datetime.now().strftime('%Y-%m-%d'),
                                            flags=formatPythonFlags()
                                            )
        # Write out parameters
        param_names = []    # to store parameter names
        pd_params = []
        model_text += '#             ["name", "units", default, [lower, upper], "type", "description"],\n'
        model_text += 'parameters = [ \n'
        if self.plugin_widget.chkStructure.isChecked():
            # Structure factor models must have radius_effective and volfraction
            param_names.append('radius_effective')
            param_names.append('volfraction')
            model_text += "              ['radius_effective', '', 1, [0.0, inf], 'volume', ''],\n"
            model_text += "              ['volfraction', '', 1, [0.0, 1.0], '', ''],\n"
        for pname, pvalue, desc in self.getParamHelper(param_str):
            param_names.append(pname)
            model_text += "              ['%s', '', %s, [-inf, inf], '', '%s'],\n" % (pname, pvalue, desc)
        if pd_param_str:
            for pname, pvalue, desc in self.getParamHelper(pd_param_str):
                param_names.append(pname)
                pd_params.append(pname)
                model_text += "              ['%s', '', %s, [-inf, inf], 'volume', '%s'],\n" % (pname, pvalue, desc)
        model_text += '             ]\n\n'

        # If creating a C model, link it to the Python file

        if model["gen_c"]:
            model_text += LINK_C_MODEL_TEMPLATE.format(c_model_name=name + ".c")
            model_text += "\n\n"

        # Write out function definition
        model_text += "def Iq(%s):\n" % ", ".join(["q"] + param_names)
        model_text += '    """Absolute scattering"""\n'
        if "scipy." in func_str:
            model_text += "    import scipy\n"
        if "numpy." in func_str:
            model_text += "    import numpy\n"
        if "np." in func_str:
            model_text += "    import numpy as np\n"
        for func_line in func_str.split("\n"):
            model_text += "%s%s\n" % ("    ", func_line)
        model_text += "\n## uncomment the following if Iq works for vector x\n"
        model_text += "#Iq.vectorized = True\n"

        # Add parameters to ER functions and include placeholder functions
        model_text += "\n"
        model_text += ER_TEMPLATE + "\n"
        model_text += ER_C_TEMPLATE if model['gen_c'] else ER_PY_TEMPLATE.format(args=", ".join(param_names))
        model_text += "\n"

        # If polydisperse, create place holders for form_volume
        if pd_params and self.include_polydisperse:
            model_text += "\n"
            model_text += CUSTOM_TEMPLATE_PD_FORM.format(args=", ".join(pd_params))
            for func_line in form_vol_str.split("\n"):
                model_text += "%s%s\n" % ("    ", func_line)
            model_text += CUSTOM_TEMPLATE_PD_SHELL.format(args=", ".join(pd_params))
            for func_line in form_vol_str.split("\n"):
                model_text += "%s%s\n" % ("#    ", func_line)

        # Create place holder for Iqxy
        model_text +="\n"
        model_text +='#def Iqxy(%s):\n' % ', '.join(["x", "y"] + param_names)
        model_text +='#    """Absolute scattering of oriented particles."""\n'
        model_text +='#    ...\n'
        model_text +='#    return oriented_form(x, y, args)\n'
        model_text +='## uncomment the following if Iqxy works for vector x, y\n'
        model_text +='#Iqxy.vectorized = True\n'
        model_text += "\n"

        return model_text

    @classmethod
    def getParamHelper(cls, param_str: str) -> []:
        """
        yield a sequence of name, value pairs for the parameters in param_str

        Parameters can be defined by one per line by name=value, or multiple
        on the same line by separating the pairs by semicolon or comma.  The
        value is optional and defaults to "1.0".
        """
        for line in param_str.replace(";", ",").split("\n"):
            for item in line.split(","):
                defn, desc = item.split("#", 1) if "#" in item else (item, "")
                name, value = defn.split("=", 1) if "=" in defn else (defn, "1.0")
                if name:
                    yield [v.strip() for v in (name, value, desc)]

    @classmethod
    def strFromParamDict(cls, param_dict: dict) -> str:
        """
        Creates string from parameter dictionary

        Example::

            {
                0: ('variable','value'),
                1: ('variable','value'),
                ...
            }
        """
        param_str = ""
        for _, params in param_dict.items():
            if not params[0]:
                continue
            value = 1
            if params[1]:
                try:
                    value = float(params[1])
                except ValueError:
                    # convert to default
                    value = 1
            param_str += params[0] + " = " + str(value) + "\n"
        return param_str

    @classmethod
    def extractFunctionBody(cls, source_code: str, function_name: str) -> str:
        """
        Extract the body of a function from a model file
        """
        tree = ast.parse(source_code)
        extractor = cls.FunctionBodyExtractor(function_name)
        extractor.visit(tree)
        return extractor.function_body_source

    class FunctionBodyExtractor(ast.NodeVisitor):
        """
        Class to extract the body of a function from a model file
        """

        def __init__(self, function_name):
            self.function_name = function_name
            self.function_body_source = None

        def visit_FunctionDef(self, node):
            """
            Extract the source code of the function with the given name.
            NOTE: Do NOT change the name of this method-- visit_ is a prefix that ast.NodeVisitor uses
            """
            if node.name == self.function_name:
                body = node.body
                # Check if the first statement is an Expr node containing a constant (docstring)
                if self._check_for_docstring(body):
                    body = body[1:]  # Exclude the docstring
                self.function_body_source = ast.unparse(body)
            # Continue traversing to find nested functions or other function definitions
            self.generic_visit(node)

        def _check_for_docstring(self, body: ast.AST) -> bool:
            """A quick check to see if an ast node has a doc string."""
            if body:
                return isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
            return False



CUSTOM_TEMPLATE = '''\
r"""
Definition
----------

Calculates {name}.

{description}

References
----------

Authorship and Verification
---------------------------

* **Author:** --- **Date:** {date}
* **Last Modified by:** --- **Date:** {date}
* **Last Reviewed by:** --- **Date:** {date}
"""

from sasmodels.special import *
from numpy import inf

name = "{name}"
title = "{title}"
description = """{description}"""
{flags}
'''

ER_TEMPLATE = '''\
# NOTE: If you want to couple this model with structure factors (S(Q)),
# please uncomment this section. This function will need to return a
# meaningful value to enable full structure factor compatibility.
'''

ER_C_TEMPLATE = '''\
# This is a list of the modes in which the effective radius can be
# applied. The list allows arbitrary values, but the index of the mode
# will be passed to the calculation, not the text. Ensure that the
# radius_effective method in the C file returns the correct value
# based on the index. The values are used by the GUI to allow the
# user to choose which method they wish to apply.

#radius_effective_modes = ["equivalent volume sphere", "radius",
#                           "half length", "half total length",]
'''

ER_PY_TEMPLATE = '''\
# def ER({args}):
#    """
#    Effective radius of particles to be used when computing structure
#    factors. Input parameters are vectors ranging over the mesh of
#    polydispersity values.
#    """
#     return 0.0
'''

CUSTOM_TEMPLATE_PD_FORM = '''\
def form_volume({args}):
    """
    Volume of the TOTAL particle shape including all "shells" and
    hollow portions (e.g. a hollow sphere like a vesicle). This is
    used to compute absolute scattering intensity, to weight
    polydisperse parameter contributions and when multiplying by
    a structure factor. Note that for hollow particles you will
    ALSO need to define a shell volume.
    """
'''

CUSTOM_TEMPLATE_PD_SHELL = '''\

# uncomment this function if it is needed
#def shell_volume({args}):
    """
    Uncomment this function if you want the vol fraction (scale)
    parameter to represent the volume of the "shell" only. For example
    for a vesicle the volume fraction of lipid is entirely in the
    shell surrounding the hollow interior. The form_volume will still
    be required when multiplying by a structure factor.
    """
'''

FLAG_TEMPLATE = """
\n# Optional flags (can be removed). Read documentation by pressing
# 'Help' for more information.\n
# single = True indicates that the model can be run using single
# precision floating point values.
# Defaults to True.
single = {chkSingle}\n\n
# opencl = False indicates that the model should not be run using
# OpenCL. Defaults to False.
opencl = {chkOpenCL}\n\n
# structure_factor = False indicates that the model is a form factor.
# Set to true if this model is a structure factor (from the
# interactions between particles). Defaults to False.
structure_factor = {chkStructure}\n\n
# have_fq = False indicates that the model does not define the
# amplitude factor, F(Q), calculation in the linked C model. Note that
# F(Q) is currently only available for C models (defined in the C file)
# and is currently only used (and is in fact required) for the beta
# approximation calculation. Defaults to False.
have_fq = {chkFQ}\n"""

SUM_TEMPLATE = """
from sasmodels.core import load_model_info
from sasmodels.sasview_model import make_model_from_info

model_info = load_model_info('{model1}{operator}{model2}')
model_info.name = '{name}'{desc_line}
Model = make_model_from_info(model_info)
"""

LINK_C_MODEL_TEMPLATE = """\
# To Enable C model, uncomment the line defining `source` and delete
# the I(Q) function in this Python model after converting your code
# to C. you should also include any c library files your C code
# will be using. eg: source = ['lib/sas_3j1x_x.c', 'my_model.c']
#
# Note: removing or commenting the "source = []" line will unlink the
# C model from the Python model, which means the C model will not be
# checked for errors when edited.

# source = ['{c_model_name}']
"""

C_COMMENT_TEMPLATE = """\
// :::Custom C model template:::
// This is a template for a custom C model.
// C Models are used for a variety of reasons in SasView, including
//   better performance and the ability to perform calculations not
//   possible in Python. For example, all oriented and magnetic models,
//   as well as most models using structure factor calculations, are
//   written in C.
// HOW TO USE THIS TEMPLATE:
// 1. Determine which functions you will need to perform your calculations;
//    delete unused functions.
//   1.1 Note that you must define at least one of Iq, Fq, Iqac, or Iqabc:
//     Iq or Fq for 1D calculation (i.e. if your model does not use
//       orientation parameters. NOTE: Fq is highly recommended and
//       ALWAYS preferred if possible. It is required if your model
//       will be used with the beta approximation when multiplying by a
//       structure factor.
//     Iqac or Iqabc if your model uses orientation parameters/is
//       magnetic. Iqac is for particles with an axis of symmetry such
//       as a cylinder or ellipsoid of revolution. Iqabc is required
//       for particles with no symmetry such as a parallelipiped.
// 2. Write C code independently of this editor and paste it into the
//    appropriate functions.
//    2.1 Note that the C editor does not support C syntax checking, so
//        be aware if writing C code directly into the SasView editor.
// 3. Ensure a python file links to your C model (source = ['filename.c'])
// 4. Press 'Apply' or 'Save' to save your model and run a model check
//      (note that the model check will fail if there is no python file
//      of the same name in your plugins directory)
//
// NOTE: SasView has many built-in functions that you can use in your C
//       model. For example, spherical Bessel functions
//       (lib/sas_3j1x_x.c), Gaussian, quadrature (lib/sas_J1.c), and
//       more. To include, add their filename to the `source = []`
//       list in the python file linking to your C model.
// NOTE: It also has many common constants following the C99 standard,
//       such as M_PI, M_SQRT1_2, and M_E. Check documentation for
//       a full list.

"""

C_PD_TEMPLATE = """\
static double
form_volume({poly_args}) // Remove arguments as needed
{{
// Volume of the TOTAL particle shape including all "shells" and
// hollow portions (e.g. a hollow sphere like a vesicle). This is
// used to compute absolute scattering intensity, to weight
// polydisperse parameter contributions and when multiplying by
// a structure factor. Note that for hollow particles you will
// ALSO need to define a shell volume.
// IMPORTANT: Make sure to delete the corresponding function in the
// python file
    return M_4PI_3 * {poly_arg1} * {poly_arg1} * {poly_arg1};
}}

// Uncomment this function if you want the vol fraction (scale)
// parameter to represent the volume of the "shell" only. For example
// for a vesicle the volume fraction of lipid is entirely in the
// shell surrounding the hollow interior.
// IMPORTANT: Make sure to delete the corresponding function in the
// python file
//static double
//shell_volume({poly_args}) // Remove arguments as needed
//{{
//    return M_4PI_3 * {poly_arg1} * {poly_arg1} * {poly_arg1};
//}}

"""

C_TEMPLATE = """\
// uncomment this and provide appropriate functions for the effective
// radius to be used IF this is to be used with structure factors.
//static double
//radius_effective(int mode) // Add arguments as needed
//{{
//    switch (mode) {{
//    default:
//    case 1:
//    // Define effective radius calculations here...
//    return 0.0;
//    }}
//}}

static void
Fq(double q,
   double *F1,
   double *F2,
   {args}) // Remove arguments as needed
{{
    // Define F(Q) calculations here...
    //IMPORTANT: You should NOT define Iq if your model uses Fq. This
    //    is the preferred approach even if you do not want to use the
    //    beta approximation. the *F2 value is F(Q)^2 and equivalent to
    //    the output of Iq. While currently F(Q) is only used in the
    //    beta approximation, it may be used for other things in the
    //    future. You must still define Iqac or Iqabc if your model has
    //    orientation  parameters (i.e. fits data in 2D plots).
    // TO USE: Convert your copied Python code to C below and uncomment
    // it. Note that F2 is essentially F1^2.
    //IMPORTANT: Ensure that you delete the I(Q) function in the
    //    corresponding Python file.

    *F1 = 0.0;
    *F2 = 0.0;
}}

static double
Iq(double q,
   {args}) // Remove arguments as needed
{{
    // Define I(Q) calculations here for 1D models (i.e. independent
    // of shape orientation) that cannot be expressed by F(Q).
    // TO USE: Convert your copied Python code to C below and
    //         uncomment it
    //IMPORTANT: DO NOT define both an I(Q) and and F(Q)
    //IMPORTANT: Ensure that you delete the I(Q) function in the
    //           corresponding Python file.

    {Iq}
    return 1.0;
}}

static double
Iqac(double qab,
     double qc,
     {args}) // Remove arguments as needed
{{
    // Define I(Q) calculations here for models dependent on shape
    // orientation (i.e. models that compute (Qx, Qy)) in
    // which the shape is rotationally symmetric about *c* axis.
    // Note: *psi* angle not needed for shapes symmetric about *c* axis
    // IMPORTANT: Only define ONE calculation for 2D I(Q): either
    //            Iqac or Iqabc.  Remove the other.
    // IMPORTANT: Make sure to remove or comment out any Iqxy in the
    //            python file
    return 1.0;
}}

static double
Iqabc(double qa,
      double qb,
      double qc,
      {args}) // Remove arguments as needed
{{
    // Define I(Q) calculations here for models dependent on shape
    //orientation in  all three axes.
    // IMPORTANT: Only define ONE calculation for 2D I(Q): either
    //            Iqac or Iqabc.  Remove the other.
    // IMPORTANT: Make sure to remove or comment out any Iqxy in the
    //            python file
    return 1.0;
}}

static double
Iqxy(double qx,
     double qy,
     {args}) // Remove arguments as needed
{{
    // WARNING: The use of Iqxy is highly discouraged; Use Iqabc or
    //    Iqac instead for their better orientational averaging. See
    //    documentation for details.
    //    NOTE: This is only supported for backward compatibility
    // IMPORTANT: Only define ONE calculation for 2D I(Q): either
    //            Iqac or Iqabc or Ixy.  Remove the others.
    // IMPORTANT: Make sure to remove or comment out any Iqxy in the
    //            python file

    return 1.0;
}}
"""
