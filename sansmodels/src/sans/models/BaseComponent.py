#!/usr/bin/env python
""" 
    Provide base functionality for all model components
"""

# imports   
import copy
#TO DO: that about a way to make the parameter
#is self return if it is fittable or not  

class BaseComponent:
    """ 
        Basic model component
        
        Since version 0.5.0, basic operations are no longer supported.
    """

    def __init__(self):
        """ Initialization"""
        
        ## Name of the model
        self.name   = "BaseComponent"
        
        ## Parameters to be accessed by client
        self.params = {}
        self.details = {}
        ## Dictionary used to store the dispersity/averaging
        #  parameters of dispersed/averaged parameters.
        self.dispersion = {}
        # string containing information about the model such as the equation
        #of the given model, exception or possible use
        self.description=''
        #list of parameter that can be fitted
        self.fixed= []
           
    def __str__(self):
        """ 
            @return: string representation
        """
        return self.name
   
    def is_fittable(self, par_name):
        """
            Check if a given parameter is fittable or not
            @param par_name: the parameter name to check 
        """
        return par_name.lower() in self.fixed
        #For the future
        #return self.params[str(par_name)].is_fittable()
   
    def run(self, x): return NotImplemented
    def runXY(self, x): return NotImplemented  
    
    def clone(self):
        """ Returns a new object identical to the current object """
        obj = copy.deepcopy(self)
        return self._clone(obj)
    
    def _clone(self, obj):
        """
            Internal utility function to copy the internal
            data members to a fresh copy.
        """
        obj.params     = copy.deepcopy(self.params)
        obj.details    = copy.deepcopy(self.details)
        obj.dispersion = copy.deepcopy(self.dispersion)
        return obj

    def setParam(self, name, value):
        """ 
            Set the value of a model parameter
        
            @param name: name of the parameter
            @param value: value of the parameter
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
        
    def getParam(self, name):
        """ 
            Set the value of a model parameter

            @param name: name of the parameter
        """
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2:
            for item in self.dispersion.keys():
                if item.lower()==toks[0].lower():
                    for par in self.dispersion[item]:
                        if par.lower() == toks[1].lower():
                            return self.dispersion[item][par]
        else:
            # Look for standard parameter
            for item in self.params.keys():
                if item.lower()==name.lower():
                    return self.params[item]
            
        raise ValueError, "Model does not contain parameter %s" % name
     
    def getParamList(self):
        """ 
            Return a list of all available parameters for the model
        """ 
        list = self.params.keys()
        # WARNING: Extending the list with the dispersion parameters
        list.extend(self.getDispParamList())
        return list
    
    def getDispParamList(self):
        """ 
            Return a list of all available parameters for the model
        """ 
        list = []
        
        for item in self.dispersion.keys():
            for p in self.dispersion[item].keys():
                if p not in ['type']:
                    list.append('%s.%s' % (item.lower(), p.lower()))
                    
        return list
    
    # Old-style methods that are no longer used
    def setParamWithToken(self, name, value, token, member): return NotImplemented
    def getParamWithToken(self, name, token, member): return NotImplemented
    def getParamListWithToken(self, token, member): return NotImplemented
    def __add__(self, other): raise ValueError, "Model operation are no longer supported"
    def __sub__(self, other): raise ValueError, "Model operation are no longer supported"
    def __mul__(self, other): raise ValueError, "Model operation are no longer supported"
    def __div__(self, other): raise ValueError, "Model operation are no longer supported"
        
