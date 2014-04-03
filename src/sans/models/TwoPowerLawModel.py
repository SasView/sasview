#!/usr/bin/env python
""" 
Provide I(q) = A*pow(qval,-1.0*m1) for q<=qc
    =scale*pow(qval,-1.0*m2) for q>qc
TwoPowerLaw function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
from numpy import power
import math

class TwoPowerLawModel(BaseComponent):
    """ 
    Class that evaluates a TwoPowerLawModel.

    I(q) = coef_A*pow(qval,-1.0*power1) for q<=qc
        =C*pow(qval,-1.0*power2) for q>qc
    where C=coef_A*pow(qc,-1.0*power1)/pow(qc,-1.0*power2).
    
    List of default parameters:
    
    * coef_A = coefficient
    * power1 = (-) Power @ low Q
    * power2 = (-) Power @ high Q
    * qc = crossover Q-value
    * background = incoherent background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "TwoPowerLaw"
        self.description="""I(q) = coef_A*pow(qval,-1.0*power1) for q<=qc
            =C*pow(qval,-1.0*power2) for q>qc
            where C=coef_A*pow(qc,-1.0*power1)/pow(qc,-1.0*power2).
             List of default parameters:
             coef_A = coefficient
             power1 = (-) Power @ low Q
             power2 = (-) Power @ high Q
             qc = crossover Q-value
             background = incoherent background
        """
        ## Define parameters
        self.params = {}
        self.params['coef_A']  = 1.0
        self.params['power1']     = 1.0
        self.params['power2']  = 4.0
        self.params['qc']     = 0.04
        self.params['background']     = 0.0
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['coef_A'] = ['', None, None]
        self.details['power1'] =  ['', None, None]
        self.details['power2']  =  ['', None, None]
        self.details['qc']  =   ['1/A', None, None]
        self.details['background']   =  ['[1/cm]', None, None]

        #list of parameter that cannot be fitted
        self.fixed= []  
    def _twopowerlaw(self, x):
        """
        Model definition
        """
        qc= self.params['qc']
        if(x<=qc):
            inten = self.params['coef_A']*power(x,-1.0*self.params['power1'])
        else:
            scale = self.params['coef_A']*power(qc,-1.0*self.params['power1']) \
                                    / power(qc,-1.0*self.params['power2'])
            inten = scale*power(x,-1.0*self.params['power2'])
        inten += self.params['background']

        return inten  
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (guinier value)
        """
        if x.__class__.__name__ == 'list':
            return self._twopowerlaw(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._twopowerlaw(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: guinier value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._twopowerlaw(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._twopowerlaw(x)
