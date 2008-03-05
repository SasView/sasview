import wx
from plottables import Plottable, Graph
from Plotter1D import ModelPanel1D
import Plotter1D

class ViewerFrame(wx.Frame):
    
    def __init__(self, parent, id, title):
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title, wx.DefaultPosition, wx.Size(950,850))
        
        # Panel for 1D plot
        self.slice_plot    = ModelPanel1D(self, -1, style=wx.RAISED_BORDER)

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
        
        # Add panel
        vbox  = wx.BoxSizer(wx.VERTICAL)
        #sizer = wx.GridBagSizer(6,6)
        sizer = wx.GridBagSizer(5,5)
        pnl1 = wx.Panel(self, -1, style=wx.SIMPLE_BORDER)
        vbox.Add(pnl1, 1, wx.EXPAND | wx.ALL)
 
        self.tc1 = wx.TextCtrl(pnl1, -1,style=wx.SIMPLE_BORDER)
        self.tc2 = wx.TextCtrl(pnl1, -1,style=wx.SIMPLE_BORDER)
    
        ix = 0
        iy = 0
        
        #sizer.Add(self.slice_plot,(ix,iy),(1,6),  wx.EXPAND | wx.ALL,5)
        sizer.Add(self.slice_plot,(ix,iy),(1,5),  wx.EXPAND | wx.ALL,5)
        sizer.SetItemMinSize(self.slice_plot, 150,200)
       
        iy+=1
        sizer.Add((20,20),(iy,ix))
        
        ix +=1
        sizer.Add(wx.StaticText(pnl1, -1, 'Constant A'),(iy,ix))
        
        ix+=1
        

        sizer.Add(self.tc1, (iy, ix), (1, 1), wx.RIGHT, 550)
        self.tc1.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        
        ix = 0
        iy +=1
        sizer.Add((20,20),(iy,ix))
        
        ix +=1
        sizer.Add(wx.StaticText(pnl1, -1, 'Constant B'),(iy,ix))
        
        ix +=1
        sizer.Add(self.tc2, (iy, ix),(1,1),  wx.RIGHT, 550)
        self.tc2.Bind(wx.EVT_KILL_FOCUS, self._onTextEnter)
        btn1 = wx.Button(pnl1,  2, 'fit', (50,90))
        self.Bind(wx.EVT_BUTTON, self.slice_plot._onFit)
        ix +=1
        sizer.Add(btn1, (iy, ix), (1, 1), wx.RIGHT, 5)
        #sizer.Add(btn1, (1, 3), (1, 1), wx.RIGHT, 5)
        pnl1.SetSizer(sizer)
        sizer.AddGrowableRow(0)
        sizer.AddGrowableCol(0)
        self.SetSizer(vbox)
        self.Centre()
        self.Bind(wx.EVT_TEXT_ENTER, self._onTextEnter)
        
   
    def _onTextEnter(self,event):
        """
            Send parameters to plot x* cstA + cstB
            
        """
        param_evt = Plotter1D.FunctionParamEvent(cstA=float(self.tc1.GetValue()),\
                                                             cstB=float(self.tc2.GetValue()))
        wx.PostEvent(self, param_evt)
        
        
    def _onClicked(self,event):
        
        self.Bind(event,self.slice_plot._onFit )
        
    def _setup_menus(self):
        """
            Set up the application menus
        """
        
        # Menu
        menubar = wx.MenuBar()
        # File menu
        filemenu = wx.Menu()
        filemenu.Append(104,'&Load 1D data', 'Load a 1D data file')
        filemenu.Append(101,'&Quit', 'Exit')
 
        # Add sub menus
        menubar.Append(filemenu, '&File')
         
        self.SetMenuBar(menubar)
        
        # Bind handlers
        wx.EVT_MENU(self, 101, self.Close)
        wx.EVT_MENU(self, 104, self.slice_plot._onLoad1DData)
               
    def _onClose(self, event):
        import sys
        wx.Exit()
        sys.exit()
                   
    def Close(self, event=None):
        """
            Quit the application
        """
        import sys
        wx.Frame.Close(self)
        wx.Exit()
        sys.exit()
   
  
class ViewApp(wx.App):
    def OnInit(self):
        frame = ViewerFrame(None, -1, 'miniView')    
        frame.Show(True)
        self.SetTopWindow(frame)
        
        return True
        

if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()        
            