# global
import logging
from periodictable import formula as Formula

from PyQt4 import QtGui, QtCore

# Local UI
from UI.DensityPanel import Ui_DensityPanel

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

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


class FormulaValidator(QtGui.QValidator):
    def __init__(self, parent=None):
        super(FormulaValidator, self).__init__(parent)
  
    def validate(self, input, pos):
        try:
            Formula(str(input))
            self._setStyleSheet("")
            return QtGui.QValidator.Acceptable, pos

        except Exception as e:
            self._setStyleSheet("background-color:pink;")
            return QtGui.QValidator.Intermediate, pos

    def _setStyleSheet(self, value):
        try:
            if self.parent():
                self.parent().setStyleSheet(value)
        except:
            pass


class DensityPanel(QtGui.QDialog):

    def __init__(self, parent=None):
        super(DensityPanel, self).__init__(parent)

        self.mode = None

        self.setupUi()
        self.setupModel()
        self.setupMapper()

    def setupUi(self):
        self.ui = Ui_DensityPanel()
        self.ui.setupUi(self)

        # set validators
        self.ui.editMolecularFormula.setValidator(FormulaValidator(self.ui.editMolecularFormula))

        rx = QtCore.QRegExp("[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?")
        self.ui.editMolarVolume.setValidator(QtGui.QRegExpValidator(rx, self.ui.editMolarVolume))
        self.ui.editMassDensity.setValidator(QtGui.QRegExpValidator(rx, self.ui.editMassDensity))

        # signals
        QtCore.QObject.connect(
            self.ui.editMolarVolume,
            QtCore.SIGNAL("textEdited(QString)"),
            lambda text: self.setMode(MODES.VOLUME_TO_DENSITY))
        QtCore.QObject.connect(
            self.ui.editMassDensity,
            QtCore.SIGNAL("textEdited(QString)"),
            lambda text: self.setMode(MODES.DENSITY_TO_VOLUME))
        QtCore.QObject.connect(
            self.ui.buttonBox.button(QtGui.QDialogButtonBox.Reset),
            QtCore.SIGNAL("clicked(bool)"),
            lambda checked: self.modelReset())

    def setupModel(self):
        self.model = QtGui.QStandardItemModel(self)
        self.model.setItem(MODEL.MOLECULAR_FORMULA, QtGui.QStandardItem())
        self.model.setItem(MODEL.MOLAR_MASS       , QtGui.QStandardItem())
        self.model.setItem(MODEL.MOLAR_VOLUME     , QtGui.QStandardItem())
        self.model.setItem(MODEL.MASS_DENSITY     , QtGui.QStandardItem())

        QtCore.QObject.connect(
            self.model,
            QtCore.SIGNAL("dataChanged(QModelIndex,QModelIndex)"),
            self.dataChanged)

        self.modelReset()

    def setupMapper(self):
        self.mapper = QtGui.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setOrientation(QtCore.Qt.Vertical)

        self.mapper.addMapping(self.ui.editMolecularFormula, MODEL.MOLECULAR_FORMULA)
        self.mapper.addMapping(self.ui.editMolarMass       , MODEL.MOLAR_MASS)
        self.mapper.addMapping(self.ui.editMolarVolume     , MODEL.MOLAR_VOLUME)
        self.mapper.addMapping(self.ui.editMassDensity     , MODEL.MASS_DENSITY)

        self.mapper.toFirst()

    def dataChanged(self, top, bottom):
        for index in xrange(top.row(), bottom.row() + 1):
            if index == MODEL.MOLECULAR_FORMULA:
                molarMass = toMolarMass(self.model.item(MODEL.MOLECULAR_FORMULA).text())
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
            self.model.item(MODEL.MASS_DENSITY).setText(str(molarDensity))

        except:
            self.model.item(MODEL.MASS_DENSITY).setText("")

    def _updateVolume(self):
        try:
            molarMass = float(toMolarMass(self.model.item(MODEL.MOLECULAR_FORMULA).text()))
            molarDensity = float(self.model.item(MODEL.MASS_DENSITY).text())

            molarVolume = molarMass / molarDensity
            self.model.item(MODEL.MOLAR_VOLUME).setText(str(molarVolume))

        except:
            self.model.item(MODEL.MOLAR_VOLUME).setText("")

    def modelReset(self):
        #self.model.beginResetModel()
        try:
            self.setMode(None)
            self.model.item(MODEL.MOLECULAR_FORMULA).setText("H2O")
            self.model.item(MODEL.MOLAR_VOLUME     ).setText("")
            self.model.item(MODEL.MASS_DENSITY     ).setText("")
        finally:
            pass
            #self.model.endResetModel()
