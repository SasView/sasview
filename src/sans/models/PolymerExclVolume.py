#!/usr/bin/env python

##############################################################################
#	This software was developed by the University of Tennessee as part of the
#	Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#	project funded by the US National Science Foundation.
#
#	If you use DANSE applications to do scientific research that leads to
#	publication, we ask that you acknowledge the use of the software with the
#	following sentence:
#
#	"This work benefited from DANSE software developed under NSF award DMR-0520547."
#
#	copyright 2008, University of Tennessee
##############################################################################
from sans.models.BaseComponent import BaseComponent
from scipy.special import gammainc,gamma
import copy    
import math
    
class PolymerExclVolume(BaseComponent):
    """ 
    Class that evaluates a PolymerExclVolModel model. 
    This file was auto-generated from ..\c_extensions\polyexclvol.h.
    Refer to that file and the structure it contains
    for details of the model.

    List of default parameters:
    
    * scale           = 0.01 
    * rg              = 100.0 [A]
    * m               = 3.0 
    * background      = 0.0 [1/cm]

    """
        
    def __init__(self):
        """ Initialization """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        
        ## Name of the model
        self.name = "PolymerExclVolume"
        ## Model description
        self.description =""" Compute the scattering intensity from polymers with excluded volume effects.
		scale: scale factor times volume fraction,
		or just volume fraction for absolute scale data
		rg: radius of gyration
		m = Porod exponent
		background: incoherent background
		"""
        ## Define parameters
        self.params = {}
        self.params['scale']        = 1.0
        self.params['rg']           = 60.0
        self.params['m']            = 3.0
        self.params['background']   = 0.0

       
        ## Parameter details [units, min, max]
        self.details = {}
        self.details['scale'] = ['', None, None]
        self.details['rg'] = ['[A]', None, None]
        self.details['m'] = ['', None, None]
        self.details['background'] = ['[1/cm]', None, None]

        ## fittable parameters
        self.fixed=[]
        
        ## non-fittable parameters
        self.non_fittable=[]
        
        ## parameters with orientation
        self.orientation_params =[]
        
    def _polymerexclvol(self, x):
        
        sc = self.params['scale']
        rg = self.params['rg']
        mm  = self.params['m']
        bg = self.params['background']
    
        nu = 1.0 / mm
    
        Xx = x * x * rg * rg *(2.0 * nu + 1.0) * (2.0 * nu + 2.0) / 6.0
        onu = 1.0 / nu
        o2nu = 1.0 /(2.0 * nu)
        Ps =(1.0 / (nu * pow(Xx,o2nu))) * (gamma(o2nu)*gammainc(o2nu,Xx) - \
                        1.0 / pow(Xx,o2nu) * gamma(onu)*gammainc(onu,Xx))

        if x == 0:
            Ps = 1.0

        return (sc * Ps + bg);

    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (guinier value)
        """
        if x.__class__.__name__ == 'list':
            return self._polymerexclvol(x[0])
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._polymerexclvol(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: guinier value
        """
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self._polymerexclvol(x)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to BaseComponent models"
        else:
            return self._polymerexclvol(x)
        

   
# End of file
