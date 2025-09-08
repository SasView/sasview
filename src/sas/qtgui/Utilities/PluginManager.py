# global
import logging
import os
from shutil import copyfile

from PySide6 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Utilities.ModelEditors.TabbedEditor.TabbedModelEditor import TabbedModelEditor
from sas.qtgui.Utilities.UI.PluginManagerUI import Ui_PluginManagerUI
from sas.sascalc.fit import models


class PluginManager(QtWidgets.QDialog, Ui_PluginManagerUI):
    """
    Class describing the model plugin manager.
    This is a simple list widget allowing for viewing/adding/deleting custom models.
    """
    def __init__(self, parent=None):
        super(PluginManager, self).__init__(parent._parent)
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
        self.plugins = models.find_plugin_models()
        model_list = list(self.plugins.keys())
        self.lstModels.addItems(model_list)

    def addSignals(self):
        """
        Define slots for widget signals
        """
        self.cmdOK.clicked.connect(self.accept)
        self.cmdDelete.clicked.connect(self.onDelete)
        self.cmdAdd.clicked.connect(self.onAdd)
        self.cmdAddFile.clicked.connect(self.onAddFile)
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
            # get filename from the plugin name
            name = self.plugins[plugin].filename
            # if no filename defined, attempt plugin name as filename
            if not name:
                name = os.path.join(models.find_plugins_dir(), plugin + ".py")
            os.remove(name)

        self.parent.communicate.customModelDirectoryChanged.emit()

    def onAdd(self):
        """
        Show the add new model dialog
        """
        self.add_widget = TabbedModelEditor(parent=self.parent)
        self.add_widget.show()

    def onAddFile(self):
        """
        Open system Load FIle dialog, load a plugin and put it in the plugin directory
        """
        plugin_file = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose a plugin", "","Python (*.py)")[0]

        if not plugin_file:
            return

        plugin_dir = models.find_plugins_dir()
        file_name = os.path.basename(str(plugin_file))

        # check if valid model
        try:
            model_results = GuiUtils.checkModel(plugin_file)
            logging.info(model_results)
        # We can't guarantee the type of the exception coming from
        # Sasmodels, so need the overreaching general Exception
        except Exception:
            msg = "Invalid plugin: %s " % file_name
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.setText(msg)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            retval = msgbox.exec_()
            return

        # check if file with the same name exists
        if file_name in os.listdir(plugin_dir):
            msg = "Plugin " + file_name + " already exists.\n"
            msg += "Do you wish to overwrite the file?"
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(msg)
            msgbox.setWindowTitle("Plugin Load")
            # custom buttons
            button_yes = QtWidgets.QPushButton("Yes")
            msgbox.addButton(button_yes, QtWidgets.QMessageBox.YesRole)
            button_no = QtWidgets.QPushButton("No")
            msgbox.addButton(button_no, QtWidgets.QMessageBox.RejectRole)
            retval = msgbox.exec_()
            if retval == QtWidgets.QMessageBox.RejectRole:
                # cancel copy
                return

        # Copy from origin to ~/.sasview/plugin_models
        from shutil import copy

        # no check on clash
        copy(plugin_file, plugin_dir)

        # Copy corresponding C file, if present
        c_file = plugin_file.replace(".py", ".c")
        if os.path.isfile(c_file):
            copy(c_file, plugin_dir)

        self.parent.communicate.customModelDirectoryChanged.emit()
        log_msg = "New plugin added: %s" % file_name
        logging.info(log_msg)

    def onDuplicate(self):
        """
        Creates a copy of the selected model(s)
        """

        plugins_to_copy = [s.data() for s in self.lstModels.selectionModel().selectedRows()]
        plugin_dir = models.find_plugins_dir()
        for plugin in plugins_to_copy:
            src_filename = plugin + ".py"

            # get filename from the plugin name
            src_file = self.plugins[plugin].filename
            # if no filename defined, attempt plugin name as filename
            if not src_file:
                src_filename = plugin + ".py"
                src_file = os.path.join(plugin_dir, src_filename)
            else:
                src_filename = os.path.basename(src_file)

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
        # get filename from the plugin name
        name = self.plugins[model_to_edit].filename
        # if no filename defined, attempt plugin name as filename
        if not name:
            name = os.path.join(plugin_location, model_to_edit + ".py")

        self.edit_widget = TabbedModelEditor(parent=self.parent, edit_only=True)
        self.edit_widget.loadFile(name)
        self.edit_widget.show()

    def onHelp(self):
        """
        Show the help page in the default browser
        """
        location = "/user/qtgui/Perspectives/Fitting/fitting_help.html#new-plugin-model"
        self.parent.showHelp(location)
