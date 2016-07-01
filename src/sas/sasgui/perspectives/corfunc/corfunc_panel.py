import wx
import sys
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.perspectives.invariant.invariant_widgets import OutputTextCtrl
from sas.sasgui.perspectives.invariant.invariant_widgets import InvTextCtrl

if sys.platform.count("win32") > 0:
    _STATICBOX_WIDTH = 350
    PANEL_WIDTH = 400
    PANEL_HEIGHT = 700
    FONT_VARIANT = 0
else:
    _STATICBOX_WIDTH = 390
    PANEL_WIDTH = 430
    PANEL_HEIGHT = 700
    FONT_VARIANT = 1

class CorfuncPanel(ScrolledPanel,PanelBase):
    window_name = "Correlation Function"
    window_caption = "Correlation Function"
    CENTER_PANE = True

    def __init__(self, parent, data=None, manager=None, *args, **kwds):
        kwds["size"] = (PANEL_WIDTH, PANEL_HEIGHT)
        kwds["style"] = wx.FULL_REPAINT_ON_RESIZE
        ScrolledPanel.__init__(self, parent=parent, *args, **kwds)
        PanelBase.__init__(self, parent)
        self.SetupScrolling()
        self.SetWindowVariant(variant=FONT_VARIANT)
        self._manager = manager
        self._data = data
        self._data_name_box = None
        self._output_ids = None
        self.state = None
        self.set_state()
        self._do_layout()

    def set_state(self, state=None, data=None):
        # TODO: Implement state restoration
        return False

    def _set_data(self, data=None):
        """
        Update the GUI to reflect new data that has been loaded in

        :param data: The data that has been loaded
        """
        self._data_name_box.SetValue(str(data.name))
        if self._manager is not None:
            self._manager.show_data(data=data, reset=True)


    def _do_layout(self):
        """
        Draw the window content
        """
        vbox = wx.GridBagSizer(0,0)

        # I(q) data box
        databox = wx.StaticBox(self, -1, "I(Q) Data Source")
        databox_sizer = wx.StaticBoxSizer(databox, wx.VERTICAL)

        file_sizer = wx.GridBagSizer(5, 5)

        file_name_label = wx.StaticText(self, -1, "Name:")
        file_sizer.Add(file_name_label, (0, 0), (1, 1),
            wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        self._data_name_box = OutputTextCtrl(self, -1,
            size=(300,20))
        file_sizer.Add(self._data_name_box, (0, 1), (1, 1),
            wx.CENTER | wx.ADJUST_MINSIZE, 15)

        file_sizer.AddSpacer((1, 25), pos=(0,2))
        databox_sizer.Add(file_sizer, wx.TOP, 15)

        vbox.Add(databox_sizer, (0, 0), (1, 1),
            wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE | wx.TOP, 15)


        # Parameters
        qbox = wx.StaticBox(self, -1, "Parameters")
        qbox_sizer = wx.StaticBoxSizer(qbox, wx.VERTICAL)
        qbox_sizer.SetMinSize((_STATICBOX_WIDTH, 75))

        q_sizer = wx.GridBagSizer(5, 5)

        # Explanation
        explanation_txt = ("Corfunc will use all values in the lower range for"
            " Guinier back extrapolation, and all values in the upper range "
            "for Porod forward extrapolation.")
        explanation_label = wx.StaticText(self, -1, explanation_txt,
            size=(_STATICBOX_WIDTH, 60))

        q_sizer.Add(explanation_label, (0,0), (1,4), wx.LEFT | wx.EXPAND, 5)

        qrange_label = wx.StaticText(self, -1, "Q Range:", size=(50,20))
        q_sizer.Add(qrange_label, (1,0), (1,1), wx.LEFT | wx.EXPAND, 5)

        # Lower Q Range
        qmin_label = wx.StaticText(self, -1, "Lower:", size=(50,20))
        qmin_dash_label = wx.StaticText(self, -1, "-", size=(10,20),
            style=wx.ALIGN_CENTER_HORIZONTAL)

        qmin_lower = OutputTextCtrl(self, -1, size=(50, 20), value="0.0")
        qmin_input = InvTextCtrl(self, -1, size=(50, 20),
                        style=wx.TE_PROCESS_ENTER, name='qmin_input')
        qmin_input.SetToolTipString(("Values with q < qmin will be used for "
            "Guinier back extrapolation"))

        q_sizer.Add(qmin_label, (2, 0), (1, 1), wx.LEFT | wx.EXPAND, 5)
        q_sizer.Add(qmin_lower, (2, 1), (1, 1), wx.LEFT, 5)
        q_sizer.Add(qmin_dash_label, (2, 2), (1, 1), wx.CENTER | wx.EXPAND, 5)
        q_sizer.Add(qmin_input, (2, 3), (1, 1), wx.LEFT, 5)

        # Upper Q range
        qmax_tooltip = ("Values with qmax1 < q < qmax2 will be used for Porod"
            " forward extrapolation")

        qmax_label = wx.StaticText(self, -1, "Upper:", size=(50,20))
        qmax_dash_label = wx.StaticText(self, -1, "-", size=(10,20),
            style=wx.ALIGN_CENTER_HORIZONTAL)

        qmax1_input = InvTextCtrl(self, -1, size=(50, 20),
            style=wx.TE_PROCESS_ENTER, name="qmax1_input")
        qmax1_input.SetToolTipString(qmax_tooltip)
        qmax2_input = InvTextCtrl(self, -1, size=(50, 20),
            style=wx.TE_PROCESS_ENTER, name="qmax2_input")
        qmax2_input.SetToolTipString(qmax_tooltip)

        q_sizer.Add(qmax_label, (3, 0), (1, 1), wx.LEFT | wx.EXPAND, 5)
        q_sizer.Add(qmax1_input, (3, 1), (1, 1), wx.LEFT, 5)
        q_sizer.Add(qmax_dash_label, (3, 2), (1, 1), wx.CENTER | wx.EXPAND, 5)
        q_sizer.Add(qmax2_input, (3,3), (1, 1), wx.LEFT, 5)

        qbox_sizer.Add(q_sizer, wx.TOP, 0)

        vbox.Add(qbox_sizer, (1, 0), (1, 1),
            wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        # Output data
        outputbox = wx.StaticBox(self, -1, "Output Measuments")
        outputbox_sizer = wx.StaticBoxSizer(outputbox, wx.VERTICAL)

        output_sizer = wx.GridBagSizer(5, 5)

        label_strings = [
            "Long Period (A): ",
            "Average Hard Block Thickness (A): ",
            "Average Interface Thickness (A): ",
            "Average Core Thickness: ",
            "PolyDispersity: ",
            "Filling Fraction: "
        ]
        self._output_ids = dict()
        for i in range(len(label_strings)):
            label = wx.StaticText(self, -1, label_strings[i])
            output_box = OutputTextCtrl(self, wx.NewId(), size=(50, 20),
                value="-", style=wx.ALIGN_CENTER_HORIZONTAL)
            self._output_ids[label_strings[i]] = output_box.GetId()
            output_sizer.Add(label, (i, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
            output_sizer.Add(output_box, (i, 2), (1, 1),
                wx.RIGHT | wx.EXPAND, 15)

        outputbox_sizer.Add(output_sizer, wx.TOP, 0)

        vbox.Add(outputbox_sizer, (2, 0), (1, 1),
            wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)


        controlbox = wx.StaticBox(self, -1, "Controls")
        controlbox_sizer = wx.StaticBoxSizer(controlbox, wx.VERTICAL)

        controls_sizer = wx.BoxSizer(wx.VERTICAL)

        extrapolate_btn = wx.Button(self, wx.NewId(), "Extrapolate")
        transform_btn = wx.Button(self, wx.NewId(), "Transform")
        compute_btn = wx.Button(self, wx.NewId(), "Compute Measuments")

        controls_sizer.Add(extrapolate_btn, wx.CENTER | wx.EXPAND)
        controls_sizer.Add(transform_btn, wx.CENTER | wx.EXPAND)
        controls_sizer.Add(compute_btn, wx.CENTER | wx.EXPAND)

        controlbox_sizer.Add(controls_sizer, wx.TOP | wx.EXPAND, 0)
        vbox.Add(controlbox_sizer, (3, 0), (1, 1),
            wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        self.SetSizer(vbox)
