# global
import sys
import os
import time
import logging

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from twisted.internet import threads

# SASCALC
from sas.sascalc.dataloader.loader import Loader

# QTGUI
import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Plotting.PlotHelper as PlotHelper

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D
from sas.qtgui.Plotting.Plotter import Plotter
from sas.qtgui.Plotting.Plotter2D import Plotter2D
from sas.qtgui.Plotting.MaskEditor import MaskEditor

from sas.qtgui.MainWindow.DataManager import DataManager
from sas.qtgui.MainWindow.DroppableDataLoadWidget import DroppableDataLoadWidget

import sas.qtgui.Perspectives as Perspectives

DEFAULT_PERSPECTIVE = "Fitting"

class DataExplorerWindow(DroppableDataLoadWidget):
    # The controller which is responsible for managing signal slots connections
    # for the gui and providing an interface to the data model.

    def __init__(self, parent=None, guimanager=None, manager=None):
        super(DataExplorerWindow, self).__init__(parent, guimanager)

        # Main model for keeping loaded data
        self.model = QtGui.QStandardItemModel(self)

        # Secondary model for keeping frozen data sets
        self.theory_model = QtGui.QStandardItemModel(self)

        # GuiManager is the actual parent, but we needed to also pass the QMainWindow
        # in order to set the widget parentage properly.
        self.parent = guimanager
        self.loader = Loader()
        self.manager = manager if manager is not None else DataManager()
        self.txt_widget = QtWidgets.QTextEdit(None)

        # Be careful with twisted threads.
        self.mutex = QtCore.QMutex()

        # Active plots
        self.active_plots = {}

        # Connect the buttons
        self.cmdLoad.clicked.connect(self.loadFile)
        self.cmdDeleteData.clicked.connect(self.deleteFile)
        self.cmdDeleteTheory.clicked.connect(self.deleteTheory)
        self.cmdFreeze.clicked.connect(self.freezeTheory)
        self.cmdSendTo.clicked.connect(self.sendData)
        self.cmdNew.clicked.connect(self.newPlot)
        self.cmdNew_2.clicked.connect(self.newPlot)
        self.cmdAppend.clicked.connect(self.appendPlot)
        self.cmdHelp.clicked.connect(self.displayHelp)
        self.cmdHelp_2.clicked.connect(self.displayHelp)

        # Fill in the perspectives combo
        self.initPerspectives()

        # Custom context menu
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.onCustomContextMenu)
        self.contextMenu()

        # Same menus for the theory view
        self.freezeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.freezeView.customContextMenuRequested.connect(self.onCustomContextMenu)

        # Connect the comboboxes
        self.cbSelect.currentIndexChanged.connect(self.selectData)

        #self.closeEvent.connect(self.closeEvent)
        self.currentChanged.connect(self.onTabSwitch)
        self.communicator = self.parent.communicator()
        self.communicator.fileReadSignal.connect(self.loadFromURL)
        self.communicator.activeGraphsSignal.connect(self.updateGraphCount)
        self.communicator.activeGraphName.connect(self.updatePlotName)
        self.communicator.plotUpdateSignal.connect(self.updatePlot)

        self.cbgraph.editTextChanged.connect(self.enableGraphCombo)
        self.cbgraph.currentIndexChanged.connect(self.enableGraphCombo)

        # Proxy model for showing a subset of Data1D/Data2D content
        self.data_proxy = QtCore.QSortFilterProxyModel(self)
        self.data_proxy.setSourceModel(self.model)

        # Don't show "empty" rows with data objects
        self.data_proxy.setFilterRegExp(r"[^()]")

        # The Data viewer is QTreeView showing the proxy model
        self.treeView.setModel(self.data_proxy)

        # Proxy model for showing a subset of Theory content
        self.theory_proxy = QtCore.QSortFilterProxyModel(self)
        self.theory_proxy.setSourceModel(self.theory_model)

        # Don't show "empty" rows with data objects
        self.theory_proxy.setFilterRegExp(r"[^()]")

        # Theory model view
        self.freezeView.setModel(self.theory_proxy)

        self.enableGraphCombo(None)

        # Current view on model
        self.current_view = self.treeView

    def closeEvent(self, event):
        """
        Overwrite the close event - no close!
        """
        event.ignore()

    def onTabSwitch(self, index):
        """ Callback for tab switching signal """
        if index == 0:
            self.current_view = self.treeView
        else:
            self.current_view = self.freezeView

    def displayHelp(self):
        """
        Show the "Loading data" section of help
        """
        tree_location = "/user/qtgui/MainWindow/data_explorer_help.html"
        self.parent.showHelp(tree_location)

    def enableGraphCombo(self, combo_text):
        """
        Enables/disables "Assign Plot" elements
        """
        self.cbgraph.setEnabled(len(PlotHelper.currentPlots()) > 0)
        self.cmdAppend.setEnabled(len(PlotHelper.currentPlots()) > 0)

    def initPerspectives(self):
        """
        Populate the Perspective combobox and define callbacks
        """
        available_perspectives = sorted([p for p in list(Perspectives.PERSPECTIVES.keys())])
        if available_perspectives:
            self.cbFitting.clear()
            self.cbFitting.addItems(available_perspectives)
        self.cbFitting.currentIndexChanged.connect(self.updatePerspectiveCombo)
        # Set the index so we see the default (Fitting)
        self.cbFitting.setCurrentIndex(self.cbFitting.findText(DEFAULT_PERSPECTIVE))

    def _perspective(self):
        """
        Returns the current perspective
        """
        return self.parent.perspective()

    def loadFromURL(self, url):
        """
        Threaded file load
        """
        load_thread = threads.deferToThread(self.readData, url)
        load_thread.addCallback(self.loadComplete)
        load_thread.addErrback(self.loadFailed)

    def loadFile(self, event=None):
        """
        Called when the "Load" button pressed.
        Opens the Qt "Open File..." dialog
        """
        path_str = self.chooseFiles()
        if not path_str:
            return
        self.loadFromURL(path_str)

    def loadFolder(self, event=None):
        """
        Called when the "File/Load Folder" menu item chosen.
        Opens the Qt "Open Folder..." dialog
        """
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose a directory", "",
              QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontUseNativeDialog)
        if folder is None:
            return

        folder = str(folder)

        if not os.path.isdir(folder):
            return

        # get content of dir into a list
        path_str = [os.path.join(os.path.abspath(folder), filename)
                    for filename in os.listdir(folder)]

        self.loadFromURL(path_str)

    def loadProject(self):
        """
        Called when the "Open Project" menu item chosen.
        """
        kwargs = {
            'parent'    : self,
            'caption'   : 'Open Project',
            'filter'    : 'Project (*.json);;All files (*.*)',
            'options'   : QtWidgets.QFileDialog.DontUseNativeDialog
        }
        filename = QtWidgets.QFileDialog.getOpenFileName(**kwargs)[0]
        if filename:
            load_thread = threads.deferToThread(self.readProject, filename)
            load_thread.addCallback(self.readProjectComplete)
            load_thread.addErrback(self.readProjectFailed)

    def loadFailed(self, reason):
        """
        """
        print("file load FAILED: ", reason)
        pass

    def readProjectFailed(self, reason):
        """
        """
        print("readProjectFailed FAILED: ", reason)
        pass

    def readProject(self, filename):
        self.communicator.statusBarUpdateSignal.emit("Loading Project... %s" % os.path.basename(filename))
        try:
            manager = DataManager()
            with open(filename, 'r') as infile:
                manager.load_from_readable(infile)

            self.communicator.statusBarUpdateSignal.emit("Loaded Project: %s" % os.path.basename(filename))
            return manager

        except:
            self.communicator.statusBarUpdateSignal.emit("Failed: %s" % os.path.basename(filename))
            raise

    def readProjectComplete(self, manager):
        self.model.clear()

        self.manager.assign(manager)
        self.model.beginResetModel()
        for id, item in self.manager.get_all_data().items():
            self.updateModel(item.data, item.path)

        self.model.endResetModel()

    def saveProject(self):
        """
        Called when the "Save Project" menu item chosen.
        """
        kwargs = {
            'parent'    : self,
            'caption'   : 'Save Project',
            'filter'    : 'Project (*.json)',
            'options'   : QtWidgets.QFileDialog.DontUseNativeDialog
        }
        name_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
        filename = name_tuple[0]
        if filename:
            _, extension = os.path.splitext(filename)
            if not extension:
                filename = '.'.join((filename, 'json'))
            self.communicator.statusBarUpdateSignal.emit("Saving Project... %s\n" % os.path.basename(filename))
            with open(filename, 'w') as outfile:
                self.manager.save_to_writable(outfile)

    def deleteFile(self, event):
        """
        Delete selected rows from the model
        """
        # Assure this is indeed wanted
        delete_msg = "This operation will delete the checked data sets and all the dependents." +\
                     "\nDo you want to continue?"
        reply = QtWidgets.QMessageBox.question(self,
                                           'Warning',
                                           delete_msg,
                                           QtWidgets.QMessageBox.Yes,
                                           QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            return

        # Figure out which rows are checked
        ind = -1
        # Use 'while' so the row count is forced at every iteration
        deleted_indices = []
        deleted_names = []
        while ind < self.model.rowCount():
            ind += 1
            item = self.model.item(ind)

            if item and item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                # Delete these rows from the model
                deleted_names.append(str(self.model.item(ind).text()))
                deleted_indices.append(item)

                self.model.removeRow(ind)
                # Decrement index since we just deleted it
                ind -= 1

        # Let others know we deleted data
        self.communicator.dataDeletedSignal.emit(deleted_indices)

        # update stored_data
        self.manager.update_stored_data(deleted_names)

    def deleteTheory(self, event):
        """
        Delete selected rows from the theory model
        """
        # Assure this is indeed wanted
        delete_msg = "This operation will delete the checked data sets and all the dependents." +\
                     "\nDo you want to continue?"
        reply = QtWidgets.QMessageBox.question(self,
                                           'Warning',
                                           delete_msg,
                                           QtWidgets.QMessageBox.Yes,
                                           QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            return

        # Figure out which rows are checked
        ind = -1
        # Use 'while' so the row count is forced at every iteration
        while ind < self.theory_model.rowCount():
            ind += 1
            item = self.theory_model.item(ind)
            if item and item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                # Delete these rows from the model
                self.theory_model.removeRow(ind)
                # Decrement index since we just deleted it
                ind -= 1

        # pass temporarily kept as a breakpoint anchor
        pass

    def sendData(self, event):
        """
        Send selected item data to the current perspective and set the relevant notifiers
        """
        # Set the signal handlers
        self.communicator.updateModelFromPerspectiveSignal.connect(self.updateModelFromPerspective)

        def isItemReady(index):
            item = self.model.item(index)
            return item.isCheckable() and item.checkState() == QtCore.Qt.Checked

        # Figure out which rows are checked
        selected_items = [self.model.item(index)
                          for index in range(self.model.rowCount())
                          if isItemReady(index)]

        if len(selected_items) < 1:
            return

        # Which perspective has been selected?
        if len(selected_items) > 1 and not self._perspective().allowBatch():
            msg = self._perspective().title() + " does not allow multiple data."
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.setText(msg)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            retval = msgbox.exec_()
            return

        # Notify the GuiManager about the send request
        self._perspective().setData(data_item=selected_items, is_batch=self.chkBatch.isChecked())

    def freezeTheory(self, event):
        """
        Freeze selected theory rows.

        "Freezing" means taking the plottable data from the Theory item
        and copying it to a separate top-level item in Data.
        """
        # Figure out which rows are checked
        # Use 'while' so the row count is forced at every iteration
        outer_index = -1
        theories_copied = 0
        while outer_index < self.theory_model.rowCount():
            outer_index += 1
            outer_item = self.theory_model.item(outer_index)
            if not outer_item:
                continue
            if outer_item.isCheckable() and \
                   outer_item.checkState() == QtCore.Qt.Checked:
                self.model.beginResetModel()
                theories_copied += 1
                new_item = self.recursivelyCloneItem(outer_item)
                # Append a "unique" descriptor to the name
                time_bit = str(time.time())[7:-1].replace('.', '')
                new_name = new_item.text() + '_@' + time_bit
                new_item.setText(new_name)
                self.model.appendRow(new_item)
                self.model.endResetModel()
            #self.model.reset()

        freeze_msg = ""
        if theories_copied == 0:
            return
        elif theories_copied == 1:
            freeze_msg = "1 theory copied from the Theory tab as a data set"
        elif theories_copied > 1:
            freeze_msg = "%i theories copied from the Theory tab as data sets" % theories_copied
        else:
            freeze_msg = "Unexpected number of theories copied: %i" % theories_copied
            raise AttributeError(freeze_msg)
        self.communicator.statusBarUpdateSignal.emit(freeze_msg)
        # Actively switch tabs
        self.setCurrentIndex(1)

    def recursivelyCloneItem(self, item):
        """
        Clone QStandardItem() object
        """
        new_item = item.clone()
        # clone doesn't do deepcopy :(
        for child_index in range(item.rowCount()):
            child_item = self.recursivelyCloneItem(item.child(child_index))
            new_item.setChild(child_index, child_item)
        return new_item

    def updatePlotName(self, name_tuple):
        """
        Modify the name of the current plot
        """
        old_name, current_name = name_tuple
        ind = self.cbgraph.findText(old_name)
        self.cbgraph.setCurrentIndex(ind)
        self.cbgraph.setItemText(ind, current_name)

    def updateGraphCount(self, graph_list):
        """
        Modify the graph name combo and potentially remove
        deleted graphs
        """
        self.updateGraphCombo(graph_list)

        if not self.active_plots:
            return
        new_plots = [PlotHelper.plotById(plot) for plot in graph_list]
        active_plots_copy = list(self.active_plots.keys())
        for plot in active_plots_copy:
            if self.active_plots[plot] in new_plots:
                continue
            self.active_plots.pop(plot)

    def updateGraphCombo(self, graph_list):
        """
        Modify Graph combo box on graph add/delete
        """
        orig_text = self.cbgraph.currentText()
        self.cbgraph.clear()
        self.cbgraph.insertItems(0, graph_list)
        ind = self.cbgraph.findText(orig_text)
        if ind > 0:
            self.cbgraph.setCurrentIndex(ind)

    def updatePerspectiveCombo(self, index):
        """
        Notify the gui manager about the new perspective chosen.
        """
        self.communicator.perspectiveChangedSignal.emit(self.cbFitting.itemText(index))
        self.chkBatch.setEnabled(self.parent.perspective().allowBatch())

    def itemFromFilename(self, filename):
        """
        Retrieves model item corresponding to the given filename
        """
        item = GuiUtils.itemFromFilename(filename, self.model)
        return item

    def displayFile(self, filename=None, is_data=True):
        """
        Forces display of charts for the given filename
        """
        model = self.model if is_data else self.theory_model
        # Now query the model item for available plots
        plots = GuiUtils.plotsFromFilename(filename, model)
        item = GuiUtils.itemFromFilename(filename, model)

        new_plots = []
        for plot in plots:
            plot_id = plot.id
            if plot_id in list(self.active_plots.keys()):
                self.active_plots[plot_id].replacePlot(plot_id, plot)
            else:
                # 'sophisticated' test to generate standalone plot for residuals
                if 'esiduals' in plot.title:
                    self.plotData([(item, plot)])
                else:
                    new_plots.append((item, plot))

        if new_plots:
            self.plotData(new_plots)

    def displayData(self, data_list):
        """
        Forces display of charts for the given data set
        """
        plot_to_show = data_list[0]
        # passed plot is used ONLY to figure out its title,
        # so all the charts related by it can be pulled from 
        # the data explorer indices.
        filename = plot_to_show.filename
        self.displayFile(filename=filename, is_data=plot_to_show.is_data)

    def addDataPlot2D(self, plot_set, item):
        """
        Create a new 2D plot and add it to the workspace
        """
        plot2D = Plotter2D(self)
        plot2D.item = item
        plot2D.plot(plot_set)
        self.addPlot(plot2D)
        self.active_plots[plot2D.data.id] = plot2D
        #============================================
        # Experimental hook for silx charts
        #============================================
        ## Attach silx
        #from silx.gui import qt
        #from silx.gui.plot import StackView
        #sv = StackView()
        #sv.setColormap("jet", autoscale=True)
        #sv.setStack(plot_set.data.reshape(1,100,100))
        ##sv.setLabels(["x: -10 to 10 (200 samples)",
        ##              "y: -10 to 5 (150 samples)"])
        #sv.show()
        #============================================

    def plotData(self, plots):
        """
        Takes 1D/2D data and generates a single plot (1D) or multiple plots (2D)
        """
        # Call show on requested plots
        # All same-type charts in one plot
        for item, plot_set in plots:
            if isinstance(plot_set, Data1D):
                if not 'new_plot' in locals():
                    new_plot = Plotter(self)
                new_plot.plot(plot_set)
                # active_plots may contain multiple charts
                self.active_plots[plot_set.id] = new_plot
            elif isinstance(plot_set, Data2D):
                self.addDataPlot2D(plot_set, item)
            else:
                msg = "Incorrect data type passed to Plotting"
                raise AttributeError(msg)

        if 'new_plot' in locals() and \
            hasattr(new_plot, 'data') and \
            isinstance(new_plot.data, Data1D):
                self.addPlot(new_plot)

    def newPlot(self):
        """
        Select checked data and plot it
        """
        # Check which tab is currently active
        if self.current_view == self.treeView:
            plots = GuiUtils.plotsFromCheckedItems(self.model)
        else:
            plots = GuiUtils.plotsFromCheckedItems(self.theory_model)

        self.plotData(plots)

    def addPlot(self, new_plot):
        """
        Helper method for plot bookkeeping
        """
        # Update the global plot counter
        title = str(PlotHelper.idOfPlot(new_plot))
        new_plot.setWindowTitle(title)

        # Set the object name to satisfy the Squish object picker
        new_plot.setObjectName(title)

        # Add the plot to the workspace
        self.parent.workspace().addSubWindow(new_plot)

        # Show the plot
        new_plot.show()
        new_plot.canvas.draw()

        # Update the active chart list
        #self.active_plots[new_plot.data.id] = new_plot

    def appendPlot(self):
        """
        Add data set(s) to the existing matplotlib chart
        """
        # new plot data
        new_plots = GuiUtils.plotsFromCheckedItems(self.model)

        # old plot data
        plot_id = str(self.cbgraph.currentText())

        assert plot_id in PlotHelper.currentPlots(), "No such plot: %s"%(plot_id)

        old_plot = PlotHelper.plotById(plot_id)

        # Add new data to the old plot, if data type is the same.
        for _, plot_set in new_plots:
            if type(plot_set) is type(old_plot._data):
                old_plot.data = plot_set
                old_plot.plot()

    def updatePlot(self, new_data):
        """
        Modify existing plot for immediate response
        """
        data = new_data[0]
        assert type(data).__name__ in ['Data1D', 'Data2D']

        id = data.id
        if data.id in list(self.active_plots.keys()):
            self.active_plots[id].replacePlot(id, data)

    def chooseFiles(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """
        # List of known extensions
        wlist = self.getWlist()

        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        paths = QtWidgets.QFileDialog.getOpenFileNames(self, "Choose a file", "",
                wlist, None, QtWidgets.QFileDialog.DontUseNativeDialog)[0]
        if not paths:
            return

        if not isinstance(paths, list):
            paths = [paths]

        return paths

    def readData(self, path):
        """
        verbatim copy-paste from
           sasgui.guiframe.local_perspectives.data_loader.data_loader.py
        slightly modified for clarity
        """
        message = ""
        log_msg = ''
        output = {}
        any_error = False
        data_error = False
        error_message = ""
        number_of_files = len(path)
        self.communicator.progressBarUpdateSignal.emit(0.0)

        for index, p_file in enumerate(path):
            basename = os.path.basename(p_file)
            _, extension = os.path.splitext(basename)
            if extension.lower() in GuiUtils.EXTENSIONS:
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
                self.communicator.statusBarUpdateSignal.emit(message)

                output_objects = self.loader.load(p_file)

                # Some loaders return a list and some just a single Data1D object.
                # Standardize.
                if not isinstance(output_objects, list):
                    output_objects = [output_objects]

                for item in output_objects:
                    # cast sascalc.dataloader.data_info.Data1D into
                    # sasgui.guiframe.dataFitting.Data1D
                    # TODO : Fix it
                    new_data = self.manager.create_gui_data(item, p_file)
                    output[new_data.id] = new_data

                    # Model update should be protected
                    self.mutex.lock()
                    self.updateModel(new_data, p_file)
                    #self.model.reset()
                    QtWidgets.QApplication.processEvents()
                    self.mutex.unlock()

                    if hasattr(item, 'errors'):
                        for error_data in item.errors:
                            data_error = True
                            message += "\tError: {0}\n".format(error_data)
                    else:

                        logging.error("Loader returned an invalid object:\n %s" % str(item))
                        data_error = True

            except Exception as ex:
                logging.error(sys.exc_info()[1])

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

            current_percentage = int(100.0* index/number_of_files)
            self.communicator.progressBarUpdateSignal.emit(current_percentage)

        if any_error or error_message:
            logging.error(error_message)
            status_bar_message = "Errors occurred while loading %s" % format(basename)
            self.communicator.statusBarUpdateSignal.emit(status_bar_message)

        else:
            message = "Loading Data Complete! "
        message += log_msg
        # Notify the progress bar that the updates are over.
        self.communicator.progressBarUpdateSignal.emit(-1)
        self.communicator.statusBarUpdateSignal.emit(message)

        return output, message

    def getWlist(self):
        """
        Wildcards of files we know the format of.
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
            raise AttributeError(msg)

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
                    is1D = isinstance(GuiUtils.dataFromItem(item), Data1D)
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError(msg)

                if is1D:
                    item.setCheckState(QtCore.Qt.Checked)

        elif index == 3:
            # Unselect All 1-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)

                try:
                    is1D = isinstance(GuiUtils.dataFromItem(item), Data1D)
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError(msg)

                if item.isCheckable() and item.checkState() == QtCore.Qt.Checked and is1D:
                    item.setCheckState(QtCore.Qt.Unchecked)

        elif index == 4:
            # Select All 2-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)
                item.setCheckState(QtCore.Qt.Unchecked)
                try:
                    is2D = isinstance(GuiUtils.dataFromItem(item), Data2D)
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError(msg)

                if is2D:
                    item.setCheckState(QtCore.Qt.Checked)

        elif index == 5:
            # Unselect All 2-D
            for index in range(self.model.rowCount()):
                item = self.model.item(index)

                try:
                    is2D = isinstance(GuiUtils.dataFromItem(item), Data2D)
                except AttributeError:
                    msg = "Bad structure of the data model."
                    raise RuntimeError(msg)

                if item.isCheckable() and item.checkState() == QtCore.Qt.Checked and is2D:
                    item.setCheckState(QtCore.Qt.Unchecked)

        else:
            msg = "Incorrect value in the Selection Option"
            # Change this to a proper logging action
            raise Exception(msg)

    def contextMenu(self):
        """
        Define actions and layout of the right click context menu
        """
        # Create a custom menu based on actions defined in the UI file
        self.context_menu = QtWidgets.QMenu(self)
        self.context_menu.addAction(self.actionDataInfo)
        self.context_menu.addAction(self.actionSaveAs)
        self.context_menu.addAction(self.actionQuickPlot)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.actionQuick3DPlot)
        self.context_menu.addAction(self.actionEditMask)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.actionDelete)


        # Define the callbacks
        self.actionDataInfo.triggered.connect(self.showDataInfo)
        self.actionSaveAs.triggered.connect(self.saveDataAs)
        self.actionQuickPlot.triggered.connect(self.quickDataPlot)
        self.actionQuick3DPlot.triggered.connect(self.quickData3DPlot)
        self.actionEditMask.triggered.connect(self.showEditDataMask)
        self.actionDelete.triggered.connect(self.deleteItem)

    def onCustomContextMenu(self, position):
        """
        Show the right-click context menu in the data treeview
        """
        index = self.current_view.indexAt(position)
        proxy = self.current_view.model()
        model = proxy.sourceModel()

        if index.isValid():
            model_item = model.itemFromIndex(proxy.mapToSource(index))
            # Find the mapped index
            orig_index = model_item.isCheckable()
            if orig_index:
                # Check the data to enable/disable actions
                is_2D = isinstance(GuiUtils.dataFromItem(model_item), Data2D)
                self.actionQuick3DPlot.setEnabled(is_2D)
                self.actionEditMask.setEnabled(is_2D)
                # Fire up the menu
                self.context_menu.exec_(self.current_view.mapToGlobal(position))

    def showDataInfo(self):
        """
        Show a simple read-only text edit with data information.
        """
        index = self.current_view.selectedIndexes()[0]
        proxy = self.current_view.model()
        model = proxy.sourceModel()
        model_item = model.itemFromIndex(proxy.mapToSource(index))

        data = GuiUtils.dataFromItem(model_item)
        if isinstance(data, Data1D):
            text_to_show = GuiUtils.retrieveData1d(data)
            # Hardcoded sizes to enable full width rendering with default font
            self.txt_widget.resize(420,600)
        else:
            text_to_show = GuiUtils.retrieveData2d(data)
            # Hardcoded sizes to enable full width rendering with default font
            self.txt_widget.resize(700,600)

        self.txt_widget.setReadOnly(True)
        self.txt_widget.setWindowFlags(QtCore.Qt.Window)
        self.txt_widget.setWindowIcon(QtGui.QIcon(":/res/ball.ico"))
        self.txt_widget.setWindowTitle("Data Info: %s" % data.filename)
        self.txt_widget.clear()
        self.txt_widget.insertPlainText(text_to_show)

        self.txt_widget.show()
        # Move the slider all the way up, if present
        vertical_scroll_bar = self.txt_widget.verticalScrollBar()
        vertical_scroll_bar.triggerAction(QtWidgets.QScrollBar.SliderToMinimum)

    def saveDataAs(self):
        """
        Save the data points as either txt or xml
        """
        index = self.current_view.selectedIndexes()[0]
        proxy = self.current_view.model()
        model = proxy.sourceModel()
        model_item = model.itemFromIndex(proxy.mapToSource(index))

        data = GuiUtils.dataFromItem(model_item)
        if isinstance(data, Data1D):
            GuiUtils.saveData1D(data)
        else:
            GuiUtils.saveData2D(data)

    def quickDataPlot(self):
        """
        Frozen plot - display an image of the plot
        """
        index = self.current_view.selectedIndexes()[0]
        proxy = self.current_view.model()
        model = proxy.sourceModel()
        model_item = model.itemFromIndex(proxy.mapToSource(index))

        data = GuiUtils.dataFromItem(model_item)

        method_name = 'Plotter'
        if isinstance(data, Data2D):
            method_name='Plotter2D'

        new_plot = globals()[method_name](self, quickplot=True)
        new_plot.data = data
        #new_plot.plot(marker='o')
        new_plot.plot()

        # Update the global plot counter
        title = "Plot " + data.name
        new_plot.setWindowTitle(title)

        # Show the plot
        new_plot.show()

    def quickData3DPlot(self):
        """
        Slowish 3D plot
        """
        index = self.current_view.selectedIndexes()[0]
        proxy = self.current_view.model()
        model = proxy.sourceModel()
        model_item = model.itemFromIndex(proxy.mapToSource(index))

        data = GuiUtils.dataFromItem(model_item)

        new_plot = Plotter2D(self, quickplot=True, dimension=3)
        new_plot.data = data
        new_plot.plot()

        # Update the global plot counter
        title = "Plot " + data.name
        new_plot.setWindowTitle(title)

        # Show the plot
        new_plot.show()

    def showEditDataMask(self):
        """
        Mask Editor for 2D plots
        """
        index = self.current_view.selectedIndexes()[0]
        proxy = self.current_view.model()
        model = proxy.sourceModel()
        model_item = model.itemFromIndex(proxy.mapToSource(index))

        data = GuiUtils.dataFromItem(model_item)

        mask_editor = MaskEditor(self, data)
        # Modal dialog here.
        mask_editor.exec_()

    def deleteItem(self):
        """
        Delete the current item
        """
        # Assure this is indeed wanted
        delete_msg = "This operation will delete the selected data sets." +\
                     "\nDo you want to continue?"
        reply = QtWidgets.QMessageBox.question(self,
                                           'Warning',
                                           delete_msg,
                                           QtWidgets.QMessageBox.Yes,
                                           QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            return

        indices = self.current_view.selectedIndexes()
        proxy = self.current_view.model()
        model = proxy.sourceModel()

        for index in indices:
            row_index = proxy.mapToSource(index)
            item_to_delete = model.itemFromIndex(row_index)
            if item_to_delete and item_to_delete.isCheckable():
                row = row_index.row()
                if item_to_delete.parent():
                    # We have a child item - delete from it
                    item_to_delete.parent().removeRow(row)
                else:
                    # delete directly from model
                    model.removeRow(row)
        pass

    def onAnalysisUpdate(self, new_perspective=""):
        """
        Update the perspective combo index based on passed string
        """
        assert new_perspective in Perspectives.PERSPECTIVES.keys()
        self.cbFitting.blockSignals(True)
        self.cbFitting.setCurrentIndex(self.cbFitting.findText(new_perspective))
        self.cbFitting.blockSignals(False)
        pass

    def loadComplete(self, output):
        """
        Post message to status bar and update the data manager
        """
        assert isinstance(output, tuple)

        # Reset the model so the view gets updated.
        #self.model.reset()
        self.communicator.progressBarUpdateSignal.emit(-1)

        output_data = output[0]
        message = output[1]
        # Notify the manager of the new data available
        self.communicator.statusBarUpdateSignal.emit(message)
        self.communicator.fileDataReceivedSignal.emit(output_data)
        self.manager.add_data(data_list=output_data)

    def loadFailed(self, reason):
        print("File Load Failed with:\n", reason)
        pass

    def updateModel(self, data, p_file):
        """
        Add data and Info fields to the model item
        """
        # Structure of the model
        # checkbox + basename
        #     |-------> Data.D object
        #     |-------> Info
        #                 |----> Title:
        #                 |----> Run:
        #                 |----> Type:
        #                 |----> Path:
        #                 |----> Process
        #                          |-----> process[0].name
        #     |-------> THEORIES

        # Top-level item: checkbox with label
        checkbox_item = GuiUtils.HashableStandardItem()
        checkbox_item.setCheckable(True)
        checkbox_item.setCheckState(QtCore.Qt.Checked)
        checkbox_item.setText(os.path.basename(p_file))

        # Add the actual Data1D/Data2D object
        object_item = GuiUtils.HashableStandardItem()
        object_item.setData(data)

        checkbox_item.setChild(0, object_item)

        # Add rows for display in the view
        info_item = GuiUtils.infoFromData(data)

        # Set info_item as the first child
        checkbox_item.setChild(1, info_item)

        # Caption for the theories
        checkbox_item.setChild(2, QtGui.QStandardItem("THEORIES"))

        # New row in the model
        self.model.beginResetModel()
        self.model.appendRow(checkbox_item)
        self.model.endResetModel()

    def updateModelFromPerspective(self, model_item):
        """
        Receive an update model item from a perspective
        Make sure it is valid and if so, replace it in the model
        """
        # Assert the correct type
        if not isinstance(model_item, QtGui.QStandardItem):
            msg = "Wrong data type returned from calculations."
            raise AttributeError(msg)

        # TODO: Assert other properties

        # Reset the view
        ##self.model.reset()
        # Pass acting as a debugger anchor
        pass

    def updateTheoryFromPerspective(self, model_item):
        """
        Receive an update theory item from a perspective
        Make sure it is valid and if so, replace/add in the model
        """
        # Assert the correct type
        if not isinstance(model_item, QtGui.QStandardItem):
            msg = "Wrong data type returned from calculations."
            raise AttributeError(msg)

        # Check if there are any other items for this tab
        # If so, delete them
        current_tab_name = model_item.text()
        for current_index in range(self.theory_model.rowCount()):
            #if current_tab_name in self.theory_model.item(current_index).text():
            if current_tab_name == self.theory_model.item(current_index).text():
                return
                self.theory_model.removeRow(current_index)
                break

        # send in the new item
        self.theory_model.appendRow(model_item)


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    dlg = DataExplorerWindow()
    dlg.show()
    sys.exit(app.exec_())
