#!/usr/bin/env python
""" 
    Provide F(x) = scale* (|x|)^(-m) + bkd
    Power law function as a BaseComponent model
"""

from sans.models.PowerLawModel import PowerLawModel
import math
class PowerLawAbsModel(PowerLawModel):
    """
        Class that evaluates a absolute Power_Law model.
        
        F(x) = scale* (|x|)^(-m) + bkd
        
        The model has three parameters: 
            m     =  power
            scale  =  scale factor
            bkd    =  incoherent background
    """
    
    def __init__(self):
        """ Initialization """
        # Initialize PowerLawAbsModel 
        PowerLawModel.__init__(self)
        ## Name of the model
        self.name = "Absolute Power_Law"
        self.description=""" The Power_Law model.
        F(x) = scale* (|x|)^(-m) + bkd
        
        The model has three parameters: 
        m     =  power
        scale  =  scale factor
        bkd    =  incoherent background"""
        
        
    def _PowerLaw(self, x):
        return PowerLawModel._PowerLaw(self, math.fabs(x))
       