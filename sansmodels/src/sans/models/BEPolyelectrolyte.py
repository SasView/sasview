#!/usr/bin/env python
""" 
    
    Provide F(x) = K*1/(4*pi()*Lb*(alpha)^(2)*(q^(2)+k2)/(1+(r02)^(2))*(q^(2)+k2)\
                       *(q^(2)-(12*h*C/b^(2)))
    BEPolyelectrolyte as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math

class BEPolyelectrolyte(BaseComponent):
   
    """
        Class that evaluates a BEPolyelectrolyte.
        
        F(x) = K*1/(4*pi()*Lb*(alpha)^(2)*(q^(2)+k2)/(1+(r02)^(2))*(q^(2)+k2)\
                       *(q^(2)-(12*h*C/b^(2)))
        
        The model has Eight parameters: 
            K        =  Constrast factor of the polymer
            Lb       =  Bjerrum length
            H        =  virial parameter
            B        =  monomer length
            Cs       =  Concentration of monovalent salt 
            alpha    =  ionazation degree 
            C        = polymer molar concentration
            bkd      = background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "BEPolyelectrolyte"

        ## Define parameters
        self.params = {}
        self.params['K']    = 10
        self.params['Lb']   = 7.1
        self.params['H']    = 12
        self.params['B']    = 10
        self.params['Cs']   = 0.0
        self.params['alpha']= 0.05
        self.params['C']    = 0.7
        self.params['bkd']  = 0.001
        

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['K']    = ['barns', None, None]
        self.details['Lb'] = ['A', None, None]
        self.details['H']   = ['A^{-3}', None, None]
        self.details['B']    = ['A', None, None]
        self.details['Cs'] = ['mol/L', None, None]
        self.details['alpha']   = ['', None, None]
        self.details['C']    = ['mol/L', None, None]
        self.details['bkd'] = ['', None, None]
       
               
    def _BEPoly(self, x):
        """
            Evaluate  
            F(x) = K*1/(4*pi()*Lb*(alpha)^(2)*(q^(2)+k2)/(1+(r02)^(2))*(q^(2)+k2)\
                       *(q^(2)-(12*h*C/b^(2)))
        
            has 3 internal parameters :
                   The inverse Debye Length: K2 = 4*pi*Lb*(2*Cs+alpha*C)
                   r02 =1/alpha/Ca^(0.5)*(B/(48*pi*Lb)^(0.5))
                   Ca = C*6.022136* exp(-4)
        """
        K2 = 4 * math.pi * self.params['Lb'] * (2*self.params['Cs'] + \
                 self.params['alpha'] * self.params['C'])
        
        Ca = self.params['C'] * 6.022136 * math.exp(-4)
        
        r02 =1/(self.params['alpha'] * math.pow(Ca,0.5) * \
                (self.params['B']/math.pow((48*math.pi *self.params['Lb']),0.5)))
        
        return ( self.params['K']/( ( 4 * math.pi *self.params['Lb']*\
                (self.params['alpha']**2)*\
                 ( x**2 + K2 )*( 1 + r02**2 ) * ( x**2 + K2 ) *\
                 (x**2 - ( 12 * self.params['H'] * \
                  self.params['C']/(self.params['B']**2) ))  )))+  self.params['bkd']
        
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (debye value)
        """
        if x.__class__.__name__ == 'list':
            return self._BEPoly(x[0]*math.cos(x[1]))*self._BEPoly(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._BEPoly(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: debye value
        """
        if x.__class__.__name__ == 'list':
            return self._BEPoly(x[0])*self._BEPoly(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._BEPolye(x)
