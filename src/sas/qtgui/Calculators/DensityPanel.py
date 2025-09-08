# global
from periodictable import formula as Formula
from PySide6 import QtCore, QtGui, QtWidgets

from sas.qtgui.Calculators.UI.DensityPanel import Ui_DensityPanel

# Local UI
from sas.qtgui.UI import main_resources_rc  # noqa: F401
from sas.qtgui.Utilities.GuiUtils import enum, formatNumber

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

        self.setFixedSize(self.minimumSizeHint())

        rx = QtCore.QRegularExpression(r"[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?")
        self.ui.editMolarVolume.setValidator(QtGui.QRegularExpressionValidator(rx, self.ui.editMolarVolume))
        self.ui.editMassDensity.setValidator(QtGui.QRegularExpressionValidator(rx, self.ui.editMassDensity))

        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.modelReset)
        self.ui.buttonBox.button(QtWidgets.QDialogButtonBox.Help).clicked.connect(self.displayHelp)

    def setupModel(self):
        self.model = QtGui.QStandardItemModel(self)
        self.model.setItem(MODEL.MOLECULAR_FORMULA, QtGui.QStandardItem())
        self.model.setItem(MODEL.MOLAR_MASS       , QtGui.QStandardItem())
        self.model.setItem(MODEL.MOLAR_VOLUME     , QtGui.QStandardItem())
        self.model.setItem(MODEL.MASS_DENSITY     , QtGui.QStandardItem())

        self.model.dataChanged.connect(self.dataChanged)

        self.ui.editMolarVolume.textEdited.connect(self.volumeChanged)
        self.ui.editMassDensity.textEdited.connect(self.massChanged)
        self.ui.editMolecularFormula.textEdited.connect(self.formulaChanged)

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

    def volumeChanged(self, current_text):
        self.setMode(MODES.VOLUME_TO_DENSITY)
        try:
            molarMass = float(toMolarMass(self.model.item(MODEL.MOLECULAR_FORMULA).text()))
            molarVolume = float(current_text)

            molarDensity = molarMass / molarVolume
            molarDensity = formatNumber(molarDensity, high=True)
            self.model.item(MODEL.MASS_DENSITY).setText(str(molarDensity))
            # be sure to store the new value in the model
            self.model.item(MODEL.MOLAR_VOLUME).setText(current_text)

        except (ArithmeticError, ValueError):
            self.model.item(MODEL.MASS_DENSITY).setText("")

    def massChanged(self, current_text):
        self.setMode(MODES.DENSITY_TO_VOLUME)
        try:
            molarMass = float(toMolarMass(self.model.item(MODEL.MOLECULAR_FORMULA).text()))
            molarDensity = float(current_text)

            molarVolume = molarMass / molarDensity
            molarVolume = formatNumber(molarVolume, high=True)
            self.model.item(MODEL.MOLAR_VOLUME).setText(str(molarVolume))
            # be sure to store the new value in the model
            self.model.item(MODEL.MASS_DENSITY).setText(current_text)

        except (ArithmeticError, ValueError):
            self.model.item(MODEL.MOLAR_VOLUME).setText("")

    def formulaChanged(self, current_text):
        try:
            toMolarMass(current_text)
            # if this doesn't fail, update the model item for formula
            # so related values can get recomputed
            self.model.item(MODEL.MOLECULAR_FORMULA).setText(current_text)

        except (ArithmeticError, ValueError):
            self.model.item(MODEL.MOLAR_VOLUME).setText("")

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


