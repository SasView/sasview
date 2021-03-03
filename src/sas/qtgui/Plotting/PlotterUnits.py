from PyQt5 import QtWidgets
from PyQt5 import QtCore

from sas.sascalc.dataloader.data_info import set_loaded_units
from sas.qtgui.Plotting.UI.UnitPropertiesUI import Ui_unitPropertiesUI


class PlotterUnits(QtWidgets.QDialog, Ui_unitPropertiesUI):

    def __init__(self, parent=None, data=None, x_converter=None,
                 y_converter=None):
        super(PlotterUnits, self).__init__(parent)
        self.setupUi(self)
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.data = data
        if not x_converter and hasattr(self.data[0], 'x_converter'):
            if not self.data[0].x_converter:
                set_loaded_units(self.data[0], 'x', self.data[0].x_unit)
            self.x_converter = self.data[0].x_converter
        else:
            self.x_converter = x_converter
        if not y_converter and hasattr(self.data[0], 'y_converter'):
            if not self.data[0].y_converter:
                set_loaded_units(self.data[0], 'y', self.data[0].y_unit)
            self.y_converter = self.data[0].y_converter
        else:
            self.y_converter = y_converter

        self.allowedXList = self.getAllowedXUnits()
        self.cbX.addItems(self.allowedXList)
        self.allowedYList = self.getAllowedYUnits()
        self.cbY.addItems(self.allowedYList)
        self.cbX.setCurrentIndex(self.allowedXList.index(self.data[0].x_unit))
        self.cbY.setCurrentIndex(self.allowedYList.index(self.data[0].y_unit))

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
