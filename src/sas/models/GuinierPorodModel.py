""" 
    I(q) = scale/q^s* exp ( - R_g^2 q^2 / (3-s) ) for q<= ql
        = scale/q^m*exp((-ql^2*Rg^2)/(3-s))*ql^(m-s) for q>=ql
    Guinier function as a BaseComponent model
"""
from sas.models.BaseComponent import BaseComponent
from math import sqrt,exp

class GuinierPorodModel(BaseComponent):
    """ 
    Class that evaluates a GuinierPorod model.

    I(q) = scale/q^s* exp ( - R_g^2 q^2 / (3-s) ) for q<= ql
        = scale/q^m*exp((-ql^2*Rg^2)/(3-s))*ql^(m-s) for q>=ql
    """
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "GuinierPorod"
        self.description = """
         I(q) = scale/q^s* exp ( - R_g^2 q^2 / (3-s) ) for q<= ql
         = scale/q^m*exp((-ql^2*Rg^2)/(3-s))*ql^(m-s) for q>=ql
                        where ql = sqrt((m-s)(3-s)/2)/Rg.
                        List of parameters:
                        scale = Guinier Scale
                        s = Dimension Variable
                        Rg = Radius of Gyration [A] 
                        m = Porod Exponent
                        background  = Background [1/cm]"""
        ## Define parameters
        self.params = {}
        self.params['scale']  = 1.0
        self.params['dim']  = 1.0
        self.params['rg']     = 100.0
        self.params['m']     = 3.0
        self.params['background']     = 0.1
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale'] = ['', None, None]
        self.details['dim']  = ['', None, None]
        self.details['rg']    = ['[A]', None, None]
        self.details['m']     = ['', None, None]
        self.details['background']     = ['[1/cm]', None, None]

        #list of parameter that cannot be fitted
        self.fixed = []  
        
    def _guinier_porod(self, x):
        """
        Guinier-Porod Model
        """
        # parameters
        G = self.params['scale']
        s = self.params['dim']
        Rg = self.params['rg']
        m = self.params['m']
        bgd = self.params['background']
        n = 3.0 - s
        qval = x
        # take care of the singular points
        if Rg <= 0.0:
            return bgd
        if (n-3.0+m) <= 0.0:
            return bgd
        #do the calculation and return the function value
        q1 = sqrt((n-3.0+m)*n/2.0)/Rg
        if qval < q1:
            F = (G/pow(qval,(3.0-n)))*exp((-qval*qval*Rg*Rg)/n) 
        else:
            F = (G/pow(qval, m))*exp(-(n-3.0+m)/2.0)*pow(((n-3.0+m)*n/2.0),
                                        ((n-3.0+m)/2.0))/pow(Rg,(n-3.0+m))
        inten = F + bgd
    
        return inten
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (guinier value)
        """
        if x.__class__.__name__ == 'list':
            return self._guinier_porod(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._guinier_porod(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: guinier value
        """
        if x.__class__.__name__ == 'list':
            q = sqrt(x[0]**2 + x[1]**2)
            return self._guinier_porod(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self._guinier_porod(x)
