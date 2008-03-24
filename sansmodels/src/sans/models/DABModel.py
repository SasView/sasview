#!/usr/bin/env python
""" 
    Provide F(x) = scale/( 1 + (x*L)^2 )^(2)
    DAB (Debye Anderson Brumberger) function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class DABModel(BaseComponent):
   
    """
        Class that evaluates a DAB model.
        
        F(x) = scale/( 1 + (x*L)^2 )^(2) +bkd
        
        The model has three parameters: 
            L     =  Correlation Length
            scale  =  scale factor
            bkd    =  incoherent background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = " DAB_Model "

        ## Define parameters
        self.params = {}
        self.params['L']     = 40.0
        self.params['scale'] = 10.0
        self.params['bkd']   = 0.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['L']    = ['A', None, None]
        self.details['scale'] = ['', None, None]
        self.details['bkd']   = ['cm^{-1}', None, None]
               
    def _DAB(self, x):
        """
            Evaluate  F(x) = scale/( 1 + (x*L)^2 )^(2) + bkd
           
        """
        return self.params['scale']/math.pow(( 1 + math.pow(x * self.params['L'],2)),2) \
         + self.params['bkd']
       
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (DAB value)
        """
        if x.__class__.__name__ == 'list':
            return self._DAB(x[0]*math.cos(x[1]))*self._DAB(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._DAB(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: DAB value
        """
        if x.__class__.__name__ == 'list':
            return self._DAB(x[0])*self._DAB(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._DAB(x)
