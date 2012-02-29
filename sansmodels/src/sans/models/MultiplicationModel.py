
from sans.models.BaseComponent import BaseComponent
import numpy, math
import copy
from sans.models.pluginmodel import Model1DPlugin
class MultiplicationModel(BaseComponent):
    """
        Use for P(Q)*S(Q); function call must be in the order of P(Q) and then S(Q):
        The model parameters are combined from both models, P(Q) and S(Q), except 1) 'effect_radius' of S(Q)
        which will be calculated from P(Q) via calculate_ER(), 
        and 2) 'scale' in P model which is synchronized w/ volfraction in S 
        then P*S is multiplied by a new param, 'scale_factor'.
        The polydispersion is applicable only to P(Q), not to S(Q).
        Note: P(Q) refers to 'form factor' model while S(Q) does to 'structure factor'.
    """
    def __init__(self, p_model, s_model ):
        BaseComponent.__init__(self)
        """
            @param p_model: form factor, P(Q)
            @param s_model: structure factor, S(Q)
        """

        ## Setting  model name model description
        self.description=""
        self.name = p_model.name +" * "+ s_model.name
        self.description= self.name+"\n"
        self.fill_description(p_model, s_model)

        ## Define parameters
        self.params = {}

        ## Parameter details [units, min, max]
        self.details = {}
        
        ##models 
        self.p_model= p_model
        self.s_model= s_model        
       
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        ## New parameter:Scaling factor
        self.params['scale_factor'] = 1
        
        ## Parameter details [units, min, max]
        self._set_details()
        self.details['scale_factor'] = ['',     None, None]
        
        #list of parameter that can be fitted
        self._set_fixed_params()  
        ## parameters with orientation
        for item in self.p_model.orientation_params:
            self.orientation_params.append(item)
            
        for item in self.s_model.orientation_params:
            if not item in self.orientation_params:
                self.orientation_params.append(item)
        # get multiplicity if model provide it, else 1.
        try:
            multiplicity = p_model.multiplicity
        except:
            multiplicity = 1
        ## functional multiplicity of the model
        self.multiplicity = multiplicity    
          
        # non-fittable parameters
        self.non_fittable = p_model.non_fittable  
        self.multiplicity_info = [] 
        self.fun_list = {}
        if self.non_fittable > 1:
            try:
                self.multiplicity_info = p_model.multiplicity_info 
                self.fun_list = p_model.fun_list
            except:
                pass
        else:
            self.multiplicity_info = []
            
    def _clone(self, obj):
        """
            Internal utility function to copy the internal
            data members to a fresh copy.
        """
        obj.params     = copy.deepcopy(self.params)
        obj.description     = copy.deepcopy(self.description)
        obj.details    = copy.deepcopy(self.details)
        obj.dispersion = copy.deepcopy(self.dispersion)
        obj.p_model  = self.p_model.clone()
        obj.s_model  = self.s_model.clone()
        #obj = copy.deepcopy(self)
        return obj
    
    
    def _set_dispersion(self):
        """
           combined the two models dispersions
           Polydispersion should not be applied to s_model
        """
        ##set dispersion only from p_model 
        for name , value in self.p_model.dispersion.iteritems():
            self.dispersion[name]= value 
                                      
    def getProfile(self):
        """
        Get SLD profile of p_model if exists
        
        : return: (r, beta) where r is a list of radius of the transition points
                beta is a list of the corresponding SLD values 
        : Note: This works only for func_shell# = 2 (exp function).
        """
        try:
            x,y = self.p_model.getProfile()
        except:
            x = None
            y = None
            
        return x, y
    
    def _set_params(self):
        """
            Concatenate the parameters of the two models to create
            this model parameters 
        """

        for name , value in self.p_model.params.iteritems():
            if not name in self.params.keys() and name != 'scale':
                self.params[name]= value
            
        for name , value in self.s_model.params.iteritems():
            #Remove the effect_radius from the (P*S) model parameters.
            if not name in self.params.keys() and name != 'effect_radius':
                self.params[name]= value
                
        # Set "scale and effec_radius to P and S model as initializing
        # since run P*S comes from P and S separately.
        self._set_scale_factor()
        self._set_effect_radius()       
            
    def _set_details(self):
        """
            Concatenate details of the two models to create
            this model details 
        """
        for name ,detail in self.p_model.details.iteritems():
            if name != 'scale':
                self.details[name]= detail
            
        for name , detail in self.s_model.details.iteritems():
            if not name in self.details.keys() or name != 'effect_radius':
                self.details[name]= detail
    
    def _set_scale_factor(self):
        """
            Set scale=volfraction to P model
        """
        value = self.params['volfraction']
        if value != None: 
            factor = self.p_model.calculate_VR()
            if factor == None or factor == NotImplemented or factor == 0.0:
                val= value
            else:
                val = value / factor
            self.p_model.setParam('scale', value)
            self.s_model.setParam('volfraction', val)
            
    def _set_effect_radius(self):
        """
            Set effective radius to S(Q) model
        """
        if not 'effect_radius' in self.s_model.params.keys():
            return
        effective_radius = self.p_model.calculate_ER()
        #Reset the effective_radius of s_model just before the run
        if effective_radius != None and effective_radius != NotImplemented:
            self.s_model.setParam('effect_radius',effective_radius)
                
    def setParam(self, name, value):
        """ 
            Set the value of a model parameter
        
            @param name: name of the parameter
            @param value: value of the parameter
        """
        # set param to P*S model
        self._setParamHelper( name, value)
        
        ## setParam to p model 
        # set 'scale' in P(Q) equal to volfraction 
        if name == 'volfraction':
            self._set_scale_factor()
        elif name in self.p_model.getParamList():
            self.p_model.setParam( name, value)
        
        ## setParam to s model 
        # This is a little bit abundant: Todo: find better way         
        self._set_effect_radius()
        if name in self.s_model.getParamList():
            if name != 'volfraction':
                self.s_model.setParam( name, value)
            

        #self._setParamHelper( name, value)
        
    def _setParamHelper(self, name, value):
        """
            Helper function to setparam
        """
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2:
            for item in self.dispersion.keys():
                if item.lower()==toks[0].lower():
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():
                            self.dispersion[item][par] = value
                            return
        else:
            # Look for standard parameter
            for item in self.params.keys():
                if item.lower()==name.lower():
                    self.params[item] = value
                    return
            
        raise ValueError, "Model does not contain parameter %s" % name
             
   
    def _set_fixed_params(self):
        """
             fill the self.fixed list with the p_model fixed list
        """
        for item in self.p_model.fixed:
            self.fixed.append(item)

        self.fixed.sort()
                
                
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (scattering function value)
        """
        # set effective radius and scaling factor before run
        self._set_effect_radius()
        self._set_scale_factor()
        return self.params['scale_factor']*self.p_model.run(x)*self.s_model.run(x)

    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: scattering function value
        """  
        # set effective radius and scaling factor before run
        self._set_effect_radius()
        self._set_scale_factor()
        return self.params['scale_factor']*self.p_model.runXY(x)* self.s_model.runXY(x)
    
    ## Now (May27,10) directly uses the model eval function 
    ## instead of the for-loop in Base Component.
    def evalDistribution(self, x = []):
        """ Evaluate the model in cartesian coordinates
            @param x: input q[], or [qx[], qy[]]
            @return: scattering function P(q[])
        """
        # set effective radius and scaling factor before run
        self._set_effect_radius()
        self._set_scale_factor()
        return self.params['scale_factor']*self.p_model.evalDistribution(x)* self.s_model.evalDistribution(x)

    def set_dispersion(self, parameter, dispersion):
        """
            Set the dispersion object for a model parameter
            @param parameter: name of the parameter [string]
            @dispersion: dispersion object of type DispersionModel
        """
        value= None
        try:
            if parameter in self.p_model.dispersion.keys():
                value= self.p_model.set_dispersion(parameter, dispersion)
            self._set_dispersion()
            return value
        except:
            raise 

    def fill_description(self, p_model, s_model):
        """
            Fill the description for P(Q)*S(Q)
        """
        description = ""
        description += "Note:1) The effect_radius (effective radius) of %s \n"% (s_model.name)
        description +="             is automatically calculated from size parameters (radius...).\n"
        description += "         2) For non-spherical shape, this approximation is valid \n"
        description += "            only for limited systems. Thus, use it at your own risk.\n"
        description +="See %s description and %s description \n"%( p_model.name, s_model.name )
        description += "        for details of individual models."
        self.description += description
    