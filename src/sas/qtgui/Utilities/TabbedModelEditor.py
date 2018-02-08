# global
import sys
import os
import types
import datetime
import numpy as np
import webbrowser
import logging

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.sascalc.fit import models

from sas.qtgui.Utilities.UI.TabbedModelEditor import Ui_TabbedModelEditor
from sas.qtgui.Utilities.PluginDefinition import PluginDefinition
from sas.qtgui.Utilities.ModelEditor import ModelEditor
import sas.qtgui.Utilities.GuiUtils as GuiUtils

class TabbedModelEditor(QtWidgets.QDialog, Ui_TabbedModelEditor):
    """
    Model editor "container" class describing interaction between
    plugin definition widget and model editor widget.
    Once the model is defined, it can be saved as a plugin.
    """
    # Signals for intertab communication plugin -> editor
    def __init__(self, parent=None, edit_only=False):
        super(TabbedModelEditor, self).__init__()

        self.parent = parent

        self.setupUi(self)

        # globals
        self.filename = ""
        self.window_title = self.windowTitle()
        self.edit_only = edit_only
        self.is_modified = False

        self.addWidgets()

        self.addSignals()

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
        self.editor_widget.modelModified.connect(self.editorModelModified)
        self.plugin_widget.modelModified.connect(self.pluginModelModified)

    def setPluginActive(self, is_active=True):
        """
        Enablement control for all the controls on the simple plugin editor
        """
        self.plugin_widget.setEnabled(is_active)

    def closeEvent(self, event):
        """
        Overwrite the close even to assure intent
        """
        if self.is_modified:
            ret = self.onModifiedExit()
            if ret == QtWidgets.QMessageBox.Cancel:
                return
            elif ret == QtWidgets.QMessageBox.Save:
                self.updateFromEditor()
        event.accept()

    def onLoad(self):
        """
        Loads a model plugin file
        """
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

        self.loadFile(filename)

    def loadFile(self, filename):
        """
        Performs the load operation and updates the view
        """
        self.editor_widget.blockSignals(True)
        with open(filename, 'r') as plugin:
            self.editor_widget.txtEditor.setPlainText(plugin.read())
        self.editor_widget.setEnabled(True)
        self.editor_widget.blockSignals(False)
        self.filename, _ = os.path.splitext(os.path.basename(filename))

        self.setWindowTitle(self.window_title + " - " + self.filename)

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
            ret = self.onModifiedExit()
            if ret == QtWidgets.QMessageBox.Cancel:
                return
            elif ret == QtWidgets.QMessageBox.Save:
                self.updateFromEditor()
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
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
        self.is_modified = True

    def pluginModelModified(self):
        """
        User modified the model in the Plugin Editor.
        Show that the model is changed.
        """
        # Ensure plugin name is non-empty
        model = self.getModel()
        if 'filename' in model and model['filename']:
            self.setWindowTitle(self.window_title + " - " + model['filename'])
            self.setTabEdited(True)
            # Enable editor
            self.editor_widget.setEnabled(True)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(True)
            self.is_modified = True
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)

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
        # TODO:
        # Temporarily disable model check -
        # unittest.suite() gives weird results in qt5.
        # needs investigating
        #try:
        #    _, msg = self.checkModel(full_path), None
        #except Exception as ex:
        #    result, msg = None, "Error building model: "+ str(ex)

        # Update the editor here.
        # Simple string forced into control.
        self.editor_widget.blockSignals(True)
        self.editor_widget.txtEditor.setPlainText(model_str)
        self.editor_widget.blockSignals(False)

        # Set the widget title
        self.setTabEdited(False)

        # Notify listeners
        self.parent.communicate.customModelDirectoryChanged.emit()

    def updateFromEditor(self):
        """
        Save the current state of the Model Editor
        """
        # make sure we have the file handly ready
        assert(self.filename != "")
        # Retrieve model string
        model_str = self.getModel()['text']
        # Save the file
        self.writeFile(self.filename, model_str)
        # Update the tab title
        self.setTabEdited(False)
        
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
        location = "/user/sasgui/perspectives/fitting/plugin.html"
        self.parent.showHelp(location)

    def getModel(self):
        """
        Retrieves plugin model from the currently open tab
        """
        return self.tabWidget.currentWidget().getModel()

    def writeFile(self, fname, model_str=""):
        """
        Write model content to file "fname"
        """
        with open(fname, 'w') as out_f:
            out_f.write(model_str)

    def generateModel(self, model, fname):
        """
        generate model from the current plugin state
        """
        name = model['filename']
        desc_str = model['description']
        param_str = self.strFromParamDict(model['parameters'])
        pd_param_str = self.strFromParamDict(model['pd_parameters'])
        func_str = model['text']
        model_text = CUSTOM_TEMPLATE % {
            'name': name,
            'title': 'User model for ' + name,
            'description': desc_str,
            'date': datetime.datetime.now().strftime('%YYYY-%mm-%dd'),
        }

        # Write out parameters
        param_names = []    # to store parameter names
        pd_params = []
        model_text += 'parameters = [ \n'
        model_text += '#   ["name", "units", default, [lower, upper], "type", "description"],\n'
        for pname, pvalue, desc in self.getParamHelper(param_str):
            param_names.append(pname)
            model_text += "    ['%s', '', %s, [-inf, inf], '', '%s'],\n" % (pname, pvalue, desc)
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

    def checkModel(self, path):
        """
        Check that the model save in file 'path' can run.
        """
        # try running the model
        from sasmodels.sasview_model import load_custom_model
        Model = load_custom_model(path)
        model = Model()
        q =  np.array([0.01, 0.1])
        Iq = model.evalDistribution(q)
        qx, qy =  np.array([0.01, 0.01]), np.array([0.1, 0.1])
        Iqxy = model.evalDistribution([qx, qy])

        # check the model's unit tests run
        from sasmodels.model_test import run_one
        result = run_one(path)

        return result

    def getParamHelper(self, param_str):
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
        
    def strFromParamDict(self, param_dict):
        """
        Creates string from parameter dictionary
        {0: ('variable','value'),
         1: ('variable','value'),
         ...}
        """
        param_str = ""
        for row, params in param_dict.items():
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

from math import *
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
    import sys
    app = QtWidgets.QApplication(sys.argv)
    sheet = TabbedModelEditor()
    sheet.show()
    sys.exit(app.exec_())
    
