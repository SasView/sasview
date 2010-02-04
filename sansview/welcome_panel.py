"""
    Welcome panel for SansView
"""
"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2009, University of Tennessee
"""

import wx
import wx.aui
import wx.lib.hyperlink
import os.path
import os, sys
import local_config as config

#Font size width 
if sys.platform.count("win32")>0:
    FONT_VARIANT = 0
else:
    FONT_VARIANT = 1 
 
class WelcomePanel(wx.aui.AuiNotebook):
    """
        Panel created like about box  as a welcome page
        Shows product name, current version, authors, and link to the product page.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "default"
    ## Name to appear on the window title bar
    window_caption = "Welcome panel"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True
   
    
    def __init__(self,parent, *args, **kwds):
        
        kwds["style"] = wx.aui.AUI_NB_DEFAULT_STYLE
        
        wx.aui.AuiNotebook.__init__(self, parent, *args, **kwds)
        #For sansview the parent is guiframe
        self.parent = parent
       
        welcome_page = WelcomePage(self)
        self.AddPage(page=welcome_page, caption="Welcome")
        
        pageClosedEvent = wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE
        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_close_page)
        self.Center()
    
    def set_manager(self, manager):
        """
            the manager of the panel in this case the application itself
        """
        self.manager = manager
        
    def on_close_page(self, event):
        """
            
        """
        if self.parent is not None:
            self.parent.on_close_welcome_panel()
        event.Veto() 
   
class WelcomePage(wx.Panel):
    """
        Panel created like about box  as a welcome page
        Shows product name, current version, authors, and link to the product page.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "default"
    ## Name to appear on the window title bar
    window_caption = "Welcome panel"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True
   
    
    def __init__(self, *args, **kwds):

        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
       
        wx.Panel.__init__(self, *args, **kwds)
        
        image = os.path.join("images","SVwelcome.png")
        
        self.SetWindowVariant(variant = FONT_VARIANT)
        self.bitmap_logo = wx.StaticBitmap(self, -1, wx.Bitmap(image))
       
        self.label_copyright = wx.StaticText(self, -1, config._copyright)
        self.static_line_1 = wx.StaticLine(self, -1)
        self.label_acknowledgement = wx.StaticText(self, -1, config._acknowledgement)
        
        self.hyperlink_license = wx.StaticText(self, -1, "Comments? Bugs? Requests?")
        self.hyperlink_paper = wx.lib.hyperlink.HyperLinkCtrl(self, -1,
                                         "Send us a ticket",URL=config._license)
        
        verwords = config.__version__.split('.')
        version = '.'.join(verwords[:-1])
        revision = verwords[-1]
        self.label_title = wx.StaticText(self, -1, config.__appname__+ " "+str(config.__version__))#(version))
        self.label_build = wx.StaticText(self, -1, "Build: "+str(config.__version__))
     
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_header = wx.BoxSizer(wx.HORIZONTAL)
        sizer_build = wx.BoxSizer(wx.VERTICAL)
       
        sizer_header.Add(self.bitmap_logo, 0, wx.EXPAND|wx.LEFT, 5)
        
        sizer_build.Add(self.label_acknowledgement,0,wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)  
        sizer_build.Add((5,5))
        sizer_build.Add(self.label_title ,0,wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)  
        sizer_build.Add(self.label_build,0,wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)  
        sizer_build.Add( self.label_copyright,0,wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15) 
        sizer_build.Add((5,5))
        sizer_build.Add( self.hyperlink_license,0,wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15) 
        sizer_build.Add( self.hyperlink_paper,0,wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15) 
        
        sizer_main.Add(sizer_header, 0, wx.TOP|wx.EXPAND, 3)
        sizer_main.Add(self.static_line_1, 0, wx.EXPAND, 0)
        sizer_main.Add(sizer_build,0, wx.BOTTOM|wx.EXPAND, 3)
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Fit()


class ViewApp(wx.App):
    def OnInit(self):
        self.frame = WelcomeFrame(None, -1, "Test App")    
        self.frame.Show(True)
        return True

class WelcomeFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(570, 400))
        WelcomePanel(self)
        self.Centre()
        self.Show(True)
   
if __name__ == "__main__": 
    app = ViewApp(0)
    app.MainLoop()
