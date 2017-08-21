import wx
import wx.lib.newevent
from parameters_panel_slicer import SlicerParameterPanel
from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.guiframe.events import (SlicerParameterEvent, EVT_SLICER_PARS,
                                        EVT_SLICER)


class SlicerPanel(wx.Panel, PanelBase):
    """
    Panel class to show the slicer parameters
    """
    # Internal name for the AUI manager
    window_name = "Slicer panel"
    # Title to appear on top of the window
    window_caption = "Slicer Panel"
    CENTER_PANE = False

    def __init__(self, parent, id=-1, type=None, base=None,
                 params=None, *args, **kwargs):
        wx.Panel.__init__(self, parent, id, *args, **kwargs)
        PanelBase.__init__(self)
        # Initialization of the class
        self.base = base
        if params is None:
            params = {}
        self.params = params
        self.parent = base.parent
        self.frame = None
        self.type = type
        self.listeners = []
        self.parameters = []
        self.bck = wx.GridBagSizer(5, 5)
        self.SetSizer(self.bck)
        if type is None and params is None:
            label = "Right-click on 2D plot for slicer options"
            title = wx.StaticText(self, -1, label, style=wx.ALIGN_LEFT)
            self.bck.Add(title, (0, 0), (1, 2),
                         flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
        else:
            self.set_slicer(type, params)
        # Bindings
        self.parent.Bind(EVT_SLICER, SlicerParameterPanel.on_evt_slicer)
        self.parent.Bind(EVT_SLICER_PARS, SlicerParameterPanel.on_param_change)

    def set_slicer(self, type, params):
        """
        Rebuild the panel
        """
        self.bck.Clear(True)
        self.type = type
        if type is None:
            label = "Right-click on 2D plot for slicer options"
            title = wx.StaticText(self, -1, label, style=wx.ALIGN_LEFT)
            self.bck.Add(title, (0, 0), (1, 2),
                         flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
        else:
            title_text = str(type) + "Parameters"
            title = wx.StaticText(self, -1, title_text,
                                  style=wx.ALIGN_LEFT)
            self.bck.Add(title, (0, 0), (1, 2),
                         flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
            n = 1
            self.parameters = []
            keys = params.keys()
            keys.sort()
            for item in keys:
                if not item.lower() in ["num_points", "avg", "avg_error", "sum",
                                        "sum_error"]:
                    n += 1
                    text = wx.StaticText(self, -1, item, style=wx.ALIGN_LEFT)
                    self.bck.Add(text, (n - 1, 0),
                                 flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL,
                                 border=15)
                    ctl = wx.TextCtrl(self, -1, size=(80, 20),
                                      style=wx.TE_PROCESS_ENTER)
                    hint_msg = "Modify the value of %s to change " % item
                    hint_msg += "the 2D slicer"
                    ctl.SetToolTipString(hint_msg)
                    ctl.SetValue(str(format_number(params[item])))
                    self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter)
                    ctl.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
                    ctl.Bind(wx.EVT_KILL_FOCUS, self.on_text_enter)
                    self.parameters.append([item, ctl])
                    self.bck.Add(ctl, (n - 1, 1), flag=wx.TOP | wx.BOTTOM,
                                 border=0)
            for item in keys:
                if item.lower() in ["num_points", "avg", "avg_error", "sum",
                                    "sum_error"]:
                    n += 1
                    text = wx.StaticText(self, -1, item + ": ",
                                         style=wx.ALIGN_LEFT)
                    self.bck.Add(text, (n - 1, 0),
                                 flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL,
                                 border=15)
                    ctl = wx.StaticText(self, -1,
                                        str(format_number(params[item])),
                                        style=wx.ALIGN_LEFT)
                    ctl.SetToolTipString("Result %s" % item)
                    self.bck.Add(ctl, (n - 1, 1), flag=wx.TOP | wx.BOTTOM,
                                 border=0)
        self.bck.Layout()
        self.Layout()
        p_sizer = self.parent.GetSizer()
        if p_sizer is not None:
            p_sizer.Layout()

    def on_set_focus(self, evt):
        """
        Highlight the txtcrtl
        """
        evt.Skip()
        # Get a handle to the TextCtrl
        widget = evt.GetEventObject()
        # Select the whole control, after this event resolves
        wx.CallAfter(widget.SetSelection, -1, -1)

    def on_text_enter(self, evt):
        """
        Parameters have changed
        """
        evt.Skip()
        params = {}
        has_error = False
        for item in self.parameters:
            try:
                params[item[0]] = float(item[1].GetValue())
                item[1].SetBackgroundColour(wx.SystemSettings_GetColour(
                    wx.SYS_COLOUR_WINDOW))
                item[1].Refresh()
            except:
                has_error = True
                item[1].SetBackgroundColour("pink")
                item[1].Refresh()
        if not has_error:
            # Post parameter event
            # base is guiframe is this case
            event = SlicerParameterEvent(type=self.type, params=params)
            wx.PostEvent(self.base, event)

    def on_close(self, event):
        """
        On Close Event
        """
        uid = self.uid
        self.parent.delete_panel(uid)
        self.frame.Destroy()
