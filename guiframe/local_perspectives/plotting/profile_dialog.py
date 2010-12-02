


import wx
import sys
from copy import deepcopy
from danse.common.plottools.plottables import Graph
from Plotter1D import ModelPanel1D as PlotPanel
from sans.guiframe.dataFitting import Theory1D
import pylab

DEFAULT_CMAP = pylab.cm.jet
_BOX_WIDTH = 76
_STATICBOX_WIDTH = 400
_SCALE = 1e-6

#SLD panel size 
if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 570
    PANEL_SIZE = 475
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 610
    PANEL_SIZE = 500
    FONT_VARIANT = 1
    
     
class SLDPanel(wx.Dialog):
    """
    Provides the SLD profile plot panel.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "SLD Profile"
    ## Name to appear on the window title bar
    window_caption = "SLD Profile"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True
    def __init__(self, parent=None, base=None, data=None, axes =['Radius'], 
                 id=-1, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        kwds["size"] = wx.Size(_STATICBOX_WIDTH, PANEL_SIZE) 
        wx.Dialog.__init__(self, parent, id=id, *args, **kwds)

        if data != None:
            #Font size 
            kwds = []
            self.SetWindowVariant(variant=FONT_VARIANT)
            self.SetTitle("Scattering Length Density Profile")
            self.parent = base
            self.data = data
            self.str = self.data.__str__()
            ## when 2 data have the same id override the 1 st plotted
            self.name = self.data.name
            # Panel for plot
            self.plotpanel = SLDplotpanel(self, axes, -1, 
                                             style=wx.TRANSPARENT_WINDOW)
            self.cmap = DEFAULT_CMAP
            ## Create Artist and bind it
            self.subplot = self.plotpanel.subplot
            # layout
            self._setup_layout()
            # plot
            data_plot = deepcopy(self.data)
            data_plot.dy = self._set_dy_data()
            self.newplot = Theory1D(data_plot.x, data_plot.y, data_plot.dy)
            self.newplot.name = 'SLD'
            self.plotpanel.add_image(self.newplot) 
            self.Centre()
            self.Layout()

    def _set_dy_data(self): 
        """
        make fake dy data
        
        :return dy: 
        """
        # set dy as zero
        dy = [0 for y in self.data.y]
        return dy      
    
    def _setup_layout(self):
        """
        Set up the layout
        """
        # panel sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.plotpanel, -1, wx.LEFT|wx.RIGHT, 5)
        sizer.Add((0, 10))
        #-----Button------------1
        id = wx.NewId()
        button_reset = wx.Button(self, id, "Close")
        button_reset.SetToolTipString("Close...")
        button_reset.Bind(wx.EVT_BUTTON, self._close, 
                          id=button_reset.GetId()) 
        sizer.Add(button_reset, 0, wx.LEFT, _STATICBOX_WIDTH - 80) 
        sizer.Add((0, 10))
        self.SetSizerAndFit(sizer)
        self.Centre()
        self.Show(True)
        button_reset.SetFocus()
        
    def _close(self, event):
        """
        Close the dialog
        """
        self.Close(True)

    def _draw_model(self, event):
        """
         on_close, update the model2d plot
        """
        pass

    def get_context_menu(self, graph=None):
        """
        When the context menu of a plot is rendered, the 
        get_context_menu method will be called to give you a 
        chance to add a menu item to the context menu.
        :param graph: the Graph object to which we attach the context menu
        
        :return: a list of menu items with call-back function
        """
        return []
    

class SLDplotpanel(PlotPanel):
    """
    Panel
    """
    def __init__(self, parent, axes=[], id=-1, color=None, dpi=None,
                  **kwargs):
        """
        """
        PlotPanel.__init__(self, parent, id=id, xtransform='x', ytransform='y', 
                           color=color, dpi=dpi, 
                           size=(_STATICBOX_WIDTH, PANEL_SIZE-100), **kwargs)

        # Keep track of the parent Frame
        self.parent = parent
        # Internal list of plottable names (because graph 
        # doesn't have a dictionary of handles for the plottables)
        self.plots = {}
        self.graph = Graph()
        self.axes_label = []
        for idx in range(0, len(axes)):
            self.axes_label.append(axes[idx])
        
    def add_image(self, plot):
        """
        Add image(Theory1D)
        """
        self.plots[plot.name] = plot
        #init graph
        self.gaph = Graph()
        #add plot
        self.graph.add(plot)
        #add axes
        x1_label = self.axes_label[0]
        self.graph.xaxis('\\rm{%s} '% x1_label, 'A')
        self.graph.yaxis('\\rm{SLD} ', 'A^{-2}')
        #draw
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
                
        # For latter scale changes 
        self.plots[plot.name].xaxis('\\rm{%s} '% x1_label, 'A')
        self.plots[plot.name].yaxis('\\rm{SLD} ', 'A^{-2}')

    def on_set_focus(self, event):
        """
        send to the parenet the current panel on focus
        
        """
        #Not implemented
        pass

    def on_kill_focus(self, event):
        """
        reset the panel color
        
        """
        #Not implemented
        pass
    
        
        
class ViewerFrame(wx.Frame):
    """
    Add comment
    """
    def __init__(self, parent, id, title):
        """
        comment
        :param parent: parent panel/container
        """
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, 
                          wx.Size(_STATICBOX_WIDTH, PANEL_SIZE))
        # Panel for 1D plot
        self.plotpanel    = SLDplotpanel(self, -1, style=wx.RAISED_BORDER)

class ViewApp(wx.App):
    def OnInit(self):
        frame = ViewerFrame(None, -1, 'testView')    
        frame.Show(True)
        self.SetTopWindow(frame)
        
        return True
               
if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()     
