#!/usr/bin/python
import wx
import wx.html as html
import os
def help():
    """
        Provide general online help text
        Future work: extend this function to allow topic selection
    """
    info_txt  = "The inversion approach is based on Moore, J. Appl. Cryst. (1980) 13, 168-175.\n\n"
    info_txt += "P(r) is set to be equal to an expansion of base functions of the type "
    info_txt += "phi_n(r) = 2*r*sin(pi*n*r/D_max). The coefficient of each base functions "
    info_txt += "in the expansion is found by performing a least square fit with the "
    info_txt += "following fit function:\n\n"
    info_txt += "chi**2 = sum_i[ I_meas(q_i) - I_th(q_i) ]**2/error**2 + Reg_term\n\n"
    info_txt += "where I_meas(q) is the measured scattering intensity and I_th(q) is "
    info_txt += "the prediction from the Fourier transform of the P(r) expansion. "
    info_txt += "The Reg_term term is a regularization term set to the second derivative "
    info_txt += "d**2P(r)/dr**2 integrated over r. It is used to produce a smooth P(r) output.\n\n"
    info_txt += "The following are user inputs:\n\n"
    info_txt += "   - Number of terms: the number of base functions in the P(r) expansion.\n\n"
    info_txt += "   - Regularization constant: a multiplicative constant to set the size of "
    info_txt += "the regularization term.\n\n"
    info_txt += "   - Maximum distance: the maximum distance between any two points in the system.\n"
     
    return info_txt
    
class HelpDialog(wx.Dialog):
    def __init__(self, parent, id):
      
        wx.Dialog.__init__(self, parent, id, size=(400, 420))
        self.SetTitle("P(r) help") 
        

        vbox = wx.BoxSizer(wx.VERTICAL)

        explanation = help()
           
        label_explain = wx.StaticText(self, -1, explanation, size=(350,320))
            
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
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(700, 450))
        """
             contains help info
        """
        vbox1  = wx.BoxSizer(wx.HORIZONTAL)
        
        lpanel = wx.Panel(self, -1,style=wx.BORDER_SUNKEN)
        rpanel = wx.Panel(self, -1)
        vbox1.Add(lpanel, -1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        vbox1.Add(rpanel, -1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        vbox = wx.BoxSizer(wx.VERTICAL)
        header = wx.Panel(rpanel, -1, size=(-1, 20))
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
        self.rhelp = html.HtmlWindow(rpanel, -1, style=wx.NO_BORDER)
        page1="""<html>
            <body>
             <p>Select topic on Menu</p>
            </body>
            </html>"""
        page="""<html>
            <body>
            <ul>
            <li><a href ="doc/change_scale_help.html" target ="showframe">Change scale</a><br></li>
            <li><a href ="doc/reset_Graph_help.html" target ="showframe">Graph Help</a><br></li>
            <li><a href ="doc/load_data_help.html" target ="showframe">Load a File</a><br></li>
            <li><a href ="doc/simultaneous_fit_help.html" target ="showframe">Simultaneous Fit</a><br></li>
            <li><a href ="doc/single_fit_help.html" target ="showframe">Single Fit</a><br></li>
            <li><a href ="doc/model_use_help.html" target ="showframe">Visualize Model</a><br></li>
            <li><a href ="doc/averaging_help.html" target ="showframe">Data Averaging</a><br></li>
            <li><a href ="doc/model_functions.html" target ="showframe">Model Functions</a><br></li>
            </ul>
            </body>
            </html>"""
        self.rhelp.SetPage(page1)
        self.lhelp.SetPage(page)
        self.lhelp.Bind(wx.html.EVT_HTML_LINK_CLICKED,self.OnLinkClicked )
        
        #'HelpWindow' from menu bar, title=model name from 'More Details' button in model penal
        if title != 'HelpWindow':
            self.rhelp.LoadPage("doc/model_functions.html")
            
        vbox.Add(self.rhelp,1, wx.EXPAND)
        vboxl.Add(self.lhelp, 1, wx.EXPAND)
        rpanel.SetSizer(vbox)
        lpanel.SetSizer(vboxl)
        lpanel.SetFocus()
        
        self.SetSizer(vbox1)
        self.Centre()
        self.Show(True)
        
    def OnButtonClicked(self, event):
        """
            Function to diplay html page related to the hyperlinktext selected
        """
        #link= "doc/modelfunction.html"
        self.rhelp.LoadPage("doc/modelfunction.html")
        
    def OnLinkClicked(self, event):
        """
            Function to diplay html page related to the hyperlinktext selected
        """
        link= event.GetLinkInfo().GetHref()
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
