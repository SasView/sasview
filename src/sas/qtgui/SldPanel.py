# global
import logging
from periodictable import formula as Formula
from periodictable.xsf import xray_energy, xray_sld_from_atoms
from periodictable.nsf import neutron_scattering

from PyQt4 import QtGui, QtCore

# Local UI
from UI.SldPanel import Ui_SldPanel

def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

MODEL = enum(
    'MOLECULAR_FORMULA',
    'MASS_DENSITY',
    'WAVELENGTH',
    'NEUTRON_SLD_REAL',
    'NEUTRON_SLD_IMAG',
    'CU_KA_SLD_REAL',
    'CU_KA_SLD_IMAG',
    'MO_KA_SLD_REAL',
    'MO_KA_SLD_IMAG',
    'NEUTRON_INC_XS',
    'NEUTRON_ABS_XS',
    'NEUTRON_LENGTH',
)

class SldResult(object):
    def __init__(self, molecular_formula, mass_density, wavelength,
        neutron_sld_real, neutron_sld_imag,
        cu_ka_sld_real, cu_ka_sld_imag,
        mo_ka_sld_real, mo_ka_sld_imag,
        neutron_inc_xs, neutron_abs_xs, neutron_length):

        self.molecular_formula = molecular_formula
        self.mass_density = mass_density
        self.wavelength = wavelength
        self.neutron_sld_real = neutron_sld_real
        self.neutron_sld_imag = neutron_sld_imag
        self.cu_ka_sld_real = cu_ka_sld_real
        self.cu_ka_sld_imag = cu_ka_sld_imag
        self.mo_ka_sld_real = mo_ka_sld_real
        self.mo_ka_sld_imag = mo_ka_sld_imag
        self.neutron_inc_xs = neutron_inc_xs
        self.neutron_abs_xs = neutron_abs_xs
        self.neutron_length = neutron_length

def sldAlgorithm(molecular_formula, mass_density, wavelength):

    sld_formula = Formula(molecular_formula, density=mass_density)

    def calculate_sld(formula):
        if len(formula.atoms) != 1:
            raise NotImplementedError()
        energy = xray_energy(formula.atoms.keys()[0].K_alpha)
        return xray_sld_from_atoms(
            sld_formula.atoms,
            density=mass_density,
            energy=energy)

    cu_real, cu_imag = calculate_sld(Formula("Cu"))
    mo_real, mo_imag = calculate_sld(Formula("Mo"))

    (sld_real, sld_imag, _), (_, neutron_abs_xs, neutron_inc_xs), neutron_length = \
        neutron_scattering(
            compound=molecular_formula,
            density=mass_density,
            wavelength=wavelength)

    SCALE = 1e-6

    # neutron sld
    neutron_sld_real = SCALE * sld_real
    neutron_sld_imag = SCALE * abs(sld_imag)

    # Cu sld
    cu_ka_sld_real = SCALE * cu_real
    cu_ka_sld_imag = SCALE * abs(cu_imag)

    # Mo sld
    mo_ka_sld_real = SCALE * mo_real
    mo_ka_sld_imag = SCALE * abs(mo_imag)

    return SldResult(
        molecular_formula, mass_density, wavelength,
        neutron_sld_real, neutron_sld_imag,
        cu_ka_sld_real, cu_ka_sld_imag,
        mo_ka_sld_real, mo_ka_sld_imag,
        neutron_inc_xs, neutron_abs_xs, neutron_length)


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


class SldPanel(QtGui.QDialog):

    def __init__(self, parent=None):
        super(SldPanel, self).__init__(parent)

        self.setupUi()
        self.setupModel()
        self.setupMapper()

    def _getOutputs(self):
        return {
            MODEL.NEUTRON_SLD_REAL: self.ui.editNeutronSldReal,
            MODEL.NEUTRON_SLD_IMAG: self.ui.editNeutronSldImag,
            MODEL.CU_KA_SLD_REAL: self.ui.editCuKaSldReal,
            MODEL.CU_KA_SLD_IMAG: self.ui.editCuKaSldImag,
            MODEL.MO_KA_SLD_REAL: self.ui.editMoKaSldReal,
            MODEL.MO_KA_SLD_IMAG: self.ui.editMoKaSldImag,
            MODEL.NEUTRON_INC_XS: self.ui.editNeutronIncXs,
            MODEL.NEUTRON_ABS_XS: self.ui.editNeutronAbsXs,
            MODEL.NEUTRON_LENGTH: self.ui.editNeutronLength
        }

    def setupUi(self):
        self.ui = Ui_SldPanel()
        self.ui.setupUi(self)

        # set validators
        self.ui.editMolecularFormula.setValidator(FormulaValidator(self.ui.editMolecularFormula))

        rx = QtCore.QRegExp("[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?")
        self.ui.editMassDensity.setValidator(QtGui.QRegExpValidator(rx, self.ui.editMassDensity))
        self.ui.editWavelength.setValidator(QtGui.QRegExpValidator(rx, self.ui.editWavelength))

        # signals
        QtCore.QObject.connect(
            self.ui.buttonBox.button(QtGui.QDialogButtonBox.Reset),
            QtCore.SIGNAL("clicked(bool)"),
            lambda checked: self.modelReset())

    def setupModel(self):
        self.model = QtGui.QStandardItemModel(self)
        self.model.setItem(MODEL.MOLECULAR_FORMULA, QtGui.QStandardItem())
        self.model.setItem(MODEL.MASS_DENSITY     , QtGui.QStandardItem())
        self.model.setItem(MODEL.WAVELENGTH       , QtGui.QStandardItem())

        for key in self._getOutputs().keys():
            self.model.setItem(key, QtGui.QStandardItem())

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
        self.mapper.addMapping(self.ui.editMassDensity     , MODEL.MASS_DENSITY)
        self.mapper.addMapping(self.ui.editWavelength      , MODEL.WAVELENGTH)

        for key, edit in self._getOutputs().iteritems():
            self.mapper.addMapping(edit, key)

        self.mapper.toFirst()

    def dataChanged(self, top, bottom):
        update = False
        for index in xrange(top.row(), bottom.row() + 1):
            if (index == MODEL.MOLECULAR_FORMULA) or (index == MODEL.MASS_DENSITY) or (index == MODEL.WAVELENGTH):
                update = True

        # calcualtion
        if update:
            formula = self.model.item(MODEL.MOLECULAR_FORMULA).text()
            density = self.model.item(MODEL.MASS_DENSITY).text()
            wavelength = self.model.item(MODEL.WAVELENGTH).text()
            if len(formula) > 0 and len(density) > 0 and len(wavelength) > 0:
                try:
                    results = sldAlgorithm(str(formula), float(density), float(wavelength))

                    def format(value):
                        return ("%-5.3g" % value).strip()

                    self.model.item(MODEL.NEUTRON_SLD_REAL).setText(format(results.neutron_sld_real))
                    self.model.item(MODEL.NEUTRON_SLD_IMAG).setText(format(results.neutron_sld_imag))

                    self.model.item(MODEL.CU_KA_SLD_REAL).setText(format(results.cu_ka_sld_real))
                    self.model.item(MODEL.CU_KA_SLD_IMAG).setText(format(results.cu_ka_sld_imag))

                    self.model.item(MODEL.MO_KA_SLD_REAL).setText(format(results.mo_ka_sld_real))
                    self.model.item(MODEL.MO_KA_SLD_IMAG).setText(format(results.mo_ka_sld_imag))

                    self.model.item(MODEL.NEUTRON_INC_XS).setText(format(results.neutron_inc_xs))
                    self.model.item(MODEL.NEUTRON_ABS_XS).setText(format(results.neutron_abs_xs))
                    self.model.item(MODEL.NEUTRON_LENGTH).setText(format(results.neutron_length))

                    return
            
                except Exception as e:
                    pass

            for key in self._getOutputs().keys():
                self.model.item(key).setText("")

    def modelReset(self):
        #self.model.beginResetModel()
        try:
            self.model.item(MODEL.MOLECULAR_FORMULA).setText("H2O")
            self.model.item(MODEL.MASS_DENSITY     ).setText("1")
            self.model.item(MODEL.WAVELENGTH       ).setText("6")
        finally:
            pass
            #self.model.endResetModel()
