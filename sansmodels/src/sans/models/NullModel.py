#!/usr/bin/env python
""" Provide sin(x) function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import math
 
class NullModel(BaseComponent):
    """ Class that evaluates a sin(x) model. 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Error!"
        self.description="""Error  model
        F(x)= 0
        """
       
    def clone(self):
        """ Return a identical copy of self """
        return self._clone(NullModel())   
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input x
            @return: 1
        """
        if x.__class__.__name__ == 'list':
            return 0
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return 0
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input x, or [x, y] [radian]
            @return: sin(x) or sin(x)*sin(y)
        """
        if x.__class__.__name__ == 'list':
            return 0
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return 0
   
# End of file
