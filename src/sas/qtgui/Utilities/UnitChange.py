from PyQt5 import QtWidgets
from PyQt5 import QtCore

from sas.sascalc.dataloader.data_info import set_loaded_units
from sas.qtgui.Utilities.UI.UnitPropertiesUI import Ui_unitPropertiesUI


class UnitChange(QtWidgets.QDialog, Ui_unitPropertiesUI):

    def __init__(self, parent=None, data=None, x_converter=None,
                 y_converter=None):
        super(UnitChange, self).__init__(parent)
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.data = data[0] if isinstance(data, list) else data

        if not x_converter and hasattr(self.data, 'x_converter'):
            if not self.data.x_converter:
                set_loaded_units(self.data, 'x', self.data.x_unit)
            self.x_converter = self.data.x_converter
        else:
            self.x_converter = x_converter
        if not y_converter and hasattr(self.data, 'y_converter'):
            if not self.data.y_converter:
                set_loaded_units(self.data, 'y', self.data.y_unit)
            self.y_converter = self.data.y_converter
        else:
            self.y_converter = y_converter

        self.allowedXList = self.getAllowedXUnits()
        self.cbX.addItems(self.allowedXList)
        self.allowedYList = self.getAllowedYUnits()
        self.cbY.addItems(self.allowedYList)
        x_index = self.allowedXList.index(self.data.x_unit) if self.data else 0
        y_index = self.allowedYList.index(self.data.y_unit) if self.data else 0
        self.cbX.setCurrentIndex(x_index)
        self.cbY.setCurrentIndex(y_index)

        self.setFixedSize(self.minimumSizeHint())

    def getAllowedXUnits(self):
        """
        Get compatible units from self.x_converter
        :return: List of compatible unit strings for the x-axis
        """
        if self.x_converter:
            return self.x_converter.get_compatible_units()
        else:
            return []

    def getAllowedYUnits(self):
        """
        Get compatible units from self.y_converter
        :return: List of compatible unit strings for the y-axis
        """
        if self.y_converter:
            return self.y_converter.get_compatible_units()
        else:
            return []
