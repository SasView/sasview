from PySide6.QtWidgets import (QTableView, QStyledItemDelegate, QCheckBox, QSizePolicy, QLineEdit)
from PySide6.QtGui import (QStandardItemModel, QStandardItem)
from PySide6.QtCore import Qt

#column layout
VIEWERLAYOUT = {
    "Subunit": 0,
    "Highlight": 1
}

class ViewTableViewDelegate(QStyledItemDelegate):
    """Delegate for appearance and 
    behaviour control of the model table view"""

    def __init__(self, parent=None):
        super(ViewTableViewDelegate, self).__init__()
    
    def createEditor(self, widget, option, index: int):
        """Create editor for the model table view"""

        if index.column() == VIEWERLAYOUT["Subunit"]: #subunit case
            return None

        else:
            editor = QLineEdit(widget)
            validator = QCheckBox(widget)
            editor.setValidator(validator)
            return editor


class ModelTableModel(QStandardItemModel):
    """Subclass from QStandardItemModel to allow displaying parameters in
    QTableView model."""

    def __init__(self, parent=None):
        super(ModelTableModel, self).__init__(parent)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Displays model parameters in the header of the model table
        """
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return ['Subunit', 'Highlight'][section]
        
        return super(ModelTableModel, self).headerData(section, orientation, role)


class ViewTable:
    def __init__(self):
        self.viewTable = QTableView()
        self.viewTable.setObjectName(u"table")
        self.viewTable.setContentsMargins(0, 0, 0, 0)

        self.onInitialiseModel()
        self.setViewerTableProperties()


    def setViewerTableProperties(self):
        """Setting table properties"""
        self.viewTable.setAlternatingRowColors(True)
        self.viewTable.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.viewTable.resizeColumnsToContents()
    

    def onInitialiseModel(self):
        """Setup the model for the subunit table"""
        self.viewmodel = ModelTableModel() #model to the table

        self.viewTable.setModel(self.viewmodel)
        self.viewTable.setItemDelegate(ViewTableViewDelegate()) #delegate to the table
        self.setViewerTableProperties() #general layout parameters
        self.viewTable.show()


    def setRows(self, subunits: list):

        numrows = len(VIEWERLAYOUT.values())

        items = [QStandardItem() for _ in range(numrows)]
        self.viewmodel.insertRow(len(subunits), items)
        for i in range(numrows):
            self.viewmodel.setData(self.viewmodel.index(i, 0), subunits[i]) 
    



    
