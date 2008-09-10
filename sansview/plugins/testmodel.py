"""
    Test plug-in model
"""
#try:
#    from DataPlugin import *
#except:
#    import sys, os
#    print os.path.abspath('..')
#    sys.path.insert(1,os.path.abspath('..'))
#    from DataPlugin import *
#    print "Running independently"
#
import math
from sans.models.BaseComponent import BaseComponent
import math
class Model1DPlugin(BaseComponent):
    ## Name of the model
    name = "Plugin Model"

    def __init__(self):
        """ Initialization """
        self.details = {}
        self.params  = {}
        
    def function(self, x):
        """
            Function to be implemented by the plug-in writer
        """
        return x
        
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input x, or [x, phi] [radian]
            @return: function value
        """
        if x.__class__.__name__ == 'list':
            x_val = x[0]*math.cos(x[1])
            y_val = x[0]*math.sin(x[1])
            return self.function(x_val)*self.function(y_val)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self.function(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input x, or [x, y] 
            @return: function value
        """
        if x.__class__.__name__ == 'list':
            return self.function(x[0])*self.function(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self.function(x)

# Your model HAS to be called Model
class Model(Model1DPlugin):
    """ Class that evaluates a cos(x) model. 
    """
    
    ## Name of the model
    name = "A+Bcos(2x)+Csin(2x)"
    
    def __init__(self):
        """ Initialization """
      
        
        ## Parameters definition and defaults
        self.params = {}
        self.params['A'] = 0.0
        self.params['B'] = 1.0
        self.params['C'] = 0.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['A'] = ['', -1e16, 1e16]
        self.details['B'] = ['', -1e16, 1e16]
        self.details['C'] = ['', -1e16, 1e16]
   
    def function(self, x = 0.0):
        """ Evaluate the model
            @param x: input x
            @return: function value
        """
        return self.params['A']+self.params['B']*math.cos(2.0*x)+self.params['C']*math.sin(2.0*x)
   