"""
This module provides some custom wx widgets for the file converter perspective
"""
import wx
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

    def GetValue(self):
        """
        Get the value of the vector input

        :return v: A Vector object
        """
        v = Vector()
        if not self.Validate(): return v
        for direction, control in self._inputs:
            try:
                value = float(control.GetValue())
                setattr(v, direction, value)
            except: # Text field is empty
                pass

        return v

    def Validate(self):
        """
        Validate the contents of the inputs

        :return control_valid: Whether or not the inputs are valid
        :return invalid_control: The control that is not valid
            (or None if all are valid)
        """
        for control in self._inputs.values():
            if control.GetValue() == '': continue
            control.SetBackgroundColour(wx.WHITE)
            control_valid = check_float(control)
            if not control_valid:
                return False, control
        return True, None


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

        self._sizer.AddSpacer((15, -1))

        y_label = wx.StaticText(self.parent, -1, self.labels[1],
            style=wx.ALIGN_CENTER_VERTICAL)
        self._sizer.Add(y_label, wx.ALIGN_CENTER_VERTICAL)
        y_input = wx.TextCtrl(self.parent, -1,
            name="{}_y".format(self.control_name), size=(50, -1))
        self._sizer.Add(y_input)
        self._inputs['y'] = y_input
        y_input.Bind(wx.EVT_TEXT, self._callback)

        if self.z_enabled:
            self._sizer.AddSpacer((15, -1))

            z_label = wx.StaticText(self.parent, -1, self.labels[2],
                style=wx.ALIGN_CENTER_VERTICAL)
            self._sizer.Add(z_label, wx.ALIGN_CENTER_VERTICAL)
            z_input = wx.TextCtrl(self.parent, -1,
                name="{}_z".format(self.control_name), size=(50, -1))
            self._sizer.Add(z_input)
            self._inputs['z'] = z_input
            z_input.Bind(wx.EVT_TEXT, self._callback)
