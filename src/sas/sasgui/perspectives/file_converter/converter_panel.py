"""
This module provides a GUI for the file converter
"""

import wx
import sys
import numpy as np
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.perspectives.file_converter.converter_widgets import VectorInput
from sas.sasgui.perspectives.file_converter.detector_panel import DetectorWindow
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.utils import check_float
from sas.sascalc.dataloader.readers.cansas_reader import Reader as CansasReader
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.data_info import Vector

# Panel size
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    _STATICBOX_WIDTH = 410
    _BOX_WIDTH = 200
    PANEL_SIZE = 480
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    _STATICBOX_WIDTH = 430
    _BOX_WIDTH = 200
    PANEL_SIZE = 500
    FONT_VARIANT = 1

class ConverterPanel(ScrolledPanel, PanelBase):

    def __init__(self, parent, base=None, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        PanelBase.__init__(self)
        self.SetupScrolling()
        self.SetWindowVariant(variant=FONT_VARIANT)

        self.base = base
        self.parent = parent
        self.detector_frame = None

        self.q_input = None
        self.iq_input = None
        self.output = None
        self.to_validate = []

        self.metadata = {
            'title': None,
            'run': None,
            'run_name': None,
            'instrument': None,
            'detector': [Detector()]
        }
        self.vectors = ['offset', 'orientation', 'pixel_size', 'beam_center']
        for vector_name in self.vectors:
            setattr(self.metadata['detector'][0], vector_name, Vector())

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def convert_to_cansas(self, data, filename):
        reader = CansasReader()
        reader.write(filename, data)

    def extract_data(self, filename):
        data = np.loadtxt(filename, dtype=str)

        if len(data.shape) != 1:
            msg = "Error reading {}: Only one column of data is allowed"
            raise Exception(msg.format(filename.split('\\')[-1]))

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
        if not self.validate_inputs():
            return

        try:
            qdata = self.extract_data(self.q_input.GetPath())
            iqdata = self.extract_data(self.iq_input.GetPath())
        except Exception as ex:
            msg = str(ex)
            wx.PostEvent(self.parent.manager.parent,
                StatusEvent(status=msg, info='error'))
            return

        output_path = self.output.GetPath()
        data = Data1D(x=qdata, y=iqdata)
        data.filename = output_path.split('\\')[-1]

        if self.metadata['run'] is not None:
            run = self.metadata['run']
            run_name = self.metadata['run_name']

            if not isinstance(run, list) and run is not None:
                self.metadata['run'] = [run]
            else:
                run = run[0]

            if not isinstance(run_name, dict):
                if run_name is not None:
                    self.metadata['run_name'] = { run: run_name }
                else:
                    self.metadata['run_name'] = {}
            else:
                self.metadata['run_name'][run] = run_name.values()[0]
        else:
            self.metadata['run'] = []
            self.metadata['run_name'] = {}
        if self.metadata['detector'][0].name is None:
            self.metadata['detector'][0].name = ''

        # Convert vectors from strings to float
        for vector_name in self.vectors:
            # Vector of strings or Nones
            vector = getattr(self.metadata['detector'][0], vector_name)
            for direction in ['x', 'y', 'z']:
                value = getattr(vector, direction)
                if value is not None:
                    value = float(value)
                    setattr(vector, direction, value)
            setattr(self.metadata['detector'][0], vector_name, vector)

        for attr, value in self.metadata.iteritems():
            if value is not None:
                setattr(data, attr, value)

        self.convert_to_cansas(data, output_path)
        wx.PostEvent(self.parent.manager.parent,
            StatusEvent(status="Conversion completed."))

    def validate_inputs(self):
        msg = "You must select a"
        if self.q_input.GetPath() == '':
            msg += " Q Axis input file."
        elif self.iq_input.GetPath() == '':
            msg += "n Intensity input file."
        elif self.output.GetPath() == '':
            msg += "destination for the converted file."
        if msg != "You must select a":
            wx.PostEvent(self.parent.manager.parent,
                StatusEvent(status=msg, info='error'))
            return

        for ctrl in self.to_validate:
            ctrl_valid = True
            invalid_control = None
            if isinstance(ctrl, VectorInput):
                ctrl_valid, invalid_control = ctrl.Validate()
            else:
                if ctrl.GetValue() == '': continue
                ctrl_valid = check_float(ctrl)
                invalid_control = ctrl
            if not ctrl_valid:
                msg = "{} must be a valid float".format(
                    invalid_control.GetName().replace('_', ' '))
                wx.PostEvent(self.parent.manager.parent,
                    StatusEvent(status=msg, info='error'))
                return False

        return True

    def show_detector_window(self, event):
        if self.detector_frame is not None:
            self.detector_frame.panel.on_close()
            return
        self.detector_frame = DetectorWindow(self.parent.manager.parent,
            manager=self, detector=self.metadata['detector'][0])
        self.parent.manager.put_icon(self.detector_frame)
        self.detector_frame.Show(True)

    def metadata_changed(self, event):
        event.Skip()
        textbox = event.GetEventObject()
        attr = textbox.GetName()
        value = textbox.GetValue().strip()

        if attr.startswith('detector_'):
            attr = attr[9:] # Strip detector_
            is_vector = False
            for vector_name in self.vectors:
                if attr.startswith(vector_name): is_vector = True
            if is_vector:
                if value == '': value = None
                direction = attr[-1]
                attr = attr[:-2]
                vector = getattr(self.metadata['detector'][0], attr)
                setattr(vector, direction, value)
                value = vector
            setattr(self.metadata['detector'][0], attr, value)
            return

        if value == '':
            self.metadata[attr] = None
        else:
            self.metadata[attr] = value


    def _do_layout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        instructions = ("Select the 1 column ASCII files containing the Q Axis"
            " and Intensity data, chose where to save the converted file, then"
            " click Convert to convert them to CanSAS XML format. If required,"
            " metadata can also be input below.")
        instruction_label = wx.StaticText(self, -1, instructions,
            size=(_STATICBOX_WIDTH+40, -1))
        instruction_label.Wrap(_STATICBOX_WIDTH+40)
        vbox.Add(instruction_label, flag=wx.TOP | wx.LEFT | wx.RIGHT, border=5)

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

        convert_btn = wx.Button(self, wx.ID_OK, "Convert")
        input_grid.Add(convert_btn, (3,0), (1,1), wx.ALL, 5)
        convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)

        section_sizer.Add(input_grid)

        vbox.Add(section_sizer, flag=wx.ALL, border=5)

        metadata_section = wx.CollapsiblePane(self, -1, "Metadata",
            size=(_STATICBOX_WIDTH+40, -1), style=wx.WS_EX_VALIDATE_RECURSIVELY)
        metadata_pane = metadata_section.GetPane()
        metadata_grid = wx.GridBagSizer(5, 5)

        y = 0
        for item in self.metadata.keys():
            if item == 'detector': continue
            label_txt = item.replace('_', ' ').capitalize()
            label = wx.StaticText(metadata_pane, -1, label_txt,
                style=wx.ALIGN_CENTER_VERTICAL)
            input_box = wx.TextCtrl(metadata_pane, name=item,
                size=(_STATICBOX_WIDTH-80, -1))
            input_box.Bind(wx.EVT_TEXT, self.metadata_changed)
            metadata_grid.Add(label, (y,0), (1,1),
                wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            metadata_grid.Add(input_box, (y,1), (1,2), wx.EXPAND)
            y += 1

        detector_label = wx.StaticText(metadata_pane, -1,
            "Detector:")
        metadata_grid.Add(detector_label, (y, 0), (1,1), wx.ALL | wx.EXPAND, 5)
        detector_btn = wx.Button(metadata_pane, -1, "Enter Detector Metadata")
        metadata_grid.Add(detector_btn, (y, 1), (1,1), wx.ALL | wx.EXPAND, 5)
        detector_btn.Bind(wx.EVT_BUTTON, self.show_detector_window)
        y += 1

        metadata_pane.SetSizer(metadata_grid)

        vbox.Add(metadata_section, proportion=0, flag=wx.ALL, border=5)

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
