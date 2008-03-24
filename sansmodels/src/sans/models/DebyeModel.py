#!/usr/bin/env python
""" 
    Provide F(x) = 2( exp(-x)+x -1 )/x**2
    Debye function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class DebyeModel(BaseComponent):
   
    """
        Class that evaluates a Debye model.
        
        F(x) = 2( exp(-x)+x -1 )/x**2
        
        The model has three parameters: 
            Rg     =  radius of gyration
            scale  =  scale factor
            bkd    =  Constant background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Debye"

        ## Define parameters
        self.params = {}
        self.params['Rg']    = 50.0
        self.params['scale'] = 1.0
        self.params['bkd']   = 0.001

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['Rg']    = ['A', None, None]
        self.details['scale'] = ['', None, None]
        self.details['bkd']   = ['cm^{-1}', None, None]
               
    def _debye(self, x):
        """
            Evaluate F(x)= scale * D + bkd
            has 2 internal parameters :
                    D = 2 * (exp(-y) +x -1)/y**2 
                    y = (x * Rg)^(2)
        """
        # prevent a value zero in the denominator 
        if x != 0.0 :
            y = math.pow((x * self.params['Rg']), 2)
            D = 2*( math.exp(-y) + y -1 )/math.pow(y,2)
            return self.params['scale']* D + self.params['bkd']
        else: 
            return False
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (debye value)
        """
        if x.__class__.__name__ == 'list':
            return self._debye(x[0]*math.cos(x[1]))*self._debye(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._debye(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: debye value
        """
        if x.__class__.__name__ == 'list':
            return self._debye(x[0])*self._debye(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._debye(x)
