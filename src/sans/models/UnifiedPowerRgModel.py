from sans.models.BaseComponent import BaseComponent
from math import exp, sqrt
from numpy import power
from scipy.special import erf
max_level_n = 7
class UnifiedPowerRgModel(BaseComponent):
    """
    This model is based on Exponential/Power-law fit method developed 
    by G. Beaucage
    """
    def __init__(self, multfactor=1):
        BaseComponent.__init__(self)
        """
        :param multfactor: number of levels in the model, 
            assumes 0<= level# <=5.
        """

        ## Setting  model name model description
        self.name = "UnifiedPowerRg"
        self.description = """
        Multiple Levels of Unified Exponential/Power-law Method.
        Up to Level 6 is provided.
        Note; the additional Level 0 is an inverse linear function, 
        i.e., y = scale/x + background.
        The Level N is defined as
        y = background + scale * Sum(1..N)[G_i*exp(-x^2*Rg_i^2/3)
        + B_i/x^(power_i)*(erf(x*Rg_i/sqrt(6))^(3*power_i))].
        Ref:
        G. Beaucage (1995).  J. Appl. Cryst., vol. 28, p717-728.
        G. Beaucage (1996).  J. Appl. Cryst., vol. 29, p134-146.
        """
        self.level_num = multfactor
        ## Define parameters
        self.params = {}

        ## Parameter details [units, min, max]
        self.details = {}
        
        # non-fittable parameters
        self.non_fittable = []

        # list of function in order of the function number 
        self.fun_list = self._get_func_list()
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        
        ## Parameter details [units, min, max]
        self._set_details()
        
        #list of parameter that can be fitted
        self._set_fixed_params()  
        
        ## functional multiplicity of the model
        self.multiplicity_info = [max_level_n, "Level No.:", [], []]
    
    def _unifiedpowerrg(self, x):
        """
        Scattering function
        
        :param x: q value(s)
        :return answer: output of the function
        """
        # common parameters for the model functions
        bkg = self.params['background'] 
        scale = self.params['scale']
        l_num = self.level_num
        # set default output
        answer = 0.0
        # Set constant on lebel zero (special case)
        if l_num == 0:
            answer = scale / x + bkg
            return answer
        # rearrange the parameters for the given label no.
        for ind in range(1, l_num+1):
            # get exp term
            exp_now = exp(-power(x*self.params['Rg%s'% ind], 2)/3.0)
            # get erf term
            erf_now = erf(x*self.params['Rg%s'% ind]/sqrt(6.0))
            # get power term
            pow_now = power((erf_now*erf_now*erf_now/x), 
                            self.params['power%s'% ind])
            # get next exp term only if it exists
            try:
                exp_next = exp(-power(x*self.params['Rg%s'% (ind+1)], 2)/3.0)
            except:
                exp_next = 1.0
            # get to the calculation
            answer += self.params['G%s'% ind]*exp_now + \
                            self.params['B%s'% ind] * exp_next * pow_now
        # take care of the singular point
        if x == 0.0:
            answer = 0.0
            for ind in range(1, l_num+1):
                answer += self.params['G%s'% ind]
        # get scaled
        answer *= scale
        # add background
        answer += bkg
        return answer
        
    def _set_dispersion(self):
        """
        model dispersions
        """ 
        ##set dispersion from model 
        self.dispersion = {}
                    

    def _set_params(self):
        """
        Concatenate the parameters of the model to create
        this model parameters 
        """
        # common parameters for the model functions
        self.params['background'] = 0.0
        self.params['scale'] = 1.0
        l_num = self.level_num
        # rearrange the parameters for the given label no.
        for ind in range(0, l_num+1):
            if ind == 0:
                continue
            # multiple factor for higher labels
            mult = 1.0
            mul_pow = 1.0
            if ind != l_num:
                mult = 10.0 * 4.0/3.0
                mul_pow = 2.0
            # Set reasonably define default values that consistent 
            # w/NIST for label #1
            self.params['G%s'% ind] = 0.3 * mult * pow(10, \
                            (l_num+1 - float('%s'% ind)))
            self.params['Rg%s'% ind] = 21.0 / mult * pow(10, \
                              (l_num - float('%s'% ind)))
            self.params['B%s'% ind] = 6e-03/mult * pow(10, \
                           -(l_num+1 - float('%s'% ind)))
            self.params['power%s'% ind] = 2.0 * mul_pow
            

    def _set_details(self):
        """
        Concatenate details of the original model to create
        this model details 
        """
        # common parameters for the model functions
        self.details['background'] = ['[1/cm]', None, None]
        self.details['scale'] = ['', None, None]
        # rearrange the parameters for the given label no.
        for ind in range(0, self.level_num+1):
            if ind == 0:
                continue
            self.details['G%s'% ind] = ['[1/(cm.sr)]', None, None]
            self.details['Rg%s'% ind] = ['[A]', None, None]
            self.details['B%s'% ind] = ['[1/(cm.sr)]', None, None]
            self.details['power%s'% ind] = ['', None, None]

    
    def _get_func_list(self):
        """
        Get the list of functions in each cases 
        """
        func_list = {}
        return func_list
        
    def getProfile(self):
        """
        Get SLD profile 
        
        : return: None, No SLD profile supporting for this model
        """
        return None
        
    def setParam(self, name, value):
        """ 
        Set the value of a model parameter
    
        : param name: name of the parameter
        : param value: value of the parameter
        """
        # set param to new model
        self._setParamHelper(name, value)

    def _setParamHelper(self, name, value):
        """
        Helper function to setParam
        """

        # Look for standard parameter
        for item in self.params.keys():
            if item.lower()==name.lower():
                self.params[item] = value
                return
        
        raise ValueError, "Model does not contain parameter %s" % name
             
   
    def _set_fixed_params(self):
        """
        Fill the self.fixed list with the model fixed list
        """
        pass         

                
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
            return self._unifiedpowerrg(x)
        elif x.__class__.__name__ == 'tuple':
            msg = "Tuples are not allowed as input to BaseComponent models"
            raise ValueError, msg
        else:
            return self._unifiedpowerrg(x)


        return self._unifiedpowerrg(x)

    def runXY(self, x = 0.0):
        """ 
        Evaluate the model
        
        : param x: input q-value (float or [float, float] as [qx, qy])
        : return: DAB value
        """  
        if x.__class__.__name__ == 'list':
            q = sqrt(x[0]**2 + x[1]**2)
            return self._unifiedpowerrg(x)
        elif x.__class__.__name__ == 'tuple':
            msg = "Tuples are not allowed as input to BaseComponent models"
            raise ValueError, msg
        else:
            return self._unifiedpowerrg(x)

    def calculate_ER(self):
        """
        """
        # Not implemented!!!
        pass
    
    def set_dispersion(self, parameter, dispersion):
        """
        Set the dispersion object for a model parameter
        
        : param parameter: name of the parameter [string]
        :dispersion: dispersion object of type DispersionModel
        """
        pass
