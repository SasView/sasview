import wx
import sys
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.events import PlotQrangeEvent
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.guiframe.utils import check_float
from sas.sasgui.perspectives.invariant.invariant_widgets import OutputTextCtrl
from sas.sasgui.perspectives.invariant.invariant_widgets import InvTextCtrl
from sas.sasgui.perspectives.fitting.basepage import ModelTextCtrl

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
        self._data = data # The data to be analysed
        self._data_name_box = None # Text box to show name of file
        self._qmin_input = None
        self._qmax1_input = None
        self._qmax2_input = None
        self._qmin = 0
        self._qmax = (0, 0)
        # Dictionary for saving IDs of text boxes used to display output data
        self._output_ids = None
        self.state = None
        self.set_state()
        self._do_layout()
        self._qmin_input.Bind(wx.EVT_TEXT, self._on_enter_qrange)
        self._qmax1_input.Bind(wx.EVT_TEXT, self._on_enter_qrange)
        self._qmax2_input.Bind(wx.EVT_TEXT, self._on_enter_qrange)

    def set_state(self, state=None, data=None):
        # TODO: Implement state restoration
        return False

    def onSetFocus(self, evt):
        if evt is not None:
            evt.Skip()
        self._validate_qrange()

    def _set_data(self, data=None):
        """
        Update the GUI to reflect new data that has been loaded in

        :param data: The data that has been loaded
        """
        self._data_name_box.SetValue(str(data.name))
        self._data = data
        if self._manager is not None:
            self._manager.show_data(data=data, reset=True)
        lower = data.x[-1]*0.05
        upper1 = data.x[-1] - lower*5
        upper2 = data.x[-1]
        self.set_qmin(lower)
        self.set_qmax((upper1, upper2))


    def _on_enter_qrange(self, event):
        """
        Read values from input boxes and save to memory.
        """
        event.Skip()
        if not self._validate_qrange():
            return
        new_qmin = float(self._qmin_input.GetValue())
        new_qmax1 = float(self._qmax1_input.GetValue())
        new_qmax2 = float(self._qmax2_input.GetValue())
        self.qmin = new_qmin
        self.qmax = (new_qmax1, new_qmax2)
        data_id = self._manager.data_id
        from sas.sasgui.perspectives.corfunc.corfunc import GROUP_ID_IQ_DATA
        group_id = GROUP_ID_IQ_DATA
        wx.PostEvent(self._manager.parent, PlotQrangeEvent(
            ctrl=[self._qmin_input, self._qmax1_input, self._qmax2_input],
            active=event.GetEventObject(), id=data_id, group_id=group_id,
            leftdown=False))

    def set_qmin(self, qmin):
        self.qmin = qmin
        self._qmin_input.SetValue(str(qmin))

    def set_qmax(self, qmax):
        self.qmax = qmax
        self._qmax1_input.SetValue(str(qmax[0]))
        self._qmax2_input.SetValue(str(qmax[1]))

    def _validate_qrange(self):
        """
        Check that the values for qmin and qmax in the input boxes are valid
        """
        if self._data is None:
            return False
        qmin_valid = check_float(self._qmin_input)
        qmax1_valid = check_float(self._qmax1_input)
        qmax2_valid = check_float(self._qmax2_input)
        qmax_valid = qmax1_valid and qmax2_valid
        if not (qmin_valid and qmax_valid):
            if not qmin_valid:
                self._qmin_input.SetBackgroundColour('pink')
                self._qmin_input.Refresh()
            if not qmax1_valid:
                self._qmax1_input.SetBackgroundColour('pink')
                self._qmax1_input.Refresh()
            if not qmax2_valid:
                self._qmax2_input.SetBackgroundColour('pink')
                self._qmax2_input.Refresh()
            return False
        qmin = float(self._qmin_input.GetValue())
        qmax1 = float(self._qmax1_input.GetValue())
        qmax2 = float(self._qmax2_input.GetValue())
        msg = ""
        if not qmin > self._data.x.min():
            msg = "qmin must be greater than the lowest q value"
            qmin_valid = False
        elif qmax2 < qmax1:
            "qmax1 must be less than qmax2"
            qmax_valid = False
        elif qmin > qmax1:
            "qmin must be less than qmax"
            qmin_valid = False
        # import pdb; pdb.set_trace()
        if not (qmin_valid and qmax_valid):
            if not qmin_valid:
                self._qmin_input.SetBackgroundColour('pink')
            if not qmax_valid:
                self._qmax1_input.SetBackgroundColour('pink')
                self._qmax2_input.SetBackgroundColour('pink')
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        else:
            self._qmin_input.SetBackgroundColour(wx.WHITE)
            self._qmax1_input.SetBackgroundColour(wx.WHITE)
            self._qmax2_input.SetBackgroundColour(wx.WHITE)
        self._qmin_input.Refresh()
        self._qmax1_input.Refresh()
        self._qmax2_input.Refresh()
        return (qmin_valid and qmax_valid)

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
        self._qmin_input = ModelTextCtrl(self, -1, size=(50, 20),
                        style=wx.TE_PROCESS_ENTER, name='qmin_input',
                        text_enter_callback=self._on_enter_qrange)
        self._qmin_input.SetToolTipString(("Values with q < qmin will be used "
            "for Guinier back extrapolation"))

        q_sizer.Add(qmin_label, (2, 0), (1, 1), wx.LEFT | wx.EXPAND, 5)
        q_sizer.Add(qmin_lower, (2, 1), (1, 1), wx.LEFT, 5)
        q_sizer.Add(qmin_dash_label, (2, 2), (1, 1), wx.CENTER | wx.EXPAND, 5)
        q_sizer.Add(self._qmin_input, (2, 3), (1, 1), wx.LEFT, 5)

        # Upper Q range
        qmax_tooltip = ("Values with qmax1 < q < qmax2 will be used for Porod"
            " forward extrapolation")

        qmax_label = wx.StaticText(self, -1, "Upper:", size=(50,20))
        qmax_dash_label = wx.StaticText(self, -1, "-", size=(10,20),
            style=wx.ALIGN_CENTER_HORIZONTAL)

        self._qmax1_input = ModelTextCtrl(self, -1, size=(50, 20),
            style=wx.TE_PROCESS_ENTER, name="qmax1_input",
            text_enter_callback=self._on_enter_qrange)
        self._qmax1_input.SetToolTipString(qmax_tooltip)
        self._qmax2_input = ModelTextCtrl(self, -1, size=(50, 20),
            style=wx.TE_PROCESS_ENTER, name="qmax2_input",
            text_enter_callback=self._on_enter_qrange)
        self._qmax2_input.SetToolTipString(qmax_tooltip)

        q_sizer.Add(qmax_label, (3, 0), (1, 1), wx.LEFT | wx.EXPAND, 5)
        q_sizer.Add(self._qmax1_input, (3, 1), (1, 1), wx.LEFT, 5)
        q_sizer.Add(qmax_dash_label, (3, 2), (1, 1), wx.CENTER | wx.EXPAND, 5)
        q_sizer.Add(self._qmax2_input, (3,3), (1, 1), wx.LEFT, 5)

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
            # Create a label and a text box for each poperty
            label = wx.StaticText(self, -1, label_strings[i])
            output_box = OutputTextCtrl(self, wx.NewId(), size=(50, 20),
                value="-", style=wx.ALIGN_CENTER_HORIZONTAL)
            # Save the ID of each of the text boxes for accessing after the
            # output data has been calculated
            self._output_ids[label_strings[i]] = output_box.GetId()
            output_sizer.Add(label, (i, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
            output_sizer.Add(output_box, (i, 2), (1, 1),
                wx.RIGHT | wx.EXPAND, 15)

        outputbox_sizer.Add(output_sizer, wx.TOP, 0)

        vbox.Add(outputbox_sizer, (2, 0), (1, 1),
            wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        # Controls
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
