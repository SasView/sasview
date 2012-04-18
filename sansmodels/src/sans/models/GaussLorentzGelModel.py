""" 
    Provide I(q) = I_0 exp ( - R_g^2 q^2 / 3.0)
    GaussLorentzGel function as a BaseComponent model
"""
from sans.models.BaseComponent import BaseComponent
import math

class GaussLorentzGelModel(BaseComponent):
    """ 
    Class that evaluates a GaussLorentzGel model.

    I(q) = scale_g*exp(- q^2*Z^2 / 2)+scale_l/(1+q^2*z^2)
            + background
    List of default parameters:
     scale_g = Gauss scale factor
     Z = Static correlation length
     scale_l = Lorentzian scale factor
     z = Dynamic correlation length
     background = Incoherent background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "GaussLorentzGel"
        self.description = """I(q)=scale_g*exp(-q^2*Z^2/2)+scale_l/(1+q^2*z^2)
            + background
            List of default parameters:
             scale_g = Gauss scale factor
             stat_colength = Static correlation length
             scale_l = Lorentzian scale factor
             dyn_colength = Dynamic correlation length
             background = Incoherent background
"""
        ## Define parameters
        self.params = {}
        self.params['scale_g']  = 100.0
        self.params['stat_colength']     = 100.0
        self.params['scale_l']  = 50.0
        self.params['dyn_colength']     = 20.0
        self.params['background']     = 0.0
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale_g'] = ['', None, None]
        self.details['stat_colength'] =  ['A', None, None]
        self.details['scale_l']  =  ['', None, None]
        self.details['dyn_colength']  =   ['A', None, None]
        self.details['background']   =  ['[1/cm]', None, None]

        #list of parameter that cannot be fitted
        self.fixed = []  
        
    def _gausslorentzgel(self, x):
        """
        Model definition
        """
        inten = self.params['scale_g'] \
                *math.exp(-1.0*x*x*self.params['stat_colength']* \
                self.params['stat_colength']/2.0) + self.params['scale_l']/ \
                (1.0 + (x*self.params['dyn_colength'])* \
                 (x*self.params['dyn_colength'])) + self.params['background']
        return inten  
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (guinier value)
        """
        if x.__class__.__name__ == 'list':
            return self._gausslorentzgel(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._gausslorentzgel(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: guinier value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._gausslorentzgel(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._gausslorentzgel(x)
