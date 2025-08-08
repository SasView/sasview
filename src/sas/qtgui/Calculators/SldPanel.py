# global
import numpy as np
from periodictable.nsf import neutron_scattering
from periodictable.xsf import xray_sld
from pyparsing.exceptions import ParseException
from PySide6 import QtCore, QtGui, QtWidgets

import sas.qtgui.Utilities.GuiUtils as GuiUtils

# Local UI
from sas.qtgui.Calculators.UI.SldPanel import Ui_SldPanel
from sas.qtgui.UI import main_resources_rc  # noqa: F401
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

class NeutronSldResult:
    def __init__(self, neutron_wavelength, neutron_sld_real,
                 neutron_sld_imag, neutron_inc_xs, neutron_abs_xs,
                 neutron_length):

        self.neutron_wavelength = neutron_wavelength
        self.neutron_sld_real = neutron_sld_real
        self.neutron_sld_imag = neutron_sld_imag
        self.neutron_inc_xs = neutron_inc_xs
        self.neutron_abs_xs = neutron_abs_xs
        self.neutron_length = neutron_length

class XraySldResult:
    def __init__(self, xray_wavelength, xray_sld_real, xray_sld_imag):

        self.xray_wavelength = xray_wavelength
        self.xray_sld_real = xray_sld_real
        self.xray_sld_imag = xray_sld_imag

def neutronSldAlgorithm(molecular_formula, mass_density, neutron_wavelength):

    (neutron_sld_real, neutron_sld_imag, _), (_, neutron_abs_xs, neutron_inc_xs), neutron_length = \
        neutron_scattering(
            compound=molecular_formula,
            density=mass_density,
            wavelength=neutron_wavelength)

    SCALE = 1e-6

    # neutron sld
    scaled_neutron_sld_real = SCALE * neutron_sld_real
    scaled_neutron_sld_imag = SCALE * abs(neutron_sld_imag)

    return NeutronSldResult(neutron_wavelength, scaled_neutron_sld_real,
                            scaled_neutron_sld_imag, neutron_inc_xs,
                            neutron_abs_xs, neutron_length)

def xraySldAlgorithm(molecular_formula, mass_density, xray_wavelength):

    xray_sld_real, xray_sld_imag = xray_sld(
            compound=molecular_formula,
            density=mass_density,
            wavelength=xray_wavelength)

    SCALE = 1e-6

    # xray sld
    scaled_xray_sld_real = SCALE * xray_sld_real
    scaled_xray_sld_imag = SCALE * abs(xray_sld_imag)


    return XraySldResult(xray_wavelength, scaled_xray_sld_real,
                         scaled_xray_sld_imag)


class SldPanel(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(SldPanel, self).__init__()

        self.manager = parent

        self.setupUi()
        self.setFixedSize(self.minimumSizeHint())

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
        # Chemical formula is checked via periodictable.formula module.
        self.ui.editMolecularFormula.setValidator(GuiUtils.FormulaValidator(self.ui.editMolecularFormula))

        rx = QtCore.QRegularExpression(r"[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?")
        self.ui.editMassDensity.setValidator(QtGui.QRegularExpressionValidator(rx, self.ui.editMassDensity))
        self.ui.editNeutronWavelength.setValidator(QtGui.QRegularExpressionValidator(rx, self.ui.editNeutronWavelength))
        self.ui.editXrayWavelength.setValidator(QtGui.QRegularExpressionValidator(rx, self.ui.editXrayWavelength))

        # signals
        self.ui.helpButton.clicked.connect(self.displayHelp)
        self.ui.closeButton.clicked.connect(self.closePanel)
        self.ui.calculateButton.clicked.connect(self.calculateSLD)

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

        #self.model.dataChanged.connect(self.dataChanged)

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
        self.ui.editMolecularFormula.setStyleSheet("background-color: white")
        self.ui.editMassDensity.setStyleSheet("background-color: white; color: black")
        formula = self.ui.editMolecularFormula.text()
        density = float(self.ui.editMassDensity.text()) if self.ui.editMassDensity.text() else None
        self.ui.editMassDensity.setToolTip("The density can either be specified here or will be calculated if all "
                                           "component densities are included in the formula.")
        neutronWavelength = self.ui.editNeutronWavelength.text()
        xrayWavelength = self.ui.editXrayWavelength.text()

        if not formula:
            return
        if not density and '@' not in formula:
            self.ui.editMassDensity.setStyleSheet("background-color: yellow")
            return
        if density and '//' in formula and '@' in formula:
            # Ignore density input when all individual densities are specified
            self.ui.editMassDensity.setStyleSheet("color: orange")
            self.ui.editMassDensity.setToolTip("The input density is overriding the density calculated from the "
                                               "individual components. Clear the density field if you want the "
                                               "calculation to take precedence.")

        def format(value):
            return ("%-5.3g" % value).strip()

        if neutronWavelength and float(neutronWavelength) > np.finfo(float).eps:
            try:
                results = neutronSldAlgorithm(str(formula), density, float(neutronWavelength))
            except (ValueError, ParseException, AssertionError, KeyError):
                self.ui.editMolecularFormula.setStyleSheet("background-color: yellow")
                return

            self.model.item(MODEL.NEUTRON_SLD_REAL).setText(format(results.neutron_sld_real))
            self.model.item(MODEL.NEUTRON_SLD_IMAG).setText(format(results.neutron_sld_imag))
            self.model.item(MODEL.NEUTRON_INC_XS).setText(format(results.neutron_inc_xs))
            self.model.item(MODEL.NEUTRON_ABS_XS).setText(format(results.neutron_abs_xs))
            self.model.item(MODEL.NEUTRON_LENGTH).setText(format(results.neutron_length))
            self.model.item(MODEL.NEUTRON_LENGTH).setEnabled(True)
            self.ui.editNeutronSldReal.setEnabled(True)
            self.ui.editNeutronSldImag.setEnabled(True)
            self.ui.editNeutronIncXs.setEnabled(True)
            self.ui.editNeutronLength.setEnabled(True)
            self.ui.editNeutronAbsXs.setEnabled(True)
        else:
            self.model.item(MODEL.NEUTRON_SLD_REAL).setText("")
            self.model.item(MODEL.NEUTRON_SLD_IMAG).setText("")
            self.model.item(MODEL.NEUTRON_INC_XS).setText("")
            self.model.item(MODEL.NEUTRON_ABS_XS).setText("")
            self.model.item(MODEL.NEUTRON_LENGTH).setText("")
            self.ui.editNeutronSldReal.setEnabled(False)
            self.ui.editNeutronSldImag.setEnabled(False)
            self.ui.editNeutronIncXs.setEnabled(False)
            self.ui.editNeutronLength.setEnabled(False)
            self.ui.editNeutronAbsXs.setEnabled(False)

        if xrayWavelength and float(xrayWavelength) > np.finfo(float).eps:
            try:
                results = xraySldAlgorithm(str(formula), density, float(xrayWavelength))
            except (ValueError, ParseException, AssertionError, KeyError):
                self.ui.editMolecularFormula.setStyleSheet("background-color: yellow")
                return

            self.model.item(MODEL.XRAY_SLD_REAL).setText(format(results.xray_sld_real))
            self.model.item(MODEL.XRAY_SLD_IMAG).setText(format(results.xray_sld_imag))
            self.ui.editXraySldReal.setEnabled(True)
            self.ui.editXraySldImag.setEnabled(True)
        else:
            self.model.item(MODEL.XRAY_SLD_REAL).setText("")
            self.model.item(MODEL.XRAY_SLD_IMAG).setText("")
            self.ui.editXraySldReal.setEnabled(False)
            self.ui.editXraySldImag.setEnabled(False)

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

