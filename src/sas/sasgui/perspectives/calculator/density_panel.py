"""
This module provide GUI for the mass density calculator

"""
import wx
import sys
from sas.sasgui.guiframe.panel_base import PanelBase
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.utils import check_float
from sas.sasgui.guiframe.events import StatusEvent
from periodictable import formula as Formula
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

AVOGADRO = 6.02214129e23
_INPUTS = ['Mass Density', 'Molar Volume']
_UNITS = ['g/cm^(3)     ', 'cm^(3)/mol ']
#Density panel size 
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    _STATICBOX_WIDTH = 410
    _BOX_WIDTH = 200
    PANEL_SIZE = 440
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    _STATICBOX_WIDTH = 430
    _BOX_WIDTH = 200
    PANEL_SIZE = 460
    FONT_VARIANT = 1

class DensityPanel(ScrolledPanel, PanelBase):
    """
    Provides the mass density calculator GUI.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Mass Density Calculator"
    ## Name to appear on the window title bar
    window_caption = "Mass Density Calculator"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True

    def __init__(self, parent, base=None, *args, **kwds):
        """
        """
        ScrolledPanel.__init__(self, parent, *args, **kwds)
        PanelBase.__init__(self)
        self.SetupScrolling()
        #Font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        # Object that receive status event
        self.base = base
        self.parent = parent
        # chemeical formula, string
        self.compound = ''
        # value of the density/volume, float
        self.input = None
        # text controls
        self.compound_ctl = None
        self.input_ctl = None
        self.molar_mass_ctl = None
        self.output_ctl = None
        self.ctr_color = self.GetBackgroundColour()
        # button
        self.button_calculate = None
        # list
        self._input_list = _INPUTS
        self._input = self._input_list[1]
        self._output = self._input_list[0]
        self._unit_list = _UNITS
        #Draw the panel
        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()

    def _do_layout(self):
        """
        Draw window content
        """
        # units
        unit_density = self._unit_list[0]
        unit_volume = self._unit_list[1]

        # sizers
        sizer_input = wx.GridBagSizer(5, 5)
        sizer_output = wx.GridBagSizer(5, 5)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # inputs
        inputbox = wx.StaticBox(self, -1, "Inputs")
        boxsizer1 = wx.StaticBoxSizer(inputbox, wx.VERTICAL)
        boxsizer1.SetMinSize((_STATICBOX_WIDTH, -1))
        compound_txt = wx.StaticText(self, -1, 'Molecular Formula ')
        self.compound_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        self.compound_eg1 = wx.StaticText(self, -1, '     e.g., H2O')
        self.compound_eg2 = wx.StaticText(self, -1, 'e.g., D2O')
        self.input_cb = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.input_cb, -1, self.on_select_input)
        hint_input_name_txt = 'Mass or volume.'
        self.input_cb.SetToolTipString(hint_input_name_txt)
        unit_density1 = "     " + unit_density
        self.input_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        self.unit_input_density = wx.StaticText(self, -1, unit_density1)
        self.unit_input_volume = wx.StaticText(self, -1, unit_volume)
        iy = 0
        ix = 0
        sizer_input.Add(compound_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.compound_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_input.Add(self.compound_eg1, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        ix += 1
        sizer_input.Add(self.compound_eg2, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        self.compound_eg1.Show(False)
        iy += 1
        ix = 0
        sizer_input.Add(self.input_cb, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.input_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_input.Add(self.unit_input_density, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.unit_input_density.Show(False)
        sizer_input.Add(self.unit_input_volume, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        boxsizer1.Add(sizer_input)
        self.sizer1.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)

        # outputs
        outputbox = wx.StaticBox(self, -1, "Outputs")
        boxsizer2 = wx.StaticBoxSizer(outputbox, wx.VERTICAL)
        boxsizer2.SetMinSize((_STATICBOX_WIDTH, -1))

        molar_mass_txt = wx.StaticText(self, -1, 'Molar Mass ')
        self.molar_mass_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        self.molar_mass_ctl.SetEditable(False)
        self.molar_mass_ctl.SetBackgroundColour(self.ctr_color)
        self.molar_mass_unit1 = wx.StaticText(self, -1, '     g/mol')
        self.molar_mass_unit2 = wx.StaticText(self, -1, 'g/mol')

        self.output_cb = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.output_cb, -1, self.on_select_output)
        hint_output_name_txt = 'Mass or volume.'
        self.output_cb.SetToolTipString(hint_output_name_txt)
        list = []
        for item in self._input_list:
            name = str(item)
            list.append(name)
        list.sort()
        for idx in range(len(list)):
            self.input_cb.Append(list[idx], idx)
            self.output_cb.Append(list[idx], idx)
        self.input_cb.SetStringSelection("Molar Volume")
        self.output_cb.SetStringSelection("Mass Density")
        unit_volume = "     " + unit_volume
        self.output_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        self.output_ctl.SetEditable(False)
        self.output_ctl.SetBackgroundColour(self.ctr_color)
        self.unit_output_density = wx.StaticText(self, -1, unit_density)
        self.unit_output_volume = wx.StaticText(self, -1, unit_volume)
        iy = 0
        ix = 0
        sizer_output.Add(molar_mass_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.molar_mass_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(self.molar_mass_unit1, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(self.molar_mass_unit2, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        self.molar_mass_unit1.Show(False)
        iy += 1
        ix = 0
        sizer_output.Add(self.output_cb, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.output_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(self.unit_output_volume,
                         (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(self.unit_output_density,
                         (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        self.unit_output_volume.Show(False)
        boxsizer2.Add(sizer_output)
        self.sizer2.Add(boxsizer2, 0, wx.EXPAND | wx.ALL, 10)

        # buttons
        id = wx.NewId()
        self.button_calculate = wx.Button(self, id, "Calculate")
        self.button_calculate.SetToolTipString("Calculate.")
        self.Bind(wx.EVT_BUTTON, self.calculate, id=id)

        id = wx.NewId()
        self.button_help = wx.Button(self, id, "HELP")
        self.button_help.SetToolTipString("Help for density calculator.")
        self.Bind(wx.EVT_BUTTON, self.on_help, id=id)

        self.button_close = wx.Button(self, wx.ID_CANCEL, 'Close')
        self.button_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.button_close.SetToolTipString("Close this window.")

        sizer_button.Add((100, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.button_calculate, 0,
                                        wx.RIGHT | wx.ADJUST_MINSIZE, 20)
        sizer_button.Add(self.button_help, 0,
                                        wx.RIGHT | wx.ADJUST_MINSIZE, 20)
        sizer_button.Add(self.button_close, 0,
                                        wx.RIGHT | wx.ADJUST_MINSIZE, 20)
        sizer3.Add(sizer_button)

        # layout
        vbox.Add(self.sizer1)
        vbox.Add(self.sizer2)
        vbox.Add(sizer3)
        vbox.Fit(self)
        self.SetSizer(vbox)

    def on_select_input(self, event):
        """
        On selection of input combobox,
        update units and output combobox
        """
        if event is None:
            return
        event.Skip()

        combo = event.GetEventObject()
        self._input = combo.GetValue()
        for name in self._input_list:
            if self._input != name:
                self._output = name
                break

        self.set_values()

    def on_select_output(self, event):
        """
        On selection of output combobox,
        update units and input combobox
        """
        if event is None:
            return
        event.Skip()

        combo = event.GetEventObject()
        self._output = combo.GetValue()
        for name in self._input_list:
            if self._output != name:
                self._input = name
                break

        self.set_values()

    def set_values(self):
        """
        Sets units and combobox values
        """
        input, output = self.get_input()
        if input is None:
            return
        # input
        self.input_cb.SetValue(str(input))
        # output
        self.output_cb.SetValue(str(output))
        # unit
        if self._input_list.index(input) == 0:
            self.molar_mass_unit1.Show(True)
            self.molar_mass_unit2.Show(False)
            self.compound_eg1.Show(True)
            self.compound_eg2.Show(False)
            self.unit_input_density.Show(True)
            self.unit_output_volume.Show(True)
            self.unit_input_volume.Show(False)
            self.unit_output_density.Show(False)
        else:
            self.molar_mass_unit1.Show(False)
            self.molar_mass_unit2.Show(True)
            self.compound_eg1.Show(False)
            self.compound_eg2.Show(True)
            self.unit_input_volume.Show(True)
            self.unit_output_density.Show(True)
            self.unit_input_density.Show(False)
            self.unit_output_volume.Show(False)
        # layout    
        self.clear_outputs()
        self.sizer1.Layout()
        self.sizer2.Layout()

    def get_input(self):
        """
        Return the current input and output combobox values
        """
        return self._input, self._output

    def check_inputs(self):
        """
        Check validity user inputs
        """
        flag = True
        msg = ""
        if check_float(self.input_ctl):
            self.input = float(self.input_ctl.GetValue())
        else:
            flag = False
            input_type = str(self.input_cb.GetValue())
            msg += "Error for %s value :expect float" % input_type

        self.compound = self.compound_ctl.GetValue().lstrip().rstrip()
        if self.compound != "":
            try :
                Formula(self.compound)
                self.compound_ctl.SetBackgroundColour(wx.WHITE)
                self.compound_ctl.Refresh()
            except:
                self.compound_ctl.SetBackgroundColour("pink")
                self.compound_ctl.Refresh()
                flag = False
                msg += "Enter correct formula"
        else:
            self.compound_ctl.SetBackgroundColour("pink")
            self.compound_ctl.Refresh()
            flag = False
            msg += "Enter Formula"
        return flag, msg


    def calculate(self, event):
        """
        Calculate the mass Density/molar Volume of the molecules
        """
        self.clear_outputs()
        try:
            #Check validity user inputs
            flag, msg = self.check_inputs()
            if self.base is not None and msg.lstrip().rstrip() != "":
                msg = "Density/Volume Calculator: %s" % str(msg)
                wx.PostEvent(self.base, StatusEvent(status=msg))
            if not flag:
               return
            #get ready to compute
            mol_formula = Formula(self.compound)
            molar_mass = float(mol_formula.molecular_mass) * AVOGADRO
            output = self._format_number(molar_mass / self.input)
            self.molar_mass_ctl.SetValue(str(self._format_number(molar_mass)))
            self.output_ctl.SetValue(str(output))
        except:
            if self.base is not None:
                msg = "Density/Volume Calculator: %s" % (sys.exc_info()[1])
                wx.PostEvent(self.base, StatusEvent(status=msg))
        if event is not None:
            event.Skip()

    def on_help(self, event):
        """
        Bring up the density/volume calculator Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param evt: Triggers on clicking the help button
    """

        _TreeLocation = "user/sasgui/perspectives/calculator/"
        _TreeLocation += "density_calculator_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "Density/Volume Calculator Help")

    def on_close(self, event):
        """
        close the window containing this panel
        """
        self.parent.Close()

    def clear_outputs(self):
        """
        Clear the outputs textctrl
        """
        self.molar_mass_ctl.SetValue("")
        self.output_ctl.SetValue("")

    def _format_number(self, value=None):
        """
        Return a float in a standardized, human-readable formatted string
        """
        try:
            value = float(value)
        except:
            output = ''
            return output

        output = "%-12.5f" % value
        return output.lstrip().rstrip()

class DensityWindow(widget.CHILD_FRAME):
    """
    """
    def __init__(self, parent=None, title="Density/Volume Calculator",
                  base=None, manager=None,
                  size=(PANEL_SIZE * 1.05, PANEL_SIZE / 1.55), *args, **kwds):
        """
        """
        kwds['title'] = title
        kwds['size'] = size
        widget.CHILD_FRAME.__init__(self, parent, *args, **kwds)
        """
        """
        self.manager = manager
        self.panel = DensityPanel(self, base=base)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetPosition((wx.LEFT, PANEL_TOP))
        self.Show(True)

    def on_close(self, event):
        """
        On close event
        """
        if self.manager is not None:
            self.manager.cal_md_frame = None
        self.Destroy()


class ViewApp(wx.App):
    """
    """
    def OnInit(self):
        """
        """
        widget.CHILD_FRAME = wx.Frame
        frame = DensityWindow(None, title="Density/Volume Calculator")
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


if __name__ == "__main__":
    app = ViewApp(0)
    app.MainLoop()
