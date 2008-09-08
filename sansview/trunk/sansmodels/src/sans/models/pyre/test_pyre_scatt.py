#!/usr/bin/env python
from pyre.applications.Script import Script
import sys

#pylint: disable-msg=W0212
#pylint: disable-msg=W0613
  

from pyre.components.Component import Component
class ToyModel(Component):

    has_changed = False

    class Inventory(Component.Inventory):
        import pyre.inventory as pyre_inventory
        
        A = pyre_inventory.float( "A", default = 1.0 )
        B = pyre_inventory.float( "B", default = 2.0 )

    def __call__(self, *args, **kwds):  
        """ Evaluate the model.
            For the real component, evaluate will
            be done through a model object.
        """
        return self.A*10.0*args[0] + self.B
    
    def _configure(self):
        Component._configure(self)
        self.A = self.inventory.A
        self.B = self.inventory.B
        
    def set(self, key, value):
        """ For the real component, we will push the
            values to the underlying model object
            using this method.
        """
        if hasattr(self, key.upper()):
            setattr(self, key.upper(), value)
        else:
            raise ValueError, "ToyModel does not have %s" % key      
        
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
        
    

  
class DemoApp(Script):
    """ Demo application to demonstrate the kind of object manipulations
        our SANS applications will need to do.
    """
    
    class Inventory(Script.Inventory):  
        import pyre.inventory  
        ## We need a model object to manipulate
        model = pyre.inventory.facility('model', default = 'sphere')

    def demo_plotter(self,graph):
        import wx
        from mplplotter import Plotter
    
        # Make a frame to show it
        frame = wx.Frame(None,-1,'Plottables')
        self.plotter = Plotter(frame)
        frame.Show()
    
        # render the graph to the pylab plotter
        graph.render(self.plotter)
        
        def onIdle(event):
            if graph.changed(): 
                graph.render(self.plotter)
                event.RequestMore()
        frame.Bind(wx.EVT_IDLE,onIdle)


    def main(self, *args, **kwds):
        """
            Main loop
        """
        import wx
        app = wx.PySimpleApp()

        print "Model output (%s)= %g" % (self.model.name, self.model(.1))
        
        # Popup graph
        import plottables
        import pyre_plottable
        
        model2 = ToyModel('toymodel','sans')
        model2._configure()
        model2._init()        
        model2.set("A", 4.0)
        
        
        m = pyre_plottable.Model(self.model)
        m2 = pyre_plottable.Model(model2)
        self.graph = plottables.Graph()
        self.graph.title('TEST')
        self.graph.add(m)
        self.graph.add(m2)

        self.demo_plotter(self.graph)
        
        import thread
        thread.start_new(self.console,())
               
        app.MainLoop()
        print "Bye"
        return
  
    def newModelTest(self):
        """ 
            Create a cylinder model directly
        """
        ComponentClass = ScatteringIntensityFactory(CylinderModel)
        self.model._fini()
        self.model = ComponentClass('cylinder')
        self.model._configure()
        self.model._init()        
        
    def newModel(self, model_name):
        """
            Instantiate a new model
            @param model_name: name of new model [string]
        """
        import pyre.inventory
        
        fac = pyre.inventory.facility('model', default = model_name)
        new_model, locator = fac._getDefaultValue(self.inventory)
        new_model._configure()
        new_model._init()
        
        self.model._fini()    
        self.model = new_model
  
    def _configure(self):
        """
            Get the inventory items
        """
        Script._configure(self)
        self.model = self.inventory.model
        return
  
    def console(self):
        # Read user commands
        continue_flag = True
        while(continue_flag):
            command = raw_input(">").lower()
            
            # Quit the application ######################################
            if command.count('q')>0:
                continue_flag = False
                
            # Get the value of a parameter ##############################
            elif command.count('get')>0:
                toks = command.split()
                if len(toks)==2:
                    try: 
                        # Get the attribute with the given name
                        print "%s = %s" % (toks[1], getattr(self.model, toks[1]))
                    except:
                        print sys.exc_value
                else:
                    print "Usage: Get <name of parameter>"

            # Set the value of a parameter ##############################
            elif command.count('set')>0:
                toks = command.split()
                if len(toks)==3:
                    try:
                        self.model.set(toks[1].lstrip().rstrip(), float(toks[2]))
                        print "Model output: ", self.model(1.0)                     
                    except:
                        print sys.exc_value
                else:
                    print "Usage: Set <name of parameter> <value>"
                
            # Set the active model ######################################
            elif command.count('model')>0:
                toks = command.split()
                if len(toks)==2:
                    try:
                        new_name = toks[1].lstrip().rstrip()
                        self.newModel(new_name)
                        print "Model output (%s) = %g" % (new_name, self.model(1.0))
                    except:
                        print sys.exc_value
                else:
                    print "Usage: model <name of the model>"

            # Help ######################################################
            else:
                print "Available commands:"
                print "   get <parameter>"
                print "   set <parameter> <value>"
                print "   model <model name>"
                print "   q"
        
            if self.graph.changed(): 
                self.graph.render(self.plotter)
        
  
# main
if __name__ == '__main__':
    app = DemoApp('sans')
    app.run()
    
  
# version
__id__ = "$Id$"
 
# End of file
