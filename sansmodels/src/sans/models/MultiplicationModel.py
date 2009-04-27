
from sans.models.BaseComponent import BaseComponent
import numpy, math
import copy
from sans.models.pluginmodel import Model1DPlugin
from sans.models.DiamCylFunc import  DiamCylFunc
from sans.models.DiamEllipFunc import  DiamEllipFunc
class MultiplicationModel(BaseComponent):
    """
        Use for P(Q)*S(Q); function call maut be in order of P(Q) and then S(Q).
        Perform multplication of two models.
        Contains the models parameters combined.
    """
    def __init__(self, model1, model2 ):
        BaseComponent.__init__(self)

       
        ## Setting  model name model description
        self.description=""
        if  model1.name != "NoStructure"and  model2.name != "NoStructure":
             self.name = model1.name +" * "+ model2.name
             self.description= self.name+"\n"
             self.description +="see %s description and %s description"%( model1.name,
                                                                         model2.name )
        elif  model2.name != "NoStructure":
            self.name = model2.name
            self.description= model2.description
        else :
            self.name = model1.name
            self.description= model1.description
                        
        #For virial coefficients for only two P(Q) models,"CylinderModel","EllipsoidModel". SphereModel works w/o it.
        modelDiam = None
        if model1.__class__.__name__ == "CylinderModel":
            Model1DPlugin("DiamCylFunc")
            modelDiam = DiamCylFunc()
            para1 = 'radius'
            para2 = 'length'
            
        elif model1.__class__.__name__  == "EllipsoidModel":
            Model1DPlugin("DiamEllipFunc")
            modelDiam = DiamEllipFunc()
            para1 = 'radius_a'
            para2 = 'radius_b'
            
        self.modelD = modelDiam
        
        if model1.__class__.__name__ == "CylinderModel" \
            or model1.__class__.__name__  == "EllipsoidModel":
          
            self.para1 = para1
            self.para2 = para2

        
        self.model1= model1
        self.model2= model2
        
       
        ## dispersion
        self._set_dispersion()
        ## Define parameters
        self._set_params()
        ## Parameter details [units, min, max]
        self._set_details()
        #list of parameter that can be fitted
        self._set_fixed_params()  
        ## parameters with orientation
        for item in self.model1.orientation_params:
            self.orientation_params.append(item)
            
        for item in self.model2.orientation_params:
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
        obj.model1  = self.model1.clone()
        obj.model2  = self.model2.clone()
        
        return obj
    
    
    def _set_dispersion(self):
        """
           combined the two models dispersions
        """
        for name , value in self.model1.dispersion.iteritems():
            self.dispersion[name]= value
            
        for name , value in self.model2.dispersion.iteritems():
            # S(Q) has only 'radius' for dispersion.
            if not name in self.dispersion.keys()and name !='radius': 
                self.dispersion[name]= value

                    
                
                
    def _set_params(self):
        """
            Concatenate the parameters of the two models to create
            this model parameters 
        """
        
        for name , value in self.model1.params.iteritems():
            self.params[name]= value
            
            if self.modelD !=None:
                if name == self.para1 or name == self.para2:
                    self.modelD.params[name]= value
                elif name in self.model2.getParamList() and name !='radius':
                    self.model2.setParam( name, value)

            elif name in self.model2.getParamList():
                self.model2.setParam(name, value)
        if self.modelD !=None:
            self.model2.setParam('radius', self.modelD.run())
            
        for name , value in self.model2.params.iteritems():
            if not name in self.params.keys()and name != 'radius':
                self.params[name]= value
            
    def _set_details(self):
        """
            Concatenate details of the two models to create
            this model details 
        """
        for name ,detail in self.model1.details.iteritems():
            self.details[name]= detail
            
        for name , detail in self.model2.details.iteritems():
            if not name in self.details.keys()and name != 'radius':
                self.details[name]= detail
                
    def setParam(self, name, value):
        """ 
            Set the value of a model parameter
        
            @param name: name of the parameter
            @param value: value of the parameter
        """

        self._setParamHelper( name, value)

        if name in self.model1.getParamList():
            self.model1.setParam( name, value)
        if self.modelD !=None:
            if name==self.para1 or name == self.para2:
                    self.modelD.params[name]= value
                    self.model2.setParam('radius', self.modelD.run())
            elif name in self.model2.getParamList():
                        self.model2.setParam( name, value)        
        else:
            if name in self.model2.getParamList():
                self.model2.setParam( name, value)
            
        
            
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
             fill the self.fixed list with the two models fixed list
        """
        for item in self.model1.fixed:
            self.fixed.append(item)
            
        for item in self.model2.fixed:
            if not item in self.fixed:
                self.fixed.append(item)
        self.fixed.sort()
                
                
    def run(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [r, theta])
            @return: (DAB value)
        """
        #MultiplicationModel(self.model1, self.model2 )      
           
        #if self.modelD!=None:
        #    value = self.modelD.run(x)
        #    self.model2.setParam( "radius", value)        
                        
            #print "self.model2.setParam( radius, value)",value 
        return self.model1.run(x)*self.model2.run(x)
   
    def runXY(self, x = 0.0):
        """ Evaluate the model
            @param x: input q-value (float or [float, float] as [qx, qy])
            @return: DAB value
        """
        return self.model1.runXY(x)* self.model2.runXY(x)
    
    def set_dispersion(self, parameter, dispersion):
        """
            Set the dispersion object for a model parameter
            @param parameter: name of the parameter [string]
            @dispersion: dispersion object of type DispersionModel
        """
        value= None
        try:
            if parameter in self.model1.dispersion.keys():
                value= self.model1.set_dispersion(parameter, dispersion)
            #There is no dispersion for the structure factors(S(Q)). 
            #ToDo: need to decide whether or not the dispersion for S(Q) has to be considered for P*S.  
            elif parameter in self.model2.dispersion.keys()and name !='radius':
                value= self.model2.set_dispersion(parameter, dispersion)
            self._set_dispersion()
            return value
        except:
            raise 


    