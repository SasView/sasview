
from sans.models.BaseComponent import BaseComponent
import numpy, math

class MultiplicationModel(BaseComponent):
    """
        Use for S(Q)*P(Q).
        Perform multplication of two models.
        Contains the models parameters combined.
    """
    def __init__(self, model1, model2 ):
        BaseComponent.__init__(self)

        
        ## Name of the model
        self.name = model1.name +" * "+ model2.name
        ## model description
        self.description= model1.name +" * "+ model2.name
        self.description +="see %s description and %s description"%(model1.name,
                                                                     model2.name)
        self.model1= model1
        self.model2= model2
        ## dispersion
        self.dispersion = {}
        self._set_dispersion()
        ## Define parameters
        self.params = {}
        self._set_params()
        ## Parameter details [units, min, max]
        self.details = {}
        self._set_details()
        #list of parameter that can be fitted
        self.fixed= []  
        self._set_fixed_params()  
        
          
    def _set_dispersion(self):
        """
           combined the two models dispersions
        """
        for name , value in self.model1.dispersion.iteritems():
            self.dispersion[name]= value
            
        for name , value in self.model2.dispersion.iteritems():
            if not name in self.dispersion.keys():
                self.dispersion[name]= value
                
                
    def _set_params(self):
        """
            Concatenate the parameters of the two models to create
            this model parameters 
        """
        for name , value in self.model1.params.iteritems():
            self.params[name]= value
            
        for name , value in self.model2.params.iteritems():
            if not name in self.params.keys():
                self.params[name]= value
            
    def _set_details(self):
        """
            Concatenate details of the two models to create
            this model details 
        """
        for name ,detail in self.model1.details.iteritems():
            self.details[name]= detail
            
        for name , detail in self.model2.details.iteritems():
            if not name in self.details.keys():
                self.details[name]= detail
                
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
        return self.model1.run(x)* self.model2.run(x)
   
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
        if parameter in self.model1.getParamList():
            return self.model1.set_dispersion(parameter, dispersion)
        else:
            return self.model2.set_dispersion(parameter, dispersion)



    