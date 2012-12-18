"""
Simple Plot Frame : supporting only copy, print, scale
"""
import wx
from sans.guiframe.local_perspectives.plotting.Plotter2D import ModelPanel2D \
                    as PlotPanel
from danse.common.plottools.toolbar import NavigationToolBar
#from danse.common.plottools.PlotPanel import PlotPanel 
from danse.common.plottools.plottables import Graph
from sans.guiframe.utils import PanelMenu

class SimplePlotPanel(PlotPanel):   
    """
    PlotPanel for 1d and 2d
    """ 
    _window_caption = 'Simple Plot'
    def __init__(self, parent, id=-1, color = None,
                 dpi=None, style=wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        """
        Init
        """
        PlotPanel.__init__(self, parent, id=id, style=style, **kwargs)
        self.SetColor(wx.WHITE)
        
        self.toolbar = NavigationToolBar(parent=self, canvas=self.canvas)
        self.toolbar.Show(False)
        self.scale = parent.scale
        self.window_caption = self._window_caption
            
    def draw(self):
        """
        """
        self.resizing = False
        self.canvas.set_resizing(self.resizing)
        self.canvas.draw()
        
    def add_toolbar(self):
        """
        """
        pass   
     
    def onContextMenu(self, event):
        """
        2D plot context menu
        
        :param event: wx context event
        
        """
        slicerpop = PanelMenu()
        slicerpop.set_plots(self.plots)
        slicerpop.set_graph(self.graph)
             
        id = wx.NewId()
        slicerpop.Append(id, '&Save Image')
        wx.EVT_MENU(self, id, self.onSaveImage)
        
        id = wx.NewId()
        slicerpop.Append(id,'&Print Image', 'Print image')
        wx.EVT_MENU(self, id, self.onPrint)
        
        id = wx.NewId()
        slicerpop.Append(id,'&Print Preview', 'Print preview')
        wx.EVT_MENU(self, id, self.onPrinterPreview)

        id = wx.NewId()
        slicerpop.Append(id, '&Copy to Clipboard', 'Copy to the clipboard')
        wx.EVT_MENU(self, id, self.OnCopyFigureMenu)

        if self.data2D.__class__.__name__ != 'NoneType':
            slicerpop.AppendSeparator()
            id = wx.NewId()
            slicerpop.Append(id, '&Toggle Grid On/Off', 'Toggle Grid On/Off')
            wx.EVT_MENU(self, id, self.on_grid_onoff)

        if self.data.__class__.__name__ == 'Data1D':
            slicerpop.AppendSeparator()
            id = wx.NewId()
            slicerpop.Append(id, '&Change Scale')
            wx.EVT_MENU(self, id, self._onProperties)        
        elif self.data2D.__class__.__name__ == 'Data2D':
            slicerpop.AppendSeparator()
            id = wx.NewId()
            slicerpop.Append(id, '&Toggle Linear/Log Scale')
            wx.EVT_MENU(self, id, self._onToggleScale) 
                
        try:
            pos_evt = event.GetPosition()
            pos = self.ScreenToClient(pos_evt)
        except:
            pos_x, pos_y = self.toolbar.GetPositionTuple()
            pos = (pos_x, pos_y + 5)
        self.PopupMenu(slicerpop, pos)
        if self.scale != None:
            self.parent.scale2d = self.scale 
    
    def on_grid_onoff(self, event):
        """
        On grid on/off
        """
        switch = (not self.grid_on)
        self.onGridOnOff(switch) 
                
    def onLeftDown(self, event):
        """
        left button down and ready to drag
        
        """
        # Check that the LEFT button was pressed
        if event.button == 1:
            self.leftdown = True
            ax = event.inaxes
            if ax != None:
                self.xInit, self.yInit = event.xdata, event.ydata
                try:
                    pos_x = float(event.xdata)  # / size_x
                    pos_y = float(event.ydata)  # / size_y
                    pos_x = "%8.3g" % pos_x
                    pos_y = "%8.3g" % pos_y
                    self.position = str(pos_x), str(pos_y)
                    wx.PostEvent(self.parent, StatusEvent(status=self.position))
                except:
                    self.position = None    
             
    def _OnReSize(self, event):   
        """
        On response of the resize of a panel, set axes_visiable False
        """
        self.resizing = False
        if self.x_size != None:
            if self.x_size == self.GetSize():
                self.canvas.set_resizing(self.resizing)
                return
        self.x_size = self.GetSize()

        # Ready for another event
        # Do not remove this Skip. 
        # Otherwise it will get runtime error on wx>=2.9.
        event.Skip() 
        # set the resizing flag
        self.canvas.set_resizing(self.resizing)
        pos_x, pos_y = self.GetPositionTuple()
        if pos_x != 0 and pos_y != 0:
            self.size, _ = self.GetClientSizeTuple()
        self.SetSizer(self.sizer)
        
    def on_set_focus(self, event):
        """
        By pass default boundary blue color drawing
        """
        pass
        
    def on_kill_focus(self, event):
        """
        Reset the panel color
        """
        pass
    
    def show_plot(self, plot):
        """
        Show the plot
        """
        _yaxis, _yunit = plot.get_yaxis()
        _xaxis, _xunit = plot.get_xaxis()
        self.data = plot
        self.plots[plot.name] = plot
        # Axis scales
        if plot.xtransform != None:
            self.xLabel = plot.xtransform
        if plot.ytransform != None:
            self.yLabel = plot.ytransform
        # Init graph
        self.graph = Graph()
        # Add plot: Handles both 1D and 2D
        self.graph.add(self.data)
        self.canvas.set_resizing(False)
        if self.data.__class__.__name__ == 'Data2D':
            self.data2D = plot
        elif self.data.__class__.__name__ == 'Data1D':
            self._onEVT_FUNC_PROPERTY(show=False)
        # Axes
        self.graph.xaxis(_xaxis, _xunit)
        self.graph.yaxis(_yaxis, _yunit)
        self.xaxis(_xaxis, _xunit)
        self.yaxis(_yaxis, _yunit) 
        self.set_xscale(self.xscale)
        self.set_yscale(self.yscale)   
        self.graph.render(self)    
                  
class PlotFrame(wx.Frame):
    """
    Frame for simple plot
    """
    def __init__(self, parent, id, title, scale='log_{10}', 
                 size=wx.Size(550, 470)): 
        """
        comment
        :param parent: parent panel/container
        """
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title,
                          wx.DefaultPosition, size)
        
        # Panel for 1D plot
        self.parent = parent
        self._mgr = None
        self._default_save_location = None
        self.scale = scale
        self.plotpanel = SimplePlotPanel(self, -1)

    def set_plot_unfocus(self):
        """
        un focusing
        """
        pass    
    
    def add_plot(self, plot):
        """
        Add Image
        """
        plotpanel = self.plotpanel
        plotpanel.scale = self.scale
        plotpanel.show_plot(plot)
        
    def set_schedule_full_draw(self, panel, func):
        """
        """
        self.plotpanel.resizing = False
    
    def set_schedule(self, schedule=False): 
        """
        """
        #Not implemented
    
    def disable_app_menu(self, panel):
        """
        """
        #Not implemented 
    
    def get_current_context_menu(self, plotpanel): 
        """
        """
        #Not implemented
        
    def on_close(self, event):
        """
        On Close 
        """
        try:
            self.parent.set_scale2d(self.scale)
            self.parent.on_panel_close(event)
        except:
            self.Destroy()
                          
