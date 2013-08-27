"""
    Help dialog
"""
import wx
import wx.html as html
from wx.lib.splitter import MultiSplitterWindow
import os
from wx.lib.scrolledpanel import ScrolledPanel

class HelpPanel(ScrolledPanel):
    def __init__(self, parent, **kwargs):
        ScrolledPanel.__init__(self, parent, **kwargs)
        self.SetupScrolling()


class HelpWindow(wx.Frame):
    """
    """
    def __init__(self, parent, id, title='Fitting Help', pageToOpen=None, size=(850, 540)):
        wx.Frame.__init__(self, parent, id, title, size=size)
        """
        contains help info
        """
        self.Show(False)
        self.SetTitle(title) 
        from sans.perspectives.fitting import get_data_path as fit_path
        fitting_path = fit_path(media='media')
        ico_file = os.path.join(fitting_path, 'ball.ico')
        if os.path.isfile(ico_file):
            self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
        splitter = MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.rpanel = wx.Panel(splitter, -1)
        self.lpanel = wx.Panel(splitter, -1, style=wx.BORDER_SUNKEN)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        header = wx.Panel(self.rpanel, -1)
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
       
        vboxl= wx.BoxSizer(wx.VERTICAL)
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
        self.rhelp = html.HtmlWindow(self.rpanel, -1, style=wx.NO_BORDER, 
                                     size=(500, -1))

        # get the media path
        if pageToOpen != None:
            path = os.path.dirname(pageToOpen)
        else:
            from sans.models import get_data_path as model_path
            # Get models help model_function path
            path = model_path(media='media')

        self.path = os.path.join(path, "model_functions.html")
        self.path_pd = os.path.join(path, "pd_help.html")
        self.path_sm = os.path.join(path, "smear_computation.html")
        self.path_mag = os.path.join(path, "polar_mag_help.html")
        
        _html_file = [("load_data_help.html", "Load a File"),
                      ("single_fit_help.html", "Single Fit"),
                      ("simultaneous_fit_help.html", "Simultaneous Fit"),
                      ("batch_help.html", "Batch Fit"),
                      ("model_use_help.html", "Model Selection"),
                      ("category_manager_help.html", "Model Category Manager"),
                      ("%s" % self.path, "Model Functions"),
                      ("model_editor_help.html", "Custom Model Editor"),
                      ("%s" % self.path_pd, "Polydispersion Distributions"),
                      ("%s" % self.path_sm, "Smear Computation"),
                      ("%s" % self.path_mag, "Polarization/Magnetic Scattering"),
                      ("key_help.html", "Key Combination"),
                      ("status_bar_help.html", "Status Bar Help"),
                      ]
 
        page1 = """<html>
            <body>
             <p>Select topic on Menu</p>
            </body>
            </html>"""
            
        page = """<html>
            <body>
            <ul>
            """
            
        for (p, title) in _html_file:
            pp = os.path.join(fitting_path, p)
            page += """<li><a href ="%s" target="showframe">%s</a><br></li>""" % (pp, title)
        page += """</ul>
                    </body>
                    </html>
                """
                
        self.rhelp.SetPage(page1)
        self.lhelp.SetPage(page)
        self.lhelp.Bind(wx.html.EVT_HTML_LINK_CLICKED, self.OnLinkClicked )
        
        #open the help frame a the current page
        if  pageToOpen != None:
            self.rhelp.LoadPage(str(pageToOpen))
            
        vbox.Add(self.rhelp, 1, wx.EXPAND)
        vboxl.Add(self.lhelp, 1, wx.EXPAND)
        self.rpanel.SetSizer(vbox)
        self.lpanel.SetSizer(vboxl)
        self.lpanel.SetFocus()
        
        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(splitter, 1, wx.EXPAND)
        splitter.AppendWindow(self.lpanel, 200)
        splitter.AppendWindow(self.rpanel)
        self.SetSizer(vbox1)

        self.splitter = splitter
        self.Centre()
        self.Bind(wx.EVT_SIZE, self.on_Size)
        
    def OnButtonClicked(self, event):
        """
        Function to diplay Model html page related to the hyperlinktext selected
        """
        self.rhelp.LoadPage(self.path)
        
    def OnLinkClicked(self, event):
        """
        Function to diplay html page related to the hyperlinktext selected
        """
        link = event.GetLinkInfo().GetHref()
        
        self.rhelp.LoadPage(os.path.abspath(link))
        
    def on_Size(self, event):
        """
        Recover the scroll position On Size
        """
        pos = self.rhelp.GetScrollPos(wx.VERTICAL)
        size = self.GetClientSize()
        self.splitter.SetSize(size)
        self.rhelp.Show(False)
        self.rhelp.ScrollLines(pos)
        self.rhelp.Show(True)
