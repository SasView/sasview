   
from sans.models.BaseComponent import BaseComponent
from sans.models.RPAModel import RPAModel
from copy import deepcopy
max_case_n = 10
class RPA10Model(BaseComponent):
    """
    This multi-model is based on Parratt formalism and provides the capability
    of changing the number of layers between 0 and 10.
    """
    def __init__(self, multfactor=1):
        BaseComponent.__init__(self)
        """
        :param multfactor: number of cases in the model, assumes 0<= case# <=10.
        """

        ## Setting  model name model description
        self.description=""
        model = RPAModel()
        self.model = model
        self.name = "RPA10Model"
        self.description=model.description
        self.case_num = multfactor
        ## Define parameters
        self.params = {}

        ## Parameter details [units, min, max]
        self.details = {}
        
        # non-fittable parameters
        self.non_fittable = model.non_fittable

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
        self.model.params['lcase_n'] = self.case_num
        
        ## functional multiplicity of the model
        self.multiplicity_info = [max_case_n,"Case No.:",["C/D Binary Mixture of Homopolymers",
                                                         "C-D Diblock Copolymer",
                                                         "B/C/D Ternary Mixture of Homopolymers",
                                                         "B/C-D Mixture of Homopolymer B and Diblock Copolymer C-D",
                                                         "B-C-D Triblock Copolymer",
                                                         "A/B/C/D Quaternary Mixture of Homopolymers",
                                                         "A/B/C-D Mixture of Homopolymer A/B and Diblock C-D",
                                                         "A/B-C-D Mixture of Homopolymer A and triblock B-C-D",
                                                         "A-B/C-D Mixture of Diblock Copolymer A-B and Diblock C-D",
                                                         "A-B-C-D Four-block Copolymer"],
                                                         []]
    
    def _clone(self, obj):
        """
        Internal utility function to copy the internal
        data members to a fresh copy.
        """
        obj.params     = deepcopy(self.params)
        obj.non_fittable     = deepcopy(self.non_fittable)
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
        self.dispersion = {}
                    

    def _set_params(self):
        """
        Concatenate the parameters of the model to create
        this model parameters 
        """
        # set the case number first
        self.model.params['lcase_n'] = self.case_num  
        # rearrange the parameters for the given # of shells
        for name , value in self.model.params.iteritems():
            if name == 'lcase_n':
                continue
            elif name.lower() == 'scale' or \
                        name.lower() == 'background':
                    self.params[name] = value
            elif self.case_num <= 1:
                if name.lower() == 'nc' or \
                        name.lower() == 'phic' or \
                        name.lower() == 'vc' or \
                        name.lower() == 'lc' or \
                        name.lower() == 'bc' or \
                        name.lower() == 'nd' or \
                        name.lower() == 'phid' or \
                        name.lower() == 'vd' or \
                        name.lower() == 'ld' or \
                        name.lower() == 'bd' or \
                        name.lower() == 'kcd':
                    self.params[name] = value
            elif self.case_num > 1 and self.case_num <= 4:
                if name.lower() == 'nb' or \
                        name.lower() == 'phib' or \
                        name.lower() == 'vb' or \
                        name.lower() == 'lb' or \
                        name.lower() == 'bb' or \
                        name.lower() == 'nc' or \
                        name.lower() == 'phic' or \
                        name.lower() == 'vc' or \
                        name.lower() == 'lc' or \
                        name.lower() == 'bc' or \
                        name.lower() == 'nd' or \
                        name.lower() == 'phid' or \
                        name.lower() == 'vd' or \
                        name.lower() == 'ld' or \
                        name.lower() == 'bd' or \
                        name.lower() == 'kbc' or \
                        name.lower() == 'kbd' or \
                        name.lower() == 'kcd' :
                    self.params[name] = value
            else:
                if name.lower() == 'na' or \
                        name.lower() == 'phia' or \
                        name.lower() == 'va' or \
                        name.lower() == 'la' or \
                        name.lower() == 'ba' or \
                        name.lower() == 'nb' or \
                        name.lower() == 'phib' or \
                        name.lower() == 'vb' or \
                        name.lower() == 'lb' or \
                        name.lower() == 'bb' or \
                        name.lower() == 'nc' or \
                        name.lower() == 'phic' or \
                        name.lower() == 'vc' or \
                        name.lower() == 'lc' or \
                        name.lower() == 'bc' or \
                        name.lower() == 'nd' or \
                        name.lower() == 'phid' or \
                        name.lower() == 'vd' or \
                        name.lower() == 'ld' or \
                        name.lower() == 'bd' or \
                        name.lower() == 'kab' or \
                        name.lower() == 'kac' or \
                        name.lower() == 'kad' or \
                        name.lower() == 'kbc' or \
                        name.lower() == 'kbd' or \
                        name.lower() == 'kcd' :
                    self.params[name] = value
            
          

    def _set_details(self):
        """
        Concatenate details of the original model to create
        this model details 
        """
        for name ,detail in self.model.details.iteritems():
            if name in self.params.iterkeys():
                self.details[name]= detail
    
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
        self._setParamHelper( name, value)
            
        self.model.setParam( name, value)

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
        
        :param x: input q, or [q,phi]
        
        :return: scattering function P(q)
        
        """

        return self.model.run(x)

    def runXY(self, x = 0.0):
        """ 
        Evaluate the model
        
        : param x: input q-value (float or [float, float] as [qx, qy])
        : return: scattering function value
        """  

        return self.model.runXY(x)
    
    ## Now (May27,10) directly uses the model eval function 
    ## instead of the for-loop in Base Component.
    def evalDistribution(self, x = []):
        """ 
        Evaluate the model in cartesian coordinates
        
        : param x: input q[], or [qx[], qy[]]
        : return: scattering function P(q[])
        """
        # set effective radius and scaling factor before run
        return self.model.evalDistribution(x)
    def calculate_ER(self):
        """
        """
        return self.model.calculate_ER()
    def set_dispersion(self, parameter, dispersion):
        """
        Set the dispersion object for a model parameter
        
        : param parameter: name of the parameter [string]
        :dispersion: dispersion object of type DispersionModel
        """
        pass
