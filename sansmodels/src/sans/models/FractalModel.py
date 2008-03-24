#!/usr/bin/env python
""" 
    
    Provide F(x)= P(x)*S(x) + bkd
    Fractal as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math
from scipy.special import gamma

class FractalModel(BaseComponent):
   
    """
        Class that evaluates a Fractal function.
        
        F(x)= P(x)*S(x) + bkd
        The model has Seven parameters: 
            scale   =  Volume fraction
            Radius  =  Block radius
            Fdim    =  Fractal dimension
            L       =  correlation Length
            SDLB    =  SDL block
            SDLS    =  SDL solvent
            bkd     =  background
           
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Number Density Fractal"

        ## Define parameters
        self.params = {}
        self.params['scale'] = 0.05
        self.params['Radius']= 5
        self.params['Fdim']  = 2
        self.params['L']     = 100
        self.params['SDLB']  = 2*math.exp(-6)
        self.params['SDLS']  = 6.35*math.exp(-6)
        self.params['bkd']   = 0.0
        

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale']    = ['', None, None]
        self.details['Radius']   = ['A', None, None]
        self.details['Fdim']     = ['', None, None]
        self.details['L']        = ['A', None, None]
        self.details['SDLB']     = ['A^{-2}', None, None]
        self.details['SDLS']     = ['A^{-2}', None, None]
        self.details['bkd']      = ['cm^{-1} sr^{-1}', None, None]
       
               
    def _Fractal(self, x):
        """
            Evaluate  
            F(x) = p(x)* s(x)+bkd  
        """
        return self.params['bkd']+ self._scatterRanDom(x)* self._Block(x)
    
    def _Block(self,x):
        
        return 1 + (math.sin((self.params['Fdim']-1) * math.atan(x * self.params['L']))\
             * self.params['Fdim'] * gamma(self.params['Fdim']-1))\
           /( math.pow( (x*self.params['Radius']),self.params['Fdim'])*\
           ( 1 + 1/math.pow(((x**2)*(self.params['L']**2)),(self.params['Fdim']-1)/2)))      
           
    def _Spherical(self,x):
        """
            F(x) = [sin(x)-xcos(x)]/3*(x**3)
        """
        if x !=0:
            return (math.sin(x)-x*math.cos(x))/(3*math.pow(x,3))
        else:
            return false
    def _scatterRanDom(self,x):
        """
             calculate p(x)= scale* V^(2)*delta^(2)* F(x*Radius)^(2)
        """
        V =(4/3)*math.pi* math.pow(self.params['Radius'],3) 
        delta = self.params['SDLB']-self.params['SDLS']
        
        return self.params['scale']* (V**2)*(delta**2)*\
                (self._Spherical(x*self.params['Radius'])**2)
        
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (Fractal value)
        """
        if x.__class__.__name__ == 'list':
            return self._Fractal(x[0]*math.cos(x[1]))*self._Fractal(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._Fractal(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: Fractal value
        """
        if x.__class__.__name__ == 'list':
            return self._Fractal(x[0])*self._Fractal(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._Fractal(x)
