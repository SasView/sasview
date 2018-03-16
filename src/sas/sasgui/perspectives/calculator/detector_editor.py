

import wx
import sys
from copy import deepcopy
from sas.sascalc.dataloader.data_info import Detector
from sas.sasgui.guiframe.utils import check_float

_BOX_WIDTH = 60
if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 465
    PANEL_WIDTH = 500
    PANEL_HEIGHT = 450
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 480
    PANEL_WIDTH = 550
    PANEL_HEIGHT = 480
    FONT_VARIANT = 1

class DetectorDialog(wx.Dialog):
    def __init__(self, parent=None, manager=None, detector=None,
                        title="Detector Editor",
                        size=(PANEL_WIDTH, PANEL_HEIGHT)):
        wx.Dialog.__init__(self, parent=parent, id=id, title=title, size=size)
        try:
            self.parent = parent
            self.manager = manager
            self._detector = detector

            self._reset_detector = deepcopy(detector)
            self._notes = ""
            self._description = "Edit Detector"
            self._do_layout()
            self.set_values()
        except:
            print("error", sys.exc_info()[1])

    def _define_structure(self):
        """
            define initial sizer
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_detector = wx.StaticBox(self, -1, str("Edit Selected Detector"))
        self.boxsizer_detector = wx.StaticBoxSizer(self.box_detector,
                                                    wx.VERTICAL)
        detector_box = wx.StaticBox(self, -1, "Edit Number of Detectors")
        self.detector_sizer = wx.StaticBoxSizer(detector_box, wx.VERTICAL)
        self.detector_sizer.SetMinSize((_STATICBOX_WIDTH, -1))
        self.detector_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detector_hint_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.detector_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.detector_hint_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.instrument_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.distance_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.offset_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.orientation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.beam_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.pixel_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.slit_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_detector(self):
        """
            Do the layout for detector related widgets
        """
        detector_name_txt = wx.StaticText(self, -1, "Detector:")
        hint_detector_txt = 'Current available detector.'
        detector_name_txt.SetToolTipString(hint_detector_txt)
        self.detector_cbox = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        hint_detector_name_txt = 'Name of detectors.'
        self.detector_cbox.SetToolTipString(hint_detector_name_txt)

        self.bt_add_detector = wx.Button(self, -1, "Add")
        self.bt_add_detector.SetToolTipString("Add data's detector.")
        self.bt_add_detector.Bind(wx.EVT_BUTTON, self.add_detector)

        self.bt_remove_detector = wx.Button(self, -1, "Remove")
        self.bt_remove_detector.SetToolTipString("Remove data's detector.")
        self.bt_remove_detector.Bind(wx.EVT_BUTTON, self.remove_detector)

        self.detector_button_sizer.AddMany([(detector_name_txt, 0, wx.LEFT, 15),
                                     (self.detector_cbox, 0, wx.LEFT, 5),
                                     (self.bt_add_detector, 0, wx.LEFT, 10),
                                     (self.bt_remove_detector, 0, wx.LEFT, 5)])
        detector_hint_txt = 'No detector is available for this data.'
        self.detector_txt = wx.StaticText(self, -1, detector_hint_txt)
        self.detector_hint_sizer.Add(self.detector_txt, 0, wx.LEFT, 10)
        self.detector_sizer.AddMany([(self.detector_button_sizer, 0,
                                       wx.ALL, 10),
                                     (self.detector_hint_sizer, 0, wx.ALL, 10)])

        self.fill_detector_combox()
        self.enable_detector()

    def _layout_instrument_sizer(self):
        """
            Do the layout for instrument related widgets
        """
        #Instrument
        instrument_name_txt = wx.StaticText(self, -1, 'Instrument Name : ')
        self.instrument_name_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH * 5, 20), style=0)
        self.instrument_sizer.AddMany([(instrument_name_txt, 0,
                                        wx.LEFT | wx.RIGHT, 10),
                                    (self.instrument_name_tcl, 0, wx.EXPAND)])
    def _layout_distance(self):
        """
            Do the  layout for distance related widgets
        """
        distance_txt = wx.StaticText(self, -1, 'Sample to Detector Distance : ')
        self.distance_tcl = wx.TextCtrl(self, -1,
                                         size=(_BOX_WIDTH, 20), style=0)
        distance_unit_txt = wx.StaticText(self, -1, 'Unit: ')
        self.distance_unit_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH, 20), style=0)
        self.distance_sizer.AddMany([(distance_txt, 0, wx.LEFT | wx.RIGHT, 10),
                                     (self.distance_tcl, 0, wx.RIGHT, 10),
                                     (distance_unit_txt, 0, wx.EXPAND),
                                     (self.distance_unit_tcl, 0, wx.RIGHT, 10)])

    def _layout_offset(self):
        """
            Do the  layout for offset related widgets
        """
        #Offset
        offset_txt = wx.StaticText(self, -1, 'Offset:')
        x_offset_txt = wx.StaticText(self, -1, 'x = ')
        self.x_offset_tcl = wx.TextCtrl(self, -1,
                                        size=(_BOX_WIDTH, 20), style=0)
        y_offset_txt = wx.StaticText(self, -1, 'y = ')
        self.y_offset_tcl = wx.TextCtrl(self, -1,
                                         size=(_BOX_WIDTH, 20), style=0)
        z_offset_txt = wx.StaticText(self, -1, 'z = ')
        self.z_offset_tcl = wx.TextCtrl(self, -1,
                                         size=(_BOX_WIDTH, 20), style=0)
        offset_unit_txt = wx.StaticText(self, -1, 'Unit: ')
        self.offset_unit_tcl = wx.TextCtrl(self, -1,
                                           size=(_BOX_WIDTH, 20), style=0)
        self.offset_sizer.AddMany([(offset_txt, 0, wx.LEFT | wx.RIGHT, 10),
                                     (x_offset_txt, 0, wx.LEFT, 30),
                                     (self.x_offset_tcl, 0, wx.RIGHT, 10),
                                     (y_offset_txt, 0, wx.EXPAND),
                                     (self.y_offset_tcl, 0, wx.RIGHT, 10),
                                     (z_offset_txt, 0, wx.EXPAND),
                                     (self.z_offset_tcl, 0, wx.RIGHT, 10),
                                     (offset_unit_txt, 0, wx.EXPAND),
                                     (self.offset_unit_tcl, 0, wx.RIGHT, 10)])

    def _layout_orientation(self):
        """
            Do the  layout for orientation related widgets
        """
        #Orientation
        orientation_txt = wx.StaticText(self, -1, 'Orientation:')
        x_orientation_txt = wx.StaticText(self, -1, 'x = ')
        self.x_orientation_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH, 20), style=0)
        y_orientation_txt = wx.StaticText(self, -1, 'y = ')
        self.y_orientation_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)
        z_orientation_txt = wx.StaticText(self, -1, 'z = ')
        self.z_orientation_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH, 20), style=0)
        orientation_unit_txt = wx.StaticText(self, -1, 'Unit: ')
        self.orientation_unit_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)
        self.orientation_sizer.AddMany([(orientation_txt, 0,
                                          wx.LEFT | wx.RIGHT, 10),
                                     (x_orientation_txt, 0, wx.LEFT, 7),
                                     (self.x_orientation_tcl, 0, wx.RIGHT, 10),
                                     (y_orientation_txt, 0, wx.EXPAND),
                                     (self.y_orientation_tcl, 0, wx.RIGHT, 10),
                                     (z_orientation_txt, 0, wx.EXPAND),
                                     (self.z_orientation_tcl, 0, wx.RIGHT, 10),
                                     (orientation_unit_txt, 0, wx.EXPAND),
                            (self.orientation_unit_tcl, 0, wx.RIGHT, 10)])

    def _layout_beam_center(self):
        """
            Do the  layout for beam center related widgets
        """
        #Beam center
        beam_center_txt = wx.StaticText(self, -1, 'Beam Center:')
        x_beam_center_txt = wx.StaticText(self, -1, 'x = ')
        self.x_beam_center_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH, 20), style=0)
        y_beam_center_txt = wx.StaticText(self, -1, 'y = ')
        self.y_beam_center_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH, 20), style=0)
        z_beam_center_txt = wx.StaticText(self, -1, 'z = ')
        self.z_beam_center_tcl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH, 20), style=0)
        beam_center_unit_txt = wx.StaticText(self, -1, 'Unit: ')
        self.beam_center_unit_tcl = wx.TextCtrl(self, -1,
                                                 size=(_BOX_WIDTH, 20), style=0)
        self.beam_sizer.AddMany([(beam_center_txt, 0, wx.LEFT | wx.RIGHT, 10),
                                     (x_beam_center_txt, 0, wx.EXPAND),
                                     (self.x_beam_center_tcl, 0, wx.RIGHT, 10),
                                     (y_beam_center_txt, 0, wx.EXPAND),
                                     (self.y_beam_center_tcl, 0, wx.RIGHT, 10),
                                     (z_beam_center_txt, 0, wx.EXPAND),
                                     (self.z_beam_center_tcl, 0, wx.RIGHT, 10),
                                     (beam_center_unit_txt, 0, wx.EXPAND),
                                (self.beam_center_unit_tcl, 0, wx.RIGHT, 10)])

    def _layout_pixel_size(self):
        """
            Do the  layout for pixel size related widgets
        """
        #Pixel Size
        pixel_size_txt = wx.StaticText(self, -1, 'Pixel Size:')
        x_pixel_size_txt = wx.StaticText(self, -1, 'x = ')
        self.x_pixel_size_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)
        y_pixel_size_txt = wx.StaticText(self, -1, 'y = ')
        self.y_pixel_size_tcl = wx.TextCtrl(self, -1,
                                            size=(_BOX_WIDTH, 20), style=0)
        z_pixel_size_txt = wx.StaticText(self, -1, 'z = ')
        self.z_pixel_size_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)
        pixel_size_unit_txt = wx.StaticText(self, -1, 'Unit: ')
        self.pixel_size_unit_tcl = wx.TextCtrl(self, -1,
                                             size=(_BOX_WIDTH, 20), style=0)
        self.pixel_sizer.AddMany([(pixel_size_txt, 0, wx.LEFT | wx.RIGHT, 10),
                                     (x_pixel_size_txt, 0, wx.LEFT, 17),
                                     (self.x_pixel_size_tcl, 0, wx.RIGHT, 10),
                                     (y_pixel_size_txt, 0, wx.EXPAND),
                                     (self.y_pixel_size_tcl, 0, wx.RIGHT, 10),
                                     (z_pixel_size_txt, 0, wx.EXPAND),
                                     (self.z_pixel_size_tcl, 0, wx.RIGHT, 10),
                                     (pixel_size_unit_txt, 0, wx.EXPAND),
                                (self.pixel_size_unit_tcl, 0, wx.RIGHT, 10)])

    def _layout_slit_length(self):
        """
            Do the  layout for slit length related widgets
        """
        #slit length
        slit_length_txt = wx.StaticText(self, -1, 'Slit Length: ')
        self.slit_length_tcl = wx.TextCtrl(self, -1,
                                            size=(_BOX_WIDTH, 20), style=0)
        slit_length_unit_txt = wx.StaticText(self, -1, 'Unit: ')
        self.slit_length_unit_tcl = wx.TextCtrl(self, -1,
                                                 size=(_BOX_WIDTH, 20), style=0)
        self.slit_sizer.AddMany([(slit_length_txt, 0, wx.LEFT, 10),
                                     (self.slit_length_tcl, 0, wx.RIGHT, 10),
                                     (slit_length_unit_txt, 0, wx.EXPAND),
                            (self.slit_length_unit_tcl, 0, wx.RIGHT, 10)])

    def _layout_button(self):
        """
            Do the layout for the button widgets
        """
        self.bt_apply = wx.Button(self, -1, 'Apply')
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)
        self.bt_apply.SetToolTipString("Apply current changes to the detector.")
        self.bt_cancel = wx.Button(self, -1, 'Cancel')
        self.bt_cancel.SetToolTipString("Cancel current changes.")
        self.bt_cancel.Bind(wx.EVT_BUTTON, self.on_click_cancel)
        self.bt_close = wx.Button(self, wx.ID_CANCEL, 'Close')
        self.bt_close.SetToolTipString("Close window.")
        self.button_sizer.AddMany([(self.bt_apply, 0, wx.LEFT, 200),
                                   (self.bt_cancel, 0, wx.LEFT, 10),
                                   (self.bt_close, 0, wx.LEFT, 10)])

    def _do_layout(self, data=None):
        """
             Draw the current panel
        """
        self._define_structure()
        self._layout_detector()
        self._layout_instrument_sizer()
        self._layout_distance()
        self._layout_offset()
        self._layout_orientation()
        self._layout_beam_center()
        self._layout_pixel_size()
        self._layout_slit_length()
        self._layout_button()

        self.boxsizer_detector.AddMany([(self.instrument_sizer, 0,
                                          wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                   (self.distance_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                   (self.offset_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                   (self.orientation_sizer, 0,
                                    wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                   (self.beam_sizer, 0,
                                    wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                   (self.pixel_sizer, 0,
                                    wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                   (self.slit_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.main_sizer.AddMany([(self.detector_sizer, 0, wx.ALL, 10),
                                 (self.boxsizer_detector, 0, wx.ALL, 10),
                                  (self.button_sizer, 0,
                                    wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])

        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)

    def reset_detector(self):
        """
            put the default value of the detector back to the current detector
        """
        self._detector = deepcopy(self._reset_detector)
        self.detector_cbox.Clear()
        self.fill_detector_combox()
        self.set_values()

    def set_manager(self, manager):
        """
            Set manager of this window
        """
        self.manager = manager

    def fill_detector_combox(self):
        """
            fill the current combobox with the available detector
        """
        for detector in self._detector:
            pos = self.detector_cbox.Append(str(detector.name))
            self.detector_cbox.SetClientData(pos, detector)
            self.detector_cbox.SetSelection(pos)
            self.detector_cbox.SetStringSelection(str(detector.name))

    def reset_detector_combobox(self, edited_detector):
        """
            take all edited editor and reset clientdata of detector combo box
        """
        for position in range(self.detector_cbox.GetCount()):
            detector = self.detector_cbox.GetClientData(position)
            if detector == edited_detector:
                detector = edited_detector
                self.detector_cbox.SetString(position, str(detector.name))
                self.detector_cbox.SetClientData(position, detector)
                self.detector_cbox.SetStringSelection(str(detector.name))

    def add_detector(self, event):
        """
            Append empty detector to data's list of detector
        """

        if not self.detector_cbox.IsEnabled():
            self.detector_cbox.Enable()
        detector = Detector()
        self._detector.append(detector)
        position = self.detector_cbox.Append(str(detector.name))
        self.detector_cbox.SetClientData(position, detector)
        self.detector_cbox.SetSelection(position)
        self.enable_detector()
        self.set_values()

    def remove_detector(self, event):
        """
            Remove detector to data's list of detector
        """
        if self.detector_cbox.IsEnabled():
            if self.detector_cbox.GetCount() > 1:
                position = self.detector_cbox.GetCurrentSelection()
                detector = self.detector_cbox.GetClientData(position)
                if detector in self._detector:
                    self._detector.remove(detector)
                    self.detector_cbox.Delete(position)
                    #set the combo box box the next available item
                    position = self.detector_cbox.GetCount()
                    if position > 0:
                        position -= 1
                    self.detector_cbox.SetSelection(position)
                    self.set_values()
        #disable or enable the combo box when necessary
        self.enable_detector()

    def enable_detector(self):
        """
            Enable /disable widgets crelated to detector
        """
        if self._detector is not None and self.detector_cbox.GetCount() > 0:
            self.detector_cbox.Enable()
            self.bt_remove_detector.Enable()
            n_detector = self.detector_cbox.GetCount()
            detector_hint_txt = 'Detectors available: %s ' % str(n_detector)
            if len(self._detector) > 1:
                self.bt_remove_detector.Enable()
            else:
                self.bt_remove_detector.Disable()
        else:
            self.detector_cbox.Disable()
            self.bt_remove_detector.Disable()
            detector_hint_txt = 'No detector is available for this data.'
        self.detector_txt.SetLabel(detector_hint_txt)

    def set_detector(self, detector):
        """
            set detector for data
        """
        if self._detector is None:
            return
        if self._detector:
            for item in self._detector:
                if item == detector:
                    item = detector
                    self.reset_detector_combobox(edited_detector=detector)
                    return

    def get_current_detector(self):
        """
        """
        if not self.detector_cbox.IsEnabled():
            return None, None, None
        position = self.detector_cbox.GetSelection()
        if position == wx.NOT_FOUND:
            return None, None, None
        detector_name = self.detector_cbox.GetStringSelection()
        detector = self.detector_cbox.GetClientData(position)
        return detector, detector_name, position

    def set_values(self):
        """
            take the detector values of the current data and display them
            through the panel
        """
        detector, _, _ = self.get_current_detector()
        if detector is None:
            return
        self.instrument_name_tcl.SetValue(str(detector.name))
        #Distance
        distance = detector.distance
        self.distance_tcl.SetValue(str(distance))
        self.distance_unit_tcl.SetValue(str(detector.distance_unit))
        #Offset
        x, y, z = detector.offset.x, detector.offset.y , detector.offset.z
        self.x_offset_tcl.SetValue(str(x))
        self.y_offset_tcl.SetValue(str(y))
        self.z_offset_tcl.SetValue(str(z))
        self.offset_unit_tcl.SetValue(str(detector.offset_unit))
        #Orientation
        x, y = detector.orientation.x, detector.orientation.y
        z = detector.orientation.z
        self.x_orientation_tcl.SetValue(str(x))
        self.y_orientation_tcl.SetValue(str(y))
        self.z_orientation_tcl.SetValue(str(z))
        self.orientation_unit_tcl.SetValue(str(detector.orientation_unit))
        #Beam center
        x, y = detector.beam_center.x, detector.beam_center.y
        z = detector.beam_center.z
        self.x_beam_center_tcl.SetValue(str(x))
        self.y_beam_center_tcl.SetValue(str(y))
        self.z_beam_center_tcl.SetValue(str(z))
        self.beam_center_unit_tcl.SetValue(str(detector.beam_center_unit))
        #Pixel size 
        x, y = detector.pixel_size.x, detector.pixel_size.y
        z = detector.pixel_size.z
        self.x_pixel_size_tcl.SetValue(str(x))
        self.y_pixel_size_tcl.SetValue(str(y))
        self.z_pixel_size_tcl.SetValue(str(z))
        self.pixel_size_unit_tcl.SetValue(str(detector.pixel_size_unit))
        #Slit length
        slit_length = detector.slit_length
        self.slit_length_tcl.SetValue(str(detector.slit_length))
        self.slit_length_unit_tcl.SetValue(str(detector.slit_length_unit))

    def get_detector(self):
        """
            return the current detector
        """
        return self._detector

    def get_notes(self):
        """
            return notes
        """
        return self._notes

    def on_change_instrument(self):
        """
            Change instrument
        """
        detector, detector_name, position = self.get_current_detector()
        if detector is None:
            return
        #Change the name of the detector
        name = self.instrument_name_tcl.GetValue().lstrip().rstrip()
        if name == "" or name == str(None):
            name = None
        if detector_name != name:
            self._notes += " Instrument's "
            self._notes += "name from %s to %s \n" % (detector_name, name)
            detector.name = name
            self.detector_cbox.SetString(position, str(detector.name))
            self.detector_cbox.SetClientData(position, detector)
            self.detector_cbox.SetStringSelection(str(detector.name))

    def on_change_distance(self):
        """
            Change distance of the sample to the detector
        """
        detector, _, position = self.get_current_detector()
        if detector is None:
            return
        #Change the distance
        distance = self.distance_tcl.GetValue().lstrip().rstrip()
        if distance == "" or distance == str(None):
            distance = None
            detector.distance = distance
        else:
            if check_float(self.distance_tcl):
                if detector.distance != float(distance):
                    self._notes += " Change Distance from"
                    self._notes += " %s to %s \n" % (detector.distance, distance)
                    detector.distance = float(distance)
            else:
                self._notes += "Error: Expected a float for "
                self._notes += " the distance won't changes "
                self._notes += "%s to %s" % (detector.distance, distance)
        #change the distance unit
        unit = self.distance_unit_tcl.GetValue().lstrip().rstrip()
        if detector.distance_unit != unit:
            self._notes += " Change distance's unit from "
            self._notes += "%s to %s" % (detector.distance_unit, unit)

        self.detector_cbox.SetString(position, str(detector.name))
        self.detector_cbox.SetClientData(position, detector)
        self.detector_cbox.SetStringSelection(str(detector.name))

    def on_change_offset(self):
        """
            Change the detector offset
        """
        detector, _, position = self.get_current_detector()
        if detector is None:
            return
        #Change x coordinate
        x_offset = self.x_offset_tcl.GetValue().lstrip().rstrip()
        if x_offset == "" or x_offset == str(None):
            x_offset = None
            detector.offset.x = x_offset
        else:
            if check_float(self.x_offset_tcl):
                if detector.offset.x != float(x_offset):
                    self._notes += "Change x of offset from"
                    self._notes += " %s to %s \n" % (detector.offset.x,
                                                      x_offset)
                    detector.offset.x = float(x_offset)
            else:
                self._notes += "Error: Expected a float for the offset 's x "
                self._notes += "won't changes x offset"
                self._notes += " from %s to %s" % (detector.offset.x, x_offset)
        #Change y coordinate
        y_offset = self.y_offset_tcl.GetValue().lstrip().rstrip()
        if y_offset == "" or y_offset == str(None):
            y_offset = None
            detector.offset.y = y_offset
        else:
            if check_float(self.y_offset_tcl):
                if detector.offset.y != float(y_offset):
                    self._notes += "Change y of offset from "
                    self._notes += "%s to %s \n" % (detector.offset.y, y_offset)
                    detector.offset.y = float(y_offset)
            else:
                self._notes += "Error: Expected a float for the offset 's y "
                self._notes += "won't changes y "
                self._notes += "offset from %s to %s" % (detector.offset.y,
                                                         y_offset)
        #Change z coordinate
        z_offset = self.z_offset_tcl.GetValue().lstrip().rstrip()
        if z_offset == "" or z_offset == str(None):
            z_offset = None
            detector.offset.z = z_offset
        else:
            if check_float(self.z_offset_tcl):
                if detector.offset.z != float(z_offset):
                    self._notes += "Change z of offset from"
                    self._notes += " %s to %s \n" % (detector.offset.z,
                                                              z_offset)
                    detector.offset.z = float(z_offset)
            else:
                self._notes += "Error: Expected a float for the offset 's x "
                self._notes += "won't changes z"
                self._notes += "offset from %s to %s" % (detector.offset.z,
                                                       z_offset)
        #change the offset unit
        unit = self.offset_unit_tcl.GetValue().lstrip().rstrip()
        if detector.offset_unit != unit:
            self._notes += " Change Offset's"
            self._notes += "unit from %s to %s" % (detector.offset_unit, unit)

        self.detector_cbox.SetString(position, str(detector.name))
        self.detector_cbox.SetClientData(position, detector)
        self.detector_cbox.SetStringSelection(str(detector.name))

    def on_change_orientation(self):
        """
            Change the detector orientation
        """
        detector, _, position = self.get_current_detector()
        if detector is None:
            return
        #Change x coordinate
        x_orientation = self.x_orientation_tcl.GetValue().lstrip().rstrip()
        if x_orientation == "" or x_orientation == str(None):
            x_orientation = None
            detector.orientation.x = x_orientation
        else:
            if check_float(self.x_orientation_tcl):
                if detector.orientation.x != float(x_orientation):
                    self._notes += "Change x of orientation from "
                    self._notes += "%s to %s \n" % (detector.orientation.x,
                                                   x_orientation)
                    detector.orientation.x = float(x_orientation)
            else:
                self._notes += "Error: Expected a float for the orientation "
                self._notes += "'s x  won't changes x orientation from "
                self._notes += "%s to %s" % (detector.orientation.x,
                                              x_orientation)
        #Change y coordinate
        y_orientation = self.y_orientation_tcl.GetValue().lstrip().rstrip()
        if y_orientation == "" or y_orientation == str(None):
            y_orientation = None
            detector.orientation.y = y_orientation
        else:
            if check_float(self.y_orientation_tcl):
                if detector.orientation.y != float(y_orientation):
                    self._notes += "Change y of orientation from "
                    self._notes += "%s to %s \n" % (detector.orientation.y,
                                                     y_orientation)
                    detector.orientation.y = float(y_orientation)
            else:
                self._notes += "Error: Expected a float for the orientation's "
                self._notes += " y won't changes y orientation from "
                self._notes += "%s to %s" % (detector.orientation.y,
                                            y_orientation)
        #Change z coordinate
        z_orientation = self.z_orientation_tcl.GetValue().lstrip().rstrip()
        if z_orientation == "" or z_orientation == str(None):
            z_orientation = None
            detector.orientation.z = z_orientation
        else:
            if check_float(self.z_orientation_tcl):
                if detector.orientation.z != float(z_orientation):
                    self._notes += "Change z of offset from "
                    self._notes += "%s to %s \n" % (detector.orientation.z,
                                                   z_orientation)
                    detector.orientation.z = float(z_orientation)
            else:
                self._notes += "Error: Expected a float for the orientation 's"
                self._notes += " x won't changes z orientation from "
                self._notes += "%s to %s" % (detector.orientation.z,
                                              z_orientation)
        #change the orientation unit
        unit = self.orientation_unit_tcl.GetValue().lstrip().rstrip()
        if detector.orientation_unit != unit:
            self._notes += " Change orientation's unit from "
            self._notes += "%s to %s" % (detector.orientation_unit, unit)

        self.detector_cbox.SetString(position, str(detector.name))
        self.detector_cbox.SetClientData(position, detector)
        self.detector_cbox.SetStringSelection(str(detector.name))

    def on_change_beam_center(self):
        """
            Change the detector beam center
        """

        detector, _, position = self.get_current_detector()
        if detector is None:
            return
        #Change x coordinate
        x_beam_center = self.x_beam_center_tcl.GetValue().lstrip().rstrip()
        if x_beam_center == "" or x_beam_center == str(None):
            x_beam_center = None
            detector.beam_center.x = x_beam_center
        else:
            if check_float(self.x_beam_center_tcl):
                if detector.beam_center.x != float(x_beam_center):
                    self._notes += "Change x of offset from "
                    self._notes += "%s to %s \n" % (detector.beam_center.x,
                                                     x_beam_center)
                    detector.beam_center.x = float(x_beam_center)
            else:
                self._notes += "Error: Expected a float for the beam "
                self._notes += "center 's x won't changes x beam center from "
                self._notes += "%s to %s" % (detector.beam_center.x,
                                            x_beam_center)
        #Change y coordinate
        y_beam_center = self.y_beam_center_tcl.GetValue().lstrip().rstrip()
        if y_beam_center == "" or y_beam_center == str(None):
            y_beam_center = None
            detector.beam_center.y = y_beam_center
        else:
            if check_float(self.y_beam_center_tcl):
                if detector.beam_center.y != float(y_beam_center):
                    self._notes += "Change y of beam center from "
                    self._notes += "%s to %s \n" % (detector.beam_center.y,
                                                     y_beam_center)
                    detector.beam_center.y = float(y_beam_center)
            else:
                self._notes += "Error: Expected a float for the beam "
                self._notes += "center 's y won't changes y beam center from "
                self._notes += "%s to %s" % (detector.beam_center.y,
                                              y_beam_center)
        #Change z coordinate
        z_beam_center = self.z_beam_center_tcl.GetValue().lstrip().rstrip()
        if z_beam_center == "" or z_beam_center == str(None):
            z_beam_center = None
            detector.beam_center.z = z_beam_center
        else:
            if check_float(self.z_beam_center_tcl):
                if detector.beam_center.z != float(z_beam_center):
                    self._notes += "Change z of beam center from "
                    self._notes += "%s to %s \n" % (detector.beam_center.z,
                                                     z_beam_center)
                    detector.beam_center.z = float(z_beam_center)
            else:
                self._notes += "Error: Expected a float for the offset 's x "
                self._notes += "won't changes z beam center from "
                self._notes += "%s to %s" % (detector.beam_center.z,
                                            z_beam_center)
        #change the beam center unit
        unit = self.beam_center_unit_tcl.GetValue().lstrip().rstrip()
        if detector.beam_center_unit != unit:
            self._notes += " Change beam center's unit from "
            self._notes += "%s to %s" % (detector.beam_center_unit, unit)

        self.detector_cbox.SetString(position, str(detector.name))
        self.detector_cbox.SetClientData(position, detector)
        self.detector_cbox.SetStringSelection(str(detector.name))

    def on_change_pixel_size(self):
        """
            Change the detector pixel size
        """
        detector, _, position = self.get_current_detector()
        if detector is None:
            return
        #Change x coordinate
        x_pixel_size = self.x_pixel_size_tcl.GetValue().lstrip().rstrip()
        if x_pixel_size == "" or x_pixel_size == str(None):
            x_pixel_size = None
        else:
            if check_float(self.x_pixel_size_tcl):
                if detector.pixel_size.x != float(x_pixel_size) :
                    self._notes += "Change x of pixel size from "
                    self._notes += "%s to %s \n" % (detector.pixel_size.x,
                                                   x_pixel_size)
                    detector.pixel_size.x = float(x_pixel_size)
            else:
                self._notes += "Error: Expected a float for the pixel"
                self._notes += " size 's x  won't changes x pixel size from "
                self._notes += "%s to %s" % (detector.pixel_size.x,
                                             x_pixel_size)
        #Change y coordinate
        y_pixel_size = self.y_pixel_size_tcl.GetValue().lstrip().rstrip()
        if y_pixel_size == "" or y_pixel_size == str(None):
            y_pixel_size = None
            detector.pixel_size.y = y_pixel_size
        else:
            if check_float(self.y_pixel_size_tcl):
                if detector.pixel_size.y != float(y_pixel_size):
                    self._notes += "Change y of pixel size from "
                    self._notes += "%s to %s \n" % (detector.pixel_size.y,
                                                   y_pixel_size)
                    detector.pixel_size.y = float(y_pixel_size)
            else:
                self._notes += "Error: Expected a float for the pixel "
                self._notes += "size's y  won't changes y pixel size from "
                self._notes += "%s to %s" % (detector.pixel_size.y,
                                              y_pixel_size)
        #Change z coordinate
        z_pixel_size = self.z_pixel_size_tcl.GetValue().lstrip().rstrip()
        if z_pixel_size == "" or z_pixel_size == str(None):
            z_pixel_size = None
            detector.pixel_size.z = z_pixel_size
        else:
            if check_float(self.z_pixel_size_tcl):
                if detector.pixel_size.z != float(z_pixel_size):
                    self._notes += "Change z of pixel size from "
                    self._notes += "%s to %s \n" % (detector.pixel_size.z,
                                                   z_pixel_size)
                    detector.pixel_size.z = float(z_pixel_size)
            else:
                self._notes += "Error: Expected a float for the offset 's x "
                self._notes += "won't changes z pixel size from "
                self._notes += "%s to %s" % (detector.pixel_size.z, z_pixel_size)
        #change the beam center unit
        unit = self.pixel_size_unit_tcl.GetValue().lstrip().rstrip()
        if detector.pixel_size_unit != unit:
            self._notes += " Change pixel size's unit from "
            self._notes += "%s to %s" % (detector.pixel_size_unit, unit)

        self.detector_cbox.SetString(position, str(detector.name))
        self.detector_cbox.SetClientData(position, detector)
        self.detector_cbox.SetStringSelection(str(detector.name))

    def on_change_slit_length(self):
        """
            Change slit length of the detector
        """
        detector, _, position = self.get_current_detector()
        if detector is None:
            return
        #Change the distance
        slit_length = self.slit_length_tcl.GetValue().lstrip().rstrip()
        if slit_length == "" or slit_length == str(None):
            slit_length = None
            detector.slit_length = slit_length
        else:
            if check_float(self.slit_length_tcl):
                if detector.slit_length != float(slit_length):
                    self._notes += " Change slit length from"
                    self._notes += " %s to %s \n" % (detector.slit_length,
                                                    slit_length)
                    detector.slit_length = float(slit_length)
            else:
                self._notes += "Error: Expected a float"
                self._notes += " for the slit length won't changes "
                self._notes += "%s to %s" % (detector.slit_length, slit_length)
        #change the distance unit
        unit = self.slit_length_unit_tcl.GetValue().lstrip().rstrip()
        if detector.slit_length_unit != unit:
            self._notes += " Change slit length's unit from "
            self._notes += "%s to %s" % (detector.slit_length_unit_tcl, unit)

        self.detector_cbox.SetString(position, str(detector.name))
        self.detector_cbox.SetClientData(position, detector)
        self.detector_cbox.SetStringSelection(str(detector.name))

    def on_click_cancel(self, event):
        """
            reset the current detector to its initial values
        """
        self.reset_detector()
        self.set_values()
        if self.manager is not None:
             self.manager.set_detector(self._detector)

    def on_click_apply(self, event):
        """
            Apply user values to the detector
        """
        self.on_change_instrument()
        self.on_change_distance()
        self.on_change_instrument()
        self.on_change_beam_center()
        self.on_change_offset()
        self.on_change_orientation()
        self.on_change_pixel_size()
        self.on_change_slit_length()
        for detector in self._detector:
            self.manager.set_detector(self._detector, self._notes)

if __name__ == "__main__":
    app = wx.App()
    test_detector = Detector()
    dlg = DetectorDialog(detector=[test_detector])
    dlg.ShowModal()
    app.MainLoop()
