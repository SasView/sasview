#!/usr/bin/env python

# version
__id__ = "$Id: aboutdialog.py 1193 2007-05-03 17:29:59Z dmitriy $"
__revision__ = "$Revision: 1193 $"

import wx
import os
import sys
import logging
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.panel_base import PanelBase
from .inversion_state import InversionState
from .pr_widgets import PrTextCtrl
from .pr_widgets import DataFileTextCtrl
from .pr_widgets import OutputTextCtrl
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

logger = logging.getLogger(__name__)

if sys.platform.count("win32") > 0:
    FONT_VARIANT = 0
else:
    FONT_VARIANT = 1

class InversionControl(ScrolledPanel, PanelBase):
    """
    """
    window_name = 'pr_control'
    window_caption = "P(r) control panel"
    CENTER_PANE = True

    # Figure of merit parameters [default]

    ## Oscillation parameters (sin function = 1.1)
    oscillation_max = 1.5

    def __init__(self, parent, id=-1, plots=None, **kwargs):
        """
        """
        ScrolledPanel.__init__(self, parent, id=id, **kwargs)
        PanelBase.__init__(self, parent)
        self.SetupScrolling()
        #Set window's font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        self._set_analysis(False)

        self.plots = plots
        self.radio_buttons = {}
        self.parent = parent.parent

        ## Data file TextCtrl
        self.data_file = None
        self.plot_data = None
        self.nfunc_ctl = None
        self.alpha_ctl = None
        self.dmax_ctl = None
        self.time_ctl = None
        self.chi2_ctl = None
        self.osc_ctl = None
        self.file_radio = None
        self.plot_radio = None
        self.label_sugg = None
        self.qmin_ctl = None
        self.qmax_ctl = None
        self.swidth_ctl = None
        self.sheight_ctl = None

        self.rg_ctl = None
        self.iq0_ctl = None
        self.bck_value = None
        self.bck_est_ctl = None
        self.bck_man_ctl = None
        self.est_bck = True
        self.bck_input = None
        self.bck_ctl = None

        # TextCtrl for fraction of positive P(r)
        self.pos_ctl = None

        # TextCtrl for fraction of 1 sigma positive P(r)
        self.pos_err_ctl = None

        ## Estimates
        self.alpha_estimate_ctl = None
        self.nterms_estimate_ctl = None
        ## D_max distance explorator
        self.distance_explorator_ctl = None
        ## Data manager
        self._manager = None
        ## Default file location for save
        self._default_save_location = os.getcwd()
        if self.parent is not None:
            self._default_save_location = \
                        self.parent._default_save_location

        # Default width
        self._default_width = 350
        self._do_layout()

    def __setattr__(self, name, value):
        """
        Allow direct hooks to text boxes
        """
        if name == 'nfunc':
            self.nfunc_ctl.SetValue(str(int(value)))
        elif name == 'd_max':
            self.dmax_ctl.SetValue(str(value))
        elif name == 'alpha':
            self.alpha_ctl.SetValue(str(value))
        elif name == 'chi2':
            self.chi2_ctl.SetValue("%-5.2g" % value)
        elif name == 'bck':
            self.bck_ctl.SetValue("%-5.2g" % value)
        elif name == 'q_min':
            self.qmin_ctl.SetValue("%-5.2g" % value)
        elif name == 'q_max':
            self.qmax_ctl.SetValue("%-5.2g" % value)
        elif name == 'elapsed':
            self.time_ctl.SetValue("%-5.2g" % value)
        elif name == 'rg':
            self.rg_ctl.SetValue("%-5.2g" % value)
        elif name == 'iq0':
            self.iq0_ctl.SetValue("%-5.2g" % value)
        elif name == 'oscillation':
            self.osc_ctl.SetValue("%-5.2g" % value)
        elif name == 'slit_width':
            self.swidth_ctl.SetValue("%-5.2g" % value)
        elif name == 'slit_height':
            self.sheight_ctl.SetValue("%-5.2g" % value)
        elif name == 'positive':
            self.pos_ctl.SetValue("%-5.2g" % value)
        elif name == 'pos_err':
            self.pos_err_ctl.SetValue("%-5.2g" % value)
        elif name == 'alpha_estimate':
            self.alpha_estimate_ctl.SetToolTipString("Click to accept value.")
            self.alpha_estimate_ctl.Enable(True)
            self.alpha_estimate_ctl.SetLabel("%-3.1g" % value)
            #self.alpha_estimate_ctl.Show()
            #self.label_sugg.Show()
        elif name == 'nterms_estimate':
            self.nterms_estimate_ctl.SetToolTipString("Click to accept value.")
            self.nterms_estimate_ctl.Enable(True)
            self.nterms_estimate_ctl.SetLabel("%-g" % value)
        elif name == 'plotname':
            self.plot_data.SetValue(str(value))
            self._on_pars_changed(None)
        elif name == 'datafile':
            self.plot_data.SetValue(str(value))
            self._on_pars_changed(None)
        else:
            wx.Panel.__setattr__(self, name, value)

    def __getattr__(self, name):
        """
        Allow direct hooks to text boxes
        """
        if name == 'nfunc':
            try:
                return int(self.nfunc_ctl.GetValue())
            except:
                return -1
        elif name == 'd_max':
            try:
                return self.dmax_ctl.GetValue()
            except:
                return -1.0
        elif name == 'alpha':
            try:
                return self.alpha_ctl.GetValue()
            except:
                return -1.0
        elif name == 'chi2':
            try:
                return float(self.chi2_ctl.GetValue())
            except:
                return None
        elif name == 'bck':
            try:
                return float(self.bck_ctl.GetValue())
            except:
                return None
        elif name == 'q_min':
            try:
                return float(self.qmin_ctl.GetValue())
            except:
                return 0.0
        elif name == 'q_max':
            try:
                return float(self.qmax_ctl.GetValue())
            except:
                return 0.0
        elif name == 'elapsed':
            try:
                return float(self.time_ctl.GetValue())
            except:
                return None
        elif name == 'rg':
            try:
                return float(self.rg_ctl.GetValue())
            except:
                return None
        elif name == 'iq0':
            try:
                return float(self.iq0_ctl.GetValue())
            except:
                return None
        elif name == 'oscillation':
            try:
                return float(self.osc_ctl.GetValue())
            except:
                return None
        elif name == 'slit_width':
            try:
                return float(self.swidth_ctl.GetValue())
            except:
                return None
        elif name == 'slit_height':
            try:
                return float(self.sheight_ctl.GetValue())
            except:
                return None
        elif name == 'pos':
            try:
                return float(self.pos_ctl.GetValue())
            except:
                return None
        elif name == 'pos_err':
            try:
                return float(self.pos_err_ctl.GetValue())
            except:
                return None
        elif name == 'alpha_estimate':
            try:
                return float(self.alpha_estimate_ctl.GetLabel())
            except:
                return None
        elif name == 'nterms_estimate':
            try:
                return int(self.nterms_estimate_ctl.GetLabel())
            except:
                return None
        elif name == 'plotname':
            return self.plot_data.GetValue()
        elif name == 'datafile':
            return self.plot_data.GetValue()
        else:
            return wx.Panel.__getattribute__(self, name)

    def save_project(self, doc=None):
        """
        return an xml node containing state of the panel
         that guiframe can write to file
        """
        data = self.get_data()
        state = self.get_state()
        if data is not None:
            new_doc = self._manager.state_reader.write_toXML(data, state)
            if new_doc is not None:
                if doc is not None and hasattr(doc, "firstChild"):
                    child = new_doc.getElementsByTagName("SASentry")
                    for item in child:
                        doc.firstChild.appendChild(item)
                else:
                    doc = new_doc
        return doc

    def on_save(self, evt=None):
        """
        Method used to create a memento of the current state

        :return: state object
        """
        # Ask the user the location of the file to write to.
        path = None
        if self.parent is not None:
            self._default_save_location = self.parent._default_save_location
        dlg = wx.FileDialog(self, "Choose a file",
                            self._default_save_location,
                            self.window_caption, "*.prv", wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._default_save_location = os.path.dirname(path)
            if self.parent is not None:
                self.parent._default_save_location = self._default_save_location
        else:
            return None

        dlg.Destroy()

        state = self.get_state()

        # MAC always needs the extension for saving
        extens = ".prv"
        # Make sure the ext included in the file name
        fName = os.path.splitext(path)[0] + extens
        self._manager.save_data(filepath=fName, prstate=state)

        return state

    def get_data(self):
        """
        """
        return self._manager.get_data()

    def get_state(self):
        """
        Get the current state

        : return: state object
        """
        # Construct the state object
        state = InversionState()

        # Read the panel's parameters
        flag, alpha, dmax, nfunc, qmin, \
        qmax, height, width, bck = self._read_pars()

        state.nfunc = nfunc
        state.d_max = dmax
        state.alpha = alpha
        state.qmin = qmin
        state.qmax = qmax
        state.width = width
        state.height = height

        # Data file
        state.file = self.plot_data.GetValue()

        # Background evaluation checkbox
        state.estimate_bck = self.est_bck
        state.bck_value = bck

        # Estimates
        state.nterms_estimate = self.nterms_estimate
        state.alpha_estimate = self.alpha_estimate

        # Read the output values
        state.chi2 = self.chi2
        state.elapsed = self.elapsed
        state.osc = self.oscillation
        state.pos = self.pos
        state.pos_err = self.pos_err
        state.rg = self.rg
        state.iq0 = self.iq0
        state.bck = self.bck

        return state

    def set_state(self, state):
        """
        Set the state of the panel and inversion problem to
        the state passed as a parameter.
        Execute the inversion immediately after filling the
        controls.

        :param state: InversionState object
        """
        if state.nfunc is not None:
            self.nfunc = state.nfunc
        if state.d_max is not None:
            self.d_max = state.d_max
        if state.alpha is not None:
            self.alpha = state.alpha
        if state.qmin is not None:
            self.q_min = state.qmin
        if state.qmax is not None:
            self.q_max = state.qmax
        if state.width is not None:
            self.slit_width = state.width
        if state.height is not None:
            self.slit_height = state.height

        # Data file
        self.plot_data.SetValue(str(state.file))

        # Background value
        self.bck_est_ctl.SetValue(state.estimate_bck)
        self.bck_man_ctl.SetValue(not state.estimate_bck)
        if not state.estimate_bck:
            self.bck_input.Enable()
            self.bck_input.SetValue(str(state.bck_value))
        self.est_bck = state.estimate_bck
        self.bck_value = state.bck_value

        # Estimates
        if state.nterms_estimate is not None:
            self.nterms_estimate = state.nterms_estimate
        if state.alpha_estimate is not None:
            self.alpha_estimate = state.alpha_estimate


        # Read the output values
        if state.chi2 is not None:
            self.chi2 = state.chi2
        if state.elapsed is not None:
            self.elapsed = state.elapsed
        if state.osc is not None:
            self.oscillation = state.osc
        if state.pos is not None:
            self.positive = state.pos
        if state.pos_err is not None:
            self.pos_err = state.pos_err
        if state.rg is not None:
            self.rg = state.rg
        if state.iq0 is not None:
            self.iq0 = state.iq0
        if state.bck is not None:
            self.bck = state.bck

        # We have the data available for serialization
        self._set_analysis(True)

        # Perform inversion
        self._on_invert(None)

    def set_manager(self, manager):
        self._manager = manager
        if manager is not None:
            self._set_analysis(False)

    def _do_layout(self):
        vbox = wx.GridBagSizer(0, 0)
        iy_vb = 0

        # ----- I(q) data -----
        databox = wx.StaticBox(self, -1, "I(q) data source")

        boxsizer1 = wx.StaticBoxSizer(databox, wx.VERTICAL)
        boxsizer1.SetMinSize((self._default_width, 50))
        pars_sizer = wx.GridBagSizer(5, 5)

        iy = 0
        self.file_radio = wx.StaticText(self, -1, "Name:")
        pars_sizer.Add(self.file_radio, (iy, 0), (1, 1),
                       wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        self.plot_data = DataFileTextCtrl(self, -1, size=(260, 20))

        pars_sizer.Add(self.plot_data, (iy, 1), (1, 1),
                       wx.EXPAND | wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 15)

        radio_sizer = wx.GridBagSizer(5, 5)

        self.bck_est_ctl = wx.RadioButton(self, -1, "Estimate background level",
            name="estimate_bck", style=wx.RB_GROUP)
        self.bck_man_ctl = wx.RadioButton(self, -1, "Input manual background level",
            name="manual_bck")

        self.bck_est_ctl.Bind(wx.EVT_RADIOBUTTON, self._on_bck_changed)
        self.bck_man_ctl.Bind(wx.EVT_RADIOBUTTON, self._on_bck_changed)

        radio_sizer.Add(self.bck_est_ctl, (0,0), (1,1), wx.LEFT | wx.EXPAND)
        radio_sizer.Add(self.bck_man_ctl, (0,1), (1,1), wx.RIGHT | wx.EXPAND)

        iy += 1
        pars_sizer.Add(radio_sizer, (iy, 0), (1, 2),
                       wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        background_label = wx.StaticText(self, -1, "Background: ")
        self.bck_input = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER,
            size=(60, 20), value="0.0")
        self.bck_input.Disable()
        self.bck_input.Bind(wx.EVT_TEXT, self._read_pars)
        background_units = wx.StaticText(self, -1, "[A^(-1)]", size=(55, 20))
        iy += 1

        background_sizer = wx.GridBagSizer(5, 5)

        background_sizer.Add(background_label, (0, 0), (1,1),
            wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 23)
        background_sizer.Add(self.bck_input, (0, 1), (1,1),
            wx.LEFT | wx.ADJUST_MINSIZE, 5)
        background_sizer.Add(background_units, (0, 2), (1,1),
            wx.LEFT | wx.ADJUST_MINSIZE, 5)
        pars_sizer.Add(background_sizer, (iy, 0), (1, 2),
            wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        boxsizer1.Add(pars_sizer, 0, wx.EXPAND)
        vbox.Add(boxsizer1, (iy_vb, 0), (1, 1),
                 wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE | wx.TOP, 5)

        # ----- Add slit parameters -----
        if True:
            sbox = wx.StaticBox(self, -1, "Slit parameters")
            sboxsizer = wx.StaticBoxSizer(sbox, wx.VERTICAL)
            sboxsizer.SetMinSize((self._default_width, 20))

            sizer_slit = wx.GridBagSizer(5, 5)

            label_sheight = wx.StaticText(self, -1, "Height", size=(40, 20))
            label_swidth = wx.StaticText(self, -1, "Width", size=(40, 20))
            label_sunits2 = wx.StaticText(self, -1, "[A^(-1)]", size=(55, 20))
            self.sheight_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER, size=(60, 20))
            self.swidth_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER, size=(60, 20))
            hint_msg = "Enter slit height in units of Q or leave blank."
            self.sheight_ctl.SetToolTipString(hint_msg)
            hint_msg = "Enter slit width in units of Q or leave blank."
            self.swidth_ctl.SetToolTipString(hint_msg)

            iy = 0
            sizer_slit.Add(label_sheight, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 5)
            sizer_slit.Add(self.sheight_ctl, (iy, 1), (1, 1), wx.LEFT | wx.EXPAND, 5)
            sizer_slit.Add(label_swidth, (iy, 2), (1, 1), wx.LEFT | wx.EXPAND, 5)
            sizer_slit.Add(self.swidth_ctl, (iy, 3), (1, 1), wx.LEFT | wx.EXPAND, 5)
            sizer_slit.Add(label_sunits2, (iy, 4), (1, 1), wx.LEFT | wx.EXPAND, 5)

            sboxsizer.Add(sizer_slit, wx.TOP, 15)
            iy_vb += 1
            vbox.Add(sboxsizer, (iy_vb, 0), (1, 1),
                     wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)

        # ----- Q range -----
        qbox = wx.StaticBox(self, -1, "Q range")
        qboxsizer = wx.StaticBoxSizer(qbox, wx.VERTICAL)
        qboxsizer.SetMinSize((self._default_width, 20))

        sizer_q = wx.GridBagSizer(5, 5)

        label_qmin = wx.StaticText(self, -1, "Q min", size=(40, 20))
        label_qmax = wx.StaticText(self, -1, "Q max", size=(40, 20))
        label_qunits2 = wx.StaticText(self, -1, "[A^(-1)]", size=(55, 20))
        self.qmin_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER, size=(60, 20))
        self.qmax_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER, size=(60, 20))
        hint_msg = "Select a lower bound for Q or leave blank."
        self.qmin_ctl.SetToolTipString(hint_msg)
        hint_msg = "Select an upper bound for Q or leave blank."
        self.qmax_ctl.SetToolTipString(hint_msg)
        self.qmin_ctl.Bind(wx.EVT_TEXT, self._on_pars_changed)
        self.qmax_ctl.Bind(wx.EVT_TEXT, self._on_pars_changed)

        iy = 0
        sizer_q.Add(label_qmin, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 5)
        sizer_q.Add(self.qmin_ctl, (iy, 1), (1, 1), wx.LEFT | wx.EXPAND, 5)
        sizer_q.Add(label_qmax, (iy, 2), (1, 1), wx.LEFT | wx.EXPAND, 5)
        sizer_q.Add(self.qmax_ctl, (iy, 3), (1, 1), wx.LEFT | wx.EXPAND, 5)
        sizer_q.Add(label_qunits2, (iy, 4), (1, 1), wx.LEFT | wx.EXPAND, 5)
        qboxsizer.Add(sizer_q, wx.TOP, 15)

        iy_vb += 1
        vbox.Add(qboxsizer, (iy_vb, 0), (1, 1),
                 wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)

        # ----- Parameters -----
        parsbox = wx.StaticBox(self, -1, "Parameters")
        boxsizer2 = wx.StaticBoxSizer(parsbox, wx.VERTICAL)
        boxsizer2.SetMinSize((self._default_width, 50))

        explanation = "P(r) is found by fitting a set of base functions"
        explanation += " to I(Q). The minimization involves"
        explanation += " a regularization term to ensure a smooth P(r)."
        explanation += " The regularization constant gives the size of that "
        explanation += "term. The suggested value is the value above which the"
        explanation += " output P(r) will have only one peak."
        label_explain = wx.StaticText(self, -1, explanation, size=(280, 90))
        boxsizer2.Add(label_explain, wx.LEFT | wx.BOTTOM, 5)

        label_nfunc = wx.StaticText(self, -1, "Number of terms")
        label_nfunc.SetMinSize((120, 20))
        label_alpha = wx.StaticText(self, -1, "Regularization constant")
        label_dmax = wx.StaticText(self, -1, "Max distance [A]")
        self.label_sugg = wx.StaticText(self, -1, "Suggested value")

        self.nfunc_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER, size=(60, 20))
        self.nfunc_ctl.SetToolTipString("Number of terms in the expansion.")
        self.alpha_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER, size=(60, 20))
        hint_msg = "Control parameter for the size of the regularization term."
        self.alpha_ctl.SetToolTipString(hint_msg)
        self.dmax_ctl = PrTextCtrl(self, -1, style=wx.TE_PROCESS_ENTER, size=(60, 20))
        hint_msg = "Maximum distance between any two points in the system."
        self.dmax_ctl.SetToolTipString(hint_msg)
        wx_id = wx.NewId()
        self.alpha_estimate_ctl = wx.Button(self, wx_id, "")
        self.Bind(wx.EVT_BUTTON, self._on_accept_alpha, id=wx_id)
        self.alpha_estimate_ctl.Enable(False)
        self.alpha_estimate_ctl.SetToolTipString("Waiting for estimate...")

        wx_id = wx.NewId()
        self.nterms_estimate_ctl = wx.Button(self, wx_id, "")
        #self.nterms_estimate_ctl.Hide()
        self.Bind(wx.EVT_BUTTON, self._on_accept_nterms, id=wx_id)
        self.nterms_estimate_ctl.Enable(False)

        self.nterms_estimate_ctl.SetToolTipString("Waiting for estimate...")

        self.nfunc_ctl.Bind(wx.EVT_TEXT, self._read_pars)
        self.alpha_ctl.Bind(wx.EVT_TEXT, self._read_pars)
        self.dmax_ctl.Bind(wx.EVT_TEXT, self._on_pars_changed)

        # Distance explorator
        wx_id = wx.NewId()
        self.distance_explorator_ctl = wx.Button(self, wx_id, "Explore")
        self.Bind(wx.EVT_BUTTON, self._on_explore, id=wx_id)


        sizer_params = wx.GridBagSizer(5, 5)

        iy = 0
        sizer_params.Add(self.label_sugg, (iy, 2), (1, 1), wx.LEFT, 15)
        iy += 1
        sizer_params.Add(label_nfunc, (iy, 0), (1, 1), wx.LEFT, 15)
        sizer_params.Add(self.nfunc_ctl, (iy, 1), (1, 1), wx.RIGHT, 0)
        sizer_params.Add(self.nterms_estimate_ctl, (iy, 2), (1, 1), wx.LEFT, 15)
        iy += 1
        sizer_params.Add(label_alpha, (iy, 0), (1, 1), wx.LEFT, 15)
        sizer_params.Add(self.alpha_ctl, (iy, 1), (1, 1), wx.RIGHT, 0)
        sizer_params.Add(self.alpha_estimate_ctl, (iy, 2), (1, 1), wx.LEFT, 15)
        iy += 1
        sizer_params.Add(label_dmax, (iy, 0), (1, 1), wx.LEFT, 15)
        sizer_params.Add(self.dmax_ctl, (iy, 1), (1, 1), wx.RIGHT, 0)
        sizer_params.Add(self.distance_explorator_ctl, (iy, 2),
                         (1, 1), wx.LEFT, 15)

        boxsizer2.Add(sizer_params, 0)

        iy_vb += 1
        vbox.Add(boxsizer2, (iy_vb, 0), (1, 1),
                 wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)


        # ----- Results -----
        resbox = wx.StaticBox(self, -1, "Outputs")
        ressizer = wx.StaticBoxSizer(resbox, wx.VERTICAL)
        ressizer.SetMinSize((self._default_width, 50))

        label_rg = wx.StaticText(self, -1, "Rg")
        label_rg_unit = wx.StaticText(self, -1, "[A]")
        label_iq0 = wx.StaticText(self, -1, "I(Q=0)")
        label_iq0_unit = wx.StaticText(self, -1, "[A^(-1)]")
        label_bck = wx.StaticText(self, -1, "Background")
        label_bck_unit = wx.StaticText(self, -1, "[A^(-1)]")
        self.rg_ctl = OutputTextCtrl(self, -1, size=(60, 20))
        hint_msg = "Radius of gyration for the computed P(r)."
        self.rg_ctl.SetToolTipString(hint_msg)
        self.iq0_ctl = OutputTextCtrl(self, -1, size=(60, 20))
        hint_msg = "Scattering intensity at Q=0 for the computed P(r)."
        self.iq0_ctl.SetToolTipString(hint_msg)
        self.bck_ctl = OutputTextCtrl(self, -1, size=(60, 20))
        self.bck_ctl.SetToolTipString("Value of estimated constant background.")

        label_time = wx.StaticText(self, -1, "Computation time")
        label_time_unit = wx.StaticText(self, -1, "secs")
        label_time.SetMinSize((120, 20))
        label_chi2 = wx.StaticText(self, -1, "Chi2/dof")
        label_osc = wx.StaticText(self, -1, "Oscillations")
        label_pos = wx.StaticText(self, -1, "Positive fraction")
        label_pos_err = wx.StaticText(self, -1, "1-sigma positive fraction")

        self.time_ctl = OutputTextCtrl(self, -1, size=(60, 20))
        hint_msg = "Computation time for the last inversion, in seconds."
        self.time_ctl.SetToolTipString(hint_msg)

        self.chi2_ctl = OutputTextCtrl(self, -1, size=(60, 20))
        self.chi2_ctl.SetToolTipString("Chi^2 over degrees of freedom.")

        # Oscillation parameter
        self.osc_ctl = OutputTextCtrl(self, -1, size=(60, 20))
        hint_msg = "Oscillation parameter. P(r) for a sphere has an "
        hint_msg += " oscillation parameter of 1.1."
        self.osc_ctl.SetToolTipString(hint_msg)

        # Positive fraction figure of merit
        self.pos_ctl = OutputTextCtrl(self, -1, size=(60, 20))
        hint_msg = "Fraction of P(r) that is positive. "
        hint_msg += "Theoretically, P(r) is defined positive."
        self.pos_ctl.SetToolTipString(hint_msg)

        # 1-simga positive fraction figure of merit
        self.pos_err_ctl = OutputTextCtrl(self, -1, size=(60, 20))
        message = "Fraction of P(r) that is at least 1 standard deviation"
        message += " greater than zero.\n"
        message += "This figure of merit tells you about the size of the "
        message += "P(r) errors.\n"
        message += "If it is close to 1 and the other figures of merit are bad,"
        message += " consider changing the maximum distance."
        self.pos_err_ctl.SetToolTipString(message)

        sizer_res = wx.GridBagSizer(5, 5)

        iy = 0
        sizer_res.Add(label_rg, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
        sizer_res.Add(self.rg_ctl, (iy, 1), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        sizer_res.Add(label_rg_unit, (iy, 2), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        iy += 1
        sizer_res.Add(label_iq0, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
        sizer_res.Add(self.iq0_ctl, (iy, 1), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        sizer_res.Add(label_iq0_unit, (iy, 2), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        iy += 1
        sizer_res.Add(label_bck, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
        sizer_res.Add(self.bck_ctl, (iy, 1), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        sizer_res.Add(label_bck_unit, (iy, 2), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        iy += 1
        sizer_res.Add(label_time, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
        sizer_res.Add(self.time_ctl, (iy, 1), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        sizer_res.Add(label_time_unit, (iy, 2), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        iy += 1
        sizer_res.Add(label_chi2, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
        sizer_res.Add(self.chi2_ctl, (iy, 1), (1, 1), wx.RIGHT | wx.EXPAND, 15)
        iy += 1
        sizer_res.Add(label_osc, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
        sizer_res.Add(self.osc_ctl, (iy, 1), (1, 1), wx.RIGHT | wx.EXPAND, 15)

        iy += 1
        sizer_res.Add(label_pos, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
        sizer_res.Add(self.pos_ctl, (iy, 1), (1, 1), wx.RIGHT | wx.EXPAND, 15)

        iy += 1
        sizer_res.Add(label_pos_err, (iy, 0), (1, 1), wx.LEFT | wx.EXPAND, 15)
        sizer_res.Add(self.pos_err_ctl, (iy, 1), (1, 1), wx.RIGHT | wx.EXPAND, 15)

        ressizer.Add(sizer_res, 0)
        iy_vb += 1
        vbox.Add(ressizer, (iy_vb, 0), (1, 1),
                 wx.LEFT | wx.RIGHT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)

        # ----- Buttons -----
        wx_id = wx.NewId()
        button_ok = wx.Button(self, wx_id, "Compute")
        button_ok.SetToolTipString("Perform P(r) inversion.")
        self.Bind(wx.EVT_BUTTON, self._on_invert, id=wx_id)

        self.button_help = wx.Button(self, -1, "HELP")
        self.button_help.SetToolTipString("Get help on P(r) inversion.")
        self.button_help.Bind(wx.EVT_BUTTON, self.on_help)

        self._set_reset_flag(True)
        self._set_save_flag(True)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_ok, 0, wx.LEFT | wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.button_help, 0, wx.LEFT | wx.ADJUST_MINSIZE, 10)

        iy_vb += 1
        vbox.Add(sizer_button, (iy_vb, 0), (1, 1),
                 wx.EXPAND | wx.BOTTOM | wx.TOP | wx.RIGHT, 10)

        self.Bind(wx.EVT_TEXT_ENTER, self._on_invert)

        self.SetSizer(vbox)

    def _on_accept_alpha(self, evt):
        """
        User has accepted the estimated alpha,
        set it as part of the input parameters
        """
        try:
            alpha = self.alpha_estimate_ctl.GetLabel()
            # Check that we have a number
            float(alpha)
            self.alpha_ctl.SetValue(alpha)
        except ValueError:
            logger.error("InversionControl._on_accept_alpha got a value that was not a number: %s" % alpha )
        except:
            # No estimate or bad estimate, either do nothing
            logger.error("InversionControl._on_accept_alpha: %s" % sys.exc_info()[1])

    def _on_accept_nterms(self, evt):
        """
        User has accepted the estimated number of terms,
        set it as part of the input parameters
        """
        try:
            nterms = self.nterms_estimate_ctl.GetLabel()
            # Check that we have a number
            float(nterms)
            self.nfunc_ctl.SetValue(nterms)
        except ValueError:
            logger.error("InversionControl._on_accept_nterms got a value that was not a number: %s" % nterms )
        except:
            # No estimate or bad estimate, either do nothing
            logger.error("InversionControl._on_accept_nterms: %s" % sys.exc_info()[1])

    def clear_panel(self):
        """
        """
        self.plot_data.SetValue("")
        self.on_reset(event=None)

    def on_reset(self, event=None):
        """
        Resets inversion parameters
        """
        self.nfunc = self._manager.DEFAULT_NFUNC
        self.d_max = self._manager.DEFAULT_DMAX
        self.alpha = self._manager.DEFAULT_ALPHA
        self.qmin_ctl.SetValue("")
        self.qmax_ctl.SetValue("")
        self.time_ctl.SetValue("")
        self.rg_ctl.SetValue("")
        self.iq0_ctl.SetValue("")
        self.bck_ctl.SetValue("")
        self.chi2_ctl.SetValue("")
        self.osc_ctl.SetValue("")
        self.pos_ctl.SetValue("")
        self.pos_err_ctl.SetValue("")
        self.alpha_estimate_ctl.Enable(False)
        self.alpha_estimate_ctl.SetLabel("")
        self.nterms_estimate_ctl.Enable(False)
        self.nterms_estimate_ctl.SetLabel("")
        self._set_analysis(False)

        self._on_pars_changed()

    def _on_bck_changed(self, evt=None):
        self.est_bck = self.bck_est_ctl.GetValue()
        if self.est_bck:
            self.bck_input.Disable()
        else:
            self.bck_input.Enable()

    def _on_pars_changed(self, evt=None):
        """
        Called when an input parameter has changed
        We will estimate the alpha parameter behind the
        scenes.
        """
        flag, alpha, dmax, nfunc, qmin, qmax, height, width, bck = self._read_pars()

        # If the pars are valid, estimate alpha
        if flag:
            self.nterms_estimate_ctl.Enable(False)
            self.alpha_estimate_ctl.Enable(False)

            dataset = self.plot_data.GetValue()
            if dataset is not None and dataset.strip() != "":
                self._manager.estimate_plot_inversion(alpha=alpha, nfunc=nfunc,
                                                      d_max=dmax,
                                                      q_min=qmin, q_max=qmax,
                                                      est_bck=self.est_bck,
                                                      bck_val=bck,
                                                      height=height,
                                                      width=width)

    def _read_pars(self, evt=None):
        """
        """
        alpha = 0
        nfunc = 5
        dmax = 120
        qmin = 0
        qmax = 0
        height = 0
        width = 0
        background = 0
        flag = True
        # Read slit height
        try:
            height_str = self.sheight_ctl.GetValue()
            if len(height_str.lstrip().rstrip()) == 0:
                height = 0
            else:
                height = float(height_str)
                self.sheight_ctl.SetBackgroundColour(wx.WHITE)
                self.sheight_ctl.Refresh()
        except:
            flag = False
            self.sheight_ctl.SetBackgroundColour("pink")
            self.sheight_ctl.Refresh()

        # Read slit width
        try:
            width_str = self.swidth_ctl.GetValue()
            if len(width_str.lstrip().rstrip()) == 0:
                width = 0
            else:
                width = float(width_str)
                self.swidth_ctl.SetBackgroundColour(wx.WHITE)
                self.swidth_ctl.Refresh()
        except:
            flag = False
            self.swidth_ctl.SetBackgroundColour("pink")
            self.swidth_ctl.Refresh()

        # Read alpha
        try:
            alpha = float(self.alpha_ctl.GetValue())
            self.alpha_ctl.SetBackgroundColour(wx.WHITE)
            self.alpha_ctl.Refresh()
        except:
            flag = False
            self.alpha_ctl.SetBackgroundColour("pink")
            self.alpha_ctl.Refresh()

        # Read d_max
        try:
            dmax = float(self.dmax_ctl.GetValue())
            self.dmax_ctl.SetBackgroundColour(wx.WHITE)
            self.dmax_ctl.Refresh()
        except:
            flag = False
            self.dmax_ctl.SetBackgroundColour("pink")
            self.dmax_ctl.Refresh()

        # Read nfunc
        try:
            nfunc = int(self.nfunc_ctl.GetValue())
            npts = self._manager.get_npts()
            if npts > 0 and nfunc > npts:
                message = "Number of function terms should be smaller "
                message += "than the number of points"
                wx.PostEvent(self._manager.parent, StatusEvent(status=message))
                raise ValueError(message)
            self.nfunc_ctl.SetBackgroundColour(wx.WHITE)
            self.nfunc_ctl.Refresh()
        except:
            flag = False
            self.nfunc_ctl.SetBackgroundColour("pink")
            self.nfunc_ctl.Refresh()

        # Read qmin
        try:
            qmin_str = self.qmin_ctl.GetValue()
            if len(qmin_str.lstrip().rstrip()) == 0:
                qmin = None
            else:
                qmin = float(qmin_str)
                self.qmin_ctl.SetBackgroundColour(wx.WHITE)
                self.qmin_ctl.Refresh()
        except:
            flag = False
            self.qmin_ctl.SetBackgroundColour("pink")
            self.qmin_ctl.Refresh()

        # Read qmax
        try:
            qmax_str = self.qmax_ctl.GetValue()
            if len(qmax_str.lstrip().rstrip()) == 0:
                qmax = None
            else:
                qmax = float(qmax_str)
                self.qmax_ctl.SetBackgroundColour(wx.WHITE)
                self.qmax_ctl.Refresh()
        except:
            flag = False
            self.qmax_ctl.SetBackgroundColour("pink")
            self.qmax_ctl.Refresh()

        # Read background
        if not self.est_bck:
            try:
                bck_str = self.bck_input.GetValue()
                if len(bck_str.strip()) == 0:
                    background = 0.0
                else:
                    background = float(bck_str)
                    self.bck_input.SetBackgroundColour(wx.WHITE)
            except ValueError:
                background = 0.0
                self.bck_input.SetBackgroundColour("pink")
            self.bck_input.Refresh()

        return flag, alpha, dmax, nfunc, qmin, qmax, height, width, background

    def _on_explore(self, evt):
        """
        Invoke the d_max exploration dialog
        """
        from .explore_dialog import ExploreDialog
        if self._manager._last_pr is not None:
            pr = self._manager._create_plot_pr()
            dialog = ExploreDialog(pr, 10, None, -1, "")
            dialog.Show()
        else:
            message = "No data to analyze. Please load a data set to proceed."
            wx.PostEvent(self._manager.parent, StatusEvent(status=message))

    def _on_invert(self, evt):
        """
        Perform inversion

        :param silent: when True, there will be no output for the user

        """
        # Get the data from the form
        # Push it to the manager

        flag, alpha, dmax, nfunc, qmin, qmax, height, width, bck = self._read_pars()

        if flag:
            dataset = self.plot_data.GetValue()
            if dataset is None or len(dataset.strip()) == 0:
                message = "No data to invert. Select a data set before"
                message += " proceeding with P(r) inversion."
                wx.PostEvent(self._manager.parent, StatusEvent(status=message))
            else:
                self._manager.setup_plot_inversion(alpha=alpha, nfunc=nfunc,
                                                   d_max=dmax,
                                                   q_min=qmin, q_max=qmax,
                                                   est_bck=self.est_bck,
                                                   bck_val = bck,
                                                   height=height,
                                                   width=width)
        else:
            message = "The P(r) form contains invalid values: "
            message += "please submit it again."
            wx.PostEvent(self.parent, StatusEvent(status=message))

    def _change_file(self, evt=None, filepath=None, data=None):
        """
        Choose a new input file for I(q)
        """
        if self._manager is not None:
            self.plot_data.SetValue(str(data.name))
            try:
                self._manager.show_data(data=data, reset=True)
                self._on_pars_changed(None)
                self._on_invert(None)
                self._set_analysis(True)
            except:
                msg = "InversionControl._change_file: %s" % sys.exc_info()[1]
                logger.error(msg)

    def on_help(self, event):
        """
        Bring up the P(r) Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param evt: Triggers on clicking the help button
    """

        _TreeLocation = "user/sasgui/perspectives/pr/pr_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "P(r) Help")


class PrDistDialog(wx.Dialog):
    """
    Property dialog to let the user change the number
    of points on the P(r) plot.
    """
    def __init__(self, parent, id):
        from sas.sascalc.pr.invertor import help
        wx.Dialog.__init__(self, parent, id, size=(250, 120))
        self.SetTitle("P(r) distribution")


        vbox = wx.BoxSizer(wx.VERTICAL)

        label_npts = wx.StaticText(self, -1, "Number of points")
        self.npts_ctl = PrTextCtrl(self, -1, size=(100, 20))

        pars_sizer = wx.GridBagSizer(5, 5)
        iy = 0
        pars_sizer.Add(label_npts, (iy, 0), (1, 1), wx.LEFT, 15)
        pars_sizer.Add(self.npts_ctl, (iy, 1), (1, 1), wx.RIGHT, 0)

        vbox.Add(pars_sizer, 0, wx.ALL | wx.EXPAND, 15)

        static_line = wx.StaticLine(self, -1)
        vbox.Add(static_line, 0, wx.EXPAND, 0)

        button_ok = wx.Button(self, wx.ID_OK, "OK")
        self.Bind(wx.EVT_BUTTON, self._checkValues, button_ok)
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")

        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        sizer_button.Add((20, 20), 1, wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        sizer_button.Add(button_ok, 0, wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(button_cancel, 0,
                         wx.LEFT | wx.RIGHT | wx.ADJUST_MINSIZE, 10)
        vbox.Add(sizer_button, 0, wx.EXPAND | wx.BOTTOM | wx.TOP, 10)

        self.SetSizer(vbox)
        self.SetAutoLayout(True)

        self.Layout()
        self.Centre()

    def _checkValues(self, event):
        """
        Check the dialog content.
        """
        flag = True
        try:
            int(self.npts_ctl.GetValue())
            self.npts_ctl.SetBackgroundColour(wx.WHITE)
            self.npts_ctl.Refresh()
        except:
            flag = False
            self.npts_ctl.SetBackgroundColour("pink")
            self.npts_ctl.Refresh()
        if flag:
            event.Skip(True)

    def get_content(self):
        """
        Return the content of the dialog.
        At this point the values have already been
        checked.
        """
        value = int(self.npts_ctl.GetValue())
        return value

    def set_content(self, npts):
        """
        Initialize the content of the dialog.
        """
        self.npts_ctl.SetValue("%i" % npts)
