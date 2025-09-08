# Global

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import QCheckBox, QStyledItemDelegate, QWidget

# Local Perspectives
from sas.qtgui.Calculators.Shape2SAS.Tables.UI.variableTableUI import Ui_VariableTable


class CustomDelegate(QStyledItemDelegate):
    """Custom delegate to set check box in the table"""

    def createEditor(self, widget, option, index):
        """Create editor for the model table view"""

        if index.column() == 0: #subunit case
            return None

        else:
            editor = QCheckBox(widget)
            return editor

    def setEditorData(self, editor, index):
        """Set the checkbox state based on the model data"""
        value = index.model().data(index, Qt.CheckStateRole)
        editor.setChecked(value == Qt.Checked)

    def setModelData(self, editor, model, index):
        """Update the model data based on the checkbox state"""
        value = Qt.Checked if editor.isChecked() else Qt.Unchecked
        model.setData(index, value, Qt.CheckStateRole)



class ModelVariableTableModel(QStandardItemModel):
    """Subclass from QStandardItemModel to allow displaying parameters in
    QTableView model."""

    def __init__(self, parent=None):
        super(ModelVariableTableModel, self).__init__(parent)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Displays model parameters in the header of the model table
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return list(['Parameters', 'Add to Fit'])[section]

        return super(ModelVariableTableModel, self).headerData(section, orientation, role)


class VariableTable(QWidget, Ui_VariableTable):

    def __init__(self):
        super(VariableTable, self).__init__()
        self.setupUi(self)

        self.initializeVariableModel()
        self.setDefaultLayout()


    def initializeVariableModel(self):
        """Setup the model for the subunit table"""
        self.variableModel = ModelVariableTableModel() #model to the table

        self.tableView.setModel(self.variableModel)
        self.tableView.setItemDelegate(CustomDelegate()) #delegate to the table
        self.setDefaultLayout()
        self.tableView.show()


    def setDefaultLayout(self):
        """Set default values"""
        self.tableView.setAlternatingRowColors(True)


    def setVariableTableData(self, names: list[str], column: int):
        """Set names and checkboxes to table"""

        numrow = self.variableModel.rowCount()

        for name in range(len(names) - 1, 0, -1):
            itemName = QStandardItem(names[name])
            itemCheck = QStandardItem()
            itemCheck.setData(Qt.Unchecked, Qt.CheckStateRole)
            itemCheck.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            itemCheck.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.variableModel.insertRow(numrow, [itemName, itemCheck])

        font = QFont()
        font.setBold(True)

        itemName = QStandardItem(names[0])
        itemName.setTextAlignment(Qt.AlignCenter)
        itemName.setFont(font)

        itemNum = QStandardItem(f"{column + 1}")
        itemNum.setTextAlignment(Qt.AlignCenter)
        itemNum.setFont(font)
        self.variableModel.insertRow(numrow, [itemName, itemNum])
        itemNum.setFlags(itemNum.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEditable)


    def removeTableData(self, row):
        """Remove data from table"""
        self.variableModel.removeRow(row)


    def resetTable(self):
        """Reset table"""
        self.variableModel.clear()


    def getAllTableNamesVariables(self):
        """Get all names from the variable table"""
        names = []

        for row in range(self.variableModel.rowCount()):
            names.append(self.variableModel.item(row, 0).text())

        return names

    def getCheckedTableNamesVariables(self):
        """Get checked names from the variable table"""
        names = []

        for row in range(self.variableModel.rowCount()):
            itemCheck = self.variableModel.item(row, 1)
            checkState = itemCheck.data(Qt.CheckStateRole)
            is_checked = checkState == Qt.Checked.value

            if is_checked:
                names.append(self.variableModel.item(row, 0).text())

        return names

    def getAllTableColumnsPos(self):
        """Get all columns from the variable table"""
        rows = []

        for row in range(self.variableModel.rowCount()):
            column = self.variableModel.item(row, 1).text()
            if column:
                rows.append(row)

        return rows


    def getCheckedVariables(self) -> list[list[bool]]:
        """Get checked names and associated columns from variable table"""
        columns = []
        rows = []

        column_pos = self.getAllTableColumnsPos()
        column_pos.append(self.variableModel.rowCount())

        i = 0
        for row in range(self.variableModel.rowCount()):
            itemCheck = self.variableModel.item(row, 1)
            checkState = itemCheck.data(Qt.CheckStateRole)
            is_checked = checkState == Qt.Checked.value

            rows.append(is_checked)
            if row == column_pos[i + 1] - 1 or row == self.variableModel.rowCount() - 1:
                columns.append(rows)
                rows = []

            #check if row is greater than lenght of the column
            if not column_pos[i + 1] > row:
                #go to the next column
                i += 1

        return columns

    def setUncheckToAllCheckBoxes(self):
        """Uncheck all checkboxes"""
        for row in range(self.variableModel.rowCount()):
            itemCheck = self.variableModel.item(row, 1)
            if itemCheck and itemCheck.isCheckable():
                itemCheck.setData(Qt.Unchecked, Qt.CheckStateRole)

    def onClearTable(self):
        """Clear the table"""
        self.resetTable()
