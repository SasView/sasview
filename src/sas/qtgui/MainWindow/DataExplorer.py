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

logger = logging.getLogger(__name__)

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

        # Plot widgets {name:widget}, required to keep track of plots shown as MDI subwindows
        self.plot_widgets = {}

        # Active plots {id:Plotter1D/2D}, required to keep track of currently displayed plots
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
        self.cmdAppend_2.clicked.connect(self.appendPlot)
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
        self.communicator.maskEditorSignal.connect(self.showEditDataMask)
        self.communicator.extMaskEditorSignal.connect(self.extShowEditDataMask)
        self.communicator.changeDataExplorerTabSignal.connect(self.changeTabs)

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

    def changeTabs(self, tab=0):
        """
        Switch tabs of the data explorer
        0: data tab
        1: theory tab
        """
        assert(tab in [0,1])
        self.setCurrentIndex(tab)

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
        deleted_items = []
        deleted_names = []
        while ind < self.model.rowCount():
            ind += 1
            item = self.model.item(ind)

            if item and item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                # Delete these rows from the model
                deleted_names.append(str(self.model.item(ind).text()))
                deleted_items.append(item)

                self.model.removeRow(ind)
                # Decrement index since we just deleted it
                ind -= 1

        # Let others know we deleted data
        self.communicator.dataDeletedSignal.emit(deleted_items)

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

    def freezeCheckedData(self):
        """
        Convert checked results (fitted model, residuals) into separate dataset.
        """
        outer_index = -1
        theories_copied = 0
        orig_model_size = self.model.rowCount()
        while outer_index < orig_model_size:
            outer_index += 1
            outer_item = self.model.item(outer_index)
            if not outer_item:
                continue
            if not outer_item.isCheckable():
                continue
            # Look for checked inner items
            inner_index = -1
            while inner_index < outer_item.rowCount():
               inner_item = outer_item.child(inner_index)
               inner_index += 1
               if not inner_item:
                   continue
               if not inner_item.isCheckable():
                   continue
               if inner_item.checkState() != QtCore.Qt.Checked:
                   continue
               self.model.beginResetModel()
               theories_copied += 1
               new_item = self.cloneTheory(inner_item)
               self.model.appendRow(new_item)
               self.model.endResetModel()

        freeze_msg = ""
        if theories_copied == 0:
            return
        elif theories_copied == 1:
            freeze_msg = "1 theory copied to a separate data set"
        elif theories_copied > 1:
            freeze_msg = "%i theories copied to separate data sets" % theories_copied
        else:
            freeze_msg = "Unexpected number of theories copied: %i" % theories_copied
            raise AttributeError(freeze_msg)
        self.communicator.statusBarUpdateSignal.emit(freeze_msg)

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
                new_item = self.cloneTheory(outer_item)
                self.model.appendRow(new_item)
                self.model.endResetModel()

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

    def cloneTheory(self, item_from):
        """
        Manually clone theory items into a new HashableItem
        """
        new_item = GuiUtils.HashableStandardItem()
        new_item.setCheckable(True)
        new_item.setCheckState(QtCore.Qt.Checked)
        info_item = QtGui.QStandardItem("Info")
        data_item = QtGui.QStandardItem()
        data_item.setData(item_from.child(0).data())
        new_item.setText(item_from.text())
        new_item.setChild(0, data_item)
        new_item.setChild(1, info_item)
        # Append a "unique" descriptor to the name
        time_bit = str(time.time())[7:-1].replace('.', '')
        new_name = new_item.text() + '_@' + time_bit
        new_item.setText(new_name)
        # Change the underlying data so it is no longer a theory
        try:
            new_item.child(0).data().is_data = True
        except AttributeError:
            #no data here, pass
            pass
        return new_item

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

    def displayFile(self, filename=None, is_data=True, id=None):
        """
        Forces display of charts for the given filename
        """
        model = self.model if is_data else self.theory_model
        # Now query the model item for available plots
        plots = GuiUtils.plotsFromFilename(filename, model)
        # Each fitpage contains the name based on fit widget number
        fitpage_name = "" if id is None else "M"+str(id)
        new_plots = []
        for item, plot in plots.items():
            if self.updatePlot(plot):
                # Don't create plots which are already displayed
                continue
            # Don't plot intermediate results, e.g. P(Q), S(Q)
            match = GuiUtils.theory_plot_ID_pattern.match(plot.id)
            # 2nd match group contains the identifier for the intermediate result, if present (e.g. "[P(Q)]")
            if match and match.groups()[1] != None:
                continue
            # Don't include plots from different fitpages, but always include the original data
            if fitpage_name in plot.name or filename in plot.name or filename == plot.filename:
                # Residuals get their own plot
                if plot.plot_role == Data1D.ROLE_RESIDUAL:
                    plot.yscale='linear'
                    self.plotData([(item, plot)])
                else:
                    new_plots.append((item, plot))

        if new_plots:
            self.plotData(new_plots)

    def displayData(self, data_list, id=None):
        """
        Forces display of charts for the given data set
        """
        plot_to_show = data_list[0]
        # passed plot is used ONLY to figure out its title,
        # so all the charts related by it can be pulled from 
        # the data explorer indices.
        filename = plot_to_show.filename
        self.displayFile(filename=filename, is_data=plot_to_show.is_data, id=id)

    def addDataPlot2D(self, plot_set, item):
        """
        Create a new 2D plot and add it to the workspace
        """
        plot2D = Plotter2D(self)
        plot2D.item = item
        plot2D.plot(plot_set)
        self.addPlot(plot2D)
        self.active_plots[plot2D.data.name] = plot2D
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

    def plotData(self, plots, transform=True):
        """
        Takes 1D/2D data and generates a single plot (1D) or multiple plots (2D)
        """
        # Call show on requested plots
        # All same-type charts in one plot
        for item, plot_set in plots:
            if isinstance(plot_set, Data1D):
                if not 'new_plot' in locals():
                    new_plot = Plotter(self)
                    new_plot.item = item
                new_plot.plot(plot_set, transform=transform)
                # active_plots may contain multiple charts
                self.active_plots[plot_set.name] = new_plot
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
        plot_widget = self.parent.workspace().addSubWindow(new_plot)

        # Show the plot
        new_plot.show()
        new_plot.canvas.draw()

        # Update the plot widgets dict
        self.plot_widgets[title]=plot_widget

        # Update the active chart list
        self.active_plots[new_plot.data.name] = new_plot

    def appendPlot(self):
        """
        Add data set(s) to the existing matplotlib chart
        """
        # new plot data; check which tab is currently active
        if self.current_view == self.treeView:
            new_plots = GuiUtils.plotsFromCheckedItems(self.model)
        else:
            new_plots = GuiUtils.plotsFromCheckedItems(self.theory_model)

        # old plot data
        plot_id = str(self.cbgraph.currentText())
        try:
            assert plot_id in PlotHelper.currentPlots(), "No such plot: %s"%(plot_id)
        except:
            return

        old_plot = PlotHelper.plotById(plot_id)

        # Add new data to the old plot, if data type is the same.
        for _, plot_set in new_plots:
            if type(plot_set) is type(old_plot._data):
                old_plot.data = plot_set
                old_plot.plot()
                # need this for lookup - otherwise this plot will never update
                self.active_plots[plot_set.name] = old_plot

    def updatePlot(self, data):
        """
        Modify existing plot for immediate response and returns True.
        Returns false, if the plot does not exist already.
        """
        try: # there might be a list or a single value being passed
            data = data[0]
        except TypeError:
            pass
        assert type(data).__name__ in ['Data1D', 'Data2D']

        ids_keys = list(self.active_plots.keys())
        ids_vals = [val.data.name for val in self.active_plots.values()]

        data_id = data.name
        if data_id in ids_keys:
            # We have data, let's replace data that needs replacing
            if data.plot_role != Data1D.ROLE_DATA:
                self.active_plots[data_id].replacePlot(data_id, data)
            return True
        elif data_id in ids_vals:
            if data.plot_role != Data1D.ROLE_DATA:
                list(self.active_plots.values())[ids_vals.index(data_id)].replacePlot(data_id, data)
            return True
        return False

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

    def setItemsCheckability(self, model, dimension=None, checked=False):
        """
        For a given model, check or uncheck all items of given dimension
        """
        mode = QtCore.Qt.Checked if checked else QtCore.Qt.Unchecked

        assert isinstance(checked, bool)

        types = (None, Data1D, Data2D)
        assert dimension in types

        for index in range(model.rowCount()):
            item = model.item(index)
            if dimension is not None and not isinstance(GuiUtils.dataFromItem(item), dimension):
                continue
            if item.isCheckable() and item.checkState() != mode:
                item.setCheckState(mode)
            # look for all children
            for inner_index in range(item.rowCount()):
                child = item.child(inner_index)
                if child.isCheckable() and child.checkState() != mode:
                    child.setCheckState(mode)

    def selectData(self, index):
        """
        Callback method for modifying the TreeView on Selection Options change
        """
        if not isinstance(index, int):
            msg = "Incorrect type passed to DataExplorer.selectData()"
            raise AttributeError(msg)

        # Respond appropriately
        if index == 0:
            self.setItemsCheckability(self.model, checked=True)

        elif index == 1:
            # De-select All
            self.setItemsCheckability(self.model, checked=False)

        elif index == 2:
            # Select All 1-D
            self.setItemsCheckability(self.model, dimension=Data1D, checked=True)

        elif index == 3:
            # Unselect All 1-D
            self.setItemsCheckability(self.model, dimension=Data1D, checked=False)

        elif index == 4:
            # Select All 2-D
            self.setItemsCheckability(self.model, dimension=Data2D, checked=True)

        elif index == 5:
            # Unselect All 2-D
            self.setItemsCheckability(self.model, dimension=Data2D, checked=False)

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
        #self.context_menu.addSeparator()
        #self.context_menu.addAction(self.actionFreezeResults)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.actionDelete)


        # Define the callbacks
        self.actionDataInfo.triggered.connect(self.showDataInfo)
        self.actionSaveAs.triggered.connect(self.saveDataAs)
        self.actionQuickPlot.triggered.connect(self.quickDataPlot)
        self.actionQuick3DPlot.triggered.connect(self.quickData3DPlot)
        self.actionEditMask.triggered.connect(self.showEditDataMask)
        self.actionDelete.triggered.connect(self.deleteItem)
        self.actionFreezeResults.triggered.connect(self.freezeSelectedItems)

    def onCustomContextMenu(self, position):
        """
        Show the right-click context menu in the data treeview
        """
        index = self.current_view.indexAt(position)
        proxy = self.current_view.model()
        model = proxy.sourceModel()

        if not index.isValid():
            return
        model_item = model.itemFromIndex(proxy.mapToSource(index))
        # Find the mapped index
        orig_index = model_item.isCheckable()
        if not orig_index:
            return
        # Check the data to enable/disable actions
        is_2D = isinstance(GuiUtils.dataFromItem(model_item), Data2D)
        self.actionQuick3DPlot.setEnabled(is_2D)
        self.actionEditMask.setEnabled(is_2D)

        # Freezing
        # check that the selection has inner items
        freeze_enabled = False
        if model_item.parent() is not None:
            freeze_enabled = True
        self.actionFreezeResults.setEnabled(freeze_enabled)

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

        self.new_plot = globals()[method_name](self, quickplot=True)
        self.new_plot.data = data
        #new_plot.plot(marker='o')
        self.new_plot.plot()

        # Update the global plot counter
        title = "Plot " + data.name
        self.new_plot.setWindowTitle(title)

        # Show the plot
        self.new_plot.show()

    def quickData3DPlot(self):
        """
        Slowish 3D plot
        """
        index = self.current_view.selectedIndexes()[0]
        proxy = self.current_view.model()
        model = proxy.sourceModel()
        model_item = model.itemFromIndex(proxy.mapToSource(index))

        data = GuiUtils.dataFromItem(model_item)

        self.new_plot = Plotter2D(self, quickplot=True, dimension=3)
        self.new_plot.data = data
        self.new_plot.plot()

        # Update the global plot counter
        title = "Plot " + data.name
        self.new_plot.setWindowTitle(title)

        # Show the plot
        self.new_plot.show()

    def extShowEditDataMask(self):
        self.showEditDataMask()

    def showEditDataMask(self, data=None):
        """
        Mask Editor for 2D plots
        """
        try:
            if data is None or not isinstance(data, Data2D):
                index = self.current_view.selectedIndexes()[0]
                proxy = self.current_view.model()
                model = proxy.sourceModel()
                model_item = model.itemFromIndex(proxy.mapToSource(index))

                data = GuiUtils.dataFromItem(model_item)

            if data is None or not isinstance(data, Data2D):
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Information)
                msg.setText("Error: cannot apply mask. \
                                Please select a 2D dataset.")
                msg.setStandardButtons(QtWidgets.QMessageBox.Cancel)
                msg.exec_()
                return
        except:
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("Error: No dataset selected. \
                            Please select a 2D dataset.")
            msg.setStandardButtons(QtWidgets.QMessageBox.Cancel)
            msg.exec_()
            return

        mask_editor = MaskEditor(self, data)
        # Modal dialog here.
        mask_editor.exec_()

    def freezeItem(self, item=None):
        """
        Freeze given item
        """
        if item is None:
            return
        self.model.beginResetModel()
        new_item = self.cloneTheory(item)
        self.model.appendRow(new_item)
        self.model.endResetModel()

    def freezeSelectedItems(self):
        """
        Freeze selected items
        """
        indices = self.treeView.selectedIndexes()

        proxy = self.treeView.model()
        model = proxy.sourceModel()

        for index in indices:
            row_index = proxy.mapToSource(index)
            item_to_copy = model.itemFromIndex(row_index)
            if item_to_copy and item_to_copy.isCheckable():
                self.freezeItem(item_to_copy)

    def deleteItem(self):
        """
        Delete the current item
        """
        # Assure this is indeed wanted
        delete_msg = "This operation will delete the selected data sets " +\
                     "and all the dependents." +\
                     "\nDo you want to continue?"
        reply = QtWidgets.QMessageBox.question(self,
                                           'Warning',
                                           delete_msg,
                                           QtWidgets.QMessageBox.Yes,
                                           QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.No:
            return

        # Every time a row is removed, the indices change, so we'll just remove
        # rows and keep calling selectedIndexes until it returns an empty list.
        indices = self.current_view.selectedIndexes()

        proxy = self.current_view.model()
        model = proxy.sourceModel()

        deleted_items = []
        deleted_names = []

        while len(indices) > 0:
            index = indices[0]
            row_index = proxy.mapToSource(index)
            item_to_delete = model.itemFromIndex(row_index)
            if item_to_delete and item_to_delete.isCheckable():
                row = row_index.row()

                # store the deleted item details so we can pass them on later
                deleted_names.append(item_to_delete.text())
                deleted_items.append(item_to_delete)

                # Delete corresponding open plots
                self.closePlotsForItem(item_to_delete)

                if item_to_delete.parent():
                    # We have a child item - delete from it
                    item_to_delete.parent().removeRow(row)
                else:
                    # delete directly from model
                    model.removeRow(row)
            indices = self.current_view.selectedIndexes()

        # Let others know we deleted data
        self.communicator.dataDeletedSignal.emit(deleted_items)

        # update stored_data
        self.manager.update_stored_data(deleted_names)

    def closePlotsForItem(self, item):
        """
        Given standard item, close all its currently displayed plots
        """
        # item - HashableStandardItems of active plots

        # {} -> 'Graph1' : HashableStandardItem()
        current_plot_items = {}
        for plot_name in PlotHelper.currentPlots():
            current_plot_items[plot_name] = PlotHelper.plotById(plot_name).item

        # item and its hashable children
        items_being_deleted = []
        if item.rowCount() > 0:
            items_being_deleted = [item.child(n) for n in range(item.rowCount())
                                   if isinstance(item.child(n), GuiUtils.HashableStandardItem)]
        items_being_deleted.append(item)
        # Add the parent in case a child is selected
        if isinstance(item.parent(), GuiUtils.HashableStandardItem):
            items_being_deleted.append(item.parent())

        # Compare plot items and items to delete
        plots_to_close = set(current_plot_items.values()) & set(items_being_deleted)

        for plot_item in plots_to_close:
            for plot_name in current_plot_items.keys():
                if plot_item == current_plot_items[plot_name]:
                    plotter = PlotHelper.plotById(plot_name)
                    # try to delete the plot
                    try:
                        plotter.close()
                        #self.parent.workspace().removeSubWindow(plotter)
                        self.plot_widgets[plot_name].close()
                        self.plot_widgets.pop(plot_name, None)
                    except AttributeError as ex:
                        logging.error("Closing of %s failed:\n %s" % (plot_name, str(ex)))

        pass # debugger anchor

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
        checkbox_item.setChild(2, QtGui.QStandardItem("FIT RESULTS"))

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
                self.theory_model.removeRow(current_index)
                break

        # send in the new item
        self.theory_model.appendRow(model_item)

    def deleteIntermediateTheoryPlotsByModelID(self, model_id):
        """Given a model's ID, deletes all items in the theory item model which reference the same ID. Useful in the
        case of intermediate results disappearing when changing calculations (in which case you don't want them to be
        retained in the list)."""
        items_to_delete = []
        for r in range(self.theory_model.rowCount()):
            item = self.theory_model.item(r, 0)
            data = item.child(0).data()
            if not hasattr(data, "id"):
                return
            match = GuiUtils.theory_plot_ID_pattern.match(data.id)
            if match:
                item_model_id = match.groups()[-1]
                if item_model_id == model_id:
                    # Only delete those identified as an intermediate plot
                    if match.groups()[2] not in (None, ""):
                        items_to_delete.append(item)

        for item in items_to_delete:
            self.theory_model.removeRow(item.row())
