# global
import sys
import os
import logging 
from shutil import copyfile

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from sas.sascalc.fit import models
from sas.qtgui.Perspectives.Fitting import ModelUtilities
from sas.qtgui.Utilities.TabbedModelEditor import TabbedModelEditor
import sas.qtgui.Utilities.GuiUtils as GuiUtils

from sas.qtgui.Utilities.UI.PluginManagerUI import Ui_PluginManagerUI


class PluginManager(QtWidgets.QDialog, Ui_PluginManagerUI):
    """
    Class describing the model plugin manager.
    This is a simple list widget allowing for viewing/adding/deleting custom models.
    """
    def __init__(self, parent=None):
        super(PluginManager, self).__init__()
        self.setupUi(self)

        self.parent = parent
        self.cmdDelete.setEnabled(False)
        self.cmdEdit.setEnabled(False)
        self.cmdDuplicate.setEnabled(False)

        # globals
        self.readModels()

        # internal representation of the parameter list
        # {<row>: (<parameter>, <value>)}
        self.plugin_dict = {}

        # Initialize signals
        self.addSignals()

    def readModels(self):
        """
        Read in custom models from the default location
        """
        self.lstModels.clear()
        plugins = ModelUtilities._find_models()
        models = list(plugins.keys())
        self.lstModels.addItems(models)

    def addSignals(self):
        """
        Define slots for widget signals
        """
        self.cmdOK.clicked.connect(self.accept)
        self.cmdDelete.clicked.connect(self.onDelete)
        self.cmdAdd.clicked.connect(self.onAdd)
        self.cmdDuplicate.clicked.connect(self.onDuplicate)
        self.cmdEdit.clicked.connect(self.onEdit)
        self.cmdHelp.clicked.connect(self.onHelp)
        self.lstModels.selectionModel().selectionChanged.connect(self.onSelectionChanged)
        self.parent.communicate.customModelDirectoryChanged.connect(self.readModels)

    def onSelectionChanged(self):
        """
        Respond to row selection
        """
        rows = len(self.lstModels.selectionModel().selectedRows())
        self.cmdDelete.setEnabled(rows>0)
        self.cmdEdit.setEnabled(rows==1)
        self.cmdDuplicate.setEnabled(rows>0)

    def onDelete(self):
        """
        Remove the file containing the selected plugin
        """
        plugins_to_delete = [s.data() for s in self.lstModels.selectionModel().selectedRows()]

        delete_msg = "Are you sure you want to remove the selected plugins?"
        reply = QtWidgets.QMessageBox.question(
            self,
            'Warning',
            delete_msg,
            QtWidgets.QMessageBox.Yes,
            QtWidgets.QMessageBox.No)

        # Exit if no
        if reply == QtWidgets.QMessageBox.No:
            return

        for plugin in plugins_to_delete:
            name = os.path.join(ModelUtilities.find_plugins_dir(), plugin + ".py")
            os.remove(name)

        self.parent.communicate.customModelDirectoryChanged.emit()

    def onAdd(self):
        """
        Show the add new model dialog
        """
        self.add_widget = TabbedModelEditor(parent=self.parent)
        self.add_widget.show()

    def onDuplicate(self):
        """
        Creates a copy of the selected model(s)
        """

        plugins_to_copy = [s.data() for s in self.lstModels.selectionModel().selectedRows()]
        plugin_dir = ModelUtilities.find_plugins_dir()
        for plugin in plugins_to_copy:
            src_filename = plugin + ".py"
            src_file = os.path.join(plugin_dir, src_filename)
            dst_filename = GuiUtils.findNextFilename(src_filename, plugin_dir)
            if not dst_filename:
                logging.error("Could not find appropriate filename for "+src_file)
            dst_file = os.path.join(plugin_dir, dst_filename)
            copyfile(src_file, dst_file)
            self.parent.communicate.customModelDirectoryChanged.emit()

    def onEdit(self):
        """
        Show the edit existing model dialog
        """
        plugin_location = models.find_plugins_dir()
        # GUI assured only one row selected. Pick up the only element in list.
        try:
            model_to_edit = self.lstModels.selectionModel().selectedRows()[0].data()
        except Exception:
            # Something wrong with model, return
            return
        name = os.path.join(plugin_location, model_to_edit + ".py")
        self.edit_widget = TabbedModelEditor(parent=self.parent, edit_only=True)
        self.edit_widget.loadFile(name)
        self.edit_widget.show()

    def onHelp(self):
        """
        Show the help page in the default browser
        """
        location = "/user/sasgui/perspectives/fitting/fitting_help.html#new-plugin-model"
        self.parent.showHelp(location)
                