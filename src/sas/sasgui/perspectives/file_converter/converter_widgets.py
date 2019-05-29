"""
This module provides some custom wx widgets for the file converter perspective
"""
import wx
import os
from sas.sascalc.dataloader.data_info import Vector
from sas.sasgui.guiframe.utils import check_float

class VectorInput(object):
    """
    An input field for inputting 2 (or 3) components of a vector.
    """

    def __init__(self, parent, control_name, callback=None,
        labels=["x: ", "y: ", "z: "], z_enabled=False):
        """
        Create the control

        :param parent: The window to add the control to
        :param control_name: All TextCtrl names will start with control_name
        :param callback: The function to call when the text is changed
        :param labels: An array of labels for the TextCtrls
        :param z_enabled: Whether or not to show the z input field
        """
        self.parent = parent
        self.control_name = control_name
        self._callback = callback
        self._name = control_name

        self.labels = labels
        self.z_enabled = z_enabled
        self._sizer = None
        self._inputs = {}

        self._do_layout()

    def GetSizer(self):
        """
        Get the control's sizer

        :return sizer: a wx.BoxSizer object
        """
        return self._sizer

    def GetName(self):
        return self._name

    def GetValue(self):
        """
        Get the value of the vector input

        :return v: A Vector object
        """
        v = Vector()
        if not self.Validate(): return v
        for direction, control in self._inputs.items():
            try:
                value = float(control.GetValue())
                setattr(v, direction, value)
            except: # Text field is empty
                pass

        return v

    def SetValue(self, vector):
        """
        Set the value of the vector input

        :param vector: A Vector object
        """
        directions = ['x', 'y']
        if self.z_enabled: directions.append('z')
        for direction in directions:
            value = getattr(vector, direction)
            if value is None: value = ''
            self._inputs[direction].SetValue(str(value))

    def Validate(self):
        """
        Validate the contents of the inputs

        :return all_valid: Whether or not the inputs are valid
        :return invalid_ctrl: A control that is not valid
            (or None if all are valid)
        """
        all_valid = True
        invalid_ctrl = None
        for control in list(self._inputs.values()):
            if control.GetValue() == '': continue
            control.SetBackgroundColour(wx.WHITE)
            control_valid = check_float(control)
            if not control_valid:
                all_valid = False
                invalid_ctrl = control
        return all_valid, invalid_ctrl


    def _do_layout(self):
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)
        x_label = wx.StaticText(self.parent, -1, self.labels[0],
            style=wx.ALIGN_CENTER_VERTICAL)
        self._sizer.Add(x_label, wx.ALIGN_CENTER_VERTICAL)
        x_input = wx.TextCtrl(self.parent, -1,
            name="{}_x".format(self.control_name), size=(50, -1))
        self._sizer.Add(x_input)
        self._inputs['x'] = x_input
        x_input.Bind(wx.EVT_TEXT, self._callback)

        self._sizer.AddSpacer((10, -1))

        y_label = wx.StaticText(self.parent, -1, self.labels[1],
            style=wx.ALIGN_CENTER_VERTICAL)
        self._sizer.Add(y_label, wx.ALIGN_CENTER_VERTICAL)
        y_input = wx.TextCtrl(self.parent, -1,
            name="{}_y".format(self.control_name), size=(50, -1))
        self._sizer.Add(y_input)
        self._inputs['y'] = y_input
        y_input.Bind(wx.EVT_TEXT, self._callback)

        if self.z_enabled:
            self._sizer.AddSpacer((10, -1))

            z_label = wx.StaticText(self.parent, -1, self.labels[2],
                style=wx.ALIGN_CENTER_VERTICAL)
            self._sizer.Add(z_label, wx.ALIGN_CENTER_VERTICAL)
            z_input = wx.TextCtrl(self.parent, -1,
                name="{}_z".format(self.control_name), size=(50, -1))
            self._sizer.Add(z_input)
            self._inputs['z'] = z_input
            z_input.Bind(wx.EVT_TEXT, self._callback)

class FileInput(object):

    def __init__(self, parent, wildcard=''):
        self.parent = parent
        self._sizer = None
        self._text_ctrl = None
        self._button_ctrl = None
        self._filepath = ''
        self._wildcard = wildcard

        self._do_layout()

    def GetCtrl(self):
        return self._sizer

    def GetPath(self):
        return self._filepath

    def SetWildcard(self, wildcard):
        self._wildcard = wildcard


    def _on_text_change(self, event):
        event.Skip()
        self._filepath = self._text_ctrl.GetValue()

    def _on_browse(self, event):
        event.Skip()
        initial_path = self._filepath
        initial_dir = os.getcwd()
        if not os.path.isfile(initial_path):
            initial_path = ''
        else:
            initial_dir = os.path.split(initial_path)[0]

        file_dlg = wx.FileDialog(self.parent, defaultDir=initial_dir,
            defaultFile=initial_path, wildcard=self._wildcard,
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if file_dlg.ShowModal() == wx.ID_CANCEL:
            file_dlg.Destroy()
            return
        self._filepath = file_dlg.GetPath()
        file_dlg.Destroy()
        self._text_ctrl.SetValue(self._filepath)

    def _do_layout(self):
        self._sizer = wx.BoxSizer(wx.HORIZONTAL)

        self._text_ctrl = wx.TextCtrl(self.parent, -1)
        self._sizer.Add(self._text_ctrl, wx.EXPAND)
        self._text_ctrl.Bind(wx.EVT_TEXT, self._on_text_change)

        self._sizer.AddSpacer(5)

        self._button_ctrl = wx.Button(self.parent, -1, "Browse")
        self._sizer.Add(self._button_ctrl)
        self._button_ctrl.Bind(wx.EVT_BUTTON, self._on_browse)
