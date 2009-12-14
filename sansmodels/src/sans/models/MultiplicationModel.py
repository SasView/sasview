
from sans.models.BaseComponent import BaseComponent
import numpy, math
import copy
from sans.models.pluginmodel import Model1DPlugin
class MultiplicationModel(BaseComponent):
    """
        Use for P(Q)*S(Q); function call must be in the order of P(Q) and then S(Q):
        The model parameters are combined from both models, P(Q) and S(Q), except 'effective_radius' of S(Q)
        which will be calculated from P(Q) via calculate_ER().
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
                        
        ##models 
        self.p_model= p_model
        self.s_model= s_model
        
       
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        ## Parameter details [units, min, max]
        self._set_details()
        #list of parameter that can be fitted
        self._set_fixed_params()  
        ## parameters with orientation
        for item in self.p_model.orientation_params:
            self.orientation_params.append(item)
            
        for item in self.s_model.orientation_params:
            if not item in self.orientation_params:
                self.orientation_params.append(item)
                
        
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

    def _set_params(self):
        """
            Concatenate the parameters of the two models to create
            this model parameters 
        """

        for name , value in self.p_model.params.iteritems():
            self.params[name]= value
            
        for name , value in self.s_model.params.iteritems():
            #Remove the effect_radius from the (P*S) model parameters.
            if not name in self.params.keys() and name != 'effect_radius':
                self.params[name]= value
            
    def _set_details(self):
        """
            Concatenate details of the two models to create
            this model details 
        """
        for name ,detail in self.p_model.details.iteritems():
            self.details[name]= detail
            
        for name , detail in self.s_model.details.iteritems():
            if not name in self.details.keys():
                self.details[name]= detail
                
    def setParam(self, name, value):
        """ 
            Set the value of a model parameter
        
            @param name: name of the parameter
            @param value: value of the parameter
        """

        self._setParamHelper( name, value)

        if name in self.p_model.getParamList():
            self.p_model.setParam( name, value)

        if name in self.s_model.getParamList():
            self.s_model.setParam( name, value)

        self._setParamHelper( name, value)
        
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
            @return: (DAB value)
        """

        effective_radius = self.p_model.calculate_ER()
        #Reset the effective_radius of s_model just before the run
        if effective_radius != None and effective_radius != NotImplemented:
            self.s_model.setParam('effect_radius',effective_radius)                       
        return self.p_model.run(x)*self.s_model.run(x)

    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: DAB value
        """
        
        effective_radius = self.p_model.calculate_ER()
        #Reset the effective_radius of s_model just before the run
        if effective_radius != None and effective_radius != NotImplemented:
            self.s_model.setParam('effect_radius',effective_radius)          
        return self.p_model.runXY(x)* self.s_model.runXY(x)

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
    