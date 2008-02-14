#!/usr/bin/env python
""" Provide base functionality for all model components
    @author: Mathieu Doucet / UTK
    @contact: mathieu.doucet@nist.gov
"""

# info
__author__ = "Mathieu Doucet /  UTK"
__id__ = "$Id: BaseComponent.py,v 1.2 2007/03/14 21:04:40 doucet Exp $"
   
# imports   
import copy
   
class BaseComponent:
    """ Basic model component
        Provides basic arithmetics
        
        The supported operations are: add (+), subtract (-), multiply (*) and divide (/).
        
        Here's an arithmetics example to define a function
        f = ( 1+sin(x) )**2 + 3.0
        and evaluate it at 1.4.
        
        
        sin   = Sin()
        const1 = Constant()
        const2 = Constant()
        const2.setParam('value', 3.0)
         
        func = (const1 + sin)*(const1 + sin) + const2
        
        print func(1.4) 
        
    """

    def __init__(self):
        """ Initialization"""
        
        ## Name of the model
        self.name   = "BaseComponent"
        ## Component left of operator
        self.operateOn = None
        ## Component right of operator
        self.other = None

        
        ## Parameters to be accessed by client
        self.params = {}
           
    def __str__(self):
        """ Prints an XML representation of the model
            @return: string representation
        """
        return self.name
   
    def run(self, x=0): #pylint: disable-msg=R0201
        """ Evaluate the model
            Dummy function
            @param x: input value
            @return: value of the model
        """
        return 0
    
    def clone(self):
        """ Returns a new object identical to the current object """
        
        obj = copy.deepcopy(self)
        obj.params = copy.deepcopy(self.params)
    
        # Check for standard data members of arithmetics sub-classes
        if hasattr(self, 'operateOn') and \
            not self.operateOn == None:
            obj.operateOn = self.operateOn.clone()

        if hasattr(self, 'other') and \
            not self.other == None:
            obj.other = self.other.clone()
        
        return obj

    def __add__(self, other):
        """ Overload addition operator
            @param other: model to add
        """
        from sans.models.AddComponent import AddComponent
        return AddComponent(self.clone(), other)
        
    def __sub__(self, other):
        """ Overload subtraction operator
            @param other: model to subtract
        """
        from sans.models.SubComponent import SubComponent
        return SubComponent(self.clone(), other)
        
    def __mul__(self, other):
        """ Overload multiplication operator
            @param other: model to multiply
        """
        from sans.models.MulComponent import MulComponent
        return MulComponent(self.clone(), other)
        
    def __div__(self, other):
        """ Overload division operator
            @param other: mode to divide by
        """
        from sans.models.DivComponent import DivComponent
        return DivComponent(self.clone(), other)
        
    def setParam(self, name, value):
        """ Set the value of a model parameter
        
            A list of all the parameters of a model can
            be obtained with the getParamList() method.
            For models resulting from an arithmetic
            operation between two models, the names of
            the parameters are modified according to
            the following rule:
             
            For parameter 'a' of model A and 
            parameter 'b' of model B:
             
            C = A + B
                C.setParam('base.a') to access 'a'
                C.setParam('add.b') to access 'b'
                 
            C = A - B
                C.setParam('base.a') to access 'a'
                C.setParam('sub.b') to access 'b'
                 
            C = A * B
                C.setParam('base.a') to access 'a'
                C.setParam('mul.b') to access 'b'
                 
            C = A / B
                C.setParam('base.a') to access 'a'
                C.setParam('div.b') to access 'b'
                         
            @param name: name of the parameter
            @param value: value of the parameter
        """
        # Lowercase for case insensitivity
        name = name.lower()
        
        keys = self.params.keys()
        found = False
        
        # Loop through the keys and find the right one
        # The case should not matter
        for key in keys:
            if name == key.lower():
                self.params[key] = value
                found = True
                break
        
        # Check whether we found the key
        if not found:
            raise ValueError, "Model does not contain parameter %s" % name

    def setParamWithToken(self, name, value, token, member):
        """ 
            Returns value of a parameter that is part of an internal component
            @param name: name of the parameter
            @param value: value of the parameter
            @param token: parameter prefix
            @param member: data member pointing to the component
        """
        # Lowercase for case insensitivity
        name = name.lower()
        
        # Look for sub-model access
        toks = name.split('.')
        if len(toks)>1:
            short_name = '.'.join(toks[1:])
            if toks[0] == 'base':
                return self.operateOn.setParam(short_name, value)
            elif toks[0] == token:
                return member.setParam(short_name, value)
            else:
                raise ValueError, "Model does not contain parameter %s" % name
   
        # If we didn't find a token we know, call the default behavior
        return BaseComponent.setParam(self, name, value)

        
    def getParam(self, name):
        """ Set the value of a model parameter

            A list of all the parameters of a model can
            be obtained with the getParamList() method.
            For models resulting from an arithmetic
            operation between two models, the names of
            the parameters are modified according to
            the following rule:
             
            For parameter 'a' of model A and 
            parameter 'b' of model B:
             
            C = A + B
                C.getParam('base.a') to access 'a'
                C.getParam('add.b') to access 'b'
                 
            C = A - B
                C.getParam('base.a') to access 'a'
                C.getParam('sub.b') to access 'b'
                 
            C = A * B
                C.getParam('base.a') to access 'a'
                C.getParam('mul.b') to access 'b'
                 
            C = A / B
                C.getParam('base.a') to access 'a'
                C.getParam('div.b') to access 'b'
                         
            @param name: name of the parameter
            @param value: value of the parameter
        """
        # Lowercase for case insensitivity
        name = name.lower()
        
        keys = self.params.keys()
        value = None
        
        # Loop through the keys and find the right one
        # The case should not matter
        for key in keys:
            if name == key.lower():
                value = self.params[key]
                break
        
        # Check whether we found the key
        if value == None:
            raise ValueError, "Model does not contain parameter %s" % name
        
        return value
        
    def getParamWithToken(self, name, token, member):
        """
            Returns value of a parameter that is part of an internal component
            @param name: name of the parameter
            @param token: parameter prefix
            @param member: data member pointing to the component
            @return: value of the parameter
        """
        # Lowercase for case insensitivity
        name = name.lower()
        
        # Look for sub-model access
        toks = name.split('.')
        if len(toks)>1:
            #short_name = string.join(toks[1:],'.')
            short_name = '.'.join(toks[1:])
            if toks[0] == 'base':
                return self.operateOn.getParam(short_name)
            elif toks[0] == token:
                return member.getParam(short_name)
            else:
                raise ValueError, "Model does not contain parameter %s" % name
   
        # If we didn't find a token we know, call the default behavior
        return BaseComponent.getParam(self, name)
        
         
    def getParamList(self):
        """ Return a list of all available parameters for the model 
        
            For models resulting from an arithmetic
            operation between two models, the names of
            the parameters are modified according to
            the following rule:
             
            For parameter 'a' of model A and 
            parameter 'b' of model B:
             
            C = A + B
                C.getParam('base.a') to access 'a'
                C.getParam('add.b') to access 'b'
                 
            C = A - B
                C.getParam('base.a') to access 'a'
                C.getParam('sub.b') to access 'b'
                 
            C = A * B
                C.getParam('base.a') to access 'a'
                C.getParam('mul.b') to access 'b'
                 
            C = A / B
                C.getParam('base.a') to access 'a'
                C.getParam('div.b') to access 'b'
                                 
        """
        param_list = self.params.keys()
        return param_list
        
    def getParamListWithToken(self, token, member):
        """ 
            Return a list of all available parameters for the model 
            
            @param token: parameter prefix
            @param member: data member pointing to internal component
            @return: list of parameters
        """
        param_list = self.params.keys()
        if not self.operateOn == None:
            sub_list = self.operateOn.params.keys()
            for p in sub_list:
                param_list.append("base.%s" % p)
        if not member == None:
            sub_list = member.params.keys()
            for p in sub_list:
                param_list.append("%s.%s" % (token, p))
        return param_list
  
# End of file