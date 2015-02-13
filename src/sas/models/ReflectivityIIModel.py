   
from sas.models.BaseComponent import BaseComponent
from sas.models.ReflAdvModel import ReflAdvModel
from copy import deepcopy
from math import floor
from math import fabs
func_list = {'Erf(|nu|*z)':0, 'RPower(z^|nu|)':1, 'LPower(z^|nu|)':2, \
                     'RExp(-|nu|*z)':3, 'LExp(-|nu|*z)':4}
max_nshells = 10
class ReflectivityIIModel(BaseComponent):
    """
    This multi-model is based on Parratt formalism and provides the capability
    of changing the number of layers between 0 and 10.
    """
    def __init__(self, multfactor=1):
        """
            :param multfactor: number of layers in the model, 
            assumes 0<= n_layers <=10.
        """
        BaseComponent.__init__(self)

        ## Setting  model name model description
        self.description = ""
        model = ReflAdvModel()
        self.model = model
        self.name = "ReflectivityIIModel"
        self.description = model.description
        self.n_layers = int(multfactor)
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
        self.model.params['n_layers'] = self.n_layers
        
        ## functional multiplicity info of the model
        # [int(maximum no. of functionality),"str(Titl),
        # [str(name of function0),...], [str(x-asix name of sld),...]]
        self.multiplicity_info = [max_nshells, "No. of Layers:", [], ['Depth']]
        ## independent parameter name and unit [string]
        self.input_name = "Q"
        self.input_unit = "A^{-1}"
        ## output name and unit  [string]
        self.output_name = "Reflectivity"
        self.output_unit = ""
   
    
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
        # rearrange the parameters for the given # of shells
        for name, value in self.model.params.iteritems():
            n = 0
            pos = len(name.split('_'))-1
            first_name = name.split('_')[0]
            last_name = name.split('_')[pos]
            if first_name == 'npts':
                self.params[name]=value
                continue
            elif first_name == 'sldIM':
                continue
            elif first_name == 'func':
                n = -1
                while n < self.n_layers:
                    n += 1
                    if last_name == 'inter%s' % str(n): 
                        self.params[name] = value
                        continue
            
                #continue
            elif last_name[0:5] == 'inter':
                n = -1
                while n < self.n_layers:
                    n += 1
                    if last_name == 'inter%s' % str(n):
                        self.params[name] = value
                        continue
            elif last_name[0:4] == 'flat':
                while n < self.n_layers:
                    n += 1
                    if last_name == 'flat%s' % str(n):
                        self.params[name] = value
                        continue
            elif name == 'n_layers':
                continue
            else:
                self.params[name] = value
  
        self.model.params['n_layers'] = self.n_layers    
  
        # set constrained values for the original model params
        self._set_xtra_model_param()       

    def _set_details(self):
        """
        Concatenate details of the original model to create
        this model details 
        """
        for name, detail in self.model.details.iteritems():
            if name in self.params.iterkeys():
                self.details[name] = detail
            
    
    def _set_xtra_model_param(self):
        """
        Set params of original model that are hidden from this model
        """
        # look for the model parameters that are not in param list
        for key in self.model.params.iterkeys():
            if key not in self.params.keys():
                if  key.split('_')[0] == 'thick':
                    self.model.setParam(key, 0)
                    continue
                if  key.split('_')[0] == 'func': 
                    self.model.setParam(key, 0)
                    continue

                for nshell in range(self.n_layers,max_nshells):
                    if key.split('_')[1] == 'flat%s' % str(nshell+1):
                        try:
                            if key.split('_')[0] == 'sld':
                                value = self.model.params['sld_medium']
                            elif key.split('_')[0] == 'sldIM':
                                value = self.model.params['sldIM_medium']
                            self.model.setParam(key, value)
                        except:
                            message = "ReflectivityIIModel evaluation problem"
                            raise RuntimeError, message
    
    def _get_func_list(self):
        """
            Get the list of functions in each layer (shell) 
        """
        return func_list
        
    def getProfile(self):
        """
        Get SLD profile 
        
        : return: (z, beta) where z is a list of depth of the transition points
                beta is a list of the corresponding SLD values 
        """
        # max_pts for each layers
        n_sub = int(self.params['npts_inter'])
        z = []
        beta = []
        z.append(0)
        beta.append(self.params['sld_bottom0']) 
       
        z0 = 0.0
        dz = 0.0
        # for layers from the top
        for n_lyr in range(1, self.n_layers+2):
            i = n_lyr
            # j=0 for interface, j=1 for flat layer 
            for j in range(0, 2):
                # interation for sub-layers
                for n_s in range(0, n_sub):
                    # for flat layer
                    if j == 1:
                        if i == self.n_layers+1:
                            break
                        # shift half sub thickness for the first point
                        z0 -= dz/2.0
                        z.append(z0)
                        sld_i = self.params['sld_flat%s' % str(i)]
                        beta.append(sld_i)
                        dz = self.params['thick_flat%s' % str(i)]
                        z0 += dz
                    else:
                        dz = self.params['thick_inter%s' % str(i-1)]/n_sub
                        nu = fabs(self.params['nu_inter%s' % str(i-1)])
                        if n_s == 0:
                            # shift half sub thickness for the point
                            z0 += dz/2.0
                        # decide which sld is which, sld_r or sld_l
                        if i == 1:
                            sld_l = self.params['sld_bottom0']
                        else:
                            sld_l = self.params['sld_flat%s' % str(i-1)]
                        if i == self.n_layers+1:
                            sld_r = self.params['sld_medium']
                        else:
                            sld_r = self.params['sld_flat%s' % str(i)]
                        if sld_r == sld_l:
                            sld_i = sld_r
                        else:
                            func_idx = self.params['func_inter%s' % str(i-1)]
                            # calculate the sld
                            sld_i = self._get_sld(func_idx, n_sub, n_s+0.5, nu,
                                              sld_l, sld_r)
                    # append to the list
                    z.append(z0)
                    beta.append(sld_i)
                    if j == 1: 
                        break
                    else: 
                        z0 += dz
        # put substrate and superstrate profile
        z.append(z0)
        beta.append(self.params['sld_medium'])  
        z_ext = z0/5.0
        
        # put the extra points for the substrate 
        # and superstrate
        z.append(z0+z_ext)
        beta.append(self.params['sld_medium']) 
        z.insert(0, -z_ext)
        beta.insert(0, self.params['sld_bottom0']) 
        # rearrange the profile for NR sld profile style
        z = [z0 - x for x in z]
        z.reverse()
        beta.reverse()  
        return z, beta
    
    def _get_sld(self, func_idx, n_sub, n_s, nu, sld_l, sld_r):
        """
        Get the function asked to build sld profile
        : param func_idx: func type number
        : param n_sub: total number of sub_layer
        : param n_s: index of sub_layer
        : param nu: coefficient of the function
        : param sld_l: sld on the left side
        : param sld_r: sld on the right side
        : return: sld value, float
        """
        from sas.models.SLDCalFunc import SLDCalFunc
        # sld_cal init
        sld_cal = SLDCalFunc()
        # set params
        sld_cal.setParam('fun_type', func_idx)
        sld_cal.setParam('npts_inter', n_sub)
        sld_cal.setParam('shell_num', n_s)
        sld_cal.setParam('nu_inter', nu)
        sld_cal.setParam('sld_left', sld_l)
        sld_cal.setParam('sld_right', sld_r)
        # return sld value
        return sld_cal.run()
    
    def setParam(self, name, value):
        """ 
        Set the value of a model parameter
    
        : param name: name of the parameter
        : param value: value of the parameter
        """
        # set param to new model
        self._setParamHelper( name, value)
        
        ## setParam to model 
        if name == 'sld_medium':
            # the sld_*** model.params not in params must set 
            # to value of sld_solv
            for key in self.model.params.iterkeys():
                if key not in self.params.keys()and key.split('_')[0] == 'sld':
                    self.model.setParam(key, value)   
        
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
    def evalDistribution(self, x):
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
