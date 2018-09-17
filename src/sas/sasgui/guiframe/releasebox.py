'''
Created on Sep 17, 2018
Developed from acknowledgebox.py
@author: sking
'''

__id__ = "$Id: releasebox.py 2018-17-09 sking $"
# What is this and is it important?
__revision__ = "$Revision: 1193 $"

import wx
import wx.richtext
import wx.lib.hyperlink
from wx.lib.expando import ExpandoTextCtrl

from sas import get_local_config
config = get_local_config()

class DialogRelease(wx.Dialog):
    """
    "Release Notes" Dialog Box

    Shows the current SasView Release Notes.
    """

    def __init__(self, *args, **kwds):

        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)

        self.preamble = wx.StaticText(self, -1, config._release_preamble)
        items = [config._release_location1,
                 config._release_location2]
        self.list1 = wx.StaticText(self, -1, "DEVELOPERS  " + items[0])
        self.list2 = wx.StaticText(self, -1, "USERS              " + items[1])
        self.static_line = wx.StaticLine(self, 0)
        self.__set_properties()
        self.__do_layout()

    def __set_properties(self):
        """
        :TODO - add method documentation
        """
        self.preamble.SetFont(wx.Font(11, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.preamble.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL, 0, ""))
        self.SetTitle("SasView Release Notes & Known Issues")
        self.SetClientSize((600, 320))

    def __do_layout(self):
        """
        :TODO - add method documentation
        """
        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_titles = wx.BoxSizer(wx.VERTICAL)
        sizer_titles.Add(self.preamble, 0, wx.ALL|wx.EXPAND, 5)
        sizer_titles.Add(self.list1, 0, wx.ALL|wx.EXPAND, 5)
        sizer_titles.Add(self.list2, 0, wx.ALL|wx.EXPAND, 5)
        sizer_main.Add(sizer_titles, -1, wx.ALL|wx.EXPAND, 5)
        self.SetAutoLayout(True)
        self.SetSizer(sizer_main)
        self.Layout()
        self.Centre()


##### testing code ############################################################
class MyApp(wx.App):
    """
    Class for running module as stand alone for testing
    """
    def OnInit(self):
        """
        Defines an init when running as standalone
        """
        wx.InitAllImageHandlers()
        dialog = DialogRelease(None, -1, "")
        self.SetTopWindow(dialog)
        dialog.ShowModal()
        dialog.Destroy()
        return 1

# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
