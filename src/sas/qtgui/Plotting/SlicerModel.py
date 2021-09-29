from PyQt5 import QtGui
from PyQt5 import QtCore

import sas.qtgui.Utilities.GuiUtils as GuiUtils


class SlicerModel(object):
    def __init__(self):
        # Model representation of local parameters
        self._model = QtGui.QStandardItemModel()

        self.update_model = True
        self._model.itemChanged.connect(self.setParamsFromModelItem)

    def setModelFromParams(self):
        """
        Set up the Qt model for data handling between controls
        """
        parameters = self.getParams()
        self._model.removeRows(0, self._model.rowCount())
        # Crete/overwrite model items
        for parameter in list(parameters.keys()):
            item1 = QtGui.QStandardItem(parameter)
            if isinstance(parameters[parameter], bool):
                item2 = QtGui.QStandardItem(parameters[parameter])
                item2.setCheckable(True)
                item2.setCheckState(QtCore.Qt.Checked if parameters[parameter] else QtCore.Qt.Unchecked)
            else:
                item2 = QtGui.QStandardItem(GuiUtils.formatNumber(parameters[parameter]))
            self._model.appendRow([item1, item2])
        self._model.setHeaderData(0, QtCore.Qt.Horizontal, "Parameter")
        self._model.setHeaderData(1, QtCore.Qt.Horizontal, "Value")

    def setParamsFromModel(self):
        """
        Set up the params dictionary based on the current model content.
        """
        params = self.getParams()
        for row_index in range(self._model.rowCount()):
            # index = self._model.indexFromItem(item)
            # row_index = index.row()
            param_name = str(self._model.item(row_index, 0).text())
            if self._model.item(row_index, 1).isCheckable():
                params[param_name] = True if self._model.item(row_index, 1).checkState() == QtCore.Qt.Checked else False
            else:
                params[param_name] = float(self._model.item(row_index, 1).text())

        self.update_model = False
        self.setParams(params)
        self.update_model = True

    def setParamsFromModelItem(self, item):
        """
        Set up the params dictionary for the parameter in item.
        """
        params = self.getParams()
        index = self._model.indexFromItem(item)
        row_index = index.row()
        param_name = str(self._model.item(row_index, 0).text())
        if self._model.item(row_index, 1).isCheckable():
            params[param_name] = True if self._model.item(row_index, 1).checkState() == QtCore.Qt.Checked else False
        else:
            params[param_name] = float(self._model.item(row_index, 1).text())

        self.update_model = False
        self.setParams(params)
        self.update_model = True

    def model(self):
        '''getter for the model'''
        return self._model

    def getParams(self):
        ''' pure virtual '''
        raise NotImplementedError("Parameter getter must be implemented in derived class.")

    def setParams(self):
        ''' pure virtual '''
        raise NotImplementedError("Parameter setter must be implemented in derived class.")

    def validate(self):
        ''' pure virtual '''
        raise NotImplementedError("Validator must be implemented in derived class.")
