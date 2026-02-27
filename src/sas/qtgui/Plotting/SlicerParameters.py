# pylint:disable=C0103,E501,E203
"""
Allows users to modify the box slicer parameters.
"""

import functools
import logging
import os
from enum import Enum

from PySide6 import QtCore, QtGui, QtWidgets

from sasdata.dataloader.loader import Loader
from sasdata.file_converter.nxcansas_writer import NXcanSASWriter

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas import config
from sas.qtgui.Plotting import PlotHelper
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.Slicers.AnnulusSlicer import AnnulusInteractor
from sas.qtgui.Plotting.Slicers.BoxSlicer import BoxInteractorX, BoxInteractorY
from sas.qtgui.Plotting.Slicers.MultiSlicerBase import (
    SectorInteractorMulti,
    WedgeInteractorPhiMulti,
    WedgeInteractorQMulti,
)
from sas.qtgui.Plotting.Slicers.SectorSlicer import SectorInteractor
from sas.qtgui.Plotting.Slicers.WedgeSlicer import WedgeInteractorPhi, WedgeInteractorQ

# Local UI
from sas.qtgui.Plotting.UI.SlicerParametersUI import Ui_SlicerParametersUI

logger = logging.getLogger(__name__)


class FittingType(Enum):
    NO_FITTING: int = 0
    FITTING_SINGLE: int = 1
    FITTING_BATCH: int = 2
    INVERSION_SINGLE: int = 3
    INVERSION_BATCH: int = 4


class SymmetricDefinitions(Enum):
    """Definitions for symmetric slicers"""

    WEDGE_PHI = ("Wedge (Phi)", WedgeInteractorPhi, WedgeInteractorPhiMulti)
    WEDGE_Q = ("Wedge (Q)", WedgeInteractorQ, WedgeInteractorQMulti)
    SECTOR = ("Sector", SectorInteractor, SectorInteractorMulti)

    def __init__(self, display_name, single_class, multi_class):
        self.display_name = display_name
        self.single_class = single_class
        self.multi_class = multi_class


FITTING_TYPES: set[int] = {FittingType.FITTING_SINGLE, FittingType.FITTING_BATCH}  # 1, 2
BATCH_TYPES: set[int] = {FittingType.FITTING_BATCH, FittingType.INVERSION_BATCH}  # 2, 4
INVERSION_TYPES: set[int] = {FittingType.INVERSION_SINGLE, FittingType.INVERSION_BATCH}  # 3, 4


class SlicerParameters(QtWidgets.QDialog, Ui_SlicerParametersUI):
    """
    Interaction between the QTableView and the underlying model,
    passed from a slicer instance.
    """

    closeWidgetSignal = QtCore.Signal()

    def __init__(self, parent=None, model=None, active_plots=None, validate_method=None, communicator=None):
        super(SlicerParameters, self).__init__(parent.manager)

        self.setupUi(self)

        self.parent = parent

        self.manager = parent.manager

        self.model = model
        self.validate_method = validate_method
        self.active_plots = active_plots
        self.active_slicer_plots = {}
        self.save_location = config.DEFAULT_OPEN_FOLDER
        self.communicator = communicator

        # Initially, Apply is disabled
        self.cmdApply.setEnabled(False)

        # Store models for each slicer
        self.slicer_models = {}

        # Set the checkbox state based on parent's stackplots attribute
        self.cbStackPlots.setChecked(getattr(self.parent, 'stackplots', False))

        # Mapping combobox index -> slicer module
        self.callbacks = {
            0: None,
            1: SectorInteractor,
            2: AnnulusInteractor,
            3: BoxInteractorX,
            4: BoxInteractorY,
            5: WedgeInteractorQ,
            6: WedgeInteractorPhi,
        }

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

        # Set up slicers list
        self.setSlicersList()

        # Set up slicer plots list
        self.setSlicerPlotsList()

        # Initial update of active plots
        self.updatePlotList()

    def setParamsList(self):
        """
        Create and initially populate the list of parameters
        """
        # Disable row number display
        self.lstParams.verticalHeader().setVisible(False)
        self.lstParams.setAlternatingRowColors(True)
        self.lstParams.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Expanding)

        # Header properties for nicer display
        header = self.lstParams.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        header.setStretchLastSection(True)

    def updatePlotList(self):
        """Update the list of active plots"""
        self.active_plots = self.parent.getActivePlots()
        self.setPlotsList()
        self.updateSlicerPlotList()

    def updateSlicerPlotList(self):
        """Update the list of active slicer plots"""
        self.active_slicer_plots = self.parent.getActiveSlicerPlots()
        self.setSlicerPlotsList()

    def getCurrentSlicerDict(self):
        """
        Returns a dictionary of currently shown slicers
        {slicer_name:checkbox_status}
        """
        current_slicers = {}
        for row in range(self.lstSlicers.count()):
            item = self.lstSlicers.item(row)
            isChecked = item.checkState() != QtCore.Qt.Unchecked
            slicer = item.text()
            current_slicers[slicer] = isChecked
        return current_slicers

    def setSlicersList(self):
        """
        Create and initially populate the list of slicers with radio button behavior
        """

        self.lstSlicers.clear()

        # Create a button group for radio button behavior
        if not hasattr(self, "slicerButtonGroup"):
            self.slicerButtonGroup = QtWidgets.QButtonGroup(self)
            self.slicerButtonGroup.setExclusive(True)

        # Determine which slicer should be selected based on the current model
        slicer_to_select = None
        if self.model is not None:
            # Find which slicer has this model
            for slicer_name, slicer_obj in self.parent.slicers.items():
                if hasattr(slicer_obj, "_model") and slicer_obj._model is self.model:
                    slicer_to_select = slicer_name
                    break

        # Fill out list of slicers
        for idx, item in enumerate(self.parent.slicers):
            # Create a widget to hold the radio button
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout(widget)
            layout.setContentsMargins(5, 2, 5, 2)

            # Create radio button
            radio = QtWidgets.QRadioButton(str(item))

            # Check if this should be selected
            should_select = (slicer_to_select == str(item)) or (slicer_to_select is None and idx == 0)
            radio.setChecked(should_select)

            # Add to button group
            self.slicerButtonGroup.addButton(radio, idx)

            layout.addWidget(radio)
            layout.addStretch()

            # Create list item
            listItem = QtWidgets.QListWidgetItem(self.lstSlicers)
            listItem.setSizeHint(widget.sizeHint())

            # Add to list
            self.lstSlicers.addItem(listItem)
            self.lstSlicers.setItemWidget(listItem, widget)

            # Store the slicer's model
            if item in self.parent.slicers:
                slicer_obj = self.parent.slicers[item]
                if hasattr(slicer_obj, "_model"):
                    self.slicer_models[str(item)] = slicer_obj._model

            # Connect radio button to update handler
            radio.toggled.connect(lambda checked, name=str(item): self.onSlicerRadioToggled(checked, name))

    def getCheckedSlicer(self):
        """
        Returns the currently checked slicer (radio button)
        """
        if not hasattr(self, "slicerButtonGroup"):
            return None

        checked_button = self.slicerButtonGroup.checkedButton()
        return checked_button.text() if checked_button else None

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

    def getCurrentSlicerPlotDict(self):
        """
        Returns a dictionary of currently shown slicer plots
        {slicer_plot_name:checkbox_status}
        """
        current_slicer_plots = {}
        for row in range(self.lstSlicerPlots.count()):
            item = self.lstSlicerPlots.item(row)
            isChecked = item.checkState() != QtCore.Qt.Unchecked
            plot = item.text()
            current_slicer_plots[plot] = isChecked
        return current_slicer_plots

    def setSlicerPlotsList(self):
        """
        Create and initially populate the list of slicer plots
        """
        current_slicer_plots = self.getCurrentSlicerPlotDict()
        self.lstSlicerPlots.clear()

        # Fill out list of slicer plots from active_slicer_plots
        for plot_name, plot_widget in self.active_slicer_plots.items():
            checked = QtCore.Qt.Checked if current_slicer_plots.get(str(plot_name), None) else QtCore.Qt.Unchecked

            chkboxItem = QtWidgets.QListWidgetItem(str(plot_name))
            chkboxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkboxItem.setCheckState(checked)
            # Store the plot widget reference in the item
            chkboxItem.setData(QtCore.Qt.UserRole, plot_widget)
            self.lstSlicerPlots.addItem(chkboxItem)

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

        # Delete slicer
        self.cmdDelete.clicked.connect(self.onDelete)

        # Delete slicer plots
        self.cmdDelSlicerPlots.clicked.connect(self.onDeleteSlicerPlots)

        # Stack Plots
        self.cbStackPlots.toggled.connect(self.onStackPlotsChanged)

        # Apply symmetric slicers
        self.cmdApplySym.clicked.connect(self.onApplySymmetricSlicers)

        # Initialize slicer combobox to the current slicer
        current_slicer = type(self.parent.slicer)
        for index in self.callbacks:
            if self.callbacks[index] == current_slicer:
                self.cbSlicer.setCurrentIndex(index)
                break
        # change the slicer type
        self.cbSlicer.currentIndexChanged.connect(self.onSlicerChanged)

        # Replace slicer type
        self.cbSlicerReplace.currentIndexChanged.connect(self.onSlicerReplaceChanged)

        # Updates to the slicer moder must propagate to all plotters
        if self.model is not None:
            self.model.itemChanged.connect(self.onParamChange)

        # selecting/deselecting items in lstPlots enables `Apply`
        self.lstPlots.itemChanged.connect(lambda: self.cmdApply.setEnabled(True))

    def onFocus(self, row, column):
        """Set the focus on the cell (row, column)"""
        selection_model = self.lstParams.selectionModel()
        selection_model.select(self.model.index(row, column), QtGui.QItemSelectionModel.Select)
        self.lstParams.setSelectionModel(selection_model)
        self.lstParams.setCurrentIndex(self.model.index(row, column))

    def onSlicerChanged(self, index: int):
        """change the parameters based on the slicer chosen"""
        if index == 0:  # No interactor
            return
        else:
            slicer = self.callbacks[index]
            if self.active_plots.keys():
                self.parent.setSlicer(slicer=slicer)
                # Reset combo box back to "None" after setting slicer
                self.cbSlicer.blockSignals(True)
                self.cbSlicer.setCurrentIndex(0)
                self.cbSlicer.blockSignals(False)
        self.onParamChange()

    def onSlicerReplaceChanged(self, index: int):
        """replace the slicer with the one chosen"""
        if index == 0:  # No interactor
            return
        else:
            # delete the currently selected slicer
            self.onDelete()
            # add the new slicer
            slicer = self.callbacks[index]
            if self.active_plots.keys():
                self.parent.setSlicer(slicer=slicer)
                # Reset combo box back to "None" after setting slicer
                self.cbSlicerReplace.blockSignals(True)
                self.cbSlicerReplace.setCurrentIndex(0)
                self.cbSlicerReplace.blockSignals(False)
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
        caption = "Save files to:"
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

    def onDelete(self):
        """
        Delete the current slicer
        """
        # Pop up a confirmation dialog
        reply = QtWidgets.QMessageBox.question(
            self,
            "Delete Slicer",
            "Are you sure you want to delete this slicer?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No,
        )
        if reply == QtWidgets.QMessageBox.No:
            return
        # Get the current slicer name
        slicer_item = self.getCheckedSlicer()
        # Remove the slicer from the dictionary
        if slicer_item in self.parent.slicers:
            slicer_obj = self.parent.slicers[slicer_item]
            # Clear only this slicer's markers without affecting other slicers
            # Use clear_markers() which uses connect.clear(*markers) instead of clearall()
            self._clear_slicer_markers(slicer_obj)
            # Remove from dictionary
            del self.parent.slicers[slicer_item]
            # Remove from slicer_models cache
            if slicer_item in self.slicer_models:
                del self.slicer_models[slicer_item]
            # update the canvas
            self.parent.canvas.draw()
            # update the slicer list
            self.updateSlicersList()
            # Select the next remaining slicer if any exist
            if len(self.parent.slicers) > 0:
                # Get the first remaining slicer
                next_slicer_name = next(iter(self.parent.slicers.keys()))
                # Update self.parent.slicer to point to the remaining slicer
                self.parent.slicer = self.parent.slicers[next_slicer_name]
                self.checkSlicerByName(next_slicer_name)
            else:
                # No slicers left, clear the model and slicer reference
                self.parent.slicer = None
                self.setModel(None)

    def deleteAllSlicerPlots(self, quiet=False):
        """
        Check all slicer plots in the list for deletion
        """
        for row in range(self.lstSlicerPlots.count()):
            item = self.lstSlicerPlots.item(row)
            item.setCheckState(QtCore.Qt.Checked)

        self.onDeleteSlicerPlots(quiet=quiet)

    def onDeleteSlicerPlots(self, quiet=False):
        """
        Delete selected slicer plots
        """
        # Pop a confirmation warning
        if not quiet:
            msg = "Are you sure you want to delete the selected plots?"
            reply = QtWidgets.QMessageBox.question(
                self, "Warning", msg, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No
            )

            if reply == QtWidgets.QMessageBox.No:
                return

        # Iterate over the list backwards and delete checked items
        # Backwards to avoid index shifting issues
        for row in range(self.lstSlicerPlots.count()-1, -1, -1):
            item = self.lstSlicerPlots.item(row)
            isChecked = item.checkState() != QtCore.Qt.Unchecked
            if isChecked:
                plot_name = item.text()
                plot_widget = item.data(QtCore.Qt.UserRole)

                # Get the plot ID for PlotHelper cleanup
                plot_id = PlotHelper.idOfPlot(plot_widget)

                # Close the plot window if it exists
                if hasattr(plot_widget, "close"):
                    plot_widget.close()

                # Remove from PlotHelper
                if plot_id:
                    PlotHelper.deletePlot(plot_id)

                # Remove from parent's slicer_plots_dict
                if plot_name in self.parent.slicer_plots_dict:
                    del self.parent.slicer_plots_dict[plot_name]

                # Remove from active plots if present
                if plot_name in self.active_plots:
                    del self.active_plots[plot_name]

                # Remove from the manager's plot_widgets if it exists
                if hasattr(self.parent.manager, "plot_widgets") and plot_id in self.parent.manager.plot_widgets:
                    subwindow = self.parent.manager.plot_widgets[plot_id]
                    # Remove from workspace
                    if hasattr(self.parent.manager.parent, "workspace"):
                        self.parent.manager.parent.workspace().removeSubWindow(subwindow)
                    del self.parent.manager.plot_widgets[plot_id]

                # Remove from the list widget
                self.lstSlicerPlots.takeItem(row)

        # Update the slicer plots list to reflect deletions
        self.setSlicerPlotsList()

    def onApplySymmetricSlicers(self):
        """
        Apply multiple symmetric slicers.
        Removes any existing multi-slicer first since only one can exist at a time.
        """

        # Check if there are existing slicers or slicer plots
        if self.parent.slicers or len(self.parent.slicer_plots_dict) > 0:
            reply = QtWidgets.QMessageBox.question(
                self,
                "Existing Slicers Detected",
                "Applying symmetric slicers will remove existing slicers and their plots.\nDo you want to continue?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                return
            self.parent.onClearSlicer()
            self.deleteAllSlicerPlots(quiet=True)

        # Get the slicer type from combobox
        slicer_type_index = self.cbSlicerType.currentIndex()

        # Map combobox index to SymmetricDefinitions enum
        symmetric_mapping = {
            0: None,
            1: SymmetricDefinitions.SECTOR,
            2: SymmetricDefinitions.WEDGE_Q,
            3: SymmetricDefinitions.WEDGE_PHI,
        }

        slicer_def = symmetric_mapping.get(slicer_type_index)

        if slicer_def is None:
            QtWidgets.QMessageBox.warning(self, "No Slicer Selected", "Please select a slicer type.")
            return

        # Get the multi-slicer class from the enum
        slicer_class = slicer_def.multi_class

        # Get the count
        try:
            count = int(self.txtSlicerCount.text())
            if count < 1:
                raise ValueError("Count must be positive")
        except (ValueError, AttributeError):
            QtWidgets.QMessageBox.warning(
                self, "Invalid Count", "Please enter a valid positive number for slicer count."
            )
            return

        # Warn if count is large
        threshold = 4 if slicer_def == SymmetricDefinitions.SECTOR else 8

        if count > threshold:
            reply = QtWidgets.QMessageBox.question(
                self,
                "That is a lot of slicers!",
                f"Are you sure you want to create more than {threshold} slicers? This may lead to severe performance issues.",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if reply == QtWidgets.QMessageBox.No:
                return

        # Stack plots
        self.parent.stackplots = True

        # Create the multi-slicer
        item = getattr(self.parent, "_item", None)

        # Create slicer with count parameter
        multi_slicer = slicer_class(
            base=self.parent, axes=self.parent.ax, count=count, item=item, color="black", zorder=3
        )

        # Generate a unique name using the display name from the enum
        slicer_name = f"{slicer_def.display_name}_Multi_{count}"

        # Add to parent's slicers dict
        self.parent.slicers[slicer_name] = multi_slicer

        # Set as active slicer
        self.parent.slicer = multi_slicer

        # Set the model
        if hasattr(multi_slicer, "_model"):
            self.setModel(multi_slicer._model)

        # Update the canvas
        self.parent.canvas.draw()

        # Update the slicers list
        self.updateSlicersList()

    def onStackPlotsChanged(self, checked: bool):
        """
        Handle stack plots checkbox change
        """
        self.parent.stackplots = checked

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
        filename = data.name if self.txtExtension.text() == "" else data.name + "_" + str(self.txtExtension.text())
        extension = self.cbSaveExt.currentText()
        filename_ext = filename + extension

        # Assure filename uniqueness
        dst_filename = GuiUtils.findNextFilename(filename_ext, self.save_location)
        if not dst_filename:
            logger.error("Could not find appropriate filename for " + filename_ext)
            return
        filepath = os.path.join(self.save_location, dst_filename)
        return filepath

    def serializeData(self, data, filepath):
        """
        Write out 1D plot in a requested format
        """
        # Choose serializer based on requested extension
        extension = self.cbSaveExt.currentText()
        if "txt" in extension:
            GuiUtils.onTXTSave(data, filepath)
        elif "xml" in extension:
            loader = Loader()
            loader.save(filepath, data, ".xml")
        elif "h5" in extension:
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
        fitting_requested = FittingType(self.cbFitOptions.currentIndex())
        self.sendToFit(items_for_fit, fitting_requested)

    def setModel(self, model):
        """Model setter"""
        # check if parent slicer changed
        current_slicer = type(self.parent.slicer)
        for index in self.callbacks:
            # must use type() for None or just imported type for ! None
            if type(self.callbacks[index]) == current_slicer or self.callbacks[index] == current_slicer:
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

    def check_perspective_and_set_data(self, fitting_requested, perspective_name, items_for_fit):
        isBatch = fitting_requested in BATCH_TYPES
        self.parent.manager.parent.loadedPerspectives[perspective_name].setData(
            data_item=items_for_fit, is_batch=isBatch
        )

    def sendToFit(self, items_for_fit, fitting_requested):
        """
        Send `items_for_fit` to the Fit perspective, in either single fit or batch mode
        """

        if fitting_requested in FITTING_TYPES:
            self.check_perspective_and_set_data(fitting_requested, "Fitting", items_for_fit)
        elif fitting_requested in INVERSION_TYPES:
            self.check_perspective_and_set_data(fitting_requested, "Inversion", items_for_fit)
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

    def _clear_slicer_markers(self, slicer_obj):
        """
        Clear the slicer by calling its clear() method.
        The slicer's clear() method handles all cleanup for that specific slicer type.
        """
        if hasattr(slicer_obj, "clear"):
            slicer_obj.clear()

    def updateSlicersList(self):
        """
        Update the slicers list when slicers are added or removed
        """
        self.setSlicersList()

    def checkSlicerByName(self, slicer_name):
        """
        Check (select) a slicer radio button by name
        """
        if not hasattr(self, "slicerButtonGroup"):
            return

        # Find and check the radio button with this slicer name
        for button in self.slicerButtonGroup.buttons():
            if button.text() == slicer_name:
                button.setChecked(True)
                break

    def onSlicerRadioToggled(self, checked, slicer_name):
        """
        Update parameter list when a slicer radio button is toggled
        """
        if not checked:
            return

        # Check if "None" was selected - don't clear everything, just update the view
        if slicer_name not in self.parent.slicers:
            # No valid slicer selected, but don't clear
            return

        # Update the parameter model to show this slicer's parameters
        if slicer_name in self.slicer_models:
            self.setModel(self.slicer_models[slicer_name])
        elif slicer_name in self.parent.slicers:
            # Get the model from the slicer object
            slicer_obj = self.parent.slicers[slicer_name]
            if hasattr(slicer_obj, "_model"):
                if slicer_name not in self.slicer_models:
                    self.slicer_models[slicer_name] = slicer_obj._model
                self.setModel(slicer_obj._model)


class ProxyModel(QtCore.QIdentityProxyModel):
    """
    Trivial proxy model with custom column edit flag
    """

    def __init__(self, parent=None):
        super(ProxyModel, self).__init__(parent)
        self._columns = set()

    def columnReadOnly(self, column):
        """Returns True if column is read only, false otherwise"""
        return column in self._columns

    def setColumnReadOnly(self, column, readonly=True):
        """Add/removes a column from the readonly list"""
        if readonly:
            self._columns.add(column)
        else:
            self._columns.discard(column)

    def flags(self, index):
        """Sets column flags"""
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
