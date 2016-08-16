import wx
from math import log10
from math import floor

class RangeDialog(wx.Dialog):
    def __init__(self, parent, id, title="Set Graph Range"):
        wx.Dialog.__init__(self, parent, id, title, size=(350, 175))

        mainbox = wx.BoxSizer(wx.VERTICAL)

        x_box = wx.BoxSizer(wx.HORIZONTAL)

        xmin_label = wx.StaticText(self, -1, 'xmin: ', size=(50,20))
        x_box.Add(xmin_label)
        self.xmin_input = wx.TextCtrl(self, -1, size=(75, -1))
        x_box.Add(self.xmin_input)

        x_box.AddSpacer(35)

        xmax_label = wx.StaticText(self, -1, "xmax: ", size=(50,20))
        x_box.Add(xmax_label)
        self.xmax_input = wx.TextCtrl(self, -1, size=(75, -1))
        x_box.Add(self.xmax_input)

        mainbox.Add(x_box, flag=wx.CENTER | wx.ALL, border=10)

        y_box = wx.BoxSizer(wx.HORIZONTAL)

        ymin_label = wx.StaticText(self, -1, 'ymin: ', size=(50,20))
        y_box.Add(ymin_label)
        self.ymin_input = wx.TextCtrl(self, -1, size=(75, -1))
        y_box.Add(self.ymin_input)

        y_box.AddSpacer(35)

        ymax_label = wx.StaticText(self, -1, "ymax: ", size=(50,20))
        y_box.Add(ymax_label)
        self.ymax_input = wx.TextCtrl(self, -1, size=(75, -1))
        y_box.Add(self.ymax_input)

        mainbox.Add(y_box, flag=wx.CENTER | wx.ALL, border=10)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer.AddSpacer(20)

        ok_btn = wx.Button(self, wx.ID_OK, 'Done')
        btn_sizer.Add(ok_btn)

        btn_sizer.AddSpacer(5)

        cancel_btn = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        btn_sizer.Add(cancel_btn)

        mainbox.Add(btn_sizer, flag=wx.CENTER, border=10)

        self.SetSizer(mainbox)

    def GetXRange(self):
        xmin, xmax = (None, None)
        try:
            xmin = float(self.xmin_input.GetValue())
        except:
            pass
        try:
            xmax = float(self.xmax_input.GetValue())
        except:
            pass

        if xmin is not None and xmax is not None:
            return (xmin, xmax)
        return None

    def SetXRange(self, x_range):
        xmin, xmax = x_range
        self.xmin_input.SetValue(str(self._round_to_sigfig(xmin, 8)))
        self.xmax_input.SetValue(str(self._round_to_sigfig(xmax, 8)))

    def GetYRange(self):
        ymin, ymax = (None, None)
        try:
            ymin = float(self.ymin_input.GetValue())
        except:
            pass
        try:
            ymax = float(self.ymax_input.GetValue())
        except:
            pass

        if ymin is not None and ymax is not None:
            return (ymin, ymax)
        return None

    def SetYRange(self, y_range):
        ymin, ymax = y_range
        self.ymin_input.SetValue(str(self._round_to_sigfig(ymin, 8)))
        self.ymax_input.SetValue(str(self._round_to_sigfig(ymax, 8)))

    def _round_to_sigfig(self, x, sigfigs):
        if x == 0.0:
            return 0.0
        return round(x, sigfigs-1-int(floor(log10(abs(x)))))
