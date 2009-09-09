#!/usr/bin/env python
""" 
    Provide I(q) = C/q^4,
    Porod function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class PorodModel(BaseComponent):
    """ Class that evaluates a Porod model.
    
       I(q) = scale/q^4 +background
        
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "PorodModel"

        ## Define parameters
        self.params = {}
        self.params['scale'] = 1.0
        self.params['background'] = 0.0
        self.description= """The Porod model.
        I(q) = scale/q^4 +background"""

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale']      = ['[1/(cm A^4)]', None, None]
        self.details['background'] = ['[1/cm]', None, None]
        #list of parameter that cannot be fitted
        self.fixed= []
               
    def _porod(self, x):
        return self.params['scale']/x**4.0 + self.params['background']
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (porod value)
        """
        if x.__class__.__name__ == 'list':
            return self._porod(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._porod(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: porod value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._porod(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._porod(x)
