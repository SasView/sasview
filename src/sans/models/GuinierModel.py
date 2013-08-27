""" 
    Provide I(q) = I_0 exp ( - R_g^2 q^2 / 3.0)
    Guinier function as a BaseComponent model
"""
from sans.models.BaseComponent import BaseComponent
import math

class GuinierModel(BaseComponent):
    """ 
        Class that evaluates a Guinier model.
    
        I(q) = I_0 exp ( - R_g^2 q^2 / 3.0 )
        
        List of default parameters:
         I_0 = Scale
         R_g = Radius of gyration
          
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Guinier"
        self.description = """ I(q) = I_0 exp ( - R_g^2 q^2 / 3.0 )
        
                        List of default parameters:
                        I_0 = Scale
                        R_g = Radius of gyration"""
        ## Define parameters
        self.params = {}
        self.params['scale']  = 1.0
        self.params['rg']     = 60

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale'] = ['[1/cm]', None, None]
        self.details['rg']    = ['[A]', None, None]
        #list of parameter that cannot be fitted
        self.fixed = []  
        
    def _guinier(self, x):
        """
            Evaluate guinier function
            :param x: q-value
        """
        return self.params['scale']*math.exp( -(self.params['rg']*x)**2/3.0 )  
   
    def run(self, x = 0.0):
        """ 
            Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (guinier value)
        """
        if x.__class__.__name__ == 'list':
            return self._guinier(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._guinier(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: guinier value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._guinier(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._guinier(x)
