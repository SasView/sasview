"""
Console Module display message of a dialog
"""
import wx
import sys
from sas.dataloader.loader import Loader

_BOX_WIDTH = 60
CONSOLE_WIDTH = 340
CONSOLE_HEIGHT = 240
if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 450
    PANEL_WIDTH = 500
    PANEL_HEIGHT = 550
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 480
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 560
    FONT_VARIANT = 1

class ConsoleDialog(wx.Dialog):
    """
        Data summary dialog
    """
    def __init__(self, parent=None, manager=None, data=None,
                    title="Data Summary", size=(PANEL_WIDTH, PANEL_HEIGHT)):
        wx.Dialog.__init__(self, parent=parent, title=title, size=size)

        self.parent = parent
        self._manager = manager
        self._data = data
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.msg_txt = wx.TextCtrl(self, size=(PANEL_WIDTH - 40,
                                                PANEL_HEIGHT - 60),
                                        style=wx.TE_MULTILINE)
        self.msg_txt.SetEditable(False)
        self.msg_txt.SetValue('No message available')
        self.sizer.Add(self.msg_txt, 1, wx.EXPAND | wx.ALL, 10)
        if self._data is not None:
            self.set_message(msg=self._data.__str__())

        self.SetSizer(self.sizer)

    def set_manager(self, manager):
        """
        Set the manager of this window
        """
        self._manager = manager

    def set_message(self, msg=""):
        """
        Display the message received
        """
        self.msg_txt.SetValue(str(msg))

if __name__ == "__main__":

    app = wx.App()
    # Instantiate a loader 
    loader = Loader()
    # Load data 
    test_data = loader.load("MAR07232_rest.ASC")
    dlg = ConsoleDialog(data=test_data)
    dlg.ShowModal()
    app.MainLoop()
