"""
    Test application that uses plottools
    This application uses most of the functionality required by the SAS group
    and should be treated as a test-case representative of that use.
    
    The following is a checklist of functionality to look for while testing:
    
    1- Start the application: the graph should be empty with a white background.
        The status bar should read "This is a data viewer".
    2- From the "File" menu, click "Add data": Three data sets should be plotted:
        - A line called Theory curve, in blue.
        - A series of green points with errors above that line, called Data set 1.
        - A series of red points with errors below that line, called Data set 2.
    3- Hovering over any plotted data will highlight the whole data set or line in yellow.
    4- Left-clicking on the graph and dragging will drag the graph.
    5- Using the mouse wheel will zoom in and out of the graph.
    6- Right-clicking on the graph when no curve is highlighted will 
        pop up the context menu:
        - "Save image" will pop up a save dialog to save an image.
        - "Reset graph" will reset the graph to its original appearance after it
            has been dragged around or zoomed in or out.
        - "Change scale" will pop up a scale dialog with which the axes can
            be transformed. Each transformation choice should work.
    7- Right-clicking on the graph when a curve is highlighted will
        pop up the context menu describe above, to which an item called
        "Linear fit to [name of the data set]" is added.
    
        Selecting a linear fit to data sets 1 or 2 will pop up a fit dialog.
        After fitting, the fit result will appear will be shown in the dialog
        and the fit curve will appear on the plot and should follow the data.
    
        It is possible to interact with the graph when the fit dialog is up.
        
        Selecting a linear fit to the theory curve will produce a message
        on the status bar saying: "Can't fit a theory curve"
     
"""
import wx
from sas.sasgui.plottools.PlotPanel import PlotPanel
from sas.sasgui.plottools.plottables import Data1D, Theory1D, Data2D
import  sys,os
import numpy as np
import random, math


class SASplotpanel(PlotPanel):
    
    def __init__(self, parent, id = -1, color = None,\
        dpi = None, **kwargs):
        PlotPanel.__init__(self, parent, id=id, color=color, dpi=dpi, **kwargs)
        
        # Keep track of the parent Frame
        self.parent = parent
       
        # Internal list of plottable names (because graph 
        # doesn't have a dictionary of handles for the plottables)
        self.plots = {}
        
    def add_plottable(self, plot):
        self.plots[plot.name] = plot
        
        self.graph.add(plot)
        self.graph.xaxis('\\rm{q} ', 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        self.onResetGraph(None)
        
    def add_image(self, plot):
        self.plots[plot.name] = plot
        
        self.graph.add(plot)
        self.graph.xaxis('\\rm{q} ', 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
        #self.onResetGraph(None)
    def plottable_selected(self, id):
        PlotPanel.plottable_selected(self, id)
        if id is not None:
            self.parent.SetStatusText("Hovering over %s" % self.graph.selected_plottable)
        else:
            self.parent.SetStatusText("")
   
    def onContextMenu(self, event):
        """
            Default context menu for a plot panel
        """
        # Slicer plot popup menu
        id = wx.NewId()
        slicerpop = wx.Menu()
        slicerpop.Append(id,'&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, id, self.onSaveImage)
        
        slicerpop.AppendSeparator()
        id = wx.NewId()
        slicerpop.Append(id, '&Change scale')
        wx.EVT_MENU(self, id, self._onProperties)
        
        id = wx.NewId()
        slicerpop.Append(id, '&Reset Graph')
        wx.EVT_MENU(self, id, self.onResetGraph)
        
        id = wx.NewId()
        slicerpop.Append(id, '&Toggle Linear/Log scale')
        wx.EVT_MENU(self, id, self._onToggleScale)
        
        if self.graph.selected_plottable in self.plots:
            # Careful here: Message to status bar
            self.parent.SetStatusText("Fit a line to %s" % self.graph.selected_plottable)
            id = wx.NewId()
            slicerpop.AppendSeparator()
            slicerpop.Append(id, '&Linear Fit to %s' % self.graph.selected_plottable )
            wx.EVT_MENU(self, id, self.onFitting)
       
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
       
    def onFitting(self, event):
        if self.graph.selected_plottable is not None:
            if self.plots[self.graph.selected_plottable].__class__.__name__ == 'Data1D':
                PlotPanel.onFitting(self, event)     
            else:
                self.parent.SetStatusText("Can't fit a theory curve")

class ViewerFrame(wx.Frame):
    """
        Add comment
    """
    def __init__(self, parent, id, title):
        """
            comment
            @param parent: parent panel/container
        """
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(950,850))
        
        # Panel for 1D plot
        self.plotpanel    = SASplotpanel(self, -1, style=wx.RAISED_BORDER)

        # Set up the menu
        self._setup_menus()
      
        # Set up the layout
        self._setup_layout()
                
        # Register the close event so it calls our own method
        wx.EVT_CLOSE(self, self._onClose)
        
       
    def _setup_layout(self):
        """
            Set up the layout
        """
        # Status bar
        self.sb = self.CreateStatusBar()
        self.SetStatusText("This is a data viewer")
        
        # Two columns of panels
        sizer = wx.GridBagSizer(0,0)
        
        sizer.Add(self.plotpanel, (0,0), (1,1),   flag=wx.EXPAND | wx.ALL, border=0)
        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)
   
        self.SetSizer(sizer)
        self.Centre()
                
    def _setup_menus(self):
        """
            Set up the application menus
        """
        
        # Menu
        menubar = wx.MenuBar()
        # File menu
        filemenu = wx.Menu()
        
        # Quit
        id = wx.NewId()
        filemenu.Append(id,'&Quit', 'Exit')
        wx.EVT_MENU(self, id, self._onClose)
        
        # New plot
        id = wx.NewId()
        filemenu.Append(id,'&Add data', 'Add a new curve to the plot')
        wx.EVT_MENU(self, id, self._add_data)
        
        id = wx.NewId()
        filemenu.Append(id,'&Load data 2D', 'load data 2D')
        wx.EVT_MENU(self, id, self.OnLoad)
        # Add sub menus
        menubar.Append(filemenu, '&File')
        self.SetMenuBar(menubar)
        
        
    def OnLoad(self,event):
        path = None
        dlg = wx.FileDialog(None, "Choose a file", os.getcwd(), "", "*", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
            from sas.sascalc.dataloader.loader import  Loader
           
            #Instantiate a loader 
            L=Loader()
            
            #Recieves data 
            try:
                output=L.load(path)
            except:
                raise
           
            newplot=Data2D(image=output.data)
            newplot.setValues(output)
            self.plotpanel.add_image(newplot)
           
                
        dlg.Destroy()
        
    def _onClose(self, event):
        """
        """
        wx.Exit()
        sys.exit()
           
    def _add_data(self, event):
        data_len = 50
        x  = np.zeros(data_len)
        y  = np.zeros(data_len)
        x2  = np.zeros(data_len)
        y2  = np.zeros(data_len)
        dy2  = np.zeros(data_len)
        x3  = np.zeros(data_len)
        y3  = np.zeros(data_len)
        dy3  = np.zeros(data_len)
        for i in range(len(x)):
            x[i] = i
            x2[i] = i-0.1+0.2*random.random()
            x3[i] = i-0.1+0.2*random.random()
            y[i] = 0.5*(i+random.random())
            y2[i] = i+random.random()
            dy2[i] = math.sqrt(y2[i]) 
            y3[i] = 0.3*(i+random.random())
            dy3[i] = math.sqrt(y3[i]) 
            
        newplot = Theory1D(x=x, y=y)
        newplot.name = "Theory curve"
        self.plotpanel.add_plottable(newplot)
        
        newplot = Data1D(x=x2, y=y2, dy=dy2)
        newplot.name = "Data set 1"
        self.plotpanel.add_plottable(newplot)
        
        newplot = Data1D(x=x3, y=y3, dy=dy3)
        newplot.name = "Data set 2"
        self.plotpanel.add_plottable(newplot)
            
  
class ViewApp(wx.App):
    def OnInit(self):
        frame = ViewerFrame(None, -1, 'testView')    
        frame.Show(True)
        self.SetTopWindow(frame)
        
        return True
        

if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()        
            
