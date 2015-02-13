""" 
    Wrapper for the Disperser class extension
"""
from sas.models.BaseComponent import BaseComponent
from sas_extension.c_models import Disperser
    
class DisperseModel(Disperser, BaseComponent):
    """ 
    Wrapper class for the Disperser extension
    Python class that takes a model and averages its output
    for a distribution of its parameters.
      
    The parameters to be varied are specified at instantiation time.
    The distributions are Gaussian, with std deviations specified for
    each parameter at instantiation time.
    
    Example: ::
    
        cyl = CylinderModel()
        disp = DisperseModel(cyl, ['cyl_phi'], [0.3])
        disp.run([0.01, 1.57])
        
    """
        
    def __init__(self, model, paramList, sigmaList):
        """ 
        Initialization 
        
        :param model: Model to disperse [BaseComponent]
        :param paramList: list of parameters to disperse [List of strings]
        :param sigmaList: list of std deviations for Gaussian dispersion
                    [List of floats]
        
        """
        
        # Initialize BaseComponent first, then sphere
        BaseComponent.__init__(self)
        Disperser.__init__(self, model, paramList, sigmaList)
        ## Name of the model
        self.name = model.name
        ## Keep track of the underlying model
        self.model = model
        self.description =''
        #list of parameter that cannot be fitted
        self.fixed = []
        
    def clone(self):
        """ Return a identical copy of self """
        return DisperseModel(self.model, self.params['paramList'], 
                             self.params['sigmaList']) 
   
    def setParam(self, name, value):
        """
            Set a parameter value
            :param name: parameter name
        """
        if name.lower() in self.params:
            BaseComponent.setParam(self, name, value)
        else:
            self.model.setParam(name, value)
   
    def getParam(self, name):
        """
            Get the value of the given parameter
            :param name: parameter name
        """
        if name.lower() in self.params:
            return BaseComponent.getParam(self, name)
        else:
            return self.model.getParam(name)
   
    def run(self, x = 0.0):
        """ 
            Evaluate the model
            :param x: input q, or [q,phi]
            :return: scattering function P(q)
        """
        return Disperser.run(self, x)
           
    def runXY(self, x = 0.0):
        """ 
            Evaluate the model
            :param x: input q, or [q,phi]
            :return: scattering function P(q)
        """
        return Disperser.runXY(self, x)
   
# End of file
