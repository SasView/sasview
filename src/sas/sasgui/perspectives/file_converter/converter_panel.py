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
from sas.sasgui.perspectives.file_converter.meta_panels import MetadataWindow
from sas.sasgui.perspectives.file_converter.meta_panels import DetectorPanel
from sas.sasgui.perspectives.file_converter.meta_panels import SamplePanel
from sas.sasgui.perspectives.file_converter.meta_panels import SourcePanel
from sas.sasgui.perspectives.file_converter.frame_select_dialog import FrameSelectDialog
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.documentation_window import DocumentationWindow
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.utils import check_float
from sas.sasgui.perspectives.file_converter.cansas_writer import CansasWriter
from sas.sasgui.perspectives.file_converter.bsl_loader import BSLLoader
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.data_info import Sample
from sas.sascalc.dataloader.data_info import Source
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
        self.meta_frames = []

        self.q_input = None
        self.iq_input = None
        self.output = None
        self.data_type = "ascii"

        self.title = None
        self.run = None
        self.run_name = None
        self.instrument = None
        self.detector = Detector()
        self.sample = Sample()
        self.source = Source()
        self.properties = ['title', 'run', 'run_name', 'instrument']

        self.detector.name = ''
        self.source.radiation = 'neutron'

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def convert_to_cansas(self, frame_data, filename, single_file):
        reader = CansasWriter()
        entry_attrs = None
        if self.run_name is not None:
            entry_attrs = { 'name': self.run_name }
        if single_file:
            reader.write(filename, frame_data,
                sasentry_attrs=entry_attrs)
        else:
            # strip extension from filename
            ext = "." + filename.split('.')[-1]
            name = filename.replace(ext, '')
            for i in range(len(frame_data)):
                f_name = "{}{}{}".format(name, i+1, ext)
                reader.write(f_name, [frame_data[i]],
                    sasentry_attrs=entry_attrs)

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

    def ask_frame_range(self, n_frames):
        valid_input = False
        dlg = FrameSelectDialog(n_frames)
        frames = None
        increment = None
        single_file = True
        while not valid_input:
            if dlg.ShowModal() == wx.ID_OK:
                msg = ""
                try:
                    first_frame = int(dlg.first_input.GetValue())
                    last_frame = int(dlg.last_input.GetValue())
                    increment = int(dlg.increment_input.GetValue())
                    single_file = dlg.single_btn.GetValue()
                    if last_frame < 0 or first_frame < 0:
                        msg = "Frame values must be positive"
                    elif increment < 1:
                        msg = "Increment must be greater than or equal to 1"
                    elif first_frame > last_frame:
                        msg = "First frame must be less than last frame"
                    elif last_frame > n_frames:
                        msg = "Last frame must be less than {}".format(n_frames)
                    else:
                        valid_input = True
                except:
                    valid_input = False
                    msg = "Please enter valid integer values"

                if not valid_input:
                    wx.PostEvent(self.parent.manager.parent,
                        StatusEvent(status=msg))
            else:
                return { 'frames': [], 'inc': None, 'file': single_file }
        frames = range(first_frame, last_frame + increment,
            increment)
        return { 'frames': frames, 'inc': increment, 'file': single_file }

    def on_convert(self, event):
        if not self.validate_inputs():
            return

        self.sample.ID = self.title

        try:
            if self.data_type == 'ascii':
                qdata = self.extract_data(self.q_input.GetPath())
                iqdata = self.extract_data(self.iq_input.GetPath())
            else: # self.data_type == 'bsl'
                loader = BSLLoader(self.q_input.GetPath(),
                    self.iq_input.GetPath())
                bsl_data = loader.load_bsl_data()
                qdata = bsl_data.q_axis.data[0]
                iqdata = bsl_data.data_axis.data
                frames = [iqdata.shape[0]]
                increment = 1
                single_file = True
                if frames[0] > 3:
                    params = self.ask_frame_range(frames[0])
                    frames = params['frames']
                    increment = params['inc']
                    single_file = params['file']
                    if frames == []: return
        except Exception as ex:
            msg = str(ex)
            wx.PostEvent(self.parent.manager.parent,
                StatusEvent(status=msg, info='error'))
            return

        output_path = self.output.GetPath()

        if self.run is None:
            self.run = []
        elif not isinstance(self.run, list):
            self.run = [self.run]

        if self.title is None:
            self.title = ''

        metadata = {
            'title': self.title,
            'run': self.run,
            'intrument': self.instrument,
            'detector': [self.detector],
            'sample': self.sample,
            'source': self.source
        }

        frame_data = []
        for i in frames:
            data = Data1D(x=qdata, y=iqdata[i])
            frame_data.append(data)
        if single_file:
            # Only need to set metadata on first Data1D object
            frame_data[0].filename = output_path.split('\\')[-1]
            for key, value in metadata.iteritems():
                setattr(frame_data[0], key, value)
        else:
            # Need to set metadata for all Data1D objects
            for datainfo in frame_data:
                datainfo.filename = output_path.split('\\')[-1]
                for key, value in metadata.iteritems():
                    setattr(datainfo, key, value)


        self.convert_to_cansas(frame_data, output_path, single_file)
        wx.PostEvent(self.parent.manager.parent,
            StatusEvent(status="Conversion completed."))

    def on_help(self, event):
        tree_location = ("user/sasgui/perspectives/file_converter/"
            "file_converter_help.html")
        doc_viewer = DocumentationWindow(self, -1, tree_location,
            "", "File Converter Help")

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

        return True

    def show_detector_window(self, event):
        if self.meta_frames != []:
            for frame in self.meta_frames:
                frame.panel.on_close()
        detector_frame = MetadataWindow(DetectorPanel,
            parent=self.parent.manager.parent, manager=self,
            metadata=self.detector, title='Detector Metadata')
        self.meta_frames.append(detector_frame)
        self.parent.manager.put_icon(detector_frame)
        detector_frame.Show(True)

    def show_sample_window(self, event):
        if self.meta_frames != []:
            for frame in self.meta_frames:
                frame.panel.on_close()
        sample_frame = MetadataWindow(SamplePanel,
            parent=self.parent.manager.parent, manager=self,
            metadata=self.sample, title='Sample Metadata')
        self.meta_frames.append(sample_frame)
        self.parent.manager.put_icon(sample_frame)
        sample_frame.Show(True)

    def show_source_window(self, event):
        if self.meta_frames != []:
            for frame in self.meta_frames:
                frame.panel.on_close()
        source_frame = MetadataWindow(SourcePanel,
            parent=self.parent.manager.parent, manager=self,
            metadata=self.source, title="Source Metadata")
        self.meta_frames.append(source_frame)
        self.parent.manager.put_icon(source_frame)
        source_frame.Show(True)

    def on_collapsible_pane(self, event):
        self.Freeze()
        self.SetupScrolling()
        self.parent.Layout()
        self.Thaw()

    def datatype_changed(self, event):
        event.Skip()
        dtype = event.GetEventObject().GetName()
        self.data_type = dtype

    def radiationtype_changed(self, event):
        event.Skip()
        rtype = event.GetEventObject().GetValue().lower()
        self.source.radiation = rtype

    def metadata_changed(self, event):
        event.Skip()
        textbox = event.GetEventObject()
        attr = textbox.GetName()
        value = textbox.GetValue().strip()

        if value == '': value = None

        setattr(self, attr, value)


    def _do_layout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        instructions = ("Select either single column ASCII files or BSL/OTOKO"
            " files containing the Q-Axis and Intensity-axis data, chose where"
            " to save the converted file, then click Convert to convert them "
            "to CanSAS XML format. If required, metadata can also be input "
            "below.")
        instruction_label = wx.StaticText(self, -1, instructions,
            size=(_STATICBOX_WIDTH+40, -1))
        instruction_label.Wrap(_STATICBOX_WIDTH+40)
        vbox.Add(instruction_label, flag=wx.TOP | wx.LEFT | wx.RIGHT, border=5)

        section = wx.StaticBox(self, -1)
        section_sizer = wx.StaticBoxSizer(section, wx.VERTICAL)
        section_sizer.SetMinSize((_STATICBOX_WIDTH, -1))

        input_grid = wx.GridBagSizer(5, 5)

        y = 0

        q_label = wx.StaticText(self, -1, "Q-Axis Data: ")
        input_grid.Add(q_label, (y,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.q_input = wx.FilePickerCtrl(self, -1,
            size=(_STATICBOX_WIDTH-80, -1),
            message="Chose the Q-Axis data file.")
        input_grid.Add(self.q_input, (y,1), (1,1), wx.ALL, 5)
        y += 1

        iq_label = wx.StaticText(self, -1, "Intensity-Axis Data: ")
        input_grid.Add(iq_label, (y,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.iq_input = wx.FilePickerCtrl(self, -1,
            size=(_STATICBOX_WIDTH-80, -1),
            message="Chose the Intensity-Axis data file.")
        input_grid.Add(self.iq_input, (y,1), (1,1), wx.ALL, 5)
        y += 1

        data_type_label = wx.StaticText(self, -1, "Input Format: ")
        input_grid.Add(data_type_label, (y,0), (1,1),
            wx.ALIGN_CENTER_VERTICAL, 5)
        radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ascii_btn = wx.RadioButton(self, -1, "ASCII", name="ascii",
            style=wx.RB_GROUP)
        ascii_btn.Bind(wx.EVT_RADIOBUTTON, self.datatype_changed)
        radio_sizer.Add(ascii_btn)
        bsl_btn = wx.RadioButton(self, -1, "BSL/OTOKO", name="bsl")
        bsl_btn.Bind(wx.EVT_RADIOBUTTON, self.datatype_changed)
        radio_sizer.Add(bsl_btn)
        input_grid.Add(radio_sizer, (y,1), (1,1), wx.ALL, 5)
        y += 1

        radiation_label = wx.StaticText(self, -1, "Radiation Type: ")
        input_grid.Add(radiation_label, (y,0), (1,1), wx.ALL, 5)
        radiation_input = wx.ComboBox(self, -1,
            choices=["Neutron", "X-Ray", "Muon", "Electron"],
            name="radiation", style=wx.CB_READONLY, value="Neutron")
        radiation_input.Bind(wx.EVT_COMBOBOX, self.radiationtype_changed)
        input_grid.Add(radiation_input, (y,1), (1,1))
        y += 1

        output_label = wx.StaticText(self, -1, "Output File: ")
        input_grid.Add(output_label, (y,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.output = wx.FilePickerCtrl(self, -1,
            size=(_STATICBOX_WIDTH-80, -1),
            message="Chose where to save the output file.",
            style=wx.FLP_SAVE | wx.FLP_OVERWRITE_PROMPT | wx.FLP_USE_TEXTCTRL,
            wildcard="*.xml")
        input_grid.Add(self.output, (y,1), (1,1), wx.ALL, 5)
        y += 1

        convert_btn = wx.Button(self, wx.ID_OK, "Convert")
        input_grid.Add(convert_btn, (y,0), (1,1), wx.ALL, 5)
        convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)

        help_btn = wx.Button(self, -1, "HELP")
        input_grid.Add(help_btn, (y,1), (1,1), wx.ALL, 5)
        help_btn.Bind(wx.EVT_BUTTON, self.on_help)

        section_sizer.Add(input_grid)

        vbox.Add(section_sizer, flag=wx.ALL, border=5)

        metadata_section = wx.CollapsiblePane(self, -1, "Metadata",
            size=(_STATICBOX_WIDTH+40, -1), style=wx.WS_EX_VALIDATE_RECURSIVELY)
        metadata_pane = metadata_section.GetPane()
        metadata_grid = wx.GridBagSizer(5, 5)

        metadata_section.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
            self.on_collapsible_pane)

        y = 0
        for item in self.properties:
            # Capitalise each word
            label_txt = " ".join(
                [s.capitalize() for s in item.replace('_', ' ').split(' ')])
            if item == 'run':
                label_txt = "Run Number"
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

        sample_label = wx.StaticText(metadata_pane, -1, "Sample: ")
        metadata_grid.Add(sample_label, (y,0), (1,1), wx.ALL | wx.EXPAND, 5)
        sample_btn = wx.Button(metadata_pane, -1, "Enter Sample Metadata")
        metadata_grid.Add(sample_btn, (y,1), (1,1), wx.ALL | wx.EXPAND, 5)
        sample_btn.Bind(wx.EVT_BUTTON, self.show_sample_window)
        y += 1

        source_label = wx.StaticText(metadata_pane, -1, "Source: ")
        metadata_grid.Add(source_label, (y,0), (1,1), wx.ALL | wx.EXPAND, 5)
        source_btn = wx.Button(metadata_pane, -1, "Enter Source Metadata")
        source_btn.Bind(wx.EVT_BUTTON, self.show_source_window)
        metadata_grid.Add(source_btn, (y,1), (1,1), wx.ALL | wx.EXPAND, 5)
        y += 1

        metadata_pane.SetSizer(metadata_grid)

        vbox.Add(metadata_section, proportion=0, flag=wx.ALL, border=5)

        vbox.Fit(self)
        self.SetSizer(vbox)

class ConverterWindow(widget.CHILD_FRAME):

    def __init__(self, parent=None, title='File Converter', base=None,
        manager=None, size=(PANEL_SIZE * 1.05, PANEL_SIZE / 1.25),
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
