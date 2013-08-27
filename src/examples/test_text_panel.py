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
from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.plottables import Plottable, Graph, Data1D, Theory1D
import  sys
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
        self.PopupMenu(slicerpop, pos)
       

# ---------------------------------------------------------------
def sample_graph():
    # Construct a simple graph

    from danse.common.plottools.plottables import Text, Graph
    
    T1 = Text(text='text example 1', xpos=0.2, ypos=0.2)
    T2 = Text(text='text example 2', xpos=0.5, ypos=0.5)
    T3 = Text(text=r'$\chi^2=1.2$', xpos=0.8, ypos=0.8)
    
    graph = Graph()
    graph.title( 'Test Text Class' )
    graph.add( T1 )
    graph.add( T2 ) 
    graph.add( T3 )
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

            
