#!/usr/bin/python
import wx
import wx.html as html
from wx.lib.splitter import MultiSplitterWindow
import os

    
class HelpDialog(wx.Dialog):
    """
    """
    def __init__(self, parent, id):
        """
        """
        wx.Dialog.__init__(self, parent, id, size=(400, 420))
        self.SetTitle("Invariant help") 
        
        vbox = wx.BoxSizer(wx.VERTICAL)

        explanation = help()
           
        label_explain = wx.StaticText(self, -1, explanation, size=(350, 320))
            
        vbox.Add(label_explain, 0, wx.ALL|wx.EXPAND, 15)


        static_line = wx.StaticLine(self, -1)
        vbox.Add(static_line, 0, wx.EXPAND, 0)
        
        button_OK = wx.Button(self, wx.ID_OK, "OK")

        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_OK, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)       
        vbox.Add(sizer_button, 0, wx.EXPAND|wx.BOTTOM|wx.TOP, 10)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)
        
        self.Layout()
        self.Centre()

class HelpWindow(wx.Frame):
    """
    """
    def __init__(self, parent, id, title= 'HelpWindow', pageToOpen=None):
        wx.Frame.__init__(self, parent, id, title, size=(820, 450))
        """
        contains help info
        """
        self.SetTitle("Invariant Help") 
        splitter = MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        rpanel = wx.Panel(splitter, -1)
        lpanel = wx.Panel(splitter, -1, style=wx.BORDER_SUNKEN)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        header = wx.Panel(rpanel, -1)
        header.SetBackgroundColour('#6666FF')
        header.SetForegroundColour('WHITE')
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        st = wx.StaticText(header, -1, 'Contents', (5, 5))
        font = st.GetFont()
        font.SetPointSize(10)
        st.SetFont(font)
        hbox.Add(st, 1, wx.TOP | wx.BOTTOM | wx.LEFT, 5)
        header.SetSizer(hbox)
        vbox.Add(header, 0, wx.EXPAND)
       
        vboxl = wx.BoxSizer(wx.VERTICAL)
        headerl = wx.Panel(lpanel, -1, size=(-1, 20))
       
        headerl.SetBackgroundColour('#6666FF')
        headerl.SetForegroundColour('WHITE')
        hboxl = wx.BoxSizer(wx.HORIZONTAL)
        lst = wx.StaticText(headerl, -1, 'Menu', (5, 5))
        fontl = lst.GetFont()
        fontl.SetPointSize(10)
        lst.SetFont(fontl)
        hboxl.Add(lst, 1, wx.TOP | wx.BOTTOM | wx.LEFT, 5)
        headerl.SetSizer(hboxl)
        vboxl.Add(headerl, 0, wx.EXPAND)
        self.lhelp = html.HtmlWindow(lpanel, -1, style=wx.NO_BORDER)
        self.rhelp = html.HtmlWindow(rpanel, -1, style=wx.NO_BORDER, 
                                     size=(500, -1))
        import sas.perspectives.invariant as invariant
        path = invariant.get_data_path(media='media')
        self.path = os.path.join(path,"invariant_help.html")
     
        self.rhelp.LoadPage(self.path)
        page = """<html>
            <body>
            <ul>
            <li><a href ="%s" target ="showframe">Invariant</a><br></li>
            </ul>
            </body>
            </html>""" % self.path
        
        self.lhelp.SetPage(page)
        self.lhelp.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnLinkClicked)
        
        vbox.Add(self.rhelp, 1, wx.EXPAND)
        vboxl.Add(self.lhelp, 1, wx.EXPAND)
        rpanel.SetSizer(vbox)
        lpanel.SetSizer(vboxl)
        lpanel.SetFocus()
        
        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(splitter, 1, wx.EXPAND)
        splitter.AppendWindow(lpanel, 200)
        splitter.AppendWindow(rpanel)
        self.SetSizer(vbox1)
       
        self.Centre()
        self.Show(True)
        
        
    def OnLinkClicked(self, event):
        """
        Function to diplay html page related to the hyperlinktext selected
        """
        self.rhelp.LoadPage(self.path)

class ViewApp(wx.App):
    """
    """
    def OnInit(self):
        """
        """
        frame = HelpWindow(None, -1, 'HelpWindow')    
        frame.Show(True)
        self.SetTopWindow(frame)
        
        return True
        

if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()     
