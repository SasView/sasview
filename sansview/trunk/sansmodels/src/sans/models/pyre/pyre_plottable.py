"""
plottables.pyre is a module for registering pyre objects as plottables.

Uses plottables from the reflectivity repository
Plottables require Python 2.5

"""
from plottables import Plottable

def label(model, collection):
    """Build a label mostly unique within a collection"""
    # Find all items in the collection of the same type
    conflicts = []
        
    model_object = model.component
    
    for item in collection:
        if item.component.name == model_object.name:
            conflicts.append(item.component)
        
    # If no conflict, return name
    if len(conflicts) == 0:
        return model_object.name
        
    # Fill out the usual detail from the inventory
    detail = {}
    #for item in model_object.properties():
    #    if not item.name.startswith("help"):
    #        detail[item.name] = item.name
            
    # Check which fields differ (only to the first level!)
    for c in conflicts:
        
        # Loop through the local properties and find differences
        for item in model_object.properties():
            if not item.name.startswith("help"):
                
                # Check common parameters for now
                if hasattr(c, item.name) and hasattr(model_object, item.name):
                    c_val = getattr(c, item.name)
                    o_val = getattr(model_object, item.name)
                    
                    if not c_val == o_val:
                        detail[item.name] = o_val
                            
    # Build a label out of the distinctions
    # TODO: how do we force natural order traversal on detail keys?
    label = model_object.name
    for item in detail:
        label += " %s=%s" % (item, str(detail[item]))

    return label

class Model(Plottable):
    """
    Prototype pyre model plottable.  
    
    Being 'model' rather than 'data' means that it will have certain style 
    attributes (e.g., lines rather than symbols) and respond in certain ways 
    to the callbacks (e.g., by recomputing the model when the limits change).
    
    We have the following attributes:
    
    - inventory: manage user visible state
    - changed(): return true if a replot is required.
    - x,y = data(): return the plottable data.
    
    """
    def __init__(self, component):
        Plottable.__init__(self)
        self.component = component
        self._xaxis, symbol, self._xunit = component.xaxis()
        self._yaxis, symbol, self._yunit = component.yaxis()
        
        self.min = 0.1
        self.max = 1.0
        self.n = 20
        
        self.has_changed = False
        self.dirty = True
        
        # Fill inventory backup
        # Pyre Trait have no way to notify us that
        # it has changed. Hack it for now.
        self.value_dict = {}
        for item in self.component.properties():
            if not item.name.startswith("help"):
                descr = self.component.inventory.getTraitDescriptor(item.name)                
                self.value_dict[item.name] = descr.value

    def __setattr__(self, key, value):
        if key in ["min", "max", "n"]:
            self.has_changed = True
            
        self.__dict__[key] = value
    
    def changed(self):
        """
        Return true if a replot is required.
        
        Queries our inventory and the inventory of our attached
        model to see if any aspects of the model have changed, forcing a
        replot.  Specialized plottables will be able to query the inventory
        intelligently.  
       
        changed() could also be used to provide 'holographic update', where
        the first pass does very coarse sampling, and this gets refined at
        the next idle.  That way we can remain responsive to the mouse while
        expensive calculations go on.
        """
        self.dirty = self.dirty or self.has_changed or self.component.changed()
        return self.dirty
    
    def data(self):
        """
        Return the plottable data.  This will automatically respond to 
        changes in inventory by recalculating.
        
        The plottables graph does not use this function directly, but 
        rather calls it through render.  Later the default render for 1D 
        theory style may want to call back to data.
        """
        if self.dirty:
            import numpy as nx
            self.x = nx.linspace(self.min, self.max, self.n)
            self.y = []
            import math
            for x in self.x:
                self.y.append(math.log(self.component(x)))
            self.dirty = False    
        return self.x, self.y

    def update_xlim(self, lo, hi):
        """
        Record the change in the graph limits.  This updates the xrange
        stored in the model plottable inventory. Later, when the application 
        is idle, obj.changed() will note the change in inventory and ask
        the data to recalculate.
        """
        self.inventory.min = lo
        self.inventory.max = hi
        
    def render(self, plot, **kw):
        """
        Add the appropriate lines to the plot for the component.
        
        The plot interface implements generic styles for particular types
        of data and formalizes the callback mechanism.  See the methods
        available in mplplot for details.
        """
        Plottable.render(self, plot)
        x, y = self.data()
        plot.xaxis(self._xaxis, self._xunit)
        plot.yaxis(self._yaxis, self._yunit)
        plot.curve(x, y, **kw)
        #plot.connect('xlim',self.update_xlim)

    @classmethod
    def labels(cls, collection):
        """Build a label mostly unique within a collection"""
        map = {}
        for item in collection:
            map[item] = label(item, collection)
        return map
