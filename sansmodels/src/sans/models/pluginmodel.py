from sans.models.BaseModel import BaseModel
import math

class Model1DPlugin(BaseModel):
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