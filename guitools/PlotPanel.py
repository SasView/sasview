import wx.lib.newevent
import matplotlib
matplotlib.interactive(False)
#Use the WxAgg back end. The Wx one takes too long to render
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import os
import fittings
import transform
from canvas import FigureCanvas
from matplotlib.widgets import RectangleSelector
from pylab import  gca, gcf
from plottables import Theory1D
#from plottables import Data1D
#TODO: make the plottables interactive

DEBUG = False

from plottables import Graph
#(FuncFitEvent, EVT_FUNC_FIT) = wx.lib.newevent.NewEvent()
import math,pylab,re

def show_tree(obj,d=0):
    """Handy function for displaying a tree of graph objects"""
    print "%s%s" % ("-"*d,obj.__class__.__name__)
    if 'get_children' in dir(obj):
        for a in obj.get_children(): show_tree(a,d+1)
        
def convertUnit(pow,unit):
    """ 
        Displays the unit with the proper convertion
        @param pow: the user set the power of the unit
        @param unit: the unit of the data
    """ 
    toks=re.match("^", unit)
    if not toks==None:
        unitValue= re.split("{",unit)
        unitPower= re.split("}",unitValue[1])
        power= int(unitPower[0])*pow
        word= unitValue[0]+"{"+str(power)+"}"
        if power==1:
            tempUnit=re.split("\^",unitValue[0])
            unit=tempUnit[0]
        else:
            unit = word
    #print"this is unit",unit
    return unit
def _rescale(lo,hi,step,pt=None,bal=None,scale='linear'):
        """
        Rescale (lo,hi) by step, returning the new (lo,hi)
        The scaling is centered on pt, with positive values of step
        driving lo/hi away from pt and negative values pulling them in.
        If bal is given instead of point, it is already in [0,1] coordinates.
    
        This is a helper function for step-based zooming.
        """
        # Convert values into the correct scale for a linear transformation
        # TODO: use proper scale transformers
        loprev = lo
        hiprev = hi
        ptprev = pt
        if scale=='log':
            assert lo >0
            if lo > 0 :
                lo = math.log10(lo)
            if hi > 0 :
                hi = math.log10(hi)
            if pt is not None: pt = math.log10(pt)
        
        # Compute delta from axis range * %, or 1-% if persent is negative
        if step > 0:
            delta = float(hi-lo)*step/100
        else:
            delta = float(hi-lo)*step/(100-step)
    
        # Add scale factor proportionally to the lo and hi values, preserving the
        # point under the mouse
        if bal is None:
            bal = float(pt-lo)/(hi-lo)
        lo = lo - bal*delta
        hi = hi + (1-bal)*delta
    
        # Convert transformed values back to the original scale
        if scale=='log':
            if (lo <= -250) or (hi >= 250):
                lo=loprev
                hi=hiprev
                print "Not possible to scale"
           
            else:
                lo,hi = math.pow(10.,lo),math.pow(10.,hi)
                #assert lo >0,"lo = %g"%lo
                print "possible to scale"
           
            print "these are low and high",lo,hi

        return (lo,hi)


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
        self.xLabel ="x"
        self.yLabel ="log10(y)"
        self.viewModel ="--"
        # keep track if the previous transformation of x and y in Property dialog
        self.prevXtrans =" "
        self.prevYtrans =" "
        self.canvas.mpl_connect('scroll_event',self.onWheel)
        self.axes = [self.subplot]
         # new data for the fit 
        self.fit_result = Theory1D(x=[], y=[], dy=None)
        #self.fit_result = Data1D(x=[], y=[],dx=None, dy=None)
        self.fit_result.name = "Fit"
        # For fit Dialog initial display
        self.xmin=0.0
        self.xmax=0.0
        self.xminView=0.0
        self.xmaxView=0.0
        self.Avalue=None
        self.Bvalue=None
        self.ErrAvalue=None
        self.ErrBvalue=None
        self.Chivalue=None
    def resetFitView(self):
        """
             For fit Dialog initial display
        """
        self.xmin=0.0
        self.xmax=0.0
        self.xminView=0.0
        self.xmaxView=0.0
        self.Avalue=None
        self.Bvalue=None
        self.ErrAvalue=None
        self.ErrBvalue=None
        self.Chivalue=None
        
    def onWheel(self, event):
        """
            Process mouse wheel as zoom events
            @param event: Wheel event
        """
        ax = event.inaxes
        step = event.step

        if ax != None:
            # Event occurred inside a plotting area
            lo,hi = ax.get_xlim()
            lo,hi = _rescale(lo,hi,step,pt=event.xdata,scale=ax.get_xscale())
            if not self.xscale=='log' or lo>0:
                ax.set_xlim((lo,hi))

            lo,hi = ax.get_ylim()
            lo,hi = _rescale(lo,hi,step,pt=event.ydata,scale=ax.get_yscale())
            if not self.yscale=='log' or lo>0:
                ax.set_ylim((lo,hi))
        else:
             # Check if zoom happens in the axes
            xdata,ydata = None,None
            x,y = event.x,event.y
           
            for ax in self.axes:
                insidex,_ = ax.xaxis.contains(event)
                if insidex:
                    xdata,_ = ax.transAxes.inverse_xy_tup((x,y))
                insidey,_ = ax.yaxis.contains(event)
                if insidey:
                    _,ydata = ax.transAxes.inverse_xy_tup((x,y))
            if xdata is not None:
                lo,hi = ax.get_xlim()
                lo,hi = _rescale(lo,hi,step,bal=xdata,scale=ax.get_xscale())
                if not self.xscale=='log' or lo>0:
                    ax.set_xlim((lo,hi))
            if ydata is not None:
                lo,hi = ax.get_ylim()
                lo,hi = _rescale(lo,hi,step,bal=ydata,scale=ax.get_yscale())
                if not self.yscale=='log' or lo>0:
                    ax.set_ylim((lo,hi))
               
        self.canvas.draw_idle()


    def returnTrans(self):
        """
            Return values and labels used by Fit Dialog
        """
        return self.xLabel,self.yLabel, self.Avalue, self.Bvalue,\
                self.ErrAvalue,self.ErrBvalue,self.Chivalue
    
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
        
        if len(list.keys())>0:
            first_item = list.keys()[0]
            dlg = LinearFit( None, first_item, self.onFitDisplay,self.returnTrans, -1, 'Linear Fit')
           
            if (self.xmin !=0.0 )and ( self.xmax !=0.0)\
                and(self.xminView !=0.0 )and ( self.xmaxView !=0.0):
                dlg.setFitRange(self.xminView,self.xmaxView,self.xmin,self.xmax)
            dlg.ShowModal() 

    def _onProperties(self, event):
        """
            when clicking on Properties on context menu ,The Property dialog is displayed
            The user selects a transformation for x or y value and a new plot is displayed
        """
        list =[]
        list = self.graph.returnPlottable()
        if len(list.keys())>0:
            first_item = list.keys()[0]
            if first_item.x !=[]:
                from PropertyDialog import Properties
                dial = Properties(self, -1, 'Properties')
                dial.setValues( self.prevXtrans, self.prevYtrans,self.viewModel )
                if dial.ShowModal() == wx.ID_OK:
                    self.xLabel, self.yLabel,self.viewModel = dial.getValues()
                    if self.viewModel =="Guinier lny vs x^(2)":
                        self.xLabel="x^(2)"
                        self.yLabel="ln(y)"
                        self.viewModel = "--"
                        dial.setValues( self.xLabel, self.yLabel,self.viewModel )
                    self._onEVT_FUNC_PROPERTY()
                dial.Destroy()
           
  
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
        #print "Save image not implemented"
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
        wx.EVT_MENU(self, 316, self._onLoad1DData)
       
        slicerpop.AppendSeparator()
        slicerpop.Append(315, '&Properties')
        wx.EVT_MENU(self, 315, self._onProperties)
        
        slicerpop.AppendSeparator()
        slicerpop.Append(317, '&Linear Fit')
        wx.EVT_MENU(self, 317, self.onFitting)
        
        slicerpop.AppendSeparator()
        slicerpop.Append(318, '&Reset Graph')
        wx.EVT_MENU(self, 318, self.onResetGraph)
       
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
        self.fit_result.x =[]  
        self.fit_result.y =[] 
        self.fit_result.dx=None
        self.fit_result.dy=None
        
        for item in list:
            item.setLabel(self.xLabel,self.yLabel)
            if ( self.xLabel=="x" ):
                item.transformX(transform.toX,transform.errToX)
                self.set_xscale("linear")
                name, units = item.get_xaxis()
                self.graph.xaxis("%s" % name,  "%s" % units)
                
                
            if ( self.xLabel=="x^(2)" ):
                item.transformX(transform.toX2,transform.errToX2)
                self.set_xscale('linear')
                name, units = item.get_xaxis()
                units=convertUnit(2,units) 
                self.graph.xaxis("%s^{2}" % name,  "%s" % units)
                
                
            if (self.xLabel=="log10(x)" ):
                item.transformX(transform.toX,transform.errToX)
                self.set_xscale("log")
                name, units = item.get_xaxis() 
                self.graph.xaxis("\log_{10}\ \  (%s)" % name,  "%s" % units)
                
                
            if ( self.yLabel=="ln(y)" ):
                item.transformY(transform.toLogX,transform.errToLogX)
                self.set_yscale("linear")
                name, units = item.get_yaxis()
                self.graph.yaxis("log\ \ %s" % name,  "%s" % units)
                
                
            if ( self.yLabel=="y" ):
                item.transformY(transform.toX,transform.errToX)
                self.set_yscale("linear")
                name, units = item.get_yaxis()
                self.graph.yaxis("%s" % name,  "%s" % units)
               
                
            if ( self.yLabel=="log10(y)" ): 
                item.transformY(transform.toX,transform.errToX)
                self.set_yscale("log")  
                name, units = item.get_yaxis()
                self.graph.yaxis("\log_{10}\ \ (%s)" % name,  "%s" % units)
                
                
            if ( self.yLabel=="y^(2)" ):
                item.transformY( transform.toX2,transform.errToX2 )    
                self.set_yscale("linear")
                name, units = item.get_yaxis()
                units=convertUnit(2,units) 
                self.graph.yaxis("%s^{2}" % name,  "%s" % units)
                
                
            if ( self.yLabel =="1/y"):
                item.transformY(transform.toOneOverX,transform.errOneOverX )
                self.set_yscale("linear")
                name, units = item.get_yaxis()
                units=convertUnit(-1,units)
                self.graph.yaxis("1/%s" % name,  "%s" % units)
                
            if ( self.yLabel =="1/sqrt(y)" ):
                item.transformY(transform.toOneOverSqrtX,transform.errOneOverSqrtX )
                self.set_yscale("linear")
                name, units = item.get_yaxis()
                units=convertUnit(-1,units)
                self.graph.yaxis("1/\sqrt{%s}" %name,  "%s" % units)
                
            if ( self.yLabel =="ln(y*x)"):
                item.transformY( transform.toLogXY,transform.errToLogXY)
                self.set_yscale("linear")
                yname, yunits = item.get_yaxis()
                xname, xunits = item.get_xaxis()
                self.graph.yaxis("log\ (%s \ \ %s)" % (yname,xname),  "%s%s" % (yunits,xunits))
               
                
            if ( self.yLabel =="ln(y*x^(2))"):
                item.transformY( transform.toLogYX2,transform.errToLogYX2)
                self.set_yscale("linear")
                yname, yunits = item.get_yaxis()
                xname, xunits = item.get_xaxis() 
                xunits = convertUnit(2,xunits) 
                self.graph.yaxis("Log (%s \ \ %s)" % (yname,xname),  "%s%s" % (yunits,xunits))
                
            
            if ( self.yLabel =="ln(y*x^(4))"):
                item.transformY(transform.toLogYX4,transform.errToLogYX4)
                self.set_yscale("linear")
                yname, yunits = item.get_yaxis()
                xname, xunits = item.get_xaxis()
                xunits = convertUnit(4,xunits) 
                self.graph.yaxis("Log (%s \ \ %s)" % (yname,xname),  "%s%s" % (yunits,xunits))
                
            if ( self.viewModel == "Guinier lny vs x^(2)"):
                
                item.transformX(transform.toX2,transform.errToX2)
                self.set_xscale('linear')
                name, units = item.get_xaxis()
                units = convertUnit(2,units) 
                self.graph.xaxis("%s^{2}" % name,  "%s" % units)
                
                
                item.transformY(transform.toLogX,transform.errToLogX )
                self.set_yscale("linear")
                name, units = item.get_yaxis()
                self.graph.yaxis("$Log %s$" % name,  "%s" % units)
               
                
            item.transformView()
            
         
        self.resetFitView()   
        self.prevXtrans = self.xLabel 
        self.prevYtrans = self.yLabel  
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
        
        
    
    def onFitDisplay(self, tempx,tempy,xminView,xmaxView,xmin,xmax,func):
        """
            Add a new plottable into the graph .In this case this plottable will be used 
            to fit some data
            @param tempx: The x data of fit line
            @param tempy: The y data of fit line
            @param xminView: the lower bound of fitting range
            @param xminView: the upper bound of  fitting range
            @param xmin: the lowest value of data to fit to the line
            @param xmax: the highest value of data to fit to the line
        """
        # Saving value to redisplay in Fit Dialog when it is opened again
        self.Avalue,self.Bvalue,self.ErrAvalue,self.ErrBvalue,self.Chivalue=func
        self.xminView=xminView
        self.xmaxView=xmaxView
        self.xmin= xmin
        self.xmax= xmax
        #In case need to change the range of data plotted
        list =[]
        list = self.graph.returnPlottable()
        for item in list:
            #item.onFitRange(xminView,xmaxView)
            item.onFitRange(None,None)
        
        # Create new data plottable with result
        self.fit_result.x =[] 
        self.fit_result.y =[]
        self.fit_result.x =tempx  
        self.fit_result.y =tempy     
        self.fit_result.dx=None
        self.fit_result.dy=None
        #Load the view with the new values
        self.fit_result.reset_view()
        # Add the new plottable to the graph 
        self.graph.add(self.fit_result) 
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
        
   
    def onResetGraph(self,event):
        """
            Reset the graph by plotting the full range of data 
        """
        list =[]
        list = self.graph.returnPlottable()
        for item in list:
            item.onReset()
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
           