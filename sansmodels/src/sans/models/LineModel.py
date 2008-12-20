#!/usr/bin/env python
""" 
    Provide Line function (y= A + Bx) as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math


class LineModel(BaseComponent):
    """ 
        Class that evaluates a linear model.
        
        f(x) = A + Bx
         
        List of default parameters:
          A = 1.0
          B = 1.0 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "LineModel"

        ## Define parameters
        self.params = {}
        self.params['A'] = 1.0
        self.params['B'] = 1.0
        self.description='f(x) = A + Bx'
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['A'] = ['', None, None]
        self.details['B'] = ['', None, None]
        # fixed paramaters
        self.fixed=[]
    def _line(self, x):
        """
            Evaluate the function
            @param x: x-value
            @return: function value
        """
        return  self.params['A'] + x *self.params['B']
    
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: (Line value)
        """
        if x.__class__.__name__ == 'list':
            return self._line(x[0]*math.cos(x[1]))*self._line(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._line(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: simple value
            @return: Line value
        """
        if x.__class__.__name__ == 'list':
            return self._line(x[0])*self._line(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._line(x)
   

if __name__ == "__main__": 
    l = Line()
    print "hello"
       
# End of file
