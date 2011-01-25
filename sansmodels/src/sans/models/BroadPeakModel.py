#!/usr/bin/env python
""" 
BroadPeakModel function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
from math import fabs
from numpy import power

class BroadPeakModel(BaseComponent):
    """ 
    Class that evaluates a BroadPeakModel.
    I(q) = I(q) = scale_p/pow(qval,exponent)+scale_l/
    (1.0 + pow((qval*length_l),exponent_l) )+ background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        self.counter = 0
        ## Name of the model
        self.name = "BroadPeak"
        self.description="""I(q) = scale_p/pow(q,exponent)+scale_l/
        (1.0 + pow((fabs(q-q_peak)*length_l),exponent_l) )+ background
             List of default parameters:
             scale_p = Porod term scaling
             exponent_p = Porod exponent
             scale_l = Lorentzian term scaling
             length_l = Lorentzian screening length [A]
             q_peak = peak location [1/A]
             exponent_l = Lorentzian exponent
             background = Incoherent background
        """
        ## Define parameters
        self.params = {}
        self.params['scale_p']  = 1.0e-05
        self.params['exponent_p']     = 3.0
        self.params['scale_l']  = 10.0
        self.params['length_l']     = 50.0
        self.params['q_peak']     = 0.1
        self.params['exponent_l']     = 2.0
        self.params['background']     = 0.1
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale_p'] = ['', None, None]
        self.details['exponent_p'] =  ['', None, None]
        self.details['scale_l']  =  ['', None, None]
        self.details['length_l']  =   ['[A]', None, None]
        self.details['q_peak']  =  ['[1/A]', None, None]
        self.details['exponent_l']  =   ['', None, None]
        self.details['background']   =  ['[1/cm]', None, None]

        #list of parameter that cannot be fitted
        self.fixed= []  
    def _broadpeak(self, x):
        """
        Model definition
        """
        inten = self.params['scale_p']/pow(x,self.params['exponent_p'])
        inten += self.params['scale_l']/(1.0 + \
                power((fabs(x-self.params['q_peak'])*self.params['length_l']),\
                    self.params['exponent_l']))

        inten += self.params['background']
        
        return inten  
   
    def run(self, x = 0.0):
        """ 
        Evaluate the model
        
        param x: input q-value (float or [float, float] as [r, theta])
        return: (scattering value)
        """
        if x.__class__.__name__ == 'list':
            return self._broadpeak(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._broadpeak(x)
   
    def runXY(self, x = 0.0):
        """ 
        Evaluate the model
        
        param x: input q-value (float or [float, float] as [qx, qy])
        return: scattering value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._broadpeak(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._broadpeak(x)
        
        
