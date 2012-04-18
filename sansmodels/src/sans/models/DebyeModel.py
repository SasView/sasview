""" 
    Provide F(x) = 2( exp(-x) + x - 1 )/x**2
    with x = (q*R_g)**2
    
    Debye function as a BaseComponent model
"""
from sans.models.BaseComponent import BaseComponent
import math

class DebyeModel(BaseComponent):
    """
        Class that evaluates a Debye model.
        
        F(x) = 2( exp(-x) + x - 1 )/x**2
        with x = (q*R_g)**2
        
        The model has three parameters: 
            Rg     =  radius of gyration
            scale  =  scale factor
            bkd    =  Constant background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Debye"
        self.description = """ 
        F(x) = 2( exp(-x) + x - 1 )/x**2
        with x = (q*R_g)**2
        
        The model has three parameters: 
        Rg     =  radius of gyration
        scale  =  scale factor
        bkd    =  Constant background
        """
        ## Define parameters
        self.params = {}
        self.params['rg']          = 50.0
        self.params['scale']       = 1.0
        self.params['background']  = 0.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['rg']         = ['[A]', None, None]
        self.details['scale']      = ['', None, None]
        self.details['background'] = ['[1/cm]', None, None]
        #list of parameter that cannot be fitted
        self.fixed = [] 
             
    def _debye(self, x):
        """
            Evaluate F(x)= scale * D + bkd
            has 2 internal parameters :
                    D = 2 * (exp(-y) + y - 1)/y**2 
                    y = (x * Rg)^(2)
        """
        # Note that a zero denominator value will raise
        # an exception
        y = (x * self.params['rg'])**2.0
        if x == 0:
            D = 1
        else:
            D = 2.0*( math.exp(-y) + y -1.0 )/y**2.0
        return self.params['scale'] * D + self.params['background']
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (debye value)
        """
        if x.__class__.__name__ == 'list':
            return self._debye(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._debye(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: debye value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._debye(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._debye(x)
