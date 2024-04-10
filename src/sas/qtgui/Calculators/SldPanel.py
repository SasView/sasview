# global
import numpy as np
import logging
from PySide6 import QtCore
from PySide6 import QtGui
from PySide6 import QtWidgets

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

class NeutronSldResult(object):
    def __init__(self, neutron_wavelength, neutron_sld_real,
                 neutron_sld_imag, neutron_inc_xs, neutron_abs_xs,
                 neutron_length):

        self.neutron_wavelength = neutron_wavelength
        self.neutron_sld_real = neutron_sld_real
        self.neutron_sld_imag = neutron_sld_imag
        self.neutron_inc_xs = neutron_inc_xs
        self.neutron_abs_xs = neutron_abs_xs
        self.neutron_length = neutron_length

class XraySldResult(object):
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
            MODEL.NEUTRON_SLD_REAL: self.ui.txtEditNeutronSldReal,
            MODEL.NEUTRON_SLD_IMAG: self.ui.txtEditNeutronSldImag,
            MODEL.XRAY_SLD_REAL: self.ui.txtEditXraySldReal,
            MODEL.XRAY_SLD_IMAG: self.ui.txtEditXraySldImag,
            MODEL.NEUTRON_INC_XS: self.ui.txtEditNeutronIncXs,
            MODEL.NEUTRON_ABS_XS: self.ui.txtEditNeutronAbsXs,
            MODEL.NEUTRON_LENGTH: self.ui.txtEditNeutronLength
        }

    def setupUi(self):
        self.ui = Ui_SldPanel()
        self.ui.setupUi(self)

        # set validators
        # TODO: GuiUtils.FormulaValidator() crashes with Qt5 - fix
        #self.ui.txtEditMolecularFormula.setValidator(GuiUtils.FormulaValidator(self.ui.txtEditMolecularFormula))

        # No need for recalculate
        self.ui.cmdRecalculate.setVisible(False)

        rx = QtCore.QRegularExpression("[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?")
        self.ui.txtEditMassDensity.setValidator(QtGui.QRegularExpressionValidator(rx, self.ui.txtEditMassDensity))
        self.ui.txtEditNeutronWavelength.setValidator(QtGui.QRegularExpressionValidator(rx, self.ui.txtEditNeutronWavelength))
        self.ui.txtEditXrayWavelength.setValidator(QtGui.QRegularExpressionValidator(rx, self.ui.txtEditXrayWavelength))

        # signals
        self.ui.cmdHelp.clicked.connect(self.displayHelp)
        self.ui.cmdClose.clicked.connect(self.closePanel)
        self.ui.cmdRecalculate.clicked.connect(self.calculateSLD)

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

        self.ui.txtEditMassDensity.textChanged.connect(self.recalculateSLD)
        self.ui.txtEditMolecularFormula.textChanged.connect(self.recalculateSLD)
        self.ui.txtEditNeutronWavelength.textChanged.connect(self.recalculateSLD)
        self.ui.txtEditXrayWavelength.textChanged.connect(self.recalculateSLD)

        self.modelReset()

    def setupMapper(self):
        self.mapper = QtWidgets.QDataWidgetMapper(self)
        self.mapper.setModel(self.model)
        self.mapper.setOrientation(QtCore.Qt.Vertical)
        self.mapper.addMapping(self.ui.txtEditMolecularFormula , MODEL.MOLECULAR_FORMULA)
        self.mapper.addMapping(self.ui.txtEditMassDensity      , MODEL.MASS_DENSITY)
        self.mapper.addMapping(self.ui.txtEditNeutronWavelength, MODEL.NEUTRON_WAVELENGTH)
        self.mapper.addMapping(self.ui.txtEditXrayWavelength   , MODEL.XRAY_WAVELENGTH)

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
        formula = self.ui.txtEditMolecularFormula.text()
        density = self.ui.txtEditMassDensity.text()
        neutronWavelength = self.ui.txtEditNeutronWavelength.text()
        xrayWavelength = self.ui.txtEditXrayWavelength.text()

        if not formula or not density:
            return

        def format(value):
            return ("%-5.3g" % value).strip()

        if neutronWavelength and float(neutronWavelength) > np.finfo(float).eps:
            results = neutronSldAlgorithm(str(formula), float(density), float(neutronWavelength))

            self.model.item(MODEL.NEUTRON_SLD_REAL).setText(format(results.neutron_sld_real))
            self.model.item(MODEL.NEUTRON_SLD_IMAG).setText(format(results.neutron_sld_imag))
            self.model.item(MODEL.NEUTRON_INC_XS).setText(format(results.neutron_inc_xs))
            self.model.item(MODEL.NEUTRON_ABS_XS).setText(format(results.neutron_abs_xs))
            self.model.item(MODEL.NEUTRON_LENGTH).setText(format(results.neutron_length))
            self.model.item(MODEL.NEUTRON_LENGTH).setEnabled(True)
            self.ui.txtEditNeutronSldReal.setEnabled(True)
            self.ui.txtEditNeutronSldImag.setEnabled(True)
            self.ui.txtEditNeutronIncXs.setEnabled(True)
            self.ui.txtEditNeutronLength.setEnabled(True)
            self.ui.txtEditNeutronAbsXs.setEnabled(True)
        else:
            self.model.item(MODEL.NEUTRON_SLD_REAL).setText("")
            self.model.item(MODEL.NEUTRON_SLD_IMAG).setText("")
            self.model.item(MODEL.NEUTRON_INC_XS).setText("")
            self.model.item(MODEL.NEUTRON_ABS_XS).setText("")
            self.model.item(MODEL.NEUTRON_LENGTH).setText("")
            self.ui.txtEditNeutronSldReal.setEnabled(False)
            self.ui.txtEditNeutronSldImag.setEnabled(False)
            self.ui.txtEditNeutronIncXs.setEnabled(False)
            self.ui.txtEditNeutronLength.setEnabled(False)
            self.ui.txtEditNeutronAbsXs.setEnabled(False)

        if xrayWavelength and float(xrayWavelength) > np.finfo(float).eps:
            results = xraySldAlgorithm(str(formula), float(density), float(xrayWavelength))

            self.model.item(MODEL.XRAY_SLD_REAL).setText(format(results.xray_sld_real))
            self.model.item(MODEL.XRAY_SLD_IMAG).setText(format(results.xray_sld_imag))
            self.ui.txtEditXraySldReal.setEnabled(True)
            self.ui.txtEditXraySldImag.setEnabled(True)
        else:
            self.model.item(MODEL.XRAY_SLD_REAL).setText("")
            self.model.item(MODEL.XRAY_SLD_IMAG).setText("")
            self.ui.txtEditXraySldReal.setEnabled(False)
            self.ui.txtEditXraySldImag.setEnabled(False)

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

