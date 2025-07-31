# Global
from enum import Enum
from types import MethodType

from numpy import inf
from PySide6.QtCore import QLocale, Qt
from PySide6.QtGui import QBrush, QColor, QDoubleValidator, QStandardItem, QStandardItemModel, QValidator
from PySide6.QtWidgets import QComboBox, QLineEdit, QSizePolicy, QStyledItemDelegate, QWidget

#Local Perspectives
from sas.qtgui.Calculators.Shape2SAS.Tables.UI.subunitTableUI import Ui_SubunitTableController


#Row option layout
class ExtendedEnum(Enum):
    """Extended Enum class to return all values"""

    #return all values in a list
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class OptionLayout(ExtendedEnum):
    """Row layout for the subunit table"""
    Subunit = "Subunit"
    ΔSLD = "SLD"
    x = "X"
    y = "Y"
    z = "Z"
    COM_x = "COMX"
    COM_y = "COMY"
    COM_z = "COMZ"
    RP_x = "RPX"
    RP_y = "RPY"
    RP_z = "RPZ"
    α = "alpha"
    β = "beta"
    γ = "gamma"
    Colour = "colour"

    @staticmethod
    def get_position(enum):
        """Get the position of a enum (row)"""

        enum_list = list(OptionLayout)
        return enum_list.index(enum)

    #Subunit methods
    def sphere(self):
        """sphere dimension layout"""
        name = {self.x: "R"}
        units = {self.x: "Å"}
        types = {self.x: "volume"}
        bounds = {self.x: [0, inf]}
        tooltip = {self.x: "Radius of the sphere"}
        defaultVal = {self.x: 50.0}

        return name, defaultVal, units, tooltip, types, bounds


    def ellipsoid(self):
        """ellipsoid dimension layout"""

        name = {self.x: "a", self.y: "b", self.z: "c"}
        units = {self.x: "Å", self.y: "Å", self.z: "Å"}
        types = {self.x: "volume", self.y: "volume", self.z: "volume"}
        bounds = {self.x: [0, inf], self.y: [0, inf], self.z: [0, inf]}
        tooltip = {self.x: "Semi-axis a of the ellipsoid along the x-axis",
                   self.y: "Semi-axis b of the ellipsoid along the y-axis",
                   self.z: "Semi-axis c of the ellipsoid along the z-axis"}
        defaultVal = {self.x: 50.0, self.y: 50.0, self.z: 200.0}

        return name, defaultVal, units, tooltip, types, bounds


    def cylinder(self):
        """Return the cylinder dimensions"""
        name = {self.x: "R", self.y: "l"}
        units = {self.x: "Å", self.y: "Å"}
        types = {self.x: "volume", self.y: "volume"}
        bounds = {self.x: [0, inf], self.y: [0, inf]}
        tooltip = {self.x: "Radius of the cylinder",
                   self.y: "Length of the cylinder"}
        defaultVal = {self.x: 50.0, self.y: 50.0}

        return name, defaultVal, units, tooltip, types, bounds


    def elliptical_cylinder(self):
        """Return the elliptical cylinder dimensions"""
        name = {self.x: "a", self.y: "b", self.z: "l"}
        units = {self.x: "Å", self.y: "Å", self.z: "Å"}
        types = {self.x: "volume", self.y: "volume", self.z: "volume"}
        bounds = {self.x: [0, inf], self.y: [0, inf], self.z: [0, inf]}
        tooltip = {self.x: "Semi-axis a of the elliptical cylinder along the x-axis",
                   self.y: "Semi-axis b of the elliptical cylinder along the y-axis",
                   self.z: "Length l of the elliptical cylinder along the z-axis"}
        defaultVal = {self.x: 50.0, self.y: 50.0, self.z: 200.0}

        return name, defaultVal, units, tooltip, types, bounds


    def disc(self):
        """Return the disc dimensions"""
        name = {self.x: "R", self.y: "r", self.z: "l"}
        units = {self.x: "Å", self.y: "Å", self.z: "Å"}
        types = {self.x: "volume", self.y: "volume", self.z: "volume"}
        bounds = {self.x: [0, inf], self.y: [0, inf], self.z: [0, inf]}
        tooltip = {self.x: "Semi-axis a of the the disc",
                   self.y: "Semi-axis b of the disc along the y-axis",
                    self.z: "Length l of the disc along the z-axis"}
        defaultVal = {self.x: 50.0, self.y: 50.0, self.z: 25.0}

        return name, defaultVal, units, tooltip, types, bounds


    def cube(self):
        """Return the cube dimensions"""
        name = {self.x: "a"}
        units = {self.x: "Å"}
        types = {self.x: "volume"}
        bounds = {self.x: [0, inf]}
        tooltip = {self.x: "Side length of the cube"}
        defaultVal = {self.x: 50.0}

        return name, defaultVal, units, tooltip, types, bounds


    def cuboid(self):
        """Return the cuboid dimensions"""
        name = {self.x: "a", self.y: "b", self.z: "c"}
        units = {self.x: "Å", self.y: "Å", self.z: "Å"}
        types = {self.x: "volume", self.y: "volume", self.z: "volume"}
        bounds = {self.x: [0, inf], self.y: [0, inf], self.z: [0, inf]}
        tooltip = {self.x: "Side length a of the cuboid along the x-axis",
                   self.y: "Side length b of the cuboid along the y-axis",
                   self.z: "Side length c of the cuboid along the z-axis"}
        defaultVal = {self.x: 50.0, self.y: 50.0, self.z: 200.0}

        return name, defaultVal, units, tooltip, types, bounds

    def hollow_sphere(self):
        """Return the hollow sphere dimensions"""
        name = {self.x: "R", self.y: "r"}
        units = {self.x: "Å", self.y: "Å"}
        types = {self.x: "volume", self.y: "volume"}
        bounds = {self.x: [0, inf], self.y: [0, inf]}
        tooltip = {self.x: "Outer radius of the hollow sphere",
                   self.y: "Inner radius of the hollow sphere"}
        defaultVal = {self.x: 50.0, self.y: 25.0}

        return name, defaultVal, units, tooltip, types, bounds


    def hollow_cube(self):
        """Return the hollow cube dimensions"""

        name = {self.x: "R", self.y: "r"}
        units = {self.x: "Å", self.y: "Å"}
        types = {self.x: "volume", self.y: "volume"}
        bounds = {self.x: [0, inf], self.y: [0, inf]}
        tooltip = {self.x: "Outer side length of the hollow cube",
                   self.y: "Inner side length of the hollow cube"}
        defaultVal = {self.x: 50.0, self.y: 25.0}

        return name, defaultVal, units, tooltip, types, bounds

    def cyl_ring(self):
        """Return the cylinder ring dimensions"""

        name = {self.x: "R", self.y: "r", self.z: "l"}
        units = {self.x: "Å", self.y: "Å", self.z: "Å"}
        types = {self.x: "volume", self.y: "volume", self.z: "volume"}
        bounds = {self.x: [0, inf], self.y: [0, inf], self.z: [0, inf]}
        tooltip = {self.x: "Outer radius of the cylinder ring",
                   self.y: "Inner radius of the cylinder ring",
                   self.z: "Length of the cylinder ring"}
        defaultVal = {self.x: 50.0, self.y: 40.0, self.z: 10.0}

        return name, defaultVal, units, tooltip, types, bounds

    #Add new subunit methods here

    #Other methods for the table
    def SLD(self):
        """Return ΔSLD dimensions"""
        name = {self.ΔSLD: "ΔSLD"}
        units = {self.ΔSLD: ""}
        types = {self.ΔSLD: "sld"}
        bounds = {self.ΔSLD: [-inf, inf]}
        tooltip = {self.ΔSLD: "Contrast"}
        defaultVal = {self.ΔSLD: 1.0}

        return name, defaultVal, units, tooltip, types, bounds


    def COMX(self):
        """Return COMX dimensions"""
        name = {self.COM_x: "COMX"}
        units = {self.COM_x: "Å"}
        types = {self.COM_x: "volume"}
        bounds = {self.COM_x: [-inf, inf]}
        tooltip = {self.COM_x: "x-axis position of center of mass"}
        defaultVal = {self.COM_x: 0.0}

        return name, defaultVal, units, tooltip, types, bounds


    def COMY(self):
        """Return COMY dimensions"""
        name = {self.COM_y: "COMY"}
        units = {self.COM_y: "Å"}
        types = {self.COM_y: "volume"}
        bounds = {self.COM_y: [-inf, inf]}
        tooltip = {self.COM_y: "y-axis position of center of mass"}
        defaultVal= {self.COM_y: 0.0}

        return name, defaultVal, units, tooltip, types, bounds


    def COMZ(self):
        """Return COMZ dimensions"""
        name = {self.COM_z: "COMZ"}
        units = {self.COM_z: "Å"}
        types = {self.COM_z: "volume"}
        bounds = {self.COM_z: [-inf, inf]}
        tooltip = {self.COM_z: "z-axis position of center of mass"}
        defaultVal = {self.COM_z: 0.0}

        return name, defaultVal, units, tooltip, types, bounds


    def RPX(self):
        """Return RPX dimensions"""
        name = {self.RP_x: "RPX"}
        units = {self.RP_x: "Å"}
        types = {self.RP_x: "volume"}
        bounds = {self.RP_x: [-inf, inf]}
        tooltip = {self.RP_x: "x-axis position of rotation point"}
        defaultVal = {self.RP_x: 0.0}

        return name, defaultVal, units, tooltip, types, bounds


    def RPY(self):
        """Return RPY dimensions"""
        name = {self.RP_y: "RPY"}
        units = {self.RP_y: "Å"}
        types = {self.RP_y: "volume"}
        bounds = {self.RP_y: [-inf, inf]}
        tooltip = {self.RP_y: "y-axis position of rotation point"}
        defaultVal = {self.RP_y: 0.0}

        return name, defaultVal, units, tooltip, types, bounds


    def RPZ(self):
        """Return RPZ dimensions"""
        name = {self.RP_z: "RPZ"}
        units = {self.RP_z: "Å"}
        types = {self.RP_z: "volume"}
        bounds = {self.RP_z: [-inf, inf]}
        tooltip = {self.RP_z: "z-axis position of rotation point"}
        defaultVal = {self.RP_z: 0.0}

        return name, defaultVal, units, tooltip, types, bounds


    def alpha(self):
        """Return α dimensions"""
        name = {self.α: "α"}
        units = {self.α: "°"}
        types = {self.α: ""}
        bounds = {self.α: [-inf, inf]}
        tooltip = {self.α: "Angle around x-axis"}
        defaultVal = {self.α: 0.0}

        return name, defaultVal, units, tooltip, types, bounds

    def beta(self):
        """Return β dimensions"""
        name = {self.β: "β"}
        units = {self.β: "°"}
        types = {self.β: ""}
        bounds = {self.β: [-inf, inf]}
        tooltip = {self.β: "Angle around y-axis"}
        defaultVal = {self.β: 0.0}

        return name, defaultVal, units, tooltip, types, bounds

    def gamma(self):
        """Return γ dimensions"""
        name = {self.γ: "γ"}
        units = {self.γ: "°"}
        types = {self.γ: ""}
        bounds = {self.γ: [-inf, inf]}
        tooltip = {self.γ: "Angle around z-axis"}
        defaultVal = {self.γ: 0.0}

        return name, defaultVal, units, tooltip, types, bounds

    def colour(self):
        """Return Colour dimensions"""
        name = {self.Colour: ""}
        units = {self.Colour: ""}
        types = {self.Colour: ""}
        bounds = {self.Colour: ""}
        tooltip = {self.Colour: "Colour to represent the subunit"}
        defaultVal = {self.Colour: "Green"}

        return name, defaultVal, units, tooltip, types, bounds


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
    """Custom QStandardItem to set initial values, roles
    and take care of subunit and colour case"""

    def __init__(self, prefix="", unit="", tooltip="", default_value=None):
        super().__init__(str(default_value))
        self.prefix = prefix
        self.tooltip = tooltip
        self.unit = unit

        self.setData(default_value, Qt.EditRole)


    def data(self, role=Qt.DisplayRole):
        """Check the role of the data"""

        value = super().data(role)
        if role == Qt.DisplayRole:
            return f"{self.prefix}{value}{self.unit}"
        elif role == Qt.ToolTipRole:
            return self.tooltip

        return value


    def setData(self, value, role=Qt.EditRole):
        """Set data for the model"""

        if role == Qt.EditRole:
            # to solve for subunit and colour case
            try:
                self.raw_value = float(value)
            except ValueError:
                self.raw_value = value
            super().setData(value, Qt.DisplayRole)
        else:
            super().setData(value, role)


class CustomDelegate(QStyledItemDelegate):
    """Delegate for appearance and
    behaviour control of the model table view"""


    def createEditor(self, widget, option, index):
        """Create editor for the model table view"""

        if index.row() == OptionLayout.get_position(OptionLayout.Subunit): #subunit case
            editor = None
        elif index.row() == OptionLayout.get_position(OptionLayout.Colour): #colour case
            editor = QComboBox(widget)
            editor.addItems(["Green", "Red", "Blue"])
        else:
            editor = QLineEdit(widget)
            validator = DoubleValidator(-10000.0, 10000.0, 99, editor)
            editor.setValidator(validator)

        return editor

    def setEditorData(self, editor, index):
        """Set the editor data from the model"""

        if isinstance(editor, QComboBox):
            value = index.model().data(index, Qt.EditRole)
            editor.setCurrentText(value)
        else:
            #QLineEdit case
            super().setEditorData(editor, index)


    def setModelData(self, editor, model, index):
        """Set model data for the editor"""

        if isinstance(editor, QComboBox):
            model.setData(index, editor.currentText(), Qt.EditRole)
        elif isinstance(editor, QLineEdit):
            text = editor.text()
            float_value = float(text) #save as float
            model.setData(index, float_value, Qt.EditRole)
        else:
            super().setModelData(editor, model, index)


class ModelTableModel(QStandardItemModel):
    """Subclass from QStandardItemModel to allow displaying parameters in
    QTableView model."""

    def __init__(self, parent=None):
        super(ModelTableModel, self).__init__(parent)

    #NOTE: The header may be added later but right now the names are a bit misleading...
    #def headerData(self, section, orientation, role=Qt.DisplayRole):
    #    """
    #    Displays model parameters in the header of the model table
    #    """
    #    if orientation == Qt.Vertical and role == Qt.DisplayRole:
    #        return list(OptionLayout.__members__.keys())[section]
    #
    #    return super(ModelTableModel, self).headerData(section, orientation, role)


class SubunitTable(QWidget, Ui_SubunitTableController):
    """Subunit table functionality and design for the model tab"""

    def __init__(self):
        super(SubunitTable, self).__init__()
        self.setupUi(self)

        self.columnEyeKeeper = []
        self.restrictedRowsPos = []

        self.initializeModel()
        self.initializeSignals()
        self.setSubunitOptions()
        self.setButtonSpinboxBounds()
        self.onClearSubunitTable()

    def setTableProperties(self):
        """Setting table properties"""

        self.table.setAlternatingRowColors(True)
        self.table.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Expanding)
        self.table.resizeColumnsToContents()

    def setSubunitOptions(self):
        """Set the subunit options in the combobox"""
        self.subunit.addItems(["sphere", "cylinder", "ellipsoid", "elliptical_cylinder", "disc",
                                "cube", "cuboid", "hollow_sphere", "hollow_cube", "cyl_ring"]) #TODO: automate this
        self.subunit.setContentsMargins(5, 5, 5, 5)

    def initializeModel(self):
        """Setup the model for the subunit table"""
        self.model = ModelTableModel() #model to the table

        self.table.setModel(self.model)
        self.table.setItemDelegate(CustomDelegate()) #delegate to the table
        self.setTableProperties() #general layout parameters
        self.table.show()

    def initializeSignals(self):
        """Setup signals for the subunit table"""
        self.add.clicked.connect(self.onAdding)
        self.deleteButton.clicked.connect(self.onDeleting)

    @staticmethod
    def smallestInteger(numcolumn, columnEyeKeeper: list) -> int:
        """Find the smallest integer not in columnEyeKeeper list"""

        if not columnEyeKeeper:
            columnEyeKeeper.append(1)
            return 1

        for i in range(1, numcolumn + 2):
            if i not in columnEyeKeeper:
                columnName = i
                columnEyeKeeper.append(columnName)
                return columnName

        return numcolumn + 1

    def onAdding(self):
        """Add a subunit to the model table"""

        numcolumn = self.model.columnCount()
        subunit = self.subunit.currentText()

        items = []

        #get subunit method for dimensions, name, default_value, units and tooltip
        subunitAttr = getattr(OptionLayout, subunit)
        subunitMethod = MethodType(subunitAttr, OptionLayout)
        subunitName, subunitDefault_value, subunitUnits, subunitTooltip, _, _ = subunitMethod()

        to_column_name = self.smallestInteger(numcolumn, self.columnEyeKeeper)
        for row in list(OptionLayout):
            if row in [OptionLayout.x, OptionLayout.y, OptionLayout.z]:
                #if row is contained in the subunit
                if row in subunitName.keys():
                    paintedName = subunitName[row] + f"{to_column_name}" + " = "
                    item = CustomStandardItem(paintedName, subunitUnits[row],
                                            subunitTooltip[row], subunitDefault_value[row])
                else:
                    #no input for this row
                    item = CustomStandardItem("", "", "", "")

            elif row == OptionLayout.Subunit:
                #paint name for colour set in delegate due to multiple names
                item = CustomStandardItem("", "", "Subunit", "")

            elif row == OptionLayout.Colour:
                attr = getattr(OptionLayout, row.value)
                method = MethodType(attr, OptionLayout)
                name, defaultVal, units, tooltip, _, _ = method()
                #paint name for colour set in delegate due to multiple names
                item = CustomStandardItem(name[row], units[row], tooltip[row], defaultVal[row])

            else:
                attr = getattr(OptionLayout, row.value)
                method = MethodType(attr, OptionLayout)
                name, defaultVal, units, tooltip, _, _ = method()
                item = CustomStandardItem(name[row] + f"{to_column_name}" + " = ", units[row],
                                          tooltip[row], defaultVal[row])

            items.append(item)

        self.model.insertColumn(numcolumn, items)
        self.model.setData(self.model.index(0, numcolumn), self.subunit.currentText())
        self.setSubunitRestriction(subunitName.keys())
        self.table.resizeColumnsToContents()
        self.setButtonSpinboxBounds()


    def onDeleting(self):
        """Delete the selected subunit from the model table"""

        self.selected_val = self.selected.value()
        self.model.removeColumn(self.selected_val - 1)
        self.setButtonSpinboxBounds()

        self.columnEyeKeeper.pop(self.selected_val - 1)
        del self.restrictedRowsPos[self.selected_val - 1]

        #clear the table if no columns are left
        if not self.model.columnCount():
            self.onClearSubunitTable()


    def setButtonSpinboxBounds(self):
        """Set new bounds for the spinbox
        when a new column is added or deleted"""

        numcolumn = self.model.columnCount()

        self.deleteButton.setEnabled(numcolumn > 0)
        self.selected.setEnabled(numcolumn > 0)
        self.selected.setMinimum(1)
        self.selected.setMaximum(numcolumn)


    def setSubunitRestriction(self, dimensions):
        """Set input restriction for a row"""
        numcolumn = self.model.columnCount()

        restrictedRowPos = []
        for dim in [OptionLayout.x, OptionLayout.y, OptionLayout.z]:
            row = OptionLayout.get_position(dim)
            column = numcolumn - 1
            index = self.model.index(row, column)
            item = self.model.itemFromIndex(index)

            if not item:
                continue

            if dim not in dimensions:
                #no input allowed
                item.setText("")
                item.setBackground(QBrush(QColor('grey')))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                restrictedRowPos.append(row)
            else:
                item.setBackground(QBrush())
                item.setFlags(item.flags() | Qt.ItemIsEditable)

        self.restrictedRowsPos.append(restrictedRowPos)


    def onClearSubunitTable(self):
        """Clear the subunit table"""

        self.model.clear()
        self.columnEyeKeeper = []
        self.restrictedRowsPos = []
        self.selected.setValue(1)
        self.setButtonSpinboxBounds()

