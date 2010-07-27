
import os 
import wx
from wx.lib.scrolledpanel import ScrolledPanel
from sans.guicomm.events import NewPlotEvent

class HintFitPage(ScrolledPanel):
    """
    This class provide general structure of  fitpanel page
    """
     ## Internal name for the AUI manager
    window_name = "Hint Page"
    ## Title to appear on top of the window
    window_caption = "Hint page "
    
    def __init__(self, parent):
        """
        """
        ScrolledPanel.__init__(self, parent,
                 style=wx.FULL_REPAINT_ON_RESIZE)
        self.SetupScrolling()
        self.parent = parent
        msg = "right click on the data when it is highlighted "
        msg += "the select option to fit for futher options"
        self.do_layout()
       
        
    def set_data(self, list=[], state=None):
        """
        """
        if not list:
            return 
        for data, path in list:
            if data.name not in self.data_cbbox.GetItems():
                self.data_cbbox.Insert(item=data.name, pos=0,
                                    clientData=(data, path))
        if self.data_cbbox.GetCount() >0:
            self.data_cbbox.SetSelection(0)
            self.data_cbbox.Enable()
            self.on_select_data(event=None)
        
    def do_layout(self):
        """
        Draw the page 
        """
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.GridBagSizer(0,0)
        box_description = wx.StaticBox(self, -1, "Hint")
        boxsizer = wx.StaticBoxSizer(box_description, wx.HORIZONTAL)
        boxsizer.SetMinSize((450,100))
        msg  = "    How to link data to the control panel: \n \n"
        msg += "    First load data file from 'File' menu. \n"
        msg += "    Then Highlight and right click on the data plot. \n"
        msg += "    Finally, select 'Select data for fitting' in the pop-up menu. \n"
        self.hint_txt = wx.StaticText(self, -1, msg, style=wx.ALIGN_LEFT)
        self.data_txt = wx.StaticText(self, -1,"Loaded Data: ")
        self.data_cbbox = wx.ComboBox(self, -1, size=(260,20))
        self.data_cbbox.Disable()
        wx.EVT_COMBOBOX(self.data_cbbox ,-1, self.on_select_data) 
        
        sizer1.Add(self.hint_txt)
        ix = 0 
        iy = 0
      
        sizer2.Add(self.data_txt, (iy, ix), (1,1),
                    wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer2.Add( self.data_cbbox, (iy, ix), (1,1),
                    wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        boxsizer.Add(sizer1)
       
        self.vbox.Add(boxsizer,0, wx.ALL, 10)
        self.vbox.Add(sizer2)
        self.SetSizer(self.vbox)
       
    def on_select_data(self, event=None):
        """
        """
        n = self.data_cbbox.GetCurrentSelection()
        data, path = self.data_cbbox.GetClientData(n)
        self.parent.manager.add_fit_page(data=data)
        if data !=None:
            if hasattr(data,"title"):
                title = str(data.title.lstrip().rstrip())
                if title == "":
                    title = str(data.name)
            else:
                title = str(data.name)
            wx.PostEvent(self.parent.parent, NewPlotEvent(plot=data, title=title))
        
    def createMemento(self):
        """
        """
        return 
 