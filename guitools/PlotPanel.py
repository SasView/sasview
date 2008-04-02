import wx.lib.newevent
import matplotlib
matplotlib.interactive(False)
#Use the WxAgg back end. The Wx one takes too long to render
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import os
import fittings
from canvas import FigureCanvas
#TODO: make the plottables interactive

from plottables import Graph
#(FuncFitEvent, EVT_FUNC_FIT) = wx.lib.newevent.NewEvent()
import math,pylab
def show_tree(obj,d=0):
    """Handy function for displaying a tree of graph objects"""
    print "%s%s" % ("-"*d,obj.__class__.__name__)
    if 'get_children' in dir(obj):
        for a in obj.get_children(): show_tree(a,d+1)



class PlotPanel(wx.Panel):
    """
    The PlotPanel has a Figure and a Canvas. OnSize events simply set a 
    flag, and the actually redrawing of the
    figure is triggered by an Idle event.
    """
    def __init__(self, parent, id = -1, color = None,\
        dpi = None, **kwargs):
        wx.Panel.__init__(self, parent, id = id, **kwargs)
        self.parent = parent
        self.figure = Figure(None, dpi)
        #self.figure = pylab.Figure(None, dpi)
        #self.canvas = NoRepaintCanvas(self, -1, self.figure)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.SetColor(color)
        #self.Bind(wx.EVT_IDLE, self._onIdle)
        #self.Bind(wx.EVT_SIZE, self._onSize)
        self._resizeflag = True
        self._SetSize()
        self.subplot = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=.2, bottom=.2)
        self.yscale = 'linear'
        self.xscale = 'linear'
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas,1,wx.EXPAND)
        self.SetSizer(sizer)

        # Graph object to manage the plottables
        self.graph = Graph()
        #self.Bind(EVT_FUNC_FIT, self.onFitRange)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)
        #self.Bind(EVT_PROPERTY, self._onEVT_FUNC_PROPERTY)
        # Define some constants
        self.colorlist = ['b','g','r','c','m','y']
        self.symbollist = ['o','x','^','v','<','>','+','s','d','D','h','H','p']
        #User scale
        self.xscales =""
        self.yscales =""
        # keep track if the previous transformation of x and y in Property dialog
        self.prevXtrans =" "
        self.prevYtrans =" "
        
    def setTrans(self,xtrans,ytrans): 
        """
            @param xtrans: set x transformation on Property dialog
            @param ytrans: set y transformation on Property dialog
        """
        self.prevXtrans =xtrans
        self.prevYtrans =ytrans
        
    def onFitting(self, event): 
        """
            when clicking on linear Fit on context menu , display Fitting Dialog
        """
        list =[]
        list = self.graph.returnPlottable()
        from fitDialog import LinearFit
        print len(list)
        if len(list.keys())>0:
            first_item = list.keys()[0]
            print first_item, list[first_item].__class__.__name__
            dlg = LinearFit( None, first_item, self.onFitDisplay, -1, 'Fitting')
            dlg.ShowModal() 

    def _onProperties(self, event):
        """
            when clicking on Properties on context menu ,The Property dialog is displayed
            The user selects a transformation for x or y value and a new plot is displayed
        """
        from PropertyDialog import Properties
        dial = Properties(self, -1, 'Properties')
        dial.setValues( self.prevXtrans, self.prevYtrans )
        if dial.ShowModal() == wx.ID_OK:
            self.xscales, self.yscales = dial.getValues()
            self._onEVT_FUNC_PROPERTY()
        dial.Destroy()
            
    def toX(self,x):
        """
            This function is used to load value on Plottable.View
            @param x: Float value
            @return x,
        """
        return x
    
    def toX2(self,x):
        """
            This function is used to load value on Plottable.View
            Calculate x^(2)
            @param x: float value
        """
        return math.pow(x,2)
    
    def fromX2(self,x):
         """
             This function is used to load value on Plottable.View
            Calculate square root of x
            @param x: float value
         """
         if not x >=0 :
             raise ValueError, "square root of a negative value "
         else:
             return math.sqrt(x)
         
    def toLogXY(self,x,y):
        """
            This function is used to load value on Plottable.View
            calculate log x
            @param x: float value
        """
        if not x*y > 0:
            raise ValueError, "Log(X*Y)of a negative value "
        else:
            return math.log(x*y)
        
    def fromLogXY(self,x):
        """
            This function is used to load value on Plottable.View
            Calculate e^(x)
            @param x: float value
        """
        return math.exp(x*y)
    
    def set_yscale(self, scale='linear'):
        """
            Set the scale on Y-axis
            @param scale: the scale of y-axis
        """
        self.subplot.set_yscale(scale)
        self.yscale = scale
        
    def get_yscale(self):
        """
             @return: Y-axis scale
        """
        return self.yscale
    
    def set_xscale(self, scale='linear'):
        """
            Set the scale on x-axis
            @param scale: the scale of x-axis
        """
        self.subplot.set_xscale(scale)
        self.xscale = scale
       
    def get_xscale(self):
        """
             @return: x-axis scale
        """
        return self.xscale

    def SetColor(self, rgbtuple):
        """Set figure and canvas colours to be the same"""
        if not rgbtuple:
            rgbtuple = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE).Get()
        col = [c/255.0 for c in rgbtuple]
        self.figure.set_facecolor(col)
        self.figure.set_edgecolor(col)
        self.canvas.SetBackgroundColour(wx.Colour(*rgbtuple))

    def _onSize(self, event):
        self._resizeflag = True

    def _onIdle(self, evt):
        if self._resizeflag:
            self._resizeflag = False
            self._SetSize()
            self.draw()

    def _SetSize(self, pixels = None):
        """
        This method can be called to force the Plot to be a desired size, which defaults to
        the ClientSize of the panel
        """
        if not pixels:
            pixels = self.GetClientSize()
        self.canvas.SetSize(pixels)
        self.figure.set_size_inches(pixels[0]/self.figure.get_dpi(),
        pixels[1]/self.figure.get_dpi())

    def draw(self):
        """Where the actual drawing happens"""
        self.figure.canvas.draw_idle()
        


    def onSaveImage(self, evt):
        #figure.savefig
        print "Save image not implemented"
        path = None
        dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", "*.png", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
            print path
        dlg.Destroy()
        if not path == None:
            self.subplot.figure.savefig(path,dpi=300, facecolor='w', edgecolor='w',
                                        orentation='portrait', papertype=None, format='png')
        
    def onContextMenu(self, event):
        """
            Default context menu for a plot panel
        """
        # Slicer plot popup menu
        slicerpop = wx.Menu()
        slicerpop.Append(313,'&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, 313, self.onSaveImage)
        slicerpop.Append(316, '&Load 1D data file')
       
        wx.EVT_MENU(self, 314, self.onSave1DData)
        wx.EVT_MENU(self, 316, self._onLoad1DData)
        slicerpop.AppendSeparator()
        slicerpop.Append(315, '&Properties')
        
        slicerpop.AppendSeparator()
        slicerpop.Append(317, '&Linear Fit')
       
        wx.EVT_MENU(self, 314, self.onSave1DData)
        wx.EVT_MENU(self, 316, self._onLoad1DData)
        wx.EVT_MENU(self, 315, self._onProperties)
        wx.EVT_MENU(self, 317, self.onFitting)
       
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
        
    
    ## The following is plottable functionality


    def properties(self,prop):
        """Set some properties of the graph.
        
        The set of properties is not yet determined.
        """
        # The particulars of how they are stored and manipulated (e.g., do 
        # we want an inventory internally) is not settled.  I've used a
        # property dictionary for now.
        #
        # How these properties interact with a user defined style file is
        # even less clear.

        # Properties defined by plot
        self.subplot.set_xlabel(r"$%s$" % prop["xlabel"])
        self.subplot.set_ylabel(r"$%s$" % prop["ylabel"])
        self.subplot.set_title(prop["title"])

        # Properties defined by user
        #self.axes.grid(True)

    def clear(self):
        """Reset the plot"""
        
        # TODO: Redraw is brutal.  Render to a backing store and swap in
        # TODO: rather than redrawing on the fly.
        self.subplot.clear()
        self.subplot.hold(True)


    def render(self):
        """Commit the plot after all objects are drawn"""
        # TODO: this is when the backing store should be swapped in.
        from matplotlib.font_manager import FontProperties
        self.subplot.legend(prop=FontProperties(size=10))
        #self.subplot.legend()
        pass

    def xaxis(self,label,units):
        """xaxis label and units.
        
        Axis labels know about units.
        
        We need to do this so that we can detect when axes are not
        commesurate.  Currently this is ignored other than for formatting
        purposes.
        """
        if units != "": label = label + " (" + units + ")"
        self.subplot.set_xlabel(label)
        pass
    
    def yaxis(self,label,units):
        """yaxis label and units."""
        if units != "": label = label + " (" + units + ")"
        self.subplot.set_ylabel(label)
        pass

    def _connect_to_xlim(self,callback):
        """Bind the xlim change notification to the callback"""
        def process_xlim(axes):
            lo,hi = subplot.get_xlim()
            callback(lo,hi)
        self.subplot.callbacks.connect('xlim_changed',process_xlim)
    
    #def connect(self,trigger,callback):
    #    print "PlotPanel.connect???"
    #    if trigger == 'xlim': self._connect_to_xlim(callback)

    def points(self,x,y,dx=None,dy=None,color=0,symbol=0,label=None):
        """Draw markers with error bars"""
        self.subplot.set_yscale('linear')
        self.subplot.set_xscale('linear')
        # Convert tuple (lo,hi) to array [(x-lo),(hi-x)]
        if dx != None and type(dx) == type(()):
            dx = nx.vstack((x-dx[0],dx[1]-x)).transpose()
        if dy != None and type(dy) == type(()):
            dy = nx.vstack((y-dy[0],dy[1]-y)).transpose()

        if dx==None and dy==None:
            h = self.subplot.plot(x,y,color=self._color(color),
                                   marker=self._symbol(symbol),linestyle='',label=label)
        else:
            self.subplot.errorbar(x, y, yerr=dy, xerr=None,
             ecolor=self._color(color), capsize=2,linestyle='', barsabove=False,
             marker=self._symbol(symbol),
             lolims=False, uplims=False,
             xlolims=False, xuplims=False,label=label)
            
        self.subplot.set_yscale(self.yscale)
        self.subplot.set_xscale(self.xscale)

    def curve(self,x,y,dy=None,color=0,symbol=0,label=None):
        """Draw a line on a graph, possibly with confidence intervals."""
        c = self._color(color)
        self.subplot.set_yscale('linear')
        self.subplot.set_xscale('linear')
        
        hlist = self.subplot.plot(x,y,color=c,marker='',linestyle='-',label=label)
        
        self.subplot.set_yscale(self.yscale)
        self.subplot.set_xscale(self.xscale)

    def _color(self,c):
        """Return a particular colour"""
        return self.colorlist[c%len(self.colorlist)]

    def _symbol(self,s):
        """Return a particular symbol"""
        return self.symbollist[s%len(self.symbollist)]
   
    def _onEVT_FUNC_PROPERTY(self):
        """
             Receive the x and y transformation from myDialog,Transforms x and y in View
              and set the scale    
        """ 
        list =[]
        list = self.graph.returnPlottable()
        for item in list:
            if ( self.xscales=="x" ):
                item.transform_x(  self.toX, self.errFunctoX )
                self.set_xscale("linear")
                self.graph.xaxis('\\rm{q} ', 'A^{-1}')
                
            if ( self.xscales=="x^(2)" ):
                item.transform_x(  self.toX2, self.errFuncToX2 )
                self.set_xscale('linear')
                self.graph.xaxis('\\rm{q^{2}} ', 'A^{-2}')
                
            if (self.xscales=="Log(x)" ):
                item.transform_x(  self.toX, self.errFuncToLogX )
                self.set_xscale("log")
                self.graph.xaxis('\\rm{q} ', 'A^{-1}')
                
            if ( self.yscales=="y" ):
                item.transform_y(  self.toX, self.errFunctoX )
                self.set_yscale("linear")
                self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
                
            if ( self.yscales=="Log(y)" ): 
                item.transform_y(  self.toX, self.errFuncToLogX)
                self.set_yscale("log")  
                self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
                
            if ( self.yscales=="y^(2)" ):
                item.transform_y(  self.toX2, self.errFuncToX2 )    
                self.set_yscale("linear")
                self.graph.yaxis("\\rm{Intensity^{2}} ","cm^{-2}")
              
        item.reset_view()
        self.prevXtrans = self.xscales 
        self.prevYtrans = self.yscales  
       
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
    def errFunctoX(self,x,dx=None):
        """
            calculate error of x**2
            @param x: float value
            @param dx: float value
        """
        if dx >=x:
            return 0.9*x
        if dx==None:
             return 0
        return dx
    def errFuncToX2(self,x,dx=None):
        """
            calculate error of x**2
            @param x: float value
            @param dx: float value
        """
        if not dx == None:
            err = 2*x*dx
            if err >= x:
                err = 0.9*x
            return err
        else:
            return 0.0
    def errFuncfromX2(self,x,dx=None):
        """
            calculate error of sqrt(x)
            @param x: float value
            @param dx: float value
        """
        if (x > 0) and (dx != None):
            err = dx/(2*math.sqrt(x))
            if err >= x:
                err = 0.9*x
            return err
        elif x==0.0:
            err = 0.9*x
            return err
        else:
            return 0.0
        
    def errFuncToLogX(self,x,dx=None):
        """
            calculate error of Log(xy)
            @param x: float value
            @param dx: float value
        """
        #if (x != 0) and (dx != None):
        #    err= dx/x
        #elif :
        if x!=0:
            if dx==None:
                err = 1/x
            else:
                err = dx/x
            if err >= x:
                err = 0.9*x
        else:
            err = 0.9*x
        
        return err
        
    def errFuncfromLogXY(self,x,dx=None):
        """
            calculate error of sqrt(x)
            @param x: float value
            @param dx: float value
        """
        if (x > 0) and (dx != None):
            err= math.exp(x)*dx
            if err >= x:
                err = 0.9*x
            return err
        elif x == 0 :
            err = 0.9*x
            return err 
        elif dx == None:
            return 0
        else:
            raise ValueError, "Can't  calculate the error"
                   
    def onFitDisplay(self, plottable):
        """
            Add a new plottable into the graph .In this case this plottable will be used 
            to fit some data
            @param plottable: the plottable to plot
        """
        self.graph.add(plottable)
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
      
    
class NoRepaintCanvas(FigureCanvasWxAgg):
    """We subclass FigureCanvasWxAgg, overriding the _onPaint method, so that
    the draw method is only called for the first two paint events. After that,
    the canvas will only be redrawn when it is resized.
    """
    def __init__(self, *args, **kwargs):
        FigureCanvasWxAgg.__init__(self, *args, **kwargs)
        self._drawn = 0

    def _onPaint(self, evt):
        """
        Called when wxPaintEvt is generated
        """
        if not self._isRealized:
            self.realize()
        if self._drawn < 2:
            self.draw(repaint = False)
            self._drawn += 1
        self.gui_repaint(drawDC=wx.PaintDC(self))
           