# global
import sys
import os
import logging

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import QtWebKit
from twisted.internet import threads

# SAS
from GuiUtils import *
from sas.sascalc.dataloader.loader import Loader
from sas.sasgui.guiframe.data_manager import DataManager

# UI
from UI.TabbedFileLoadUI import DataLoadWidget

class DataExplorerWindow(DataLoadWidget):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.

    def __init__(self, parent=None, guimanager=None):
        super(DataExplorerWindow, self).__init__(parent)

        # Main model for keeping loaded data
        self.model = QtGui.QStandardItemModel(self)
        self._default_save_location = None

        # GuiManager is the actual parent, but we needed to also pass the QMainWindow
        # in order to set the widget parentage properly.
        self.parent = guimanager
        self.loader = Loader()
        self.manager = DataManager()

        # Connect the buttons
        self.cmdLoad.clicked.connect(self.loadFile)
        self.cmdDelete.clicked.connect(self.deleteFile)
        self.cmdSendTo.clicked.connect(self.sendData)

        # Connect the comboboxes
        self.cbSelect.currentIndexChanged.connect(self.selectData)

        # Communicator for signal definitions
        self.communicate = self.parent.communicator()

        # Proxy model for showing a subset of Data1D/Data2D content
        self.proxy = QtGui.QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)

        # The Data viewer is QTreeView showing the proxy model
        self.treeView.setModel(self.proxy)


    def loadFile(self, event=None):
        """
        Called when the "Load" button pressed.
        Opens the Qt "Open File..." dialog 
        """
        path_str = self.chooseFiles()
        if not path_str:
            return

        # Notify the manager of the new data available
        self.communicate.fileReadSignal.emit(path_str)

        # threaded file load
        load_thread = threads.deferToThread(self.readData, path_str)
        load_thread.addCallback(self.loadComplete)

        return

    def loadFolder(self, event=None):
        """
        Called when the "File/Load Folder" menu item chosen.
        Opens the Qt "Open Folder..." dialog 
        """
        dir = QtGui.QFileDialog.getExistingDirectory(self, "Choose a directory", "",
              QtGui.QFileDialog.ShowDirsOnly)
        if dir is None:
            return

        dir = str(dir)

        if not os.path.isdir(dir):
            return

        # get content of dir into a list
        path_str = [os.path.join(os.path.abspath(dir), filename) for filename in os.listdir(dir)]

        # threaded file load
        load_thread = threads.deferToThread(self.readData, path_str)
        load_thread.addCallback(self.loadComplete)
        
        return

    def deleteFile(self, event):
        """
        Delete selected rows from the model
        """
        # Assure this is indeed wanted
        delete_msg = "This operation will delete the checked data sets and all the dependents." +\
                     "\nDo you want to continue?"
        reply = QtGui.QMessageBox.question(self, 'Warning', delete_msg,
                QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.No:
            return

        # Figure out which rows are checked
        ind = -1
        # Use 'while' so the row count is forced at every iteration
        while ind < self.model.rowCount():
            ind += 1
            item = self.model.item(ind)
            if item and item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                # Delete these rows from the model
                self.model.removeRow(ind)
                # Decrement index since we just deleted it
                ind -= 1

        # pass temporarily kept as a breakpoint anchor
        pass

    def sendData(self, event):
        """
        Send selected item data to the current perspective and set the relevant notifiers
        """
        # should this reside on GuiManager or here?
        self._perspective = self.parent.perspective()

        # Set the signal handlers
        self.communicator = self._perspective.communicator()
        self.communicator.updateModelFromPerspectiveSignal.connect(self.updateModelFromPerspective)

        # Figure out which rows are checked
        selected_items = []
        for index in range(self.model.rowCount()):
            item = self.model.item(index)
            if item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                selected_items.append(item)

        # Which perspective has been selected?
        if len(selected_items) > 1 and not self._perspective.allowBatch():
            msg = self._perspective.title() + " does not allow multiple data."
            msgbox = QtGui.QMessageBox()
            msgbox.setIcon(QtGui.QMessageBox.Critical)
            msgbox.setText(msg)
            msgbox.setStandardButtons(QtGui.QMessageBox.Ok)
            retval = msgbox.exec_()
            return
        # Dig up data from model
        data = [selected_items[0].child(0).data().toPyObject()]

        # TODO
        # New plot or appended?

        # Notify the GuiManager about the send request
        self._perspective.setData(data_list=data)


    def chooseFiles(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """
        # List of known extensions
        wlist = self.getWlist()

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        paths = QtGui.QFileDialog.getOpenFileName(self, "Choose a file", "",
                wlist, None, QtGui.QFileDialog.DontUseNativeDialog)
        if paths is None:
            return

        if paths.__class__.__name__ != "list":
            paths = [paths]

        path_str=[]
        for path in paths:
            if str(path):
                path_str.append(str(path))

        return path_str

    def readData(self, path):
        """
        verbatim copy/paste from
            sasgui\guiframe\local_perspectives\data_loader\data_loader.py
        slightly modified for clarity
        """
        message = ""
        log_msg = ''
        output = {}
        any_error = False
        data_error = False
        error_message = ""
        
        for p_file in path:
            info = "info"
            basename = os.path.basename(p_file)
            _, extension = os.path.splitext(basename)
            if extension.lower() in EXTENSIONS:
                any_error = True
                log_msg = "Data Loader cannot "
                log_msg += "load: %s\n" % str(p_file)
                log_msg += """Please try to open that file from "open project" """
                log_msg += """or "open analysis" menu\n"""
                error_message = log_msg + "\n"
                logging.info(log_msg)
                continue

            try:
                message = "Loading Data... " + str(basename) + "\n"

                # change this to signal notification in GuiManager
                self.communicate.statusBarUpdateSignal.emit(message)

                output_objects = self.loader.load(p_file)

                # Some loaders return a list and some just a single Data1D object.
                # Standardize.
                if not isinstance(output_objects, list):
                    output_objects = [output_objects]

                for item in output_objects:
                    # cast sascalc.dataloader.data_info.Data1D into sasgui.guiframe.dataFitting.Data1D
                    # TODO : Fix it
                    new_data = self.manager.create_gui_data(item, p_file)
                    output[new_data.id] = new_data
                    self.updateModel(new_data, p_file)
                    self.model.reset()

                    QtGui.qApp.processEvents()

                    if hasattr(item, 'errors'):
                        for error_data in item.errors:
                            data_error = True
                            message += "\tError: {0}\n".format(error_data)
                    else:

                        logging.error("Loader returned an invalid object:\n %s" % str(item))
                        data_error = True

            except Exception as ex:
                logging.error(sys.exc_value)

                any_error = True
            if any_error or error_message != "":
                if error_message == "":
                    error = "Error: " + str(sys.exc_info()[1]) + "\n"
                    error += "while loading Data: \n%s\n" % str(basename)
                    error_message += "The data file you selected could not be loaded.\n"
                    error_message += "Make sure the content of your file"
                    error_message += " is properly formatted.\n\n"
                    error_message += "When contacting the SasView team, mention the"
                    error_message += " following:\n%s" % str(error)
                elif data_error:
                    base_message = "Errors occurred while loading "
                    base_message += "{0}\n".format(basename)
                    base_message += "The data file loaded but with errors.\n"
                    error_message = base_message + error_message
                else:
                    error_message += "%s\n" % str(p_file)
                info = "error"
        
        if any_error or error_message:
            # self.loadUpdate(output=output, message=error_message, info=info)
            self.communicate.statusBarUpdateSignal.emit(error_message)

        else:
            message = "Loading Data Complete! "
        message += log_msg
        return (output, message)

    def getWlist(self):
        """
        """
        # Display the Qt Load File module
        cards = self.loader.get_wildcards()

        # get rid of the wx remnant in wildcards
        # TODO: modify sasview loader get_wildcards method, after merge,
        # so this kludge can be avoided
        new_cards = []
        for item in cards:
            new_cards.append(item[:item.find("|")])
        wlist = ';;'.join(new_cards)

        return wlist

    def selectData(self, index):
        """
        Callback method for modifying the TreeView on Selection Options change
        """
        if not isinstance(index, int):
            msg = "Incorrect type passed to DataExplorer.selectData()"
            raise AttributeError, msg

        # Respond appropriately
        if index == 0:
            # Select All
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                if item.isCheckable() and item.checkState() == QtCore.Qt.Unchecked:
                    item.setCheckState(QtCore.Qt.Checked)
        elif index == 1:
            # De-select All
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                if item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                    item.setCheckState(QtCore.Qt.Unchecked)

        elif index == 2:
            # Select All 1-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                item.setCheckState(QtCore.Qt.Unchecked)

                try:
                    is1D = item.child(0).data().toPyObject().__class__.__name__ == 'Data1D'
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError, msg

                if is1D:
                    item.setCheckState(QtCore.Qt.Checked)

        elif index == 3:
            # Unselect All 1-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)

                try:
                    is1D = item.child(0).data().toPyObject().__class__.__name__ == 'Data1D'
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError, msg

                if item.isCheckable() and item.checkState() == QtCore.Qt.Checked and is1D:
                    item.setCheckState(QtCore.Qt.Unchecked)

        elif index == 4:
            # Select All 2-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                item.setCheckState(QtCore.Qt.Unchecked)
                try:
                    is2D = item.child(0).data().toPyObject().__class__.__name__ == 'Data2D'
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError, msg

                if is2D:
                    item.setCheckState(QtCore.Qt.Checked)

        elif index == 5:
            # Unselect All 2-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)

                try:
                    is2D = item.child(0).data().toPyObject().__class__.__name__ == 'Data2D'
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError, msg

                if item.isCheckable() and item.checkState() == QtCore.Qt.Checked and is2D:
                    item.setCheckState(QtCore.Qt.Unchecked)

        else:
            msg = "Incorrect value in the Selection Option"
            # Change this to a proper logging action
            raise Exception, msg


    def loadComplete(self, output, message=""):
        """
        Post message to status bar and update the data manager
        """
        self.model.reset()
        # Notify the manager of the new data available
        self.communicate.statusBarUpdateSignal.emit(message)
        self.communicate.fileDataReceivedSignal.emit(output)
        self.manager.add_data(data_list=output)

    def updateModel(self, data, p_file):
        """
        """
        # Structure of the model
        # checkbox + basename
        #     |-------> Info
        #                 |----> Data.D object
        #                 |----> Title:
        #                 |----> Run:
        #                 |----> Type:
        #                 |----> Path:
        #                 |----> Process
        #                          |-----> process[0].name
        #

        # Top-level item: checkbox with label
        checkbox_item = QtGui.QStandardItem(True)
        checkbox_item.setCheckable(True)
        checkbox_item.setCheckState(QtCore.Qt.Checked)
        checkbox_item.setText(os.path.basename(p_file))

        # Add "Info" item
        info_item = QtGui.QStandardItem("Info")

        # Add the actual Data1D/Data2D object
        object_item = QtGui.QStandardItem()
        object_item.setData(QtCore.QVariant(data))

        checkbox_item.setChild(0, object_item)

        # Add rows for display in the view
        self.addExtraRows(info_item, data)

        # Set info_item as the only child
        checkbox_item.setChild(1, info_item)

        # New row in the model
        self.model.appendRow(checkbox_item)
        
        # Don't show "empty" rows with data objects
        self.proxy.setFilterRegExp(r"[^()]")

    def updateModelFromPerspective(self, model_item):
        """
        """
        # Overwrite the index with what we got from the perspective
        if type(model_item) != QtGui.QStandardItem:
            msg = "Wrong data type returned from calculations."
            raise AttributeError, msg
        # self.model.insertRow(model_item)
        # Reset the view
        self.model.reset()
        # Pass acting as a debugger anchor
        pass

    def addExtraRows(self, info_item, data):
        """
        Extract relevant data to include in the Info ModelItem
        """
        title_item   = QtGui.QStandardItem("Title: "      + data.title)
        run_item     = QtGui.QStandardItem("Run: "        + str(data.run))
        type_item    = QtGui.QStandardItem("Type: "       + str(data.__class__.__name__))
        path_item    = QtGui.QStandardItem("Path: "       + data.path)
        instr_item   = QtGui.QStandardItem("Instrument: " + data.instrument)
        process_item = QtGui.QStandardItem("Process")
        if isinstance(data.process, list) and data.process:
            for process in data.process:
                process_date = process.date
                process_date_item = QtGui.QStandardItem("Date: " + process_date)
                process_item.appendRow(process_date_item)

                process_descr = process.description
                process_descr_item = QtGui.QStandardItem("Description: " + process_descr)
                process_item.appendRow(process_descr_item)

                process_name = process.name
                process_name_item = QtGui.QStandardItem("Name: " + process_name)
                process_item.appendRow(process_name_item)

        info_item.appendRow(title_item)
        info_item.appendRow(run_item)
        info_item.appendRow(type_item)
        info_item.appendRow(path_item)
        info_item.appendRow(instr_item)
        info_item.appendRow(process_item)
       

if __name__ == "__main__":
    app = QtGui.QApplication([])
    dlg = DataExplorerWindow()
    dlg.show()
    sys.exit(app.exec_())