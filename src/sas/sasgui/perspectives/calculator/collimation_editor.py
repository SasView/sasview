"""
"""
import wx
import sys
from copy import deepcopy
from sas.sascalc.dataloader.loader import Loader
from sas.sascalc.dataloader.data_info import Aperture, Collimation
from .aperture_editor import ApertureDialog

from sas.sasgui.guiframe.utils import check_float
_BOX_WIDTH = 60

if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 500
    PANEL_WIDTH = 530
    PANEL_HEIGHT = 430
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 550
    PANEL_WIDTH = 600
    PANEL_HEIGHT = 480
    FONT_VARIANT = 1

class CollimationDialog(wx.Dialog):
    """
    """
    def __init__(self, parent=None, manager=None,
                 collimation=[], *args, **kwds):
        """
        """
        kwds['size'] = (PANEL_WIDTH, PANEL_HEIGHT)
        kwds['title'] = "Collimation Editor"
        wx.Dialog.__init__(self, parent=parent, *args, **kwds)
        self.parent = parent
        self.manager = manager
        self._collimation = collimation
        self._reset_collimation = deepcopy(collimation)
        self._notes = ""
        self._description = "Edit collimation"
        #layout attributes
        self.main_sizer = None
        self.box_collimation = None
        self.boxsizer_collimation = None


        self._do_layout()
        self.set_values()

    def _define_structure(self):
        """
        define initial sizer
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_collimation = wx.StaticBox(self, -1,
                                            str("Edit Selected Collimation"))
        self.boxsizer_collimation = wx.StaticBoxSizer(self.box_collimation,
                                                       wx.VERTICAL)

        collimation_box = wx.StaticBox(self, -1, "Edit Number of Collimations")
        self.collimation_sizer = wx.StaticBoxSizer(collimation_box, wx.VERTICAL)
        self.collimation_sizer.SetMinSize((_STATICBOX_WIDTH, -1))
        self.collimation_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.collimation_hint_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.length_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        aperture_box = wx.StaticBox(self, -1, "Edit Aperture")
        self.aperture_sizer = wx.StaticBoxSizer(aperture_box, wx.VERTICAL)
        self.aperture_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.aperture_hint_sizer = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_collimation(self):
        """
        Do the layout for collimation related widgets
        """
        collimation_name_txt = wx.StaticText(self, -1, "Collimation:")
        hint_collimation_txt = 'Current available collimation.'
        collimation_name_txt.SetToolTipString(hint_collimation_txt)
        self.collimation_cbox = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.collimation_cbox, -1, self.on_select_collimation)
        hint_collimation_name_txt = 'Name of collimations.'
        self.collimation_cbox.SetToolTipString(hint_collimation_name_txt)

        self.bt_add_collimation = wx.Button(self, -1, "Add")
        self.bt_add_collimation.SetToolTipString("Edit data's collimation.")
        self.bt_add_collimation.Bind(wx.EVT_BUTTON, self.add_collimation)

        self.bt_remove_collimation = wx.Button(self, -1, "Remove")
        hint = "Remove data's collimation."
        self.bt_remove_collimation.SetToolTipString(hint)
        self.bt_remove_collimation.Bind(wx.EVT_BUTTON, self.remove_collimation)

        self.collimation_button_sizer.AddMany([(collimation_name_txt, 0,
                                                 wx.LEFT, 15),
                                     (self.collimation_cbox, 0, wx.LEFT, 5),
                                     (self.bt_add_collimation, 0, wx.LEFT, 10),
                                     (self.bt_remove_collimation,
                                       0, wx.LEFT, 5)])
        collimation_hint_txt = 'No collimation is available for this data.'
        self.collimation_txt = wx.StaticText(self, -1, collimation_hint_txt)
        self.collimation_hint_sizer.Add(self.collimation_txt, 0, wx.LEFT, 10)
        self.collimation_sizer.AddMany([(self.collimation_button_sizer,
                                          0, wx.ALL, 10),
                                     (self.collimation_hint_sizer,
                                       0, wx.ALL, 10)])

        self.fill_collimation_combox()
        self.enable_collimation()


    def _layout_name(self):
        """
        Do the layout for collimation name related widgets
        """
        #Collimation name [string]
        name_txt = wx.StaticText(self, -1, 'Name : ')
        self.name_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH * 5, 20), style=0)
        self.name_sizer.AddMany([(name_txt, 0, wx.LEFT | wx.RIGHT, 10),
                                       (self.name_tcl, 0, wx.EXPAND)])

    def _layout_length(self):
        """
        Do the  layout for length related widgets
        """
        #Collimation length
        length_txt = wx.StaticText(self, -1, 'Length:')
        self.length_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 20), style=0)
        length_unit_txt = wx.StaticText(self, -1, 'Unit: ')
        self.length_unit_tcl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                           style=0)
        self.length_sizer.AddMany([(length_txt, 0, wx.LEFT | wx.RIGHT, 10),
                                     (self.length_tcl, 0, wx.LEFT, 12),
                                     (length_unit_txt, 0, wx.LEFT | wx.RIGHT, 10),
                                     (self.length_unit_tcl, 0, wx.EXPAND)])

    def _layout_button(self):
        """
        Do the layout for the button widgets
        """
        self.bt_apply = wx.Button(self, -1, 'Apply')
        self.bt_apply.Bind(wx.EVT_BUTTON, self.on_click_apply)
        self.bt_apply.SetToolTipString("Apply current changes to collimation.")
        self.bt_cancel = wx.Button(self, -1, 'Cancel')
        self.bt_cancel.SetToolTipString("Cancel current changes.")
        self.bt_cancel.Bind(wx.EVT_BUTTON, self.on_click_cancel)
        self.bt_close = wx.Button(self, wx.ID_CANCEL, 'Close')
        self.bt_close.SetToolTipString("Close window.")
        self.button_sizer.AddMany([(self.bt_apply, 0, wx.LEFT, 200),
                                   (self.bt_cancel, 0, wx.LEFT, 10),
                                   (self.bt_close, 0, wx.LEFT, 10)])
    def _layout_aperture(self):
        """
        Do the layout for aperture related widgets
        """
        aperture_name_txt = wx.StaticText(self, -1, "Aperture:")
        hint_aperture_txt = 'Current available aperture.'
        aperture_name_txt.SetToolTipString(hint_aperture_txt)
        self.aperture_cbox = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        hint_aperture_name_txt = 'Name of apertures.'
        self.aperture_cbox.SetToolTipString(hint_aperture_name_txt)

        self.bt_add_aperture = wx.Button(self, -1, "Add")
        self.bt_add_aperture.SetToolTipString("Edit data's aperture.")
        self.bt_add_aperture.Bind(wx.EVT_BUTTON, self.add_aperture)
        self.bt_edit_aperture = wx.Button(self, -1, "Edit")
        self.bt_edit_aperture.SetToolTipString("Edit data's aperture.")
        self.bt_edit_aperture.Bind(wx.EVT_BUTTON, self.edit_aperture)
        self.bt_remove_aperture = wx.Button(self, -1, "Remove")
        self.bt_remove_aperture.SetToolTipString("Remove data's aperture.")
        self.bt_remove_aperture.Bind(wx.EVT_BUTTON, self.remove_aperture)

        self.aperture_button_sizer.AddMany([(aperture_name_txt, 0, wx.LEFT, 15),
                                     (self.aperture_cbox, 0, wx.LEFT, 5),
                                     (self.bt_add_aperture, 0, wx.LEFT, 10),
                                     (self.bt_edit_aperture, 0, wx.LEFT, 5),
                                     (self.bt_remove_aperture, 0, wx.LEFT, 5)])
        aperture_hint_txt = 'No aperture is available for this data.'
        self.aperture_txt = wx.StaticText(self, -1, aperture_hint_txt)
        self.aperture_hint_sizer.Add(self.aperture_txt, 0, wx.LEFT, 10)
        self.aperture_sizer.AddMany([(self.aperture_button_sizer,
                                       0, wx.ALL, 10),
                                     (self.aperture_hint_sizer, 0, wx.ALL, 10)])
        self.fill_aperture_combox()
        self.enable_aperture()

    def _do_layout(self):
        """
        Draw the current panel
        """
        self._define_structure()
        self._layout_collimation()
        self._layout_name()
        self._layout_length()
        self._layout_aperture()
        self._layout_button()

        self.boxsizer_collimation.AddMany([(self.name_sizer, 0,
                                          wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                          (self.length_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                     (self.aperture_sizer, 0,
                                     wx.EXPAND | wx.ALL, 10)])
        self.main_sizer.AddMany([(self.collimation_sizer, 0, wx.ALL, 10),
                                  (self.boxsizer_collimation, 0, wx.ALL, 10),
                                  (self.button_sizer, 0,
                                    wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)

    def get_current_collimation(self):
        """
        """
        if not self.collimation_cbox.IsEnabled():
            return None, None, None
        position = self.collimation_cbox.GetSelection()
        if position == wx.NOT_FOUND:
            return None, None, None
        collimation_name = self.collimation_cbox.GetStringSelection()
        collimation = self.collimation_cbox.GetClientData(position)
        return collimation, collimation_name, position

    def fill_collimation_combox(self):
        """
        fill the current combobox with the available collimation
        """
        if self._collimation is None or self._collimation == []:
            return
        for collimation in self._collimation:
            pos = self.collimation_cbox.Append(str(collimation.name))
            self.collimation_cbox.SetClientData(pos, collimation)
            self.collimation_cbox.SetSelection(pos)
            self.collimation_cbox.SetStringSelection(str(collimation.name))

    def add_collimation(self, event):
        """
        Append empty collimation to data's list of collimation
        """

        if not self.collimation_cbox.IsEnabled():
            self.collimation_cbox.Enable()
        collimation = Collimation()
        self._collimation.append(collimation)
        position = self.collimation_cbox.Append(str(collimation.name))
        self.collimation_cbox.SetClientData(position, collimation)
        self.collimation_cbox.SetSelection(position)
        self.enable_collimation()
        self.bt_add_aperture.Enable()
        self.fill_aperture_combox()
        self.enable_aperture()
        self.set_values()

    def remove_collimation(self, event):
        """
        Remove collimation to data's list of collimation
        """
        if self.collimation_cbox.IsEnabled():
            if self.collimation_cbox.GetCount() > 0:
                position = self.collimation_cbox.GetCurrentSelection()
                collimation = self.collimation_cbox.GetClientData(position)
                if collimation in self._collimation:
                    self._collimation.remove(collimation)
                    self.collimation_cbox.Delete(position)
                    #set the combo box box the next available item
                    position = self.collimation_cbox.GetCount()
                    if position > 0:
                        position -= 1
                    self.collimation_cbox.SetSelection(position)
        if not self._collimation and self.collimation_cbox.GetCount() == 0:
            self.bt_add_aperture.Disable()
            self.name_tcl.Clear()
            self.length_tcl.Clear()
            self.length_unit_tcl.Clear()
            self.aperture_cbox.Clear()
            self.aperture_cbox.Disable()
        #disable or enable the combo box when necessary
        self.enable_collimation()
        self.enable_aperture()

    def on_select_collimation(self, event):
        """
        fill the control on the panel according to
        the current  selected collimation
        """
        self.set_values()
        self.fill_aperture_combox()
        self.enable_aperture()

    def enable_collimation(self):
        """
        Enable /disable widgets related to collimation
        """
        if self._collimation is not None and \
            self.collimation_cbox.GetCount() > 0:
            self.collimation_cbox.Enable()
            self.bt_remove_collimation.Enable()
            n_collimation = self.collimation_cbox.GetCount()
            collimation_hint_txt = "collimations"
            collimation_hint_txt += " available: %s " % str(n_collimation)
            if len(self._collimation) > 0:
                self.bt_remove_collimation.Enable()
            else:
                self.bt_remove_collimation.Disable()
        else:
            self.collimation_cbox.Disable()
            self.bt_remove_collimation.Disable()
            collimation_hint_txt = 'No collimation is available for this data.'
        self.collimation_txt.SetLabel(collimation_hint_txt)


    def reset_collimation_combobox(self, edited_collimation):
        """
        take all edited editor and reset clientdata of collimation combo box
        """
        for position in range(self.collimation_cbox.GetCount()):
            collimation = self.collimation_cbox.GetClientData(position)
            if collimation == edited_collimation:
                collimation = edited_collimation
                self.collimation_cbox.SetString(position, str(collimation.name))
                self.collimation_cbox.SetClientData(position, collimation)
                self.collimation_cbox.SetStringSelection(str(collimation.name))

    def add_aperture(self, event):
        """
        Append empty aperture to data's list of aperture
        """
        collimation, _, _ = self.get_current_collimation()
        if not self.aperture_cbox.IsEnabled():
            self.aperture_cbox.Enable()
        aperture = Aperture()
        collimation.aperture.append(aperture)
        position = self.aperture_cbox.Append(str(aperture.name))
        self.aperture_cbox.SetClientData(position, aperture)
        self.aperture_cbox.SetSelection(position)
        self.enable_aperture()

    def edit_aperture(self, event):
        """
        Edit the selected aperture
        """
        if self._collimation is None or not self.aperture_cbox.IsEnabled():
            return
        position = self.aperture_cbox.GetSelection()
        if position != wx.NOT_FOUND:
            name = self.aperture_cbox.GetStringSelection()
            aperture = self.aperture_cbox.GetClientData(position)
            dlg = ApertureDialog(parent=self, aperture=aperture)
            dlg.set_manager(self)
            dlg.ShowModal()

    def remove_aperture(self, event):
        """
        Remove aperture to data's list of aperture
        """
        if self._collimation is None or not self._collimation:
            return
        collimation, _, _ = self.get_current_collimation()
        if self.aperture_cbox.IsEnabled():
            if self.aperture_cbox.GetCount() > 1:
                position = self.aperture_cbox.GetCurrentSelection()
                aperture = self.aperture_cbox.GetClientData(position)
                if aperture in collimation.aperture:
                    collimation.aperture.remove(aperture)
                    self.aperture_cbox.Delete(position)
                    #set the combo box box the next available item
                    position = self.aperture_cbox.GetCount()
                    if position > 0:
                        position -= 1
                    self.aperture_cbox.SetSelection(position)

        #disable or enable the combo box when necessary
        self.enable_aperture()

    def set_aperture(self, aperture):
        """
        set aperture for data
        """
        if self._collimation is None or not self._collimation:
            return
        collimation, _, _ = self.get_current_collimation()
        if collimation.aperture:
            for item in collimation.aperture:
                if item == aperture:
                    item = aperture
                    self.reset_aperture_combobox(edited_aperture=aperture)
                    return

    def enable_aperture(self):
        """
        Enable /disable widgets crelated to aperture
        """
        collimation, _, _ = self.get_current_collimation()
        if  self.aperture_cbox.GetCount() > 0:
            self.aperture_cbox.Enable()
            self.bt_edit_aperture.Enable()
            self.bt_remove_aperture.Enable()
            n_aperture = self.aperture_cbox.GetCount()
            aperture_hint_txt = 'apertures available: %s ' % str(n_aperture)
            if len(collimation.aperture) > 0:
                self.bt_remove_aperture.Enable()
            else:
                self.bt_remove_aperture.Disable()
        else:
            self.aperture_cbox.Disable()
            self.bt_edit_aperture.Disable()
            self.bt_remove_aperture.Disable()
            aperture_hint_txt = 'No aperture is available for this data.'
        self.aperture_txt.SetLabel(aperture_hint_txt)

    def reset_aperture_combobox(self, edited_aperture):
        """
        take all edited editor and reset clientdata of aperture combo box
        """
        for position in range(self.aperture_cbox.GetCount()):
            aperture = self.aperture_cbox.GetClientData(position)
            if aperture == edited_aperture:
                aperture = edited_aperture
                self.aperture_cbox.SetString(position, str(aperture.name))
                self.aperture_cbox.SetClientData(position, aperture)
                self.aperture_cbox.SetStringSelection(str(aperture.name))

    def fill_aperture_combox(self):
        """
        fill the current combobox with the available aperture
        """
        self.aperture_cbox.Clear()
        collimation, _, _ = self.get_current_collimation()
        if collimation is None or not collimation.aperture:
            return
        for aperture in collimation.aperture:
            pos = self.aperture_cbox.Append(str(aperture.name))
            self.aperture_cbox.SetClientData(pos, aperture)
            self.aperture_cbox.SetSelection(pos)
            self.aperture_cbox.SetStringSelection(str(aperture.name))

    def set_manager(self, manager):
        """
        Set manager of this window
        """
        self.manager = manager

    def set_values(self):
        """
        take the collimation values of the current data and display them
        through the panel
        """
        collimation, _, _ = self.get_current_collimation()
        if collimation is None:
            self.bt_add_aperture.Disable()
            self.length_tcl.SetValue("")
            self.name_tcl.SetValue("")
            self.length_unit_tcl.SetValue("")
            return
        #Name
        self.name_tcl.SetValue(str(collimation.name))
        #length
        self.length_tcl.SetValue(str(collimation.length))
        #Length unit
        self.length_unit_tcl.SetValue(str(collimation.length_unit))

    def get_collimation(self):
        """
        return the current collimation
        """
        return self._collimation

    def get_notes(self):
        """
        return notes
        """
        return self._notes

    def on_change_name(self):
        """
        Change name
        """
        collimation, collimation_name, position = self.get_current_collimation()
        if collimation is None:
            return
        #Change the name of the collimation
        name = self.name_tcl.GetValue().lstrip().rstrip()
        if name == "" or name == str(None):
            name = None
        if collimation.name != name:
            self._notes += "Change collimation 's "
            self._notes += "name from %s to %s \n" % (collimation.name, name)
            collimation.name = name
            self.collimation_cbox.SetString(position, str(collimation.name))
            self.collimation_cbox.SetClientData(position, collimation)
            self.collimation_cbox.SetStringSelection(str(collimation.name))

    def on_change_length(self):
        """
        Change the length
        """
        collimation, collimation_name, position = self.get_current_collimation()
        if collimation is None:
            return
        #Change length  
        length = self.length_tcl.GetValue().lstrip().rstrip()
        if length == "" or length == str(None):
            length = None
            collimation.length = length
        else:
            if check_float(self.length_tcl):
                if collimation.length != float(length):
                    self._notes += "Change Collimation length from "
                    self._notes += "%s to %s \n" % (collimation.length, length)
                    collimation.length = float(length)
            else:
                self._notes += "Error: Expected a float for collimation length"
                self._notes += " won't changes length from "
                self._notes += "%s to %s" % (collimation.length, length)
        #change length  unit
        unit = self.length_unit_tcl.GetValue().lstrip().rstrip()
        if collimation.length_unit != unit:
            self._notes += " Change length's unit from "
            self._notes += "%s to %s" % (collimation.length_unit, unit)
            collimation.length_unit = unit

    def on_click_apply(self, event):
        """
        Apply user values to the collimation
        """
        self.on_change_name()
        self.on_change_length()
        self.set_values()
        if self.manager is not None:
            self.manager.set_collimation(self._collimation, self._notes)

    def on_click_cancel(self, event):
        """
        leave the collimation as it is and close
        """
        self._collimation = deepcopy(self._reset_collimation)
        self.set_values()
        if self.manager is not None:
            self.manager.set_collimation(self._collimation)


if __name__ == "__main__":

    app = wx.App()
    dlg = CollimationDialog(collimation=[Collimation()])
    dlg.ShowModal()
    app.MainLoop()
