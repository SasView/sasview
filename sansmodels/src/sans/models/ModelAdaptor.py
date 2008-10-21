#!/usr/bin/env python
"""
    This software was developed by the University of Tennessee as part of the
    Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
    project funded by the US National Science Foundation.

    If you use DANSE applications to do scientific research that leads to
    publication, we ask that you acknowledge the use of the software with the
    following sentence:

    "This work benefited from DANSE software developed under NSF award DMR-0520547."

    copyright 2008, University of Tennessee
"""

""" 
    Provide base functionality for all model components
    
    The following has changed since going from BaseComponent to BaseModel:
    
        - Arithmetic operation between models is no longer supported.
          It was found to be of little use and not very flexible.
        
        - Parameters are now stored as Parameter object to provide 
          the necessary extra information like limits, units, etc... 
"""

class ParameterDict(dict):
    """
        Parameter dictionary used for backward 
        compatibility between the old-style 'params'
        dictionary and the new-style 'parameters'
        dictionary.
    """
    def __init__(self, parameters):
        """    
            Initialization
            @param parameters: new-style 'parameters' dictionary
        """
        self.parameters = parameters
        
    def __setitem__(self, name, value):
        self.parameters[name].value = value
    
    def __getitem__(self, name):
        return self.parameters[name].value 
    
class ModelAdaptor(object):
    """ 
        Model adaptor to provide old-style model functionality
    """

    def __init__(self):
        """ Initialization"""
        ## Dictionary of Parameter objects
        self.parameters = {}
        ## Dictionary of parameters, available for backward compatibility
        self.params = ParameterDict(self.parameters)
        ## Additional details, provided for backward compatibility
        self.details = {}
        self.description=''
        ## Dictionary used to store the dispersity/averaging
        #  parameters of dispersed/averaged parameters.
        ## Provided for backward compatibility
        self.dispersion = {}
                              
    # Old-style methods that are no longer used
    def setParamWithToken(self, name, value, token, member): return NotImplemented
    def getParamWithToken(self, name, token, member): return NotImplemented
    def getParamListWithToken(self, token, member): return NotImplemented
    def __add__(self, other): raise ValueError, "Model operation are no longer supported"
    def __sub__(self, other): raise ValueError, "Model operation are no longer supported"
    def __mul__(self, other): raise ValueError, "Model operation are no longer supported"
    def __div__(self, other): raise ValueError, "Model operation are no longer supported"

    

if __name__ == "__main__":
    b = BaseModel() 
    print b.operateOn
    
