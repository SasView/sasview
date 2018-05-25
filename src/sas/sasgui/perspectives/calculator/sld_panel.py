"""
This module provide GUI for the neutron scattering length density calculator

"""

import wx
import math
import sys

from sas.sasgui.guiframe.panel_base import PanelBase

from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.utils import check_float
from sas.sasgui.guiframe.events import StatusEvent

# the calculator default value for wavelength is 6
#import periodictable
from periodictable import formula
from periodictable.xsf import xray_energy
from periodictable.xsf import xray_sld_from_atoms
from periodictable.nsf import neutron_scattering
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

WAVELENGTH = 6.0
_BOX_WIDTH = 76
_STATICBOX_WIDTH = 350
_SCALE = 1e-6

#SLD panel size 
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    _STATICBOX_WIDTH = 350
    PANEL_SIZE = 400
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    _STATICBOX_WIDTH = 380
    PANEL_SIZE = 410
    FONT_VARIANT = 1

class SldPanel(wx.Panel, PanelBase):
    """
    Provides the SLD calculator GUI.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "SLD Calculator"
    ## Name to appear on the window title bar
    window_caption = "SLD Calculator"
    ## Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True

    def __init__(self, parent, base=None, *args, **kwds):
        """
        """
        wx.Panel.__init__(self, parent, *args, **kwds)
        PanelBase.__init__(self)
        #Font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        # Object that receive status event
        self.base = base
        self.neutron_wavelength = WAVELENGTH
        self.xray_source_input = WAVELENGTH
        self.parent = parent
        #layout attribute
        self.compound_ctl = None
        self.density_ctl = None
        self.compound = ""
        self.density = ""
        self.neutron_wavelength_ctl = None
        self.xray_source_input_ctl = None
        self.xray_cbox = None
        self.neutron_sld_real_ctl = None
        self.neutron_sld_im_ctl = None
        self.xray_sld_real_ctl = None
        self.xray_sld_im_ctl = None
        self.neutron_abs_ctl = None
        self.neutron_inc_ctl = None
        self.neutron_length_ctl = None
        self.button_calculate = None
        self.xray_source = None
        #Draw the panel
        self._do_layout()
        self.SetAutoLayout(True)
        self.Layout()
        self.fill_xray_cbox()

    def _do_layout(self):
        """
        Draw window content
        """
        unit_a = '[A]'
        unit_density = '[g/cm^(3)]'
        unit_sld = '[1/A^(2)]'
        unit_cm1 = '[1/cm]'
        unit_cm = '[cm]'
        sizer_input = wx.GridBagSizer(5, 5)
        sizer_output = wx.GridBagSizer(5, 5)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        #---------inputs----------------
        inputbox = wx.StaticBox(self, -1, "Input")
        boxsizer1 = wx.StaticBoxSizer(inputbox, wx.VERTICAL)
        boxsizer1.SetMinSize((_STATICBOX_WIDTH, -1))

        compound_txt = wx.StaticText(self, -1, 'Compound ')
        self.compound_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH * 2, -1))
        density_txt = wx.StaticText(self, -1, 'Density ')
        self.density_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        unit_density_txt = wx.StaticText(self, -1, unit_density)
        neutron_wavelength_txt = wx.StaticText(self, -1, 'Neutron wavelength')
        self.neutron_wavelength_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        self.neutron_wavelength_ctl.SetValue(str(self.neutron_wavelength))
        self.xray_source_input_txt = wx.StaticText(self, -1, 'X-ray wavelength')
        self.xray_source_input_ctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH, -1))
        self.xray_source_input_ctl.SetValue(str(self.xray_source_input))
        neutron_unit_a_txt = wx.StaticText(self, -1, unit_a)

        self.xray_cbox = wx.ComboBox(self, -1, size=(70, 20), style=wx.CB_READONLY)
        xray_cbox_tip = "Select an element, wavelength or energy"
        self.xray_cbox.SetToolTipString(xray_cbox_tip)
        wx.EVT_COMBOBOX(self.xray_cbox, -1, self.on_select_xray)

        iy = 0
        ix = 0
        sizer_input.Add(compound_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.compound_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_input.Add(density_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.density_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_input.Add(unit_density_txt, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_input.Add(neutron_wavelength_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.neutron_wavelength_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_input.Add(neutron_unit_a_txt, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_input.Add(self.xray_source_input_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_input.Add(self.xray_source_input_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_input.Add(self.xray_cbox, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        boxsizer1.Add(sizer_input)
        sizer1.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)
        #---------Outputs sizer--------
        outputbox = wx.StaticBox(self, -1, "Output")
        boxsizer2 = wx.StaticBoxSizer(outputbox, wx.VERTICAL)
        boxsizer2.SetMinSize((_STATICBOX_WIDTH, -1))

        i_complex = '- i'
        neutron_sld_txt = wx.StaticText(self, -1, 'Neutron SLD')
        self.neutron_sld_real_ctl = wx.TextCtrl(self, -1,
                                                 size=(_BOX_WIDTH, -1))
        self.neutron_sld_real_ctl.SetEditable(False)
        self.neutron_sld_real_ctl.SetToolTipString("Neutron SLD real")
        self.neutron_sld_im_ctl = wx.TextCtrl(self, -1,
                                              size=(_BOX_WIDTH, -1))
        self.neutron_sld_im_ctl.SetEditable(False)
        self.neutron_sld_im_ctl.SetToolTipString("Neutron SLD imaginary")
        neutron_sld_units_txt = wx.StaticText(self, -1, unit_sld)

        xray_sld_txt = wx.StaticText(self, -1, 'X-ray SLD')
        self.xray_sld_real_ctl = wx.TextCtrl(self, -1,
                                               size=(_BOX_WIDTH, -1))
        self.xray_sld_real_ctl.SetEditable(False)
        self.xray_sld_real_ctl.SetToolTipString("X-ray SLD real")
        self.xray_sld_im_ctl = wx.TextCtrl(self, -1,
                                            size=(_BOX_WIDTH, -1))
        self.xray_sld_im_ctl.SetEditable(False)
        self.xray_sld_im_ctl.SetToolTipString("X-ray SLD imaginary")
        xray_sld_units_txt = wx.StaticText(self, -1, unit_sld)

        neutron_inc_txt = wx.StaticText(self, -1, 'Neutron Inc. Xs')
        self.neutron_inc_ctl = wx.TextCtrl(self, -1,
                                            size=(_BOX_WIDTH, -1))
        self.neutron_inc_ctl.SetEditable(False)
        self.neutron_inc_ctl.SetToolTipString("Neutron Inc. Xs")
        neutron_inc_units_txt = wx.StaticText(self, -1, unit_cm1)

        neutron_abs_txt = wx.StaticText(self, -1, 'Neutron Abs. Xs')
        self.neutron_abs_ctl = wx.TextCtrl(self, -1,
                                           size=(_BOX_WIDTH, -1))
        self.neutron_abs_ctl.SetEditable(False)
        self.neutron_abs_ctl.SetToolTipString("Neutron Abs. Xs")
        neutron_abs_units_txt = wx.StaticText(self, -1, unit_cm1)

        neutron_length_txt = wx.StaticText(self, -1, 'Neutron 1/e length')
        self.neutron_length_ctl = wx.TextCtrl(self, -1,
                                               size=(_BOX_WIDTH, -1))
        self.neutron_length_ctl.SetEditable(False)
        self.neutron_length_ctl.SetToolTipString("Neutron 1/e length")
        neutron_length_units_txt = wx.StaticText(self, -1, unit_cm)

        iy = 0
        ix = 0
        sizer_output.Add(neutron_sld_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.neutron_sld_real_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(wx.StaticText(self, -1, i_complex),
                         (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(self.neutron_sld_im_ctl,
                         (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(neutron_sld_units_txt,
                         (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_output.Add(xray_sld_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.xray_sld_real_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(wx.StaticText(self, -1, i_complex),
                         (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(self.xray_sld_im_ctl,
                         (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        sizer_output.Add(xray_sld_units_txt,
                         (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_output.Add(neutron_inc_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.neutron_inc_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer_output.Add(neutron_inc_units_txt, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_output.Add(neutron_abs_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.neutron_abs_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer_output.Add(neutron_abs_units_txt, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        sizer_output.Add(neutron_length_txt, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        sizer_output.Add(self.neutron_length_ctl, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 2
        sizer_output.Add(neutron_length_units_txt, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        boxsizer2.Add(sizer_output)
        sizer2.Add(boxsizer2, 0, wx.EXPAND | wx.ALL, 10)
        #-----Button  sizer------------

        id = wx.NewId()
        self.button_calculate = wx.Button(self, id, "Calculate")
        self.button_calculate.SetToolTipString("Calculate SLD.")
        self.Bind(wx.EVT_BUTTON, self.calculateSld, id=id)

        id = wx.NewId()
        self.button_help = wx.Button(self, id, "HELP")
        self.button_help.SetToolTipString("help on SLD calculator.")
        self.Bind(wx.EVT_BUTTON, self.on_help, id=id)

        self.button_close = wx.Button(self, wx.ID_CANCEL, 'Close')
        self.button_close.Bind(wx.EVT_BUTTON, self.on_close)
        self.button_close.SetToolTipString("Close this window.")

        sizer_button.Add((150, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(self.button_calculate, 0, wx.RIGHT | wx.ADJUST_MINSIZE, 20)
        sizer_button.Add(self.button_help, 0, wx.RIGHT | wx.ADJUST_MINSIZE, 20)
        sizer_button.Add(self.button_close, 0, wx.RIGHT | wx.ADJUST_MINSIZE, 20)
        sizer3.Add(sizer_button)
        #---------layout----------------
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(sizer1)
        vbox.Add(sizer2)
        vbox.Add(sizer3)
        vbox.Fit(self)
        self.SetSizer(vbox)

    def fill_xray_cbox(self):
        """
        fill the x-ray combobox with the sources
        """
        source_list = ['[A]', '[keV]', 'Element']
        for source in source_list:
            pos = self.xray_cbox.Append(str(source))
            self.xray_cbox.SetClientData(pos, str(source.strip()))
        self.xray_cbox.SetSelection(0)
        self.xray_source = source_list[0]

    def on_select_xray(self, event=None):
        """
        On Selecting a source
        """
        item = event.GetEventObject()
        self.xray_source = item.GetValue().strip()

        if self.xray_source == "[A]":
            self.xray_source_input_txt.SetLabel("X-ray wavelength")
        elif self.xray_source == "[keV]":
            self.xray_source_input_txt.SetLabel("X-ray energy")
        elif self.xray_source == "Element":
            self.xray_source_input_txt.SetLabel("X-ray source")

    def on_help(self, event):
        """
        Bring up the SLD Documentation whenever
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
        _TreeLocation += "sld_calculator_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "General Scattering Calculator Help")

    def on_close(self, event):
        """
        close the window containing this panel
        """
        self.parent.Close()

    def calculate_xray_sld(self, element):
        """
        Get an element and compute the corresponding SLD for a given formula

        :param element:  elements a string of existing atom

        """
        myformula = formula(str(element))
        if len(myformula.atoms) != 1:
            return
        element = list(myformula.atoms.keys())[0]
        energy = xray_energy(element.K_alpha)

        self.sld_formula = formula(str(self.compound), density=self.density)
        atom = self.sld_formula.atoms
        return xray_sld_from_atoms(atom, density=self.density, energy=energy)

    def check_inputs(self):
        """Check validity user inputs"""
        flag = True
        msg = ""
        if check_float(self.density_ctl):
            self.density = float(self.density_ctl.GetValue())
        else:
            flag = False
            msg += "Error for Density value :expect float"

        self.neutron_wavelength = self.neutron_wavelength_ctl.GetValue()
        self.xray_source_input = self.xray_source_input_ctl.GetValue()

        if str(self.neutron_wavelength).lstrip().rstrip() == "":
            self.neutron_wavelength = WAVELENGTH
            self.neutron_wavelength_ctl.SetValue(str(WAVELENGTH))
            self.neutron_wavelength_ctl.SetBackgroundColour(wx.WHITE)
            self.neutron_wavelength_ctl.Refresh()
            msg += "Default value for wavelength is 6.0"
        else:
            if check_float(self.neutron_wavelength_ctl):
                self.neutron_wavelength = float(self.neutron_wavelength)
            else:
                flag = False
                msg += "Error for wavelength value :expect float"

        if str(self.xray_source_input).lstrip().rstrip() == "":
            self.xray_source_input = WAVELENGTH
            self.xray_source_input_ctl.SetValue(str(WAVELENGTH))
            self.xray_source_input_ctl.SetBackgroundColour(wx.WHITE)
            self.xray_source_input_ctl.Refresh()
            msg += "Default value for wavelength is 6.0"
        else:
            if (self.xray_source == '[A]') or (self.xray_source == '[keV]'):
                if check_float(self.xray_source_input_ctl):
                    self.xray_source_input = float(self.xray_source_input)
                else:
                    flag = False
                    msg += "Error for wavelength value :expect float"
            elif (self.xray_source == 'Element'):
                try:
                    import periodictable
                    exec("periodictable." + self.xray_source_input)
                except AttributeError:
                    flag = False
                    msg += "X-ray element supplied isn't in the database"



        self.compound = self.compound_ctl.GetValue().lstrip().rstrip()
        if self.compound != "":
            try :
                formula(self.compound)
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
            msg += "Enter a formula"
        return flag, msg

    def calculate_sld_helper(self, element, density, molecule_formula):
        """
        Get an element and compute the corresponding SLD for a given formula

        :param element:  elements a string of existing atom

        """
        element_formula = formula(str(element))
        if len(element_formula.atoms) != 1:
            return
        element = list(element_formula.atoms.keys())[0]
        energy = xray_energy(element.K_alpha)
        atom = molecule_formula.atoms
        return xray_sld_from_atoms(atom, density=density, energy=energy)

    def calculateSld(self, event):
        """
            Calculate the neutron scattering density length of a molecule
        """
        self.clear_outputs()
        try:
            #Check validity user inputs
            flag, msg = self.check_inputs()
            if self.base is not None and msg.lstrip().rstrip() != "":
                msg = "SLD Calculator: %s" % str(msg)
                wx.PostEvent(self.base, StatusEvent(status=msg))
            if not flag:
               return
            #get ready to compute
            self.sld_formula = formula(self.compound,
                                            density=self.density)
            (sld_real, sld_im, _), (_, absorp, incoh), \
                        length = neutron_scattering(compound=self.compound,
                                   density=self.density,
                                   wavelength=self.neutron_wavelength)
            if self.xray_source == "[A]":
                energy = xray_energy(self.xray_source_input)
                xray_real, xray_im = xray_sld_from_atoms(self.sld_formula.atoms,
                                                         density=self.density,
                                                         energy=energy)
            elif self.xray_source == "[keV]":
                xray_real, xray_im = xray_sld_from_atoms(self.sld_formula.atoms,
                                                         density=self.density,
                                                         energy=self.xray_source_input)
            elif self.xray_source == "Element":
                xray_real, xray_im = self.calculate_sld_helper(element=self.xray_source_input,
                                                               density=self.density,
                                                               molecule_formula=self.sld_formula)
            # set neutron sld values
            val = format_number(sld_real * _SCALE)
            self.neutron_sld_real_ctl.SetValue(val)
            val = format_number(math.fabs(sld_im) * _SCALE)
            self.neutron_sld_im_ctl.SetValue(val)
            # Compute the Cu SLD
            self.xray_sld_real_ctl.SetValue(format_number(xray_real * _SCALE))
            val = format_number(math.fabs(xray_im) * _SCALE)
            self.xray_sld_im_ctl.SetValue(val)
            # set incoherence and absorption
            self.neutron_inc_ctl.SetValue(format_number(incoh))
            self.neutron_abs_ctl.SetValue(format_number(absorp))
            # Neutron length
            self.neutron_length_ctl.SetValue(format_number(length))
            # display wavelength
            #self.wavelength_ctl.SetValue(str(self.wavelength))
            #self.wavelength_ctl.SetValue(str(self.wavelength))
        except:
            if self.base is not None:
                msg = "SLD Calculator: %s" % (sys.exc_info()[1])
                wx.PostEvent(self.base, StatusEvent(status=msg))
        if event is not None:
            event.Skip()

    def clear_outputs(self):
        """
        Clear the outputs textctrl
        """
        self.neutron_sld_real_ctl.SetValue("")
        self.neutron_sld_im_ctl.SetValue("")
        self.xray_sld_real_ctl.SetValue("")
        self.xray_sld_im_ctl.SetValue("")
        self.neutron_abs_ctl.SetValue("")
        self.neutron_inc_ctl.SetValue("")
        self.neutron_length_ctl.SetValue("")


class SldWindow(widget.CHILD_FRAME):
    """
    """
    def __init__(self, parent=None, title="SLD Calculator",
                  base=None, manager=None,
                  size=(PANEL_SIZE, PANEL_SIZE), *args, **kwds):
        """
        """
        kwds['title'] = title
        kwds['size'] = size
        widget.CHILD_FRAME.__init__(self, parent, *args, **kwds)
        """
        """
        self.parent = parent
        self.base = base
        self.manager = manager
        self.panel = SldPanel(self, base=base)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.SetPosition((wx.LEFT, PANEL_TOP))
        self.Show(True)

    def on_close(self, event):
        """
        On close event
        """
        if self.manager is not None:
            self.manager.sld_frame = None
        self.Destroy()


class ViewApp(wx.App):
    """
    """
    def OnInit(self):
        """
        """
        widget.CHILD_FRAME = wx.Frame
        frame = SldWindow(None, title='SLD Calculator')
        frame.Show(True)
        self.SetTopWindow(frame)
        return True


if __name__ == "__main__":
    app = ViewApp(0)
    app.MainLoop()
