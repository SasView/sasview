"""
Test application that uses plottools

An application required by the REFL group and mainly test copy and print.
    
The following is a checklist of functionality to look for while testing:
1- Start the application:
   the graph should have theory curve, experimental data, chisq
   with a white background.

2- Hovering over any plotted data will highlight the whole data set
   or line in yellow.

3- Left-clicking on the graph and dragging will drag the graph.

4- Using the mouse wheel will zoom in and out of the graph.

5- Right-clicking on the graph when no curve is highlighted will 
   pop up the context menu:
   - 'copy image':    copy the bitmap of figure to system clipboard
   - 'print Setup':   setup the size of figure for printing
   - 'print preview': preview printer page
   - 'print':         send figure to system printer.

"""

import wx
from sans.plottools.PlotPanel import PlotPanel
from sans.plottools.plottables import Graph, Data1D, Theory1D
import  sys
sys.platform = 'win95'
import numpy


class TestPlotPanel(PlotPanel):
    
    def __init__(self, parent, id = -1,
                 color = None,
                 dpi = None,
                 **kwargs):
        PlotPanel.__init__(self, parent, id=id, color=color,
                           dpi=dpi, **kwargs)
        
        # Keep track of the parent Frame
        self.parent = parent
        
        # Internal list of plottable names (because graph 
        # doesn't have a dictionary of handles for the plottables)
        self.plots = {}
        
                
    def onContextMenu(self, event):
        """
        Default context menu for a plot panel
        """
        wxID_Copy  = wx.NewId()
        wxID_Print = wx.NewId()
        wxID_PrintPreview = wx.NewId()
        wxID_PrintSetup   = wx.NewId()

        _menu = wx.Menu()
        _menu.Append(wxID_Copy,'&Copy Image', 'Copy image to Clipboard')
        wx.EVT_MENU(self, wxID_Copy, self.OnCopyFigureMenu)
        
        _menu.AppendSeparator()
        _menu.Append(wxID_PrintSetup, '&Print setup')
        wx.EVT_MENU(self, wxID_PrintSetup, self.onPrinterSetup)
        
        _menu.Append(wxID_PrintPreview, '&Print preview ')
        wx.EVT_MENU(self, wxID_PrintPreview, self.onPrinterPreview)

        _menu.Append(wxID_Print, '&Print ')
        wx.EVT_MENU(self, wxID_Print, self.onPrint)
 
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(_menu, pos)
       

# ---------------------------------------------------------------
def sample_graph():
    # Construct a simple graph
    x = numpy.linspace(0,2.0, 50)
    y = numpy.sin(2*numpy.pi*x*2.8)
    dy = numpy.sqrt(100*numpy.abs(y))/100
    
    data = Data1D(x,y,dy=dy)
    data.xaxis('distance', 'm')
    data.yaxis('time', 's')
    
    graph = Graph()
    
    graph.add(data)
    graph.add( Theory1D(x,y,dy=dy))

    graph.title( 'Test Copy and Print Image' )
    return graph


def demo_plotter(graph):
    # Make a frame to show it
    app     = wx.PySimpleApp()
    frame   = wx.Frame(None,-1,'Plottables')
    plotter = TestPlotPanel(frame)
    frame.Show()

    # render the graph to the pylab plotter
    graph.render(plotter)
    
    app.MainLoop()

    
if __name__ == "__main__":
    pass
    demo_plotter(sample_graph())

            
