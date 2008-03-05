"""Prototype plottable object support.

The main point of this prototype is to provide a clean separation between
the style (plotter details: color, grids, widgets, etc.) and substance
(application details: which information to plot).  Programmers should not be
dictating line colours and plotting symbols.

Unlike the problem of style in CSS or Word, where most paragraphs look
the same, each line on a graph has to be distinguishable from its neighbours.
Our solution is to provide parametric styles, in which a number of
different classes of object (e.g., reflectometry data, reflectometry
theory) representing multiple graph primitives cycle through a colour
palette provided by the underlying plotter.

A full treatment would provide perceptual dimensions of prominence and
distinctiveness rather than a simple colour number.
"""

# Design question: who owns the color?
# Is it a property of the plottable?
# Or of the plottable as it exists on the graph?
# Or if the graph?
# If a plottable can appear on multiple graphs, in some case the
# color should be the same on each graph in which it appears, and
# in other cases (where multiple plottables from different graphs
# coexist), the color should be assigned by the graph.  In any case
# once a plottable is placed on the graph its color should not
# depend on the other plottables on the graph.  Furthermore, if
# a plottable is added and removed from a graph and added again,
# it may be nice, but not necessary, to have the color persist.
#
# The safest approach seems to be to give ownership of color
# to the graph, which will allocate the colors along with the
# plottable.  The plottable will need to return the number of
# colors that are needed.
#
# The situation is less clear for symbols.  It is less clear
# how much the application requires that symbols be unique across
# all plots on the graph.

# Support for ancient python versions
if 'any' not in dir(__builtins__):
    def any(L):
        for cond in L:
            if cond: return True
        return False
    def all(L):
        for cond in L:
            if not cond: return False
        return True

# Graph structure for holding multiple plottables
class Graph:
    """
    Generic plottables graph structure.
    
    Plot styles are based on color/symbol lists.  The user gets to select
    the list of colors/symbols/sizes to choose from, not the application
    developer.  The programmer only gets to add/remove lines from the
    plot and move to the next symbol/color.

    Another dimension is prominence, which refers to line sizes/point sizes.

    Axis transformations allow the user to select the coordinate view
    which provides clarity to the data.  There is no way we can provide
    every possible transformation for every application generically, so
    the plottable objects themselves will need to provide the transformations.
    Here are some examples from reflectometry:
       independent: x -> f(x)
          monitor scaling: y -> M*y
          log:  y -> log(y if y > min else min)
          cos:  y -> cos(y*pi/180)
       dependent:   x -> f(x,y)
          Q4:      y -> y*x^4
          fresnel: y -> y*fresnel(x)
       coordinated: x,y = f(x,y)
          Q:    x -> 2*pi/L (cos(x*pi/180) - cos(y*pi/180))
                y -> 2*pi/L (sin(x*pi/180) + sin(y*pi/180))
       reducing: x,y = f(x1,x2,y1,y2)
          spin asymmetry: x -> x1, y -> (y1 - y2)/(y1 + y2)
          vector net: x -> x1, y -> y1*cos(y2*pi/180)
    Multiple transformations are possible, such as Q4 spin asymmetry

    Axes have further complications in that the units of what are being
    plotted should correspond to the units on the axes.  Plotting multiple
    types on the same graph should be handled gracefully, e.g., by creating
    a separate tab for each available axis type, breaking into subplots,
    showing multiple axes on the same plot, or generating inset plots.
    Ultimately the decision should be left to the user.

    Graph properties such as grids/crosshairs should be under user control,
    as should the sizes of items such as axis fonts, etc.  No direct
    access will be provided to the application.

    Axis limits are mostly under user control.  If the user has zoomed or
    panned then those limits are preserved even if new data is plotted.
    The exception is when, e.g., scanning through a set of related lines
    in which the user may want to fix the limits so that user can compare
    the values directly.  Another exception is when creating multiple
    graphs sharing the same limits, though this case may be important
    enough that it is handled by the graph widget itself.  Axis limits
    will of course have to understand the effects of axis transformations.

    High level plottable objects may be composed of low level primitives.
    Operations such as legend/hide/show copy/paste, etc. need to operate
    on these primitives as a group.  E.g., allowing the user to have a
    working canvas where they can drag lines they want to save and annotate
    them.

    Graphs need to be printable.  A page layout program for entire plots
    would be nice.
    """
    def xaxis(self,name,units):
        """Properties of the x axis.
        """
        if self.prop["xunit"] and units != self.prop["xunit"]:
            pass
            #print "Plottable: how do we handle non-commensurate units"
        self.prop["xlabel"] = "%s (%s)"%(name,units)
        self.prop["xunit"] = units

    def yaxis(self,name,units):
        """Properties of the y axis.
        """
        if self.prop["xunit"] and units != self.prop["xunit"]:
            pass
            #print "Plottable: how do we handle non-commensurate units"
        self.prop["ylabel"] = "%s (%s)"%(name,units)
        self.prop["xunit"] = units
        
    def title(self,name):
        """Graph title
        """
        self.prop["title"] = name
        
    def get(self,key):
        """Get the graph properties"""
        if key=="color":
            return self.color
        elif key == "symbol":
            return self.symbol
        else:
            return self.prop[key]

    def set(self,**kw):
        """Set the graph properties"""
        for key in kw:
            if key == "color":
                self.color = kw[key]%len(self.colorlist)
            elif key == "symbol":
                self.symbol = kw[key]%len(self.symbollist)
            else:
                self.prop[key] = kw[key]

    def isPlotted(self, plottable):
        """Return True is the plottable is already on the graph"""
        if plottable in self.plottables:
            return True
        return False  
        
    def add(self,plottable):
        """Add a new plottable to the graph"""
        # record the colour associated with the plottable
        if not plottable in self.plottables:          
            self.plottables[plottable]=self.color
            self.color += plottable.colors()
        
    def changed(self):
        """Detect if any graphed plottables have changed"""
        return any([p.changed() for p in self.plottables])

    def delete(self,plottable):
        """Remove an existing plottable from the graph"""
        if plottable in self.plottables:
            del self.plottables[plottable]

    def reset(self):
        """Reset the graph."""
        self.color = 0
        self.symbol = 0
        self.prop = {"xlabel":"", "xunit":None,
                     "ylabel":"","yunit":None,
                     "title":""}
        self.plottables = {}

    def _make_labels(self):
        # Find groups of related plottables
        sets = {}
        for p in self.plottables:
            if p.__class__ in sets:
                sets[p.__class__].append(p)
            else:
                sets[p.__class__] = [p]
                
        # Ask each plottable class for a set of unique labels
        labels = {}
        for c in sets:
            labels.update(c.labels(sets[c]))
        
        return labels

    def render(self,plot):
        """Redraw the graph"""
        plot.clear()
        plot.properties(self.prop)
        labels = self._make_labels()
        for p in self.plottables:
            p.render(plot,color=self.plottables[p],symbol=0,label=labels[p])
        plot.render()

    def __init__(self,**kw):
        self.reset()
        self.set(**kw)


# Transform interface definition
# No need to inherit from this class, just need to provide
# the same methods.
class Transform:
    """Define a transform plugin to the plottable architecture.
    
    Transforms operate on axes.  The plottable defines the
    set of transforms available for it, and the axes on which
    they operate.  These transforms can operate on the x axis
    only, the y axis only or on the x and y axes together.
    
    This infrastructure is not able to support transformations
    such as log and polar plots as these require full control
    over the drawing of axes and grids.
    
    A transform has a number of attributes.
    
    name: user visible name for the transform.  This will
        appear in the context menu for the axis and the transform
        menu for the graph.
    type: operational axis.  This determines whether the 
        transform should appear on x,y or z axis context
        menus, or if it should appear in the context menu for
        the graph.
    inventory: (not implemented) 
        a dictionary of user settable parameter names and
        their associated types.  These should appear as keyword 
        arguments to the transform call.  For example, Fresnel 
        reflectivity requires the substrate density:
             { 'rho': type.Value(10e-6/units.angstrom**2) }
        Supply reasonable defaults in the callback so that 
        limited plotting clients work even though they cannot 
        set the inventory.
    """
        
    def __call__(self,plottable,**kwargs):
        """Transform the data.  Whenever a plottable is added
        to the axes, the infrastructure will apply all required
        transforms.  When the user selects a different representation
        for the axes (via menu, script, or context menu), all
        plottables on the axes will be transformed.  The
        plottable should store the underlying data but set
        the standard x,dx,y,dy,z,dz attributes appropriately.
        
        If the call raises a NotImplemented error the dataline 
        will not be plotted.  The associated string will usually
        be 'Not a valid transform', though other strings are possible.
        The application may or may not display the message to the
        user, along with an indication of which plottable was at fault.
        """
        raise NotImplemented,"Not a valid transform"

    # Related issues
    # ==============
    #
    # log scale:
    #    All axes have implicit log/linear scaling options.
    # 
    # normalization:
    #    Want to display raw counts vs detector efficiency correction
    #    Want to normalize by time/monitor/proton current/intensity.
    #    Want to display by eg. counts per 3 sec or counts per 10000 monitor.
    #    Want to divide by footprint (ab initio, fitted or measured).
    #    Want to scale by attenuator values.
    #
    # compare/contrast:
    #    Want to average all visible lines with the same tag, and
    #    display difference from one particular line.  Not a transform
    #    issue?
    #
    # multiline graph:
    #    How do we show/hide data parts.  E.g., data or theory, or 
    #    different polarization cross sections?  One way is with
    #    tags: each plottable has a set of tags and the tags are
    #    listed as check boxes above the plotting area.  Click a
    #    tag and all plottables with that tag are hidden on the
    #    plot and on the legend.
    #
    # nonconformant y-axes:
    #    What do we do with temperature vs. Q and reflectivity vs. Q
    #    on the same graph?
    #
    # 2D -> 1D:
    #    Want various slices through the data.  Do transforms apply
    #    to the sliced data as well?


class Plottable:
    def xaxis(self, name, units):
        self._xaxis = name
        self._xunit = units

    def yaxis(self, name, units):
        self._yaxis = name
        self._yunit = units

    @classmethod
    def labels(cls,collection):
        """
        Construct a set of unique labels for a collection of plottables of 
        the same type.
        
        Returns a map from plottable to name.
        """
        n = len(collection)
        map = {}
        if n > 0:
            basename = str(cls).split('.')[-1]
            if n == 1:
                map[collection[0]] = basename
            else:
                for i in xrange(len(collection)):
                    map[collection[i]] = "%s %d"%(basename,i)
        return map
    ##Use the following if @classmethod doesn't work
    # labels = classmethod(labels)

    def __init__(self):
        pass
    
    def render(self,plot):
        """The base class makes sure the correct units are being used for
        subsequent plottable.  
        
        For now it is assumed that the graphs are commensurate, and if you 
        put a Qx object on a Temperature graph then you had better hope 
        that it makes sense.
        """
        plot.xaxis(self._xaxis, self._xunit)
        plot.yaxis(self._yaxis, self._yunit)
        
    def colors(self):
        """Return the number of colors need to render the object"""
        return 1


class Data1D(Plottable):
    """Data plottable: scatter plot of x,y with errors in x and y.
    """
    
    def __init__(self,x,y,dx=None,dy=None):
        """Draw points specified by x[i],y[i] in the current color/symbol.
        Uncertainty in x is given by dx[i], or by (xlo[i],xhi[i]) if the
        uncertainty is asymmetric.  Similarly for y uncertainty.

        The title appears on the legend.
        The label, if it is different, appears on the status bar.
        """
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy

    def render(self,plot,**kw):
        Plottable.render(self,plot)
        plot.points(self.x,self.y,dx=self.dx,dy=self.dy,**kw)

    def changed(self):
        return False

class Theory1D(Plottable):
    """Theory plottable: line plot of x,y with confidence interval y.
    """
    def __init__(self,x,y,dy=None):
        """Draw lines specified in x[i],y[i] in the current color/symbol.
        Confidence intervals in x are given by dx[i] or by (xlo[i],xhi[i])
        if the limits are asymmetric.
        
        The title is the name that will show up on the legend.
        """
        self.x = x
        self.y = y
 
        self.dy = dy

    def render(self,plot,**kw):
        plot.curve(self.x,self.y,dy=self.dy,**kw)

    def changed(self):
        return False



class Fit1D(Plottable):
    """Fit plottable: composed of a data line plus a theory line.  This
    is treated like a single object from the perspective of the graph,
    except that it will have two legend entries, one for the data and
    one for the theory.

    The color of the data and theory will be shared."""

    def __init__(self,data=None,theory=None):
        self.data=data
        self.theory=theory

    def render(self,plot,**kw):
        self.data.render(plot,**kw)
        self.theory.render(plot,**kw)

    def changed(self):
        return self.data.changed() or self.theory.changed()

######################################################

def sample_graph():
    import numpy as nx
    
    # Construct a simple graph
    if False:
        x = nx.array([1,2,3,4,5,6],'d')
        y = nx.array([4,5,6,5,4,5],'d')
        dy = nx.array([0.2, 0.3, 0.1, 0.2, 0.9, 0.3])
    else:
        x = nx.linspace(0,1.,10000)
        y = nx.sin(2*nx.pi*x*2.8)
        dy = nx.sqrt(100*nx.abs(y))/100
    data = Data1D(x,y,dy=dy)
    data.xaxis('distance', 'm')
    data.yaxis('time', 's')
    graph = Graph()
    graph.title('Walking Results')
    graph.add(data)
    graph.add(Theory1D(x,y,dy=dy))

    return graph

def demo_plotter(graph):
    import wx
    #from pylab_plottables import Plotter
    from mplplotter import Plotter

    # Make a frame to show it
    app = wx.PySimpleApp()
    frame = wx.Frame(None,-1,'Plottables')
    plotter = Plotter(frame)
    frame.Show()

    # render the graph to the pylab plotter
    graph.render(plotter)
    
    class GraphUpdate:
        callnum=0
        def __init__(self,graph,plotter):
            self.graph,self.plotter = graph,plotter
        def __call__(self):
            if self.graph.changed(): 
                self.graph.render(self.plotter)
                return True
            return False
        def onIdle(self,event):
            #print "On Idle checker %d"%(self.callnum)
            self.callnum = self.callnum+1
            if self.__call__(): 
                pass # event.RequestMore()
    update = GraphUpdate(graph,plotter)
    frame.Bind(wx.EVT_IDLE,update.onIdle)
    app.MainLoop()

import sys; print sys.version
if __name__ == "__main__":
    demo_plotter(sample_graph())
    
