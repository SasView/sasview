#!/usr/bin/env python
""" 
    Provide F(x) = scale/( 1 + (x*L)^2 )^(2) + background
    DAB (Debye Anderson Brumberger) function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class DABModel(BaseComponent):
   
    """
        Class that evaluates a DAB model.
        
        F(x) = scale*(L^3)/( 1 + (x*L)^2 )^(2) + background
        
        The model has three parameters: 
            L             =  Correlation Length
            scale         =  scale factor
            background    =  incoherent background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "DAB_Model"
        self.description="""F(x) = scale*(L^3)/( 1 + (x*L)^2 )^(2) + background
        
        The model has three parameters: 
        L             =  Correlation Length
        scale         =  scale factor
        background    =  incoherent background"""
        ## Define parameters
        self.params = {}
        self.params['length']             = 50.0
        self.params['scale']              = 1.0
        self.params['background']         = 0.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['length']            = ['[A]', None, None]
        self.details['scale']             = ['', None, None]
        self.details['background']        = ['[1/cm]', None, None]
        #list of parameter that cannot be fitted
        self.fixed= []      
    def _DAB(self, x):
        """
            Evaluate  F(x) = (scale*L^3)/( 1 + (x*L)^2 )^(2) + background
           
        """
        # According to SRK (Igor/NIST code: 6 JUL 2009  changed definition of 'scale' to be uncorrelated with 'length')
        return self.params['scale']*math.pow(self.params['length'],3)/math.pow(( 1 + math.pow(x * self.params['length'],2)),2) \
         + self.params['background']
       
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (DAB value)
        """
        if x.__class__.__name__ == 'list':
            return self._DAB(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._DAB(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: DAB value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._DAB(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._DAB(x)
