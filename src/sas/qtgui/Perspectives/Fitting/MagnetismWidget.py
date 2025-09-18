"""
Widget/logic for magnetism.
"""
import logging
from importlib import resources
from typing import Any

from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Perspectives.Fitting import FittingUtilities

# Local UI
from sas.qtgui.Perspectives.Fitting.UI.MagnetismWidget import Ui_MagnetismWidgetUI
from sas.qtgui.Perspectives.Fitting.ViewDelegate import MagnetismViewDelegate

logger = logging.getLogger(__name__)


class MagnetismWidget(QtWidgets.QWidget, Ui_MagnetismWidgetUI):
    cmdFitSignal = QtCore.Signal()
    updateDataSignal = QtCore.Signal()
    iterateOverModelSignal = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None, logic: Any | None = None) -> None:
        super(MagnetismWidget, self).__init__()

        self.setupUi(self)
        self.lstMagnetic.isEnabled = True
        self._magnet_model = FittingUtilities.ToolTippedItemModel()
        self.is2D = False
        self.isActive = False
        self.logic = parent.logic
        self.magnet_params = {}
        self.has_magnet_error_column = False
        self.magnet_params_to_fit = []
        # Magnetism widget table default index for function combobox
        # self.orig_poly_index = 4
        FittingUtilities.setTableProperties(self.lstMagnetic)
        self.lstMagnetic.setItemDelegate(MagnetismViewDelegate(self))
        self.lstMagnetic.installEventFilter(self)
        self._magnet_model.dataChanged.connect(self.onMagnetModelChange)

        self.lstMagnetic.setModel(self._magnet_model)
        FittingUtilities.setTableProperties(self.lstMagnetic)
        # self.lstMagnetic.itemDelegate().combo_updated.connect(self.onPolyComboIndexChange)
        # self.lstMagnetic.itemDelegate().filename_updated.connect(self.onPolyFilenameChange)

        self.lstMagnetic.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.lstMagnetic.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)
        self.cmdMagneticDisplay.clicked.connect(self.onDisplayMagneticAngles)

        # Magnetic angles explained in one picture
        self.magneticAnglesWidget = QtWidgets.QWidget()
        labl = QtWidgets.QLabel(self.magneticAnglesWidget)
        with resources.open_binary("sas.qtgui.images", "M_angles_pic.png") as file:
            image_data = file.read()
            pixmap = QtGui.QPixmap()
            pixmap.loadFromData(image_data)
        labl.setPixmap(pixmap)
        self.magneticAnglesWidget.setFixedSize(pixmap.width(), pixmap.height())

    def onDisplayMagneticAngles(self) -> None:
        """
        Display a simple image showing direction of magnetic angles
        """
        self.magneticAnglesWidget.show()

    def setMagneticModel(self) -> None:
        """
        Set magnetism values on model
        """
        self.magnet_params = {}
        if not self.logic.model_parameters:
            return
        self._magnet_model.clear()
        # default initial value
        m0 = 0.5
        for param in self.logic.model_parameters.call_parameters:
            if param.type != 'magnetic':
                continue
            if "M0" in param.name:
                m0 += 0.5
                value = m0
            else:
                value = param.default
            self.addCheckedMagneticListToModel(param, value)

        FittingUtilities.addHeadersToModel(self._magnet_model)

    def getParamNamesMagnet(self) -> list[str]:
        """
        Return list of magnetic parameters for the current model
        """
        magnetic_model_params = [self._magnet_model.item(row).text()
                            for row in range(self._magnet_model.rowCount())
                            if self._magnet_model.item(row, 0).isCheckable()]
        return magnetic_model_params

    def onMagnetModelChange(self, top: QtCore.QModelIndex, bottom: QtCore.QModelIndex) -> None:
        """
        Callback method for updating the sasmodel magnetic parameters with the GUI values
        """
        item = self._magnet_model.itemFromIndex(top)
        model_column = item.column()
        model_row = item.row()
        name_index = self._magnet_model.index(model_row, 0)
        parameter_name = str(self._magnet_model.data(name_index))

        if model_column == 0:
            value = item.checkState()
            if value == QtCore.Qt.Checked:
                self.magnet_params_to_fit.append(parameter_name)
            else:
                if parameter_name in self.magnet_params_to_fit:
                    self.magnet_params_to_fit.remove(parameter_name)
            self.cmdFitSignal.emit()
            return

        # Extract changed value
        try:
            value = GuiUtils.toDouble(item.text())
        except TypeError:
            # Unparsable field
            return
        delegate = self.lstMagnetic.itemDelegate()

        if model_column > 1:
            if model_column == delegate.mag_min:
                pos = 1
            elif model_column == delegate.mag_max:
                pos = 2
            elif model_column == delegate.mag_unit:
                pos = 0
            else:
                # For all other values sent here (e.g. the error column, do nothing)
                return
            # min/max to be changed in self.logic.kernel_module.details[parameter_name] = ['Ang', 0.0, inf]
            self.logic.kernel_module.details[parameter_name][pos] = value
        else:
            self.magnet_params[parameter_name] = value
            self.logic.kernel_module.setParam(parameter_name, value)
            # Update plot
            self.updateDataSignal.emit()

    def updateModel(self, model: Any | None = None) -> None:
        # add magnetic parameters if asked
        if self.isActive and self._magnet_model.rowCount() > 0:
            for key, value in self.magnet_params.items():
                model.setParam(key, value)

    def iterateOverMagnetModel(self, func: Any) -> None:
        """
        Take func and throw it inside the magnet model row loop
        """
        for row_i in range(self._magnet_model.rowCount()):
            func(row_i)

    def updateFullMagnetModel(self, param_dict: dict[str, list[str]]) -> None:
        """
        Update the magnetism model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            if row >= self._magnet_model.rowCount():
                return
            param_name = str(self._magnet_model.item(row, 0).text()).rsplit()[-1]
            if param_name not in list(param_dict.keys()):
                return
            # checkbox state
            param_checked = QtCore.Qt.Checked if param_dict[param_name][0] == "True" else QtCore.Qt.Unchecked
            self._magnet_model.item(row,0).setCheckState(param_checked)

            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
            self._magnet_model.item(row, 1).setText(param_repr)

            # Potentially the error column
            ioffset = 0
            joffset = 0
            if len(param_dict[param_name])>4:
                ioffset = 1
            if self.has_magnet_error_column:
                joffset = 1
            # min
            param_repr = GuiUtils.formatNumber(param_dict[param_name][2+ioffset], high=True)
            self._magnet_model.item(row, 2+joffset).setText(param_repr)
            # max
            param_repr = GuiUtils.formatNumber(param_dict[param_name][3+ioffset], high=True)
            self._magnet_model.item(row, 3+joffset).setText(param_repr)

        self.iterateOverMagnetModel(updateFittedValues)

    def updateMagnetModelFromList(self, param_dict: dict[str, tuple[float, float]]) -> None:
        """
        Update the magnetic model with new parameters, create the errors column
        """
        assert isinstance(param_dict, dict)
        if self._magnet_model.rowCount() == 0:
            return

        def updateFittedValues(row):
            # Utility function for main model update
            # internal so can use closure for param_dict
            if self._magnet_model.item(row, 0) is None:
                return
            param_name = str(self._magnet_model.item(row, 0).text())
            if param_name not in list(param_dict.keys()):
                return
            # modify the param value
            param_repr = GuiUtils.formatNumber(param_dict[param_name][0], high=True)
            self._magnet_model.item(row, 1).setText(param_repr)
            self.logic.kernel_module.setParam(param_name, param_dict[param_name][0])
            if self.has_magnet_error_column:
                error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                self._magnet_model.item(row, 2).setText(error_repr)

        def createErrorColumn(row):
            # Utility function for error column update
            item = QtGui.QStandardItem()
            def createItem(param_name):
                if param_name in self.magnet_params_to_fit:
                    error_repr = GuiUtils.formatNumber(param_dict[param_name][1], high=True)
                else:
                    error_repr = ""
                item.setText(error_repr)
            def curr_param():
                return str(self._magnet_model.item(row, 0).text())

            [createItem(param_name) for param_name in list(param_dict.keys()) if curr_param() == param_name]

            error_column.append(item)

        self.iterateOverMagnetModel(updateFittedValues)

        if self.has_magnet_error_column:
            self._magnet_model.removeColumn(2)

        self.lstMagnetic.itemDelegate().addErrorColumn()
        error_column = []
        self.iterateOverMagnetModel(createErrorColumn)

        # switch off reponse to model change
        self._magnet_model.insertColumn(2, error_column)
        FittingUtilities.addErrorHeadersToModel(self._magnet_model)

        self.has_magnet_error_column = True

    def gatherMagnetParams(self, row):
        """
        Create list of magnetic parameters based on _magnet_model
        """
        param_name = str(self._magnet_model.item(row, 0).text())
        param_checked = str(self._magnet_model.item(row, 0).checkState() == QtCore.Qt.Checked)
        param_value = str(self._magnet_model.item(row, 1).text())
        param_error = None
        column_offset = 0
        if self.has_magnet_error_column:
            column_offset = 1
            param_error = str(self._magnet_model.item(row, 1+column_offset).text())
        param_min = str(self._magnet_model.item(row, 2+column_offset).text())
        param_max = str(self._magnet_model.item(row, 3+column_offset).text())
        param_list = [[param_name, param_checked, param_value,
                        param_error, param_min, param_max, ()]]
        return param_list

    def addCheckedMagneticListToModel(self, param: Any, value: float) -> None:
        """
        Wrapper for model update with a subset of magnetic parameters
        """
        try:
            basename, _ = param.name.rsplit('_', 1)
        except ValueError:
            basename = param.name
        if basename in self.logic.shell_names:
            try:
                shell_index = int(basename[-2:])
            except ValueError:
                shell_index = int(basename[-1:])

            if shell_index > self.logic.current_shell_displayed:
                return

        checked_list = [param.name,
                        str(value),
                        str(param.limits[0]),
                        str(param.limits[1]),
                        param.units]

        self.magnet_params[param.name] = value

        FittingUtilities.addCheckedListToModel(self._magnet_model, checked_list)
        all_items = self._magnet_model.rowCount()
        self._magnet_model.item(all_items-1,0).setData(param.name, role=QtCore.Qt.UserRole)
