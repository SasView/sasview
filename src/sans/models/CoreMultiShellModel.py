"""
    Core-Multi-Shell model
"""
from sans.models.BaseComponent import BaseComponent
from sans.models.CoreFourShellModel import CoreFourShellModel
import copy
max_nshells = 5
class CoreMultiShellModel(BaseComponent):
    """
    This multi-model is based on CoreFourShellModel and provides the capability
    of changing the number of shells between 1 and 4.
    """
    def __init__(self, multfactor=1):
        BaseComponent.__init__(self)
        """
        :param n_shells: number of shells in the model, assumes 1<= n_shells <=4.
        """

        ## Setting  model name model description
        self.description=""
        model = CoreFourShellModel()
        self.model = model
        self.name = "CoreMultiShellModel"
        self.description=""
        self.n_shells = multfactor
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
        
        #list of parameter that can be fitted
        self._set_fixed_params()  
        self.orientation_params = []
        self.magnetic_params = []
        
        ## functional multiplicity info of the model
        # [int(maximum no. of functionality),"str(Titl),
        # [str(name of function0),...], [str(x-asix name of sld),...]]
        self.multiplicity_info = [max_nshells, "No. of Shells:", [], ['Radius']]

        ## parameters with orientation: can be removed since there is no orientational params
        self._set_orientation_params()
                
        
    def _clone(self, obj):
        """
        Internal utility function to copy the internal
        data members to a fresh copy.
        """
        obj.params = copy.deepcopy(self.params)
        obj.description = copy.deepcopy(self.description)
        obj.details = copy.deepcopy(self.details)
        obj.dispersion = copy.deepcopy(self.dispersion)
        obj.model = self.model.clone()

        return obj
    
    
    def _set_dispersion(self):
        """
        model dispersions
        Polydispersion should not be applied to s_model
        """ 
        ##set dispersion from model 
        for name , value in self.model.dispersion.iteritems():      
            nshell = 0
            if name.split('_').count('thick') > 0:
                while nshell < self.n_shells:
                    nshell += 1
                    if name.split('_')[-1] == 'shell%s' % str(nshell):
                        self.dispersion[name] = value
                    else: 
                        continue
            else:
                self.dispersion[name] = value
                
    def _set_orientation_params(self):
        """
        model orientation and magnetic parameters, same params for this model
        """ 
        ##set dispersion from model 
        for param in self.model.orientation_params:     
            nshell = 0
            if param.split('_')[-1].count('shell') < 1:
                #print "param", param, param.split('_')[-1].count('shell')
                self.orientation_params.append(param)
                self.magnetic_params.append(param)
                continue
            while nshell < self.n_shells:
                nshell += 1
                if param.split('_')[-1] == 'shell%s' % str(nshell):
                    self.orientation_params.append(param)
                    self.magnetic_params.append(param)
                    continue                           

    def _set_params(self):
        """
        Concatenate the parameters of the model to create
        this model parameters 
        """
        # rearrange the parameters for the given # of shells
        for name , value in self.model.params.iteritems():
            nshell = 0
            if name.split('_').count('thick') > 0 or \
                        name.split('_').count('sld') > 0 or \
                        name[0] == 'M':
                if name.split('_')[-1] == 'solv' or \
                        name.split('_')[-1] == 'core0':
                    self.params[name]= value
                    continue
                while nshell < self.n_shells:
                    nshell += 1
                    if name.split('_')[-1] == 'shell%s' % str(nshell):
                        self.params[name]= value
                        continue
            else:
                self.params[name]= value
            
        # set constrained values for the original model params
        self._set_xtra_model_param()       
  
    def _set_details(self):
        """
        Concatenate details of the original model to create
        this model details 
        """
        for name ,detail in self.model.details.iteritems():
            if name in self.params.iterkeys():
                self.details[name]= detail
            
    
    def _set_xtra_model_param(self):
        """
        Set params of original model that are hidden from this model
        """
        # look for the model parameters that are not in param list
        for key in self.model.params.iterkeys():
            if key not in self.params.keys():
                if  key.split('_').count('thick') > 0:
                    self.model.setParam(key, 0)
                    continue

                for nshell in range(self.n_shells,max_nshells):
                     if key.split('_').count('sld') > 0 and \
                            key.split('_')[-1] == 'shell%s' % str(nshell+1):
                        try:
                            if key[0] != 'M':
                                value = self.model.params['sld_solv']
                                self.model.setParam(key, value)
                            else:
                                self.model.setParam(key, 0.0)
                        except: pass
                     

    def getProfile(self):
        """
        Get SLD profile 
        
        : return: (r, beta) where r is a list of radius of the transition points
                beta is a list of the corresponding SLD values 
        : Note: This works only for func_shell# = 2.
        """
        r = []
        beta = []
        # for core at r=0
        r.append(0)
        beta.append(self.params['sld_core0'])
        # for core at r=rad_core
        r.append(self.params['rad_core0'])
        beta.append(self.params['sld_core0'])
        
        # for shells
        for n in range(1, self.n_shells+1):
            # Left side of each shells
            r0 = r[len(r)-1]            
            r.append(r0)
            exec "beta.append(self.params['sld_shell%s'% str(n)])"

            # Right side of each shells
            exec "r0 += self.params['thick_shell%s'% str(n)]"
            r.append(r0)
            exec "beta.append(self.params['sld_shell%s'% str(n)])"
            
        # for solvent
        r0 = r[len(r)-1]            
        r.append(r0)
        beta.append(self.params['sld_solv'])
        r_solv = 5*r0/4
        r.append(r_solv)
        beta.append(self.params['sld_solv'])
        
        return r, beta

    def setParam(self, name, value):
        """ 
        Set the value of a model parameter
    
        : param name: name of the parameter
        : param value: value of the parameter
        """
        # set param to new model
        self._setParamHelper( name, value)
        ## setParam to model 
        if name == 'sld_solv':
            # the sld_*** model.params not in params must set to value of sld_solv
            for key in self.model.params.iterkeys():
                if key not in self.params.keys():
                    if key.split('_')[0] == 'sld':
                        self.model.setParam(key, value)
                    elif key.split('_')[1] == 'sld':
                        # mag params
                        self.model.setParam(key, 0.0)
        self.model.setParam( name, value)

    def _setParamHelper(self, name, value):
        """
        Helper function to setParam
        """
        #look for dispersion parameters
        toks = name.split('.')
        if len(toks) == 2:
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
        
        #raise ValueError, "Model does not contain parameter %s" % name
             
   
    def _set_fixed_params(self):
        """
        Fill the self.fixed list with the model fixed list
        """
        for item in self.model.fixed:
            if item.split('.')[0] in self.params.keys(): 
                self.fixed.append(item)

        self.fixed.sort()
                
    def run(self, x = 0.0):
        """ 
        Evaluate the model
        
        : param x: input q-value (float or [float, float] as [r, theta])
        : return: (DAB value)
        """
        # set effective radius and scaling factor before run

        return self.model.run(x)

    def runXY(self, x = 0.0):
        """ 
        Evaluate the model
        
        : param x: input q-value (float or [float, float] as [qx, qy])
        : return: DAB value
        """  
        # set effective radius and scaling factor before run

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
        Calculate the effective radius for P(q)*S(q)
        
        :return: the value of the effective radius
        
        """       
        return self.model.calculate_ER() 
    
    def calculate_VR(self):
        """ 
        Calculate the volf ratio for P(q)*S(q)
        
        :return: the value of the volf ratio
        
        """       
        return self.model.calculate_VR()
    
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
