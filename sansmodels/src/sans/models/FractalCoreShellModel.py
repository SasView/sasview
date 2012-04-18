"""
    Fractal Core-Shell model
"""
from sans.models.BaseComponent import BaseComponent
from sans.models.CoreShellModel import CoreShellModel
from scipy.special import gammaln
import math
from numpy import power
from copy import deepcopy

class FractalCoreShellModel(BaseComponent):
    """
    Class that evaluates a FractalCoreShellModel
    List of default parameters:
    volfraction     = 0.05
    radius          = 20.0 [A]
    thickness       = 5.0 [A]
    frac_dim        = 2.0
    cor_length      = 100 [A]
    core_sld        = 3.5e-006 [1/A^(2)]
    shell_sld       = 1.0e-006 [1/A^(2)]
    solvent_sld     = 6.35e-006 [1/A^(2)]
    background      = 0.0 [1/cm]
    """
    def __init__(self):
        BaseComponent.__init__(self)

        ## Setting  model name model description
        model = CoreShellModel()
        self.description = model
        
        self.model = model
        self.name = "FractalCoreShell"
        self.description = """Scattering  from a fractal structure 
        with a primary building block of a spherical particle 
        with particle with a core-shell structure.
        Note: Setting the (core) radius polydispersion with a Schulz 
        distribution is equivalent to the FractalPolyCore function 
        in NIST/Igor Package.
        List of parameters:
        volfraction: volume fraction of building block spheres
        radius: radius of building block
        thickness: shell thickness
        frac_dim:  fractal dimension
        cor_length: correlation length of fractal-like aggregates
        core_sld: SLD of building block
        shell_sld: SLD of shell
        solvent_sld: SLD of matrix or solution
        background: flat background"""
        
        ## Define parameters
        self.params = {}

        ## Parameter details [units, min, max]
        self.details = {}
        
        # non-fittable parameters
        self.non_fittable = model.non_fittable
        
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        
        ## Parameter details [units, min, max]
        self._set_details()

        ## parameters with orientation:
        for item in self.model.orientation_params:
            self.orientation_params.append(item)
                
    def _fractalcore(self, x):
        """
        Define model function
        
        return S(q): Fractal Structure 
        """
        # set local variables
        Df = self.params['frac_dim']
        corr = self.params['cor_length']
        r0 = self.params['radius']
        #calculate S(q)
        sq = Df*math.exp(gammaln(Df-1.0))*math.sin((Df-1.0)*math.atan(x*corr))
        sq /= power((x*r0), Df) * power((1.0 + 1.0/(x*corr*x*corr)), ((Df-1)/2))
        sq += 1.0
        return sq

    def _clone(self, obj):
        """
        Internal utility function to copy the internal
        data members to a fresh copy.
        """
        obj.params     = deepcopy(self.params)
        obj.description     = deepcopy(self.description)
        obj.details    = deepcopy(self.details)
        obj.dispersion = deepcopy(self.dispersion)
        obj.model  = self.model.clone()

        return obj 
    
    def _set_dispersion(self):
        """
        model dispersions
        """ 
        ##set dispersion from model 
        for name , value in self.model.dispersion.iteritems():      
            self.dispersion[name] = value
                              
    def _set_params(self):
        """
        Concatenate the parameters of the model to create
        this model parameters 
        """
        # rearrange the parameters for the given # of shells
        for name , value in self.model.params.iteritems():
            if name == 'scale':
                value = 0.05   
            elif name == 'radius':
                value = 20.0
            elif name == 'thickness':
                value = 5.0
            elif name == 'core_sld':
                value = 3.5e-06
            elif name == 'shell_sld':
                value = 1.0e-06
            elif name == 'solvent_sld':
                value = 6.35e-06
            elif name == 'background':
                value = 0.0
            self.model.params[name] = value
            if name  == 'scale':
                name = 'volfraction'
            self.params[name] = value
        self.params['frac_dim'] = 2.0
        self.params['cor_length'] = 100.0  
  
    def _set_details(self):
        """
        Concatenate details of the original model to create
        this model details 
        """
        for name, detail in self.model.details.iteritems():
            if name in self.params.iterkeys():
                if name == 'scale':
                    name = 'volfraction'
                self.details[name] = detail
        self.details['frac_dim']   = ['', None, None]
        self.details['cor_length'] = ['[A]', None, None]  


    def setParam(self, name, value):
        """ 
        Set the value of a model parameter
    
        : param name: name of the parameter
        : param value: value of the parameter
        """
        # set param to new model
        self._setParamHelper(name, value)

        if name == 'volfraction':
            name = 'scale'
        # model.setParam except the two names below
        if name != 'frac_dim' and name != 'cor_length':
            # background is always 0.0 in the coreshellmodel
            if name == 'background':
                value = 0.0
            self.model.setParam(name, value)

    def _setParamHelper(self, name, value):
        """
        Helper function to setParam
        """
        #look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2:
            for item in self.dispersion.keys():
                if item.lower()==toks[0].lower():
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():
                            self.dispersion[item][par] = value
                            return
        # Look for standard parameter
        for item in self.params.keys():
            if item.lower()==name.lower():
                self.params[item] = value
                return
        
        raise ValueError, "Model does not contain parameter %s" % name
             
     
                
    def run(self, x = 0.0):
        """ 
        Evaluate the model
        
        : param x: input q-value (float or [float, float] as [r, theta])
        : return: (DAB value)
        """
        if x.__class__.__name__ == 'list':
            # Take absolute value of Q, since this model is really meant to
            # be defined in 1D for a given length of Q
            #qx = math.fabs(x[0]*math.cos(x[1]))
            #qy = math.fabs(x[0]*math.sin(x[1]))
            return self.params['background']\
                +self._fractalcore(x[0])*self.model.run(x)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self.params['background']\
                +self._fractalcore(x)*self.model.run(x)

        return self.params['background']+self._fractalcore(x)*self.model.run(x)

    def runXY(self, x = 0.0):
        """ 
        Evaluate the model
        
        : param x: input q-value (float or [float, float] as [qx, qy])
        : return: DAB value
        """  
        if x.__class__.__name__ == 'list':
            q = math.sqrt(x[0]**2 + x[1]**2)
            return self.params['background']\
                +self._fractalcore(q)*self.model.runXY(x)
        elif x.__class__.__name__ == 'tuple':
            raise ValueError, "Tuples are not allowed as input to models"
        else:
            return self.params['background']\
                +self._fractalcore(x)*self.model.runXY(x)

    def set_dispersion(self, parameter, dispersion):
        """
        Set the dispersion object for a model parameter
        
        : param parameter: name of the parameter [string]
        :dispersion: dispersion object of type DispersionModel
        """
        value = None
        try:
            if parameter in self.model.dispersion.keys():
                value = self.model.set_dispersion(parameter, dispersion)
            self._set_dispersion()
            return value
        except:
            raise 
