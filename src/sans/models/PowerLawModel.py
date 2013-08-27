""" 
    Provide F(x) = scale* (x)^(-m) + bkd
    Power law function as a BaseComponent model
"""
from sans.models.BaseComponent import BaseComponent
import math

class PowerLawModel(BaseComponent):
    """
        Class that evaluates a Power_Law model.
        
        F(x) = scale* (x)^(-m) + bkd
        
        The model has three parameters: 
            m     =  power
            scale  =  scale factor
            bkd    =  incoherent background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "Power_Law"

        ## Define parameters
        self.params = {}
        self.params['m']            = 4.0
        self.params['scale']        = 1.0
        self.params['background']   = 0.0
        self.description = """ The Power_Law model.
        F(x) = scale* (x)^(-m) + bkd
        
        The model has three parameters: 
        m     =  power
        scale  =  scale factor
        bkd    =  incoherent background"""
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['m']           = ['', 0,    None]
        self.details['scale']       = ['', None, None]
        self.details['background']  = ['[1/cm]', None, None]
        #list of parameter that cannot be fitted
        self.fixed = []    
    def _PowerLaw(self, x):
        """
            Evaluate  F(x) = scale* (x)^(-m) + bkd
            :param x: q-value
        """
        if self.params['m'] > 0 and x == 0:
            return 1e+32
        elif self.params['m'] == 0 and x == 0:
            return 1
        else:
            return self.params['scale']*math.pow(x, -1.0*self.params['m'])\
                + self.params['background']
       
    def run(self, x = 0.0):
        """ Evaluate the model
            :param x: input q-value (float or [float, float] as [r, theta])
            :return: (PowerLaw value)
        """
        if x.__class__.__name__ == 'list':
            # Take absolute value of Q, since this model is really meant to
            # be defined in 1D for a given length of Q
            #qx = math.fabs(x[0]*math.cos(x[1]))
            #qy = math.fabs(x[0]*math.sin(x[1]))
            return self._PowerLaw(math.fabs(x[0]))
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._PowerLaw(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: PowerLaw value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._PowerLaw(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._PowerLaw(x)
