#!/usr/bin/env python
########################################################################
#
# PDFgui            by DANSE Diffraction group
#                   Simon J. L. Billinge
#                   (c) 2006 trustees of the Michigan State University.
#                   All rights reserved.
#
# File coded by:    Dmitriy Bryndin
#
# See AUTHORS.txt for a list of people who contributed.
# See LICENSE.txt for license information.
#
# Modified by U. Tennessee for DANSE/SANS
########################################################################

# version
__id__ = "$Id: aboutdialog.py 1193 2007-05-03 17:29:59Z dmitriy $"
__revision__ = "$Revision: 1193 $"

import wx
import wx.lib.hyperlink
import random
import os.path
import os
try:
    # Try to find a local config
    import imp
    path = os.getcwd()
    if(os.path.isfile("%s/%s.py" % (path, 'local_config'))) or \
      (os.path.isfile("%s/%s.pyc" % (path, 'local_config'))):
            fObj, path, descr = imp.find_module('local_config', [path])
            config = imp.load_module('local_config', fObj, path, descr)  
    else:
        # Try simply importing local_config
        import local_config as config
except:
    # Didn't find local config, load the default 
    import config

def launchBrowser(url):
    '''Launches browser and opens specified url
    
    In some cases may require BROWSER environment variable to be set up.
    
    @param url: URL to open
    '''
    import webbrowser
    webbrowser.open(url)


class PanelAbout(wx.Panel):
    """
    Panel created like about box  as a welcome page
    Shows product name, current version, authors, and link to the product page.
    Current version is taken from version.py
    """
    
    def __init__(self, *args, **kwds):

        # begin wxGlade: DialogAbout.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
       
        wx.Panel.__init__(self, *args, **kwds)
        
        file_dir = os.path.dirname(__file__)
        
        # Mac doesn't display images with transparent background so well, keep it for Windows
        image = file_dir+"\images\SVwelcome.png"
        
        if os.path.isfile(config._welcome_image):
            image = config._welcome_image     
               
        if os.name == 'nt':
            self.bitmap_logo = wx.StaticBitmap(self, -1, wx.Bitmap(image))
        else:
            self.bitmap_logo = wx.StaticBitmap(self, -1, wx.Bitmap(image))
       
        self.label_copyright = wx.StaticText(self, -1, config._copyright)
       
        self.static_line_1 = wx.StaticLine(self, -1)
        self.label_acknowledgement = wx.StaticText(self, -1, config._acknowledgement)
        
        self.hyperlink_license = wx.StaticText(self, -1, "Comments? Bugs? Requests?")
        self.hyperlink_paper = wx.lib.hyperlink.HyperLinkCtrl(self, -1,
                                         "Send us a ticket",URL=config._license)
        # end wxGlade
        
#      
        # randomly shuffle authors' names
        random.shuffle(config._authors)
        strLabel = ", ".join(config._authors)
        
        # display version and svn revison numbers
        verwords = config.__version__.split('.')
        version = '.'.join(verwords[:-1])
        revision = verwords[-1]
        self.label_title = wx.StaticText(self, -1, config.__appname__+ " "+str(config.__version__))#(version))
        self.label_build = wx.StaticText(self, -1, "Build: "+str(config.__version__))
      
     
        # resize dialog window to fit version number nicely
        if wx.VERSION >= (2,7,2,0):
            size = [self.GetEffectiveMinSize()[0], self.GetSize()[1]]
        else:
            size = [self.GetBestFittingSize()[0], self.GetSize()[1]]
        self.__do_layout()
        self.Fit()



    def __do_layout(self):
        # begin wxGlade: DialogAbout.__do_layout
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
        self.Layout()
        self.Centre()
        # end wxGlade

    

# end of class DialogAbout
class HelpWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(570, 400))
       
        
        self.page = PanelAbout(self)
        
        self.Centre()
        self.Show(True)


   
if __name__=="__main__":
    app = wx.App()
    HelpWindow(None, -1, 'HelpWindow')
    app.MainLoop()
        
