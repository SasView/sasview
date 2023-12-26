from PySide6 import QtGui, QtCore, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils
from abc import ABC, abstractmethod

class SlicerParameterWidget(ABC, QtWidgets.QWidget):
    """ Slicer parameter"""

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        # Model representation of local parameters
        self._qt_item_model = QtGui.QStandardItemModel()

        self.update_model = True
        self._qt_item_model.itemChanged.connect(self.setParamsFromModelItem)

    def setModelFromParams(self):
        """
        Set up the Qt model for data handling between controls
        """
        parameters = self.getParams()
        self._qt_item_model.removeRows(0, self._qt_item_model.rowCount())

        # Crete/overwrite model items
        for parameter in list(parameters.keys()):
            item1 = QtGui.QStandardItem(parameter)
            if isinstance(parameters[parameter], bool):
                item2 = QtGui.QStandardItem(parameters[parameter])
                item2.setCheckable(True)
                item2.setCheckState(QtCore.Qt.Checked if parameters[parameter] else QtCore.Qt.Unchecked)
            else:
                item2 = QtGui.QStandardItem(GuiUtils.formatNumber(parameters[parameter]))

            self._qt_item_model.appendRow([item1, item2])
        self._qt_item_model.setHeaderData(0, QtCore.Qt.Horizontal, "Parameter")
        self._qt_item_model.setHeaderData(1, QtCore.Qt.Horizontal, "Value")

    def setParamsFromModel(self):
        """
        Set up the params dictionary based on the current model content.
        """
        params = self.getParams()
        for row_index in range(self._qt_item_model.rowCount()):
            # index = self._model.indexFromItem(item)
            # row_index = index.row()
            param_name = str(self._qt_item_model.item(row_index, 0).text())
            if self._qt_item_model.item(row_index, 1).isCheckable():
                params[param_name] = True if self._qt_item_model.item(row_index, 1).checkState() == QtCore.Qt.Checked else False
            else:
                params[param_name] = float(self._qt_item_model.item(row_index, 1).text())

        self.update_model = False
        self.setParams(params)
        self.update_model = True

    def setParamsFromModelItem(self, item):
        """
        Set up the params dictionary for the parameter in item.
        """
        params = self.getParams()
        index = self._qt_item_model.indexFromItem(item)
        row_index = index.row()
        param_name = str(self._qt_item_model.item(row_index, 0).text())
        if self._qt_item_model.item(row_index, 1).isCheckable():
            params[param_name] = True if self._qt_item_model.item(row_index, 1).checkState() == QtCore.Qt.Checked else False
        else:
            params[param_name] = float(self._qt_item_model.item(row_index, 1).text())

        self.update_model = False
        self.setParams(params)
        self.update_model = True


    @abstractmethod
    def getParams(self):
        """ Returns the parameters for this model """

    @abstractmethod
    def setParams(self):
        """ Sets the parameters for this model """

    @abstractmethod
    def validate(self):
        """ Check current parameters are valid """