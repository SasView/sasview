import wx
import sys
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.perspectives.file_converter.converter_widgets import VectorInput
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sascalc.dataloader.data_info import Detector
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.utils import check_float

if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    _STATICBOX_WIDTH = 350
    PANEL_SIZE = 440
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    _STATICBOX_WIDTH = 380
    PANEL_SIZE = 470
    FONT_VARIANT = 1

class MetadataPanel(ScrolledPanel, PanelBase):

    def __init__(self, parent, metadata, base=None, *args, **kwargs):
        ScrolledPanel.__init__(self, parent, *args, **kwargs)
        PanelBase.__init__(self)
        self.SetupScrolling()
        self.SetWindowVariant(variant=FONT_VARIANT)

        self.base = base
        self.parent = parent
        self._to_validate = []
        self._vectors = []
        self.metadata = metadata

    def on_change(self, event):
        ctrl = event.GetEventObject()
        value = ctrl.GetValue()
        if value == '': value = None
        setattr(self.metadata, ctrl.GetName(), value)

    def on_close(self, event=None):
        for ctrl in self._to_validate:
            ctrl.SetBackgroundColour(wx.WHITE)
            if ctrl.GetValue() == '': continue
            if not check_float(ctrl):
                msg = "{} must be a valid float".format(
                    ctrl.GetName().replace("_", " "))
                wx.PostEvent(self.parent.manager.parent.manager.parent,
                    StatusEvent(status=msg, info='error'))
                return
        for vector_in in self._vectors:
            is_valid, invalid_ctrl = vector_in.Validate()
            if not is_valid:
                msg = "{} must be a valid float".format(
                    invalid_ctrl.GetName().replace("_", " "))
                wx.PostEvent(self.parent.manager.parent.manager.parent,
                    StatusEvent(status=msg, info='error'))
                return
            setattr(self.metadata, vector_in.GetName(), vector_in.GetValue())

class DetectorPanel(MetadataPanel):

    def __init__(self, parent, detector, base=None, *args, **kwargs):
        if detector.name is None:
            detector.name = ''

        MetadataPanel.__init__(self, parent, detector, base, *args, **kwargs)

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def on_close(self, event=None):
        MetadataPanel.on_close(self, event)

        self.parent.manager.metadata['detector'] = [self.metadata]
        self.parent.on_close(event)

    def _do_layout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        section = wx.StaticBox(self, -1, "Detector")
        section_sizer = wx.StaticBoxSizer(section, wx.VERTICAL)
        section_sizer.SetMinSize((_STATICBOX_WIDTH, -1))

        input_grid = wx.GridBagSizer(5, 5)

        y = 0
        name_label = wx.StaticText(self, -1, "Name: ")
        input_grid.Add(name_label, (y,0), (1,1), wx.ALL, 5)
        name_input = wx.TextCtrl(self, -1, name="name")
        input_grid.Add(name_input, (y,1), (1,1))
        name_input.Bind(wx.EVT_TEXT, self.on_change)
        y += 1

        distance_label = wx.StaticText(self, -1,
            "Distance (mm): ")
        input_grid.Add(distance_label, (y, 0), (1,1), wx.ALL, 5)
        distance_input = wx.TextCtrl(self, -1,
            name="distance", size=(50,-1))
        input_grid.Add(distance_input, (y,1), (1,1))
        distance_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(distance_input)
        y += 1

        offset_label = wx.StaticText(self, -1, "Offset (mm): ")
        input_grid.Add(offset_label, (y,0), (1,1), wx.ALL, 5)
        offset_input = VectorInput(self, "offset")
        input_grid.Add(offset_input.GetSizer(), (y,1), (1,1))
        self._vectors.append(offset_input)
        y += 1

        orientation_label = wx.StaticText(self, -1, "Orientation (\xb0): ")
        input_grid.Add(orientation_label, (y,0), (1,1), wx.ALL, 5)
        orientation_input = VectorInput(self, "orientation", z_enabled=True,
            labels=["Roll: ", "Pitch: ", "Yaw: "])
        input_grid.Add(orientation_input.GetSizer(), (y,1), (1,1))
        self._vectors.append(orientation_input)
        y += 1

        pixel_label = wx.StaticText(self, -1, "Pixel Size (mm): ")
        input_grid.Add(pixel_label, (y,0), (1,1), wx.ALL, 5)
        pixel_input = VectorInput(self, "pixel_size")
        input_grid.Add(pixel_input.GetSizer(), (y,1), (1,1))
        self._vectors.append(pixel_input)
        y += 1

        beam_label = wx.StaticText(self, -1, "Beam Center (mm): ")
        input_grid.Add(beam_label, (y,0), (1,1), wx.ALL, 5)
        beam_input = VectorInput(self, "beam_center")
        input_grid.Add(beam_input.GetSizer(), (y,1), (1,1))
        self._vectors.append(beam_input)
        y += 1

        slit_label = wx.StaticText(self, -1, "Slit Length (mm): ")
        input_grid.Add(slit_label, (y,0), (1,1), wx.ALL, 5)
        slit_input = wx.TextCtrl(self, -1, name="slit_length", size=(50,-1))
        input_grid.Add(slit_input, (y,1), (1,1))
        slit_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(slit_input)
        y += 1

        done_btn = wx.Button(self, -1, "Done")
        input_grid.Add(done_btn, (y,0), (1,1), wx.ALL, 5)
        done_btn.Bind(wx.EVT_BUTTON, self.on_close)

        section_sizer.Add(input_grid)
        vbox.Add(section_sizer, flag=wx.ALL, border=10)

        name_input.SetValue(self.metadata.name)
        distance = self.metadata.distance
        if distance is None: distance = ''
        elif '.' not in distance: distance += '.0'
        distance_input.SetValue(str(distance))
        offset_input.SetValue(self.metadata.offset)
        orientation_input.SetValue(self.metadata.orientation)
        pixel_input.SetValue(self.metadata.pixel_size)
        beam_input.SetValue(self.metadata.beam_center)
        slit_len = self.metadata.slit_length
        if slit_len is None: slit_len = ''
        elif '.' not in slit_len: slit_len += '.0'
        slit_input.SetValue(slit_len)

        vbox.Fit(self)
        self.SetSizer(vbox)

class SamplePanel(MetadataPanel):

    def __init__(self, parent, sample, base=None, *args, **kwargs):
        MetadataPanel.__init__(self, parent, sample, base, *args, **kwargs)

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def on_close(self, event=None):
        MetadataPanel.on_close(self, event)

        self.parent.manager.metadata['sample'] = self.metadata
        self.parent.on_close(event)

    def _do_layout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        section = wx.StaticBox(self, -1, "Sample")
        section_sizer = wx.StaticBoxSizer(section, wx.VERTICAL)
        section_sizer.SetMinSize((_STATICBOX_WIDTH, -1))

        input_grid = wx.GridBagSizer(5, 5)

        y = 0
        name_label = wx.StaticText(self, -1, "Name: ")
        input_grid.Add(name_label, (y,0), (1,1), wx.ALL, 5)
        name_input = wx.TextCtrl(self, -1, name="name")
        input_grid.Add(name_input, (y,1), (1,1))
        name_input.Bind(wx.EVT_TEXT, self.on_change)
        y += 1

        id_label = wx.StaticText(self, -1, "ID: ")
        input_grid.Add(id_label, (y,0), (1,1), wx.ALL, 5)
        id_input = wx.TextCtrl(self, -1, name="ID")
        input_grid.Add(id_input, (y,1), (1,1))
        id_input.Bind(wx.EVT_TEXT, self.on_change)
        y += 1

        thickness_label = wx.StaticText(self, -1, "Thickness (mm): ")
        input_grid.Add(thickness_label, (y,0), (1,1), wx.ALL, 5)
        thickness_input = wx.TextCtrl(self, -1, name="thickness")
        input_grid.Add(thickness_input, (y,1), (1,1))
        thickness_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(thickness_input)
        y += 1

        name_input.SetValue(self.metadata.name)
        id_input.SetValue(self.metadata.ID)
        thickness = self.metadata.thickness
        if thickness is None:
            thickness = ''
        thickness_input.SetValue(str(thickness))

        done_btn = wx.Button(self, -1, "Done")
        input_grid.Add(done_btn, (y,0), (1,1), wx.ALL, 5)
        done_btn.Bind(wx.EVT_BUTTON, self.on_close)

        section_sizer.Add(input_grid)
        vbox.Add(section_sizer, flag=wx.ALL, border=10)

        vbox.Fit(self)
        self.SetSizer(vbox)

class MetadataWindow(widget.CHILD_FRAME):

    def __init__(self, PanelClass, parent=None, title='', base=None,
        manager=None, size=(PANEL_SIZE, PANEL_SIZE*0.8), metadata=None,
         *args, **kwargs):
        kwargs['title'] = title
        kwargs['size'] = size
        widget.CHILD_FRAME.__init__(self, parent, *args, **kwargs)

        self.manager = manager
        self.panel = PanelClass(self, metadata, base=None)
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def on_close(self, event):
        if self.manager is not None:
            self.manager.meta_frames.remove(self)
        self.Destroy()
