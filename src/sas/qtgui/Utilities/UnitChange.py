"""
A simple GUI widget to change the I and Q units for the data set or plot that triggered the window.

This currently only converts I and Q units, but could be extended to include any value found in the data.
"""

from typing import Optional
from PyQt5 import QtWidgets
from PyQt5 import QtCore

from sas.sascalc.dataloader.data_info import set_loaded_units
from sas.qtgui.Utilities.UI.UnitPropertiesUI import Ui_unitPropertiesUI


class UnitChange(QtWidgets.QDialog, Ui_unitPropertiesUI):

    def __init__(self, parent=None, data=None, q_converter=None, i_converter=None):
        # type: (Optional[QtWidgets.QWidget], Optional[Data1D|Data2D], Optional[Converter], Optional[Converter]) -> None
        """Constructs a modal window that allows the end-user to convert the units for a data set

        :param parent: Any QWidget that called the UnitChange.
        :param data: A Data1D or Data2D object that will be converted
        :param q_converter: A Converter() that is ready to convert the Q data. One will be generated if None passed
        :param i_converter: A Converter() that is ready to convert the I data. One will be generated if None passed
        """
        super(UnitChange, self).__init__(parent)
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)
        # Set data to a single Data1D or Data2D object
        self.data = data[0] if isinstance(data, list) else data

        # Define Q unit converter for the window
        if not q_converter and hasattr(self.data, 'Q_unit'):
            # 2D data
            if not self.data.x_converter:
                set_loaded_units(self.data, 'x', self.data.x_unit)
                set_loaded_units(self.data, 'y', self.data.y_unit)
            self.q_converter = self.data.x_converter
            self.q_unit = self.data.Q_unit
        elif not q_converter and hasattr(self.data, 'x_converter'):
            # 1D data
            if not self.data.x_converter:
                set_loaded_units(self.data, 'x', self.data.x_unit)
            self.q_converter = self.data.x_converter
            self.q_unit = self.data.x_unit
        else:
            # No data
            self.q_converter = q_converter
            self.q_unit = self.data.x_unit if self.data else 'None'

        # Define the Intensity converter for the window
        # Define Q unit converter for the window
        if not i_converter and hasattr(self.data, 'I_unit'):
            # 2D data
            if not self.data.z_converter:
                set_loaded_units(self.data, 'z', self.data.z_unit)
            self.i_converter = self.data.z_converter
            self.i_unit = self.data.I_unit
        elif not i_converter and hasattr(self.data, 'y_converter'):
            # 1D data
            if not self.data.y_converter:
                set_loaded_units(self.data, 'y', self.data.y_unit)
            self.i_converter = self.data.y_converter
            self.i_unit = self.data.z_unit if hasattr(self.data, 'z_unit') else self.data.y_unit
        else:
            # No data
            self.i_converter = i_converter
            self.i_unit = self.data.y_unit if self.data else 'None'

        # Populate the I and Q combo boxes with a list of units that are compatible with the data units
        self.allowedQList = self.getAllowedQUnits()
        self.cbX.addItems(self.allowedQList)
        self.allowedIList = self.getAllowedIUnits()
        self.cbY.addItems(self.allowedIList)
        # Go to the Q and I indices for the units in the data set
        q_index = self.allowedQList.index(self.q_unit) if self.q_unit in self.allowedQList else 0
        i_index = self.allowedIList.index(self.i_unit) if self.i_unit in self.allowedIList else 0
        self.cbX.setCurrentIndex(q_index)
        self.cbY.setCurrentIndex(i_index)

        self.setFixedSize(self.minimumSizeHint())

    def getAllowedQUnits(self):
        # type: () -> [str]
        """Get compatible units from self.x_converter

        :return: List of compatible unit strings for the x-axis
        """
        if self.q_converter:
            return self.q_converter.get_compatible_units()
        else:
            return []

    def getAllowedIUnits(self):
        # type: () -> [str]
        """Get compatible units from self.y_converter

        :return: List of compatible unit strings for the y-axis
        """
        if self.i_converter:
            return self.i_converter.get_compatible_units()
        else:
            return []