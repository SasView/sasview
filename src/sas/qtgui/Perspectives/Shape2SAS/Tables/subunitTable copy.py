from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import (QStandardItemModel, QStandardItem, 
                           QDoubleValidator, QBrush, QColor, QValidator)
from PySide6.QtWidgets import (QStyledItemDelegate, QLineEdit, QComboBox, 
                               QWidget, QSizePolicy)

from sas.qtgui.Perspectives.Shape2SAS.UI.SubunitTableControllerUI import Ui_SubunitTableController

#Row option layout
OPTIONLAYOUT = {"Subunit": 0,
                "SLD": 1, #Scattering length density
                "x": 2, 
                "y": 3, 
                "z": 4,
                "COM_x": 5, #Center of Mass
                "COM_y": 6, 
                "COM_z": 7, 
                "RP_x": 8, #Rotation Point
                "RP_y": 9, 
                "RP_z": 10, 
                "α": 11, #Alpha, Beta, Gamma
                "β": 12, 
                "γ": 13,
                "Colour": 14}


class DoubleValidator(QDoubleValidator):
    """Custom QDoubleValidator that ensures no comma values can be written."""

    def __init__(self, bottom: float, top: float, decimals: int, parent=None):
        super(DoubleValidator, self).__init__(bottom, top, decimals, parent)
        locale = QLocale(QLocale.English) #set local to English
        self.setLocale(locale)

    def validate(self, input: str, pos: int) -> tuple:
        """Return invalid for commas to prevent decimal separator issues."""

        if ',' in input:
            return QValidator.Invalid, input, pos

        return super(DoubleValidator, self).validate(input, pos)


class ModelTableViewDelegate(QStyledItemDelegate):
    """Delegate for appearance and 
    behaviour control of the model table view"""

    def __init__(self, parent=None):
        super(ModelTableViewDelegate, self).__init__()
    
    def createEditor(self, widget, option, index: int):
        """Create editor for the model table view"""

        if index.row() == OPTIONLAYOUT["Subunit"]: #subunit case
            return None
        
        elif index.row() == OPTIONLAYOUT["Colour"]:
            editor = QComboBox(widget)
            editor.addItems(["Green", "Red", "Blue"])
            return editor

        else:
            editor = QLineEdit(widget)
            validator = DoubleValidator(0.0, 10000.0, 99, editor)
            editor.setValidator(validator)
            return editor


    #NOTE: default paint method used


class ModelTableModel(QStandardItemModel):
    """Subclass from QStandardItemModel to allow displaying parameters in
    QTableView model."""

    def __init__(self, parent=None):
        super(ModelTableModel, self).__init__(parent)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Displays model parameters in the header of the model table
        """
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            return list(OPTIONLAYOUT.keys())[section]
        
        return super(ModelTableModel, self).headerData(section, orientation, role)


class SubunitTable(QWidget, Ui_SubunitTableController):
    """Subunit table functionality and design for the model tab"""

    def __init__(self):
        super(SubunitTable, self).__init__()
        self.setupUi(self)

        self.initializeModel()
        self.initializeSignals()
        self.getRestrictedSubunitRows()
        self.setSubunitOptions()
        self.getUnrestrictedSubunitRows()
        self.setButtonSpinboxBounds()
    

    def setTableProperties(self):
        """Setting table properties"""
        
        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.table.resizeColumnsToContents()


    def setSubunitOptions(self):
        """Set the subunit options in the combobox"""
        self.subunit.addItems(self.restricted.keys())


    def initializeModel(self):
        """Setup the model for the subunit table"""
        self.model = ModelTableModel() #model to the table

        self.table.setModel(self.model)
        self.table.setItemDelegate(ModelTableViewDelegate()) #delegate to the table
        self.setTableProperties() #general layout parameters
        self.table.show()


    def initializeSignals(self):
        """Setup signals for the subunit table"""
        #self.model.dataChanged.connect(self.onModelTableChange)
        self.add.clicked.connect(self.onAdding)
        self.delete.clicked.connect(self.onDeleting)


    def onAdding(self):
        """Add a subunit to the model table"""

        numcolumn = self.model.columnCount()

        #adding new column for new subunit
        items = [QStandardItem() for _ in range(len(OPTIONLAYOUT))]
        self.model.insertColumn(numcolumn, items)
        self.model.setData(self.model.index(0, numcolumn), self.subunit.currentText())

        subunit_dims = self.restricted[self.subunit.currentText()]
        self.setSubunitRestriction(subunit_dims)
        self.setButtonSpinboxBounds()


    def onDeleting(self):
        """Delete the selected subunit from the model table"""

        selected_val = self.selected.value()
        self.model.removeColumn(selected_val - 1)
        self.setButtonSpinboxBounds()


    def setButtonSpinboxBounds(self):
        """Set new bounds for the spinbox
        when a new column is added or deleted"""

        numcolumn = self.model.columnCount()

        if numcolumn == 0:
            self.delete.setEnabled(False)
            self.selected.setEnabled(False)

        else:
            self.delete.setEnabled(True)
            self.selected.setEnabled(True)
            self.selected.setMaximum(numcolumn)


    def getUnrestrictedSubunitRows(self):
        """Unrestricted dimension rows for a subunit"""

        self.unrestricted = {
            "Sphere": [OPTIONLAYOUT["x"]],
            "Ellipsoid": [OPTIONLAYOUT["x"], OPTIONLAYOUT["y"], OPTIONLAYOUT["z"]],
            "Cylinder": [OPTIONLAYOUT["x"], OPTIONLAYOUT["y"]],
            "Elliptical cylinder": [OPTIONLAYOUT["x"], OPTIONLAYOUT["y"], OPTIONLAYOUT["z"]],
            "Disc": [OPTIONLAYOUT["x"]],
            "Cube": [OPTIONLAYOUT["x"]],
            "Cuboid": [OPTIONLAYOUT["x"], OPTIONLAYOUT["y"], OPTIONLAYOUT["z"]],
            "Hollow sphere": [OPTIONLAYOUT["x"], OPTIONLAYOUT["y"]],
            "Hollow cube": [OPTIONLAYOUT["x"], OPTIONLAYOUT["y"]]}


    def getRestrictedSubunitRows(self):
        """Restricted dimension rows for a subunit"""

        self.restricted = {
            "Sphere": [OPTIONLAYOUT["y"], OPTIONLAYOUT["z"]],
            "Ellipsoid": [],
            "Cylinder": [OPTIONLAYOUT["z"]],
            "Elliptical cylinder": [],
            "Disc": [OPTIONLAYOUT["z"]],
            "Cube": [OPTIONLAYOUT["y"], OPTIONLAYOUT["z"]],
            "Cuboid": [],
            "Hollow sphere": [OPTIONLAYOUT["z"]],
            "Hollow cube": [OPTIONLAYOUT["z"]]
            }
        
    
    def setSubunitRestriction(self, dimensions):
        """Set dimension row restrictions for a subunit"""
        numcolumn = self.model.columnCount()

        for dim in [OPTIONLAYOUT["x"], OPTIONLAYOUT["y"], OPTIONLAYOUT["z"]]:
            index = self.model.index(dim, numcolumn - 1)
            item = self.model.itemFromIndex(index)

            if item:
                if dim in dimensions:
                    item.setBackground(QBrush(QColor('grey')))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                else:
                    item.setBackground(QBrush())
                    item.setFlags(item.flags() | Qt.ItemIsEditable)

                item.setText("")

