import logging

from numpy import inf
from PySide6 import QtCore, QtWidgets

from sasmodels.modelinfo import Parameter

from sas.qtgui.Utilities.ModelEditors.Dialogs.UI.ParameterEditDialogUI import Ui_ParameterEditDialog

logger = logging.getLogger(__name__)


class ParameterEditDialog(QtWidgets.QDialog, Ui_ParameterEditDialog):

    # Signals
    returnNewParamsSignal = QtCore.Signal(list)
    returnEditedParamSignal = QtCore.Signal(list, QtWidgets.QTreeWidgetItem)

    def __init__(self, parent=None, properties=None, qtree_item=None):
        super(ParameterEditDialog, self).__init__(parent)

        self.parent = parent
        self.properties = properties
        self.qtree_item = qtree_item

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

        # Detect if properties are passed in (if we are in edit-mode)
        if self.properties:
            self.setWindowTitle("Edit Parameter: %s" % self.properties['name'])

            # Load properties into table
            for property in self.properties:
                if property not in ("name", "highlighted_property", "id"):
                    self.writeValuesToTable(self.valuesTable, property, str(self.properties[property]))
                elif property == "name":
                    self.txtName.setText(self.properties[property])
                elif property == "id":
                    self.id = self.properties[property]

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
        self.cmdSave.setFocus() # Ensure that all table values are written to table's data() before saving

        if self.properties:
            self.returnEditedParamSignal.emit(self.getValues(), self.qtree_item)
        else:
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
            limit_str = limits[i]
            if "inf" in limit_str and "-" in limit_str:
                limits[i] = -inf
            elif limits[i] == inf:
                limits[i] = inf
            try:
                limits[i] = float(limits[i])
            except ValueError:
                logger.error("Invalid limit value: %s" % limits[i])
                return None
        parameter.limits = tuple(limits)
        parameter.default = self.getValuesFromTable(self.valuesTable, "Default")
        parameter.units = self.getValuesFromTable(self.valuesTable, "Units")
        parameter.type = self.getValuesFromTable(self.valuesTable, "Type")
        parameter.description = self.getValuesFromTable(self.valuesTable, "Description")

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
        property_row = table.findItems(search_string, QtCore.Qt.MatchContains)[0].row()
        try:
            return table.item(property_row, 1).text()
        except AttributeError:
            return ""

    @staticmethod
    def writeValuesToTable(table, search_string, value):
        """
        Write values to column 2 of table given a search string in column 1
        :param table: QTableWidget
        :param search_string: str
        """
        property_row = table.findItems(search_string, QtCore.Qt.MatchContains)[0].row()
        try:
            return table.item(property_row, 1).setText(value)
        except AttributeError:
            # Generate and place a blank QTableWidgetItem so we can set its text
            new_item = QtWidgets.QTableWidgetItem()
            table.setItem(property_row, 1, new_item)
            return table.item(property_row, 1).setText(value)

    def onClose(self):
        self.close()
        self.deleteLater()
