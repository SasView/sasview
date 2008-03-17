import wx
from PlotPanel import PlotPanel
from plottables import Plottable, Graph, Data1D
import  sys
import numpy
import pylab


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
        self.plotpanel    = PlotPanel(self, -1, style=wx.RAISED_BORDER)

        x  = pylab.arange(0, 25, 1)
        dx = numpy.zeros(len(x))
        y  = x/2.0
        dy = y*0.1

        self.data = Data1D(x=x, y=y, dx=None, dy=dy)

        # Graph        
        self.graph = Graph()
        self.graph.xaxis('\\rm{q} ', 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        self.graph.add(self.data)
        self.graph.render(self.plotpanel)

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
        filemenu.Append(101,'&Quit', 'Exit')
 
        # Add sub menus
        menubar.Append(filemenu, '&File')
         
        self.SetMenuBar(menubar)
        
        # Bind handlers
        wx.EVT_MENU(self, 101, self.Close)
               
    def _onClose(self, event):
        """
        """
        wx.Exit()
        sys.exit()
                   
    def Close(self, event=None):
        """
            Quit the application
        """
        wx.Frame.Close(self)
        wx.Exit()
        sys.exit()
   
  
class ViewApp(wx.App):
    def OnInit(self):
        frame = ViewerFrame(None, -1, 'testView')    
        frame.Show(True)
        self.SetTopWindow(frame)
        
        return True
        

if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()        
            