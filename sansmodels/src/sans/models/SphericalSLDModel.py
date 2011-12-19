   
from sans.models.BaseComponent import BaseComponent
from sans.models.SphereSLDModel import SphereSLDModel
from copy import deepcopy
from math import floor
#from scipy.special import erf
func_list = {'Erf(|nu|*z)':0, 'RPower(z^|nu|)':1, 'LPower(z^|nu|)':2, \
                     'RExp(-|nu|*z)':3, 'LExp(-|nu|*z)':4}
max_nshells = 10
class SphericalSLDModel(BaseComponent):
    """
    This multi-model is based on Parratt formalism and provides the capability
    of changing the number of layers between 0 and 10.
    """
    def __init__(self, multfactor=1):
        BaseComponent.__init__(self)
        """
        :param multfactor: number of layers in the model, 
        assumes 0<= n_shells <=10.
        """

        ## Setting  model name model description
        self.description=""
        model = SphereSLDModel()
        self.model = model
        self.name = "SphericalSLDModel"
        self.description=model.description
        self.n_shells = multfactor
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
        self.model.params['n_shells'] = self.n_shells
        
        ## functional multiplicity info of the model
        # [int(maximum no. of functionality),"str(Titl),
        # [str(name of function0),...], [str(x-asix name of sld),...]]
        self.multiplicity_info = [max_nshells,"No. of Shells:",[],['Radius']]
        
    
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
        for name , value in self.model.dispersion.iteritems():   
              
            nshell = -1
            if name.split('_')[0] == 'thick':
                while nshell<1:
                    nshell += 1
                    if name.split('_')[1] == 'inter%s' % str(nshell):
                        self.dispersion[name]= value
                    else: 
                        continue
            else:
                self.dispersion[name]= value

    def _set_params(self):
        """
        Concatenate the parameters of the model to create
        this model parameters 
        """
        # rearrange the parameters for the given # of shells
        for name , value in self.model.params.iteritems():
            n = 0
            pos = len(name.split('_'))-1
            first_name = name.split('_')[0]
            last_name = name.split('_')[pos]
            if first_name == 'npts':
                self.params[name]=value
                continue
            elif first_name == 'func':
                n= -1
                while n<self.n_shells:
                    n += 1
                    if last_name == 'inter%s' % str(n): 
                        self.params[name]=value
                        continue
            elif last_name[0:5] == 'inter':
                n= -1
                while n<self.n_shells:
                    n += 1
                    if last_name == 'inter%s' % str(n):
                        self.params[name]= value
                        continue
            elif last_name[0:4] == 'flat':
                while n<self.n_shells:
                    n += 1
                    if last_name == 'flat%s' % str(n):
                        self.params[name]= value
                        continue
            elif name == 'n_shells':
                continue
            else:
                self.params[name]= value
  
        self.model.params['n_shells'] = self.n_shells    
  
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
                if  key.split('_')[0] == 'thick':
                    self.model.setParam(key, 0)
                    continue
                if  key.split('_')[0] == 'func': 
                        self.model.setParam(key, 0)
                        continue

                for nshell in range(self.n_shells,max_nshells):
                    if key.split('_')[1] == 'flat%s' % str(nshell+1):
                        try:
                            if key.split('_')[0] == 'sld':
                                value = self.model.params['sld_solv']
                            self.model.setParam(key, value)
                        except: pass
    
    def _get_func_list(self):
        """
        Get the list of functions in each layer (shell) 
        """
        #func_list = {}
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
        z0 = 0
        sub_range = floor(n_sub/2.0)
        # two sld points for core
        z.append(0)
        beta.append(self.params['sld_core0']) 
        z.append(self.params['rad_core0']) 
        beta.append(self.params['sld_core0']) 
        z0 += self.params['rad_core0']
        # for layers from the core
        for n in range(1,self.n_shells+2):
            i = n
            # j=0 for interface, j=1 for flat layer 
            for j in range(0,2):
                # interation for sub-layers
                for n_s in range(0,n_sub+1):
                    if j==1:
                        if i==self.n_shells+1:
                            break
                        # shift half sub thickness for the first point
                        z0 -= dz#/2.0
                        z.append(z0)
                        #z0 -= dz/2.0
                        z0 += self.params['thick_flat%s'% str(i)]
                        
                        sld_i = self.params['sld_flat%s'% str(i)]
                        beta.append(self.params['sld_flat%s'% str(i)])
                        dz = 0
                    else:
                        dz = self.params['thick_inter%s'% str(i-1)]/n_sub
                        nu = self.params['nu_inter%s'% str(i-1)]
                        # decide which sld is which, sld_r or sld_l
                        if i == 1:
                            sld_l = self.params['sld_core0']
                        else:
                            sld_l = self.params['sld_flat%s'% str(i-1)]
                        if i == self.n_shells+1:
                            sld_r = self.params['sld_solv']
                        else:
                            sld_r = self.params['sld_flat%s'% str(i)]
                        # get function type
                        func_idx = self.params['func_inter%s'% str(i-1)]
                        # calculate the sld
                        sld_i = self._get_sld(func_idx, n_sub, n_s, nu,
                                              sld_l, sld_r)
                    # append to the list
                    z.append(z0)
                    beta.append(sld_i)
                    z0 += dz
                    if j==1: break
        # put sld of solvent
        z.append(z0)
        beta.append(self.params['sld_solv'])  
        z_ext = z0/5.0
        z.append(z0+z_ext)
        beta.append(self.params['sld_solv']) 
        # return sld profile (r, beta)
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
        from sans.models.SLDCalFunc import SLDCalFunc
        # sld_cal init
        sld_cal = SLDCalFunc()
        # set params
        sld_cal.setParam('fun_type',func_idx)
        sld_cal.setParam('npts_inter',n_sub)
        sld_cal.setParam('shell_num',n_s)
        sld_cal.setParam('nu_inter',nu)
        sld_cal.setParam('sld_left',sld_l)
        sld_cal.setParam('sld_right',sld_r)
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
        if name=='sld_solv':
            # the sld_*** model.params not in params must set to 
            # value of sld_solv
            for key in self.model.params.iterkeys():
                if key not in self.params.keys()and key.split('_')[0] == 'sld':
                        self.model.setParam(key, value)
            
        self.model.setParam( name, value)

    def _setParamHelper(self, name, value):
        """
        Helper function to setParam
        """
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
             
   
    def _set_fixed_params(self):
        """
        Fill the self.fixed list with the model fixed list
        """
        for item in self.model.fixed:
            if item.split('.')[0] in self.params.keys(): 
                self.fixed.append(item)

        self.fixed.sort()
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
        value= None
        try:
            if parameter in self.model.dispersion.keys():
                value= self.model.set_dispersion(parameter, dispersion)
            self._set_dispersion()
            return value
        except:
            raise 
