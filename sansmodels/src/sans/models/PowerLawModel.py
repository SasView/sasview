#!/usr/bin/env python
""" 
    Provide F(x) = scale/( 1 + (x*L)^2 ) + bkd
    Lorentz function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class PowerLawModel(BaseComponent):
   
    """
        Class that evaluates a Power_Law model.
        
        F(x) = scale* (x)^(m) + bkd
        
        The model has three parameters: 
            m     =  power
            scale  =  scale factor
            bkd    =  incoherent background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Power_Law"

        ## Define parameters
        self.params = {}
        self.params['m']     = 50.0
        self.params['scale'] = 100.0
        self.params['bkd']   = 1

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['m']    = ['', None, None ]
        self.details['scale'] = ['', None, None]
        self.details['bkd']   = ['cm^{-1}', None, None]
               
    def _PowerLaw(self, x):
        """
            Evaluate  F(x) = scale* (x)^(m) + bkd
           
        """
        return self.params['scale']*math.pow(x ,self.params['m'])\
                + self.params['bkd']
       
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (PowerLaw value)
        """
        if x.__class__.__name__ == 'list':
            return self._PowerLaw(x[0]*math.cos(x[1]))*self._PowerLaw(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._PowerLaw(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: PowerLaw value
        """
        if x.__class__.__name__ == 'list':
            return self._PowerLaw(x[0])*self._PowerLaw(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._PowerLaw(x)
