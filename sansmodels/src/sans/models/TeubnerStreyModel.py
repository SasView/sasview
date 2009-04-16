#!/usr/bin/env python
""" 
    Provide F(x) = 1/( scale + c1*(x)^(2)+  c2*(x)^(4)) + bkd
    Teubner-Strey function as a BaseComponent model
    
"""

from sans.models.BaseComponent import BaseComponent
import math

class TeubnerStreyModel(BaseComponent):
   
    """
        Class that evaluates  the TeubnerStrey model.
        
        F(x) = 1/( scale + c1*(x)^(2)+  c2*(x)^(4)) + bkd
        
        The model has Four parameters: 
            scale  =  scale factor
            c1     =  constant
            c2     =  constant
            bkd    =  incoherent background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Teubner Strey"
        self.description="""The TeubnerStrey model.
        F(x) = 1/( scale + c1*(x)^(2)+  c2*(x)^(4)) + bkd
        
        The model has Four parameters: 
        scale  =  scale factor
        c1     =  constant
        c2     =  constant
        bkd    =  incoherent background"""
        ## Define parameters
        self.params = {}
        self.params['c1']     = -30.0
        self.params['c2']     = 5000.0
        self.params['scale']  = 0.1
        self.params['background']    = 0.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['c1']    = ['', None, None ]
        self.details['c2']    = ['', None, None ]
        self.details['scale'] = ['', None, None]
        self.details['background']   = ['[1/cm]', None, None]
        #list of parameter that cannot be fitted
        self.fixed= []
               
    def _TeubnerStrey(self, x):
        """
            Evaluate  F(x) = 1/( scale + c1*(x)^(2)+  c2*(x)^(4)) + bkd
           
        """
        return 1/( self.params['scale']+ self.params['c1'] * math.pow(x ,2)\
                + self.params['c2'] * math.pow(x ,4) ) + self.params['background']
       
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (PowerLaw value)
        """
        if x.__class__.__name__ == 'list':
            return self._TeubnerStrey(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._TeubnerStrey(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: PowerLaw value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._TeubnerStrey(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._TeubnerStrey(x)
        
    def teubnerStreyLengths(self):
        """
            Calculate the correlation length (L) 
            @return L: the correlation distance 
        """
        return  math.pow( 1/2 * math.pow( (self.params['scale']/self.params['c2']), 1/2 )\
                            +(self.params['c1']/(4*self.params['c2'])),-1/2 )
    def teubnerStreyDistance(self):
        """
            Calculate the quasi-periodic repeat distance (D/(2*pi)) 
            @return D: quasi-periodic repeat distance
        """
        return  math.pow( 1/2 * math.pow( (self.params['scale']/self.params['c2']), 1/2 )\
                            -(self.params['c1']/(4*self.params['c2'])),-1/2 )
