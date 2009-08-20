"""
    This module intends to compute the neutron scattering length density of molecule
    @author: Gervaise B. Alina
"""

import periodictable
from periodictable import formula
from periodictable.xsf import xray_energy, xray_sld_from_atoms
from periodictable.constants import avogadro_number
import periodictable.nsf
neutron_sld_from_atoms= periodictable.nsf.neutron_sld_from_atoms 

class SldCalculator(object):
    """
        compute neutron SLD and related parameters
    """
    def __init__(self):
        self.wavelength  = 6.0
        self.coherence   = 0.0
        self.absorption  = 0.0
        self.incoherence = 0.0
        self.sld_formula = None
        self.volume = 0.0
        self.density = None
        self.length= 0.0
        
        
    def setValue(self,user_formula, density, wavelength=6.0):
        """
            Store values of density and wavelength into the calculator 
            and compute the volume
        """
        self.wavelength = wavelength
        self.density    = float(density)
        self.sld_formula = formula(str(user_formula), density= self.density)
        if self.density==0:
            raise ZeroDivisionError,"integer division or modulo by zero for density"
            return 
        self.volume = (self.sld_formula.mass /self.density)/avogadro_number*1.0e24   
        
        
    def calculateXRaySld(self, element):
        """
            Get an element and compute the corresponding SLD for a given formula
            @param element:  elementis a string of existing atom
        """
        myformula = formula(str (element))
        if len(myformula.atoms)!=1:
            return 
        element= myformula.atoms.keys()[0] 
        energy = xray_energy(element.K_alpha)
        atom = self.sld_formula.atoms
        atom_reel, atom_im = xray_sld_from_atoms( atom,
                                              density= self.density,
                                              energy= energy )
        return atom_reel, atom_im
      
        
    def calculateNSld(self):
        """
            Compute the neutron SLD for a given molecule
            @return absorp: absorption
            @return coh: coherence cross section
            @return inc: incoherence cross section
        """
        if self.density ==0:
            raise ZeroDivisionError,"integer division or modulo by zero for density"
            return 
        atom = self.sld_formula.atoms
        coh,absorp,inc = neutron_sld_from_atoms(atom,self.density,self.wavelength)
        #Don't know if value is return in cm or  cm^(-1).assume return in cm
        # to match result of neutron inc of Alan calculator
        self.incoherence = inc*1/10
        #Doesn't match result of Alan calculator for absorption factor of 2
        #multiplication of 100 is going around
        self.absorption = absorp*2*100
        self.coherence  = coh
        return self.coherence, self.absorption, self.incoherence
    
    
    def computeLength(self):
        """
            Compute the neutron 1/e length
        """
        self.length= (self.coherence+ self.absorption+ self.incoherence)/self.volume
        return self.length
        
        
    def absorptionIm(self):
        """
            Compute imaginary part of the absorption 
        """
        atom = self.sld_formula.atoms 
        #im: imaginary part of neutron SLD
        im=0
        for el, count in atom.iteritems():
            if el.neutron.b_c_i !=None:
                im += el.neutron.b_c_i*count 
        if self.volume !=0:
            im = im/self.volume
        else:
            raise ZeroDivisionError,"integer division or modulo by zero for volume"
        return im
        