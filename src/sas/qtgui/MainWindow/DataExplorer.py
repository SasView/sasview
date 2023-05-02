# pylint: disable=E501, E203, E701
# global
import sys
import os
import time
import logging
import copy

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
from sas.qtgui.MainWindow.NameChanger import ChangeName

import sas.qtgui.Perspectives as Perspectives

DEFAULT_PERSPECTIVE = "Fitting"
ANALYSIS_TYPES = ['Fitting (*.fitv)', 'Inversion (*.pr)', 'Invariant (*.inv)',
                  'Corfunc (*.crf)', 'All Files (*.*)']

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

        # Read in default locations
        self.default_save_location = None
        self.default_load_location = GuiUtils.DEFAULT_OPEN_FOLDER
        self.default_project_location = None

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
        self.cbSelect.activated.connect(self.selectData)

        self.currentChanged.connect(self.onTabSwitch)
        self.communicator = self.parent.communicator()
        self.communicator.fileReadSignal.connect(self.loadFromURL)
        self.communicator.activeGraphsSignal.connect(self.updateGraphCount)
        self.communicator.activeGraphName.connect(self.updatePlotName)
        self.communicator.plotUpdateSignal.connect(self.updatePlot)
        self.communicator.maskEditorSignal.connect(self.showEditDataMask)
        self.communicator.extMaskEditorSignal.connect(self.extShowEditDataMask)
        self.communicator.changeDataExplorerTabSignal.connect(self.changeTabs)
        self.communicator.forcePlotDisplaySignal.connect(self.displayData)
        self.communicator.updateModelFromPerspectiveSignal.connect(self.updateModelFromPerspective)

        # fixing silly naming clash in other managers
        self.communicate = self.communicator

        self.cbgraph.editTextChanged.connect(self.enableGraphCombo)
        self.cbgraph.currentIndexChanged.connect(self.enableGraphCombo)

        self.cbgraph_2.editTextChanged.connect(self.enableGraphCombo)
        self.cbgraph_2.currentIndexChanged.connect(self.enableGraphCombo)

        # Proxy model for showing a subset of Data1D/Data2D content
        self.data_proxy = QtCore.QSortFilterProxyModel(self)
        self.data_proxy.setSourceModel(self.model)

        # Slots for model changes
        self.model.itemChanged.connect(self.onFileListChanged)
        self.theory_model.itemChanged.connect(self.onFileListChanged)

        # Don't show "empty" rows with data objects
        self.data_proxy.setFilterRegExp(r"[^()]")

        # Create a window to allow the display name to change
        self.nameChangeBox = ChangeName(self)

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
        assert(tab in [0, 1])
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
        kwargs = {
            'parent'    : self,
            'caption'   : 'Choose a directory',
            'options'   : QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontUseNativeDialog,
            'directory' : self.default_load_location
        }
        folder = QtWidgets.QFileDialog.getExistingDirectory(**kwargs)

        if folder is None:
            return

        folder = str(folder)
        if not os.path.isdir(folder):
            return
        self.default_load_location = folder
        # get content of dir into a list
        path_str = [os.path.join(os.path.abspath(folder), filename)
                    for filename in os.listdir(folder)]

        self.loadFromURL(path_str)

    def loadProject(self):
        """
        Called when the "Open Project" menu item chosen.
        """
        # check if any items loaded and warn about data deletion
        if self.model.rowCount() > 0:
            msg = "This operation will remove all data, plots and analyses from"
            msg += " SasView before loading the project. Do you wish to continue?"
            msgbox = QtWidgets.QMessageBox(self)
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.setText(msg)
            msgbox.setWindowTitle("Project Load")
            # custom buttons
            button_yes = QtWidgets.QPushButton("Yes")
            msgbox.addButton(button_yes, QtWidgets.QMessageBox.YesRole)
            button_no = QtWidgets.QPushButton("No")
            msgbox.addButton(button_no, QtWidgets.QMessageBox.RejectRole)
            retval = msgbox.exec_()
            if retval == QtWidgets.QMessageBox.RejectRole:
                # cancel fit
                return

        kwargs = {
            'parent'    : self,
            'caption'   : 'Open Project',
            'filter'    : 'Project Files (*.json);;Old Project Files (*.svs);;All files (*.*)',
            'options'   : QtWidgets.QFileDialog.DontUseNativeDialog
        }
        filename = QtWidgets.QFileDialog.getOpenFileName(**kwargs)[0]
        if filename:
            self.default_project_location = os.path.dirname(filename)
            # Delete all data and initialize all perspectives
            self.deleteAllItems()
            self.cbFitting.disconnect()
            self.parent.loadAllPerspectives()
            self.initPerspectives()
            self.readProject(filename)

    def loadAnalysis(self):
        """
        Called when the "Open Analysis" menu item chosen.
        """
        file_filter = ';;'.join(ANALYSIS_TYPES)
        kwargs = {
            'parent'    : self,
            'caption'   : 'Open Analysis',
            'filter'    : file_filter,
            'options'   : QtWidgets.QFileDialog.DontUseNativeDialog
        }
        filename = QtWidgets.QFileDialog.getOpenFileName(**kwargs)[0]
        if filename:
            self.readProject(filename)

    def saveProject(self):
        """
        Called when the "Save Project" menu item chosen.
        """
        kwargs = {
            'parent'    : self,
            'caption'   : 'Save Project',
            'filter'    : 'Project (*.json)',
            'options'   : QtWidgets.QFileDialog.DontUseNativeDialog,
            'directory' : self.default_project_location
        }
        name_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
        filename = name_tuple[0]
        if not filename:
            return
        self.default_project_location = os.path.dirname(filename)
        _, extension = os.path.splitext(filename)
        if not extension:
            filename = '.'.join((filename, 'json'))
        self.communicator.statusBarUpdateSignal.emit("Saving Project... %s\n" % os.path.basename(filename))

        return filename

    def saveAsAnalysisFile(self, tab_id=1, extension='fitv'):
        """
        Show the save as... dialog and return the chosen filepath
        """
        default_name = "Analysis"+str(tab_id)+"."+str(extension)

        wildcard = "{0} files (*.{0})".format(extension)
        kwargs = {
            'caption'   : 'Save As',
            'directory' : default_name,
            'filter'    : wildcard,
            'parent'    : None,
        }
        # Query user for filename.
        filename_tuple = QtWidgets.QFileDialog.getSaveFileName(**kwargs)
        filename = filename_tuple[0]
        return filename

    def saveAnalysis(self, data, tab_id=1, ext='fitv'):
        """
        Called when the "Save Analysis" menu item chosen.
        """
        filename = self.saveAsAnalysisFile(tab_id, ext)
        if not filename:
            return
        _, extension = os.path.splitext(filename)
        if not extension:
            filename = '.'.join((filename, ext))
        self.communicator.statusBarUpdateSignal.emit("Saving analysis... %s\n" % os.path.basename(filename))

        with open(filename, 'w') as outfile:
            GuiUtils.saveData(outfile, data)

        self.communicator.statusBarUpdateSignal.emit('Analysis saved.')

    def flatDataForModel(self, model):
        """
        Get a flat "name:data1d/2d" dict for all
        items in the model, including children
        """
        all_data = {}
        for i in range(model.rowCount()):
            item = model.item(i)
            data = GuiUtils.dataFromItem(item)
            if data is None: continue
            # Now, all plots under this item
            name = data.name
            all_data[name] = data
            other_datas = GuiUtils.plotsFromDisplayName(name, model)
            # skip the main plot
            other_datas = list(other_datas.values())[1:]
            for data in other_datas:
                all_data[data.name] = data

        return all_data

    def getAllFlatData(self):
        """
        Get items from both data and theory models
        """
        data = self.flatDataForModel(self.model)
        theory = self.flatDataForModel(self.theory_model)
        return (data, theory)

    def allDataForModel(self, model):
        # data model
        all_data = {}
        for i in range(model.rowCount()):
            properties = {}
            item = model.item(i)
            data = GuiUtils.dataFromItem(item)
            if data is None: continue
            # Now, all plots under this item
            name = data.name
            is_checked = item.checkState()
            properties['checked'] = is_checked
            # save underlying theories
            other_datas = GuiUtils.plotsFromDisplayName(name, model)
            # skip the main plot
            other_datas = list(other_datas.values())[1:]
            all_data[data.id] = [data, properties, other_datas]
        return all_data

    def getDataForID(self, id):
        # return the dataset with the given ID
        all_data = []
        for model in (self.model, self.theory_model):
            for i in range(model.rowCount()):
                properties = {}
                item = model.item(i)
                data = GuiUtils.dataFromItem(item)
                if data is None: continue
                if data.id != id: continue
                # We found the dataset - save it.
                name = data.name
                is_checked = item.checkState()
                properties['checked'] = is_checked
                other_datas = GuiUtils.plotsFromDisplayName(name, model)
                # skip the main plot
                other_datas = list(other_datas.values())[1:]
                all_data = [data, properties, other_datas]
                break
        return all_data

    def getItemForID(self, id):
        # return the model item with the given ID
        item = None
        for model in (self.model, self.theory_model):
            for i in range(model.rowCount()):
                data = GuiUtils.dataFromItem(model.item(i))
                if data is None: continue
                if data.id != id: continue
                # We found the item - return it
                item = model.item(i)
                break
        return item

    def getAllData(self):
        """
        Get items from both data and theory models
        """
        data = self.allDataForModel(self.model)
        theory = self.allDataForModel(self.theory_model)
        return (data, theory)

    def getSerializedData(self):
        """
        converts all datasets into serializable dictionary
        """
        data, theory = self.getAllData()
        all_data = {}
        all_data['is_batch'] = str(self.chkBatch.isChecked())

        for key, value in data.items():
            all_data[key] = value
        for key, value in theory.items():
            if key in all_data:
                raise ValueError("Inconsistent data in Project file.")
            all_data[key] = value
        return all_data

    def saveDataToFile(self, outfile):
        """
        Save every dataset to a json file
        """
        all_data = self.getAllData()
        # save datas
        GuiUtils.saveData(outfile, all_data)

    def readProject(self, filename):
        """
        Read out datasets and perspective information from file
        """
        # Find out the filetype based on extension
        ext = os.path.splitext(filename)[1]
        all_data = {}
        if 'svs' in ext.lower():
            # backward compatibility mode.
            try:
                datasets = GuiUtils.readProjectFromSVS(filename)
            except Exception as ex:
                # disregard malformed SVS and try to recover whatever
                # is available
                msg = "Error while reading the project file: " + str(ex)
                logging.error(msg)
                pass
            # Convert fitpage properties and update the dict
            try:
                all_data = GuiUtils.convertFromSVS(datasets)
            except Exception as ex:
                # disregard malformed SVS and try to recover regardless
                msg = "Error while converting the project file: " + str(ex)
                logging.error(msg)
                pass
        else:
            with open(filename, 'r') as infile:
                try:
                    all_data = GuiUtils.readDataFromFile(infile)
                except Exception as ex:
                    logging.error("Project load failed with " + str(ex))
                    return
        cs_keys = []
        visible_perspective = DEFAULT_PERSPECTIVE
        for key, value in all_data.items():
            if key == 'is_batch':
                self.chkBatch.setChecked(value == 'True')
                if 'batch_grid' in all_data:
                    grid_pages = all_data['batch_grid']
                    for grid_name, grid_page in grid_pages.items():
                        grid_page.append(grid_name)
                        self.parent.showBatchOutput(grid_page)
                continue
            # Store constraint pages until all individual fits are open
            if 'cs_tab' in key:
                cs_keys.append(key)
                continue
            # Load last visible perspective as stored in project file
            if 'visible_perspective' in key:
                visible_perspective = value
            # send newly created items to the perspective
            self.updatePerspectiveWithProperties(key, value)
        # Set to fitting perspective and load in Batch and C&S Pages
        self.cbFitting.setCurrentIndex(
            self.cbFitting.findText(DEFAULT_PERSPECTIVE))
        # See if there are any batch pages defined and create them, if so
        self.updateWithBatchPages(all_data)
        # Get the constraint dict and apply it
        constraint_dict = GuiUtils.getConstraints(all_data)
        self._perspective().updateFromConstraints(constraint_dict)
        # Only now can we create/assign C&S pages.
        for key in cs_keys:
            self.updatePerspectiveWithProperties(key, all_data[key])

        # Set to perspective shown when project was saved
        self.cbFitting.setCurrentIndex(
                self.cbFitting.findText(visible_perspective))

    def updateWithBatchPages(self, all_data):
        """
        Checks all properties and see if there are any batch pages defined.
        If so, pull out relevant indices and recreate the batch page(s)
        """
        batch_pages = []
        for key, value in all_data.items():
            if 'fit_params' not in value:
                continue
            params = value['fit_params']
            for page in params:
                if not isinstance(page, dict):
                    continue
                if 'is_batch_fitting' not in page:
                    continue
                if page['is_batch_fitting'][0] != 'True':
                    continue
                batch_ids = page['data_id'][0]
                # check for duplicates
                batch_set = set(batch_ids)
                if batch_set in batch_pages:
                    continue
                # Found a unique batch page. Send it away
                items = [self.getItemForID(i) for i in batch_set]
                # Update the batch page list
                batch_pages.append(batch_set)
                # Assign parameters to the most recent (current) page.
                self._perspective().setData(data_item=items, is_batch=True)
                self._perspective().updateFromParameters(page)
        pass

    def updatePerspectiveWithProperties(self, key, value):
        """
        """
        if 'fit_data' in value:
            data_dict = {key: value['fit_data']}
            # Create new model items in the data explorer
            items = self.updateModelFromData(data_dict)

        if 'fit_params' in value:
            self.cbFitting.setCurrentIndex(self.cbFitting.findText(DEFAULT_PERSPECTIVE))
            params = value['fit_params']
            # Make the perspective read the rest of the read data
            if not isinstance(params, list):
                params = [params]
            for page in params:
                # Check if this set of parameters is for a batch page
                # if so, skip the update
                if page['is_batch_fitting'][0] == 'True':
                    continue
                tab_index = None
                if 'tab_index' in page:
                    tab_index = page['tab_index'][0]
                    tab_index = int(tab_index)
                # Send current model item to the perspective
                self.sendItemToPerspective(items[0], tab_index=tab_index)
                # Assign parameters to the most recent (current) page.
                self._perspective().updateFromParameters(page)
        if 'pr_params' in value:
            self.cbFitting.setCurrentIndex(self.cbFitting.findText('Inversion'))
            params = value['pr_params']
            self.sendItemToPerspective(items[0])
            self._perspective().updateFromParameters(params)
        if 'invar_params' in value:
            self.cbFitting.setCurrentIndex(self.cbFitting.findText('Invariant'))
            self.sendItemToPerspective(items[0])
            self._perspective().updateFromParameters(value['invar_params'])
        if 'corfunc_params' in value:
            self.cbFitting.setCurrentIndex(self.cbFitting.findText('Corfunc'))
            self.sendItemToPerspective(items[0])
            self._perspective().updateFromParameters(value['corfunc_params'])
        if 'cs_tab' in key and 'is_constraint' in value:
            # Create a C&S page
            self._perspective().addConstraintTab()
            # Modify the tab
            self._perspective().updateFromParameters(value)

        pass  # debugger

    def updateModelFromData(self, data):
        """
        Given data from analysis/project file,
        create indices and populate data/theory models
        """
        # model items for top level datasets
        items = []
        for key, value in data.items():
            # key - cardinal number of dataset
            # value - main dataset, [dependant filesets]
            # add the main index
            if not value: continue
            new_data = value[0]
            from sas.sascalc.dataloader.data_info import Data1D as old_data1d
            from sas.sascalc.dataloader.data_info import Data2D as old_data2d
            if isinstance(new_data, (old_data1d, old_data2d)):
                new_data = self.manager.create_gui_data(value[0], new_data.name)
            if hasattr(value[0], 'id'):
                new_data.id = value[0].id
                new_data.group_id = value[0].group_id
            assert isinstance(new_data, (Data1D, Data2D))
            # make sure the ID is retained
            properties = value[1]
            is_checked = properties['checked']
            new_item = GuiUtils.createModelItemWithPlot(new_data, new_data.name)
            new_item.setCheckState(is_checked)
            items.append(new_item)
            model = self.theory_model
            if new_data.is_data:
                model = self.model
                # Caption for the theories
                new_item.setChild(2, QtGui.QStandardItem("FIT RESULTS"))

            model.appendRow(new_item)
            self.manager.add_data(data_list={new_data.id: new_data})

            # Add the underlying data
            if not value[2]:
                continue
            for plot in value[2]:
                assert isinstance(plot, (Data1D, Data2D))
                GuiUtils.updateModelItemWithPlot(new_item, plot, plot.name)
        return items

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

                # Delete corresponding open plots
                self.closePlotsForItem(item)
                # Close result panel if results represent the deleted data item
                # Results panel only stores Data1D/Data2D object
                #   => QStandardItems must still exist for direct comparison
                self.closeResultPanelOnDelete(GuiUtils.dataFromItem(item))

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

        deleted_items = []
        deleted_names = []
        while ind < self.theory_model.rowCount():
            ind += 1
            item = self.theory_model.item(ind)

            if item and item.isCheckable() and item.checkState() == QtCore.Qt.Checked:
                # Delete these rows from the model
                deleted_names.append(str(self.theory_model.item(ind).text()))
                deleted_items.append(item)
                self.closePlotsForItem(item)

                self.theory_model.removeRow(ind)
                # Decrement index since we just deleted it
                ind -= 1

        # Let others know we deleted data
        self.communicator.dataDeletedSignal.emit(deleted_items)

        # update stored_data
        self.manager.update_stored_data(deleted_names)

    def sendData(self, event=None):
        """
        Send selected item data to the current perspective and set the relevant notifiers
        """
        def isItemReady(index):
            item = self.model.item(index)
            return item.isCheckable() and item.checkState() == QtCore.Qt.Checked

        # Figure out which rows are checked
        selected_items = [self.model.item(index)
                          for index in range(self.model.rowCount())
                          if isItemReady(index)]

        if len(selected_items) < 1:
            return
        #Check that you have only one box item checked when swaping data
        if len(selected_items) > 1 and (self.chkSwap.isChecked() or not self._perspective().allowBatch()):
            if hasattr(self._perspective(), 'name'):
                title = self._perspective().name
            else:
                title = self._perspective().windowTitle()
            msg = title + " does not allow replacing multiple data."
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.setText(msg)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            _ = msgbox.exec_()
            return

        # Notify the GuiManager about the send request
        try:
            if self.chkSwap.isChecked():
                self._perspective().swapData(selected_items[0])
            else:
                self._perspective().setData(data_item=selected_items, is_batch=self.chkBatch.isChecked())
        except Exception as ex:
            msg = "%s perspective returned the following message: \n%s\n" % (self._perspective().name, str(ex))
            logging.error(msg)
            msg = str(ex)
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.setText(msg)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            _ = msgbox.exec_()

    def sendItemToPerspective(self, item, tab_index=None):
        """
        Send the passed item data to the current perspective and set the relevant notifiers
        """
        # Set the signal handlers
        self.communicator.updateModelFromPerspectiveSignal.connect(self.updateModelFromPerspective)
        selected_items = [item]
        # Notify the GuiManager about the send request
        try:
            if tab_index is None:
                self._perspective().setData(data_item=selected_items, is_batch=False)
            else:
                self._perspective().setData(data_item=selected_items, is_batch=False, tab_index=tab_index)
        except Exception as ex:
            msg = "%s perspective returned the following message: \n%s\n" % (self._perspective().name, str(ex))
            logging.error(msg)
            msg = str(ex)
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.setText(msg)
            msgbox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            _ = msgbox.exec_()

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
            if outer_item.isCheckable() and outer_item.checkState() == QtCore.Qt.Checked:
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
        orig_data = copy.deepcopy(item_from.child(0).data())
        data_item.setData(orig_data)
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
            new_item.child(0).data().symbol = 'Circle'
            new_item.child(0).data().id = new_name
        except AttributeError:
            # no data here, pass
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
        graph = self.cbgraph
        if self.current_view == self.freezeView:
            graph = self.cbgraph_2
        ind = graph.findText(old_name)
        graph.setCurrentIndex(ind)
        graph.setItemText(ind, current_name)

    def add_data(self, data_list):
        """
        Update the data manager with new items
        """
        self.manager.add_data(data_list)

    def updateGraphCount(self, graphs):
        """
        Modify the graph name combo and potentially remove
        deleted graphs
        """
        graph2, delete = graphs
        graph_list = PlotHelper.currentPlots()
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
        graph = self.cbgraph
        if self.current_view == self.freezeView:
            graph = self.cbgraph_2
        orig_text = graph.currentText()
        graph.clear()
        graph.insertItems(0, graph_list)
        ind = graph.findText(orig_text)
        if ind > 0:
            graph.setCurrentIndex(ind)

    def updatePerspectiveCombo(self, index):
        """
        Notify the gui manager about the new perspective chosen.
        """
        self.communicator.perspectiveChangedSignal.emit(self.cbFitting.itemText(index))
        self.chkBatch.setEnabled(self.parent.perspective().allowBatch())
        # Deactivate and uncheck the swap data option if the current perspective does not allow it
        self.chkSwap.setEnabled(self.parent.perspective().allowSwap())
        if not self.parent.perspective().allowSwap():
            self.chkSwap.setCheckState(False)

    def itemFromDisplayName(self, name):
        """
        Retrieves model item corresponding to the given display name
        """
        item = GuiUtils.itemFromDisplayName(name, self.model)
        return item

    def displayDataByName(self, name=None, is_data=True, id=None):
        """
        Forces display of charts for the given name
        """
        model = self.model if is_data else self.theory_model
        # Now query the model item for available plots
        plots = GuiUtils.plotsFromDisplayName(name, model)
        # Each fitpage contains the name based on fit widget number
        fitpage_name = "" if id is None else "M" + str(id)
        new_plots = []
        for item, plot in plots.items():
            if self.updatePlot(plot):
                # Don't create plots which are already displayed
                continue
            # Don't plot intermediate results, e.g. P(Q), S(Q)
            match = GuiUtils.theory_plot_ID_pattern.match(plot.id)
            # 2nd match group contains the identifier for the intermediate
            # result, if present (e.g. "[P(Q)]")
            if match and match.groups()[1] is not None:
                continue
            # Don't include plots from different fitpages,
            # but always include the original data
            if (fitpage_name in plot.name
                    or name in plot.name
                    or name == plot.filename):
                # Residuals get their own plot
                if plot.plot_role == Data1D.ROLE_RESIDUAL:
                    plot.yscale = 'linear'
                    self.plotData([(item, plot)])
                else:
                    new_plots.append((item, plot))

        if new_plots:
            self.plotData(new_plots)

    def displayData(self, data_list, id=None):
        """
        Forces display of charts for the given data set
        """
        # data_list = [QStandardItem, Data1D/Data2D]
        plots_to_show = data_list[1:]
        plot_item = data_list[0]

        # plots to show
        new_plots = []

        # Get the main data plot
        main_data = GuiUtils.dataFromItem(plot_item.parent())
        if main_data is None:
            # Try the current item
            main_data = GuiUtils.dataFromItem(plot_item)
        # 1D dependent plots of 2D sets - special treatment
        if isinstance(main_data, Data2D) and isinstance(plots_to_show[0], Data1D):
            main_data = None

        # Make sure main data for 2D is always displayed
        if main_data is not None:
            if isinstance(main_data, Data2D):
                if self.isPlotShown(main_data):
                    self.active_plots[main_data.name].showNormal()
                else:
                    self.plotData([(plot_item, main_data)])

        append = False
        plot_to_append_to = None
        for plot_to_show in plots_to_show:
            # Check if this plot already exists
            shown = self.updatePlot(plot_to_show)
            # Retain append status throughout loop
            append = shown if shown else append

            plot_name = plot_to_show.name
            role = plot_to_show.plot_role

            if (role == Data1D.ROLE_RESIDUAL and shown) or role == Data1D.ROLE_DELETABLE:
                # Nothing to do if separate plot already shown or to be deleted
                continue
            elif role == Data1D.ROLE_RESIDUAL:
                # Residual plots should always be separate
                plot_to_show.yscale='linear'
                self.plotData([(plot_item, plot_to_show)])
            elif append:
                # Assume all other plots sent together should be on the same chart if a previous plot exists
                if not plot_to_append_to:
                    plot_to_append_to = self.active_plots[plot_name]
                # Remove existing if already exists
                self.appendOrUpdatePlot(self, plot_to_show, plot_to_append_to)
            else:
                # Plots with main data points on the same chart
                # Get the main data plot unless data is 2D which is plotted earlier
                if main_data is not None and not isinstance(main_data, Data2D):
                    new_plots.append((plot_item, main_data))
                new_plots.append((plot_item, plot_to_show))

        if append:
            # Append any plots handled in loop before an existing plot was found
            for _, plot_set in new_plots:
                self.appendOrUpdatePlot(self, plot_set, plot_to_append_to)
            # Clear list of any potential new plots now that they're appended to the existing plot
            new_plots = []

        if new_plots:
            self.plotData(new_plots)

    def isPlotShown(self, plot):
        """
        Checks currently shown plots and returns true if match
        """
        if not hasattr(plot, 'name'):
            return False
        ids_vals = [val.data[0].name for val in self.active_plots.values()]
                    #if val.data[0].plot_role != Data1D.ROLE_DATA]

        return plot.name in ids_vals

    def addDataPlot2D(self, plot_set, item):
        """
        Create a new 2D plot and add it to the workspace
        """
        plot2D = Plotter2D(self)
        plot2D.item = item
        plot2D.plot(plot_set)
        self.addPlot(plot2D)
        self.active_plots[plot2D.data[0].name] = plot2D
        # ============================================
        # Experimental hook for silx charts
        # ============================================
        # # Attach silx
        # from silx.gui import qt
        # from silx.gui.plot import StackView
        # sv = StackView()
        # sv.setColormap("jet", autoscale=True)
        # sv.setStack(plot_set.data.reshape(1,100,100))
        # #sv.setLabels(["x: -10 to 10 (200 samples)",
        # #              "y: -10 to 5 (150 samples)"])
        # sv.show()
        # ============================================

    def plotData(self, plots, transform=True):
        """
        Takes 1D/2D data and generates a single plot (1D) or multiple plots (2D)
        """
        # Call show on requested plots
        # All same-type charts in one plot
        for item, plot_set in plots:
            if isinstance(plot_set, Data1D):
                if 'new_plot' not in locals():
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
            isinstance(new_plot.data[0], Data1D):
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
        if sys.platform == 'darwin':
            workspace_height = int(float(self.parent.workspace().sizeHint().height()) / 2)
            workspace_width = int(float(self.parent.workspace().sizeHint().width()) / 2)
            plot_widget.resize(workspace_width, workspace_height)

        # Show the plot
        new_plot.show()
        new_plot.canvas.draw()

        # Update the plot widgets dict
        self.plot_widgets[title] = plot_widget

        # Update the active chart list
        self.active_plots[new_plot.data[0].name] = new_plot

    def appendPlot(self):
        """
        Add data set(s) to the existing matplotlib chart
        """
        # new plot data; check which tab is currently active
        if self.current_view == self.treeView:
            new_plots = GuiUtils.plotsFromCheckedItems(self.model)
            graph = self.cbgraph
        else:
            new_plots = GuiUtils.plotsFromCheckedItems(self.theory_model)
            graph = self.cbgraph_2

        # old plot data
        plot_id = str(graph.currentText())
        try:
            assert plot_id in PlotHelper.currentPlots(), "No such plot: %s" % (plot_id)
        except:
            return

        old_plot = PlotHelper.plotById(plot_id)

        # Add new data to the old plot, if data type is the same.
        for _, plot_set in new_plots:
            if type(plot_set) is type(old_plot._data[0]):
                old_plot.plot(plot_set)

    @staticmethod
    def appendOrUpdatePlot(self, data, plot):
        name = data.name
        if isinstance(plot, Plotter2D) or name in plot.plot_dict.keys():
            plot.replacePlot(name, data)
        else:
            plot.plot(data)

    def updatePlot(self, data):
        """
        Modify existing plot for immediate response and returns True.
        Returns false, if the plot does not exist already.
        """
        try:  # there might be a list or a single value being passed
            data = data[0]
        except TypeError:
            pass
        assert type(data).__name__ in ['Data1D', 'Data2D']

        ids_keys = list(self.active_plots.keys())
        #ids_vals = [val.data.name for val in self.active_plots.values()]

        data_id = data.name
        if data_id in ids_keys:
            # We have data, let's replace data that needs replacing
            if data.plot_role != Data1D.ROLE_DATA:
                self.active_plots[data_id].replacePlot(data_id, data)
                # restore minimized window, if applicable
                self.active_plots[data_id].showNormal()
            return True
        #elif data_id in ids_vals:
        #    if data.plot_role != Data1D.ROLE_DATA:
        #        list(self.active_plots.values())[ids_vals.index(data_id)].replacePlot(data_id, data)
        #        self.active_plots[data_id].showNormal()
        #    return True
        return False

    def chooseFiles(self):
        """
        Shows the Open file dialog and returns the chosen path(s)
        """
        # List of known extensions
        wlist = self.getWlist()
        # Location is automatically saved - no need to keep track of the last dir
        # But only with Qt built-in dialog (non-platform native)
        kwargs = {
            'parent'    : self,
            'caption'   : 'Choose files',
            'filter'    : wlist,
            'options'   : QtWidgets.QFileDialog.DontUseNativeDialog |
                          QtWidgets.QFileDialog.DontUseCustomDirectoryIcons,
            'directory' : self.default_load_location
        }
        paths = QtWidgets.QFileDialog.getOpenFileNames(**kwargs)[0]
        if not paths:
            return

        if not isinstance(paths, list):
            paths = [paths]

        self.default_load_location = os.path.dirname(paths[0])
        return paths

    def readData(self, path):
        """
        verbatim copy-paste from
        ``sasgui.guiframe.local_perspectives.data_loader.data_loader.py``
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

                for item in output_objects:
                    # cast sascalc.dataloader.data_info.Data1D into
                    # sasgui.guiframe.dataFitting.Data1D
                    # TODO : Fix it
                    new_data = self.manager.create_gui_data(item, p_file)
                    output[new_data.id] = new_data

                    # Model update should be protected
                    self.mutex.lock()
                    self.updateModel(new_data, new_data.name)
                    #self.model.reset()
                    QtWidgets.QApplication.processEvents()
                    self.mutex.unlock()

                    if hasattr(item, 'errors'):
                        for error_data in item.errors:
                            data_error = True
                            error_message += "\tError: {0}\n".format(error_data)
                    else:

                        logging.error("Loader returned an invalid object:\n %s" % str(item))
                        data_error = True

            except Exception as ex:
                logging.error(str(ex) + str(sys.exc_info()[1]))

                any_error = True
            if any_error or data_error or error_message != "":
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
        if dimension not in types:
            return

        for index in range(model.rowCount()):
            item = model.item(index)
            if item.isCheckable() and item.checkState() != mode:
                data = item.child(0).data()
                if dimension is None or isinstance(data, dimension):
                    item.setCheckState(mode)

            items = list(GuiUtils.getChildrenFromItem(item))

            for it in items:
                if it.isCheckable() and it.checkState() != mode:
                    data = it.child(0).data()
                    if dimension is None or isinstance(data, dimension):
                        it.setCheckState(mode)

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
        self.context_menu.addAction(self.actionSelect)
        self.context_menu.addAction(self.actionDeselect)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.actionChangeName)
        self.context_menu.addAction(self.actionDataInfo)
        self.context_menu.addAction(self.actionSaveAs)
        self.context_menu.addAction(self.actionQuickPlot)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.actionQuick3DPlot)
        self.context_menu.addAction(self.actionEditMask)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.actionFreezeResults)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.actionDelete)

        # Define the callbacks
        self.actionSelect.triggered.connect(self.onFileListSelected)
        self.actionDeselect.triggered.connect(self.onFileListDeselected)
        self.actionChangeName.triggered.connect(self.changeName)
        self.actionDataInfo.triggered.connect(self.showDataInfo)
        self.actionSaveAs.triggered.connect(self.saveDataAs)
        self.actionQuickPlot.triggered.connect(self.quickDataPlot)
        self.actionQuick3DPlot.triggered.connect(self.quickData3DPlot)
        self.actionEditMask.triggered.connect(self.showEditDataMask)
        self.actionDelete.triggered.connect(self.deleteSelectedItem)
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
        self.actionSelect.setEnabled(True)

        # Name Changing
        # Disallow name changes after the data has been assigned any plots to prevent orphans
        children = list(GuiUtils.getChildrenFromItem(model_item))
        hashables = [child for child in children if isinstance(child, GuiUtils.HashableStandardItem)]
        self.actionChangeName.setEnabled(len(hashables) <= 1)
        # Do not allow name change for lower level plots
        self.actionChangeName.setVisible(model_item.parent() is None)

        # Freezing
        # check that the selection has inner items
        freeze_enabled = False
        if model_item.parent() is not None:
            freeze_enabled = True
        self.actionFreezeResults.setEnabled(freeze_enabled)

        # Fire up the menu
        self.context_menu.exec_(self.current_view.mapToGlobal(position))

    def changeName(self):
        """
        Open a modal window that can change the display name of the selected data
        """
        index = self.current_view.selectedIndexes()[0]
        proxy = self.current_view.model()
        model = proxy.sourceModel()

        # Get the model item and update the name change box
        model_item = model.itemFromIndex(proxy.mapToSource(index))

        # Do not allow name changes after the data has plots assigned
        children = list(GuiUtils.getChildrenFromItem(model_item))
        hashables = [child for child in children if isinstance(child, GuiUtils.HashableStandardItem)]
        if len(hashables) <= 1:
            self.nameChangeBox.model_item = model_item
            # Open the window
            self.nameChangeBox.show()

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
            self.txt_widget.resize(420, 600)
        else:
            text_to_show = GuiUtils.retrieveData2d(data)
            # Hardcoded sizes to enable full width rendering with default font
            self.txt_widget.resize(700, 600)

        self.txt_widget.setReadOnly(True)
        self.txt_widget.setWindowFlags(QtCore.Qt.Window)
        self.txt_widget.setWindowIcon(QtGui.QIcon(":/res/ball.ico"))
        self.txt_widget.setWindowTitle("Data Info: %s" % data.name)
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
            method_name = 'Plotter2D'

        self.new_plot = globals()[method_name](self, quickplot=True)
        self.new_plot.data = data
        self.new_plot.plot(data=data)

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
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Error: cannot apply mask.\n" +
                    "Please select a 2D dataset.")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)

        try:
            if data is None or not isinstance(data, Data2D):
                # if data wasn't passed - try to get it from
                # the currently selected item
                index = self.current_view.selectedIndexes()[0]
                proxy = self.current_view.model()
                model = proxy.sourceModel()
                model_item = model.itemFromIndex(proxy.mapToSource(index))

                data = GuiUtils.dataFromItem(model_item)

            if data is None or not isinstance(data, Data2D):
                # If data is still not right, complain
                msg.exec_()
                return
        except Exception as ex:
            logging.error(str(ex) + str(sys.exc_info()[1]))
            msg.exec_()
            return

        mask_editor = MaskEditor(self, data)
        # Modal dialog here.
        mask_editor.exec_()

        # Mask assigning done update qranges (Data has been updated in-place)
        self.communicator.updateMaskedDataSignal.emit()

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

    def freezeDataToItem(self, data=None):
        """
        Freeze given set of data to main model
        """
        if data is None:
            return
        self.model.beginResetModel()
        # Append a "unique" descriptor to the name
        time_bit = str(time.time())[7:-1].replace('.', '')
        new_name = data.name + '_@' + time_bit
        # Change the underlying data so it is no longer a theory
        try:
            data.is_data = True
            data.symbol = 'Circle'
            data.id = new_name
        except AttributeError:
            # no data here, pass
            pass
        new_item = GuiUtils.createModelItemWithPlot(data, new_name)

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

    def deleteAllItems(self):
        """
        Deletes all datasets from both model and theory_model
        """
        deleted_items = [self.model.item(row) for row in range(self.model.rowCount())
                         if self.model.item(row).isCheckable()]
        deleted_theory_items = [self.theory_model.item(row)
                                for row in range(self.theory_model.rowCount())
                                if self.theory_model.item(row).isCheckable()]
        deleted_items += deleted_theory_items
        deleted_names = [item.text() for item in deleted_items]
        deleted_names += deleted_theory_items
        # Close all active plots
        self.closeAllPlots()
        # Let others know we deleted data
        self.communicator.dataDeletedSignal.emit(deleted_items)
        # update stored_data
        self.manager.update_stored_data(deleted_names)
        self.manager.delete_data(data_id=[], theory_id=[], delete_all=True)

        # Clear the model
        self.model.clear()
        self.theory_model.clear()

    def deleteSelectedItem(self):
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

        indices = self.current_view.selectedIndexes()
        self.deleteIndices(indices)

    def deleteIndices(self, indices):
        """
        Delete model idices from the current view
        """
        proxy = self.current_view.model()
        model = proxy.sourceModel()

        deleted_items = []
        deleted_names = []

        # Every time a row is removed, the indices change, so we'll just remove
        # rows and keep calling selectedIndexes until it returns an empty list.
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

    def closeAllPlots(self):
        """
        Close all currently displayed plots
        """

        for plot_id in PlotHelper.currentPlots():
            try:
                plotter = PlotHelper.plotById(plot_id)
                plotter.close()
                self.plot_widgets[plot_id].close()
                self.plot_widgets.pop(plot_id, None)
            except AttributeError as ex:
                logging.error("Closing of %s failed:\n %s" % (plot_id, str(ex)))

    def minimizeAllPlots(self):
        """
        Minimize all currently displayed plots
        """
        for plot_id in PlotHelper.currentPlots():
            plotter = PlotHelper.plotById(plot_id)
            plotter.showMinimized()

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
                        self.plot_widgets[plot_name].close()
                        self.plot_widgets.pop(plot_name, None)
                    except AttributeError as ex:
                        logging.error("Closing of %s failed:\n %s" % (plot_name, str(ex)))

        pass  # debugger anchor

    def closeResultPanelOnDelete(self, data):
        """
        Given a data1d/2d object, close the fitting results panel if currently populated with the data
        """
        # data - Single data1d/2d object to be deleted
        self.parent.results_panel.onDataDeleted(data)

    def onAnalysisUpdate(self, new_perspective_name: str):
        """
        Update the perspective combo index based on passed string
        """
        assert new_perspective_name in Perspectives.PERSPECTIVES.keys()
        self.cbFitting.blockSignals(True)
        self.cbFitting.setCurrentIndex(self.cbFitting.findText(new_perspective_name))
        self.cbFitting.blockSignals(False)
        pass

    def loadComplete(self, output):
        """
        Post message to status bar and update the data manager
        """
        assert isinstance(output, tuple)
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
        if p_file is not None:
            p_file = os.path.basename(p_file) if os.path.exists(p_file) else p_file
            checkbox_item.setText(p_file)

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

        # send in the new item
        self.model.appendRow(model_item)
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

        # Check if there exists an item for this tab
        # If so, replace it
        current_tab_name = model_item.text()
        for current_index in range(self.theory_model.rowCount()):
            current_item = self.theory_model.item(current_index)
            if current_tab_name == current_item.text():
                # replace data instead
                new_data = GuiUtils.dataFromItem(model_item)
                current_item.child(0).setData(new_data)
                return current_item

        # add the new item to the model
        self.theory_model.appendRow(model_item)
        return model_item

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

    def onFileListSelected(self):
        """
        Slot for actionSelect
        """
        self.setCheckItems(status=QtCore.Qt.Checked)

    def onFileListDeselected(self):
        """
        Slot for actionDeselect
        """
        self.setCheckItems(status=QtCore.Qt.Unchecked)

    def onFileListChanged(self, item):
        """
        Slot for model (data/theory) changes.
        Currently only reacting to checkbox selection.
        """
        if len(self.current_view.selectedIndexes()) < 2:
            return
        self.setCheckItems(status=item.checkState())

    def setCheckItems(self, status=QtCore.Qt.Unchecked):
        """
        Sets requested checkbox status on selected indices
        """
        proxy = self.current_view.model()
        model = proxy.sourceModel()
        model.blockSignals(True)
        for index in self.current_view.selectedIndexes():
            item = model.itemFromIndex(proxy.mapToSource(index))
            if item.isCheckable():
                item.setCheckState(status)
        model.blockSignals(False)
