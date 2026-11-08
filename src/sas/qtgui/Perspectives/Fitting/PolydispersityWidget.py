"""
Widget/logic for polydispersity.
"""
import dataclasses
import logging
import os
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting import FittingUtilities
from sas.qtgui.Perspectives.Fitting.DocumentShadow import mirrors
from sas.qtgui.Perspectives.Fitting.FittingConstants import DEFAULT_POLYDISP_FUNCTION
from sas.qtgui.Perspectives.Fitting.model.parameters import ArrayDistribution, Dispersion

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.PolydispersityWidget import Ui_PolydispersityWidgetUI
from sas.qtgui.Perspectives.Fitting.ViewDelegate import PolyViewDelegate

logger = logging.getLogger(__name__)

class PolydispersityWidget(QtWidgets.QWidget, Ui_PolydispersityWidgetUI):
    updateDataSignal = QtCore.Signal()
    deletePlotSignal = QtCore.Signal(str)
    toggledSignal = QtCore.Signal(bool)  # Signal when polydispersity is enabled/disabled

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super(PolydispersityWidget, self).__init__()

        self.setupUi(self)
        self.lstPoly.isEnabled = True
        self.poly_model = FittingUtilities.ToolTippedItemModel()
        self.is2D = False
        self.isActive = False
        self._fitting_widget = parent
        self.logic = parent.logic
        self.poly_params = {}
        self.has_poly_error_column = False
        self.poly_params_to_fit = []
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

    @mirrors('parameters')
    def setPolyModel(self) -> None:
        """
        Set polydispersity values
        """
        if not self.logic.model_parameters:
            return
        self.poly_model.clear()
        self.poly_params = {}

        # Copy: '+=' would append the orientation parameters to the sasmodels
        # ParameterTable itself, duplicating rows on every subsequent call.
        parameters = list(self.logic.model_parameters.form_volume_parameters)
        if self.is2D:
            parameters += self.logic.model_parameters.orientation_parameters

        # Reset delegate column indices to standard (no error column) BEFORE creating parameters
        # This ensures comboboxes are created at the correct column positions
        delegate = self.lstPoly.itemDelegate()
        delegate.poly_parameter = 0
        delegate.poly_pd = 1
        delegate.poly_error = None
        delegate.poly_min = 2
        delegate.poly_max = 3
        delegate.poly_npts = 4
        delegate.poly_nsigs = 5
        delegate.poly_function = 6
        delegate.poly_filename = 7

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
        An edit in the polydispersity table: a controller intent
        """
        page = self._fitting_widget
        if page.controller.muted:
            return
        item = self.poly_model.itemFromIndex(top)
        if page.shadow.depth > 0:
            # A legacy writer: the shadow reads it back when it ends
            page.refreshFitLists()
            return
        key = page.keyAt(item.row(), "poly")
        if key is None:
            return
        column = item.column()
        delegate = self.lstPoly.itemDelegate()
        if column == delegate.poly_parameter:
            page.controller.set_fit_flag(key, item.checkState() == QtCore.Qt.Checked)
            return
        value = FittingUtilities.parse_number(item.text())
        if value is None:
            return
        p = page.document.parameters[key]
        if column in (delegate.poly_min, delegate.poly_max):
            page.controller.set_parameter(key, **{"min" if column == delegate.poly_min else "max": value})
            return
        if column == delegate.poly_pd:
            if p.value != 0.0 and value == 0.0:
                # The polydispersity plot of this parameter is no longer meaningful
                self.deletePlotSignal.emit(key[:-len(".width")])
            page.controller.set_parameter(key, value=value)
        elif column == delegate.poly_npts:
            page.controller.set_parameter(key, dispersion=dataclasses.replace(p.dispersion, npts=int(value)))
        elif column == delegate.poly_nsigs:
            page.controller.set_parameter(key, dispersion=dataclasses.replace(p.dispersion, nsigmas=value))
        else:
            return
        # Update plot
        self.updateDataSignal.emit()

    def checkedListFromModel(self) -> list[str]:
        """
        Returns list of checked parameters for given model
        """
        def isChecked(row: int) -> bool:
            return self.poly_model.item(row, 0).checkState() == QtCore.Qt.Checked

        return [self.polyNameToParam(str(self.poly_model.item(row_index, 0).text()))
                for row_index in range(self.poly_model.rowCount())
                if isChecked(row_index)]

    @mirrors('parameters')
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

        # Emit signal to notify parent that state changed
        self.toggledSignal.emit(isChecked)

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
                        str(npts), str(nsigs), "",'']
        FittingUtilities.addCheckedListToModel(self.poly_model, checked_list)

        all_items = self.poly_model.rowCount()
        self.poly_model.item(all_items-1,0).setData(param_wname, role=QtCore.Qt.UserRole)

        # All possible polydisp. functions as strings in combobox
        func = QtWidgets.QComboBox()
        func.addItems([str(name_disp) for name_disp in POLYDISPERSITY_MODELS])
        # Set the default index
        func.setCurrentIndex(func.findText(DEFAULT_POLYDISP_FUNCTION))
        ind = self.poly_model.index(all_items-1,self.lstPoly.itemDelegate().poly_function)
        self.lstPoly.setIndexWidget(ind, func)
        func.currentIndexChanged.connect(lambda: self.onPolyComboIndexChange(str(func.currentText()), all_items-1))

    @mirrors('parameters')
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
        A distribution chosen for a width: a controller intent. 'array' asks for its weights file
        and makes the width unfitted; a named distribution takes its default npts and nsigmas.
        """
        page = self._fitting_widget
        if page.controller.muted:
            return
        key = page.keyAt(row_index, "poly")
        if key is None or page.shadow.building:
            return
        current = page.document.parameters[key].dispersion
        if combo_string == "array":
            try:
                array = self.loadPolydispArray(row_index)
            except OSError:
                # Cancelled or unreadable: show the current distribution again
                combo = self.lstPoly.indexWidget(self.poly_model.index(row_index, self.lstPoly.itemDelegate().poly_function))
                if combo is not None:
                    combo.blockSignals(True)
                    combo.setCurrentIndex(combo.findText(current.type))
                    combo.blockSignals(False)
                return
            page.controller.set_parameter(key, dispersion=Dispersion(current.npts, current.nsigmas, "array", array),
                                          fit=False)
            return
        if combo_string not in POLYDISPERSITY_MODELS:
            logger.error("Error in setting the dispersion model. Reverting to Gaussian.")
            combo_string = "gaussian"
        defaults = POLYDISPERSITY_MODELS[combo_string].default
        page.controller.set_parameter(key, dispersion=Dispersion(defaults['npts'], defaults['nsigmas'], combo_string))

    def loadPolydispArray(self, row_index: int) -> ArrayDistribution:
        """
        Show the load file dialog and read the weights file; OSError if none is chosen
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

        return ArrayDistribution(tuple(values), tuple(weights), os.path.basename(str(datafile)))

    def iterateOverPolyModel(self, func: Any) -> None:
        """
        Take func and throw it inside the poly model row loop
        """
        for row_i in range(self.poly_model.rowCount()):
            func(row_i)

    @mirrors('parameters')
    def updatePolyModelFromList(self, param_dict: dict[str, tuple[float, float]]) -> None:
        """
        Update the polydispersity model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if not param_dict:
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

