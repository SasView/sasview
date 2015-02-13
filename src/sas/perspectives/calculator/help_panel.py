#!/usr/bin/python
"""
Help panel for calculator
"""
import os
import wx
import wx.html as html
from wx.lib.splitter import MultiSplitterWindow
import sas.perspectives.calculator as calculator


class HelpWindow(wx.Frame):
    """
    """
    def __init__(self, parent, id=-1, title="Tool Help", pageToOpen=None, 
                                                    size=(700, 450)):
        wx.Frame.__init__(self, parent, id, title, size=size)
        """
             contains help info
        """
        self.SetTitle(title) 
        splitter = MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        rpanel = wx.Panel(splitter, -1)
        self.lpanel = wx.Panel(splitter, -1, style=wx.BORDER_SUNKEN)
        
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
        headerl = wx.Panel(self.lpanel, -1, size=(-1, 20))
       
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
        self.lhelp = html.HtmlWindow(self.lpanel, -1, style=wx.NO_BORDER)
        self.rhelp = html.HtmlWindow(rpanel, -1, style=wx.NO_BORDER, 
                                     size=(500,-1))
        if pageToOpen != None:
            path = os.path.dirname(pageToOpen)
            self.path = os.path.join(path, "gen_sas_help.html")
        else:
            self.path = calculator.get_data_path(media='media')
       
        page1 = """<html>
            <body>
             <p>Select topic on Menu</p>
            </body>
            </html>"""
        self.rhelp.SetPage(page1)
        page = """<html>
            <body>
            <ul>
            <li><a href ="data_operator_help.html" 
            target ="showframe">Data Operator</a><br></li>
            <li><a href ="sld_calculator_help.html" 
            target ="showframe">SLD Calculator</a><br></li>
            <li><a href ="density_calculator_help.html" 
            target ="showframe">Density Calculator</a><br></li>
            <li><a href ="slit_calculator_help.html" 
            target ="showframe">Slit Size Calculator</a><br></li>
            <li><a href ="kiessig_calculator_help.html" 
            target ="showframe">Kiessig Thickness Calculator</a><br></li>
            <li><a href ="resolution_calculator_help.html" 
            target ="showframe">Resolution Estimator</a><br></li>
            <li><a href ="gen_sas_help.html" 
            target ="showframe">Generic Scattering Calculator</a><br></li>
            <li><a href ="pycrust_help.html" 
            target ="showframe">Python Shell</a><br></li>
            <li><a href ="load_image_help.html" 
            target ="showframe">Image Viewer</a><br></li>
            </ul>
            </body>
            </html>"""

        self.lhelp.SetPage(page)
        self.lhelp.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnLinkClicked)
        if  pageToOpen != None:
            self.rhelp.LoadPage(str(pageToOpen))
        vbox.Add(self.rhelp, 1, wx.EXPAND)
        vboxl.Add(self.lhelp, 1, wx.EXPAND)
        rpanel.SetSizer(vbox)
        self.lpanel.SetSizer(vboxl)
        self.lpanel.SetFocus()
        
        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(splitter, 1, wx.EXPAND)
        splitter.AppendWindow(self.lpanel, 200)
        splitter.AppendWindow(rpanel)
        self.SetSizer(vbox1)
        
        self.splitter = splitter
        self.Centre()
        self.Show(True)
        
    def OnLinkClicked(self, event):
        """
            Function to diplay html page related to the hyperlinktext selected
        """
        link = event.GetLinkInfo().GetHref()
        link = os.path.join(self.path, link)
        self.rhelp.LoadPage(link)
        
        
class ViewApp(wx.App):
    def OnInit(self):
        frame = HelpWindow(None, -1, 'HelpWindow')    
        frame.Show(True)
        self.SetTopWindow(frame)
        return True
        
if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()     
