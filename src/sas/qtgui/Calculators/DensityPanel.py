# global
import logging
import functools
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from periodictable import formula as Formula

from sas.qtgui.Utilities.GuiUtils import FormulaValidator
from sas.qtgui.UI import main_resources_rc
from sas.qtgui.Utilities.GuiUtils import HELP_DIRECTORY_LOCATION

# Local UI
from sas.qtgui.Calculators.UI.DensityPanel import Ui_DensityPanel

from sas.qtgui.Utilities.GuiUtils import enum
from sas.qtgui.Utilities.GuiUtils import formatNumber

MODEL = enum(
    'MOLECULAR_FORMULA',
    'MOLAR_MASS',
    'MOLAR_VOLUME',
    'MASS_DENSITY',
)

MODES = enum(
    'VOLUME_TO_DENSITY',
    'DENSITY_TO_VOLUME',
)

def toMolarMass(formula):
    AVOGADRO = 6.02214129e23

    try:
        f = Formula(str(formula))
        return "%g" % (f.molecular_mass * AVOGADRO)
    except:
        return ""


class DensityPanel(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(DensityPanel, self).__init__()

        self.mode = None
        self.manager = parent
        self.setupUi()
        self.setupModel()
        self.setupMapper()

    def setupUi(self):
        self.ui = Ui_DensityPanel()
        self.ui.setupUi(self)

        # no reason to have this widget resizable
        self.setFixedSize(self.minimumSizeHint())

        # set validators
        #self.ui.editMolecularFormula.setValidator(FormulaValidator(self.ui.editMolecularFormula))

        rx = QtCore.QRegExp("[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?")
        self.ui.editMolarVolume.setValidator(QtGui.QRegExpValidator(rx, self.ui.editMolarVolume))
        self.ui.editMassDensity.setValidator(QtGui.QRegExpValidator(rx, self.ui.editMassDensity))

        # signals
        self.ui.editMolarVolume.textEdited.connect(functools.partial(self.setMode, MODES.VOLUME_TO_DENSITY))
        self.ui.editMassDensity.textEdited.connect(functools.partial(self.setMode, MODES.DENSITY_TO_VOLUME))

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.modelReset)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Help).clicked.connect(self.displayHelp)

    def setupModel(self):
        self.model = QtGui.QStandardItemModel(self)
        self.model.setItem(MODEL.MOLECULAR_FORMULA, QtGui.QStandardItem())
        self.model.setItem(MODEL.MOLAR_MASS       , QtGui.QStandardItem())
        self.model.setItem(MODEL.MOLAR_VOLUME     , QtGui.QStandardItem())
        self.model.setItem(MODEL.MASS_DENSITY     , QtGui.QStandardItem())

        self.model.dataChanged.connect(self.dataChanged)

        self.modelReset()

    def setupMapper(self):
        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setOrientation(QtCore.Qt.Vertical)

        self.mapper.addMapping(self.ui.editMolecularFormula, MODEL.MOLECULAR_FORMULA)
        self.mapper.addMapping(self.ui.editMolarMass       , MODEL.MOLAR_MASS)
        self.mapper.addMapping(self.ui.editMolarVolume     , MODEL.MOLAR_VOLUME)
        self.mapper.addMapping(self.ui.editMassDensity     , MODEL.MASS_DENSITY)

        self.mapper.toFirst()

    def dataChanged(self, top, bottom):
        for index in range(top.row(), bottom.row() + 1):
            if index == MODEL.MOLECULAR_FORMULA:
                molarMass = toMolarMass(self.model.item(MODEL.MOLECULAR_FORMULA).text())
                molarMass = formatNumber(molarMass, high=True)
                self.model.item(MODEL.MOLAR_MASS).setText(molarMass)

                if self.mode == MODES.VOLUME_TO_DENSITY:
                    self._updateDensity()
                elif self.mode == MODES.DENSITY_TO_VOLUME:
                    self._updateVolume()

            elif index == MODEL.MOLAR_VOLUME and self.mode == MODES.VOLUME_TO_DENSITY:
                self._updateDensity()

            elif index == MODEL.MASS_DENSITY and self.mode == MODES.DENSITY_TO_VOLUME:
                self._updateVolume()

    def setMode(self, mode):
        self.mode = mode

    def _updateDensity(self):
        try:
            molarMass = float(toMolarMass(self.model.item(MODEL.MOLECULAR_FORMULA).text()))
            molarVolume = float(self.model.item(MODEL.MOLAR_VOLUME).text())

            molarDensity = molarMass / molarVolume
            molarDensity = formatNumber(molarDensity, high=True)
            self.model.item(MODEL.MASS_DENSITY).setText(str(molarDensity))

        except (ArithmeticError, ValueError):
            self.model.item(MODEL.MASS_DENSITY).setText("")

    def _updateVolume(self):
        try:
            molarMass = float(toMolarMass(self.model.item(MODEL.MOLECULAR_FORMULA).text()))
            molarDensity = float(self.model.item(MODEL.MASS_DENSITY).text())

            molarVolume = molarMass / molarDensity
            molarVolume = formatNumber(molarVolume, high=True)
            self.model.item(MODEL.MOLAR_VOLUME).setText(str(molarVolume))

        except (ArithmeticError, ValueError):
            self.model.item(MODEL.MOLAR_VOLUME).setText("")

    def modelReset(self):
        try:
            self.setMode(None)
            self.model.item(MODEL.MOLECULAR_FORMULA).setText("H2O")
            self.model.item(MODEL.MOLAR_VOLUME     ).setText("")
            self.model.item(MODEL.MASS_DENSITY     ).setText("")
        finally:
            pass

    def displayHelp(self):
        location = "/user/qtgui/Calculators/density_calculator_help.html"
        self.manager.showHelp(location)


