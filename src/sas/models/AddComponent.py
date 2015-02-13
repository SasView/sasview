#!/usr/bin/env python

""" 
Provide base functionality for all model components

:author: Mathieu Doucet / UTK

:contact: mathieu.doucet@nist.gov

"""

# info
__author__ = "Mathieu Doucet /  UTK"
__id__ = "$Id: BaseComponent.py,v 1.2 2007/03/14 21:04:40 doucet Exp $"
   
# imports   
from sas.models.BaseComponent import BaseComponent

class AddComponent(BaseComponent):
    """ 
    Basic model component for Addition
    Provides basic arithmetics
    """

    def __init__(self, base=None, other=None):
        """
        :param base: component to add to 
        :param other: component to add
        
        """
        BaseComponent.__init__(self)
        # Component to add to
        self.operateOn = base
        # Component to add
        self.other = other
        # name
        self.name = 'AddComponent'
        
    def run(self, x=0):
        """
        Evaluate each part of the component and sum the results
        
        :param x: input parameter
        
        :return: value of the model at x
        
        """
        return self.operateOn.run(x) + self.other.run(x)
        
    def runXY(self, x=0):
        """
        Evaluate each part of the component and sum the results
        
        :param x: input parameter
        
        :return: value of the model at x
        
        """
        return self.operateOn.runXY(x) + self.other.runXY(x)
        
    def setParam(self, name, value):
        """ 
        Set the value of a model parameter
        
        :param name: name of parameter to set
        :param value: value to give the paramter
        
        """
        return BaseComponent.setParamWithToken(self, name, 
                                               value, 'add', self.other)
    
    def getParam(self, name):
        """ 
        Set the value of a model parameter
        
        :param name: name of the parameter
        
        :return: value of the parameter
        
        """
        return BaseComponent.getParamWithToken(self, name, 'add', self.other)
    
    def getParamList(self):
        """ 
        Return a list of all available parameters for the model 
        """
        return BaseComponent.getParamListWithToken(self, 'add', self.other)
        
    
# End of file