"""
    Test plug-in model
"""
try:
    from DataPlugin import *
except:
    import sys, os
    print os.path.abspath('..')
    sys.path.insert(1,os.path.abspath('..'))
    from DataPlugin import *
    print "Running independently"

import math

# Your model HAS to be called Model
class Model(Model1DPlugin):
    """ Class that evaluates a cos(x) model. 
    """
    
    ## Name of the model
    name = "A+Bcos(2x)+Csin(2x)"
    
    def __init__(self):
        """ Initialization """
        
        Model1DPlugin.__init__(self)
        
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
   