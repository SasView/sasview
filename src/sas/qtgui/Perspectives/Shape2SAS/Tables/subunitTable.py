from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import (QStandardItemModel, QStandardItem, 
                           QDoubleValidator, QBrush, QColor, QValidator)
from PySide6.QtWidgets import (QStyledItemDelegate, QLineEdit, QComboBox, 
                               QWidget, QSizePolicy)

from sas.qtgui.Perspectives.Shape2SAS.UI.SubunitTableControllerUI import Ui_SubunitTableController

#Row option layout
OPTIONLAYOUT = {"Subunit": 0,
                "ΔSLD": 1, #Scattering length density
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


class CustomStandardItem(QStandardItem):
    def __init__(self, prefix="", unit="", tooltip="", default_value=any):
        super().__init__(str(default_value))
        self.prefix = prefix
        self.tooltip = tooltip
        self.unit = unit
        self.setData(default_value, Qt.EditRole)

    def data(self, role=Qt.DisplayRole):
        value = super().data(role)
        if role == Qt.DisplayRole:
            return f"{self.prefix}{value}{self.unit}"
        elif role == Qt.ToolTipRole:
            return self.tooltip
        return value
    
    def setData(self, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            ##TODO: try argument is sloppy Since an if statement could be made 
            # to solve for subunit and colour case
            try:
                self.raw_value = float(value)
            except:
                self.raw_value = value
            super().setData(value, Qt.DisplayRole)
        else:
            super().setData(value, role)

class CustomDelegate(QStyledItemDelegate):
    """Delegate for appearance and 
    behaviour control of the model table view"""


    def createEditor(self, widget, option, index):
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
    
    def setEditorData(self, editor, index):
        """Set the editor data from the model"""
        if isinstance(editor, QComboBox):
            value = index.model().data(index, Qt.EditRole)
            editor.setCurrentText(value)
        else:
            super().setEditorData(editor, index)
    

    def setModelData(self, editor, model, index):
        """Set model data for the editor"""
        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.EditRole)
        elif isinstance(editor, QLineEdit):
            text = editor.text()
            float_value = float(text)
            model.setData(index, float_value, Qt.EditRole)
        else:
            super().setModelData(editor, model, index)


    #NOTE: default paint method used

    #NOTE: default set editor used


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

        self.setPainting()
        self.setToolTips()
        self.setDefaultValues()
        self.initializeModel()
        self.initializeSignals()
        self.getRestrictedSubunitRows()
        self.setSubunitOptions()
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
        self.table.setItemDelegate(CustomDelegate()) #delegate to the table
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
        subunit = self.subunit.currentText()

        items = []

        for row in OPTIONLAYOUT.values():
            if row in [OPTIONLAYOUT["x"], OPTIONLAYOUT["y"], OPTIONLAYOUT["z"]]:
                item = CustomStandardItem(self.name[row][subunit], self.units[row][subunit], 
                                          self.tooltip[row][subunit], self.defaultValue[row][subunit])
            else:
                item = CustomStandardItem(self.name[row], self.units[row], self.tooltip[row],
                                          self.defaultValue[row])

            items.append(item)

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

    
    def setToolTips(self):
        """Tooltips for each cell in subunit table"""

        self.tooltipx = {
            "Sphere": "Radius of the sphere",
            "Ellipsoid": "Semi-axis a of the ellipsoid along the x-axis",
            "Cylinder": "Radius of the cylinder",
            "Elliptical cylinder": "Semi-axis a of the elliptical cylinder along the x-axis",
            "Disc": "Semi-axis a of the the disc",
            "Cube": "Side length of the cube",
            "Cuboid": "Side length a of the cuboid along the x-axis",
            "Hollow sphere": "Outer radius of the hollow sphere",
            "Hollow cube": "Outer radius of the hollow cube"
        }

        self.tooltipy = {
            "Sphere": "",
            "Ellipsoid": "Semi-axis b of the ellipsoid along the y-axis",
            "Cylinder": "Length of the cylinder",
            "Elliptical cylinder": "Semi-axis b of the elliptical cylinder along the y-axis",
            "Disc": "Semi-axis b of the disc along the y-axis",
            "Cube": "",
            "Cuboid": "Side length b of the cuboid along the y-axis",
            "Hollow sphere": "Inner radius of the hollow sphere",
            "Hollow cube": "Inner radius of the hollow cube"
        }

        self.tooltipz = {
            "Sphere": "",
            "Ellipsoid": "Semi-axis c of the ellipsoid along the z-axis",
            "Cylinder": "",
            "Elliptical cylinder": "Length l of the elliptical cylinder along the z-axis",
            "Disc": "Length l of the disc along the z-axis",
            "Cube": "",
            "Cuboid": "Side length c of the cuboid along the z-axis",
            "Hollow sphere": "",
            "Hollow cube": ""
        }

        self.tooltip = {
            OPTIONLAYOUT["Subunit"]: "Subunit",
            OPTIONLAYOUT["ΔSLD"]: "Contrast",
            OPTIONLAYOUT["x"]: self.tooltipx,
            OPTIONLAYOUT["y"]: self.tooltipy,
            OPTIONLAYOUT["z"]: self.tooltipz,
            OPTIONLAYOUT["COM_x"]: "x-axis position of center of mass",
            OPTIONLAYOUT["COM_y"]: "y-axis position of center of mass",
            OPTIONLAYOUT["COM_z"]: "z-axis position of center of mass",
            OPTIONLAYOUT["RP_x"]: "x-axis position of rotation point",
            OPTIONLAYOUT["RP_y"]: "y-axis position of rotation point",
            OPTIONLAYOUT["RP_z"]: "z-axis position of rotation point",
            OPTIONLAYOUT["α"]: "Angle around x-axis",
            OPTIONLAYOUT["β"]: "Angle around y-axis",
            OPTIONLAYOUT["γ"]: "Angle around z-axis",
            OPTIONLAYOUT["Colour"]: "Colour to represent the subunit"

        }

    def setDefaultValues(self):
        """Set default values for the subunit table"""

        self.defaultvaluex = {
            "Sphere": 50.0,
            "Ellipsoid": 50.0,
            "Cylinder": 50.0,
            "Elliptical cylinder": 50.0,
            "Disc": 50.0,
            "Cube": 50.0,
            "Cuboid": 50.0,
            "Hollow sphere": 50.0,
            "Hollow cube": 50.0
        }

        self.defaultValuey = {
            "Sphere": "",
            "Ellipsoid": 50.0,
            "Cylinder": 50.0,
            "Elliptical cylinder": 50.0,
            "Disc": 50.0,
            "Cube": "",
            "Cuboid": 50.0,
            "Hollow sphere": 25.0,
            "Hollow cube": 25.0
        }

        self.defaultvaluez = {
            "Sphere": "",
            "Ellipsoid": 200.0,
            "Cylinder": "",
            "Elliptical cylinder": 200.0,
            "Disc": 25.0,
            "Cube": "",
            "Cuboid": 200.0,
            "Hollow sphere": "",
            "Hollow cube": ""
        }

        self.defaultValue = {OPTIONLAYOUT["Subunit"]: "",
                      OPTIONLAYOUT["ΔSLD"]: 1.0,
                        OPTIONLAYOUT["x"]: self.defaultvaluex,
                        OPTIONLAYOUT["y"]: self.defaultValuey,
                        OPTIONLAYOUT["z"]: self.defaultvaluez,
                        OPTIONLAYOUT["COM_x"]: 0.0,
                        OPTIONLAYOUT["COM_y"]: 0.0,
                        OPTIONLAYOUT["COM_z"]: 0.0,
                        OPTIONLAYOUT["RP_x"]: 0.0,
                        OPTIONLAYOUT["RP_y"]: 0.0,
                        OPTIONLAYOUT["RP_z"]: 0.0,
                        OPTIONLAYOUT["α"]: 0.0,
                        OPTIONLAYOUT["β"]: 0.0,
                        OPTIONLAYOUT["γ"]: 0.0,
                        OPTIONLAYOUT["Colour"]: "Green"
        }

    def setPainting(self):
        """painting the cells in subunit table"""

        self.name = {
        OPTIONLAYOUT["Subunit"]: "",
        OPTIONLAYOUT["ΔSLD"]: "",
        OPTIONLAYOUT["x"]:{
            "Sphere": "R = ",
            "Ellipsoid": "a = ",
            "Cylinder": "R = ",
            "Elliptical cylinder": "a = ",
            "Disc": "a = ",
            "Cube": "a = ",
            "Cuboid": "a = ",
            "Hollow sphere": "R = ",
            "Hollow cube": "R = "
        },
        OPTIONLAYOUT["y"]:{
         "Sphere": "",
         "Ellipsoid": "b = ",
         "Cylinder": "L = ",
         "Elliptical cylinder": "b = ",
         "Disc": "b = ",
         "Cube": "",
         "Cuboid": "b = ",
         "Hollow sphere": "r = ",
         "Hollow cube": "r = "
        },
        OPTIONLAYOUT["z"]: {
         "Sphere": "",
         "Ellipsoid": "c = ",
         "Cylinder": "",
         "Elliptical cylinder": "c = ",
         "Disc": "c = ",
         "Cube": "",
         "Cuboid": "c = ",
         "Hollow sphere": "",
         "Hollow cube": ""
        },
        OPTIONLAYOUT["COM_x"]: "",
        OPTIONLAYOUT["COM_y"]: "",
        OPTIONLAYOUT["COM_z"]: "",
        OPTIONLAYOUT["RP_x"]: "",
        OPTIONLAYOUT["RP_y"]: "",
        OPTIONLAYOUT["RP_z"]: "",
        OPTIONLAYOUT["α"]: "",
        OPTIONLAYOUT["β"]: "",
        OPTIONLAYOUT["γ"]: "",
        OPTIONLAYOUT["Colour"]: ""
        }

        self.unitsx = {
            "Sphere": " Å",
            "Ellipsoid": " Å",
            "Cylinder": " Å",
            "Elliptical cylinder": " Å",
            "Disc": " Å",
            "Cube": " Å",
            "Cuboid": " Å",
            "Hollow sphere": " Å",
            "Hollow cube": " Å"
        }

        self.unitsy = {
            "Sphere": "",
            "Ellipsoid": " Å",
            "Cylinder": " Å",
            "Elliptical cylinder": " Å",
            "Disc": " Å",
            "Cube": "",
            "Cuboid": " Å",
            "Hollow sphere": " Å",
            "Hollow cube": " Å"
        }

        self.unitsz = {
            "Sphere": "",
            "Ellipsoid": " Å",
            "Cylinder": "",
            "Elliptical cylinder": " Å",
            "Disc": " Å",
            "Cube": "",
            "Cuboid": " Å",
            "Hollow sphere": "",
            "Hollow cube": ""
        }
        

        self.units = {OPTIONLAYOUT["Subunit"]: "",
                      OPTIONLAYOUT["ΔSLD"]: "",
                        OPTIONLAYOUT["x"]: self.unitsx,
                        OPTIONLAYOUT["y"]: self.unitsy,
                        OPTIONLAYOUT["z"]: self.unitsz,
                        OPTIONLAYOUT["COM_x"]: " Å",
                        OPTIONLAYOUT["COM_y"]: " Å",
                        OPTIONLAYOUT["COM_z"]: " Å",
                        OPTIONLAYOUT["RP_x"]: " Å",
                        OPTIONLAYOUT["RP_y"]: " Å",
                        OPTIONLAYOUT["RP_z"]: " Å",
                        OPTIONLAYOUT["α"]: "°",
                        OPTIONLAYOUT["β"]: "°",
                        OPTIONLAYOUT["γ"]: "°",
                        OPTIONLAYOUT["Colour"]: ""
        }


    def getRestrictedSubunitRows(self):
        """Restricted dimension rows for a subunit"""

        self.restricted = {
            "Sphere": [OPTIONLAYOUT["y"], OPTIONLAYOUT["z"]],
            "Ellipsoid": [],
            "Cylinder": [OPTIONLAYOUT["z"]],
            "Elliptical cylinder": [],
            "Disc": [],
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
                    item.setText("")
                    item.setBackground(QBrush(QColor('grey')))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                
                else:
                    item.setBackground(QBrush())
                    item.setFlags(item.flags() | Qt.ItemIsEditable)


