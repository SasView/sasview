"""
    This class provide general structure of  fitpanel page
"""
import wx
from sas.guiframe.panel_base import PanelBase

class HintFitPage(wx.ScrolledWindow, PanelBase):
    """
        This class provide general structure of  fitpanel page
    """
    ## Internal name for the AUI manager
    window_name = "Hint Page"
    ## Title to appear on top of the window
    window_caption = "Hint page "

    def __init__(self, parent):
        wx.ScrolledWindow.__init__(self, parent,
                 style=wx.FULL_REPAINT_ON_RESIZE)
        PanelBase.__init__(self, parent)
        msg = "right click on the data when it is highlighted "
        msg += "the select option to fit for futher options"
        self.do_layout()

    def do_layout(self):
        """
            Draw the page
        """
        name = "Hint"
        box_description = wx.StaticBox(self, wx.ID_ANY, name)
        boxsizer = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        msg = "    How to link data to the control panel: \n \n"
        msg += "    First load data file from 'File' menu. \n"
        msg += "    Then Highlight and right click on the data plot. \n"
        msg += "    Finally, select 'Select data for fitting' in the pop-up menu. \n"
        self.hint_txt = wx.StaticText(self, wx.ID_ANY, msg, style=wx.ALIGN_LEFT)
        boxsizer.Add(self.hint_txt, wx.ALL | wx.EXPAND, 20)
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(boxsizer)
        self.vbox.Layout()
        self.vbox.Fit(self)
        self.SetSizer(self.vbox)
        self.SetScrollbars(20, 20, 25, 65)
        self.Layout()

    def createMemento(self):
        return


class HelpWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(570, 400))

        self.page = HintFitPage(self)
        self.Centre()
        self.Show(True)
