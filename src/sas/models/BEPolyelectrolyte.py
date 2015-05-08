"""
 BEPolyelectrolyte as a BaseComponent model
"""

from sas.models.BaseComponent import BaseComponent
import math

class BEPolyelectrolyte(BaseComponent):
    """
        Class that evaluates a BEPolyelectrolyte.
        
        F(x) = K/(4 pi Lb (alpha)^(2)) (q^(2)+k2)/(1+(r02)^(2)) (q^(2)+k2)\
                        (q^(2)-(12 h C/b^(2)))
        
        The model has Eight parameters::

            K        = Constrast factor of the polymer
            Lb       = Bjerrum length
            H        = virial parameter
            B        = monomer length
            Cs       = Concentration of monovalent salt
            alpha    = ionazation degree
            C        = polymer molar concentration
            bkd      = background
    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "BEPolyelectrolyte"
        self.description = """
        F(x) = K*1/(4*pi*Lb*(alpha)^(2))*(q^(2)+k^(2))/(1+(r02)^(2))
            *(q^(2)+k^(2))*(q^(2)-(12*h*C/b^(2)))+bkd
                
        The model has Eight parameters: 
        K        =  Constrast factor of the polymer
        Lb       =  Bjerrum length
        H        =  virial parameter
        B        =  monomer length
        Cs       =  Concentration of monovalent salt 
        alpha    =  ionazation degree 
        C        = polymer molar concentration
        bkd      = background
        """
        ## Define parameters
        self.params = {}
        self.params['k']     = 10
        self.params['lb']    = 7.1
        self.params['h']     = 12
        self.params['b']     = 10
        self.params['cs']    = 0.0
        self.params['alpha'] = 0.05
        self.params['c']     = 0.7
        self.params['background']  = 0.0

        ## Parameter details [units, min, max]
        self.details = {}
        self.details['k']     = ['[barns]', None, None]
        self.details['lb']    = ['[A]', None, None]
        self.details['h']     = ['[1/A^(2)]', None, None]
        self.details['b']     = ['[A]', None, None]
        self.details['cs']    = ['[mol/L]', None, None]
        self.details['alpha'] = ['', None, None]
        self.details['c']     = ['[mol/L]', None, None]
        self.details['background'] = ['[1/cm]', None, None]
        #list of parameter that cannot be fitted
        self.fixed = []
               
    def _BEPoly(self, x):
        """
            Evaluate  
            F(x) = K 1/(4 pi Lb (alpha)^(2)) (q^(2)+k2)/(1+(r02)^(2))
                 (q^(2)+k2) (q^(2)-(12 h C/b^(2)))
        
            has 3 internal parameters :
                   The inverse Debye Length: K2 = 4 pi Lb (2 Cs+alpha C)
                   r02 =1/alpha/Ca^(0.5) (B/(48 pi Lb)^(0.5))
                   Ca = 6.022136e-4 C
        """
        Ca = self.params['c'] * 6.022136e-4
        #remove singulars
        if self.params['alpha']<=0 or self.params['c']<=0\
            or self.params['b']==0 or self.params['lb']<=0:
            return 0
        else:
            
            K2 = 4.0 * math.pi * self.params['lb'] * (2*self.params['cs'] + \
                     self.params['alpha'] * Ca)
            
            r02 = 1.0/self.params['alpha']/math.sqrt(Ca) * \
                    (self.params['b']/\
                     math.sqrt((48.0*math.pi*self.params['lb'])))
            
            return self.params['k']/( 4.0 * math.pi * self.params['lb'] \
                                      * self.params['alpha']**2 ) \
                   * ( x**2 + K2 ) / ( 1.0 + r02**2 * ( x**2 + K2 ) \
                        * (x**2 - ( 12.0 * self.params['h'] \
                        * Ca/(self.params['b']**2) ))) \
                        + self.params['background']
   
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (debye value)
        """
        if x.__class__.__name__ == 'list':
            return self._BEPoly(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._BEPoly(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: debye value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._BEPoly(q)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._BEPoly(x)
