"""
"""
import wx

class Properties(wx.Dialog):
    """
    """
    def __init__(self, parent, id=-1, title="Select the scale of the graph"):
        wx.Dialog.__init__(self, parent, id, title)
        self.parent = parent
        vbox = wx.BoxSizer(wx.VERTICAL)
        sizer = wx.GridBagSizer(5, 5)

        x_size = 70

        ix = 1
        iy = 1
        sizer.Add(wx.StaticText(self, -1, 'X'), (iy, ix))
        ix += 2
        sizer.Add(wx.StaticText(self, -1, 'Y'), (iy, ix))
        ix += 2
        sizer.Add(wx.StaticText(self, -1, 'View'), (iy, ix))
        iy += 1
        ix = 1
        self.xvalue = wx.ComboBox(self, -1)
        x_size += self.xvalue.GetSize()[0]
        sizer.Add(self.xvalue, (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        ix += 2
        self.yvalue = wx.ComboBox(self, -1)
        x_size += self.yvalue.GetSize()[0]
        sizer.Add(self.yvalue, (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        ix += 2
        self.view = wx.ComboBox(self, -1)
        x_size += self.view.GetSize()[0]
        self.view.SetMinSize((160, 30))
        sizer.Add(self.view, (iy, ix), (1, 1),
                  wx.EXPAND | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        self.SetMinSize((x_size, 50))
        vbox.Add(sizer, 0, wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        cancel_button = wx.Button(self, wx.ID_CANCEL, 'Cancel')
        ok_button = wx.Button(self, wx.ID_OK, "OK")
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(ok_button, 0, wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(cancel_button, 0, wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        vbox.Add(sizer_button, 0,
                 wx.EXPAND | wx.TOP | wx.BOTTOM | wx.ADJUST_MINSIZE, 10)
        # scale value for x
        self.xvalue.SetValue("ln(x)")
        self.xvalue.Insert("x", 0)
        self.xvalue.Insert("x^(2)", 1)
        self.xvalue.Insert("x^(4)", 2)
        self.xvalue.Insert("ln(x)", 3)
        self.xvalue.Insert("log10(x)", 4)
        self.xvalue.Insert("log10(x^(4))", 5)

        # scale value for y
        self.yvalue.SetValue("ln(y)")
        self.yvalue.Insert("y", 0)
        self.yvalue.Insert("1/y", 1)
        self.yvalue.Insert("ln(y)", 2)
        self.yvalue.Insert("y^(2)", 3)
        self.yvalue.Insert("y*x^(2)", 4)
        self.yvalue.Insert("y*x^(4)", 5)
        self.yvalue.Insert("1/sqrt(y)", 6)
        self.yvalue.Insert("log10(y)", 7)
        self.yvalue.Insert("ln(y*x)", 8)
        self.yvalue.Insert("ln(y*x^(2))", 9)
        self.yvalue.Insert("ln(y*x^(4))", 10)
        self.yvalue.Insert("log10(y*x^(4))", 11)
        # type of view or model used
        self.view.SetValue("--")
        self.view.Insert("--", 0)
        self.view.Insert("Linear y vs x", 1)
        self.view.Insert("Guinier lny vs x^(2)", 2)
        self.view.Insert("XS Guinier ln(y*x) vs x^(2)", 3)
        self.view.Insert("Porod y*x^(4) vs x^(4)", 4)
        self.view.Insert("Kratky y*x^(2) vs x", 5)
        self.SetSizer(vbox)
        self.Fit()
        self.Centre()

    def setValues(self, x, y, view):
        """
        """
        return  self.xvalue.SetValue(x), self.yvalue.SetValue(y), \
                    self.view.SetValue(view)

    def getValues(self):
        """
        """
        return self.xvalue.GetValue(), self.yvalue.GetValue(), \
                            self.view.GetValue()
