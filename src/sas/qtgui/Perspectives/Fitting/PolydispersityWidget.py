"""
Widget/logic for polydispersity.
"""
import logging
import os
from typing import Any

import numpy as np
from PySide6 import QtCore, QtGui, QtWidgets

from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting import FittingUtilities

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.PolydispersityWidget import Ui_PolydispersityWidgetUI
from sas.qtgui.Perspectives.Fitting.ViewDelegate import PolyViewDelegate

DEFAULT_POLYDISP_FUNCTION = 'gaussian'
logger = logging.getLogger(__name__)

class PolydispersityWidget(QtWidgets.QWidget, Ui_PolydispersityWidgetUI):
    cmdFitSignal = QtCore.Signal()
    updateDataSignal = QtCore.Signal()
    iterateOverModelSignal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super(PolydispersityWidget, self).__init__()

        self.setupUi(self)
        self.lstPoly.isEnabled = True
        self.poly_model = FittingUtilities.ToolTippedItemModel()
        self.is2D = False
        self.isActive = False
        self.logic = parent.logic
        self.poly_params = {}
        self.has_poly_error_column = False
        self.poly_params_to_fit = []
        # Polydisp widget table default index for function combobox
        self.orig_poly_index = 4
        FittingUtilities.setTableProperties(self.lstPoly)
        self.lstPoly.setItemDelegate(PolyViewDelegate(self))
        self.lstPoly.installEventFilter(self)
        self.poly_model.dataChanged.connect(self.onPolyModelChange)

        self.lstPoly.setModel(self.poly_model)

        self.lstPoly.itemDelegate().combo_updated.connect(self.onPolyComboIndexChange)
        self.lstPoly.itemDelegate().filename_updated.connect(self.onPolyFilenameChange)

        self.lstPoly.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.lstPoly.customContextMenuRequested.connect(self.showModelContextMenu)
        self.lstPoly.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

    def polyModel(self) -> FittingUtilities.ToolTippedItemModel:
        """
        Return the polydispersity model
        """
        return self.poly_model

    def setPolyModel(self) -> None:
        """
        Set polydispersity values
        """
        if not self.logic.model_parameters:
            return
        self.poly_model.clear()
        self.poly_params = {}

        parameters = self.logic.model_parameters.form_volume_parameters
        if self.is2D:
            parameters += self.logic.model_parameters.orientation_parameters

        [self.setPolyModelParameters(i, param) for i, param in \
            enumerate(parameters) if param.polydisperse]

        FittingUtilities.addPolyHeadersToModel(self.poly_model)
        self.poly_params_to_fit = self.checkedListFromModel()

    @staticmethod
    def polyNameToParam(param_name: str) -> str:
        """
        Translate polydisperse QTable representation into parameter name
        """
        param_name = param_name.replace('Distribution of ', '')
        param_name += '.width'
        return param_name

    def getParamNamesPoly(self) -> list[str]:
        """
        Return list of polydisperse parameters for the current model
        """
        if not self.isActive:
            return []
        poly_model_params = [self.polyNameToParam(self.poly_model.item(row).text())
                             for row in range(self.poly_model.rowCount())]
        return poly_model_params

    def onPolyModelChange(self, top: QtCore.QModelIndex) -> None:
        """
        Callback method for updating the main model and sasmodel
        parameters with the GUI values in the polydispersity view
        """
        item = self.poly_model.itemFromIndex(top)
        model_column = item.column()
        model_row = item.row()
        name_index = self.poly_model.index(model_row, 0)
        parameter_name = str(name_index.data()) # "distribution of sld" etc.
        parameter_name_w = self.polyNameToParam(parameter_name)
        # Needs to retrieve also name of main parameter in order to update
        # corresponding values in FitPage
        parameter_name = parameter_name.rsplit()[-1]

        delegate = self.lstPoly.itemDelegate()

        # Extract changed value.
        if model_column == delegate.poly_parameter:
            # Is the parameter checked for fitting?
            value = item.checkState()

            if value == QtCore.Qt.Checked:
                self.poly_params_to_fit.append(parameter_name_w)
            else:
                if parameter_name_w in self.poly_params_to_fit:
                    self.poly_params_to_fit.remove(parameter_name_w)
            self.cmdFitSignal.emit()
            # self.updateUndo()

        elif model_column in [delegate.poly_min, delegate.poly_max]:
            try:
                value = GuiUtils.toDouble(item.text())
            except TypeError:
                # Can't be converted properly, bring back the old value and exit
                return

            current_details = self.logic.kernel_module.details[parameter_name_w]
            if self.has_poly_error_column:
                # err column changes the indexing
                current_details[model_column-2] = value
            else:
                current_details[model_column-1] = value

        elif model_column == delegate.poly_function:
            # name of the function - just pass
            pass

        else:
            try:
                value = GuiUtils.toDouble(item.text())
            except TypeError:
                # Can't be converted properly, bring back the old value and exit
                return

            # Update the sasmodel
            # PD[ratio] -> width, npts -> npts, nsigs -> nsigmas
            if model_column in delegate.columnDict():
                # Map the column to the poly param that was changed
                associations = {1: "width", delegate.poly_npts: "npts", delegate.poly_nsigs: "nsigmas"}
                p_name = f"{parameter_name}.{associations.get(model_column, 'width')}"
                self.poly_params[p_name] = value
                self.logic.kernel_module.setParam(p_name, value)

                # Update plot
                self.updateDataSignal.emit()

        # Update main model for display
        self.iterateOverModelSignal.emit()

    def checkedListFromModel(self) -> list[str]:
        """
        Returns list of checked parameters for given model
        """
        def isChecked(row: int) -> bool:
            return self.poly_model.item(row, 0).checkState() == QtCore.Qt.Checked

        return [self.polyNameToParam(str(self.poly_model.item(row_index, 0).text()))
                for row_index in range(self.poly_model.rowCount())
                if isChecked(row_index)]

    def togglePoly(self, isChecked: bool = True) -> None:
        """
        Toggle polydispersity
        """
        self.isActive = isChecked
        # Set sasmodel polydispersity to 0 if polydispersity is unchecked, if not use Qmodel values
        if self.poly_model.rowCount() > 0:
            for key, value in self.poly_params.items():
                if key[-6:] == '.width':
                    self.logic.kernel_module.setParam(key, (value if isChecked else 0))

    def updateModel(self, model: Any | None = None) -> None:
        # add polydisperse parameters if asked
        if self.isActive and self.poly_model.rowCount() > 0:
            for key, value in self.poly_params.items():
                model.setParam(key, value)

    def setPolyModelParameters(self, i: int, param: Any) -> None:
        """
        Standard of multishell poly parameter driver
        """
        param_name = param.name
        # see it if the parameter is multishell
        if '[' in param.name:
            # Skip empty shells
            if self.logic.current_shell_displayed == 0:
                return
            else:
                # Create as many entries as current shells
                for ishell in range(1, self.logic.current_shell_displayed+1):
                    # Remove [n] and add the shell numeral
                    name = param_name[0:param_name.index('[')] + str(ishell)
                    self.addNameToPolyModel(name)
        else:
            # Just create a simple param entry
            self.addNameToPolyModel(param_name)

    def addNameToPolyModel(self, param_name: str) -> None:
        """
        Creates a checked row in the poly model with param_name
        """
        # Polydisp. values from the sasmodel
        param_wname = param_name + '.width'
        width = self.logic.kernel_module.getParam(param_wname)
        npts = self.logic.kernel_module.getParam(param_name + '.npts')
        nsigs = self.logic.kernel_module.getParam(param_name + '.nsigmas')
        _, min, max = self.logic.kernel_module.details[param_wname]

        # Update local param dict
        self.poly_params[param_wname] = width
        self.poly_params[param_name + '.npts'] = npts
        self.poly_params[param_name + '.nsigmas'] = nsigs

        # Construct a row with polydisp. related variable.
        # This will get added to the polydisp. model
        # Note: last argument needs extra space padding for decent display of the control
        checked_list = ["Distribution of " + param_name, str(width),
                        str(min), str(max),
                        str(npts), str(nsigs), "gaussian      ",'']
        FittingUtilities.addCheckedListToModel(self.poly_model, checked_list)

        all_items = self.poly_model.rowCount()
        self.poly_model.item(all_items-1,0).setData(param_wname, role=QtCore.Qt.UserRole)

        # All possible polydisp. functions as strings in combobox
        func = QtWidgets.QComboBox()
        func.addItems([str(name_disp) for name_disp in POLYDISPERSITY_MODELS.keys()])
        # Set the default index
        func.setCurrentIndex(func.findText(DEFAULT_POLYDISP_FUNCTION))
        ind = self.poly_model.index(all_items-1,self.lstPoly.itemDelegate().poly_function)
        self.lstPoly.setIndexWidget(ind, func)
        func.currentIndexChanged.connect(lambda: self.onPolyComboIndexChange(str(func.currentText()), all_items-1))

    def onPolyFilenameChange(self, row_index: int) -> None:
        """
        Respond to filename_updated signal from the delegate
        """
        # For the given row, invoke the "array" combo handler
        array_caption = 'array'

        # Get the combo box reference
        ind = self.poly_model.index(row_index, self.lstPoly.itemDelegate().poly_function)
        widget = self.lstPoly.indexWidget(ind)

        # Update the combo box so it displays "array"
        widget.blockSignals(True)
        widget.setCurrentIndex(self.lstPoly.itemDelegate().POLYDISPERSE_FUNCTIONS.index(array_caption))
        widget.blockSignals(False)

        # Invoke the file reader
        self.onPolyComboIndexChange(array_caption, row_index)

    def onPolyComboIndexChange(self, combo_string: str, row_index: int) -> None:
        """
        Modify polydisp. defaults on function choice
        """
        # Get npts/nsigs for current selection
        param = self.logic.model_parameters.form_volume_parameters[row_index]
        file_index = self.poly_model.index(row_index, self.lstPoly.itemDelegate().poly_function)
        combo_box = self.lstPoly.indexWidget(file_index)
        try:
            self.disp_model = POLYDISPERSITY_MODELS[combo_string]()
        except IndexError:
            logger.error("Error in setting the dispersion model. Reverting to Gaussian.")
            self.disp_model = POLYDISPERSITY_MODELS['gaussian']()

        if combo_string == 'array':
            try:
                # assure the combo is at the right index
                combo_box.blockSignals(True)
                combo_box.setCurrentIndex(combo_box.findText(combo_string))
                combo_box.blockSignals(False)
                # Load the file
                self.loadPolydispArray(row_index)
                self.logic.kernel_module.set_dispersion(param.name, self.disp_model)
                # uncheck the parameter
                self.poly_model.item(row_index, 0).setCheckState(QtCore.Qt.Unchecked)
                # disable the row
                lo = self.lstPoly.itemDelegate().poly_parameter
                hi = self.lstPoly.itemDelegate().poly_function
                self.poly_model.blockSignals(True)
                [self.poly_model.item(row_index, i).setEnabled(False) for i in range(lo, hi)]
                self.poly_model.blockSignals(False)
                return
            except OSError:
                combo_box.setCurrentIndex(self.orig_poly_index)
                # Pass for cancel/bad read
                pass
        else:
            self.logic.kernel_module.set_dispersion(param.name, self.disp_model)

        # Enable the row in case it was disabled by Array
        self.poly_model.blockSignals(True)
        [self.poly_model.item(row_index, i).setEnabled(True) for i in range(7)]
        file_index = self.poly_model.index(row_index, self.lstPoly.itemDelegate().poly_filename)
        self.poly_model.setData(file_index, "")
        self.poly_model.blockSignals(False)

        npts_index = self.poly_model.index(row_index, self.lstPoly.itemDelegate().poly_npts)
        nsigs_index = self.poly_model.index(row_index, self.lstPoly.itemDelegate().poly_nsigs)

        npts = POLYDISPERSITY_MODELS[str(combo_string)].default['npts']
        nsigs = POLYDISPERSITY_MODELS[str(combo_string)].default['nsigmas']

        self.poly_model.setData(npts_index, npts)
        self.poly_model.setData(nsigs_index, nsigs)

        if combo_box is not None:
            self.orig_poly_index = combo_box.currentIndex()

    def loadPolydispArray(self, row_index: int) -> None:
        """
        Show the load file dialog and loads requested data into state
        """
        datafile = QtWidgets.QFileDialog.getOpenFileName(
            self, "Choose a weight file", "", "All files (*.*)", None,
            QtWidgets.QFileDialog.DontUseNativeDialog)[0]

        if not datafile:
            logger.info("No weight data chosen.")
            raise OSError

        values = []
        weights = []
        def appendData(data_tuple: list[str]) -> None:
            """
            Fish out floats from a tuple of strings
            """
            try:
                values.append(float(data_tuple[0]))
                weights.append(float(data_tuple[1]))
            except (ValueError, IndexError):
                # just pass through if line with bad data
                return

        with open(datafile) as column_file:
            column_data = [line.rstrip().split() for line in column_file.readlines()]
            [appendData(line) for line in column_data]

        # If everything went well - update the sasmodel values
        self.disp_model.set_weights(np.array(values), np.array(weights))
        # + update the cell with filename
        fname = os.path.basename(str(datafile))
        fname_index = self.poly_model.index(row_index, self.lstPoly.itemDelegate().poly_filename)
        self.poly_model.setData(fname_index, fname)

    def iterateOverPolyModel(self, func: Any) -> None:
        """
        Take func and throw it inside the poly model row loop
        """
        for row_i in range(self.poly_model.rowCount()):
            func(row_i)

    def updatePolyModelFromList(self, param_dict: dict[str, tuple[float, float]]) -> None:
        """
        Update the polydispersity model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def updateFittedValues(row_i: int) -> None:
            # Utility function for main model update
            # internal so can use closure for param_dict
            if row_i >= self.poly_model.rowCount():
                return
            param_name = str(self.poly_model.item(row_i, 0).text()).rsplit()[-1] + '.width'
            if param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self.poly_model.item(row_i, 1).setText(param_repr)
            self.logic.kernel_module.setParam(param_name, param_dict[param_name][0])
            if self.has_poly_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self.poly_model.item(row_i, 2).setText(error_repr)

        def createErrorColumn(row_i: int) -> None:
            # Utility function for error column update
            if row_i >= self.poly_model.rowCount():
                return
            item = QtGui.QStandardItem()

            def createItem(param_name: str) -> None:
                if param_name in self.poly_params_to_fit:
                    error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                else:
                    error_repr = ""
                item.setText(error_repr)

            def poly_param() -> str:
                return str(self.poly_model.item(row_i, 0).text()).rsplit()[-1] + '.width'

            [createItem(param_name) for param_name in list(param_dict.keys()) if poly_param() == param_name]

            error_column.append(item)

        self.iterateOverPolyModel(updateFittedValues)

        if self.has_poly_error_column:
            self.poly_model.removeColumn(2)

        self.lstPoly.itemDelegate().addErrorColumn()
        error_column = []
        self.iterateOverPolyModel(createErrorColumn)

        # switch off reponse to model change
        self.poly_model.insertColumn(2, error_column)
        FittingUtilities.addErrorPolyHeadersToModel(self.poly_model)

        self.has_poly_error_column = True

    def resetParameters(self) -> None:
        """
        Reset polydispersity parameters
        """
        self.poly_params_to_fit = []

    def updateFullPolyModel(self, param_dict: dict[str, list[str]]) -> None:
        """
        Update the polydispersity model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not dict:
            return

        def updateFittedValues(row: int) -> None:
            # Utility function for main model update
            # internal so can use closure for param_dict
            if row >= self.poly_model.rowCount():
                return
            param_name = str(self.poly_model.item(row, 0).text()).rsplit()[-1] + '.width'
            if param_name not in list(param_dict.keys()):
                return
            # checkbox state
            param_checked = QtCore.Qt.Checked if param_dict[param_name][0] == "True" else QtCore.Qt.Unchecked
            self.poly_model.item(row,0).setCheckState(param_checked)

            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
            self.poly_model.item(row, 1).setText(param_repr)

            # Potentially the error column
            ioffset = 0
            joffset = 0
            if len(param_dict[param_name])>7:
                ioffset = 1
            if self.has_poly_error_column:
                joffset = 1
            # min
            param_repr = GuiUtils.formatNumber(param_dict[param_name][2+ioffset], high=True)
            self.poly_model.item(row, 2+joffset).setText(param_repr)
            # max
            param_repr = GuiUtils.formatNumber(param_dict[param_name][3+ioffset], high=True)
            self.poly_model.item(row, 3+joffset).setText(param_repr)
            # Npts
            param_repr = GuiUtils.formatNumber(param_dict[param_name][4+ioffset], high=True)
            self.poly_model.item(row, 4+joffset).setText(param_repr)
            # Nsigs
            param_repr = GuiUtils.formatNumber(param_dict[param_name][5+ioffset], high=True)
            self.poly_model.item(row, 5+joffset).setText(param_repr)
            # Function
            param_repr = param_dict[param_name][6+ioffset]
            self.poly_model.item(row, 6+joffset).setText(param_repr)
            index = self.poly_model.index(row, 6+joffset)
            widget = self.lstPoly.indexWidget(index)
            if widget is not None and isinstance(widget, QtWidgets.QComboBox):
                func_index = widget.findText(param_repr)
                widget.setCurrentIndex(func_index)

            self.setFocus()

        self.iterateOverPolyModel(updateFittedValues)

    def gatherPolyParams(self, row: int) -> list[list[str]]:
        """
        Create list of polydisperse parameters based on _poly_model
        """
        param_list = []
        param_name = str(self.poly_model.item(row, 0).text()).split()[-1]
        param_checked = str(self.poly_model.item(row, 0).checkState() == QtCore.Qt.Checked)
        param_value = str(self.poly_model.item(row, 1).text())
        param_error = None
        column_offset = 0
        if self.has_poly_error_column:
            column_offset = 1
            param_error = str(self.poly_model.item(row, 1+column_offset).text())
        param_min   = str(self.poly_model.item(row, 2+column_offset).text())
        param_max   = str(self.poly_model.item(row, 3+column_offset).text())
        param_npts  = str(self.poly_model.item(row, 4+column_offset).text())
        param_nsigs = str(self.poly_model.item(row, 5+column_offset).text())
        param_fun   = str(self.poly_model.item(row, 6+column_offset).text()).rstrip()
        index = self.poly_model.index(row, 6+column_offset)
        widget = self.lstPoly.indexWidget(index)
        if widget is not None and isinstance(widget, QtWidgets.QComboBox):
            param_fun = widget.currentText()
        # width
        name = param_name+".width"
        param_list.append([name, param_checked, param_value, param_error,
                            param_min, param_max, param_npts, param_nsigs, param_fun])
        return param_list

