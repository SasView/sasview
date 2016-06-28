import wx
import sys
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.panel_base import PanelBase

BACKGROUND = 0.0
if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 450
    PANEL_WIDTH = 500
    PANEL_HEIGHT = 700
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 490
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 700
    FONT_VARIANT = 1

class CorfuncPanel(ScrolledPanel,PanelBase):
    window_name = "Correlation Function"
    window_caption = "Correlation Function"
    CENTER_PANE = True

    def __init__(self, parent, data=None, manager=None, *args, **kwds):
        kwds["size"] = (PANEL_WIDTH, PANEL_HEIGHT)
        kwds["style"] = wx.FULL_REPAINT_ON_RESIZE
        ScrolledPanel.__init__(self, parent=parent, *args, **kwds)
        PanelBase.__init__(self, parent)
        self.SetupScrolling()
        self.SetWindowVariant(variant=FONT_VARIANT)
        self._manager = manager
        self._data = data
        self._background = BACKGROUND
        self.state = None

        self._main_sizer = None

        self.set_state()
        self._do_layout()

    def set_state(self, state=None, data=None):
        return False

    def _do_layout(self):
        """
        Draw the window content
        """
        self._main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        txt = wx.StaticText(self, id=wx.NewId(), label="TODO: Add GUI",
            style=wx.ALIGN_CENTRE_HORIZONTAL)
        self._main_sizer.Add(txt, 1, wx.EXPAND)
        self.SetSizer(self._main_sizer)
        self.SetAutoLayout(True)
