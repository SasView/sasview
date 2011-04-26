#!/usr/bin/python

import wx
import wx.html as html
from wx.lib.splitter import MultiSplitterWindow
import os
import sys

    
class HelpWindow(wx.Frame):
    """
    """
    def __init__(self, parent, id, title= 'HelpWindow', pageToOpen=None):
        wx.Frame.__init__(self, parent, id, title, size=(850, 530))
        """
        contains help info
        """
        path = os.path.dirname(__file__)
        temp_path = os.path.join(path,'images')
        ico_file = os.path.join(temp_path,'ball.ico')
        if os.path.isfile(ico_file):
            self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
        else:
            temp_path = os.path.join(os.getcwd(),'images')
            ico_file = os.path.join(temp_path,'ball.ico')
            if os.path.isfile(ico_file):
                self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
            else:
                ico_file = os.path.join(os.path.dirname(os.path.sys.path[0]),
                             'images', 'ball.ico')
                if os.path.isfile(ico_file):
                    self.SetIcon(wx.Icon(ico_file, wx.BITMAP_TYPE_ICO))
                    
        splitter = MultiSplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        rpanel = wx.Panel(splitter, -1)
        lpanel = wx.Panel(splitter, -1,style=wx.BORDER_SUNKEN)
        
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
       
        vboxl= wx.BoxSizer(wx.VERTICAL)
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
        self.rhelp = html.HtmlWindow(rpanel, -1, style=wx.NO_BORDER, size=(500,-1))

        import sans.models as models 
        # get the media path
        path = models.get_data_path(media='media')
        if not os.path.isdir(path):
             path = os.path.dirname(os.path.sys.path[0])
        self.path = os.path.join(path,"model_functions.html")
        self.path_pd = os.path.join(path,"pd_help.html")
        self.path_sm = os.path.join(path,"smear_computation.html")
                    
        page1="""<html>
            <body>
             <p>Select topic on Menu</p>
            </body>
            </html>"""
        
        if not os.path.isfile(os.path.join(path, "change_scale_help.html")):
            path = os.path.join(os.path.dirname(os.path.sys.path[0]), 'media')
        page = """<html>
            <body>
            <ul>
            <li><a href ="%s" target ="showframe">Change Scale</a><br></li>
            """ % str(os.path.join(path, "change_scale_help.html"))
        page += """
            <li><a href ="%s" target ="showframe">Graph Help</a><br></li>
            """ % str(os.path.join(path,  "reset_Graph_help.html"))
        page += """
            <li><a href ="%s" target ="showframe">Status Bar Help</a><br></li>
            """ % str(os.path.join(path,  "status_bar_help.html"))
        page += """
            <li><a href ="%s" target ="showframe">Load a File</a><br></li>
            """ % str(os.path.join(path, "load_data_help.html"))
        page += """
            <li><a href ="%s" 
            target ="showframe">Simultaneous Fit</a><br></li>
            """ % str(os.path.join(path, "simultaneous_fit_help.html"))
        page += """
            <li><a href ="%s" 
            target ="showframe">Single Fit</a><br></li>
            """ % str(os.path.join(path,  "single_fit_help.html"))
        page += """
            <li><a href ="%s" 
            target ="showframe">Visualize Model</a><br></li>
            """ % str(os.path.join(path, "model_use_help.html"))
        page += """
            <li><a href ="%s" 
            target ="showframe">Data Averaging</a><br></li>
            """ % str(os.path.join(path,  "averaging_help.html"))
        page += """
            <li><a href ="%s" target ="showframe">Model Functions</a><br></li>
            """ % str(self.path)
        page += """<li><a href ="%s" target ="showframe">
                Polydispersion Distributions</a><br></li>
                """ % str(self.path_pd)
        page += """
            <li><a href ="%s" target ="showframe">Smear Computation</a><br></li>
            """ % str(self.path_sm)
        page += """<li><a href ="%s" 
        target ="showframe">Key Combination</a><br></li>
            </ul>
            </body>
            </html>""" % str(os.path.join(path,  "key_help.html"))
        
        self.rhelp.SetPage(page1)
        self.lhelp.SetPage(page)
        self.lhelp.Bind(wx.html.EVT_HTML_LINK_CLICKED,self.OnLinkClicked )
        
        #open the help frame a the current page
        if  pageToOpen!= None:
            self.rhelp.LoadPage(str( pageToOpen))
            
        vbox.Add(self.rhelp,1, wx.EXPAND)
        vboxl.Add(self.lhelp, 1, wx.EXPAND)
        rpanel.SetSizer(vbox)
        lpanel.SetSizer(vboxl)
        lpanel.SetFocus()
        
        vbox1 = wx.BoxSizer(wx.HORIZONTAL)
        vbox1.Add(splitter,1,wx.EXPAND)
        splitter.AppendWindow(lpanel, 200)
        splitter.AppendWindow(rpanel)
        self.SetSizer(vbox1)
       
        self.Centre()
        self.Show(True)
        
    def OnButtonClicked(self, event):
        """
        Function to diplay Model html page related to the hyperlinktext selected
        """
        
        self.rhelp.LoadPage(self.path)
        
    def OnLinkClicked(self, event):
        """
        Function to diplay html page related to the hyperlinktext selected
        """
        link= event.GetLinkInfo().GetHref()
        
        self.rhelp.LoadPage(link)
        
"""
Example: ::

    class ViewApp(wx.App):
        def OnInit(self):
            frame = HelpWindow(None, -1, 'HelpWindow')    
            frame.Show(True)
            self.SetTopWindow(frame)
            
            return True
            
    
    if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()  

"""   
