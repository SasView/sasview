#!/usr/bin/env python
""" Provide sin(x) function as a BaseComponent model
"""

from sas.models.BaseComponent import BaseComponent
import math
 
class Sin(BaseComponent):
    """ Class that evaluates a sin(x) model. 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Sin"
        self.description=""" the sin model
        F(x)=sin(x)
        """
        ## Parameter details [units, min, max]
        self.details = {}
        #list of parameter that cannot be fitted
        self.fixed= []
    def clone(self):
        """ Return a identical copy of self """
        return Sin()
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input x, or [x, phi] [radian]
            @return: sin(x) or sin(x*cos(phi))*sin(x*sin(phi))
        """
        if x.__class__.__name__ == 'list':
            return math.sin(x[0]*math.cos(x[1]))*math.sin(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return math.sin(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input x, or [x, y] [radian]
            @return: sin(x) or sin(x)*sin(y)
        """
        if x.__class__.__name__ == 'list':
            return math.sin(x[0])*math.sin(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return math.sin(x)
   
# End of file
