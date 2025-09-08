# pylint:disable=C0103,E501,E203
"""
Allows users to modify the box slicer parameters.
"""
import functools
import logging
import os

from PySide6 import QtCore, QtGui, QtWidgets

from sasdata.dataloader.loader import Loader
from sasdata.file_converter.nxcansas_writer import NXcanSASWriter

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas import config
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Slicers.AnnulusSlicer import AnnulusInteractor
from sas.qtgui.Plotting.Slicers.BoxSlicer import BoxInteractorX, BoxInteractorY
from sas.qtgui.Plotting.Slicers.SectorSlicer import SectorInteractor
from sas.qtgui.Plotting.Slicers.WedgeSlicer import WedgeInteractorPhi, WedgeInteractorQ

# Local UI
from sas.qtgui.Plotting.UI.SlicerParametersUI import Ui_SlicerParametersUI


class SlicerParameters(QtWidgets.QDialog, Ui_SlicerParametersUI):
    """
    Interaction between the QTableView and the underlying model,
    passed from a slicer instance.
    """
    closeWidgetSignal = QtCore.Signal()

    def __init__(self, parent=None,
                 model=None,
                 active_plots=None,
                 validate_method=None,
                 communicator=None):
        super(SlicerParameters, self).__init__(parent.manager)

        self.setupUi(self)

        self.parent = parent

        self.manager = parent.manager

        self.model = model
        self.validate_method = validate_method
        self.active_plots = active_plots
        self.save_location = config.DEFAULT_OPEN_FOLDER
        self.communicator = communicator

        # Initially, Apply is disabled
        self.cmdApply.setEnabled(False)

        # Mapping combobox index -> slicer module
        self.callbacks = {0: None,
                          1: SectorInteractor,
                          2: AnnulusInteractor,
                          3: BoxInteractorX,
                          4: BoxInteractorY,
                          5: WedgeInteractorQ,
                          6: WedgeInteractorPhi}

        # Define a proxy model so cell enablement can be finegrained.
        self.proxy = ProxyModel(self)
        self.proxy.setSourceModel(self.model)

        # Set the proxy model for display in the Table View.
        self.lstParams.setModel(self.proxy)

        # Disallow edit of the parameter name column.
        self.lstParams.model().setColumnReadOnly(0, True)

        # Specify the validator on the parameter value column.
        self.delegate = EditDelegate(self, validate_method=self.validate_method)
        self.lstParams.setItemDelegate(self.delegate)

        # respond to graph deletion
        self.communicator.activeGraphsSignal.connect(self.updatePlotList)

        # Set up paths
        self.txtLocation.setText(self.save_location)

        # define slots
        self.setSlots()

        # Switch off Auto Save
        self.onGeneratePlots(False)

        # Set up params list
        self.setParamsList()

        # Set up plots list
        self.setPlotsList()

    def setParamsList(self):
        """
        Create and initially populate the list of parameters
        """
        # Disable row number display
        self.lstParams.verticalHeader().setVisible(False)
        self.lstParams.setAlternatingRowColors(True)
        self.lstParams.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,
                                     QtWidgets.QSizePolicy.Expanding)

        # Header properties for nicer display
        header = self.lstParams.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        header.setStretchLastSection(True)

    def updatePlotList(self):
        '''
        '''
        self.active_plots = self.parent.getActivePlots()
        self.setPlotsList()

    def getCurrentPlotDict(self):
        """
        Returns a dictionary of currently shown plots
        {plot_name:checkbox_status}
        """
        current_plots = {}
        if self.lstPlots.count() != 0:
            for row in range(self.lstPlots.count()):
                item = self.lstPlots.item(row)
                isChecked = item.checkState() != QtCore.Qt.Unchecked
                plot = item.text()
                current_plots[plot] = isChecked
        return current_plots

    def setPlotsList(self):
        """
        Create and initially populate the list of plots
        """
        current_plots = self.getCurrentPlotDict()
        self.lstPlots.clear()
        # Fill out list of plots
        for item in self.active_plots.keys():
            if isinstance(self.active_plots[item].data[0], Data1D):
                # don't include dependant 1D plots
                continue
            if str(item) in current_plots.keys():
                # redo the list
                checked = QtCore.Qt.Checked if current_plots[item] else QtCore.Qt.Unchecked
            else:
                # create a new list
                checked = QtCore.Qt.Checked if (self.parent.data[0].name == item) else QtCore.Qt.Unchecked

            chkboxItem = QtWidgets.QListWidgetItem(str(item))
            chkboxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkboxItem.setCheckState(checked)
            self.lstPlots.addItem(chkboxItem)

    def setSlots(self):
        """
        define slots for signals from various sources
        """
        self.delegate.refocus_signal.connect(self.onFocus)
        self.cbSave1DPlots.toggled.connect(self.onGeneratePlots)
        self.cmdFiles.clicked.connect(self.onChooseFilesLocation)
        # Display Help on clicking the button
        self.cmdHelp.clicked.connect(self.onHelp)

        # Close doesn't trigger closeEvent automatically, so force it
        self.cmdClose.clicked.connect(functools.partial(self.closeEvent, None))

        # Apply slicer to selected plots
        self.cmdApply.clicked.connect(self.onApply)

        # Initialize slicer combobox to the current slicer
        current_slicer = type(self.parent.slicer)
        for index in self.callbacks:
            if self.callbacks[index] == current_slicer:
                self.cbSlicer.setCurrentIndex(index)
                break
        # change the slicer type
        self.cbSlicer.currentIndexChanged.connect(self.onSlicerChanged)

        # Updates to the slicer moder must propagate to all plotters
        if self.model is not None:
            self.model.itemChanged.connect(self.onParamChange)

        # selecting/deselecting items in lstPlots enables `Apply`
        self.lstPlots.itemChanged.connect(lambda: self.cmdApply.setEnabled(True))

    def onFocus(self, row, column):
        """ Set the focus on the cell (row, column) """
        selection_model = self.lstParams.selectionModel()
        selection_model.select(self.model.index(row, column), QtGui.QItemSelectionModel.Select)
        self.lstParams.setSelectionModel(selection_model)
        self.lstParams.setCurrentIndex(self.model.index(row, column))

    def onSlicerChanged(self, index):
        """ change the parameters based on the slicer chosen """
        if index == 0:  # No interactor
            self.parent.onClearSlicer()
            self.setModel(None)
            self.onGeneratePlots(False)
        else:
            slicer = self.callbacks[index]
            if self.active_plots.keys():
                self.parent.setSlicer(slicer=slicer)
        self.onParamChange()

    def onGeneratePlots(self, isChecked):
        """
        Respond to choice of auto saving plots
        """
        self.enableFileControls(isChecked)
        # state changed - enable apply
        self.cmdApply.setEnabled(True)
        self.isSave = isChecked

    def onChooseFilesLocation(self):
        """
        Open save file location dialog
        """
        parent = self
        caption = 'Save files to:'
        options = QtWidgets.QFileDialog.ShowDirsOnly
        directory = self.save_location
        folder = QtWidgets.QFileDialog.getExistingDirectory(parent, caption, directory, options)

        if folder is None:
            return

        folder = str(folder)
        if not os.path.isdir(folder):
            return
        self.save_location = folder
        self.txtLocation.setText(self.save_location)

    def enableFileControls(self, enabled):
        """
        Sets enablement of file related UI elements
        """
        self.txtLocation.setEnabled(enabled)
        self.txtExtension.setEnabled(enabled)
        self.cmdFiles.setEnabled(enabled)
        self.cbFitOptions.setEnabled(enabled)
        self.label_4.setEnabled(enabled)
        self.cbSaveExt.setEnabled(enabled)

    def onParamChange(self):
        """
        Respond to param change by updating plots
        """
        for row in range(self.lstPlots.count()):
            item = self.lstPlots.item(row)
            isChecked = item.checkState() != QtCore.Qt.Unchecked
            # Only checked items
            if not isChecked:
                continue
            plot = item.text()
            # Apply plotter to a plot
            self.applyPlotter(plot)

    def onApply(self):
        """
        Apply current slicer to selected plots
        """
        plots = []
        for row in range(self.lstPlots.count()):
            item = self.lstPlots.item(row)
            isChecked = item.checkState() != QtCore.Qt.Unchecked
            # Only checked items
            if not isChecked:
                continue
            plot = item.text()
            # Apply plotter to a plot
            self.applyPlotter(plot)
            # Save 1D plots if required
            plots.append(plot)
        if self.isSave and self.model is not None:
            self.save1DPlotsForPlot(plots)
        pass  # debug anchor

    def applyPlotter(self, plot):
        """
        Apply the current slicer to a plot
        """
        # don't assign to itself
        if plot == self.parent.data[0].name:
            return
        # a plot might have been deleted
        if plot not in self.active_plots:
            return
        # get the plotter2D instance
        plotter = self.active_plots[plot]
        # Assign model to slicer
        index = self.cbSlicer.currentIndex()

        slicer = self.callbacks[index]
        if slicer is None:
            plotter.onClearSlicer()
            return
        plotter.setSlicer(slicer=slicer, reset=False)
        # override slicer model
        plotter.slicer._model = self.model
        # force conversion model->parameters in slicer
        plotter.slicer.setParamsFromModel()

    def prepareFilePathFromData(self, data):
        """
        Prepares full, unique path for a 1D plot
        """
        # Extend filename with the requested string
        filename = data.name if self.txtExtension.text() == ""\
            else data.name + "_" + str(self.txtExtension.text())
        extension = self.cbSaveExt.currentText()
        filename_ext = filename + extension

        # Assure filename uniqueness
        dst_filename = GuiUtils.findNextFilename(filename_ext, self.save_location)
        if not dst_filename:
            logging.error("Could not find appropriate filename for " + filename_ext)
            return
        filepath = os.path.join(self.save_location, dst_filename)
        return filepath

    def serializeData(self, data, filepath):
        """
        Write out 1D plot in a requested format
        """
        # Choose serializer based on requested extension
        extension = self.cbSaveExt.currentText()
        if 'txt' in extension:
            GuiUtils.onTXTSave(data, filepath)
        elif 'xml' in extension:
            loader = Loader()
            loader.save(filepath, data, ".xml")
        elif 'h5' in extension:
            nxcansaswriter = NXcanSASWriter()
            nxcansaswriter.write([data], filepath)
        else:
            raise AttributeError("Incorrect extension chosen")

    def save1DPlotsForPlot(self, plots):
        """
        Save currently shown 1D sliced data plots for a given 2D plot
        """
        items_for_fit = []
        for plot in plots:
            for item in self.active_plots.keys():
                data = self.active_plots[item].data[-1]
                if not isinstance(data, Data1D):
                    continue
                if plot not in data.name:
                    continue

                filepath = self.prepareFilePathFromData(data)
                self.serializeData(data, filepath)

                # Add plot to the DataExplorer tree
                new_name, _ = os.path.splitext(os.path.basename(filepath))
                new_item = GuiUtils.createModelItemWithPlot(data, name=new_name)
                self.parent.manager.updateModelFromPerspective(new_item)

                items_for_fit.append(new_item)
        # Send to fitting, if needed
        # We can get away with directly querying the UI, since this is the only
        # place we need that state.
        fitting_requested = self.cbFitOptions.currentIndex()
        self.sendToFit(items_for_fit, fitting_requested)

    def setModel(self, model):
        """ Model setter """
        # check if parent slicer changed
        current_slicer = type(self.parent.slicer)
        for index in self.callbacks:
            # must use type() for None or just imported type for ! None
            if type(self.callbacks[index]) == current_slicer or \
               self.callbacks[index] == current_slicer:
                if index != self.cbSlicer.currentIndex():
                    # parameters already updated, no need to notify
                    # combobox listeners
                    self.cbSlicer.blockSignals(True)
                    self.cbSlicer.setCurrentIndex(index)
                    self.cbSlicer.blockSignals(False)
                break
        self.model = model
        self.proxy.setSourceModel(self.model)
        if model is not None:
            self.model.itemChanged.connect(self.onParamChange)

    def check_perspective_and_set_data(self,fitting_requested, perspective_name, items_for_fit):        
        isBatch = fitting_requested in (2, 4)
        self.parent.manager.parent.loadedPerspectives[perspective_name].setData(data_item=items_for_fit,is_batch=isBatch)

    def sendToFit(self, items_for_fit, fitting_requested):
        """
        Send `items_for_fit` to the Fit perspective, in either single fit or batch mode
        """

        if fitting_requested in (1, 2):
            self.check_perspective_and_set_data(fitting_requested, 'Fitting', items_for_fit)
        elif fitting_requested in (3, 4):
            self.check_perspective_and_set_data(fitting_requested, 'Inversion', items_for_fit)
        else:
            return
    

    def keyPressEvent(self, event):
        """
        Added Esc key shortcut
        """
        key = event.key()
        if key == QtCore.Qt.Key_Escape:
            self.closeWidgetSignal.emit()

    def closeEvent(self, event):
        """
        Overwritten close widget method in order to send the close
        signal to the parent.
        """
        self.closeWidgetSignal.emit()
        if event:
            event.accept()

    def onHelp(self):
        """
        Display generic data averaging help
        """
        url = "/user/qtgui/MainWindow/graph_help.html#d-data-averaging"
        self.manager.parent.showHelp(url)


class ProxyModel(QtCore.QIdentityProxyModel):
    """
    Trivial proxy model with custom column edit flag
    """
    def __init__(self, parent=None):
        super(ProxyModel, self).__init__(parent)
        self._columns = set()

    def columnReadOnly(self, column):
        '''Returns True if column is read only, false otherwise'''
        return column in self._columns

    def setColumnReadOnly(self, column, readonly=True):
        '''Add/removes a column from the readonly list'''
        if readonly:
            self._columns.add(column)
        else:
            self._columns.discard(column)

    def flags(self, index):
        '''Sets column flags'''
        flags = super(ProxyModel, self).flags(index)
        if self.columnReadOnly(index.column()):
            flags &= ~QtCore.Qt.ItemIsEditable
        return flags


class PositiveDoubleEditor(QtWidgets.QLineEdit):
    # a signal to tell the delegate when we have finished editing
    editingFinished = QtCore.Signal()

    def __init__(self, parent=None):
        # Initialize the editor object
        super(PositiveDoubleEditor, self).__init__(parent)
        self.setAutoFillBackground(True)
        validator = GuiUtils.DoubleValidator()
        # Don't use the scientific notation, cause 'e'.
        validator.setNotation(GuiUtils.DoubleValidator.StandardNotation)

        self.setValidator(validator)

    def focusOutEvent(self, event):
        # Once focus is lost, tell the delegate we're done editing
        self.editingFinished.emit()


class EditDelegate(QtWidgets.QStyledItemDelegate):
    refocus_signal = QtCore.Signal(int, int)

    def __init__(self, parent=None, validate_method=None):
        super(EditDelegate, self).__init__(parent)
        self.editor = None
        self.index = None
        self.validate_method = validate_method

    def createEditor(self, parent, option, index):
        # Creates and returns the custom editor object we will use to edit the cell
        if not index.isValid():
            return 0

        result = index.column()
        if result == 1:
            self.editor = PositiveDoubleEditor(parent)
            self.index = index
            return self.editor

        return QtWidgets.QStyledItemDelegate.createEditor(self, parent, option, index)

    def setModelData(self, editor, model, index):
        """
        Custom version of the model update, rejecting bad values
        """
        self.index = index

        # Find out the changed parameter name and proposed value
        new_value = GuiUtils.toDouble(self.editor.text())
        param_name = model.sourceModel().item(index.row(), 0).text()
        value_accepted = True
        if self.validate_method:
            # Validate the proposed value in the slicer
            value_accepted = self.validate_method(param_name, new_value)
            # Update the model only if value accepted
        if value_accepted:
            return super(EditDelegate, self).setModelData(editor, model, index)
        else:
            return None
