"""
This module intends to compute the neutron scattering length density 
of a molecule.It uses methods of the periodictable package to provide 
easy user interface for  Sld calculator applications.
"""

import periodictable
from periodictable import formula
from periodictable.xsf import xray_energy, xray_sld_from_atoms
from periodictable.constants import avogadro_number
import periodictable.nsf
neutron_sld_from_atoms = periodictable.nsf.neutron_sld_from_atoms 

class SldCalculator(object):
    """
    Given a molecule, a density and a wavelength, this class 
    determine scattering length density.
    
    Example: To get the sld value and the length 1/e the following 
    methods need to be called in this later order::
             formula = "H2O"
             density = 1.0
             wavelength = 6.0
             sld_calculator = SldCalculator()
             sld_calculator.set_value(formula, density, wavelength) 
             sld_real, sld_im, _ = sld_calculator.calculate_neutron_sld()
             result : sld = sld_real +i sld_im
             
    Note: **set_value()** and **calculate_neutron_sld()** methods must
    be called in this order prior calling **calculate_length()** to get 
    the proper result.
    """
    def __init__(self):
        #Private variable
        self._volume = 0.0
        #Inputs
        self.wavelength  = 6.0
        self.sld_formula = None
        self.density = None
        #Outputs
        self.sld_real = None
        self.sld_im = None
        self.coherence   = 0.0
        self.absorption  = 0.0
        self.incoherence = 0.0
        self.length = 0.0
        
    def set_value(self, formula, density, wavelength=6.0):
        """
        Store values into the sld calculator and compute the corresponding
        volume.
        """
        self.wavelength = wavelength
        self.density    = float(density)
        self.sld_formula = formula(str(formula), density=self.density)
       
        if self.density == 0:
            raise ZeroDivisionError("integer division or modulo\
                         by zero for density")
        self._volume = (self.sld_formula.mass / self.density) / avogadro_number\
                                *1.0e24   
        
        
    def calculate_xray_sld(self, element):
        """
        Get an element and compute the corresponding SLD for a given formula
        @param element:  elementis a string of existing atom
        """
        myformula = formula(str(element))
        if len(myformula.atoms) != 1:
            return 
        element = myformula.atoms.keys()[0] 
        energy = xray_energy(element.K_alpha)
        atom = self.sld_formula.atoms
        atom_reel, atom_im = xray_sld_from_atoms(atom,
                                              density= self.density,
                                              energy= energy)
        return atom_reel, atom_im
      
        
    def calculate_neutron_sld(self):
        """
        Compute the neutron SLD for a given molecule
        @return sld_real : real part of the sld value
        @return sld_im: imaginary part of the sld value
        @return inc: incoherence cross section
        """
        if self.density == 0:
            raise ZeroDivisionError("integer division or modulo\
                         by zero for density")
            return 
        atom = self.sld_formula.atoms
        sld_real, sld_im, inc = neutron_sld_from_atoms(atom, self.density, 
                                                  self.wavelength)
        self.incoherence = inc
        self.sld_real = sld_real
        self.sld_im  = sld_im
        return self.sld_real, self.sld_im, self.incoherence
    
    def calculate_length(self):
        """
        Compute the neutron 1/e length
        """
        self.length = (self.coherence + self.absorption +\
                            self.incoherence) / self._volume
        return self.length
        
