from sas.sascalc.calculator.BaseComponent import BaseComponent
import math

class Model1DPlugin(BaseComponent):
    is_multiplicity_model = False

    ## Name of the model

    def __init__(self , name="Plugin Model" ):
        """ Initialization """
        BaseComponent.__init__(self)
        self.name = name
        self.details = {}
        self.params  = {}
        self.description = 'plugin model'

    def function(self, x):
        """
        Function to be implemented by the plug-in writer
        """
        return x

    def run(self, x = 0.0):
        """
        Evaluate the model

        :param x: input x, or [x, phi] [radian]

        :return: function value

        """
        if x.__class__.__name__ == 'list':
            x_val = x[0]*math.cos(x[1])
            y_val = x[0]*math.sin(x[1])
            return self.function(x_val)*self.function(y_val)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError("Tuples are not allowed as input to BaseComponent models")
        else:
            return self.function(x)


    def runXY(self, x = 0.0):
        """
        Evaluate the model

        :param x: input x, or [x, y]

        :return: function value

        """
        if x.__class__.__name__ == 'list':
            return self.function(x[0])*self.function(x[1])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError("Tuples are not allowed as input to BaseComponent models")
        else:
            return self.function(x)

    def set_details(self):
        """
        Set default details
        """
        if not self.params:
            return {}

        for key in self.params.keys():
            self.details[key] = ['', None, None]