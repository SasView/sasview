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
            scale        =  Volume fraction
            radius       =  Block radius
            fractal_dim  =  Fractal dimension
            corr_length  =  correlation Length
            block_sld    =  SDL block
            solvent_sld  =  SDL solvent
            background   =  background
           
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then fractal
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Number Density Fractal"
        self.description="""
        I(x)= P(x)*S(x) + bkd
        
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
        ## Define parameters
        self.params = {}
        self.params['scale']       = 0.05
        self.params['radius']      = 5.0
        self.params['fractal_dim'] = 2.0
        self.params['corr_length'] = 100.0
        self.params['block_sld']   = 2.0e-6
        self.params['solvent_sld'] = 6.0e-6
        self.params['background']  = 0.0
        

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale']       = ['',     None, None]
        self.details['radius']      = ['[A]',    None, None]
        self.details['fractal_dim'] = ['',       0,  None]
        self.details['corr_length'] = ['[A]',    None, None]
        self.details['block_sld']   = ['[1/A^(2)]',  None, None]
        self.details['solvent_sld'] = ['[1/A^(2)]',  None, None]
        self.details['background']  = ['[1/cm]', None, None]
       
               
    def _Fractal(self, x):
        """
            Evaluate  
            F(x) = p(x) * s(x) + bkd  
        """
        #if x<0 and self.params['fractal_dim']>0:
         #   raise ValueError, "negative number cannot be raised to a fractional power"
        #if x==0 and self.params['fractal_dim']==0:
         #   return 1+self.params['background']
        #elif x<0 and self.params['fractal_dim']==0:
        #    return 1e+32
        #else:
        return self.params['background']+ self._scatterRanDom(x)* self._Block(x)

    
    def _Block(self,x):
        #if self.params['fractal_dim']<0:
        #    self.params['fractal_dim']=-self.params['fractal_dim']
        try:
            if x<0:
                x=-x
            if self.params['radius']<0:
                self.params['radius']=-self.params['radius']
                
            if x==0 or self.params['radius']==0 :
                 return 1e+32
            elif self.params['fractal_dim']==0:
                return 1.0 + (math.sin((self.params['fractal_dim']-1.0) * math.atan(x * self.params['corr_length']))\
                              * self.params['fractal_dim'] * gamma(self.params['fractal_dim']-1.0))\
                              *( math.pow( 1.0 + 1.0/((x**2)*(self.params['corr_length']**2)),1/2.0)) 
            elif self.params['corr_length']==0 or self.params['fractal_dim']==1:
                return 1.0 + (math.sin((self.params['fractal_dim']-1.0) * math.atan(x * self.params['corr_length']))\
                              * self.params['fractal_dim'] * gamma(self.params['fractal_dim']-1.0))\
                              /( math.pow( (x*self.params['radius']), self.params['fractal_dim']))   
                
            elif self.params['fractal_dim']<1:
                return 1.0 + (math.sin((self.params['fractal_dim']-1.0) * math.atan(x * self.params['corr_length']))\
                              * self.params['fractal_dim'] * gamma(self.params['fractal_dim']-1.0))\
                              /( math.pow( (x*self.params['radius']), self.params['fractal_dim']))*\
                                 math.pow( 1.0 + 1.0/((x**2)*(self.params['corr_length']**2)),(1-self.params['fractal_dim'])/2.0)   
            else:
                return 1.0 + (math.sin((self.params['fractal_dim']-1.0) * math.atan(x * self.params['corr_length']))\
                              * self.params['fractal_dim'] * gamma(self.params['fractal_dim']-1.0))\
                              / math.pow( (x*self.params['radius']), self.params['fractal_dim'])\
                                 /math.pow( 1.0 + 1.0/((x**2)*(self.params['corr_length']**2)),(self.params['fractal_dim']-1.0)/2.0)   
        except:
            return 1 # Need a real fix. 
    def _Spherical(self,x):
        """
            F(x) = 3*[sin(x)-xcos(x)]/x**3
        """
        if x==0:
            return 0
        else:
            return 3.0*(math.sin(x)-x*math.cos(x))/(math.pow(x,3.0))
        
    def _scatterRanDom(self,x):
        """
             calculate p(x)= scale* V^(2)*delta^(2)* F(x*Radius)^(2)
        """
        V =(4.0/3.0)*math.pi* math.pow(self.params['radius'],3.0) 
        delta = self.params['block_sld']-self.params['solvent_sld']
        
        return 1.0e8*self.params['scale']* V *(delta**2)*\
                (self._Spherical(x*self.params['radius'])**2)
        
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (Fractal value)
        """
        if x.__class__.__name__ == 'list':
            # Take absolute value of Q, since this model is really meant to
            # be defined in 1D for a given length of Q
            #qx = math.fabs(x[0]*math.cos(x[1]))
            #qy = math.fabs(x[0]*math.sin(x[1]))
            
            return self._Fractal(math.fabs(x[0]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._Fractal(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: Fractal value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._Fractal(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._Fractal(x)
