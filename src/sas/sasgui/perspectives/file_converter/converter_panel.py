"""
This module provides a GUI for the file converter
"""

import wx
import sys
import os
import numpy as np
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.perspectives.file_converter.converter_widgets import FileInput
from sas.sasgui.perspectives.file_converter.meta_panels import MetadataWindow
from sas.sasgui.perspectives.file_converter.meta_panels import DetectorPanel
from sas.sasgui.perspectives.file_converter.meta_panels import SamplePanel
from sas.sasgui.perspectives.file_converter.meta_panels import SourcePanel
from sas.sasgui.perspectives.file_converter.frame_select_dialog import FrameSelectDialog
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.documentation_window import DocumentationWindow
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sascalc.dataloader.data_info import Data2D
from sas.sasgui.guiframe.utils import check_float
from sas.sascalc.file_converter.cansas_writer import CansasWriter
from sas.sascalc.file_converter.otoko_loader import OTOKOLoader
from sas.sascalc.file_converter.bsl_loader import BSLLoader
from sas.sascalc.file_converter.ascii2d_loader import ASCII2DLoader
from sas.sascalc.file_converter.nxcansas_writer import NXcanSASWriter
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.data_info import Sample
from sas.sascalc.dataloader.data_info import Source
from sas.sascalc.dataloader.data_info import Vector

# Panel size
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    _STATICBOX_WIDTH = 410
    _BOX_WIDTH = 200
    PANEL_SIZE = 520
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    _STATICBOX_WIDTH = 430
    _BOX_WIDTH = 200
    PANEL_SIZE = 540
    FONT_VARIANT = 1

class ConverterPanel(ScrolledPanel, PanelBase):
    """
    This class provides the File Converter GUI
    """

    def __init__(self, parent, base=None, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        PanelBase.__init__(self)
        self.SetupScrolling()
        self.SetWindowVariant(variant=FONT_VARIANT)

        self.base = base
        self.parent = parent
        self.meta_frames = []

        # GUI inputs
        self.q_input = None
        self.iq_input = None
        self.output = None
        self.radiation_input = None
        self.convert_btn = None
        self.metadata_section = None

        self.data_type = "ascii"

        # Metadata values
        self.title = ''
        self.run = ''
        self.run_name = ''
        self.instrument = ''
        self.detector = Detector()
        self.sample = Sample()
        self.source = Source()
        self.properties = ['title', 'run', 'run_name', 'instrument']

        self.detector.name = ''
        self.source.radiation = 'neutron'

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def convert_to_cansas(self, frame_data, filepath, single_file):
        """
        Saves an array of Data1D objects to a single CanSAS file with multiple
        <SasData> elements, or to multiple CanSAS files, each with one
        <SasData> element.

        :param frame_data: If single_file is true, an array of Data1D
            objects. If single_file is false, a dictionary of the
            form *{frame_number: Data1D}*.
        :param filepath: Where to save the CanSAS file
        :param single_file: If true, array is saved as a single file,
            if false, each item in the array is saved to it's own file
        """
        writer = CansasWriter()
        entry_attrs = None
        if self.run_name != '':
            entry_attrs = { 'name': self.run_name }

        if single_file:
            writer.write(filepath, frame_data,
                sasentry_attrs=entry_attrs)
        else:
            # Folder and base filename
            [group_path, group_name] = os.path.split(filepath)
            ext = "." + group_name.split('.')[-1] # File extension
            for frame_number, frame_data in frame_data.items():
                # Append frame number to base filename
                filename = group_name.replace(ext, str(frame_number)+ext)
                destination = os.path.join(group_path, filename)
                writer.write(destination, [frame_data],
                    sasentry_attrs=entry_attrs)

    def extract_ascii_data(self, filename):
        """
        Extracts data from a single-column ASCII file

        :param filename: The file to load data from
        :return: A numpy array containing the extracted data
        """
        try:
            data = np.loadtxt(filename, dtype=str)
        except:
            is_bsl = False
            # Check if file is a BSL or OTOKO header file
            f = open(filename, 'r')
            f.readline()
            f.readline()
            bsl_metadata = f.readline().strip().split()
            f.close()
            if len(bsl_metadata) == 10:
                msg = ("Error parsing ASII data. {} looks like a BSL or OTOKO "
                    "header file.")
                raise Exception(msg.format(os.path.split(filename)[-1]))

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
                data = [s[0:-1] for s in data]
            else:
                msg = ("Error reading {}: Lines must end with a digit, comma "
                    "or semi-colon").format(filename.split('\\')[-1])
                raise Exception(msg)

        return np.array(data, dtype=np.float32)

    def extract_otoko_data(self, filename):
        """
        Extracts data from a 1D OTOKO file

        :param filename: The OTOKO file to load the data from
        :return: A numpy array containing the extracted data
        """
        loader = OTOKOLoader(self.q_input.GetPath(),
            self.iq_input.GetPath())
        otoko_data = loader.load_otoko_data()
        qdata = otoko_data.q_axis.data
        iqdata = otoko_data.data_axis.data
        if len(qdata) > 1:
            msg = ("Q-Axis file has multiple frames. Only 1 frame is "
                "allowed for the Q-Axis")
            wx.PostEvent(self.parent.manager.parent,
                StatusEvent(status=msg, info="error"))
            return
        else:
            qdata = qdata[0]

        return qdata, iqdata

    def extract_bsl_data(self, filename):
        """
        Extracts data from a 2D BSL file

        :param filename: The header file to extract the data from
        :return x_data: A 1D array containing all the x coordinates of the data
        :return y_data: A 1D array containing all the y coordinates of the data
        :return frame_data: A dictionary of the form *{frame_number: data}*, where data is a 2D numpy array containing the intensity data
        """
        loader = BSLLoader(filename)
        frames = [0]
        should_continue = True

        if loader.n_frames > 1:
            params = self.ask_frame_range(loader.n_frames)
            frames = params['frames']
            if len(frames) == 0:
                should_continue = False
        elif loader.n_rasters == 1 and loader.n_frames == 1:
            message = ("The selected file is an OTOKO file. Please select the "
            "'OTOKO 1D' option if you wish to convert it.")
            dlg = wx.MessageDialog(self,
            message,
            'Error!',
            wx.OK | wx.ICON_WARNING)
            dlg.ShowModal()
            should_continue = False
            dlg.Destroy()
        else:
            message = ("The selected data file only has 1 frame, it might be"
                " a multi-frame OTOKO file.\nContinue conversion?")
            dlg = wx.MessageDialog(self,
            message,
            'Warning!',
            wx.YES_NO | wx.ICON_WARNING)
            should_continue = (dlg.ShowModal() == wx.ID_YES)
            dlg.Destroy()

        if not should_continue:
            return None

        frame_data = loader.load_frames(frames)

        return frame_data

    def ask_frame_range(self, n_frames):
        """
        Display a dialog asking the user to input the range of frames they
        would like to export

        :param n_frames: How many frames the loaded data file has
        :return: A dictionary containing the parameters input by the user
        """
        valid_input = False
        _, ext = os.path.splitext(self.output.GetPath())
        show_single_btn = (ext == '.h5')
        dlg = FrameSelectDialog(n_frames, show_single_btn)
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
                    if not show_single_btn:
                        single_file = dlg.single_btn.GetValue()

                    if last_frame < 0 or first_frame < 0:
                        msg = "Frame values must be positive"
                    elif increment < 1:
                        msg = "Increment must be greater than or equal to 1"
                    elif first_frame > last_frame:
                        msg = "First frame must be less than last frame"
                    elif last_frame >= n_frames:
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
        frames = list(range(first_frame, last_frame + 1, increment))
        return { 'frames': frames, 'inc': increment, 'file': single_file }

    def get_metadata(self):
        # Prepare the metadata for writing to a file
        if self.run is None:
            self.run = []
        elif not isinstance(self.run, list):
            self.run = [self.run]

        run_name = None
        if len(self.run) > 0:
            run_number = self.run[0]
            run_name = { run_number: self.run_name }

        if self.title is None:
            self.title = ''

        metadata = {
            'title': self.title,
            'run': self.run,
            'run_name': run_name,
            'instrument': self.instrument,
            'detector': [self.detector],
            'sample': self.sample,
            'source': self.source
        }

        return metadata

    def convert_1d_data(self, qdata, iqdata):
        """
        Formats a 1D array of q_axis data and a 2D array of I axis data (where
        each row of iqdata is a separate row), into an array of Data1D objects
        """
        frames = []
        increment = 1
        single_file = True
        n_frames = iqdata.shape[0]
        # Standard file has 3 frames: SAS, calibration and WAS
        if n_frames > 3:
            # File has multiple frames - ask the user which ones they want to
            # export
            params = self.ask_frame_range(n_frames)
            frames = params['frames']
            increment = params['inc']
            single_file = params['file']
            if frames == []: return
        else: # Only interested in SAS data
            frames = [0]

        output_path = self.output.GetPath()
        metadata = self.get_metadata()

        frame_data = {}
        for i in frames:
            data = Data1D(x=qdata, y=iqdata[i])
            frame_data[i] = data
        if single_file:
            # Only need to set metadata on first Data1D object
            frame_data = list(frame_data.values()) # Don't need to know frame numbers
            frame_data[0].filename = output_path.split('\\')[-1]
            for key, value in metadata.items():
                setattr(frame_data[0], key, value)
        else:
            # Need to set metadata for all Data1D objects
            for datainfo in list(frame_data.values()):
                datainfo.filename = output_path.split('\\')[-1]
                for key, value in metadata.items():
                    setattr(datainfo, key, value)

        _, ext = os.path.splitext(output_path)
        if ext == '.xml':
            self.convert_to_cansas(frame_data, output_path, single_file)
        else: # ext == '.h5'
            w = NXcanSASWriter()
            w.write(frame_data, output_path)

    def convert_2d_data(self, dataset):
        metadata = self.get_metadata()
        for key, value in metadata.items():
            setattr(dataset[0], key, value)

        w = NXcanSASWriter()
        w.write(dataset, self.output.GetPath())

    def on_convert(self, event):
        """Called when the Convert button is clicked"""
        if not self.validate_inputs():
            return

        self.sample.ID = self.title

        try:
            if self.data_type == 'ascii':
                qdata = self.extract_ascii_data(self.q_input.GetPath())
                iqdata = np.array([self.extract_ascii_data(self.iq_input.GetPath())])
                self.convert_1d_data(qdata, iqdata)
            elif self.data_type == 'otoko':
                qdata, iqdata = self.extract_otoko_data(self.q_input.GetPath())
                self.convert_1d_data(qdata, iqdata)
            elif self.data_type == 'ascii2d':
                loader = ASCII2DLoader(self.iq_input.GetPath())
                data = loader.load()
                dataset = [data] # ASCII 2D only ever contains 1 frame
                self.convert_2d_data(dataset)
            else: # self.data_type == 'bsl'
                dataset = self.extract_bsl_data(self.iq_input.GetPath())
                if dataset is None:
                    # Cancelled by user
                    return
                self.convert_2d_data(dataset)

        except Exception as ex:
            msg = str(ex)
            wx.PostEvent(self.parent.manager.parent,
                StatusEvent(status=msg, info='error'))
            return

        wx.PostEvent(self.parent.manager.parent,
            StatusEvent(status="Conversion completed."))

    def on_help(self, event):
        """
        Show the File Converter documentation
        """
        tree_location = ("user/sasgui/perspectives/file_converter/"
            "file_converter_help.html")
        doc_viewer = DocumentationWindow(self, -1, tree_location,
            "", "File Converter Help")

    def validate_inputs(self):
        msg = "You must select a"
        if self.q_input.GetPath() == '' and self.data_type != 'bsl' \
            and self.data_type != 'ascii2d':
            msg += " Q Axis input file."
        elif self.iq_input.GetPath() == '':
            msg += "n Intensity input file."
        elif self.output.GetPath() == '':
            msg += " destination for the converted file."
        if msg != "You must select a":
            wx.PostEvent(self.parent.manager.parent,
                StatusEvent(status=msg, info='error'))
            return

        return True

    def show_detector_window(self, event):
        """
        Show the window for inputting Detector metadata
        """
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
        """
        Show the window for inputting Sample metadata
        """
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
        """
        Show the window for inputting Source metadata
        """
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
        """
        Resize the scrollable area to fit the metadata pane when it's
        collapsed or expanded
        """
        self.Freeze()
        self.SetupScrolling()
        self.parent.Layout()
        self.Thaw()

    def datatype_changed(self, event):
        """
        Update the UI and self.data_type when a data type radio button is
        pressed
        """
        event.Skip()
        dtype = event.GetEventObject().GetName()
        self.data_type = dtype
        if dtype == 'bsl' or dtype == 'ascii2d':
            self.q_input.SetPath("")
            self.q_input.Disable()
            self.output.SetWildcard("NXcanSAS HDF5 File (*.h5)|*.h5")
        else:
            self.q_input.Enable()
            self.radiation_input.Enable()
            self.metadata_section.Enable()
            self.output.SetWildcard("CanSAS 1D (*.xml)|*.xml|NXcanSAS HDF5 File (*.h5)|*.h5")

    def radiationtype_changed(self, event):
        event.Skip()
        rtype = event.GetEventObject().GetValue().lower()
        self.source.radiation = rtype

    def metadata_changed(self, event):
        event.Skip()
        textbox = event.GetEventObject()
        attr = textbox.GetName()
        value = textbox.GetValue().strip()

        setattr(self, attr, value)


    def _do_layout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        instructions = (
        "If converting a 1D dataset, select linked single-column ASCII files "
        "containing the Q-axis and intensity-axis data, or a 1D BSL/OTOKO file."
        " If converting 2D data, select an ASCII file in the ISIS 2D file "
        "format, or a 2D BSL/OTOKO file. Choose where to save the converted "
        "file and click convert.\n"
        "One dimensional ASCII and BSL/OTOKO files can be converted to CanSAS "
        "(XML) or NXcanSAS (HDF5) formats. Two dimensional datasets can only be"
        " converted to the NXcanSAS format.\n"
        "Metadata can also be optionally added to the output file."
        )

        instruction_label = wx.StaticText(self, -1, instructions,
            size=(_STATICBOX_WIDTH+40, -1))
        instruction_label.Wrap(_STATICBOX_WIDTH+40)
        vbox.Add(instruction_label, flag=wx.TOP | wx.LEFT | wx.RIGHT, border=5)

        section = wx.StaticBox(self, -1)
        section_sizer = wx.StaticBoxSizer(section, wx.VERTICAL)
        section_sizer.SetMinSize((_STATICBOX_WIDTH, -1))

        input_grid = wx.GridBagSizer(5, 5)

        y = 0

        data_type_label = wx.StaticText(self, -1, "Input Format: ")
        input_grid.Add(data_type_label, (y,0), (1,1),
            wx.ALIGN_CENTER_VERTICAL, 5)
        radio_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ascii_btn = wx.RadioButton(self, -1, "ASCII 1D", name="ascii",
            style=wx.RB_GROUP)
        ascii_btn.Bind(wx.EVT_RADIOBUTTON, self.datatype_changed)
        radio_sizer.Add(ascii_btn)
        ascii2d_btn = wx.RadioButton(self, -1, "ASCII 2D", name="ascii2d")
        ascii2d_btn.Bind(wx.EVT_RADIOBUTTON, self.datatype_changed)
        radio_sizer.Add(ascii2d_btn)
        otoko_btn = wx.RadioButton(self, -1, "BSL 1D", name="otoko")
        otoko_btn.Bind(wx.EVT_RADIOBUTTON, self.datatype_changed)
        radio_sizer.Add(otoko_btn)
        bsl_btn = wx.RadioButton(self, -1, "BSL 2D", name="bsl")
        bsl_btn.Bind(wx.EVT_RADIOBUTTON, self.datatype_changed)
        radio_sizer.Add(bsl_btn)
        input_grid.Add(radio_sizer, (y,1), (1,1), wx.ALL, 5)
        y += 1

        q_label = wx.StaticText(self, -1, "Q-Axis Data: ")
        input_grid.Add(q_label, (y,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.q_input = wx.FilePickerCtrl(self, -1,
            size=(_STATICBOX_WIDTH-80, -1),
            message="Chose the Q-Axis data file.",
            style=wx.FLP_USE_TEXTCTRL | wx.FLP_CHANGE_DIR)
        input_grid.Add(self.q_input, (y,1), (1,1), wx.ALL, 5)
        y += 1

        iq_label = wx.StaticText(self, -1, "Intensity Data: ")
        input_grid.Add(iq_label, (y,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.iq_input = wx.FilePickerCtrl(self, -1,
            size=(_STATICBOX_WIDTH-80, -1),
            message="Chose the Intensity-Axis data file.",
            style=wx.FLP_USE_TEXTCTRL | wx.FLP_CHANGE_DIR)
        input_grid.Add(self.iq_input, (y,1), (1,1), wx.ALL, 5)
        y += 1

        radiation_label = wx.StaticText(self, -1, "Radiation Type: ")
        input_grid.Add(radiation_label, (y,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)
        self.radiation_input = wx.ComboBox(self, -1,
            choices=["Neutron", "X-Ray", "Muon", "Electron"],
            name="radiation", style=wx.CB_READONLY, value="Neutron")
        self.radiation_input.Bind(wx.EVT_COMBOBOX, self.radiationtype_changed)
        input_grid.Add(self.radiation_input, (y,1), (1,1), wx.ALL, 5)
        y += 1

        output_label = wx.StaticText(self, -1, "Output File: ")
        input_grid.Add(output_label, (y,0), (1,1), wx.ALIGN_CENTER_VERTICAL, 5)

        self.output = FileInput(self,
            wildcard="CanSAS 1D (*.xml)|*.xml|NXcanSAS HDF5 File (*.h5)|*.h5")
        input_grid.Add(self.output.GetCtrl(), (y,1), (1,1), wx.EXPAND | wx.ALL, 5)
        y += 1

        self.convert_btn = wx.Button(self, wx.ID_OK, "Stop Converstion")
        self.convert_btn.SetLabel("Convert")
        input_grid.Add(self.convert_btn, (y,0), (1,1), wx.ALL, 5)
        self.convert_btn.Bind(wx.EVT_BUTTON, self.on_convert)

        help_btn = wx.Button(self, -1, "HELP")
        input_grid.Add(help_btn, (y,1), (1,1), wx.ALL, 5)
        help_btn.Bind(wx.EVT_BUTTON, self.on_help)

        section_sizer.Add(input_grid)

        vbox.Add(section_sizer, flag=wx.ALL, border=5)

        self.metadata_section = wx.CollapsiblePane(self, -1, "Metadata",
            size=(_STATICBOX_WIDTH+40, -1), style=wx.WS_EX_VALIDATE_RECURSIVELY)
        metadata_pane = self.metadata_section.GetPane()
        metadata_grid = wx.GridBagSizer(5, 5)

        self.metadata_section.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED,
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

        vbox.Add(self.metadata_section, proportion=0, flag=wx.ALL, border=5)

        vbox.Fit(self)
        self.SetSizer(vbox)

class ConverterWindow(widget.CHILD_FRAME):
    """Displays ConverterPanel"""

    def __init__(self, parent=None, title='File Converter', base=None,
        manager=None, size=(PANEL_SIZE * 0.96, PANEL_SIZE * 0.9),
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
