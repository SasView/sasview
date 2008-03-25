#!/usr/bin/env python
""" 
    Failed attempt at a Beaucage model.
"""
#TODO: Clean this up
#TODO: Remove setValueParam, which doesn't belong in this class!
#      It totally breaks the philosophy of this class

from sans.models.BaseComponent import BaseComponent
import math
import matplotlib
from scipy.special import erf
class UnifiedPowerLawModel(BaseComponent):
   
    """
        Class that evaluates a Unified Power_Law model.
    
        F(x) =  bkd + sum(G[i]*exp(-x**2 *Rg[i]**2 /3)) \
          + [B[i]( erf(x*Rg[i]/math.sqrt(6)))** (3*p[i])]/x**p[i] )
        
        For each level four parameters must be chosen
        The model has 5 parameters: 
           Gi  = ?
           Rgi = Guinier Radius
           Pi  = power for each level
           Bi  = ?
        Four Levels can be used
            i is each level 
           
    """
   
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = " UnifiedPowerLaw " 
        # default Number of levels 

        self.LevelTotal =2

        ## Define parameters
        self.params = {}
        
        for i in xrange(self.LevelTotal):
            self.params['G'+ str(i+1)]= 0.0
            self.params['B'+ str(i+1)]= 0.0
            self.params['Rg'+ str(i+1)]= 0.0
            self.params['P'+ str(i+1)]= 0.0
            
        ## input Variables with default values for two levels
        
        self.params['G1']     = 400.0
        self.params['G2']     = 3.0
        
        self.params['B1']     = 5 * math.exp(-6)
        self.params['B2']     = 0.0006
        
        self.params['Rg1']    = 200.0
        self.params['Rg2']    = 100.0
        
        self.params['P1']    = 4.0
        self.params['P2']    = 2.0
        
        self.params['bkd']    = 0.0
        
        

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['G1']    = ['cm^{-1} sr^{-1}', None, None ]
        self.details['G2']    = ['cm^{-1} sr^{-1}', None, None ]
        self.details['B1']    = ['cm^{-1} sr^{-1}', None, None ]
        self.details['B2']    = ['cm^{-1} sr^{-1}', None, None ]
        self.details['Rg1']   = ['A', None, None ]
        self.details['Rg2']   = ['A', None, None ]
        self.details['P1']    = ['', None, None ]
        self.details['P2']    = ['', None, None ]
        self.details['bkd']   = ['cm^{-1} sr^{-1}', None, None]

    def getValue(self, paramType,level):
        
        return self.getParam(str(paramType)+str(level))
    
    def setValueParam(self,level,Bvalue,Rgvalue,Gvalue,Pvalue):
        """
            set value of parameter given a level
        """
        self.params['G'+str(level)] = Gvalue
        self.params['B'+str(level)] = Bvalue
        self.params['Rg'+str(level)]= Rgvalue
        self.params['P'+str(level)] = Pvalue
        # set the number total of level for the sum
        if self.LevelTotal < level:
            self.LevelTotal = level
            
        # set parameter details
        self.details['G'+str(level)]   = ['cm^{-1} sr^{-1}', None, None ]
        self.details['B'+str(level)]   = ['cm^{-1} sr^{-1}', None, None ]
        self.details['Rg'+str(level)]  = ['A', None, None ]
        self.details['P'+str(level)]   = ['', None, None ]
 

    def _Sum(self,x):
        """
            Calculate the sum of Gi*exp(-x^(2)*Rgi^(2)/3)
        """
        sum =0
        # the default level is 2 and we are using the default values
        if (self.LevelTotal <= 2)and (self.LevelTotal > 1):
            return self.params['G1']*math.exp(-(x**2)* (self.params['Rg1']**2)/3)+\
                self.params['G2']*math.exp(-(x**2)* (self.params['Rg2']**2)/3)
        # For level higher than 2 
        else: 
            for i in xrange(self.LevelTotal):
                sum =sum +self.params['G'+str(i+1)]*math.exp(-(x**2)* (self.params['Rg'+str(i+1)]**2)/3)
            return sum 
                
 
    def _UnifiedPow(self,level,x ):
        """
            Calculates the values of the Unified Power Law function
            @param level: user should enters the level of computation else level =2 
                will be used
            @param x: a number
        """
       
        return self.params['bkd']+self._Sum(x)+ (self.params['B'+str(level)]*\
             math.pow(erf(x * self.params['Rg'+str(level)]/math.sqrt(6))\
            ,3 * self.params['P'+str(level)]))/math.pow(x,self.params['P'+str(level)])
       
    def run(self, level,x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @param level : level of computation
            @return: (Unified Power law value)
        """
        if x.__class__.__name__ == 'list':
            return self._UnifiedPow(level, x[0]*math.cos(x[1]))*\
                self.__UnifiedPow(level, x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._UnifiedPow(level,x)
   
    def runXY(self,level, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @param level : level of computation
            @return: Unified Power law value
        """
        if x.__class__.__name__ == 'list':
            return self._UnifiedPow(level, x[0])*self._UnifiedPow(level,x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._UnifiedPow(level, x)
