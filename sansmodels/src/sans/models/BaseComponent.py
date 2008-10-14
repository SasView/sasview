#!/usr/bin/env python
""" 
    Provide base functionality for all model components
"""

# imports   
import copy
   
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
           
    def __str__(self):
        """ 
            @return: string representation
        """
        return self.name
   
    def run(self, x): return NotImplemented
    def runXY(self, x): return NotImplemented  
    
    def clone(self):
        """ Returns a new object identical to the current object """
        
        obj = copy.deepcopy(self)
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
        

    def _setParam(self, name, value):
        """ 
            Set the value of a model parameter
        
            @param name: name of the parameter
            @param value: value of the parameter
        """
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2 and toks[0] in self.dispersion:
            # Setting a dispersion model parameter
            if toks[1] in self.dispersion[toks[0]]: 
                self.dispersion[toks[0]][toks[1]] = value
                return
            else:
                raise ValueError, "Model does not contain parameter %s.%s" % (toks[0], toks[1])
        
        if name in self.params.keys():
            self.params[name] = value
        else:
            raise ValueError, "Model does not contain parameter %s" % name
        
    def _getParam(self, name):
        """ 
            Set the value of a model parameter

            @param name: name of the parameter
        """
        # Look for dispersion parameters
        toks = name.split('.')
        if len(toks)==2 and toks[0] in self.dispersion:
            # Setting a dispersion model parameter
            if toks[1] in self.dispersion[toks[0]]: 
                return self.dispersion[toks[0]][toks[1]] 
            else:
                raise ValueError, "Model does not contain parameter %s.%s" % (toks[0], toks[1])

        if name in self.params.keys():
            return self.params[name]
        else:
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
        
