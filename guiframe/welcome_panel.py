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
    '''"About" Dialog
    
    Shows product name, current version, authors, and link to the product page.
    Current version is taken from version.py
    '''
    
    def __init__(self, *args, **kwds):

        # begin wxGlade: DialogAbout.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
       
        wx.Panel.__init__(self, *args, **kwds)
        
        file_dir = os.path.dirname(__file__)
        
        # Mac doesn't display images with transparent background so well, keep it for Windows
        image = file_dir+"/images/angles_flat.png"
        if os.path.isfile(config._corner_image):
            image = config._corner_image

        if os.name == 'nt':
            self.bitmap_logo = wx.StaticBitmap(self, -1, wx.Bitmap(image))
        else:
            self.bitmap_logo = wx.StaticBitmap(self, -1, wx.Bitmap(image))
        self.bitmap_logo.SetFocus()
        self.label_title = wx.StaticText(self, -1, config.__appname__)
        self.label_version = wx.StaticText(self, -1, "")
        self.label_build = wx.StaticText(self, -1, "Build:")
        self.label_svnrevision = wx.StaticText(self, -1, "")
        self.label_copyright = wx.StaticText(self, -1, config._copyright)
        self.label_author = wx.StaticText(self, -1, "authors")
        self.hyperlink = wx.StaticText(self, -1, str(config._homepage))
        #self.hyperlink = wx.lib.hyperlink.HyperLinkCtrl(self, -1, config._homepage, URL=config._homepage)
        #self.hyperlink_license = wx.lib.hyperlink.HyperLinkCtrl(self, -1, "Comments? Bugs? Requests?", URL=config._paper)
        self.hyperlink_license = wx.StaticText(self, -1, "Comments? Bugs? Requests?")
        self.hyperlink_paper = wx.StaticText(self, -1, str(config._license))
        #self.hyperlink_paper = wx.lib.hyperlink.HyperLinkCtrl(self, -1, "Send us a ticket", URL=config._license)
        
        self.hyperlink_download = wx.StaticText(self, -1, str(config._download))
        #self.hyperlink_download = wx.lib.hyperlink.HyperLinkCtrl(self, -1, "Get the latest version", URL=config._download)
        self.static_line_1 = wx.StaticLine(self, -1)
        self.label_acknowledgement = wx.StaticText(self, -1, config._acknowledgement)
        self.static_line_2 = wx.StaticLine(self, -1)
        self.bitmap_button_nsf = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_danse = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_msu = wx.BitmapButton(self, -1, wx.NullBitmap)
        

        self.__set_properties()
        self.__do_layout()

        # end wxGlade
        
        # fill in acknowledgements
#       self.text_ctrl_acknowledgement.SetValue(__acknowledgement__)

        # randomly shuffle authors' names
        random.shuffle(config._authors)
        strLabel = ", ".join(config._authors)
        
        # display version and svn revison numbers
        verwords = config.__version__.split('.')
        version = '.'.join(verwords[:-1])
        revision = verwords[-1]
        
        self.label_author.SetLabel(strLabel)
        self.label_version.SetLabel(version)
        self.label_svnrevision.SetLabel(config.__version__)
        
        # set bitmaps for logo buttons
        image = file_dir+"/images/nsf_logo.png"
        if os.path.isfile(config._nsf_logo):
            image = config._nsf_logo
        logo = wx.Bitmap(image)        
        self.bitmap_button_nsf.SetBitmapLabel(logo)

        image = file_dir+"/images/danse_logo.png"
        if os.path.isfile(config._danse_logo):
            image = config._danse_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_danse.SetBitmapLabel(logo)
        
        image = file_dir+"/images/utlogo.gif"
        if os.path.isfile(config._inst_logo):
            image = config._inst_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_msu.SetBitmapLabel(logo)
        
        # resize dialog window to fit version number nicely
        if wx.VERSION >= (2,7,2,0):
            size = [self.GetEffectiveMinSize()[0], self.GetSize()[1]]
        else:
            size = [self.GetBestFittingSize()[0], self.GetSize()[1]]

        self.Fit()
#        self.SetSize(size)
#       self.FitInside()
        

    def __set_properties(self):
        # begin wxGlade: DialogAbout.__set_properties
       
        self.SetSize((600, 595))
        self.label_title.SetFont(wx.Font(26, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_version.SetFont(wx.Font(26, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        #self.hyperlink_license.Enable(False)
        #self.hyperlink_license.Hide()
        self.hyperlink_paper.Enable(True)
        #self.hyperlink_paper.Hide()
        self.bitmap_button_nsf.SetSize(self.bitmap_button_nsf.GetBestSize())
        self.bitmap_button_danse.SetSize(self.bitmap_button_danse.GetBestSize())
        self.bitmap_button_msu.SetSize(self.bitmap_button_msu.GetBestSize())
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: DialogAbout.__do_layout
        sizer_main = wx.BoxSizer(wx.VERTICAL)
       
        sizer_logos = wx.BoxSizer(wx.HORIZONTAL)
        sizer_header = wx.BoxSizer(wx.HORIZONTAL)
        sizer_titles = wx.BoxSizer(wx.VERTICAL)
        sizer_build = wx.BoxSizer(wx.HORIZONTAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        sizer_header.Add(self.bitmap_logo, 0, wx.EXPAND, 0)
        sizer_title.Add(self.label_title, 0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        sizer_title.Add((20, 20), 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_title.Add(self.label_version, 0, wx.RIGHT|wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 10)
        sizer_titles.Add(sizer_title, 0, wx.EXPAND, 0)
        sizer_build.Add(self.label_build, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        sizer_build.Add(self.label_svnrevision, 0, wx.ADJUST_MINSIZE, 0)
        sizer_titles.Add(sizer_build, 0, wx.TOP|wx.EXPAND, 5)
        sizer_titles.Add(self.label_copyright, 0, wx.LEFT|wx.RIGHT|wx.TOP|wx.ADJUST_MINSIZE, 10)
        sizer_titles.Add(self.label_author, 0, wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        sizer_titles.Add(self.hyperlink, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_titles.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        sizer_titles.Add(self.hyperlink_license, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_titles.Add(self.hyperlink_paper, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_titles.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        sizer_titles.Add(self.hyperlink_download, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_header.Add(sizer_titles, 0, wx.EXPAND, 0)
        sizer_main.Add(sizer_header, 0, wx.BOTTOM|wx.EXPAND, 3)
        sizer_main.Add(self.static_line_1, 0, wx.EXPAND, 0)
        sizer_main.Add(self.label_acknowledgement, 0, wx.LEFT|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE, 7)
        sizer_main.Add(self.static_line_2, 0, wx.EXPAND, 0)
        sizer_logos.Add(self.bitmap_button_nsf, 0, wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_danse, 0, wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_msu, 0, wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add((50, 50), 0, wx.ADJUST_MINSIZE, 0)
        sizer_main.Add(sizer_logos, 0, wx.EXPAND, 0)
        
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre()
        # end wxGlade

    

# end of class DialogAbout

