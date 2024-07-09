import logging
from numpy import inf

from PySide6 import QtWidgets, QtCore, QtGui

from sas.qtgui.Utilities.UI.ParameterEditDialogUI import Ui_ParameterEditDialog

from sasmodels.modelinfo import Parameter

logger = logging.getLogger(__name__)

class ParameterEditDialog(QtWidgets.QDialog, Ui_ParameterEditDialog):

    # Signals
    returnNewParamsSignal = QtCore.Signal(list)

    def __init__(self, parent=None):
        super(ParameterEditDialog, self).__init__(parent)

        self.parent = parent

        self.setupUi(self)

        self.addSignals()

        self.onLoad()
    
    def addSignals(self):
        if self.parent:
            self.parent.destroyed.connect(self.onClose)
        self.valuesTable.cellPressed.connect(self.onCellPressed)
        self.cmdCancel.clicked.connect(self.onClose)
        self.cmdSave.clicked.connect(self.onSave)
    
    def onLoad(self):
        self.valuesTable.resizeRowsToContents()
        self.adjustTableSize()
    
    def onCellPressed(self):
        # Clear bold formatting in the first column
        for row in range(self.valuesTable.rowCount()):
            item = self.valuesTable.item(row, 0)
            font = item.font()
            font.setBold(False)
            item.setFont(font)
        
        # Make text bolded in the clicked-on box in the first column
        selected_row = self.valuesTable.currentRow()
        item = self.valuesTable.item(selected_row, 0)
        font = item.font()
        font.setBold(True)
        item.setFont(font)
    
    def onSave(self):
        """
        Return the values in the table to the listening parent widget
        """
        self.returnNewParamsSignal.emit(self.getValues())
        self.onClose()
    
    def getValues(self):
        """
        Get the values from the table and return them as a parameter object
        """
        parameter = Parameter(name=self.txtName.text())
        minimum_value = self.valuesTable.item(self.valuesTable.findItems("Min", QtCore.Qt.MatchContains)[0].row(), 1).text()
        maximum_value = self.valuesTable.item(self.valuesTable.findItems("Max", QtCore.Qt.MatchContains)[0].row(), 1).text()

        # Format minimum and maximum values into required format for Parameter object tuple(float, float)
        limits = [minimum_value, maximum_value]
        for i in range(len(limits)):
            try:
                limits[i] = float(limits[i])
            except ValueError:
                if "inf" in limits[i]:
                    limits[i] = inf
                    if "-" in limits[i]:
                        limits[i] = -inf
                else:
                    logger.error("Invalid limit value: %s" % limits[i])
                    return None
        parameter.limits = tuple(limits)
        parameter.default = self.getValuesFromTable(self.valuesTable, "Default")
        parameter.units = self.getValuesFromTable(self.valuesTable, "Units")
        parameter.type = self.getValuesFromTable(self.valuesTable, "Type")
        parameter.description = self.valuesTable.item(self.valuesTable.findItems("Description", QtCore.Qt.MatchContains)[0].row(), 1).text()

        return [parameter]
    
    def adjustTableSize(self):
        self.valuesTable.setFixedHeight(self.valuesTable.verticalHeader().length() + self.valuesTable.horizontalHeader().height())
    
    @staticmethod
    def getValuesFromTable(table, search_string):
        """
        Get values from column 2 of table given a search string in column 1
        :param table: QTableWidget
        :param search_string: str
        """
        return table.item(table.findItems(search_string, QtCore.Qt.MatchContains)[0].row(), 1).text()
    
    def onClose(self):
        self.close()
        self.deleteLater()