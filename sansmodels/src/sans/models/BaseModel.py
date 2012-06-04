#!/usr/bin/env python

############################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation.
#
#If you use DANSE applications to do scientific research that leads to
#publication, we ask that you acknowledge the use of the software with the
#following sentence:
#
#"This work benefited from DANSE software developed
# under NSF award DMR-0520547."
#
#copyright 2008, University of Tennessee
#############################################################################

""" 
Provide base functionality for all model components

The following has changed since going from BaseComponent to BaseModel:

    - Arithmetic operation between models is no longer supported.
      It was found to be of little use and not very flexible.
    
    - Parameters are now stored as Parameter object to provide 
      the necessary extra information like limits, units, etc... 
"""

# imports   
import copy
   
class Parameter(object):
    """
    Parameter class
    """
    name  = ''
    value = 0.0
    def __init__(self, name, value):
        self.name = name
        self.value = value
        
    def __str__(self):
        return "%s: %g" % (self.name, self.value)

class ParameterProperty(object):
    """
    Parameter property allow direct access to
    the parameter values
    """
    def __init__(self,name,**kw):
        self.name = name
       
    def __get__(self,instance,cls):
        return instance.parameters[self.name].value

    def __set__(self,instance,value):
        instance.parameters[self.name].value = value


   
from ModelAdaptor import ModelAdaptor

class BaseModel(ModelAdaptor):
    """ 
    Basic model component
    """
    ## Name of the model
    name = "BaseModel"
    
    def __init__(self):
        ## Dictionary of Parameter objects
        self.parameters = {}

    # Evaluation methods to be implemented by the models
    def run(self, x=0):  return NotImplemented
    def runXY(self, x=0):  return NotImplemented
    def calculate_ER(self):  return NotImplemented
    def __call__(self, x=0):
        """     
        Evaluate the model. Equivalent to runXY(x)
        
        :param x: input value
        
        :return: value of the model
        
        """
        return self.runXY(x)
    
    def clone(self):
        """ Returns a new object identical to the current object """
        
        obj = copy.deepcopy(self)
        obj.params = copy.deepcopy(self.params)
        obj.details = copy.deepcopy(self.details)
        return obj
    
    def setParam(self, name, value):
        """ 
        Set the value of a model parameter
    
        :param name: name of the parameter
        :param value: value of the parameter
        
        """
        # Lowercase for case insensitivity
        name = name.lower()
        if name in self.parameters:
            print "found"
            #self.parameters[name].value = value
        return object.__setattr__(self, name, value)
        
    def getParam(self, name):
        """ 
        Set the value of a model parameter

        :param name: name of the parameter
        :param value: value of the parameter
        
        """
        # Lowercase for case insensitivity
        name = name.lower()
        return object.__getattribute__(self, name)
        
    def getParamList(self):
        """ 
        Return a list of all available parameters for the model 
        """
        param_list = self.params.keys()
        return param_list
        
    
if __name__ == "__main__":
    b = BaseModel() 
    #print b.operateOn
    
