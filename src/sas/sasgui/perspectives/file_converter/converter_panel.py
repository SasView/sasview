"""
This module provides a GUI for the file converter
"""

import wx
import sys
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.perspectives.calculator import calculator_widgets as widget

# Panel size
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    _STATICBOX_WIDTH = 410
    _BOX_WIDTH = 200
    PANEL_SIZE = 440
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    _STATICBOX_WIDTH = 430
    _BOX_WIDTH = 200
    PANEL_SIZE = 460
    FONT_VARIANT = 1

class ConverterPanel(ScrolledPanel, PanelBase):

    def __init__(self, parent, base=None, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        PanelBase.__init__(self)

        self.SetWindowVariant(variant=FONT_VARIANT)

        self.base = base
        self.parent = parent

        self._do_layout
        self.SetAutoLayout(True)
        self.Layout()

    def _do_layout(self):
        # TODO: Get this working
        vbox = wx.BoxSizer(wx.VERTICAL)

        inputsection = wx.StaticBox(self, -1, "Input File")
        inputsection_sizer = wx.StaticBoxSizer(inputsection, wx.VERTICAL)

        input_grid = wx.GridBagSizer(5, 5)

        input_box = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        input_grid.Add(input_box, (0,0), (1,1), wx.LEFT, 5)

        inputsection_sizer.Add(input_grid)

        vbox.Add(input_section, (0,0), (0,1), wx.TOP, 15)

        vbox.Fit(self)
        self.SetSizer(vbox)

class ConverterWindow(widget.CHILD_FRAME):

    def __init__(self, parent=None, title='File Converter', base=None,
        manager=None, size=(PANEL_SIZE * 1.05, PANEL_SIZE / 1.55),
        *args, **kwargs):
        kwargs['title'] = title
        kwargs['size'] = size
        widget.CHILD_FRAME.__init__(self, parent, *args, **kwargs)

        self.manager = manager
        self.panel = ConverterPanel(self, base=None)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetPosition((wx.LEFT, PANEL_TOP))
        self.Show(True)

    def on_close(self, event):
        if self.manager is not None:
            self.manager.converter_frame = None
        self.Destroy()
