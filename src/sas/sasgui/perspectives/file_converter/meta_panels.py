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

    def get_property_string(self, name, is_float=False):
        value = getattr(self.metadata, name)
        if value is None or value == []:
            value = ''
            is_float = False
        if isinstance(value, list):
            value = value[0]
        value = str(value)
        if is_float and not '.' in value: value += '.0'
        return value

    def on_change(self, event):
        ctrl = event.GetEventObject()
        value = ctrl.GetValue()
        name = ctrl.GetName()
        old_value = getattr(self.metadata, name)
        if value == '': value = None
        if isinstance(old_value, list): value = [value]

        setattr(self.metadata, name, value)

    def on_close(self, event=None):
        for ctrl in self._to_validate:
            ctrl.SetBackgroundColour(wx.WHITE)
            if ctrl.GetValue() == '': continue
            if not check_float(ctrl):
                msg = "{} must be a valid float".format(
                    ctrl.GetName().replace("_", " "))
                wx.PostEvent(self.parent.manager.parent.manager.parent,
                    StatusEvent(status=msg, info='error'))
                return False
        for vector_in in self._vectors:
            is_valid, invalid_ctrl = vector_in.Validate()
            if not is_valid:
                msg = "{} must be a valid float".format(
                    invalid_ctrl.GetName().replace("_", " "))
                wx.PostEvent(self.parent.manager.parent.manager.parent,
                    StatusEvent(status=msg, info='error'))
                return False
            setattr(self.metadata, vector_in.GetName(), vector_in.GetValue())
        return True

class DetectorPanel(MetadataPanel):

    def __init__(self, parent, detector, base=None, *args, **kwargs):
        if detector.name is None:
            detector.name = ''

        MetadataPanel.__init__(self, parent, detector, base, *args, **kwargs)

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def on_close(self, event=None):
        if not MetadataPanel.on_close(self, event):
            return

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
        distance = self.get_property_string("distance", is_float=True)
        distance_input.SetValue(distance)
        offset_input.SetValue(self.metadata.offset)
        orientation_input.SetValue(self.metadata.orientation)
        pixel_input.SetValue(self.metadata.pixel_size)
        beam_input.SetValue(self.metadata.beam_center)
        slit_len = self.get_property_string("slit_length", is_float=True)
        slit_input.SetValue(slit_len)

        vbox.Fit(self)
        self.SetSizer(vbox)

class SamplePanel(MetadataPanel):

    def __init__(self, parent, sample, base=None, *args, **kwargs):
        MetadataPanel.__init__(self, parent, sample, base, *args, **kwargs)
        if sample.name is None:
            sample.name = ''

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def on_close(self, event=None):
        if not MetadataPanel.on_close(self, event):
            return

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

        thickness_label = wx.StaticText(self, -1, "Thickness (mm): ")
        input_grid.Add(thickness_label, (y,0), (1,1), wx.ALL, 5)
        thickness_input = wx.TextCtrl(self, -1, name="thickness")
        input_grid.Add(thickness_input, (y,1), (1,1))
        thickness_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(thickness_input)
        y += 1

        transmission_label = wx.StaticText(self, -1, "Transmission: ")
        input_grid.Add(transmission_label, (y,0), (1,1), wx.ALL, 5)
        transmission_input = wx.TextCtrl(self, -1, name="transmission")
        input_grid.Add(transmission_input, (y,1), (1,1))
        transmission_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(transmission_input)
        y += 1

        temperature_label = wx.StaticText(self, -1, "Temperature: ")
        input_grid.Add(temperature_label, (y,0), (1,1), wx.ALL, 5)
        temperature_input = wx.TextCtrl(self, -1, name="temperature")
        temperature_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(temperature_input)
        input_grid.Add(temperature_input, (y,1), (1,1))
        temp_unit_label = wx.StaticText(self, -1, "Unit: ")
        input_grid.Add(temp_unit_label, (y,2), (1,1))
        temp_unit_input = wx.TextCtrl(self, -1, name="temperature_unit",
            size=(50,-1))
        temp_unit_input.Bind(wx.EVT_TEXT, self.on_change)
        input_grid.Add(temp_unit_input, (y,3), (1,1))
        y += 1

        position_label = wx.StaticText(self, -1, "Position (mm): ")
        input_grid.Add(position_label, (y,0), (1,1), wx.ALL, 5)
        position_input = VectorInput(self, "position")
        self._vectors.append(position_input)
        input_grid.Add(position_input.GetSizer(), (y,1), (1,2))
        y += 1

        orientation_label = wx.StaticText(self, -1, "Orientation (\xb0): ")
        input_grid.Add(orientation_label, (y,0), (1,1), wx.ALL, 5)
        orientation_input = VectorInput(self, "orientation",
            labels=["Roll: ", "Pitch: ", "Yaw: "], z_enabled=True)
        self._vectors.append(orientation_input)
        input_grid.Add(orientation_input.GetSizer(), (y,1), (1,3))
        y += 1

        details_label = wx.StaticText(self, -1, "Details: ")
        input_grid.Add(details_label, (y,0), (1,1), wx.ALL, 5)
        details_input = wx.TextCtrl(self, -1, name="details",
            style=wx.TE_MULTILINE)
        input_grid.Add(details_input, (y,1), (3,3), wx.EXPAND)
        y += 3

        name_input.SetValue(self.metadata.name)
        thickness_input.SetValue(
            self.get_property_string("thickness", is_float=True))
        transmission_input.SetValue(
            self.get_property_string("transmission", is_float=True))
        temperature_input.SetValue(
            self.get_property_string("temperature", is_float=True))
        temp_unit_input.SetValue(self.get_property_string("temperature_unit"))
        position_input.SetValue(self.metadata.position)
        orientation_input.SetValue(self.metadata.orientation)
        details_input.SetValue(self.get_property_string("details"))
        details_input.Bind(wx.EVT_TEXT, self.on_change)

        done_btn = wx.Button(self, -1, "Done")
        input_grid.Add(done_btn, (y,0), (1,1), wx.ALL, 5)
        done_btn.Bind(wx.EVT_BUTTON, self.on_close)

        section_sizer.Add(input_grid)
        vbox.Add(section_sizer, flag=wx.ALL, border=10)

        vbox.Fit(self)
        self.SetSizer(vbox)

class SourcePanel(MetadataPanel):

    def __init__(self, parent, source, base=None, *args, **kwargs):
        MetadataPanel.__init__(self, parent, source, base, *args, **kwargs)
        if source.name is None:
            source.name = ''
        source.wavelength_unit = 'nm'

        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def on_close(self, event=None):
        if not MetadataPanel.on_close(self, event):
            return

        self.parent.manager.metadata['source'] = self.metadata
        self.parent.on_close(event)

    def _do_layout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        section = wx.StaticBox(self, -1, "Source")
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

        size_label = wx.StaticText(self, -1, "Beam Size (mm): ")
        input_grid.Add(size_label, (y,0), (1,1), wx.ALL, 5)
        size_input = VectorInput(self, "beam_size")
        self._vectors.append(size_input)
        input_grid.Add(size_input.GetSizer(), (y,1), (1,1))
        y += 1

        shape_label = wx.StaticText(self, -1, "Beam Shape: ")
        input_grid.Add(shape_label, (y,0), (1,1), wx.ALL, 5)
        shape_input = wx.TextCtrl(self, -1, name="beam_shape")
        shape_input.Bind(wx.EVT_TEXT, self.on_change)
        input_grid.Add(shape_input, (y,1), (1,1))
        y += 1

        wavelength_label = wx.StaticText(self, -1, "Wavelength (nm): ")
        input_grid.Add(wavelength_label, (y,0), (1,1), wx.ALL, 5)
        wavelength_input = wx.TextCtrl(self, -1, name="wavelength",
            size=(50,-1))
        wavelength_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(wavelength_input)
        input_grid.Add(wavelength_input, (y,1), (1,1))
        y += 1

        min_wavelength_label = wx.StaticText(self, -1, "Min. Wavelength (nm): ")
        input_grid.Add(min_wavelength_label, (y,0), (1,1), wx.ALL, 5)
        min_wavelength_input = wx.TextCtrl(self, -1, name="wavelength_min",
            size=(50,-1))
        min_wavelength_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(min_wavelength_input)
        input_grid.Add(min_wavelength_input, (y,1), (1,1))
        y += 1

        max_wavelength_label = wx.StaticText(self, -1, "Max. Wavelength (nm): ")
        input_grid.Add(max_wavelength_label, (y,0), (1,1), wx.ALL, 5)
        max_wavelength_input = wx.TextCtrl(self, -1, name="wavelength_max",
            size=(50,-1))
        max_wavelength_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(max_wavelength_input)
        input_grid.Add(max_wavelength_input, (y,1), (1,1))
        y += 1

        wavelength_spread_label = wx.StaticText(self, -1,
            "Wavelength Spread (%): ")
        input_grid.Add(wavelength_spread_label, (y,0), (1,1), wx.ALL, 5)
        wavelength_spread_input = wx.TextCtrl(self, -1,
            name="wavelength_spread", size=(50,-1))
        wavelength_spread_input.Bind(wx.EVT_TEXT, self.on_change)
        self._to_validate.append(wavelength_spread_input)
        input_grid.Add(wavelength_spread_input, (y,1), (1,1))
        y += 1

        name_input.SetValue(self.get_property_string("name"))
        size_input.SetValue(self.metadata.beam_size)
        shape_input.SetValue(self.get_property_string("beam_shape"))
        wavelength_input.SetValue(
            self.get_property_string("wavelength", is_float=True))
        min_wavelength_input.SetValue(
            self.get_property_string("wavelength_min", is_float=True))
        max_wavelength_input.SetValue(
            self.get_property_string("wavelength_max", is_float=True))

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
