#!/usr/bin/env python
""" Provide y=exp (ax^(2)+b),Guinier function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class GuinierModel(BaseComponent):
    """ Class that evaluates a Guinier model.
    
        Info about the model
     
        List of default parameters:
         value           = 1.0 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Guinier"

        ## Define parameters
        self.params = {}
        self.params['A'] = 0.0
        self.params['B'] = 0.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['A'] = ['', None, None]
        self.details['B'] = ['', None, None]
               
    def _guinier(self, x):
        return math.exp(self.params['A'] + self.params['B']* math.pow(x, 2))  
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (guinier value)
        """
        if x.__class__.__name__ == 'list':
            return self._guinier(x[0]*math.cos(x[1]))*self._guinier(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._guinier(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: guinier value
        """
        if x.__class__.__name__ == 'list':
            return self._guinier(x[0])*self._guinier(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._guinier(x)
