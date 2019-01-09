# global
import logging
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from periodictable import formula as Formula
from periodictable.xsf import xray_energy, xray_sld
from periodictable.nsf import neutron_scattering

import sas.qtgui.Utilities.GuiUtils as GuiUtils

from sas.qtgui.UI import main_resources_rc

# Local UI
from sas.qtgui.Calculators.UI.SldPanel import Ui_SldPanel

from sas.qtgui.Utilities.GuiUtils import enum

MODEL = enum(
    'MOLECULAR_FORMULA',
    'MASS_DENSITY',
    'NEUTRON_WAVELENGTH',
    'NEUTRON_SLD_REAL',
    'NEUTRON_SLD_IMAG',
    'XRAY_WAVELENGTH',
    'XRAY_SLD_REAL',
    'XRAY_SLD_IMAG',
    'NEUTRON_INC_XS',
    'NEUTRON_ABS_XS',
    'NEUTRON_LENGTH',
)

class SldResult(object):
    def __init__(self, molecular_formula, mass_density,
        neutron_wavelength, neutron_sld_real, neutron_sld_imag,
        xray_wavelength, xray_sld_real, xray_sld_imag,
        neutron_inc_xs, neutron_abs_xs, neutron_length):

        self.molecular_formula = molecular_formula
        self.mass_density = mass_density
        self.neutron_wavelength = neutron_wavelength
        self.neutron_sld_real = neutron_sld_real
        self.neutron_sld_imag = neutron_sld_imag
        self.xray_wavelength = xray_wavelength
        self.xray_sld_real = xray_sld_real
        self.xray_sld_imag = xray_sld_imag
        self.neutron_inc_xs = neutron_inc_xs
        self.neutron_abs_xs = neutron_abs_xs
        self.neutron_length = neutron_length

def sldAlgorithm(molecular_formula, mass_density, neutron_wavelength, xray_wavelength):

    xray_sld_real, xray_sld_imag = xray_sld(
            compound=molecular_formula,
            density=mass_density,
            wavelength=xray_wavelength)

    (neutron_sld_real, neutron_sld_imag, _), (_, neutron_abs_xs, neutron_inc_xs), neutron_length = \
        neutron_scattering(
            compound=molecular_formula,
            density=mass_density,
            wavelength=neutron_wavelength)

    SCALE = 1e-6

    # neutron sld
    scaled_neutron_sld_real = SCALE * neutron_sld_real
    scaled_neutron_sld_imag = SCALE * abs(neutron_sld_imag)

    # xray sld
    scaled_xray_sld_real = SCALE * xray_sld_real
    scaled_xray_sld_imag = SCALE * abs(xray_sld_imag)


    return SldResult(
        molecular_formula, mass_density,
        neutron_wavelength, scaled_neutron_sld_real, scaled_neutron_sld_imag,
        xray_wavelength, scaled_xray_sld_real, scaled_xray_sld_imag,
        neutron_inc_xs, neutron_abs_xs, neutron_length)


class SldPanel(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(SldPanel, self).__init__()

        self.manager = parent

        self.setupUi()
        # disable the context help icon
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint)

        self.setupModel()
        self.setupMapper()

    def _getOutputs(self):
        return {
            MODEL.NEUTRON_SLD_REAL: self.ui.editNeutronSldReal,
            MODEL.NEUTRON_SLD_IMAG: self.ui.editNeutronSldImag,
            MODEL.XRAY_SLD_REAL: self.ui.editXraySldReal,
            MODEL.XRAY_SLD_IMAG: self.ui.editXraySldImag,
            MODEL.NEUTRON_INC_XS: self.ui.editNeutronIncXs,
            MODEL.NEUTRON_ABS_XS: self.ui.editNeutronAbsXs,
            MODEL.NEUTRON_LENGTH: self.ui.editNeutronLength
        }

    def setupUi(self):
        self.ui = Ui_SldPanel()
        self.ui.setupUi(self)

        # set validators
        # TODO: GuiUtils.FormulaValidator() crashes with Qt5 - fix
        #self.ui.editMolecularFormula.setValidator(GuiUtils.FormulaValidator(self.ui.editMolecularFormula))

        rx = QtCore.QRegExp("[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?")
        self.ui.editMassDensity.setValidator(QtGui.QRegExpValidator(rx, self.ui.editMassDensity))
        self.ui.editNeutronWavelength.setValidator(QtGui.QRegExpValidator(rx, self.ui.editNeutronWavelength))
        self.ui.editXrayWavelength.setValidator(QtGui.QRegExpValidator(rx, self.ui.editXrayWavelength))

        # signals
        self.ui.helpButton.clicked.connect(self.displayHelp)
        self.ui.closeButton.clicked.connect(self.closePanel)
        self.ui.recalculateButton.clicked.connect(self.calculateSLD)

    def calculateSLD(self):
        self.recalculateSLD()

    def setupModel(self):
        self.model = QtGui.QStandardItemModel(self)
        self.model.setItem(MODEL.MOLECULAR_FORMULA , QtGui.QStandardItem())
        self.model.setItem(MODEL.MASS_DENSITY      , QtGui.QStandardItem())
        self.model.setItem(MODEL.NEUTRON_WAVELENGTH, QtGui.QStandardItem())
        self.model.setItem(MODEL.XRAY_WAVELENGTH   , QtGui.QStandardItem())

        for key in list(self._getOutputs().keys()):
            self.model.setItem(key, QtGui.QStandardItem())

        self.model.dataChanged.connect(self.dataChanged)

        self.ui.editMassDensity.textChanged.connect(self.recalculateSLD)
        self.ui.editMolecularFormula.textChanged.connect(self.recalculateSLD)
        self.ui.editNeutronWavelength.textChanged.connect(self.recalculateSLD)
        self.ui.editXrayWavelength.textChanged.connect(self.recalculateSLD)

        self.modelReset()

    def setupMapper(self):
        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.addMapping(self.ui.editMolecularFormula , MODEL.MOLECULAR_FORMULA)
        self.mapper.addMapping(self.ui.editMassDensity      , MODEL.MASS_DENSITY)
        self.mapper.addMapping(self.ui.editNeutronWavelength, MODEL.NEUTRON_WAVELENGTH)
        self.mapper.addMapping(self.ui.editXrayWavelength   , MODEL.XRAY_WAVELENGTH)

        for key, edit in self._getOutputs().items():
            self.mapper.addMapping(edit, key)

        self.mapper.toFirst()

    def dataChanged(self, top, bottom):
        update = False
        for index in range(top.row(), bottom.row() + 1):
            if (index == MODEL.MOLECULAR_FORMULA) or (index == MODEL.MASS_DENSITY) or (index == MODEL.NEUTRON_WAVELENGTH) or (index == MODEL.XRAY_WAVELENGTH):
                update = True

        # calculation
        if update:
            self.recalculateSLD()

    def recalculateSLD(self):
        formula = self.ui.editMolecularFormula.text()
        density = self.ui.editMassDensity.text()
        neutronWavelength = self.ui.editNeutronWavelength.text()
        xrayWavelength = self.ui.editXrayWavelength.text()

        if len(formula) > 0 and len(density) > 0 and len(neutronWavelength) > 0 and len(xrayWavelength) > 0:
            try:
                results = sldAlgorithm(str(formula), float(density), float(neutronWavelength), float(xrayWavelength))

                def format(value):
                    return ("%-5.3g" % value).strip()

                self.model.item(MODEL.NEUTRON_SLD_REAL).setText(format(results.neutron_sld_real))
                self.model.item(MODEL.NEUTRON_SLD_IMAG).setText(format(results.neutron_sld_imag))

                self.model.item(MODEL.XRAY_SLD_REAL).setText(format(results.xray_sld_real))
                self.model.item(MODEL.XRAY_SLD_IMAG).setText(format(results.xray_sld_imag))

                self.model.item(MODEL.NEUTRON_INC_XS).setText(format(results.neutron_inc_xs))
                self.model.item(MODEL.NEUTRON_ABS_XS).setText(format(results.neutron_abs_xs))
                self.model.item(MODEL.NEUTRON_LENGTH).setText(format(results.neutron_length))

                return

            except Exception as e:
                pass

        for key in list(self._getOutputs().keys()):
            self.model.item(key).setText("")

    def modelReset(self):
        #self.model.beginResetModel()
        try:
            self.model.item(MODEL.MOLECULAR_FORMULA ).setText("H2O")
            self.model.item(MODEL.MASS_DENSITY      ).setText("1.0")
            self.model.item(MODEL.NEUTRON_WAVELENGTH).setText("6.0")
            self.model.item(MODEL.XRAY_WAVELENGTH   ).setText("1.0")
            self.recalculateSLD()
        finally:
            pass
        #self.model.endResetModel()

    def displayHelp(self):
        location = "/user/qtgui/Calculators/sld_calculator_help.html"
        self.manager.showHelp(location)


    def closePanel(self):
        """
        close the window containing this panel
        """
        self.close()

