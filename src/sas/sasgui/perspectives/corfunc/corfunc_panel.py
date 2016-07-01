import wx
import sys
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.perspectives.invariant.invariant_widgets import OutputTextCtrl

BACKGROUND = 0.0
if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 350
    PANEL_WIDTH = 400
    PANEL_HEIGHT = 700
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 390
    PANEL_WIDTH = 430
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
        self.set_state()
        self._do_layout()

    def set_state(self, state=None, data=None):
        return False

    def _set_data(self, data=None):
        """
        Update the GUI to reflect new data that has been loaded in

        :param data: The data that has been loaded
        """
        self.data_name_box.SetValue(str(data.name))
        if self._manager is not None:
            self._manager.show_data(data=data, reset=True)


    def _do_layout(self):
        """
        Draw the window content
        """
        vbox = wx.GridBagSizer(0,0)

        # I(q) data box
        databox = wx.StaticBox(self, -1, "I(q) data source")

        pars_sizer = wx.GridBagSizer(5, 5)

        box_sizer1 = wx.StaticBoxSizer(databox, wx.VERTICAL)
        box_sizer1.SetMinSize((350, 50))

        file_name_label = wx.StaticText(self, -1, "Name:")
        pars_sizer.Add(file_name_label, (0, 0), (1, 1),
            wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        self.data_name_box = OutputTextCtrl(self, -1, size=(350,20))
        pars_sizer.Add(self.data_name_box, (0, 1), (1, 1),
            wx.EXPAND | wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 15)

        box_sizer1.Add(pars_sizer, 0, wx.EXPAND)
        vbox.Add(box_sizer1, (0, 0), (1, 1),
            wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE | wx.TOP, 5)

        self.SetSizer(vbox)
