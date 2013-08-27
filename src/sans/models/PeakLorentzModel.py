#!/usr/bin/env python
""" 
    Model describes a Lorentzian shaped peak including a flat background
    Provide F(q) = scale/(1+[(q-q0)/B]^2 ) + background
    PeakLorentzModel function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class PeakLorentzModel(BaseComponent):
   
    """
        Class that evaluates a gaussian  shaped peak.
        
        F(q) = scale/(1+[(q-q0)/B]^2 ) + background
        
        The model has three parameters: 
            scale     =  scale
            q0        =  peak position
            B         =  ( hwhm) half-width-halfmaximum
            background=  incoherent background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Peak Lorentz Model"
        self.description = """ F(q) = scale/(1+[(q-q0)/B]^2 ) + background
        
        The model has three parameters: 
        scale     =  scale
        q0        =  peak position
        B         =  ( hwhm) half-width-halfmaximum
        background=  incoherent background"""
        ## Define parameters
        self.params = {}
        self.params['scale']              = 100.0
        self.params['q0']                 = 0.05
        self.params['B']              = 0.005
        self.params['background']         = 1.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['q0']            = ['[1/A]', None, None]
        self.details['scale']             = ['', 0, None]
        self.details['B']            = ['[1/A]', None, None]
        self.details['background']        = ['[1/cm]', None, None]
        #list of parameter that cannot be fitted
        self.fixed = []  
            
    def _PeakLorentz(self, x):
        """
            Evaluate  F(x) = scale/(1+[(x-q0)/B]^2 ) + background
           
        """
        return self.params['scale']/(1+\
                         math.pow((x - self.params['q0'])/self.params['B'],2)) \
                            + self.params['background']
       
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: Peak Lorentzian value
        """
        if x.__class__.__name__ == 'list':
            return self._PeakLorentz(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._PeakLorentz(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: Peak Lorentzian value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._PeakLorentz(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._PeakLorentz(x)
