#!/usr/bin/env python
""" Pyre Component Model factory
    Factory class that creates pyre component models

    @copyright: Mathieu Doucet (University of Tennessee), for the DANSE project
"""
#pylint: disable-msg=R0904
#pylint: disable-msg=R0912
#pylint: disable-msg=R0201
#pylint: disable-msg=W0142

from pyre.components.Component import Component

def ScatteringIntensityFactory( ModelClass ):
    """ Returns the model if found 
        @param name: class of the model [class]
        @return: the pyre component class [class]
    """

    ## Model object to inspect to write the adapter
    model = ModelClass()
     
    class ScatteringModel(Component):
        """
            Pyre component adapter class for the specified model
        """
        has_changed = False

        class Inventory(Component.Inventory):
            """
                Inventory class for the model adapter
            """
            import pyre.inventory as pyre_inventory
            
            # Create the inventory items from the parameters 
            # of the model
            for name in model.params:
                line = '%s=pyre_inventory.float( name, default = %g )' \
                    % (name, model.params[name])
                exec line in locals()
                continue
        
        def __init__(self, name, facility="sans"):
            """ Initialize the component
                @param name: name of the component object
                @param facility: name of the facility for the object
            """
            Component.__init__(self, name, facility)
            
            ## Model to be manipulated through the adapter
            self._engine = ModelClass()
            return

                    
        def __call__(self, *args, **kwds):  
            """ 
                Evaluate the model
            """
            return self._engine.run(args[0])
            
        def _configure(self):
            """
                Configure the component
            """
            Component._configure(self)
            
            # Add the inventory items to the list of attributes
            for name in model.params: 
                line = "self.%s = self.inventory.%s" % (name, name)
                exec line in locals()
                continue
            return
                    
            
        def _init(self):
            """ 
                Initialization of the underlying model 
            """
            Component._init(self)
            
            # Set the parameters of the underlying model
            for name in model.params: 
                if hasattr(self, name):
                    self.set(name, getattr(self, name))
                else:
                    raise ValueError, "%s not an attribute" % name
            
            return
            
        def set(self, key, value):
            """ 
                Set a parameter of the underlying model 
            """
            
            # Check that the parameter to set is available
            if key not in model.params: 
                raise ValueError, "Model doesn't have param %s" % key
            
            # Make use of  pyre's validator to check the inputs
            cmd = "self.inventory.%s = value" % key
            exec cmd in locals()
            
            # Pass the parameter to the underlying model
            self._engine.setParam(key, value)
            self.has_changed = True
            
        def __setattr__(self, key, value):
            self.__dict__["has_changed"] = True
            return Component.__setattr__(self, key, value)
        
        def changed(self):
            tmp = self.has_changed
            self.has_changed = False    
            return tmp
        
        def xaxis(self): 
            return "time", "t", "s"
        def yaxis(self): 
            return "amplitude", "A", ""
            
            
            
    return ScatteringModel
