# pylint:disable=C0103,E501,E203
"""
Allows users to modify the box slicer parameters.
"""
import os
import functools

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Slicers.BoxSlicer import BoxInteractorX
from sas.qtgui.Plotting.Slicers.BoxSlicer import BoxInteractorY
from sas.qtgui.Plotting.Slicers.AnnulusSlicer import AnnulusInteractor
from sas.qtgui.Plotting.Slicers.SectorSlicer import SectorInteractor

# Local UI
from sas.qtgui.Plotting.UI.SlicerParametersUI import Ui_SlicerParametersUI


class SlicerParameters(QtWidgets.QDialog, Ui_SlicerParametersUI):
    """
    Interaction between the QTableView and the underlying model,
    passed from a slicer instance.
    """
    closeWidgetSignal = QtCore.pyqtSignal()

    def __init__(self, parent=None,
                 model=None,
                 active_plots=None,
                 validate_method=None,
                 communicator=None):
        super(SlicerParameters, self).__init__()

        self.setupUi(self)

        #assert isinstance(model, QtGui.QStandardItemModel)
        self.parent = parent

        self.model = model
        self.validate_method = validate_method
        self.active_plots = active_plots
        self.save_location = GuiUtils.DEFAULT_OPEN_FOLDER
        self.communicator = communicator

        # Initially, Apply is disabled
        self.cmdApply.setEnabled(False)

        # Mapping combobox index -> slicer module
        self.callbacks = {0: None,
                          1: SectorInteractor,
                          2: AnnulusInteractor,
                          3: BoxInteractorX,
                          4: BoxInteractorY}

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

    def setPlotsList(self):
        """
        Create and initially populate the list of plots
        """
        self.lstPlots.clear()
        # Fill out list of plots
        for item in self.active_plots.keys():
            if isinstance(self.active_plots[item].data[0], Data1D):
                continue
            checked = QtCore.Qt.Unchecked
            if self.parent.data[0].name == item:
                checked = QtCore.Qt.Checked
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
        if index == 0: # No interactor
            self.parent.onClearSlicer()
            self.setModel(None)
        else:
            slicer = self.callbacks[index]
            if self.active_plots.keys():
                self.parent.setSlicer(slicer=slicer)

    def onGeneratePlots(self, isChecked):
        """
        Respond to choice of auto saving plots
        """
        self.enableFileControls(isChecked)
        self.isSave = isChecked

    def onChooseFilesLocation(self):
        """
        Open save file location dialog
        """
        kwargs = {
            'parent'    : self,
            'caption'   : 'Save files to:',
            'options'   : QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontUseNativeDialog,
            'directory' : self.save_location
        }
        folder = QtWidgets.QFileDialog.getExistingDirectory(**kwargs)

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

    def onApply(self):
        """
        Apply current slicer to selected plots
        """
        for row in range(self.lstPlots.count()):
            item = self.lstPlots.item(row)
            isChecked = item.checkState() == QtCore.Qt.Checked
            # Only checked items
            if not isChecked:
                continue
            plot = item.text()
            # don't assign to itself
            if plot == self.parent.data[0].name:
                continue
            # a plot might have been deleted
            if plot not in self.active_plots:
                continue
            # get the plotter2D instance
            plotter = self.active_plots[plot]
            # Assign model to slicer
            index = self.cbSlicer.currentIndex()

            slicer = self.callbacks[index]
            plotter.setSlicer(slicer=slicer)
            # override slicer model
            plotter.slicer._model = self.model
            # force conversion model->parameters in slicer
            plotter.slicer.setParamsFromModel()
        pass

    def setModel(self, model):
        """ Model setter """
        self.model = model
        self.proxy.setSourceModel(self.model)

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
        GuiUtils.showHelp(url)


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
    refocus_signal = QtCore.pyqtSignal(int, int)

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
        if self.validate_method:
            # Validate the proposed value in the slicer
            value_accepted = self.validate_method(param_name, new_value)
            # Update the model only if value accepted
            return super(EditDelegate, self).setModelData(editor, model, index)
        return None
