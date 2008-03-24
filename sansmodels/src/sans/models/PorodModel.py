#!/usr/bin/env python
""" Provide y=,Guinier function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class PorodModel(BaseComponent):
    """ Class that evaluates a Porod model.
    
       F(x) = exp[ [C]/Q**4 ]
        
        The model has one parameter: C
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Porod Model"

        ## Define parameters
        self.params = {}
        self.params['C'] = 0.0
        

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['C'] = ['', None, None]
      
               
    def _porod(self, x):
        return math.exp(self.params['C']/ math.pow(x, 4))  
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (porod value)
        """
        if x.__class__.__name__ == 'list':
            return self._porod(x[0]*math.cos(x[1]))*self._porod(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._porod(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: porod value
        """
        if x.__class__.__name__ == 'list':
            return self._porod(x[0])*self._porod(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._porod(x)
