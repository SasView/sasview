import wx


class HintFitPage(wx.ScrolledWindow):
    """
        This class provide general structure of  fitpanel page
    """
     ## Internal name for the AUI manager
    window_name = "Hint Page"
    ## Title to appear on top of the window
    window_caption = "Hint page "
    
    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent,
                 style= wx.FULL_REPAINT_ON_RESIZE )
        
        msg = "right click on the data when it is highlighted "
        msg += "the select option to fit for futher options"
        self.do_layout()
        
    def do_layout(self):
        """
            Draw the page 
        """
        name="Hint"
        box_description= wx.StaticBox(self, -1,name)
        boxsizer = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        msg = "Load data, then right click on the data, when highlighted,\n"
        msg += "select option to fit for further analysis"
        self.hint_txt = wx.StaticText(self, -1, msg, style=wx.ALIGN_LEFT)
        boxsizer.Add(self.hint_txt, wx.ALL|wx.EXPAND, 20)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(boxsizer )
        self.vbox.Layout()
        self.vbox.Fit(self) 
        self.SetSizer(self.vbox)
        self.SetScrollbars(20,20,25,65)
        self.Layout()
        
    def createMemento(self):
        return 
        
class HelpWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(570, 400))
       
        self.page = HintFitPage(self) 
        self.Centre()
        self.Show(True)
 
if __name__=="__main__":
    app = wx.App()
    HelpWindow(None, -1, 'HelpWindow')
    app.MainLoop()
                