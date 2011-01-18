#!/usr/bin/env python
""" 
TwoLorentzianModel function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
from numpy import power

class TwoLorentzianModel(BaseComponent):
    """ 
    Class that evaluates a TwoLorentzianModel.
    I(q) = II(q) = scale_1/(1.0 + pow((q*length_1),exponent_1))
    + scale_2/(1.0 + pow((q*length_2),exponent_2) )+ background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "TwoLorentzian"
        self.description="""I(q) = scale_1/(1.0 + pow((q*length_1),exponent_1))
             + scale_2/(1.0 + pow((q*length_2),exponent_2) )+ background
             List of default parameters:
             scale_1 = Lorentzian term scaling #1
             length_1 = Lorentzian screening length #1 [A]
             exponent_1 = Lorentzian exponent #1
             scale_2 = Lorentzian term scaling #2
             length_2 = Lorentzian screening length #2 [A]
             exponent_2 = Lorentzian exponent #2
             background = Incoherent background
        """
        ## Define parameters
        self.params = {}
        self.params['scale_1']  = 10.0
        self.params['length_1']     = 100.0
        self.params['exponent_1']     = 3.0
        self.params['scale_2']  = 1.0
        self.params['length_2']     = 10.0
        self.params['exponent_2']     = 2.0
        self.params['background']     = 0.1
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale_1'] = ['', None, None]
        self.details['length_1'] = ['A', None, None]
        self.details['exponent_1'] =  ['', None, None]
        self.details['scale_2']  =  ['', None, None]
        self.details['length_2']  =   ['A', None, None]
        self.details['exponent_2']  =   ['', None, None]
        self.details['background']   =  ['[1/cm]', None, None]

        #list of parameter that cannot be fitted
        self.fixed= []  
    def _twolorentzian(self, x):
        """
        Model definition
        """
        inten = self.params['scale_1']/(1.0 + \
                power((x*self.params['length_1']),self.params['exponent_1']))
        inten += self.params['scale_2']/(1.0 + \
                power((x*self.params['length_2']),self.params['exponent_2']))
        inten += self.params['background']

        return inten  
   
    def run(self, x = 0.0):
        """ 
        Evaluate the model
        
        param x: input q-value (float or [float, float] as [r, theta])
        return: (scattering value)
        """
        if x.__class__.__name__ == 'list':
            return self._twolorentzian(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._twolorentzian(x)
   
    def runXY(self, x = 0.0):
        """ 
        Evaluate the model
        
        param x: input q-value (float or [float, float] as [qx, qy])
        return: scattering value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._twolorentzian(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._twolorentzian(x)
