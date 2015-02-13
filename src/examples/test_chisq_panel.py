"""
Test application that uses plottools

An application required by the REFL group and mainly test the Chisq class.
    
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
   - 'Save image' will pop up a save dialog to save an image.
   - 'Reset graph' will reset the graph to its original appearance after it
                   has been dragged around or zoomed in or out.
   - 'Change scale' will pop up a scale dialog with which the axes can
                    be transformed. Each transformation choice should work.

"""

import wx
from sas.plottools.PlotPanel import PlotPanel
from sas.plottools.plottables import Plottable, Graph, Data1D, Theory1D
import  sys
import numpy


class ReflPlotPanel(PlotPanel):
    
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
        # Slicer plot popup menu
        id = wx.NewId()
        _menu = wx.Menu()
        _menu.Append(id,'&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, id, self.onSaveImage)
        
        _menu.AppendSeparator()
        id = wx.NewId()
        _menu.Append(id, '&Change scale')
        wx.EVT_MENU(self, id, self._onProperties)
        
        id = wx.NewId()
        _menu.Append(id, '&Reset Graph')
        wx.EVT_MENU(self, id, self.onResetGraph)
 
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(_menu, pos)
       

# ---------------------------------------------------------------
def sample_graph():
    # Construct a simple graph
    if False:
        x = numpy.array([1,2,3,4,5,6],'d')
        y = numpy.array([4,5,26,5,4,-1],'d')
        dy = numpy.array([0.2, 0.3, 0.1, 0.2, 0.9, 0.3])
    else:
        x = numpy.linspace(0,2.0, 50)
        y = numpy.sin(2*numpy.pi*x*2.8)
        dy = numpy.sqrt(100*numpy.abs(y))/100

    from sas.plottools.plottables import Data1D, Theory1D, Chisq , Graph
    data = Data1D(x,y,dy=dy)
    data.xaxis('distance', 'm')
    data.yaxis('time', 's')
    graph = Graph()
    graph.title('Walking Results')
    graph.add(data)
    graph.add( Theory1D(x,y,dy=dy))
    graph.add( Chisq( 1.0 ) )
    return graph


def demo_plotter(graph):
    # Make a frame to show it
    app     = wx.PySimpleApp()
    frame   = wx.Frame(None,-1,'Plottables')
    plotter = ReflPlotPanel(frame)
    frame.Show()

    # render the graph to the pylab plotter
    graph.render(plotter)
    
    app.MainLoop()

    
if __name__ == "__main__":
    pass
    demo_plotter(sample_graph())

            
