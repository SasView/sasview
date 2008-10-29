#!/usr/bin/python
import wx
import wx.html as html

class HelpWindow(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title, size=(450, 450))
        
        vbox1  = wx.BoxSizer(wx.HORIZONTAL)
        
        #lpanel = wx.Panel(self, -1, style=wx.BORDER_SUNKEN)
        rpanel = wx.Panel(self, -1)
        #vbox1.Add(lpanel, -1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        vbox1.Add(rpanel, -1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        header = wx.Panel(rpanel, -1, size=(-1, 20))
        header = wx.Panel(rpanel, -1)
        header.SetBackgroundColour('#6666FF')
        header.SetForegroundColour('WHITE')
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        st = wx.StaticText(header, -1, 'Help', (5, 5))
        
        font = st.GetFont()
        font.SetPointSize(10)
        st.SetFont(font)
        hbox.Add(st, 1, wx.TOP | wx.BOTTOM | wx.LEFT, 5)
        header.SetSizer(hbox)
        vbox.Add(header, 0, wx.EXPAND)
       

        help = html.HtmlWindow(rpanel, -1, style=wx.NO_BORDER)
        help.LoadPage('help.html')
       
        vbox.Add(help, 1, wx.EXPAND)
        
        rpanel.SetSizer(vbox)
        #lpanel.SetFocus()
        
        self.SetSizer(vbox1)
        self.Centre()
        self.Show(True)

class MyApp(wx.App):
    def OnInit(self):
        
        dialog = HelpWindow(None, -1, 'HelpWindow')
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Destroy()
        
        return 1
   

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()


