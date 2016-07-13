"""
This module provides a GUI for the file converter
"""

import wx
import sys
import numpy as np
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader

# Panel size
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    _STATICBOX_WIDTH = 410
    _BOX_WIDTH = 200
    PANEL_SIZE = 460
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    _STATICBOX_WIDTH = 430
    _BOX_WIDTH = 200
    PANEL_SIZE = 480
    FONT_VARIANT = 1

class ConverterPanel(ScrolledPanel, PanelBase):

    def __init__(self, parent, base=None, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        PanelBase.__init__(self)
        self.SetupScrolling()
        self.SetWindowVariant(variant=FONT_VARIANT)

        self.base = base
        self.parent = parent

        self.q_input = None
        self.iq_input = None
        self.output = None

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def convert_to_cansas(self, data, filename):
        reader = CansasReader()
        reader.write(filename, data)

    def extract_data(self, filename):
        data = np.loadtxt(filename, dtype=str)

        is_float = True
        try:
            float(data[0])
        except:
            is_float = False

        if not is_float:
            end_char = data[0][-1]
            # If lines end with comma or semi-colon, trim the last character
            if end_char == ',' or end_char == ';':
                data = map(lambda s: s[0:-1], data)
            else:
                msg = ("Error reading {}: Lines must end with a digit, comma "
                    "or semi-colon").format(filename.split('\\')[-1])
                raise Exception(msg)

        return np.array(data, dtype=np.float32)

    def on_convert(self, event):
        try:
            qdata = self.extract_data(self.q_input.GetPath())
            iqdata = self.extract_data(self.iq_input.GetPath())
        except Exception as ex:
            msg = str(ex)
            wx.PostEvent(self.parent.manager.parent,
                StatusEvent(status=msg, info='error'))
            return

        data = Data1D(x=qdata, y=iqdata)
        self.convert_to_cansas(data, self.output.GetPath())
        wx.PostEvent(self.parent.manager.parent,
            StatusEvent(status="Conversion completed."))

    def _do_layout(self):
        vbox = wx.GridBagSizer(wx.VERTICAL)

        instructions = ("Select the 1 column ASCII files containing the Q Axis"
            "and Intensity data, chose where to save the converted file, then "
            "click Convert to convert them to CanSAS XML format")
        instruction_label = wx.StaticText(self, -1, "",
            size=(_STATICBOX_WIDTH+40, 28))
        instruction_label.SetLabel(instructions)
        vbox.Add(instruction_label, (0,0), (1,1), wx.ALL, 5)

        section = wx.StaticBox(self, -1)
        section_sizer = wx.StaticBoxSizer(section, wx.VERTICAL)
        section_sizer.SetMinSize((_STATICBOX_WIDTH, -1))

        input_grid = wx.GridBagSizer(5, 5)

        q_label = wx.StaticText(self, -1, "Q Axis: ")
        input_grid.Add(q_label, (0,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.q_input = wx.FilePickerCtrl(self, -1,
            size=(_STATICBOX_WIDTH-80, -1),
            message="Chose the Q Axis data file.")
        input_grid.Add(self.q_input, (0,1), (1,1), wx.ALL, 5)

        iq_label = wx.StaticText(self, -1, "Intensity Data: ")
        input_grid.Add(iq_label, (1,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.iq_input = wx.FilePickerCtrl(self, -1,
            size=(_STATICBOX_WIDTH-80, -1),
            message="Chose the Intensity data file.")
        input_grid.Add(self.iq_input, (1,1), (1,1), wx.ALL, 5)

        output_label = wx.StaticText(self, -1, "Output File: ")
        input_grid.Add(output_label, (2,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.output = wx.FilePickerCtrl(self, -1,
            size=(_STATICBOX_WIDTH-80, -1),
            message="Chose the Intensity data file.",
            style=wx.FLP_SAVE | wx.FLP_OVERWRITE_PROMPT | wx.FLP_USE_TEXTCTRL,
            wildcard="*.xml")
        input_grid.Add(self.output, (2,1), (1,1), wx.ALL, 5)

        convert_btn = wx.Button(self, -1, "Convert")
        input_grid.Add(convert_btn, (3,0), (1,1), wx.ALL, 5)
        convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)

        section_sizer.Add(input_grid)

        vbox.Add(section_sizer, (1,0), (1,1), wx.ALL, 5)

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
