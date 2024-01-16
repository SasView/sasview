# global
import sys
import os
import re
import ast
import datetime
import logging
import traceback

from PySide6 import QtWidgets, QtCore, QtGui
from pathlib import Path

from sas.sascalc.fit import models
from sas.sascalc.fit.models import find_plugins_dir

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.UI.TabbedModelEditor import Ui_TabbedModelEditor
from sas.qtgui.Utilities.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.ModelEditor import ModelEditor

class TabbedModelEditor(QtWidgets.QDialog, Ui_TabbedModelEditor):
    """
    Model editor "container" class describing interaction between
    plugin definition widget and model editor widget.
    Once the model is defined, it can be saved as a plugin.
    """
    # Signals for intertab communication plugin -> editor
    def __init__(self, parent=None, edit_only=False, model=False, load_file=None):
        super(TabbedModelEditor, self).__init__(parent._parent)

        self.parent = parent

        self.setupUi(self)

        # globals
        self.filename = ""
        self.is_python = True
        self.window_title = self.windowTitle()
        self.edit_only = edit_only
        self.load_file = load_file.lstrip("//") if load_file else None
        self.model = model
        self.is_modified = False
        self.label = None
        self.file_to_regenerate = ""

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
        # Initially, nothing in the editor
        self.editor_widget.setEnabled(False)
        self.tabWidget.addTab(self.editor_widget, "Model editor")
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)

        if self.edit_only:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setText("Save")
            # Hide signals from the plugin widget
            self.plugin_widget.blockSignals(True)
            # and hide the tab/widget itself
            self.tabWidget.removeTab(0)
        
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
        self.plugin_widget.txtName.editingFinished.connect(self.pluginTitleSet)

    def setPluginActive(self, is_active=True):
        """
        Enablement control for all the controls on the simple plugin editor
        """
        self.plugin_widget.setEnabled(is_active)

    def saveClose(self):
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

    def closeEvent(self, event):
        """
        Overwrite the close even to assure intent
        """
        if self.is_modified:
            saveCancelled = self.saveClose()
            if saveCancelled:
                return
        event.accept()

    def onLoad(self, at_launch=False):
        """
        Loads a model plugin file. at_launch is value of whether to attempt a load of a file from launch of the widget or not
        """
        self.is_python = True # By default assume the file you load is python

        if self.is_modified:
            saveCancelled = self.saveClose()
            if saveCancelled:
                return
            self.is_modified = False

        # If we are loading in a file at the launch of the editor instead of letting the user pick, we need to process the HTML location from
        # the documentation viewer into the filepath for its corresponding RST
        if at_launch:
            from sas.sascalc.doc_regen.makedocumentation import MAIN_DOC_SRC
            user_models = find_plugins_dir()
            user_model_name = user_models + self.load_file + ".py"

            if self.model is True:
                # Find location of model .py files and load from that location
                if os.path.isfile(user_model_name):
                    filename = user_model_name
                else:
                    filename = MAIN_DOC_SRC / "user" / "models" / "src" / self.load_file + ".py"
            else:
                filename = MAIN_DOC_SRC / self.load_file.replace(".html", ".rst")
                self.is_python = False
        else:
            plugin_location = models.find_plugins_dir()
            filename = QtWidgets.QFileDialog.getOpenFileName(
                                            self,
                                            'Open Plugin',
                                            plugin_location,
                                            'SasView Plugin Model (*.py)',
                                            None,
                                            QtWidgets.QFileDialog.DontUseNativeDialog)[0]

        # Load the file
        if not filename:
            logging.info("No data file chosen.")
            return

        # remove c-plugin tab, if present.
        if self.tabWidget.count()>1:
            self.tabWidget.removeTab(1)
        self.file_to_regenerate = filename
        self.loadFile(str(filename))

    def loadFile(self, filename):
        """
        Performs the load operation and updates the view
        """
        self.editor_widget.blockSignals(True)
        plugin_text = ""
        with open(filename, 'r', encoding="utf-8") as plugin:
            plugin_text = plugin.read()
            self.editor_widget.txtEditor.setPlainText(plugin_text)
        self.editor_widget.setEnabled(True)
        self.editor_widget.blockSignals(False)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
        self.filename = Path(filename)
        display_name = self.filename.stem
        if not self.model:
            self.setWindowTitle(self.window_title + " - " + display_name)
        else:
            self.setWindowTitle("Documentation Editor" + " - " + display_name)
        # Name the tab with .py filename
        self.tabWidget.setTabText(0, display_name)

        # Check the validity of loaded model if the model is python
        if self.is_python is True:
            error_line = self.checkModel(plugin_text)
            if error_line > 0:
                # select bad line
                cursor = QtGui.QTextCursor(self.editor_widget.txtEditor.document().findBlockByLineNumber(error_line-1))
                self.editor_widget.txtEditor.setTextCursor(cursor)
                return

        # In case previous model was incorrect, change the frame colours back
        self.editor_widget.txtEditor.setStyleSheet("")
        self.editor_widget.txtEditor.setToolTip("")

        # See if there is filename.c present
        c_path = Path(str(self.filename.parent) + self.filename.name.replace(".py", ".c"))
        if not c_path.exists() or ".rst" in c_path.name: return
        # add a tab with the same highlighting
        c_display_name = c_path.name
        self.c_editor_widget = ModelEditor(self, is_python=False)
        self.tabWidget.addTab(self.c_editor_widget, c_display_name)
        # Read in the file and set in on the widget
        with open(c_path, 'r', encoding="utf-8") as plugin:
            self.c_editor_widget.txtEditor.setPlainText(plugin.read())
        self.c_editor_widget.modelModified.connect(self.editorModelModified)

    def onModifiedExit(self):
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
        if self.is_modified:
            saveCancelled = self.saveClose()
            if saveCancelled:
                return
        self.reject()

    def onApply(self):
        """
        Write the plugin and update the model editor if plugin editor open
        Write/overwrite the plugin if model editor open
        """
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

    def pluginTitleSet(self):
        """
        User modified the model name.
        Display the model name in the window title
        and allow for model save.
        """
        # Ensure plugin name is non-empty
        model = self.getModel()
        if 'filename' in model and model['filename']:
            self.setWindowTitle(self.window_title + " - " + model['filename'])
            self.setTabEdited(True)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
            self.is_modified = True
        else:
            # the model name is empty - disable Apply and clear the editor
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
            self.editor_widget.blockSignals(True)
            self.editor_widget.txtEditor.setPlainText('')
            self.editor_widget.blockSignals(False)
            self.editor_widget.setEnabled(False)

    def setTabEdited(self, is_edited):
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
        """
        Write the plugin and update the model editor
        """
        # get current model
        model = self.getModel()
        if 'filename' not in model: return

        # get required filename
        filename = model['filename']

        # check if file exists
        plugin_location = models.find_plugins_dir()
        full_path = os.path.join(plugin_location, filename)
        if os.path.splitext(full_path)[1] != ".py":
            full_path += ".py"

        # Update the global path definition
        self.filename = full_path

        if not self.canWriteModel(model, full_path):
            return

        # generate the model representation as string
        model_str = self.generateModel(model, full_path)
        self.writeFile(full_path, model_str)

        # disable "Apply"
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)

        # Run the model test in sasmodels
        if not self.isModelCorrect(full_path):
            return

        self.editor_widget.setEnabled(True)

        # Update the editor here.
        # Simple string forced into control.
        self.editor_widget.blockSignals(True)
        self.editor_widget.txtEditor.setPlainText(model_str)
        self.editor_widget.blockSignals(False)

        # Set the widget title
        self.setTabEdited(False)

        # Notify listeners
        self.parent.communicate.customModelDirectoryChanged.emit()

        # Notify the user
        msg = "Custom model "+filename + " successfully created."
        self.parent.communicate.statusBarUpdateSignal.emit(msg)
        logging.info(msg)

    def checkModel(self, model_str):
        """
        Run the ast check
        and return True if the model is good.
        False otherwise.
        """
        # successfulCheck = True
        error_line = 0
        try:
            ast.parse(model_str)

        except SyntaxError as ex:
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
            # Put a thick, red border around the mini-editor
            self.tabWidget.currentWidget().txtEditor.setStyleSheet("border: 5px solid red")
            # last_lines = traceback.format_exc().split('\n')[-4:]
            traceback_to_show = '\n'.join(last_lines)
            self.tabWidget.currentWidget().txtEditor.setToolTip(traceback_to_show)
            # attempt to find the failing command line number, usually the last line with
            # `File ... line` syntax
            for line in reversed(all_lines):
                if 'File' in line and 'line' in line:
                    error_line = re.split('line ', line)[1]
                    try:
                        error_line = int(error_line)
                        break
                    except ValueError:
                        error_line = 0
        return error_line

    def isModelCorrect(self, full_path):
        """
        Run the sasmodels method for model check
        and return True if the model is good.
        False otherwise.
        """
        successfulCheck = True
        try:
            model_results = GuiUtils.checkModel(full_path)
            logging.info(model_results)
        # We can't guarantee the type of the exception coming from
        # Sasmodels, so need the overreaching general Exception
        except Exception as ex:
            msg = "Error building model: "+ str(ex)
            logging.error(msg)
            #print three last lines of the stack trace
            # this will point out the exact line failing
            last_lines = traceback.format_exc().split('\n')[-4:]
            traceback_to_show = '\n'.join(last_lines)
            logging.error(traceback_to_show)

            # Set the status bar message
            self.parent.communicate.statusBarUpdateSignal.emit("Model check failed")

            # Remove the file so it is not being loaded on refresh
            os.remove(full_path)
            # Put a thick, red border around the mini-editor
            self.plugin_widget.txtFunction.setStyleSheet("border: 5px solid red")
            # Use the last line of the traceback for the tooltip
            last_lines = traceback.format_exc().split('\n')[-2:]
            traceback_to_show = '\n'.join(last_lines)
            self.plugin_widget.txtFunction.setToolTip(traceback_to_show)
            successfulCheck = False
        return successfulCheck

    def updateFromEditor(self):
        """
        Save the current state of the Model Editor
        """
        filename = self.filename
        w = self.tabWidget.currentWidget()
        if not w.is_python:
            base, _ = os.path.splitext(filename)
            filename = base + '.c'

        # make sure we have the file handle ready
        assert(filename != "")
        # Retrieve model string
        model_str = self.getModel()['text']
        if w.is_python and self.is_python:
            error_line = self.checkModel(model_str)
            if error_line > 0:
                # select bad line
                cursor = QtGui.QTextCursor(w.txtEditor.document().findBlockByLineNumber(error_line-1))
                w.txtEditor.setTextCursor(cursor)
                return

        # change the frame colours back
        w.txtEditor.setStyleSheet("")
        w.txtEditor.setToolTip("")
        # Save the file
        self.writeFile(filename, model_str)
        # Update the tab title
        self.setTabEdited(False)

        # Notify listeners, since the plugin name might have changed
        self.parent.communicate.customModelDirectoryChanged.emit()

        # notify the user
        msg = str(filename) + " successfully saved."
        self.parent.communicate.statusBarUpdateSignal.emit(msg)
        logging.info(msg)
        self.regenerateDocumentation()
    
    def regenerateDocumentation(self):
        """
        Defer to subprocess the documentation regeneration process
        """
        if self.parent.helpWindow:
            self.parent.helpWindow.regenerateHtml(self.filename)

    def canWriteModel(self, model=None, full_path=""):
        """
        Determine if the current plugin can be written to file
        """
        assert(isinstance(model, dict))
        assert(full_path!="")

        # Make sure we can overwrite the file if it exists
        if os.path.isfile(full_path):
            # can we overwrite it?
            if not model['overwrite']:
                # notify the viewer
                msg = "Plugin with specified name already exists.\n"
                msg += "Please specify different filename or allow file overwrite."
                QtWidgets.QMessageBox.critical(self, "Plugin Error", msg)
                # Don't accept but return
                return False
        # Update model editor if plugin definition changed
        func_str = model['text']
        msg = None
        if func_str:
            if 'return' not in func_str:
                msg = "Error: The func(x) must 'return' a value at least.\n"
                msg += "For example: \n\nreturn 2*x"
        else:
            msg = 'Error: Function is not defined.'
        if msg is not None:
            QtWidgets.QMessageBox.critical(self, "Plugin Error", msg)
            return False
        return True

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

    @classmethod
    def writeFile(cls, fname, model_str=""):
        """
        Write model content to file "fname"
        """
        with open(fname, 'w', encoding="utf-8") as out_f:
            out_f.write(model_str)

    def generateModel(self, model, fname):
        """
        generate model from the current plugin state
        """
        name = model['filename']
        if not name:
            model['filename'] = fname
            name = fname
        desc_str = model['description']
        param_str = self.strFromParamDict(model['parameters'])
        pd_param_str = self.strFromParamDict(model['pd_parameters'])
        func_str = model['text']
        model_text = CUSTOM_TEMPLATE % {
            'name': name,
            'title': 'User model for ' + name,
            'description': desc_str,
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
        }

        # Write out parameters
        param_names = []    # to store parameter names
        pd_params = []
        model_text += 'parameters = [ \n'
        model_text += '#   ["name", "units", default, [lower, upper], "type", "description"],\n'
        if param_str:
            for pname, pvalue, desc in self.getParamHelper(param_str):
                param_names.append(pname)
                model_text += "    ['%s', '', %s, [-inf, inf], '', '%s'],\n" % (pname, pvalue, desc)
        if pd_param_str:
            for pname, pvalue, desc in self.getParamHelper(pd_param_str):
                param_names.append(pname)
                pd_params.append(pname)
                model_text += "    ['%s', '', %s, [-inf, inf], 'volume', '%s'],\n" % (pname, pvalue, desc)
        model_text += '    ]\n'

        # Write out function definition
        model_text += 'def Iq(%s):\n' % ', '.join(['x'] + param_names)
        model_text += '    """Absolute scattering"""\n'
        if "scipy." in func_str:
            model_text +="    import scipy\n"
        if "numpy." in func_str:
            model_text +="    import numpy\n"
        if "np." in func_str:
            model_text +="    import numpy as np\n"
        for func_line in func_str.split('\n'):
                model_text +='%s%s\n' % ("    ", func_line)
        model_text +='## uncomment the following if Iq works for vector x\n'
        model_text +='#Iq.vectorized = True\n'

        # If polydisperse, create place holders for form_volume, ER and VR
        if pd_params:
            model_text +="\n"
            model_text +=CUSTOM_TEMPLATE_PD % {'args': ', '.join(pd_params)}

        # Create place holder for Iqxy
        model_text +="\n"
        model_text +='#def Iqxy(%s):\n' % ', '.join(["x", "y"] + param_names)
        model_text +='#    """Absolute scattering of oriented particles."""\n'
        model_text +='#    ...\n'
        model_text +='#    return oriented_form(x, y, args)\n'
        model_text +='## uncomment the following if Iqxy works for vector x, y\n'
        model_text +='#Iqxy.vectorized = True\n'

        return model_text

    @classmethod
    def getParamHelper(cls, param_str):
        """
        yield a sequence of name, value pairs for the parameters in param_str

        Parameters can be defined by one per line by name=value, or multiple
        on the same line by separating the pairs by semicolon or comma.  The
        value is optional and defaults to "1.0".
        """
        for line in param_str.replace(';', ',').split('\n'):
            for item in line.split(','):
                defn, desc = item.split('#', 1) if '#' in item else (item, '')
                name, value = defn.split('=', 1) if '=' in defn else (defn, '1.0')
                if name:
                    yield [v.strip() for v in (name, value, desc)]

    @classmethod
    def strFromParamDict(cls, param_dict):
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
            if not params[0]: continue
            value = 1
            if params[1]:
                try:
                    value = float(params[1])
                except ValueError:
                    # convert to default
                    value = 1
            param_str += params[0] + " = " + str(value) + "\n"
        return param_str


CUSTOM_TEMPLATE = '''\
r"""
Definition
----------

Calculates %(name)s.

%(description)s

References
----------

Authorship and Verification
---------------------------

* **Author:** --- **Date:** %(date)s
* **Last Modified by:** --- **Date:** %(date)s
* **Last Reviewed by:** --- **Date:** %(date)s
"""

from sasmodels.special import *
from numpy import inf

name = "%(name)s"
title = "%(title)s"
description = """%(description)s"""

'''

CUSTOM_TEMPLATE_PD = '''\
def form_volume(%(args)s):
    """
    Volume of the particles used to compute absolute scattering intensity
    and to weight polydisperse parameter contributions.
    """
    return 0.0

def ER(%(args)s):
    """
    Effective radius of particles to be used when computing structure factors.

    Input parameters are vectors ranging over the mesh of polydispersity values.
    """
    return 0.0

def VR(%(args)s):
    """
    Volume ratio of particles to be used when computing structure factors.

    Input parameters are vectors ranging over the mesh of polydispersity values.
    """
    return 1.0
'''

SUM_TEMPLATE = """
from sasmodels.core import load_model_info
from sasmodels.sasview_model import make_model_from_info

model_info = load_model_info('{model1}{operator}{model2}')
model_info.name = '{name}'{desc_line}
Model = make_model_from_info(model_info)
"""

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    sheet = TabbedModelEditor()
    sheet.show()
    app.exec_()
    
