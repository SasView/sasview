#!/usr/bin/env python
""" 
Provide Line function (y= A + Bx) 
"""

import math

class LineModel(object):
    """ 
    Class that evaluates a linear model.
    
    f(x) = A + Bx
     
    List of default parameters:
    A = 0.0
    B = 0.0 
    """
        
    def __init__(self):
        """ Initialization """
        ## Name of the model
        self.name = "LineModel"

        ## Define parameters
        self.params = {}
        self.params['A'] = 1.0
        self.params['B'] = 1.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['A'] = ['', None, None]
        self.details['B'] = ['', None, None]
               
    def getParam(self, name):
        """
        """
        return self.params[name.upper()]
    
    def setParam(self, name, value):
        """
        """
        self.params[name.upper()] = value
    
    def _line(self, x):
        """
        Evaluate the function
        
        :param x: x-value
        
        :return: function value
        
        """
        return  self.params['A'] + (x * self.params['B'])
    
    def run(self, x = 0.0):
        """ 
        Evaluate the model
        
        :param x: simple value
        
        :return: (Line value)
        """
        if x.__class__.__name__ == 'list':
            return self._line(x[0] * math.cos(x[1])) * \
                                self._line(x[0] * math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            msg  = "Tuples are not allowed as input to BaseComponent models"
            raise ValueError, msg
        else:
            return self._line(x)
   
    def runXY(self, x = 0.0):
        """ 
        Evaluate the model
            
        :param x: simple value
        
        :return: Line value
        
        """
        if x.__class__.__name__ == 'list':
            return self._line(x[0]) * self._line(x[1])
        elif x.__class__.__name__ == 'tuple':
            msg = "Tuples are not allowed as input to BaseComponent models"
            raise ValueError, msg
        else:
            return self._line(x)
   

if __name__ == "__main__": 
    l = Line()

