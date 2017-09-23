
import unittest

_SCALE = 1e-6

# the calculator default value for wavelength is 6
import periodictable
from periodictable import formula
from periodictable.xsf import xray_energy, xray_sld_from_atoms
from periodictable.constants import avogadro_number
from  periodictable.nsf import neutron_scattering, neutron_sld


def calculate_xray_sld(element, density, molecule_formula):
    """
    Get an element and compute the corresponding SLD for a given formula
    :param element:  elements a string of existing atom
    """
    element_formula = formula(str(element))
    if len(element_formula.atoms) != 1:
        return
    element = next(iter(element_formula.atoms))  # only one element...
    energy = xray_energy(element.K_alpha)
    atom = molecule_formula.atoms
    return xray_sld_from_atoms(atom, density=density, energy=energy)


class TestH2O(unittest.TestCase):
    """
    Sld calculator test for H2O
    """

    def setUp(self):
        """Inititialze variables"""

        self.compound = "H2O"
        self.density = 1.0
        self.wavelength = 6.0
        self.sld_formula = formula(self.compound, density=self.density)

    def test_neutron_sld(self):
        """
        test sld
        """
        #Compute incoherence , absorption, and incoherence
        (sld_real,sld_im,sld_inc), (coh,abs,incoh), length = neutron_scattering(self.compound,
                                       density=self.density, wavelength=self.wavelength)
        cu_real, cu_im = calculate_xray_sld(element="Cu", density=self.density,
                                  molecule_formula=self.sld_formula)
        mo_real, mo_im = calculate_xray_sld(element="Mo", density=self.density,
                                  molecule_formula=self.sld_formula)
        #test sld
        self.assertAlmostEquals(sld_real * _SCALE, -5.6e-7, 1)
        self.assertAlmostEquals(sld_im * _SCALE, 0)
        #test absorption value
        self.assertAlmostEquals(abs, 0.0741, 2)
        self.assertAlmostEquals(incoh, 5.62, 2)
        #Test length
        self.assertAlmostEquals(length, 0.1755, 3)
        #test Cu sld
        self.assertAlmostEquals(cu_real * _SCALE, 9.46e-6, 1)
        self.assertAlmostEquals(cu_im * _SCALE, 3.01e-8)
        # test Mo sld
        self.assertAlmostEquals(mo_real * _SCALE, 9.43e-6)
        self.assertAlmostEquals(mo_im * _SCALE, 5.65e-7,1)


class TestD2O(unittest.TestCase):
    """
    Sld calculator test for D2O
    """

    def setUp(self):
        """Inititialze variables"""

        self.compound = "D2O"
        self.density = 1.1
        self.wavelength = 6.0
        self.sld_formula = formula(self.compound, density=self.density)

    def test_neutron_sld(self):
        """
        test sld
        """
        #Compute incoherence , absorption, and incoherence
        (sld_real,sld_im,sld_inc), (coh,abs,incoh), length = neutron_scattering(self.compound,
                                       density=self.density, wavelength=self.wavelength)
        cu_real, cu_im = calculate_xray_sld(element="Cu", density=self.density,
                                  molecule_formula=self.sld_formula)
        mo_real, mo_im = calculate_xray_sld(element="Mo", density=self.density,
                                  molecule_formula=self.sld_formula)
        #test sld
        self.assertAlmostEquals(sld_real * _SCALE, 6.33e-6, 1)
        self.assertAlmostEquals(sld_im * _SCALE, 0)
        #test absorption value
        self.assertAlmostEquals(abs, 1.35e-4, 2)
        self.assertAlmostEquals(incoh, 0.138, 2)
        #Test length
        self.assertAlmostEquals(length, 1.549, 3)
        #test Cu sld
        self.assertAlmostEquals(cu_real * _SCALE, 9.36e-6, 1)
        self.assertAlmostEquals(cu_im * _SCALE, 2.98e-8)
        # test Mo sld
        self.assertAlmostEquals(mo_real * _SCALE, 9.33e-6)
        self.assertAlmostEquals(mo_im * _SCALE, 5.59e-9,1)


class TestCd(unittest.TestCase):
    """
    Sld calculator test for Cd
    """

    def setUp(self):
        """Inititialze variables"""
        # the calculator default value for wavelength is 6
        self.compound = "Cd"
        self.density = 4.0
        self.wavelength = 6.0
        self.sld_formula = formula(self.compound, density=self.density)

    def test_neutron_sld(self):
        """
        test sld
        """
        #Compute incoherence , absorption, and incoherence
        (sld_real,sld_im,sld_inc), (coh,abs,incoh), length = neutron_scattering(self.compound,
                                density=self.density, wavelength=self.wavelength)
        cu_real, cu_im = calculate_xray_sld(element="Cu", density=self.density,
                                  molecule_formula=self.sld_formula)
        mo_real, mo_im = calculate_xray_sld(element="Mo", density=self.density,
                                  molecule_formula=self.sld_formula)
        #test sld
        self.assertAlmostEquals(sld_real * _SCALE, 1.04e-6, 1)
        self.assertAlmostEquals(sld_im * _SCALE, -1.5e-7, 1)
        #test absorption value
        self.assertAlmostEquals(abs, 180.0,0)
        self.assertAlmostEquals(incoh, 0.0754, 2)
        #Test length
        self.assertAlmostEquals(length, 0.005551, 4)
        #test Cu sld
        self.assertAlmostEquals(cu_real * _SCALE, 2.89e-5, 1)
        self.assertAlmostEquals(cu_im * _SCALE, 2.81e-6)
        # test Mo sld
        self.assertAlmostEquals(mo_real * _SCALE, 2.84e-5, 1)
        self.assertAlmostEquals(mo_im * _SCALE, 7.26e-7,1)

if __name__ == '__main__':
    unittest.main()
