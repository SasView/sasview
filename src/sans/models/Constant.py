""" 
    Provide constant function as a BaseComponent model
"""

from sans.models.BaseComponent import BaseComponent
import copy

class Constant(BaseComponent):
    """
    Class that evaluates a constant model. 
    List of default parameters:
    
    * value           = 1.0 
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Constant"
        self.description = 'F(c)= c where c is a constant'
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['value'] = ['', None, None]
        self.params['value'] = 1.0
        #list of parameter that cannot be fitted
        self.fixed = []
    def clone(self):
        """ Return a identical copy of self """
        obj = Constant()
        obj.params = copy.deepcopy(self.params)
        return obj   
    
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: unused
            @return: (constant value)
        """
        return self.params['value']
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: unused
            @return: constant value
        """
        return self.params['value']
   
# End of file
