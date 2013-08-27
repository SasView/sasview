""" 
    Provide cos(x) function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math
 
class Cos(BaseComponent):
    """ 
        Class that evaluates a cos(x) model. 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Cos"
        self.description = 'F(x)=cos(x)'
        ## Parameter details [units, min, max]
        self.details = {}
   
    def clone(self):
        """ Return a identical copy of self """
        return Cos()
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input x, or [x, phi] [radian]
            @return: cos(x) or cos(x*cos(phi))*cos(x*cos(phi))
        """
        if x.__class__.__name__ == 'list':
            return math.cos(x[0]*math.cos(x[1]))*math.cos(x[0]*math.sin(x[1]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return math.cos(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input x, or [x, y] [radian]
            @return: cos(x) or cos(x)*cos(y)
        """
        if x.__class__.__name__ == 'list':
            return math.cos(x[0])*math.cos(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return math.cos(x)

