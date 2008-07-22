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
#TODO: make the plottables interactive
from binder import BindArtist

DEBUG = False

from plottables import Graph
#(FuncFitEvent, EVT_FUNC_FIT) = wx.lib.newevent.NewEvent()
import math,pylab,re

def show_tree(obj,d=0):
    """Handy function for displaying a tree of graph objects"""
    print "%s%s" % ("-"*d,obj.__class__.__name__)
    if 'get_children' in dir(obj):
        for a in obj.get_children(): show_tree(a,d+1)
     
from unitConverter import UnitConvertion as convertUnit   
def _convertUnit(pow,unit):
    """ 
        Displays the unit with the proper convertion
        @param pow: the user set the power of the unit
        @param unit: the unit of the data
    """ 
    return unit
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
            else:
                lo,hi = math.pow(10.,lo),math.pow(10.,hi)
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
        self.yLabel ="y"
        self.viewModel ="--"
        # keep track if the previous transformation of x and y in Property dialog
        self.prevXtrans ="x"
        self.prevYtrans ="y"
        self.canvas.mpl_connect('scroll_event',self.onWheel)
        #taking care of dragging
        self.canvas.mpl_connect('motion_notify_event',self.onMouseMotion)
        self.canvas.mpl_connect('button_press_event',self.onLeftDown)
        self.canvas.mpl_connect('button_release_event',self.onLeftUp)
        
       
        self.leftdown=False
        self.leftup=False
        self.mousemotion=False
        
        self.axes = [self.subplot]
        
        ## Fit dialog
        self._fit_dialog = None
        
        # Interactor
        self.connect = BindArtist(self.subplot.figure)
        #self.selected_plottable = None

        # new data for the fit 
        self.fit_result = Theory1D(x=[], y=[], dy=None)
        #self.fit_result = Data1D(x=[], y=[],dx=None, dy=None)
        self.fit_result.name = "Fit"
        # For fit Dialog initial display
        self.xmin=0.0
        self.xmax=0.0
        self.xminView=0.0
        self.xmaxView=0.0
        self._scale_xlo = None
        self._scale_xhi = None
        self._scale_ylo = None
        self._scale_yhi = None
        self.Avalue=None
        self.Bvalue=None
        self.ErrAvalue=None
        self.ErrBvalue=None
        self.Chivalue=None
        
        # Dragging info
        self.begDrag=False
        self.xInit=None
        self.yInit=None
        self.xFinal=None
        self.yFinal=None
        
        # Default locations
        self._default_save_location = os.getcwd()        
        
        
    def onLeftDown(self,event): 
        """ left button down and ready to drag"""
        # Check that the LEFT button was pressed
        if event.button == 1:
            self.leftdown=True
            ax = event.inaxes
            if ax != None:
                self.xInit,self.yInit=event.xdata,event.ydata
            
            
    def onLeftUp(self,event): 
        """ Dragging is done """
        # Check that the LEFT button was released
        if event.button == 1:
            self.leftdown=False
            self.mousemotion=False 
            self.leftup=True
      
    def onMouseMotion(self,event): 
        """
            check if the left button is press and the mouse in moving.
            computer delta for x and y coordinates and then calls draghelper 
            to perform the drag
        """
        self.mousemotion=True 
        if self.leftdown==True and self.mousemotion==True:
            
            ax = event.inaxes
            if ax !=None:#the dragging is perform inside the figure
                self.xFinal,self.yFinal=event.xdata,event.ydata
                
                # Check whether this is the first point
                if self.xInit==None:
                    self.xInit = self.xFinal
                    self.yInit = self.yFinal
                    
                xdelta = self.xFinal -self.xInit
                ydelta = self.yFinal -self.yInit
                
                if self.xscale=='log':
                    xdelta = math.log10(self.xFinal) -math.log10(self.xInit)
                if self.yscale=='log':
                    ydelta = math.log10(self.yFinal) -math.log10(self.yInit)
                self.dragHelper(xdelta,ydelta)
              
            else:# no dragging is perform elsewhere
                self.dragHelper(0,0)
                
    def _offset_graph(self):
        """
             Zoom and offset the graph to the last known 
             settings 
        """

        for ax in self.axes:
            if self._scale_xhi is not None and self._scale_xlo is not None:
                ax.set_xlim(self._scale_xlo, self._scale_xhi)
            if self._scale_yhi is not None and self._scale_ylo is not None:
                ax.set_ylim(self._scale_ylo, self._scale_yhi)
            
            
    def dragHelper(self,xdelta,ydelta):
        """ dragging occurs here"""
       
        # Event occurred inside a plotting area
        for ax in self.axes:
            lo,hi= ax.get_xlim()
            #print "x lo %f and x hi %f"%(lo,hi)
            newlo,newhi= lo- xdelta, hi- xdelta
            if self.xscale=='log':
                if lo > 0:
                    newlo= math.log10(lo)-xdelta
                if hi > 0:
                    newhi= math.log10(hi)-xdelta
            if self.xscale=='log':
                self._scale_xlo = math.pow(10,newlo)
                self._scale_xhi = math.pow(10,newhi)
                ax.set_xlim(math.pow(10,newlo),math.pow(10,newhi))
            else:
                self._scale_xlo = newlo
                self._scale_xhi = newhi
                ax.set_xlim(newlo,newhi)
            #print "new lo %f and new hi %f"%(newlo,newhi)
            
            lo,hi= ax.get_ylim()
            #print "y lo %f and y hi %f"%(lo,hi)
            newlo,newhi= lo- ydelta, hi- ydelta
            if self.yscale=='log':
                if lo > 0:
                    newlo= math.log10(lo)-ydelta
                if hi > 0:
                    newhi= math.log10(hi)-ydelta
                #print "new lo %f and new hi %f"%(newlo,newhi)
            if  self.yscale=='log':
                self._scale_ylo = math.pow(10,newlo)
                self._scale_yhi = math.pow(10,newhi)
                ax.set_ylim(math.pow(10,newlo),math.pow(10,newhi))
            else:
                self._scale_ylo = newlo
                self._scale_yhi = newhi
                ax.set_ylim(newlo,newhi)
        self.canvas.draw_idle()
        
        
   
    def resetFitView(self):
        """
             For fit Dialog initial display
        """
        self.xmin=0.0
        self.xmax=0.0
        self.xminView=0.0
        self.xmaxView=0.0
        self._scale_xlo = None
        self._scale_xhi = None
        self._scale_ylo = None
        self._scale_yhi = None
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
                self._scale_xlo = lo
                self._scale_xhi = hi
                ax.set_xlim((lo,hi))

            lo,hi = ax.get_ylim()
            lo,hi = _rescale(lo,hi,step,pt=event.ydata,scale=ax.get_yscale())
            if not self.yscale=='log' or lo>0:
                self._scale_ylo = lo
                self._scale_yhi = hi
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
                    self._scale_xlo = lo
                    self._scale_xhi = hi
                    ax.set_xlim((lo,hi))
            if ydata is not None:
                lo,hi = ax.get_ylim()
                lo,hi = _rescale(lo,hi,step,bal=ydata,scale=ax.get_yscale())
                if not self.yscale=='log' or lo>0:
                    self._scale_ylo = lo
                    self._scale_yhi = hi
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

    def linear_plottable_fit(self, plot): 
        """
            when clicking on linear Fit on context menu , display Fitting Dialog
            @param plot: PlotPanel owning the graph
        """
        from fitDialog import LinearFit
        
        if self._fit_dialog is not None:
            return
        
        self._fit_dialog = LinearFit( None, plot, self.onFitDisplay,self.returnTrans, -1, 'Linear Fit')
        
        # Set the zoom area 
        if self._scale_xhi is not None and self._scale_xlo is not None:
            self._fit_dialog.set_fit_region(self._scale_xlo, self._scale_xhi)
        
        # Register the close event
        self._fit_dialog.register_close(self._linear_fit_close)
        
        # Show a non-model dialog
        self._fit_dialog.Show() 

    def _linear_fit_close(self):
        """
            A fit dialog was closed
        """
        self._fit_dialog = None
        

    def _onProperties(self, event):
        """
            when clicking on Properties on context menu ,The Property dialog is displayed
            The user selects a transformation for x or y value and a new plot is displayed
        """
        if self._fit_dialog is not None:
            self._fit_dialog.Destroy()
            self._fit_dialog = None
            
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
        dlg = wx.FileDialog(self, "Choose a file", self._default_save_location, "", "*.png", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._default_save_location = os.path.dirname(path)
        dlg.Destroy()
        if not path == None:
            self.subplot.figure.savefig(path,dpi=300, facecolor='w', edgecolor='w',
                                        orentation='portrait', papertype=None, format='png')
        
    def onContextMenu(self, event):
        """
            Default context menu for a plot panel
        """
        # Slicer plot popup menu
        id = wx.NewId()
        slicerpop = wx.Menu()
        slicerpop.Append(id,'&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, id, self.onSaveImage)
        
        #id = wx.NewId()
        #slicerpop.Append(id, '&Load 1D data file')
        #wx.EVT_MENU(self, id, self._onLoad1DData)
       
        id = wx.NewId()
        slicerpop.AppendSeparator()
        slicerpop.Append(id, '&Properties')
        wx.EVT_MENU(self, id, self._onProperties)
        
        id = wx.NewId()
        slicerpop.AppendSeparator()
        slicerpop.Append(id, '&Linear Fit')
        wx.EVT_MENU(self, id, self.onFitting)
        
        id = wx.NewId()
        slicerpop.AppendSeparator()
        slicerpop.Append(id, '&Reset Graph')
        wx.EVT_MENU(self, id, self.onResetGraph)
       
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

    def interactive_points(self,x,y,dx=None,dy=None,name='', color=0,symbol=0,label=None):
        """Draw markers with error bars"""
        self.subplot.set_yscale('linear')
        self.subplot.set_xscale('linear')
        
        from plottable_interactor import PointInteractor
        p = PointInteractor(self, self.subplot, zorder=3, id=name)
        p.points(x, y, dx=dx, dy=dy, color=color, symbol=symbol, label=label)
        
        self.subplot.set_yscale(self.yscale)
        self.subplot.set_xscale(self.xscale)

    def interactive_curve(self,x,y,dy=None,name='',color=0,symbol=0,label=None):
        """Draw markers with error bars"""
        self.subplot.set_yscale('linear')
        self.subplot.set_xscale('linear')
        
        from plottable_interactor import PointInteractor
        p = PointInteractor(self, self.subplot, zorder=4, id=name)
        p.curve(x, y, dy=dy, color=color, symbol=symbol, label=label)
        
        self.subplot.set_yscale(self.yscale)
        self.subplot.set_xscale(self.xscale)

    def plottable_selected(self, id):
        """
            Called to register a plottable as selected
        """
        #TODO: check that it really is in the list of plottables
        self.graph.selected_plottable = id

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
            col = self._color(color)
            self.subplot.errorbar(x, y, yerr=dy, xerr=None,
             ecolor=col, capsize=2,linestyle='', barsabove=False,
             mec=col, mfc=col,
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
   
    def _replot(self, remove_fit=False):
        """
            Rescale the plottables according to the latest
            user selection and update the plot
            
            @param remove_fit: Fit line will be removed if True
        """
        self.graph.reset_scale()
        self._onEVT_FUNC_PROPERTY(remove_fit=remove_fit)
        
        #TODO: Why do we have to have the following line?
        self.fit_result.reset_view()
        
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
   
    def _onEVT_FUNC_PROPERTY(self, remove_fit=True):
        """
             Receive the x and y transformation from myDialog,Transforms x and y in View
              and set the scale    
        """ 
        # The logic should be in the right order
        # Delete first, and then get the whole list...
        if remove_fit:
            self.graph.delete(self.fit_result)
            
        list =[]
        list = self.graph.returnPlottable()
        
        # Changing the scale might be incompatible with
        # currently displayed data (for instance, going 
        # from ln to log when all plotted values have
        # negative natural logs). 
        # Go linear and only change the scale at the end.
        self.set_xscale("linear")
        self.set_yscale("linear")
        _xscale = 'linear'
        _yscale = 'linear'
        
        
        for item in list:
            item.setLabel(self.xLabel,self.yLabel)
            if ( self.xLabel=="x" ):
                item.transformX(transform.toX,transform.errToX)
                name, units = item.get_xaxis()
                self.graph._xaxis_transformed("%s" % name,  "%s" % units)
                
                
            if ( self.xLabel=="x^(2)" ):
                item.transformX(transform.toX2,transform.errToX2)
                name, units = item.get_xaxis()
                units=convertUnit(2,units) 
                self.graph._xaxis_transformed("%s^{2}" % name,  "%s" % units)
                
                
            if (self.xLabel=="log10(x)" ):
                item.transformX(transform.toX_pos,transform.errToX_pos)
                _xscale = 'log'
                name, units = item.get_xaxis() 
                self.graph._xaxis_transformed("\log_{10}\ \  (%s)" % name,  "%s" % units)
                
                
            if ( self.yLabel=="ln(y)" ):
                item.transformY(transform.toLogX,transform.errToLogX)
                name, units = item.get_yaxis()
                self.graph._yaxis_transformed("\log\ \ %s" % name,  "%s" % units)
                
                
            if ( self.yLabel=="y" ):
                item.transformY(transform.toX,transform.errToX)
                name, units = item.get_yaxis()
                self.graph._yaxis_transformed("%s" % name,  "%s" % units)
               
                
            if ( self.yLabel=="log10(y)" ): 
                item.transformY(transform.toX_pos,transform.errToX_pos)
                _yscale = 'log'  
                name, units = item.get_yaxis()
                self.graph._yaxis_transformed("\log_{10}\ \ (%s)" % name,  "%s" % units)
                
                
            if ( self.yLabel=="y^(2)" ):
                item.transformY( transform.toX2,transform.errToX2 )    
                name, units = item.get_yaxis()
                units=convertUnit(2,units) 
                self.graph._yaxis_transformed("%s^{2}" % name,  "%s" % units)
                
                
            if ( self.yLabel =="1/y"):
                item.transformY(transform.toOneOverX,transform.errOneOverX )
                name, units = item.get_yaxis()
                units=convertUnit(-1,units)
                self.graph._yaxis_transformed("1/%s" % name,  "%s" % units)
                
            if ( self.yLabel =="1/sqrt(y)" ):
                item.transformY(transform.toOneOverSqrtX,transform.errOneOverSqrtX )
                name, units = item.get_yaxis()
                units=convertUnit(-0.5,units)
                self.graph._yaxis_transformed("1/\sqrt{%s}" %name,  "%s" % units)
                
            if ( self.yLabel =="ln(y*x)"):
                item.transformY( transform.toLogXY,transform.errToLogXY)
                yname, yunits = item.get_yaxis()
                xname, xunits = item.get_xaxis()
                self.graph._yaxis_transformed("\log\ (%s \ \ %s)" % (yname,xname),  "%s%s" % (yunits,xunits))
               
                
            if ( self.yLabel =="ln(y*x^(2))"):
                item.transformY( transform.toLogYX2,transform.errToLogYX2)
                yname, yunits = item.get_yaxis()
                xname, xunits = item.get_xaxis() 
                xunits = convertUnit(2,xunits) 
                self.graph._yaxis_transformed("\log (%s \ \ %s^{2})" % (yname,xname),  "%s%s" % (yunits,xunits))
                
            
            if ( self.yLabel =="ln(y*x^(4))"):
                item.transformY(transform.toLogYX4,transform.errToLogYX4)
                yname, yunits = item.get_yaxis()
                xname, xunits = item.get_xaxis()
                xunits = convertUnit(4,xunits) 
                self.graph._yaxis_transformed("\log (%s \ \ %s^{4})" % (yname,xname),  "%s%s" % (yunits,xunits))
                
            if ( self.viewModel == "Guinier lny vs x^(2)"):
                
                item.transformX(transform.toX2,transform.errToX2)
                name, units = item.get_xaxis()
                units = convertUnit(2,units) 
                self.graph._xaxis_transformed("%s^{2}" % name,  "%s" % units)
                
                
                item.transformY(transform.toLogX,transform.errToLogX )
                name, units = item.get_yaxis()
                self.graph._yaxis_transformed("\log\ \ %s" % name,  "%s" % units)
               
                
            item.transformView()
            
        self.resetFitView()   
        self.prevXtrans = self.xLabel 
        self.prevYtrans = self.yLabel  
        self.graph.render(self)
        
        self.set_xscale(_xscale)
        self.set_yscale(_yscale)
         
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
        self._offset_graph()
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
           