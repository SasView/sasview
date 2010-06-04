#!/usr/bin/env python
""" 
Provide F(x)= P(|x|)*S(|x|) + bkd
Fractal as a BaseComponent model
"""

from sans.models.FractalModel import FractalModel
import math

class FractalAbsModel(FractalModel):
    """
    Class that evaluates a Fractal function.
    
    F(|x|)= P(|x|)*S(|x|) + bkd
    The model has Seven parameters: 
        scale        =  Volume fraction
        radius       =  Block radius
        fractal_dim  =  Fractal dimension
        corr_length  =  correlation Length
        block_sld    =  SDL block
        solvent_sld  =  SDL solvent
        background   =  background
       
    """
    def __init__(self):
        """Initialization """
        # Initialize FractalModel 

        FractalModel.__init__(self)
        ## Name of the model
        self.name = "Absolute Number Density Fractal"
        self.description="""
        I(x)= P(|x|)*S(|x|) + bkd
        
        p(x)= scale* V^(2)*delta^(2)* F(x*radius)^(2)
        F(x) = 3*[sin(x)-x cos(x)]/x**3
        
        The model has Seven parameters: 
        scale        =  Volume fraction
        radius       =  Block radius
        fractal_dim  =  Fractal dimension
        corr_length  =  correlation Length
        block_sld    =  SDL block
        solvent_sld  =  SDL solvent
        background   =  background
        """
    def _Fractal(self, x):
        """
        """
        return FractalModel._Fractal(self, math.fabs(x))
    
    