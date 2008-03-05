import wx
import matplotlib
matplotlib.interactive(False)
#Use the WxAgg back end. The Wx one takes too long to render
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import os

#from canvas import FigureCanvas
#TODO: make the plottables interactive

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

        self.figure = Figure(None, dpi)
        self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
        self.SetColor(color)
        self._resizeflag = True
        self._SetSize()
        self.subplot = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=.2, bottom=.2)
        self.yscale = 'linear'
        self.xscale = 'linear'
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas,1,wx.EXPAND)
        self.SetSizer(sizer)


        
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)

        # Define some constants
        self.colorlist = ['b','g','r','c','m','y']
        self.symbollist = ['o','x','^','v','<','>','+','s','d','D','h','H','p']

    def set_yscale(self, scale='linear'):
        self.subplot.set_yscale(scale)
        self.yscale = scale.lower()
        
    def get_yscale(self):
        return self.yscale
    
    def set_xscale(self, scale='linear'):
        
        if scale.lower()=='squared':
            self.subplot.set_xscale('linear')
        else:
            self.subplot.set_xscale(scale)
            
        self.xscale = scale.lower()
        
    def get_xscale(self):
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

    #def connect(self,trigger,callback):
    #    print "PlotPanel.connect???"
    #    if trigger == 'xlim': self._connect_to_xlim(callback)

    def points(self,x,y,dx=None,dy=None,color=0,symbol=0,label=None):
        """Draw markers with error bars"""
        # Convert tuple (lo,hi) to array [(x-lo),(hi-x)]
        import numpy as nx
        if dx != None and type(dx) == type(()):
            dx = nx.vstack((x-dx[0],dx[1]-x)).transpose()
        if dy != None and type(dy) == type(()):
            dy = nx.vstack((y-dy[0],dy[1]-y)).transpose()

        if True or dx is None and dy is None:
            h = self.subplot.plot(x,y,color=self._color(color),
                                   marker=self._symbol(symbol))
        else:
            h,hcap,hbar = self.subplot.errorbar(x,y,dy,color=self._color(color),
                                             marker=self._symbol(symbol), 
                                             linestyle='None',
                                             label=label,picker=5)

    def curve(self,x,y,dy=None,color=0,symbol=0,label=None):
        """Draw a line on a graph, possibly with confidence intervals."""
        c = self._color(color)
        self.subplot.set_yscale('linear')
        self.subplot.set_xscale('linear')
        
        x_tmp = x
        if self.xscale == 'squared':
            x_tmp = []
            for x_i in x:
                x_tmp.append(x_i*x_i)
        
        hlist = self.subplot.plot(x_tmp,y,color=c,marker='',linestyle='-',label=label)
        
        self.subplot.set_yscale(self.yscale)
        if not self.xscale == 'squared':
            self.subplot.set_xscale(self.xscale)
        
        if False and dy != None:
            if type(dy) == type(()):
                self.subplot.plot(x,dy[0],color=c,
                               marker='',linestyle='--',label='_nolegend_')
                self.subplot.plot(x,dy[1],color=c,
                               marker='',linestyle='--',label='_nolegend_')
            elif len(dy)==len(y):
                upper = []
                lower = []
                for i in range(len(y)):
                    lower.append(y[i]-dy[i])
                    upper.append(y[i]+dy[i])
                
                self.subplot.plot(x,upper,color=c,
                               marker='',linestyle='--',label='_nolegend_')
                self.subplot.plot(x,lower,color=c,
                               marker='',linestyle='--',label='_nolegend_')

    def _color(self,c):
        """Return a particular colour"""
        return self.colorlist[c%len(self.colorlist)]

    def _symbol(self,s):
        """Return a particular symbol"""
        return self.symbollist[s%len(self.symbollist)]

