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

from sas import get_local_config
config = get_local_config()

def launchBrowser(url):
    """
    Launches browser and opens specified url

    In some cases may require BROWSER environment variable to be set up.

    :param url: URL to open

    """
    import webbrowser
    webbrowser.open(url)


class DialogAbout(wx.Dialog):
    """
    "About" Dialog

    Shows product name, current version, authors, and link to the product page.
    Current version is taken from version.py

    """

    def __init__(self, *args, **kwds):

        # begin wxGlade: DialogAbout.__init__
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)

        file_dir = os.path.dirname(__file__)

        # Mac doesn't display images with transparent background so well,
        # keep it for Windows
        image = file_dir + "/images/angles_flat.png"

        if os.path.isfile(config._corner_image):
            image = config._corner_image

        if os.name == 'nt':
            self.bitmap_logo = wx.StaticBitmap(self, -1, wx.Bitmap(image))
        else:
            self.bitmap_logo = wx.StaticBitmap(self, -1, wx.Bitmap(image))

        self.label_title = wx.StaticText(self, -1, config.__appname__)
        self.label_version = wx.StaticText(self, -1, "")
        self.label_build = wx.StaticText(self, -1, "Build:")
        self.label_svnrevision = wx.StaticText(self, -1, "")
        self.label_copyright = wx.StaticText(self, -1, config._copyright)
        self.label_author = wx.StaticText(self, -1, "authors")
        self.hyperlink = wx.lib.hyperlink.HyperLinkCtrl(self, -1,
                                                        config._homepage,
                                                        URL=config._homepage)
        #self.hyperlink_license = wx.lib.hyperlink.HyperLinkCtrl(self, -1,
        #"Comments? Bugs? Requests?", URL=config._paper)
        self.hyperlink_license = wx.StaticText(self, -1,
                                               "Comments? Bugs? Requests?")
        self.hyperlink_paper = wx.lib.hyperlink.HyperLinkCtrl(self, -1,
                                                        "Send us a ticket",
                                                        URL=config._license)
        self.hyperlink_download = wx.lib.hyperlink.HyperLinkCtrl(self, -1,
                                                "Get the latest version",
                                                URL=config._download)
        self.static_line_1 = wx.StaticLine(self, -1)
        self.label_acknowledgement = wx.StaticText(self, -1,
                                                   config._acknowledgement)
        self.static_line_2 = wx.StaticLine(self, -1)
        self.bitmap_button_nist = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_umd = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_ornl = wx.BitmapButton(self, -1, wx.NullBitmap)
        #self.bitmap_button_sns = wx.BitmapButton(self, -1, wx.NullBitmap)
        #self.bitmap_button_nsf = wx.BitmapButton(self, -1,
        #                                         wx.NullBitmap)
        #self.bitmap_button_danse = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_msu = wx.BitmapButton(self, -1, wx.NullBitmap)

        self.bitmap_button_isis = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_ess = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_ill = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_ansto = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_tudelft = wx.BitmapButton(self, -1, wx.NullBitmap)
        self.bitmap_button_dls = wx.BitmapButton(self, -1, wx.NullBitmap)

        self.static_line_3 = wx.StaticLine(self, -1)
        self.button_OK = wx.Button(self, wx.ID_OK, "OK")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.onNistLogo, self.bitmap_button_nist)
        self.Bind(wx.EVT_BUTTON, self.onUmdLogo, self.bitmap_button_umd)
        #self.Bind(wx.EVT_BUTTON, self.onSnsLogo, self.bitmap_button_sns)
        self.Bind(wx.EVT_BUTTON, self.onOrnlLogo, self.bitmap_button_ornl)
        #self.Bind(wx.EVT_BUTTON, self.onNsfLogo, self.bitmap_button_nsf)
        #self.Bind(wx.EVT_BUTTON, self.onDanseLogo, self.bitmap_button_danse)
        self.Bind(wx.EVT_BUTTON, self.onUTLogo, self.bitmap_button_msu)
        self.Bind(wx.EVT_BUTTON, self.onIsisLogo, self.bitmap_button_isis)
        self.Bind(wx.EVT_BUTTON, self.onEssLogo, self.bitmap_button_ess)
        self.Bind(wx.EVT_BUTTON, self.onIllLogo, self.bitmap_button_ill)
        self.Bind(wx.EVT_BUTTON, self.onAnstoLogo, self.bitmap_button_ansto)
        self.Bind(wx.EVT_BUTTON, self.onTudelftLogo, self.bitmap_button_tudelft)
        self.Bind(wx.EVT_BUTTON, self.onDlsLogo, self.bitmap_button_dls)
        # end wxGlade
        # fill in acknowledgements
        #self.text_ctrl_acknowledgement.SetValue(__acknowledgement__)
        # randomly shuffle authors' names
        random.shuffle(config._authors)
        strLabel = ", ".join(config._authors)

        # display version and svn revison numbers
        verwords = config.__version__.split('.')
        version = '.'.join(verwords[:-1])
        revision = verwords[-1]
        try:
            build_num = str(config.__build__)
        except:
            build_num = str(config.__version__)
        self.label_author.SetLabel(strLabel)
        self.label_version.SetLabel(config.__version__)#(version)
        self.label_svnrevision.SetLabel(build_num)

        # set bitmaps for logo buttons
        image = file_dir + "/images/nist_logo.png"
        if os.path.isfile(config._nist_logo):
            image = config._nist_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_nist.SetBitmapLabel(logo)

        image = file_dir + "/images/umd_logo.png"
        if os.path.isfile(config._umd_logo):
            image = config._umd_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_umd.SetBitmapLabel(logo)

        image = file_dir + "/images/ornl_logo.png"
        if os.path.isfile(config._ornl_logo):
            image = config._ornl_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_ornl.SetBitmapLabel(logo)

        """
        image = file_dir + "/images/sns_logo.png"
        if os.path.isfile(config._sns_logo):
            image = config._sns_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_sns.SetBitmapLabel(logo)

        image = file_dir + "/images/nsf_logo.png"
        if os.path.isfile(config._nsf_logo):
            image = config._nsf_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_nsf.SetBitmapLabel(logo)

        image = file_dir + "/images/danse_logo.png"
        if os.path.isfile(config._danse_logo):
            image = config._danse_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_danse.SetBitmapLabel(logo)
        """
        image = file_dir + "/images/utlogo.png"
        if os.path.isfile(config._inst_logo):
            image = config._inst_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_msu.SetBitmapLabel(logo)

        image = file_dir + "/images/isis_logo.png"
        if os.path.isfile(config._isis_logo):
            image = config._isis_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_isis.SetBitmapLabel(logo)

        image = file_dir + "/images/ess_logo.png"
        if os.path.isfile(config._ess_logo):
            image = config._ess_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_ess.SetBitmapLabel(logo)

        image = file_dir + "/images/ill_logo.png"
        if os.path.isfile(config._ill_logo):
            image = config._ill_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_ill.SetBitmapLabel(logo)

        image = file_dir + "/images/ansto_logo.png"
        if os.path.isfile(config._ansto_logo):
            image = config._ansto_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_ansto.SetBitmapLabel(logo)

        image = file_dir + "/images/tudelft_logo.png"
        if os.path.isfile(config._tudelft_logo):
            image = config._tudelft_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_tudelft.SetBitmapLabel(logo)

        image = file_dir + "/images/dls_logo.png"
        if os.path.isfile(config._dls_logo):
            image = config._dls_logo
        logo = wx.Bitmap(image)
        self.bitmap_button_dls.SetBitmapLabel(logo)

        # resize dialog window to fit version number nicely
        if wx.VERSION >= (2, 7, 2, 0):
            size = [self.GetEffectiveMinSize()[0], self.GetSize()[1]]
        else:
            size = [self.GetBestFittingSize()[0], self.GetSize()[1]]
        self.Fit()

    def __set_properties(self):
        """
        """
        # begin wxGlade: DialogAbout.__set_properties
        self.SetTitle("About")
        self.SetSize((600, 595))
        self.label_title.SetFont(wx.Font(26, wx.DEFAULT, wx.NORMAL,
                                         wx.BOLD, 0, ""))
        self.label_version.SetFont(wx.Font(26, wx.DEFAULT, wx.NORMAL,
                                           wx.NORMAL, 0, ""))
        self.hyperlink_paper.Enable(True)
        self.bitmap_button_nist.SetSize(self.bitmap_button_nist.GetBestSize())
        self.bitmap_button_umd.SetSize(self.bitmap_button_umd.GetBestSize())
        self.bitmap_button_ornl.SetSize(self.bitmap_button_ornl.GetBestSize())
        #self.bitmap_button_sns.SetSize(self.bitmap_button_sns.GetBestSize())
        #self.bitmap_button_nsf.SetSize(self.bitmap_button_nsf.GetBestSize())
        #self.bitmap_button_danse.SetSize(self.bitmap_button_danse.GetBestSize())
        self.bitmap_button_msu.SetSize(self.bitmap_button_msu.GetBestSize())
        self.bitmap_button_isis.SetSize(self.bitmap_button_isis.GetBestSize())
        self.bitmap_button_ess.SetSize(self.bitmap_button_ess.GetBestSize())
        self.bitmap_button_ill.SetSize(self.bitmap_button_ill.GetBestSize())
        self.bitmap_button_ansto.SetSize(self.bitmap_button_ansto.GetBestSize())
        self.bitmap_button_tudelft.SetSize(self.bitmap_button_tudelft.GetBestSize())
        self.bitmap_button_dls.SetSize(self.bitmap_button_dls.GetBestSize())
        # end wxGlade

    def __do_layout(self):
        """
        """
        # begin wxGlade: DialogAbout.__do_layout
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_logos = wx.BoxSizer(wx.HORIZONTAL)
        sizer_header = wx.BoxSizer(wx.HORIZONTAL)
        sizer_titles = wx.BoxSizer(wx.VERTICAL)
        sizer_build = wx.BoxSizer(wx.HORIZONTAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        sizer_header.Add(self.bitmap_logo, 0, wx.EXPAND, 0)
        sizer_title.Add(self.label_title, 0,
                        wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        sizer_title.Add((20, 20), 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_title.Add(self.label_version, 0,
                        wx.RIGHT|wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 10)
        sizer_titles.Add(sizer_title, 0, wx.EXPAND, 0)
        sizer_build.Add(self.label_build, 0,
                        wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        sizer_build.Add(self.label_svnrevision, 0, wx.ADJUST_MINSIZE, 0)
        sizer_titles.Add(sizer_build, 0, wx.TOP|wx.EXPAND, 5)
        sizer_titles.Add(self.label_copyright, 0,
                         wx.LEFT|wx.RIGHT|wx.TOP|wx.ADJUST_MINSIZE, 10)
        sizer_titles.Add(self.label_author, 0,
                         wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        sizer_titles.Add(self.hyperlink, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_titles.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        sizer_titles.Add(self.hyperlink_license, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_titles.Add(self.hyperlink_paper, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_titles.Add((20, 20), 0, wx.ADJUST_MINSIZE, 0)
        sizer_titles.Add(self.hyperlink_download, 0, wx.LEFT|wx.RIGHT, 10)
        sizer_header.Add(sizer_titles, 0, wx.EXPAND, 0)
        sizer_main.Add(sizer_header, 0, wx.BOTTOM|wx.EXPAND, 3)
        sizer_main.Add(self.static_line_1, 0, wx.EXPAND, 0)
        sizer_main.Add(self.label_acknowledgement, 0,
                       wx.LEFT|wx.TOP|wx.BOTTOM|wx.ADJUST_MINSIZE, 7)
        sizer_main.Add(self.static_line_2, 0, wx.EXPAND, 0)

        sizer_logos.Add(self.bitmap_button_msu, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        #sizer_logos.Add(self.bitmap_button_danse, 0,
        #                wx.LEFT|wx.ADJUST_MINSIZE, 2)
        #sizer_logos.Add(self.bitmap_button_nsf, 0,
        #                wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_umd, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_nist, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        #sizer_logos.Add(self.bitmap_button_sns, 0,
        #                wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_ornl, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_isis, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_ess, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_ill, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_ansto, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_tudelft, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)
        sizer_logos.Add(self.bitmap_button_dls, 0,
                        wx.LEFT|wx.ADJUST_MINSIZE, 2)

        sizer_logos.Add((10, 50), 0, wx.ADJUST_MINSIZE, 0)
        sizer_main.Add(sizer_logos, 0, wx.EXPAND, 0)
        sizer_main.Add(self.static_line_3, 0, wx.EXPAND, 0)
        sizer_button.Add((20, 40), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.button_OK, 0,
                         wx.RIGHT|wx.ADJUST_MINSIZE|wx.CENTER, 10)
        sizer_main.Add(sizer_button, 0, wx.EXPAND, 0)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre()
        # end wxGlade

    def onNistLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._nist_url)
        event.Skip()

    def onUmdLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._umd_url)
        event.Skip()

    def onOrnlLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._ornl_url)
        event.Skip()

    def onSnsLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._sns_url)
        event.Skip()

    def onNsfLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._nsf_url)
        event.Skip()

    def onDanseLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._danse_url)
        event.Skip()

    def onUTLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._inst_url)
        event.Skip()

    def onIsisLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._isis_url)
        event.Skip()

    def onEssLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._ess_url)
        event.Skip()

    def onIllLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._ill_url)
        event.Skip()

    def onAnstoLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._ansto_url)
        event.Skip()

    def onTudelftLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._tudelft_url)
        event.Skip()

    def onDlsLogo(self, event):
        """
        """
        # wxGlade: DialogAbout.<event_handler>
        launchBrowser(config._dls_url)
        event.Skip()

# end of class DialogAbout

##### testing code ############################################################
class MyApp(wx.App):
    """
    """
    def OnInit(self):
        """
        """
        wx.InitAllImageHandlers()
        dialog = DialogAbout(None, -1, "")
        self.SetTopWindow(dialog)
        dialog.ShowModal()
        dialog.Destroy()
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()

##### end of testing code #####################################################
