"""
    FitPanel class contains fields allowing to display results when
    fitting  a model and one data
"""
import sys
import wx
import wx.lib.newevent
import numpy as np
import copy
import math
import time
import traceback

from sasmodels.weights import MODELS as POLYDISPERSITY_MODELS

from sas.sascalc.fit.qsmearing import smear_selection

from sas.sasgui.guiframe.events import StatusEvent, NewPlotEvent, \
    PlotQrangeEvent
from sas.sasgui.guiframe.dataFitting import check_data_validity
from sas.sasgui.guiframe.utils import format_number, check_float
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

from sas.sasgui.perspectives.fitting.basepage import BasicPage as BasicPage
from sas.sasgui.perspectives.fitting.basepage import PageInfoEvent as \
    PageInfoEvent
from .basepage import ModelTextCtrl

(Chi2UpdateEvent, EVT_CHI2_UPDATE) = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 76
_DATA_BOX_WIDTH = 300
SMEAR_SIZE_H = 0.00
CUSTOM_MODEL = 'Plugin Models'

class FitPage(BasicPage):
    """
    FitPanel class contains fields allowing to display results when
    fitting  a model and one data

    :note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.
    """

    def __init__(self, parent, color=None):
        """
        Initialization of the Panel
        """
        BasicPage.__init__(self, parent, color=color)

        # draw sizer
        self._fill_data_sizer()
        self.is_2D = None
        self.fit_started = False
        self.weightbt_string = None
        self.m_name = None
        # get smear info from data
        self._get_smear_info()
        self._fill_model_sizer(self.sizer1)
        self._get_defult_custom_smear()
        self._fill_range_sizer()
        self._set_smear(self.data)
        self.Bind(EVT_CHI2_UPDATE, self.on_complete_chisqr)
        # bind key event
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        self._set_bookmark_flag(False)
        self._set_save_flag(False)
        self._set_preview_flag(False)
        self._set_copy_flag(False)
        self._set_paste_flag(False)
        self.btFit.SetFocus()
        self.enable_fit_button()
        self.fill_data_combobox(data_list=self.data_list)
        # create a default data for an empty panel
        self.create_default_data()
        self._manager.frame.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)

    def enable_fit_button(self):
        """
        Enable fit button if data is valid and model is valid
        """
        flag = check_data_validity(self.data) & (self.model is not None)
        self.btFit.Enable(flag)

    def on_set_focus(self, event):
        """
        Override the basepage focus method to ensure the save flag is set
        properly when focusing on the fit page.
        """
        flag = check_data_validity(self.data) & (self.model is not None)
        self._set_save_flag(flag)
        self.parent.on_set_focus(event)
        self.on_tap_focus()

    def _fill_data_sizer(self):
        """
        fill sizer 0 with data info
        """
        self.data_box_description = wx.StaticBox(self, wx.ID_ANY,
                                                 'I(q) Data Source')
        if check_data_validity(self.data):
            dname_color = wx.BLUE
        else:
            dname_color = wx.RED
        self.data_box_description.SetForegroundColour(dname_color)
        boxsizer1 = wx.StaticBoxSizer(self.data_box_description, wx.VERTICAL)
        # ----------------------------------------------------------
        sizer_data = wx.BoxSizer(wx.HORIZONTAL)
        self.dataSource = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.dataSource, wx.ID_ANY, self.on_select_data)
        self.dataSource.SetMinSize((_DATA_BOX_WIDTH, -1))
        sizer_data.Add(wx.StaticText(self, wx.ID_ANY, 'Name : '))
        sizer_data.Add(self.dataSource)
        sizer_data.Add((0, 5))
        boxsizer1.Add(sizer_data, 0, wx.ALL, 10)
        self.sizer0.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)
        self.sizer0.Layout()

    def enable_datasource(self):
        """
        Enable or disable data source control depending on existing data
        """
        if not self.data_list:
            self.dataSource.Disable()
        else:
            self.dataSource.Enable()

    def fill_data_combobox(self, data_list):
        """
        Get a list of data and fill the corresponding combobox
        """
        self.dataSource.Clear()
        self.data_list = data_list
        self.enable_datasource()
        if len(data_list) > 0:
            # find the maximum range covering all data
            qmin, qmax, npts = self.compute_data_set_range(data_list)
            self.qmin_data_set = qmin
            self.qmax_data_set = qmax
            self.npts_data_set = npts

            self.qmin.SetValue(str(self.qmin_data_set))
            self.qmax.SetValue(str(self.qmax_data_set))
            self.qmin.SetBackgroundColour("white")
            self.qmax.SetBackgroundColour("white")
            self.qmin_x = self.qmin_data_set
            self.qmax_x = self.qmax_data_set
            self.state.qmin = self.qmin_x
            self.state.qmax = self.qmax_x
        is_data = False
        for data in self.data_list:
            if data is not None:
                self.dataSource.Append(str(data.name), clientData=data)
                if not is_data:
                    is_data = check_data_validity(data)
        if is_data:
            self.dataSource.SetSelection(0)
            self.on_select_data(event=None)

        if len(data_list) == 1:
            self.dataSource.Disable()

    def on_select_data(self, event=None):
        """
        On_select_data
        """
        if self.dataSource.GetCount() > 0:
            pos = self.dataSource.GetSelection() if event is not None else 0
            data = self.dataSource.GetClientData(pos)
            self.set_data(data)

    def _on_fit_complete(self):
        """
        When fit is complete ,reset the fit button label.
        """
        self.fit_started = False
        self.set_fitbutton()

    def _is_2D(self):
        """
        Check if data_name is Data2D

        :return: True or False
        """
        if self.data.__class__.__name__ == "Data2D" or \
                        self.enable2D:
            return True
        return False

    def _fill_range_sizer(self):
        """
        Fill the Fitting sizer on the fit panel which contains: the smearing
        information (dq), the weighting information (dI or other), the plotting
        range, access to the 2D mask editor, the compute, fit, and help
        buttons, xi^2, number of points etc.
        """
        is_2d_data = False

        # Check if data is 2D
        if self.data.__class__.__name__ == "Data2D" or \
                        self.enable2D:
            is_2d_data = True

        title = "Fitting"
        # smear messages & titles
        smear_message_none = "No smearing is selected..."
        smear_message_dqdata = "The dQ data is being used for smearing..."
        smear_message_2d = \
              "Higher accuracy is very time-expensive. Use it with care..."
        smear_message_new_ssmear = \
              "Please enter only the value of interest to customize smearing..."
        smear_message_new_psmear = \
              "Please enter a fixed percentage to be applied to all Q values..."
        smear_message_2d_x_title = "<dQp>[1/A]:"
        smear_message_2d_y_title = "<dQs>[1/A]:"
        smear_message_pinhole_percent_title = "dQ[%]:"
        smear_message_slit_height_title = "Slit height[1/A]:"
        smear_message_slit_width_title = "Slit width[1/A]:"

        self._get_smear_info()

        # Sizers
        box_description_range = wx.StaticBox(self, wx.ID_ANY, str(title))
        box_description_range.SetForegroundColour(wx.BLUE)
        boxsizer_range = wx.StaticBoxSizer(box_description_range, wx.VERTICAL)
        self.sizer_set_smearer = wx.BoxSizer(wx.VERTICAL)
        sizer_smearer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_new_smear = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_set_masking = wx.BoxSizer(wx.HORIZONTAL)
        sizer_chi2 = wx.BoxSizer(wx.VERTICAL)
        smear_set_box = wx.StaticBox(self, wx.ID_ANY,
                                     'Set Instrumental Smearing')
        sizer_smearer_box = wx.StaticBoxSizer(smear_set_box, wx.HORIZONTAL)
        sizer_smearer_box.SetMinSize((_DATA_BOX_WIDTH, 60))

        weighting_set_box = wx.StaticBox(self, wx.ID_ANY,
                                         'Set Weighting by Selecting dI Source')
        weighting_box = wx.StaticBoxSizer(weighting_set_box, wx.HORIZONTAL)
        sizer_weighting = wx.BoxSizer(wx.HORIZONTAL)
        weighting_box.SetMinSize((_DATA_BOX_WIDTH, 40))
        # Filling the sizer containing weighting info.
        self.dI_noweight = wx.RadioButton(self, wx.ID_ANY,
                                          'No Weighting', style=wx.RB_GROUP)
        self.dI_didata = wx.RadioButton(self, wx.ID_ANY, 'Use dI Data')
        self.dI_sqrdata = wx.RadioButton(self, wx.ID_ANY, 'Use |sqrt(I Data)|')
        self.dI_idata = wx.RadioButton(self, wx.ID_ANY, 'Use |I Data|')
        self.Bind(wx.EVT_RADIOBUTTON, self.onWeighting,
                  id=self.dI_noweight.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onWeighting,
                  id=self.dI_didata.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onWeighting,
                  id=self.dI_sqrdata.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onWeighting,
                  id=self.dI_idata.GetId())
        self.dI_noweight.SetValue(True)
        # add 4 types of weighting to the sizer
        sizer_weighting.Add(self.dI_noweight, 0, wx.LEFT, 10)
        sizer_weighting.Add((14, 10))
        sizer_weighting.Add(self.dI_didata)
        sizer_weighting.Add((14, 10))
        sizer_weighting.Add(self.dI_sqrdata)
        sizer_weighting.Add((14, 10))
        sizer_weighting.Add(self.dI_idata)
        sizer_weighting.Add((10, 10))
        self.dI_noweight.Enable(True)
        self.dI_didata.Enable(False)
        self.dI_sqrdata.Enable(False)
        self.dI_idata.Enable(False)
        weighting_box.Add(sizer_weighting)

        # combobox for smear2d accuracy selection
        self.smear_accuracy = wx.ComboBox(self, wx.ID_ANY,
                                          size=(50, -1), style=wx.CB_READONLY)
        self._set_accuracy_list()
        self.smear_accuracy.SetValue(self.smear2d_accuracy)
        self.smear_accuracy.SetSelection(0)
        self.smear_accuracy.SetToolTipString(
            "'Higher' uses more Gaussian points for smearing computation.")

        wx.EVT_COMBOBOX(self.smear_accuracy, wx.ID_ANY,
                        self._on_select_accuracy)

        # Fit button
        self.btFit = wx.Button(self, next(self._ids), 'Fit')
        self.default_bt_colour = self.btFit.GetDefaultAttributes()
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit, id=self.btFit.GetId())
        self.btFit.SetToolTipString("Start fitting.")

        # General Help button
        self.btFitHelp = wx.Button(self, wx.ID_ANY, 'Help')
        self.btFitHelp.SetToolTipString("General fitting help.")
        self.btFitHelp.Bind(wx.EVT_BUTTON, self._onFitHelp)

        # Resolution Smearing Help button (for now use same technique as
        # used for dI help to get tiniest possible button that works
        # both on MAC and PC.  Should completely rewrite the fitting sizer
        # in future.  This is minimum to get out release 3.1
        #        comment June 14, 2015     --- PDB
        if sys.platform.count("win32") > 0:
            size_q = (20, 15)  # on PC
        else:
            size_q = (30, 20)  # on MAC
        self.btSmearHelp = wx.Button(self, wx.ID_ANY, '?',
                                     style=wx.BU_EXACTFIT, size=size_q)
        self.btSmearHelp.SetToolTipString("Resolution smearing help.")
        self.btSmearHelp.Bind(wx.EVT_BUTTON, self._onSmearHelp)

        # textcntrl for custom resolution
        self.smear_pinhole_percent = ModelTextCtrl(self, wx.ID_ANY,
                                                   size=(_BOX_WIDTH - 25, 20),
                                                   style=wx.TE_PROCESS_ENTER,
                                                   text_enter_callback=
                                                   self.onPinholeSmear)
        self.smear_slit_height = ModelTextCtrl(self, wx.ID_ANY,
                            size=(_BOX_WIDTH - 25, 20),
                            style=wx.TE_PROCESS_ENTER,
                            text_enter_callback=self.onSlitSmear)
        self.smear_slit_width = ModelTextCtrl(self, wx.ID_ANY,
                            size=(_BOX_WIDTH - 25, 20),
                            style=wx.TE_PROCESS_ENTER,
                            text_enter_callback=self.onSlitSmear)

        # smear
        self.smear_data_left = BGTextCtrl(self, wx.ID_ANY,
                                          size=(_BOX_WIDTH - 25, 20), style=0)
        self.smear_data_left.SetValue(str(self.dq_l))
        self.smear_data_right = BGTextCtrl(self, wx.ID_ANY,
                                           size=(_BOX_WIDTH - 25, 20), style=0)
        self.smear_data_right.SetValue(str(self.dq_r))

        # set default values for smear
        self.smear_pinhole_percent.SetValue(str(self.dx_percent))
        self.smear_slit_height.SetValue(str(self.dxl))
        self.smear_slit_width.SetValue(str(self.dxw))

        # Filling the sizer containing instruments smearing info.
        self.disable_smearer = wx.RadioButton(self, wx.ID_ANY,
                                              'None', style=wx.RB_GROUP)
        self.enable_smearer = wx.RadioButton(self, wx.ID_ANY, 'Use dQ Data')
        # self.enable_smearer.SetToolTipString(
        # "Click to use the loaded dQ data for smearing.")
        self.pinhole_smearer = wx.RadioButton(self, wx.ID_ANY,
                                              'Custom Pinhole Smear')
        # self.pinhole_smearer.SetToolTipString
        # ("Click to input custom resolution for pinhole smearing.")
        self.slit_smearer = wx.RadioButton(self, wx.ID_ANY, 'Custom Slit Smear')
        # self.slit_smearer.SetToolTipString
        # ("Click to input custom resolution for slit smearing.")
        self.Bind(wx.EVT_RADIOBUTTON, self.onSmear,
                  id=self.disable_smearer.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSmear,
                  id=self.enable_smearer.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onPinholeSmear,
                  id=self.pinhole_smearer.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSlitSmear,
                  id=self.slit_smearer.GetId())
        self.disable_smearer.SetValue(True)

        sizer_smearer.Add(self.disable_smearer, 0, wx.LEFT, 10)
        sizer_smearer.Add(self.enable_smearer)
        sizer_smearer.Add(self.pinhole_smearer)
        sizer_smearer.Add(self.slit_smearer)
        sizer_smearer.Add(self.btSmearHelp)
        sizer_smearer.Add((10, 10))

        # StaticText for chi2, N(for fitting), Npts + Log/linear spacing
        self.tcChi = BGTextCtrl(self, wx.ID_ANY, "-", size=(75, 20), style=0)
        self.tcChi.SetToolTipString("Chi2/Npts(Fit)")
        self.Npts_fit = BGTextCtrl(self, wx.ID_ANY, "-", size=(75, 20), style=0)
        self.Npts_fit.SetToolTipString(
            " Npts : number of points selected for fitting")
        self.Npts_total = ModelTextCtrl(self, wx.ID_ANY, size=(_BOX_WIDTH, 20),
                                        style=wx.TE_PROCESS_ENTER,
                                        text_enter_callback=self._onQrangeEnter)
        self.Npts_total.SetValue(format_number(self.npts_x))
        self.Npts_total.SetToolTipString(
            " Total Npts : total number of data points")

        # Update and Draw button
        self.draw_button = wx.Button(self, next(self._ids), 'Compute')
        self.draw_button.Bind(wx.EVT_BUTTON,
                              self._onDraw, id=self.draw_button.GetId())
        self.draw_button.SetToolTipString("Compute and Draw.")

        self.points_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.pointsbox = wx.CheckBox(self, wx.ID_ANY, 'Log?', (10, 10))
        self.pointsbox.SetValue(False)
        self.pointsbox.SetToolTipString("Check mark to use log spaced points")
        wx.EVT_CHECKBOX(self, self.pointsbox.GetId(), self.select_log)

        self.points_sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Npts    '))
        self.points_sizer.Add(self.pointsbox)

        box_description_1 = wx.StaticText(self, wx.ID_ANY, '   Chi2/Npts')
        box_description_2 = wx.StaticText(self, wx.ID_ANY, 'Npts(Fit)')

        # StaticText for smear
        self.smear_description_none = wx.StaticText(self, wx.ID_ANY,
                                    smear_message_none, style=wx.ALIGN_LEFT)
        self.smear_description_dqdata = wx.StaticText(self, wx.ID_ANY,
                                 smear_message_dqdata, style=wx.ALIGN_LEFT)
        self.smear_description_type = wx.StaticText(self, wx.ID_ANY,
                                    "Type:", style=wx.ALIGN_LEFT)
        self.smear_description_accuracy_type = wx.StaticText(self, wx.ID_ANY,
                                    "Accuracy:", style=wx.ALIGN_LEFT)
        self.smear_description_smear_type = BGTextCtrl(self, wx.ID_ANY,
                                                       size=(57, 20), style=0)
        self.smear_description_smear_type.SetValue(str(self.dq_l))
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())
        self.smear_description_2d = wx.StaticText(self, wx.ID_ANY,
                                    smear_message_2d, style=wx.ALIGN_LEFT)
        self.smear_message_new_s = wx.StaticText(self, wx.ID_ANY,
                         smear_message_new_ssmear, style=wx.ALIGN_LEFT)
        self.smear_message_new_p = wx.StaticText(self, wx.ID_ANY,
                            smear_message_new_psmear, style=wx.ALIGN_LEFT)
        self.smear_description_2d_x = wx.StaticText(self, wx.ID_ANY,
                            smear_message_2d_x_title, style=wx.ALIGN_LEFT)
        self.smear_description_2d_x.SetToolTipString(
                                        "  dQp(parallel) in q_r direction.")
        self.smear_description_2d_y = wx.StaticText(self, wx.ID_ANY,
                            smear_message_2d_y_title, style=wx.ALIGN_LEFT)
        self.smear_description_2d_y.SetToolTipString(
                                    " dQs(perpendicular) in q_phi direction.")
        self.smear_description_pin_percent = wx.StaticText(self, wx.ID_ANY,
                                            smear_message_pinhole_percent_title,
                                            style=wx.ALIGN_LEFT)
        self.smear_description_slit_height = wx.StaticText(self, wx.ID_ANY,
                        smear_message_slit_height_title, style=wx.ALIGN_LEFT)
        self.smear_description_slit_width = wx.StaticText(self, wx.ID_ANY,
                        smear_message_slit_width_title, style=wx.ALIGN_LEFT)

        # arrange sizers
        self.sizer_set_smearer.Add(sizer_smearer)
        self.sizer_set_smearer.Add((10, 10))
        self.sizer_set_smearer.Add(self.smear_description_none,
                                   0, wx.CENTER, 10)
        self.sizer_set_smearer.Add(self.smear_description_dqdata,
                                   0, wx.CENTER, 10)
        self.sizer_set_smearer.Add(self.smear_description_2d,
                                   0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_description_type,
                                 0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_description_accuracy_type,
                                 0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_accuracy)
        self.sizer_new_smear.Add(self.smear_description_smear_type,
                                 0, wx.CENTER, 10)
        self.sizer_new_smear.Add((15, -1))
        self.sizer_new_smear.Add(self.smear_description_2d_x, 0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_description_slit_height,
                                 0, wx.CENTER, 10)

        self.sizer_new_smear.Add(self.smear_slit_height, 0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_data_left, 0, wx.CENTER, 10)
        self.sizer_new_smear.Add((20, -1))
        self.sizer_new_smear.Add(self.smear_description_2d_y,
                                 0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_description_pin_percent,
                                 0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_description_slit_width,
                                 0, wx.CENTER, 10)

        self.sizer_new_smear.Add(self.smear_pinhole_percent, 0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_slit_width, 0, wx.CENTER, 10)
        self.sizer_new_smear.Add(self.smear_data_right, 0, wx.CENTER, 10)

        self.sizer_set_smearer.Add(self.smear_message_new_s, 0, wx.CENTER, 10)
        self.sizer_set_smearer.Add(self.smear_message_new_p, 0, wx.CENTER, 10)
        self.sizer_set_smearer.Add((5, 2))
        self.sizer_set_smearer.Add(self.sizer_new_smear, 0, wx.CENTER, 10)

        # add all to chi2 sizer
        sizer_smearer_box.Add(self.sizer_set_smearer)
        sizer_chi2.Add(sizer_smearer_box)
        sizer_chi2.Add((-1, 5))
        sizer_chi2.Add(weighting_box)
        sizer_chi2.Add((-1, 5))

        # hide all smear messages and textctrl
        self._hide_all_smear_info()

        # get smear_selection
        self.current_smearer = smear_selection(self.data, self.model)

        # Show only the relevant smear messages, etc
        if self.current_smearer is None:
            if not is_2d_data:
                self.smear_description_none.Show(True)
                self.enable_smearer.Disable()
            else:
                self.smear_description_none.Show(True)
                self.slit_smearer.Disable()
            if self.data is None:
                self.slit_smearer.Disable()
                self.pinhole_smearer.Disable()
                self.enable_smearer.Disable()
        else:
            self._show_smear_sizer()
        boxsizer_range.Add(self.sizer_set_masking)
        # 2D data? default
        is_2d_data = False

        # check if it is 2D data
        if self.data.__class__.__name__ == "Data2D" or self.enable2D:
            is_2d_data = True

        self.sizer5.Clear(True)

        self.qmin = ModelTextCtrl(self, wx.ID_ANY, size=(_BOX_WIDTH, 20),
                                  style=wx.TE_PROCESS_ENTER,
                                  set_focus_callback=self.qrang_set_focus,
                                  text_enter_callback=self._onQrangeEnter,
                                  name='qmin')
        self.qmin.SetValue(str(self.qmin_x))
        q_tip = "Click outside of the axes\n to remove the lines."
        qmin_tip = "Minimun value of Q.\n"
        qmin_tip += q_tip
        self.qmin.SetToolTipString(qmin_tip)

        self.qmax = ModelTextCtrl(self, wx.ID_ANY, size=(_BOX_WIDTH, 20),
                                  style=wx.TE_PROCESS_ENTER,
                                  set_focus_callback=self.qrang_set_focus,
                                  text_enter_callback=self._onQrangeEnter,
                                  name='qmax')
        self.qmax.SetValue(str(self.qmax_x))
        qmax_tip = "Maximum value of Q.\n"
        qmax_tip += q_tip
        self.qmax.SetToolTipString(qmax_tip)
        self.qmin.Bind(wx.EVT_MOUSE_EVENTS, self.qrange_click)
        self.qmax.Bind(wx.EVT_MOUSE_EVENTS, self.qrange_click)
        self.qmin.Bind(wx.EVT_KEY_DOWN, self.on_key)
        self.qmax.Bind(wx.EVT_KEY_DOWN, self.on_key)
        self.qmin.Bind(wx.EVT_TEXT, self.on_qrange_text)
        self.qmax.Bind(wx.EVT_TEXT, self.on_qrange_text)
        wx_id = next(self._ids)
        self.reset_qrange = wx.Button(self, wx_id, 'Reset')

        self.reset_qrange.Bind(wx.EVT_BUTTON, self.on_reset_clicked, id=wx_id)
        self.reset_qrange.SetToolTipString("Reset Q range to the default")

        sizer = wx.GridSizer(5, 5, 2, 6)

        self.btEditMask = wx.Button(self, next(self._ids), 'Editor')
        self.btEditMask.Bind(wx.EVT_BUTTON, self._onMask,
                             id=self.btEditMask.GetId())
        self.btEditMask.SetToolTipString("Edit Mask.")
        self.EditMask_title = wx.StaticText(self, wx.ID_ANY, ' Masking(2D)')

        sizer.Add(wx.StaticText(self, wx.ID_ANY, '   Q range'))
        sizer.Add(wx.StaticText(self, wx.ID_ANY, ' Min[1/A]'))
        sizer.Add(wx.StaticText(self, wx.ID_ANY, ' Max[1/A]'))
        sizer.Add(self.EditMask_title)
        sizer.Add((-1, 5))

        sizer.Add(self.reset_qrange)
        sizer.Add(self.qmin)
        sizer.Add(self.qmax)
        sizer.Add(self.btEditMask)
        sizer.Add((-1, 5))

        sizer.AddMany(5*[(-1, 5)])

        sizer.Add(box_description_1, 0, 0)
        sizer.Add(box_description_2, 0, 0)
        sizer.Add(self.points_sizer, 0, 0)
        sizer.Add(self.draw_button, 0, 0)
        sizer.Add((-1, 5))

        sizer.Add(self.tcChi, 0, 0)
        sizer.Add(self.Npts_fit, 0, 0)
        sizer.Add(self.Npts_total, 0, 0)
        sizer.Add(self.btFit, 0, 0)
        sizer.Add(self.btFitHelp, 0, 0)

        boxsizer_range.Add(sizer_chi2)
        boxsizer_range.Add(sizer)
        if is_2d_data:
            self.btEditMask.Enable()
            self.EditMask_title.Enable()
        else:
            self.btEditMask.Disable()
            self.EditMask_title.Disable()
        # save state
        self.save_current_state()
        self.sizer5.Add(boxsizer_range, 0, wx.EXPAND | wx.ALL, 10)
        self.sizer5.Layout()

    def _set_sizer_dispersion(self):
        """
        draw sizer with gaussian dispersity parameters
        """
        self.fittable_param = []
        self.fixed_param = []
        self.orientation_params_disp = []

        self.sizer4_4.Clear(True)
        if self.model is None:
            # no model is selected
            return
        if not self.enable_disp.GetValue():
            # the user didn't select dispersity display
            return

        self._reset_dispersity()

        # fill a sizer with the combobox to select dispersion type
        model_disp = wx.StaticText(self, wx.ID_ANY, 'Function')
        CHECK_STATE = False

        ix = 0
        iy = 0
        disp = wx.StaticText(self, wx.ID_ANY, ' ')
        self.sizer4_4.Add(disp, (iy, ix), (1, 1),
                          wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 1
        values = wx.StaticText(self, wx.ID_ANY, 'PD[ratio]')
        polytext = "Polydispersity (= STD/mean); "
        polytext += "the standard deviation over the mean value."
        values.SetToolTipString(polytext)

        self.sizer4_4.Add(values, (iy, ix), (1, 1),
                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 2
        if self.is_mac:
            err_text = 'Error'
        else:
            err_text = ''
        self.text_disp_1 = wx.StaticText(self, wx.ID_ANY, err_text)
        self.sizer4_4.Add(self.text_disp_1, (iy, ix), (1, 1),
                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        ix += 1
        self.text_disp_min = wx.StaticText(self, wx.ID_ANY, 'Min')
        self.sizer4_4.Add(self.text_disp_min, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        ix += 1
        self.text_disp_max = wx.StaticText(self, wx.ID_ANY, 'Max')
        self.sizer4_4.Add(self.text_disp_max, (iy, ix), (1, 1),
                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        ix += 1
        npts = wx.StaticText(self, wx.ID_ANY, 'Npts')
        npts.SetToolTipString("Number of sampling points for the numerical\n\
        integration over the distribution function.")
        self.sizer4_4.Add(npts, (iy, ix), (1, 1),
                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        nsigmas = wx.StaticText(self, wx.ID_ANY, 'Nsigs')
        nsigmas.SetToolTipString("Number of sigmas between which the range\n\
         of the distribution function will be used for weighting. \n\
        The value '3' covers 99.5% for Gaussian distribution \n\
        function. Note: Not recommended to change this value.")
        self.sizer4_4.Add(nsigmas, (iy, ix), (1, 1),
                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer4_4.Add(model_disp, (iy, ix), (1, 1),
                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

        self.text_disp_max.Show(True)
        self.text_disp_min.Show(True)

        for item in list(self.model.dispersion.keys()):
            if not self.magnetic_on:
                if item in self.model.magnetic_params:
                    continue
            if item not in self.model.orientation_params:
                if item not in self.disp_cb_dict:
                    self.disp_cb_dict[item] = None
                name0 = "Distribution of " + item
                name1 = item + ".width"
                name2 = item + ".npts"
                name3 = item + ".nsigmas"
                if name1 not in self.model.details:
                    self.model.details[name1] = ["", None, None]

                iy += 1
                for p in list(self.model.dispersion[item].keys()):

                    if p == "width":
                        ix = 0
                        cb = wx.CheckBox(self, wx.ID_ANY, name0, (10, 10))
                        cb.SetValue(CHECK_STATE)
                        cb.SetToolTipString("Check mark to fit")
                        wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                        self.sizer4_4.Add(cb, (iy, ix), (1, 1),
                                wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)
                        ix = 1
                        value = self.model.getParam(name1)
                        ctl1 = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 1.3, 20),
                                             style=wx.TE_PROCESS_ENTER)
                        ctl1.SetLabel('PD[ratio]')
                        poly_text = "Polydispersity (STD/mean) of %s\n" % item
                        poly_text += "STD: the standard deviation"
                        poly_text += " from the mean value."
                        ctl1.SetToolTipString(poly_text)
                        ctl1.SetValue(str(format_number(value, True)))
                        self.sizer4_4.Add(ctl1, (iy, ix), (1, 1), wx.EXPAND)
                        # text to show error sign
                        ix = 2
                        text2 = wx.StaticText(self, wx.ID_ANY, '+/-')
                        self.sizer4_4.Add(text2, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                        if not self.is_mac:
                            text2.Hide()

                        ix = 3
                        ctl2 = wx.TextCtrl(self, wx.ID_ANY,
                                           size=(_BOX_WIDTH / 1.3, 20),
                                           style=0)

                        self.sizer4_4.Add(ctl2, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                        if not self.is_mac:
                            ctl2.Hide()

                        ix = 4
                        ctl3 = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 2, 20),
                                             style=wx.TE_PROCESS_ENTER,
                            text_enter_callback=self._onparamRangeEnter)

                        self.sizer4_4.Add(ctl3, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                        ix = 5
                        ctl4 = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 2, 20),
                                             style=wx.TE_PROCESS_ENTER,
                            text_enter_callback=self._onparamRangeEnter)

                        self.sizer4_4.Add(ctl4, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                        ctl3.Show(True)
                        ctl4.Show(True)

                    elif p == "npts":
                        ix = 6
                        value = self.model.getParam(name2)
                        Tctl = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 2.2, 20),
                                             style=wx.TE_PROCESS_ENTER)

                        Tctl.SetValue(str(format_number(value)))
                        self.sizer4_4.Add(Tctl, (iy, ix), (1, 1),
                                           wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                        self.fixed_param.append([None, name2, Tctl, None, None,
                                                 None, None, None])
                    elif p == "nsigmas":
                        ix = 7
                        value = self.model.getParam(name3)
                        Tct2 = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 2.2, 20),
                                             style=wx.TE_PROCESS_ENTER)

                        Tct2.SetValue(str(format_number(value)))
                        self.sizer4_4.Add(Tct2, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                        self.fixed_param.append([None, name3, Tct2,
                                                 None, None, None,
                                                 None, None])

                ix = 8
                disp_box = wx.ComboBox(self, wx.ID_ANY, size=(65, -1),
                                       style=wx.CB_READONLY, name='%s' % name1)
                for key, value in POLYDISPERSITY_MODELS.items():
                    name_disp = str(key)
                    disp_box.Append(name_disp, value)
                    disp_box.SetStringSelection("gaussian")
                wx.EVT_COMBOBOX(disp_box, wx.ID_ANY, self._on_disp_func)
                self.sizer4_4.Add(disp_box, (iy, ix), (1, 1), wx.EXPAND)
                self.fittable_param.append([cb, name1, ctl1, text2,
                                            ctl2, ctl3, ctl4, disp_box])

        ix = 0
        iy += 1
        self.sizer4_4.Add((20, 20), (iy, ix), (1, 1),
                          wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        first_orient = True
        for item in list(self.model.dispersion.keys()):
            if not self.magnetic_on:
                if item in self.model.magnetic_params:
                    continue
            if item in self.model.orientation_params:
                if item not in self.disp_cb_dict:
                    self.disp_cb_dict[item] = None
                name0 = "Distribution of " + item
                name1 = item + ".width"
                name2 = item + ".npts"
                name3 = item + ".nsigmas"

                if name1 not in self.model.details:
                    self.model.details[name1] = ["", None, None]

                iy += 1
                for p in list(self.model.dispersion[item].keys()):

                    if p == "width":
                        ix = 0
                        cb = wx.CheckBox(self, wx.ID_ANY, name0, (10, 10))
                        cb.SetValue(CHECK_STATE)
                        cb.SetToolTipString("Check mark to fit")
                        wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                        self.sizer4_4.Add(cb, (iy, ix), (1, 1),
                                wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)
                        if self.data.__class__.__name__ == "Data2D" or \
                                    self.enable2D:
                            cb.Show(True)
                        elif cb.IsShown():
                            cb.Hide()
                        ix = 1
                        value = self.model.getParam(name1)
                        ctl1 = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 1.3, 20),
                                             style=wx.TE_PROCESS_ENTER)
                        poly_tip = "Absolute Sigma for %s." % item
                        ctl1.SetToolTipString(poly_tip)
                        ctl1.SetValue(str(format_number(value, True)))
                        if self.data.__class__.__name__ == "Data2D" or \
                                    self.enable2D:
                            if first_orient:
                                values.SetLabel('PD[ratio], Sig[deg]')
                                poly_text = "PD(polydispersity for lengths):\n"
                                poly_text += "It should be a value between"
                                poly_text += "0 and 1\n"
                                poly_text += "Sigma for angles: \n"
                                poly_text += "It is the STD (ratio*mean)"
                                poly_text += " of the distribution.\n "

                                values.SetToolTipString(poly_text)
                                first_orient = False
                            ctl1.Show(True)
                        elif ctl1.IsShown():
                            ctl1.Hide()

                        self.sizer4_4.Add(ctl1, (iy, ix), (1, 1), wx.EXPAND)
                        # text to show error sign
                        ix = 2
                        text2 = wx.StaticText(self, wx.ID_ANY, '+/-')
                        self.sizer4_4.Add(text2, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                        text2.Hide()

                        ix = 3
                        ctl2 = wx.TextCtrl(self, wx.ID_ANY,
                                           size=(_BOX_WIDTH / 1.3, 20),
                                           style=0)

                        self.sizer4_4.Add(ctl2, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                        ctl2.Hide()
                        if self.data.__class__.__name__ == "Data2D" or \
                                self.enable2D:
                            if self.is_mac:
                                text2.Show(True)
                                ctl2.Show(True)

                        ix = 4
                        ctl3 = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 2, 20),
                                             style=wx.TE_PROCESS_ENTER,
                                text_enter_callback=self._onparamRangeEnter)

                        self.sizer4_4.Add(ctl3, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                        ctl3.Hide()

                        ix = 5
                        ctl4 = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 2, 20),
                                             style=wx.TE_PROCESS_ENTER,
                            text_enter_callback=self._onparamRangeEnter)
                        self.sizer4_4.Add(ctl4, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                        ctl4.Hide()

                        if self.data.__class__.__name__ == "Data2D" or \
                                self.enable2D:
                            ctl3.Show(True)
                            ctl4.Show(True)

                    elif p == "npts":
                        ix = 6
                        value = self.model.getParam(name2)
                        Tctl = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 2.2, 20),
                                             style=wx.TE_PROCESS_ENTER)

                        Tctl.SetValue(str(format_number(value)))
                        if self.data.__class__.__name__ == "Data2D" or \
                                self.enable2D:
                            Tctl.Show(True)
                        else:
                            Tctl.Hide()
                        self.sizer4_4.Add(Tctl, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                        self.fixed_param.append([None, name2, Tctl, None, None,
                                                 None, None, None])
                        self.orientation_params_disp.append([None, name2,
                                                             Tctl, None, None,
                                                             None, None, None])
                    elif p == "nsigmas":
                        ix = 7
                        value = self.model.getParam(name3)
                        Tct2 = ModelTextCtrl(self, wx.ID_ANY,
                                             size=(_BOX_WIDTH / 2.2, 20),
                                             style=wx.TE_PROCESS_ENTER)

                        Tct2.SetValue(str(format_number(value)))
                        if self.data.__class__.__name__ == "Data2D" or \
                                self.enable2D:
                            Tct2.Show(True)
                        else:
                            Tct2.Hide()
                        self.sizer4_4.Add(Tct2, (iy, ix), (1, 1),
                                          wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                        self.fixed_param.append([None, name3, Tct2,
                                                 None, None, None, None, None])

                        self.orientation_params_disp.append([None, name3,
                                        Tct2, None, None, None, None, None])

                ix = 8
                disp_box = wx.ComboBox(self, wx.ID_ANY, size=(65, -1),
                                style=wx.CB_READONLY, name='%s' % name1)
                for key, value in POLYDISPERSITY_MODELS.items():
                    name_disp = str(key)
                    disp_box.Append(name_disp, value)
                    disp_box.SetStringSelection("gaussian")
                wx.EVT_COMBOBOX(disp_box, wx.ID_ANY, self._on_disp_func)
                self.sizer4_4.Add(disp_box, (iy, ix), (1, 1), wx.EXPAND)
                self.fittable_param.append([cb, name1, ctl1, text2,
                                            ctl2, ctl3, ctl4, disp_box])
                self.orientation_params_disp.append([cb, name1, ctl1,
                                            text2, ctl2, ctl3, ctl4, disp_box])

                if self.data.__class__.__name__ == "Data2D" or \
                                self.enable2D:
                    disp_box.Show(True)
                else:
                    disp_box.Hide()

        self.state.disp_cb_dict = copy.deepcopy(self.disp_cb_dict)

        self.state.model = self.model.clone()
        # save state into
        self._copy_parameters_state(self.parameters, self.state.parameters)
        self._copy_parameters_state(self.orientation_params_disp,
                                     self.state.orientation_params_disp)
        self._copy_parameters_state(self.fittable_param,
                                    self.state.fittable_param)
        self._copy_parameters_state(self.fixed_param, self.state.fixed_param)

        wx.PostEvent(self.parent,
                     StatusEvent(status=" Selected Distribution: Gaussian"))
        # Fill the list of fittable parameters
        self.get_all_checked_params()
        self.Layout()

    def _onDraw(self, event):
        """
        Update and Draw the model
        """
        if self.model is None:
            msg = "Please select a Model first..."
            wx.MessageBox(msg, 'Info')
            return
        """
        if not self.data.is_data:
            self.npts_x = self.Npts_total.GetValue()
            self.Npts_fit.SetValue(self.npts_x)
            self.create_default_data()
        """
        flag, is_modified = self._update_paramv_on_fit()

        wx.CallAfter(self._onparamEnter_helper, is_modified)
        if not flag:
            msg = "The parameters are invalid"
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
            return

    def _onFit(self, event):
        """
        Allow to fit
        """
        if event is not None:
            event.Skip()
        if self.fit_started:
            self._StopFit()
            self.fit_started = False
            wx.CallAfter(self.set_fitbutton)
            return

        if self.data is None:
            msg = "Please get Data first..."
            wx.MessageBox(msg, 'Info')
            wx.PostEvent(self._manager.parent,
                         StatusEvent(status="Fit: %s" % msg))
            return
        if self.model is None:
            msg = "Please select a Model first..."
            wx.MessageBox(msg, 'Info')
            wx.PostEvent(self._manager.parent,
                         StatusEvent(status="Fit: %s" % msg, type="stop"))
            return

        if len(self.param_toFit) <= 0:
            msg = "Select at least one parameter to fit"
            wx.MessageBox(msg, 'Info')
            wx.PostEvent(self._manager.parent,
                         StatusEvent(status=msg, type="stop"))
            return

        flag = self._update_paramv_on_fit()

        if self.batch_on and not self._is_2D():
            if not self._validate_Npts_1D():
                return

        if not flag:
            msg = "Fitting range or parameters are invalid"
            wx.PostEvent(self._manager.parent,
                         StatusEvent(status=msg, type="stop"))
            return

        self.select_param()

        # Remove or do not allow fitting on the Q=0 point, especially
        # when y(q=0)=None at x[0].
        self.qmin_x = float(self.qmin.GetValue())
        self.qmax_x = float(self.qmax.GetValue())
        self._manager._reset_schedule_problem(value=0, uid=self.uid)
        self._manager.schedule_for_fit(uid=self.uid, value=1)
        self._manager.set_fit_range(uid=self.uid, qmin=self.qmin_x,
                                    qmax=self.qmax_x)

        # single fit
        # self._manager.onFit(uid=self.uid)
        self.fit_started = self._manager.onFit(uid=self.uid)
        wx.CallAfter(self.set_fitbutton)

    def _onFitHelp(self, event):
        """
        Bring up the Full Fitting Documentation whenever the HELP button is
        clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        web browser does not pass anything past the # to the browser when it is
        running "file:///...."

        :param evt: Triggers on clicking the help button
        """

        _TreeLocation = "user/sasgui/perspectives/fitting/fitting_help.html"
        _doc_viewer = DocumentationWindow(self, wx.ID_ANY, _TreeLocation, "",
                                          "General Fitting Help")

    def _onSmearHelp(self, event):
        """
        Bring up the instrumental resolution smearing Documentation whenever
        the ? button in the smearing box is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        web browser does not pass anything past the # to the browser when it is
        running "file:///...."

        :param evt: Triggers on clicking the help button
        """

        _TreeLocation = "user/sasgui/perspectives/fitting/resolution.html"
        _doc_viewer = DocumentationWindow(self, wx.ID_ANY, _TreeLocation, "",
                                          "Instrumental Resolution Smearing \
                                          Help")

    def set_fitbutton(self):
        """
        Set fit button label depending on the fit_started[bool]
        """
        # Skip this feature if we are not on Windows
        # NOTE: the is_mac data member actually means "is no Windows".
        if self.is_mac:
            return

        if self.fit_started:
            label = "Stop"
            color = "red"
        else:
            label = "Fit"
            color = "black"
        # self.btFit.Enable(False)
        self.btFit.SetLabel(label)
        self.btFit.SetForegroundColour(color)
        self.btFit.Enable(True)

    def get_weight_flag(self):
        """
        Get flag corresponding to a given weighting dI data.
        """
        button_list = [self.dI_noweight,
                       self.dI_didata,
                       self.dI_sqrdata,
                       self.dI_idata]
        flag = 1
        for item in button_list:
            if item.GetValue():
                if button_list.index(item) == 0:
                    flag = 0  # dy = np.ones_like(dy_data)
                elif button_list.index(item) == 1:
                    flag = 1  # dy = dy_data
                elif button_list.index(item) == 2:
                    flag = 2  # dy = np.sqrt(np.abs(data))
                elif button_list.index(item) == 3:
                    flag = 3  # dy = np.abs(data)
                break
        return flag

    def _StopFit(self, event=None):
        """
        Stop fit
        """
        if event is not None:
            event.Skip()
        self._manager.stop_fit(self.uid)
        self._manager._reset_schedule_problem(value=0)
        self._on_fit_complete()

    def rename_model(self):
        """
        find a short name for model
        """
        if self.model is not None:
            self.model.name = "M" + str(self.index_model)

    def _on_select_model(self, event=None, keep_pars=False):
        """
        call back for model selection
        """
        self.Show(False)
        if event is not None:
            control = event.GetEventObject()
            if ((control == self.formfactorbox
                 and self.structurebox.GetLabel() != 'None')
                    or control == self.structurebox
                    or control == self.multifactorbox):
                keep_pars = True

        if keep_pars:
            saved_pars = self.get_copy_params()
            is_poly_enabled = self.enable_disp.GetValue()
        else:
            saved_pars = None
            is_poly_enabled = None

        try:
            self._on_select_model_helper()
        except Exception as e:
            evt = StatusEvent(status=e.message, info="error")
            wx.PostEvent(self._manager.parent, evt)
            # Set S(Q) to None
            self.structurebox.SetSelection(0)
            self._on_select_model()
            return
        self.set_model_param_sizer(self.model)
        if self.model is None:
            self._set_bookmark_flag(False)
            self._keep.Enable(False)
            self._set_save_flag(False)
        self.enable_disp.SetValue(False)
        self.disable_disp.SetValue(True)
        # TODO: should not have an untrapped exception when displaying disperser
        # TODO: do we need to create the disperser panel on every model change?
        # Note: if we fix this, then remove ID_DISPERSER_HELP from basepage
        try:
            self.set_dispers_sizer()
        except Exception:
            pass
        self.state.enable_disp = self.enable_disp.GetValue()
        self.state.disable_disp = self.disable_disp.GetValue()
        self.state.pinhole_smearer = self.pinhole_smearer.GetValue()
        self.state.slit_smearer = self.slit_smearer.GetValue()

        self.state.structurecombobox = self.structurebox.GetValue()
        self.state.formfactorcombobox = self.formfactorbox.GetValue()
        self.state.categorycombobox = self.categorybox.GetValue()
        self.enable_fit_button()
        if self.model is not None:
            self.m_name = self.model.name
            self.state.m_name = self.m_name
            self.rename_model()
            self._set_copy_flag(True)
            self._set_paste_flag(True)
            if self.data is not None:
                is_data = check_data_validity(self.data)
                if is_data:
                    self._set_bookmark_flag(not self.batch_on)
                    self._keep.Enable(not self.batch_on)
                    self._set_save_flag(True)
            #Setting smearing for cases with and without data.
            self._set_smear(self.data)

            # more disables for 2D
            self._set_smear_buttons()

            try:
                # update smearer sizer
                #This call for smearing set up caused double evaluation of
                #I(q) and double compilation as results
                #self.onSmear(None)
                temp_smear = None
                if not self.disable_smearer.GetValue():
                    # Set the smearer environments
                    temp_smear = self.current_smearer
            except:
                raise
                # error occured on chisqr computation
                # pass
            # event to post model to fit to fitting plugins
            (ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()

            # set smearing value whether or not data contain the smearing info
            evt = ModelEventbox(model=self.model,
                                smearer=temp_smear,
                                enable_smearer=not self.disable_smearer.GetValue(),
                                qmin=float(self.qmin_x),
                                uid=self.uid,
                                caption=self.window_caption,
                                qmax=float(self.qmax_x))

            self._manager._on_model_panel(evt=evt)
            self.mbox_description.SetLabel("Model [ %s ]" %
                                           str(self.model.name))
            self.mbox_description.SetForegroundColour(wx.BLUE)
            self.state.model = self.model.clone()
            self.state.model.name = self.model.name

        # when select a model only from guictr/button
        if is_poly_enabled is not None:
            self.enable_disp.SetValue(is_poly_enabled)
            self.disable_disp.SetValue(not is_poly_enabled)
            self._set_dipers_Param(event=None)
            self.state.enable_disp = self.enable_disp.GetValue()
            self.state.disable_disp = self.disable_disp.GetValue()

        # Keep the previous param values
        if saved_pars:
            self.get_paste_params(saved_pars)

        if event is not None:
            # update list of plugins if new plugin is available
            # mod_cat = self.categorybox.GetStringSelection()
            # if mod_cat == CUSTOM_MODEL:
            #     temp = self.parent.update_model_list()
            #     for v in self.parent.model_dictionary.values():
            #         if v.id == self.model.id:
            #             self.model = v()
            #             break
            #     if temp:
            #         self.model_list_box = temp
            #         current_val = self.formfactorbox.GetLabel()
            #         pos = self.formfactorbox.GetSelection()
            #         self._show_combox_helper()
            #         self.formfactorbox.SetStringSelection(current_val)
            #         self.formfactorbox.SetValue(current_val)
            # post state to fit panel
            new_event = PageInfoEvent(page=self)
            wx.PostEvent(self.parent, new_event)
            wx.CallAfter(self._onDraw, None)

        else:
            self._draw_model()

        if self.batch_on:
            self.slit_smearer.Enable(False)
            self.pinhole_smearer.Enable(False)
            self.btEditMask.Disable()
            self.EditMask_title.Disable()

        self.Show(True)
        self.SetupScrolling()

    def _onparamEnter(self, event):
        """
        when enter value on panel redraw model according to changed
        """
        if self.model is None:
            msg = "Please select a Model first..."
            wx.MessageBox(msg, 'Info')
            return

        # default flag
        flag = False
        self.fitrange = True
        # get event object
        tcrtl = event.GetEventObject()
        # Clear msg if previously shown.
        msg = ""
        wx.PostEvent(self._manager.parent, StatusEvent(status=msg))

        if check_float(tcrtl):
            flag = self._onparamEnter_helper()
            self.show_npts2fit()
            if self.fitrange:
                temp_smearer = None
                if not self.disable_smearer.GetValue():
                    temp_smearer = self.current_smearer
                    # set smearing value whether or not data contain the
                    # smearing info
                    if self.slit_smearer.GetValue():
                        flag1 = self.update_slit_smear()
                        flag = flag or flag1
                    elif self.pinhole_smearer.GetValue():
                        flag1 = self.update_pinhole_smear()
                        flag = flag or flag1
                elif self.data.__class__.__name__ != "Data2D" and \
                        not self.enable2D:
                    enable_smearer = not self.disable_smearer.GetValue()
                    self._manager.set_smearer(smearer=temp_smearer,
                                              fid=self.data.id,
                                              uid=self.uid,
                                              qmin=float(self.qmin_x),
                                              qmax=float(self.qmax_x),
                                              enable_smearer=enable_smearer)
                if flag:
                    # self.compute_chisqr(smearer= temp_smearer)

                    # new state posted
                    if self.state_change:
                        # self._undo.Enable(True)
                        event = PageInfoEvent(page=self)
                        wx.PostEvent(self.parent, event)
                    self.state_change = False
            else:
                # invalid fit range: do nothing here:
                # msg already displayed in validate
                return
        else:
            self.save_current_state()
            msg = "Cannot Plot: Must enter a number!!!  "
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))

        self.save_current_state()
        return

    def _onparamRangeEnter(self, event):
        """
        Check validity of value enter in the parameters range field
        """
        tcrtl = event.GetEventObject()
        # Clear msg if previously shown.
        msg = ""
        wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        # Flag to register when a parameter has changed.
        is_modified = False
        if tcrtl.GetValue().lstrip().rstrip() != "":
            try:
                tcrtl.SetBackgroundColour(wx.WHITE)
                self._check_value_enter(self.fittable_param)
                self._check_value_enter(self.parameters)
            except:
                tcrtl.SetBackgroundColour("pink")
                msg = "Model Error:wrong value entered : %s" % sys.exc_info()[1]
                wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
                return
        else:
            tcrtl.SetBackgroundColour(wx.WHITE)

        # self._undo.Enable(True)
        self.save_current_state()
        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)
        self.state_change = False

    def qrang_set_focus(self, event=None):
        """
        ON Qrange focus
        """
        if event is not None:
            event.Skip()
        # tcrtl = event.GetEventObject()
        self._validate_qrange(self.qmin, self.qmax)

    def qrange_click(self, event):
        """
        On Qrange textctrl click, make the qrange lines in the plot
        """
        if event is not None:
            event.Skip()
        if self.data.__class__.__name__ == "Data2D":
            return
        is_click = event.LeftDown()
        if is_click:
            d_id = self.data.id
            d_group_id = self.data.group_id
            act_ctrl = event.GetEventObject()
            wx.PostEvent(self._manager.parent,
                         PlotQrangeEvent(ctrl=[self.qmin, self.qmax], id=d_id,
                                     group_id=d_group_id, leftdown=is_click,
                                     active=act_ctrl))

    def on_qrange_text(self, event):
        """
        #On q range value updated. DO not combine with qrange_click().
        """
        if event is not None:
            event.Skip()
        if self.data.__class__.__name__ == "Data2D":
            return
        act_ctrl = event.GetEventObject()
        d_id = self.data.id
        d_group_id = self.data.group_id
        wx.PostEvent(self._manager.parent,
                     PlotQrangeEvent(ctrl=[self.qmin, self.qmax], id=d_id,
                                     group_id=d_group_id, leftdown=False,
                                     active=act_ctrl))
        self._validate_qrange(self.qmin, self.qmax)

    def on_key(self, event):
        """
        On Key down
        """
        event.Skip()
        if self.data.__class__.__name__ == "Data2D":
            return
        ctrl = event.GetEventObject()
        try:
            x_data = float(ctrl.GetValue())
        except:
            return
        key = event.GetKeyCode()
        length = len(self.data.x)
        indx = (np.abs(self.data.x - x_data)).argmin()
        # return array.flat[idx]
        if key == wx.WXK_PAGEUP or key == wx.WXK_NUMPAD_PAGEUP:
            indx += 1
            if indx >= length:
                indx = length - 1
        elif key == wx.WXK_PAGEDOWN or key == wx.WXK_NUMPAD_PAGEDOWN:
            indx -= 1
            if indx < 0:
                indx = 0
        else:
            return
        ctrl.SetValue(str(self.data.x[indx]))
        self._validate_qrange(self.qmin, self.qmax)

    def _onQrangeEnter(self, event):
        """
        Check validity of value enter in the Q range field
        """
        tcrtl = event.GetEventObject()
        # Clear msg if previously shown.
        msg = ""
        wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        # For theory mode
        if not self.data.is_data:
            self.npts_x = self.Npts_total.GetValue()
            self.Npts_fit.SetValue(self.npts_x)
            self.create_default_data()
        # Flag to register when a parameter has changed.
        if tcrtl.GetValue().lstrip().rstrip() != "":
            try:
                tcrtl.SetBackgroundColour(wx.WHITE)
                # If qmin and qmax have been modified, update qmin and qmax
                if self._validate_qrange(self.qmin, self.qmax):
                    tempmin = float(self.qmin.GetValue())
                    if tempmin != self.qmin_x:
                        self.qmin_x = tempmin
                    tempmax = float(self.qmax.GetValue())
                    if tempmax != self.qmax_x:
                        self.qmax_x = tempmax
                else:
                    tcrtl.SetBackgroundColour("pink")
                    msg = "Model Error:wrong value entered : %s" % sys.exc_info()[1]
                    wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
                    return
            except:
                tcrtl.SetBackgroundColour("pink")
                msg = "Model Error:wrong value entered : %s" % sys.exc_info()[1]
                wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
                return
            # Check if # of points for theory model are valid(>0).
            # check for 2d
            if self.data.__class__.__name__ == "Data2D" or \
                    self.enable2D:
                # set mask
                radius = np.sqrt(self.data.qx_data * self.data.qx_data +
                                    self.data.qy_data * self.data.qy_data)
                index_data = ((self.qmin_x <= radius) & (radius <= self.qmax_x))
                index_data = (index_data) & (self.data.mask)
                index_data = (index_data) & (np.isfinite(self.data.data))
                if len(index_data[index_data]) < 10:
                    msg = "Cannot Plot :No or too little npts in"
                    msg += " that data range!!!  "
                    wx.PostEvent(self._manager.parent,
                                 StatusEvent(status=msg))
                    return
                else:
                    # self.data.mask = index_data
                    # self.Npts_fit.SetValue(str(len(self.data.mask)))
                    self.show_npts2fit()
            else:
                index_data = ((self.qmin_x <= self.data.x) &
                              (self.data.x <= self.qmax_x))
                self.Npts_fit.SetValue(str(len(self.data.x[index_data])))

            self.npts_x = self.Npts_total.GetValue()
            self.create_default_data()
            self._save_plotting_range()
        else:
            tcrtl.SetBackgroundColour("pink")
            msg = "Model Error:wrong value entered!!!"
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))

        self._draw_model()
        self.save_current_state()
        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)
        self.state_change = False
        return

    def _clear_Err_on_Fit(self):
        """
        hide the error text control shown
        after fitting
        """

        if self.is_mac:
            return
        if hasattr(self, "text2_3"):
            self.text2_3.Hide()

        if len(self.parameters) > 0:
            for item in self.parameters:
                if item[0].IsShown():
                    # Skip the angle parameters if 1D data
                    if self.data.__class__.__name__ != "Data2D" and \
                            not self.enable2D:
                        if item in self.orientation_params:
                            continue
                    if item in self.param_toFit:
                        continue
                    # hide statictext +/-
                    if len(item) < 4:
                        continue
                    if item[3] is not None and item[3].IsShown():
                        item[3].Hide()
                    # hide textcrtl  for error after fit
                    if item[4] is not None and item[4].IsShown():
                        item[4].Hide()

        if len(self.fittable_param) > 0:
            for item in self.fittable_param:
                if item[0].IsShown():
                    # Skip the angle parameters if 1D data
                    if self.data.__class__.__name__ != "Data2D" and \
                            not self.enable2D:
                        if item in self.orientation_params:
                            continue
                    if item in self.param_toFit:
                        continue
                    if len(item) < 4:
                        continue
                    # hide statictext +/-
                    if item[3] is not None and item[3].IsShown():
                        item[3].Hide()
                    # hide textcrtl  for error after fit
                    if item[4] is not None and item[4].IsShown():
                        item[4].Hide()
        return

    def _get_defult_custom_smear(self):
        """
        Get the defult values for custum smearing.
        """
        # get the default values
        if self.dxl is None:
            self.dxl = 0.0
        if self.dxw is None:
            self.dxw = ""
        if self.dx_percent is None:
            self.dx_percent = SMEAR_SIZE_H

    def _get_smear_info(self):
        """
        Get the smear info from data.

        :return: self.smear_type, self.dq_l and self.dq_r,
            respectively the type of the smear, dq_min and
            dq_max for pinhole smear data
            while dxl and dxw for slit smear
        """
        # default
        self.smear_type = None
        self.dq_l = None
        self.dq_r = None
        data = self.data
        if self.data is None:
            return
        elif self.data.__class__.__name__ == "Data2D" or \
            self.enable2D:
            if data.dqx_data is None or data.dqy_data is None:
                return
            elif self.current_smearer is not None \
                and data.dqx_data.any() != 0 \
                and data.dqx_data.any() != 0:
                self.smear_type = "Pinhole2d"
                self.dq_l = format_number(np.average(data.dqx_data))
                self.dq_r = format_number(np.average(data.dqy_data))
                return
            else:
                return
        # check if it is pinhole smear and get min max if it is.
        if data.dx is not None and np.any(data.dx):
            self.smear_type = "Pinhole"
            self.dq_l = data.dx[0]
            self.dq_r = data.dx[-1]

        # check if it is slit smear and get min max if it is.
        elif data.dxl is not None or data.dxw is not None:
            self.smear_type = "Slit"
            if data.dxl is not None and np.all(data.dxl, 0):
                self.dq_l = data.dxl[0]
            if data.dxw is not None and np.all(data.dxw, 0):
                self.dq_r = data.dxw[0]
        # return self.smear_type,self.dq_l,self.dq_r

    def _show_smear_sizer(self):
        """
        Show only the sizers depending on smear selection
        """
        # smear disabled
        if self.disable_smearer.GetValue():
            self.smear_description_none.Show(True)
        # 2Dsmear
        elif self._is_2D():
            self.smear_description_accuracy_type.Show(True)
            self.smear_accuracy.Show(True)
            self.smear_description_accuracy_type.Show(True)
            self.smear_description_2d.Show(True)
            self.smear_description_2d_x.Show(True)
            self.smear_description_2d_y.Show(True)
            if self.pinhole_smearer.GetValue():
                self.smear_pinhole_percent.Show(True)
        # smear from data
        elif self.enable_smearer.GetValue():

            self.smear_description_dqdata.Show(True)
            if self.smear_type is not None:
                self.smear_description_smear_type.Show(True)
                if self.smear_type == 'Slit':
                    self.smear_description_slit_height.Show(True)
                    self.smear_description_slit_width.Show(True)
                elif self.smear_type == 'Pinhole':
                    self.smear_description_pin_percent.Show(True)
                self.smear_description_smear_type.Show(True)
                self.smear_description_type.Show(True)
                self.smear_data_left.Show(True)
                self.smear_data_right.Show(True)
        # custom pinhole smear
        elif self.pinhole_smearer.GetValue():
            if self.smear_type == 'Pinhole':
                self.smear_message_new_p.Show(True)
                self.smear_description_pin_percent.Show(True)

            self.smear_pinhole_percent.Show(True)
        # custom slit smear
        elif self.slit_smearer.GetValue():
            self.smear_message_new_s.Show(True)
            self.smear_description_slit_height.Show(True)
            self.smear_slit_height.Show(True)
            self.smear_description_slit_width.Show(True)
            self.smear_slit_width.Show(True)

    def _hide_all_smear_info(self):
        """
        Hide all smearing messages in the set_smearer sizer
        """
        self.smear_description_none.Hide()
        self.smear_description_dqdata.Hide()
        self.smear_description_type.Hide()
        self.smear_description_smear_type.Hide()
        self.smear_description_accuracy_type.Hide()
        self.smear_description_2d_x.Hide()
        self.smear_description_2d_y.Hide()
        self.smear_description_2d.Hide()

        self.smear_accuracy.Hide()
        self.smear_data_left.Hide()
        self.smear_data_right.Hide()
        self.smear_description_pin_percent.Hide()
        self.smear_pinhole_percent.Hide()
        self.smear_description_slit_height.Hide()
        self.smear_slit_height.Hide()
        self.smear_description_slit_width.Hide()
        self.smear_slit_width.Hide()
        self.smear_message_new_p.Hide()
        self.smear_message_new_s.Hide()

    def _set_accuracy_list(self):
        """
        Set the list of an accuracy in 2D custum smear:
                Xhigh, High, Med, or Low
        """
        # list of accuracy choices
        list = ['Low', 'Med', 'High', 'Xhigh']
        for idx in range(len(list)):
            self.smear_accuracy.Append(list[idx], idx)

    def _set_fun_box_list(self, fun_box):
        """
        Set the list of func for multifunctional models
        """
        # Check if it is multi_functional model
        if self.model.__class__ not in self.model_list_box["Multi-Functions"] \
                and not self.temp_multi_functional:
            return None
        # Get the func name list
        list = self.model.fun_list
        if len(list) == 0:
            return None
        # build function (combo)box
        ind = 0
        while(ind < len(list)):
            for key, val in list(list.items()):
                if val == ind:
                    fun_box.Append(key, val)
                    break
            ind += 1

    def _on_select_accuracy(self, event):
        """
        Select an accuracy in 2D custom smear: Xhigh, High, Med, or Low
        """
        # event.Skip()
        # Check if the accuracy is same as before
        # self.smear2d_accuracy = event.GetEventObject().GetValue()
        self.smear2d_accuracy = self.smear_accuracy.GetValue()
        if self.pinhole_smearer.GetValue():
            self.onPinholeSmear(event=None)
        else:
            self.onSmear(event=None)
            if self.current_smearer is not None:
                self.current_smearer.set_accuracy(accuracy=\
                                                  self.smear2d_accuracy)
        event.Skip()

    def _on_fun_box(self, event):
        """
        Select an func: Erf,Rparabola,LParabola
        """
        fun_val = None
        fun_box = event.GetEventObject()
        name = fun_box.Name
        value = fun_box.GetValue()
        if value in self.model.fun_list:
            fun_val = self.model.fun_list[value]

        self.model.setParam(name, fun_val)
        # save state
        self._copy_parameters_state(self.str_parameters,
                                    self.state.str_parameters)
        # update params
        self._update_paramv_on_fit()
        # draw
        self._draw_model()
        self.Refresh()
        # get ready for new event
        event.Skip()

    def _onMask(self, event):
        """
        Build a panel to allow to edit Mask
        """
        from sas.sasgui.guiframe.local_perspectives.plotting.masking import \
            MaskPanel as MaskDialog

        self.panel = MaskDialog(base=self, data=self.data, id=wx.NewId())
        self.panel.ShowModal()

    def _draw_masked_model(self, event):
        """
        Draw model image w/mask
        """
        is_valid_qrange = self._update_paramv_on_fit()

        if is_valid_qrange and self.model is not None:
            self.panel.MakeModal(False)
            event.Skip()
            # try re draw the model plot if it exists
            self._draw_model()
            self.show_npts2fit()
        elif self.model is None:
            self.panel.MakeModal(False)
            event.Skip()
            self.show_npts2fit()
            msg = "No model is found on updating MASK in the model plot... "
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        else:
            event.Skip()
            msg = ' Please consider your Q range, too.'
            self.panel.ShowMessage(msg)

    def _set_smear(self, data):
        """
        Set_smear
        """
        if data is None:
            return
        self.current_smearer = smear_selection(data, self.model)
        flag = self.disable_smearer.GetValue()
        if self.current_smearer is None:
            self.enable_smearer.Disable()
        else:
            self.enable_smearer.Enable()
        if not flag:
            self.onSmear(None)

    def get_view_mode(self):
        """
        return True if the panel allow 2D or False if 1D
        """
        return self.enable2D

    def compute_data_set_range(self, data_list):
        """
        find the range that include all data  in the set
        return the minimum and the maximum values
        """
        if data_list is not None and data_list != []:
            for data in data_list:
                qmin, qmax, npts = self.compute_data_range(data)
                self.qmin_data_set = min(self.qmin_data_set, qmin)
                self.qmax_data_set = max(self.qmax_data_set, qmax)
                self.npts_data_set += npts
        return self.qmin_data_set, self.qmax_data_set, self.npts_data_set

    def compute_data_range(self, data):
        """
        compute the minimum and the maximum range of the data
        return the npts contains in data
        :param data:
        """
        qmin, qmax, npts = None, None, None
        if data is not None:
            if not hasattr(data, "data"):
                try:
                    qmin = min(data.x)
                    # Maximum value of data
                    qmax = max(data.x)
                    npts = len(data.x)
                except:
                    msg = "Unable to find min/max/length of \n data named %s" %\
                                data.filename
                    wx.PostEvent(self._manager.parent, StatusEvent(status=msg,
                                               info="error"))
                    raise ValueError(msg)

            else:
                qmin = 0
                try:
                    x = max(math.fabs(data.xmin), math.fabs(data.xmax))
                    y = max(math.fabs(data.ymin), math.fabs(data.ymax))
                except:
                    msg = "Unable to find min/max of \n data named %s" % \
                                data.filename
                    wx.PostEvent(self._manager.parent, StatusEvent(status=msg,
                                               info="error"))
                    raise ValueError(msg)
                # Maximum value of data
                qmax = math.sqrt(x * x + y * y)
                npts = len(data.data)
        return qmin, qmax, npts

    def set_data(self, data):
        """
        reset the current data
        """
        id = None
        flag = False
        is_data = False
        npts = 0
        try:
            old_id = self.data.id
            old_group_id = self.data.group_id
        except:
            old_id = id
            old_group_id = id
        if self.data is not None:
            is_data = check_data_validity(self.data)
        if not is_data and data is not None:
                flag = True
        if data is not None:
            if is_data:
                self.graph_id = self.data.group_id
                flag = (data.id != self.data.id)
        self.data = data
        if check_data_validity(data):
            self.graph_id = data.group_id
        self.data.group_id = self.graph_id

        if self.data is None:
            data_name = ""
            self._set_bookmark_flag(False)
            self._keep.Enable(False)
            self._set_save_flag(False)
        else:
            if self.model is not None:
                self._set_bookmark_flag(not self.batch_on)
                self._keep.Enable(not self.batch_on)
            if self.data.is_data:
                self._set_save_flag(True)
                self._set_preview_flag(True)

            # more disables for 2D
            di_flag = False
            dq_flag = False
            if self.data.__class__.__name__ == "Data2D" or \
                        self.enable2D:
                self.slit_smearer.Disable()
                self.pinhole_smearer.Enable(True)
                self.default_mask = copy.deepcopy(self.data.mask)
                if self.data.err_data is not None \
                        and np.any(self.data.err_data):
                    di_flag = True
                if self.data.dqx_data is not None \
                        and np.any(self.data.dqx_data):
                    dq_flag = True
            else:
                self.slit_smearer.Enable(True)
                self.pinhole_smearer.Enable(True)
                if self.data.dy is not None and np.any(self.data.dy):
                    di_flag = True
                if self.data.dx is not None and np.any(self.data.dx):
                    dq_flag = True
                elif self.data.dxl is not None and np.any(self.data.dxl):
                    dq_flag = True

            if dq_flag:
                self.enable_smearer.Enable(True)
                self.enable_smearer.SetValue(True)
                self.disable_smearer.SetValue(False)
            else:
                self.enable_smearer.Disable()
                self.disable_smearer.Enable(True)
                self.disable_smearer.SetValue(True)

            if di_flag:
                self.dI_didata.Enable(True)
                self.dI_didata.SetValue(True)
                self.weightbt_string = self.dI_didata.GetLabelText()
            else:
                self.dI_didata.Enable(False)
                self.dI_noweight.SetValue(True)
                self.weightbt_string = self.dI_noweight.GetLabelText()

            # Enable weighting radio buttons
            self.dI_noweight.Enable(True)
            self.dI_sqrdata.Enable(True)
            self.dI_idata.Enable(True)

            self.formfactorbox.Enable()
            self.structurebox.Enable()
            data_name = self.data.name
            _, _, npts = self.compute_data_range(self.data)
            # set maximum range for x in linear scale
            if not hasattr(self.data, "data"):  # Display only for 1D data fit
                self.btEditMask.Disable()
                self.EditMask_title.Disable()
            else:
                self.btEditMask.Enable()
                self.EditMask_title.Enable()

        self.Npts_total.SetValue(str(npts))
        # default:number of data points selected to fit
        self.Npts_fit.SetValue(str(npts))
        self.Npts_total.SetEditable(False)
        self.Npts_total.SetBackgroundColour(
                                    self.GetParent().GetBackgroundColour())

        self.Npts_total.Bind(wx.EVT_MOUSE_EVENTS, self._npts_click)
        self.pointsbox.Disable()
        self.dataSource.SetValue(data_name)
        self.state.data = data
        self.enable_fit_button()
        # send graph_id to page_finder
        self._manager.set_graph_id(uid=self.uid, graph_id=self.graph_id)
        # focus the page
        if check_data_validity(data):
            self.data_box_description.SetForegroundColour(wx.BLUE)

        if self.batch_on:
            self.slit_smearer.Enable(False)
            self.pinhole_smearer.Enable(False)
            self.btEditMask.Disable()
            self.EditMask_title.Disable()

        self.on_smear_helper()
        self.on_set_focus(None)
        self.Refresh()
        # update model plot with new data information
        if flag:
            if self.data.__class__.__name__ == "Data2D":
                self.enable2D = True
                self.model_view.SetLabel("2D Mode")
            else:
                self.enable2D = False
                self.model_view.SetLabel("1D Mode")
            self.model_view.Disable()
            #  replace data plot on combo box selection
            # by removing the previous selected data
            try:
                wx.PostEvent(self._manager.parent,
                             NewPlotEvent(action="delete",
                                          group_id=old_group_id, id=old_id))
            except:
                pass
            # plot the current selected data
            wx.PostEvent(self._manager.parent,
                         NewPlotEvent(action="check", plot=self.data,
                                      title=str(self.data.title)))
            self._draw_model()

    def _npts_click(self, event):
        """
        Prevent further handling of the mouse event on Npts_total
        by not calling Skip().
        """
        pass

    def reset_page(self, state, first=False):
        """
        reset the state
        """
        try:
            self.reset_page_helper(state)

            self.select_param()
            # Save state_fit
            self.save_current_state_fit()
            self.onSmear(None)
            self._onDraw(None)
        except:
            self._show_combox_helper()
            msg = "Error: This model state has missing or outdated "
            msg += "information.\n"
            msg += traceback.format_exc()
            wx.PostEvent(self._manager.parent,
                         StatusEvent(status=msg, info="error"))
        self._lay_out()
        self.Refresh()

    def get_range(self):
        """
        return the fitting range
        """
        return float(self.qmin_x), float(self.qmax_x)

    def get_npts2fit(self):
        """
        return numbers of data points within qrange

        :Note: This is to normalize chisq by Npts of fit

        """
        if self.data is None:
            return
        npts2fit = 0
        qmin, qmax = self.get_range()
        if self.data.__class__.__name__ == "Data2D" or \
                        self.enable2D:
            radius = np.sqrt(self.data.qx_data * self.data.qx_data +
                                self.data.qy_data * self.data.qy_data)
            index_data = (self.qmin_x <= radius) & (radius <= self.qmax_x)
            index_data = (index_data) & (self.data.mask)
            index_data = (index_data) & (np.isfinite(self.data.data))
            npts2fit = len(self.data.data[index_data])
        else:
            for qx in self.data.x:
                if qmax >= qx >= qmin:
                    npts2fit += 1
        return npts2fit

    def show_npts2fit(self):
        """
        setValue Npts for fitting
        """
        self.Npts_fit.SetValue(str(self.get_npts2fit()))

    def get_chi2(self):
        """
        return the current chi2
        """
        return self.tcChi.GetValue()

    def onsetValues(self, chisqr, p_name, out, cov):
        """
        Build the panel from the fit result

        :param chisqr: Value of the goodness of fit metric
        :param p_name: the name of parameters
        :param out: list of parameter with the best value found during fitting
        :param cov: Covariance matrix

        """

        # make sure stop button to fit button all the time
        self._on_fit_complete()
        if out is None or not np.isfinite(chisqr):
            raise ValueError("Fit error occured...")

        is_modified = False
        has_error = False
        dispersity = ''

        # Hide textctrl boxes of errors.
        self._clear_Err_on_Fit()

        # Check if chi2 is finite
        if chisqr is not None and np.isfinite(chisqr):
            # format chi2
            chi2 = format_number(chisqr, True)
            self.tcChi.SetValue(chi2)
            self.tcChi.Refresh()
        else:
            self.tcChi.SetValue("-")

        # Hide error title
        if self.text2_3.IsShown() and not self.is_mac:
            self.text2_3.Hide()

        try:
            if self.enable_disp.GetValue():
                if hasattr(self, "text_disp_1"):
                    if self.text_disp_1 is not None and not self.is_mac:
                        self.text_disp_1.Hide()
        except:
            dispersity = None
            pass

        i = 0
        # Set the panel when fit result are list

        for item in self.param_toFit:
            if len(item) > 5 and item is not None:

                if item[0].IsShown():
                    # reset error value to initial state
                    if not self.is_mac:
                        item[3].Hide()
                        item[4].Hide()
                    for ind in range(len(out)):
                        if item[1] == p_name[ind]:
                            break
                    if len(out) > 0 and out[ind] is not None:
                        val_out = format_number(out[ind], True)
                        item[2].SetValue(val_out)

                    if(cov is not None and len(cov) == len(out)):
                        try:
                            if dispersity is not None:
                                if self.enable_disp.GetValue():
                                    if hasattr(self, "text_disp_1"):
                                        if self.text_disp_1 is not None:
                                            if not self.text_disp_1.IsShown()\
                                                  and not self.is_mac:
                                                self.text_disp_1.Show(True)
                        except:
                            pass

                        if cov[ind] is not None:
                            if np.isfinite(float(cov[ind])):
                                val_err = format_number(cov[ind], True)
                                item[4].SetForegroundColour(wx.BLACK)
                            else:
                                val_err = 'NaN'
                                item[4].SetForegroundColour(wx.RED)
                            if not self.is_mac:
                                item[3].Show(True)
                                item[4].Show(True)
                            item[4].SetValue(val_err)
                            has_error = True
                i += 1
            else:
                raise ValueError("onsetValues: Invalid parameters...")
        # Show error title when any errors displayed
        if has_error:
            if not self.text2_3.IsShown():
                self.text2_3.Show(True)
        # save current state
        self.save_current_state()

        if not self.is_mac:
            self.Layout()
            self.Refresh()
        # plot model ( when drawing, do not update chisqr value again)
        self._draw_model(update_chisqr=False, source='fit')

    def onWeighting(self, event):
        """
        On Weighting radio button event, sets the weightbt_string
        """
        self.weightbt_string = event.GetEventObject().GetLabelText()
        self._set_weight()

    def _set_weight(self, is_2D=None):
        """
        Set weight in fit problem
        """
        # compute weight for the current data
        flag_weight = self.get_weight_flag()
        if is_2D is None:
            is_2D = self._is_2D()
        self._manager.set_fit_weight(uid=self.uid,
                                     flag=flag_weight,
                                     is2d=is_2D,
                                     fid=None)

    def onPinholeSmear(self, event):
        """
        Create a custom pinhole smear object that will change the way residuals
        are compute when fitting

        :Note: accuracy is given by strings'High','Med', 'Low' FOR 2d,
                     None for 1D

        """
        # Need update param values
        self._update_paramv_on_fit()

        if event is not None:
            tcrtl = event.GetEventObject()
            # event case of radio button
            if tcrtl.GetValue():
                self.dx_percent = 0.0
                is_new_pinhole = True
            else:
                is_new_pinhole = self._is_changed_pinhole()
        else:
            is_new_pinhole = True
        # if any value is changed
        if is_new_pinhole:
            self._set_pinhole_smear()
        # hide all silt sizer
        self._hide_all_smear_info()

        # show relevant slit sizers
        self._show_smear_sizer()

        self.sizer_set_smearer.Layout()
        # we need FitInside here not just self.Layout to ensure all the sizers
        # end up with the necessasary space to in the scroll panel. In
        # particular the compute and fit buttons end up on top of each other
        # PDB Nov 28 2015.
        self.FitInside()

        if event is not None:
            event.Skip()
        # self._undo.Enable(True)
        self.save_current_state()
        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)

    def _is_changed_pinhole(self):
        """
        check if any of pinhole smear is changed

        :return: True or False

        """
        # get the values
        pin_percent = self.smear_pinhole_percent.GetValue()

        # Check changes in slit heigth
        try:
            dx_percent = float(pin_percent)
        except:
            return True
        if self.dx_percent != dx_percent:
            return True
        return False

    def _set_pinhole_smear(self):
        """
        Set custom pinhole smear

        :return: msg

        """
        # copy data
        data = copy.deepcopy(self.data)
        if self._is_2D():
            self.smear_type = 'Pinhole2d'
            len_data = len(data.data)
            data.dqx_data = np.zeros(len_data)
            data.dqy_data = np.zeros(len_data)
        else:
            self.smear_type = 'Pinhole'
            len_data = len(data.x)
            data.dx = np.zeros(len_data)
            data.dxl = None
            data.dxw = None
        msg = None

        get_pin_percent = self.smear_pinhole_percent

        if not check_float(get_pin_percent):
            get_pin_percent.SetBackgroundColour("pink")
            msg = "Model Error:wrong value entered!!!"
        else:
            if len_data < 2:
                len_data = 2
            self.dx_percent = float(get_pin_percent.GetValue())
            if self.dx_percent < 0:
                get_pin_percent.SetBackgroundColour("pink")
                msg = "Model Error:This value can not be negative!!!"
            elif self.dx_percent is not None:
                percent = self.dx_percent/100
                if self._is_2D():
                    data.dqx_data[data.dqx_data == 0] = percent * data.qx_data
                    data.dqy_data[data.dqy_data == 0] = percent * data.qy_data
                else:
                    data.dx = percent * data.x
            self.current_smearer = smear_selection(data, self.model)
            # 2D need to set accuracy
            if self._is_2D():
                self.current_smearer.set_accuracy(
                    accuracy=self.smear2d_accuracy)

        if msg is not None:
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        else:
            get_pin_percent.SetBackgroundColour("white")
        # set smearing value whether or not the data contain the smearing info

        enable_smearer = not self.disable_smearer.GetValue()
        self._manager.set_smearer(smearer=self.current_smearer,
                                  fid=self.data.id,
                                  qmin=float(self.qmin_x),
                                  qmax=float(self.qmax_x),
                                  enable_smearer=enable_smearer,
                                  uid=self.uid)
        return msg

    def update_pinhole_smear(self):
        """
        called by kill_focus on pinhole TextCntrl
        to update the changes

        :return: False when wrong value was entered

        """
        # msg default
        msg = None
        # check if any value is changed
        if self._is_changed_pinhole():
            msg = self._set_pinhole_smear()
        wx.CallAfter(self.save_current_state)

        if msg is not None:
            return False
        else:
            return True

    def onSlitSmear(self, event):
        """
        Create a custom slit smear object that will change the way residuals
        are compute when fitting
        """
        # Need update param values
        self._update_paramv_on_fit()

        # msg default
        msg = None
        # for event given
        if event is not None:
            tcrtl = event.GetEventObject()
            # event case of radio button
            if tcrtl.GetValue():
                self.dxl = 0.0
                self.dxw = 0.0
                is_new_slit = True
            else:
                is_new_slit = self._is_changed_slit()
        else:
            is_new_slit = True

        # if any value is changed
        if is_new_slit:
            msg = self._set_slit_smear()

        # hide all silt sizer
        self._hide_all_smear_info()
        # show relevant slit sizers
        self._show_smear_sizer()
        self.sizer_set_smearer.Layout()
        # we need FitInside here not just self.Layout to ensure all the sizers
        # end up with the necessasary space to in the scroll panel. In
        # particular the compute and fit buttons end up on top of each other
        # PDB Nov 28 2015.
        self.FitInside()

        if event is not None:
            event.Skip()
        self.save_current_state()
        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)
        if msg is not None:
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))

    def _is_changed_slit(self):
        """
        check if any of slit lengths is changed

        :return: True or False

        """
        # get the values
        width = self.smear_slit_width.GetValue()
        height = self.smear_slit_height.GetValue()

        # check and change the box bg color if it was pink
        #    but it should be white now
        # because this is the case that _set_slit_smear() will not handle
        if height.lstrip().rstrip() == "":
            self.smear_slit_height.SetBackgroundColour(wx.WHITE)
        if width.lstrip().rstrip() == "":
            self.smear_slit_width.SetBackgroundColour(wx.WHITE)

        # Check changes in slit width
        if width == "":
            dxw = 0.0
        else:
            try:
                dxw = float(width)
            except:
                return True
        if self.dxw != dxw:
            return True

        # Check changes in slit heigth
        if height == "":
            dxl = 0.0
        else:
            try:
                dxl = float(height)
            except:
                return True
        if self.dxl != dxl:
            return True

        return False

    def _set_slit_smear(self):
        """
        Set custom slit smear

        :return: message to inform the user about the validity
            of the values entered for slit smear
        """
        if self.data.__class__.__name__ == "Data2D" or self.enable2D:
            return
        # make sure once more if it is smearer
        data = copy.deepcopy(self.data)
        data_len = len(data.x)
        data.dx = None
        data.dxl = None
        data.dxw = None
        msg = None

        try:
            self.dxl = float(self.smear_slit_height.GetValue())
            data.dxl = self.dxl * np.ones(data_len)
            self.smear_slit_height.SetBackgroundColour(wx.WHITE)
        except:
            self.dxl = None
            data.dxl = np.zeros(data_len)
            if self.smear_slit_height.GetValue().lstrip().rstrip() != "":
                self.smear_slit_height.SetBackgroundColour("pink")
                msg = "Wrong value entered... "
            else:
                self.smear_slit_height.SetBackgroundColour(wx.WHITE)
        try:
            self.dxw = float(self.smear_slit_width.GetValue())
            self.smear_slit_width.SetBackgroundColour(wx.WHITE)
            data.dxw = self.dxw * np.ones(data_len)
        except:
            self.dxw = None
            data.dxw = np.zeros(data_len)
            if self.smear_slit_width.GetValue().lstrip().rstrip() != "":
                self.smear_slit_width.SetBackgroundColour("pink")
                msg = "Wrong Fit value entered... "
            else:
                self.smear_slit_width.SetBackgroundColour(wx.WHITE)

        self.current_smearer = smear_selection(data, self.model)
        # set smearing value whether or not the data contain the smearing info
        enable_smearer = not self.disable_smearer.GetValue()
        self._manager.set_smearer(smearer=self.current_smearer,
                                  fid=self.data.id,
                                  qmin=float(self.qmin_x),
                                  qmax=float(self.qmax_x),
                                  enable_smearer=enable_smearer,
                                  uid=self.uid)
        return msg

    def update_slit_smear(self):
        """
        called by kill_focus on pinhole TextCntrl
        to update the changes

        :return: False when wrong value was entered

        """
        # msg default
        msg = None
        # check if any value is changed
        if self._is_changed_slit():
            msg = self._set_slit_smear()
        # self._undo.Enable(True)
        self.save_current_state()

        if msg is not None:
            return False
        else:
            return True

    def onSmear(self, event):
        """
        Create a smear object that will change the way residuals
        are computed when fitting
        """
        if event is not None:
            event.Skip()
        if self.data is None:
            return

        # Need update param values
        self._update_paramv_on_fit()
        if self.model is not None:
            if self.data.is_data:
                self._manager.page_finder[self.uid].add_data(data=self.data)
        temp_smearer = self.on_smear_helper()

        self.sizer_set_smearer.Layout()
        # we need FitInside here not just self.Layout to ensure all the sizers
        # end up with the necessasary space to in the scroll panel. In
        # particular the compute and fit buttons end up on top of each other
        # PDB Nov 28 2015.
        self.FitInside()
        self._set_weight()

        # set smearing value whether or not the data contain the smearing info
        enable_smearer = not self.disable_smearer.GetValue()
        wx.CallAfter(self._manager.set_smearer, uid=self.uid,
                     smearer=temp_smearer,
                     fid=self.data.id,
                     qmin=float(self.qmin_x),
                     qmax=float(self.qmax_x),
                     enable_smearer=enable_smearer)

        self.state.enable_smearer = self.enable_smearer.GetValue()
        self.state.disable_smearer = self.disable_smearer.GetValue()
        self.state.pinhole_smearer = self.pinhole_smearer.GetValue()
        self.state.slit_smearer = self.slit_smearer.GetValue()

    def on_smear_helper(self, update=False):
        """
        Help for onSmear

        :param update: force or not to update
        """
        self._get_smear_info()
        # renew smear sizer
        if self.smear_type is not None:
            self.smear_description_smear_type.SetValue(str(self.smear_type))
            self.smear_data_left.SetValue(str(self.dq_l))
            self.smear_data_right.SetValue(str(self.dq_r))

        self._hide_all_smear_info()
        data = copy.deepcopy(self.data)

        # make sure once more if it is smearer
        temp_smearer = smear_selection(data, self.model)
        if self.current_smearer != temp_smearer or update:
            self.current_smearer = temp_smearer
        if self.enable_smearer.GetValue():
            if self.current_smearer is None:
                wx.PostEvent(self._manager.parent,
                    StatusEvent(status="Data contains no smearing information"))
            else:
                wx.PostEvent(self._manager.parent,
                    StatusEvent(status="Data contains smearing information"))

            self.smear_data_left.Show(True)
            self.smear_data_right.Show(True)
            temp_smearer = self.current_smearer
        elif self.disable_smearer.GetValue():
            self.smear_description_none.Show(True)
        elif self.pinhole_smearer.GetValue():
            self.onPinholeSmear(None)
        elif self.slit_smearer.GetValue():
            self.onSlitSmear(None)
        self._show_smear_sizer()

        return temp_smearer

    def on_complete_chisqr(self, event):
        """
        Display result chisqr on the panel
        :event: activated by fitting/ complete after draw
        """
        try:
            if event is None:
                output = "-"
            elif not np.isfinite(event.output):
                output = "-"
            else:
                output = event.output
            self.tcChi.SetValue(str(format_number(output, True)))
            self.state.tcChi = self.tcChi.GetValue()
        except:
            pass

    def get_all_checked_params(self):
        """
        Found all parameters current check and add them to list of parameters
        to fit
        """
        self.param_toFit = []
        for item in self.parameters:
            if item[0].GetValue() and item not in self.param_toFit:
                if item[0].IsShown():
                    self.param_toFit.append(item)
        for item in self.fittable_param:
            if item[0].GetValue() and item not in self.param_toFit:
                if item[0].IsShown():
                    self.param_toFit.append(item)
        self.save_current_state_fit()

        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)
        param2fit = []
        for item in self.param_toFit:
            if item[0] and item[0].IsShown():
                param2fit.append(item[1])
        self._manager.set_param2fit(self.uid, param2fit)

    def select_param(self, event=None):
        """
        Select TextCtrl  checked for fitting purpose and stores them
        in  self.param_toFit=[] list
        """
        self.param_toFit = []
        for item in self.parameters:
            # Skip t ifhe angle parameters if 1D data
            if self.data.__class__.__name__ != "Data2D" and\
                        not self.enable2D:
                if item in self.orientation_params:
                    continue
            # Select parameters to fit for list of primary parameters
            if item[0].GetValue() and item[0].IsShown():
                if not (item in self.param_toFit):
                    self.param_toFit.append(item)
            else:
                #remove parameters from the fitting list
                if item in self.param_toFit:
                    self.param_toFit.remove(item)

        # Select parameters to fit for list of fittable parameters
        #        with dispersion
        for item in self.fittable_param:
            # Skip t ifhe angle parameters if 1D data
            if self.data.__class__.__name__ != "Data2D" and\
                        not self.enable2D:
                if item in self.orientation_params:
                    continue
            if item[0].GetValue() and item[0].IsShown():
                if not (item in self.param_toFit):
                    self.param_toFit.append(item)
            else:
                # remove parameters from the fitting list
                if item in self.param_toFit:
                    self.param_toFit.remove(item)

        # Calculate num. of angle parameters
        if self.data.__class__.__name__ == "Data2D" or \
                       self.enable2D:
            len_orient_para = 0
        else:
            len_orient_para = len(self.orientation_params)  # assume even len
        # Total num. of angle parameters
        if len(self.fittable_param) > 0:
            len_orient_para *= 2

        self.save_current_state_fit()
        if event is not None:
            # post state to fit panel
            event = PageInfoEvent(page=self)
            wx.PostEvent(self.parent, event)

        param2fit = []
        for item in self.param_toFit:
            if item[0] and item[0].IsShown():
                param2fit.append(item[1])
        self._manager.set_param2fit(self.uid, param2fit)

    def set_model_param_sizer(self, model):
        """
        Build the panel from the model content

        :param model: the model selected in combo box for fitting purpose

        """
        self.sizer3.Clear(True)
        self.parameters = []
        self.str_parameters = []
        self.param_toFit = []
        self.fittable_param = []
        self.fixed_param = []
        self.orientation_params = []
        self.orientation_params_disp = []

        if model is None:
            self.sizer3.Layout()
            self.SetupScrolling()
            return

        box_description = wx.StaticBox(self, wx.ID_ANY, str("Model Parameters"))
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer = wx.GridBagSizer(5, 5)
        # save the current model
        self.model = model

        keys = self.model.getParamList()

        # list of dispersion parameters
        self.disp_list = self.model.getDispParamList()

        def custom_compare(a, b):
            """
            Custom compare to order, first by alphabets then second by number.
            """
            # number at the last digit
            a_last = a[len(a) - 1]
            b_last = b[len(b) - 1]
            # default
            num_a = None
            num_b = None
            # split the names
            a2 = a.lower().split('_')
            b2 = b.lower().split('_')
            # check length of a2, b2
            len_a2 = len(a2)
            len_b2 = len(b2)
            # check if it contains a int number(<10)
            try:
                num_a = int(a_last)
            except:
                pass
            try:
                num_b = int(b_last)
            except:
                pass
            # Put 'scale' near the top; happens
            # when numbered param name exists
            if a == 'scale':
                return -1
            # both have a number
            if num_a is not None and num_b is not None:
                if num_a > num_b:
                    return -1
                # same number
                elif num_a == num_b:
                    # different last names
                    if a2[len_a2 - 1] != b2[len_b2 - 1] and num_a != 0:
                        return -cmp(a2[len_a2 - 1], b2[len_b2 - 1])
                    else:
                        return cmp(a, b)
                else:
                    return 1
            # one of them has a number
            elif num_a is not None:
                return 1
            elif num_b is not None:
                return -1
            # no numbers
            else:
                return cmp(a.lower(), b.lower())

        # keys obtained now from ordered dict, so commenting alphabetical
        # ordering keys.sort(custom_compare)

        iy = 0
        ix = 0
        sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Parameter'),
                  (iy, ix), (1, 1), wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.text2_2 = wx.StaticText(self, wx.ID_ANY, 'Value')
        sizer.Add(self.text2_2, (iy, ix), (1, 1),
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 2
        self.text2_3 = wx.StaticText(self, wx.ID_ANY, 'Error')
        sizer.Add(self.text2_3, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        if not self.is_mac:
            self.text2_3.Hide()
        ix += 1
        self.text2_min = wx.StaticText(self, wx.ID_ANY, 'Min')
        sizer.Add(self.text2_min, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        # self.text2_min.Hide()
        ix += 1
        self.text2_max = wx.StaticText(self, wx.ID_ANY, 'Max')
        sizer.Add(self.text2_max, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        # self.text2_max.Hide()
        ix += 1
        self.text2_4 = wx.StaticText(self, wx.ID_ANY, '[Units]')
        sizer.Add(self.text2_4, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        self.text2_4.Hide()

        CHECK_STATE = False
        for item in keys:

            if item not in self.disp_list and not item in \
                    self.model.orientation_params:

                # prepare a spot to store errors
                if item not in self.model.details:
                    self.model.details[item] = ["", None, None]

                iy += 1
                ix = 0
                if (self.model.__class__ in
                    self.model_list_box["Multi-Functions"] or
                    self.temp_multi_functional)\
                    and (item in self.model.non_fittable):
                    non_fittable_name = wx.StaticText(self, wx.ID_ANY, item)
                    sizer.Add(non_fittable_name, (iy, ix), (1, 1),
                            wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 21)
                    # add parameter value
                    ix += 1
                    value = self.model.getParam(item)
                    if len(self.model.fun_list) > 0:
                        # num = item.split('_')[1][5:7]
                        fun_box = wx.ComboBox(self, wx.ID_ANY, size=(100, -1),
                                    style=wx.CB_READONLY, name='%s' % item)
                        self._set_fun_box_list(fun_box)
                        fun_box.SetSelection(0)
                        # self.fun_box.SetToolTipString("A function
                        #    describing the interface")
                        wx.EVT_COMBOBOX(fun_box, wx.ID_ANY, self._on_fun_box)
                    else:
                        fun_box = ModelTextCtrl(self, wx.ID_ANY,
                                                size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER, name='%s' % item)
                        fun_box.SetToolTipString(
                                "Hit 'Enter' after typing to update the plot.")
                        fun_box.SetValue(format_number(value, True))
                    sizer.Add(fun_box, (iy, ix), (1, 1), wx.EXPAND)
                    self.str_parameters.append([None, item, fun_box,
                                                None, None, None,
                                                None, None])
                else:
                    # add parameters name with checkbox for selecting to fit
                    cb = wx.CheckBox(self, wx.ID_ANY, item)
                    cb.SetValue(CHECK_STATE)
                    cb.SetToolTipString(" Check mark to fit.")
                    # cb.SetValue(True)
                    wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)

                    sizer.Add(cb, (iy, ix), (1, 1),
                              wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)

                    # add parameter value
                    ix += 1
                    value = self.model.getParam(item)
                    ctl1 = ModelTextCtrl(self, wx.ID_ANY, size=(_BOX_WIDTH, 20),
                                         style=wx.TE_PROCESS_ENTER)
                    ctl1.SetToolTipString(
                                "Hit 'Enter' after typing to update the plot.")
                    ctl1.SetValue(format_number(value, True))
                    sizer.Add(ctl1, (iy, ix), (1, 1), wx.EXPAND)
                    # text to show error sign
                    ix += 1
                    text2 = wx.StaticText(self, wx.ID_ANY, '+/-')
                    sizer.Add(text2, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                    if not self.is_mac:
                        text2.Hide()
                    ix += 1
                    ctl2 = wx.TextCtrl(self, wx.ID_ANY,
                                       size=(_BOX_WIDTH / 1.2, 20), style=0)
                    sizer.Add(ctl2, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                    if not self.is_mac:
                        ctl2.Hide()

                    ix += 1
                    ctl3 = ModelTextCtrl(self, wx.ID_ANY,
                                         size=(_BOX_WIDTH / 1.9, 20),
                                         style=wx.TE_PROCESS_ENTER,
                                text_enter_callback=self._onparamRangeEnter)
                    min_bound = self.model.details[item][1]
                    if min_bound is not None:
                        ctl3.SetValue(format_number(min_bound, True))

                    sizer.Add(ctl3, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                    ix += 1
                    ctl4 = ModelTextCtrl(self, wx.ID_ANY,
                                         size=(_BOX_WIDTH / 1.9, 20),
                                         style=wx.TE_PROCESS_ENTER,
                                text_enter_callback=self._onparamRangeEnter)
                    max_bound = self.model.details[item][2]
                    if max_bound is not None:
                        ctl4.SetValue(format_number(max_bound, True))
                    sizer.Add(ctl4, (iy, ix), (1, 1),
                              wx.EXPAND | wx.FIXED_MINSIZE, 0)

                    ix += 1
                    # Units
                    if item in self.model.details:
                        units = wx.StaticText(self, wx.ID_ANY,
                            self.model.details[item][0], style=wx.ALIGN_LEFT)
                    else:
                        units = wx.StaticText(self, wx.ID_ANY, "",
                                              style=wx.ALIGN_LEFT)
                    sizer.Add(units, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                    self.parameters.append([cb, item, ctl1,
                                            text2, ctl2, ctl3, ctl4, units])

        iy += 1
        sizer.Add((10, 10), (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

        # type can be either Guassian or Array
        if len(list(self.model.dispersion.values())) > 0:
            type = list(self.model.dispersion.values())[0]["type"]
        else:
            type = "Gaussian"

        iy += 1
        ix = 0
        # Add tile for orientational angle
        for item in keys:
            if item in self.model.orientation_params:
                orient_angle = wx.StaticText(self, wx.ID_ANY, '[For 2D only]:')
                mag_on_button = wx.Button(self, wx.ID_ANY, "Magnetic ON")
                mag_on_button.SetToolTipString("Turn Pol Beam/Mag scatt on/off")
                mag_on_button.Bind(wx.EVT_BUTTON, self._on_mag_on)
                mag_angle_help_button = wx.Button(self, wx.ID_ANY,
                                                  "Magnetic angles?")
                mag_angle_help_button.SetToolTipString("see angle definitions")
                mag_help_button = wx.Button(self, wx.ID_ANY, "Mag HELP")
                mag_help_button.SetToolTipString("Help on pol beam/mag fitting")
                mag_help_button.Bind(wx.EVT_BUTTON, self._on_mag_help)
                mag_angle_help_button.Bind(wx.EVT_BUTTON,
                                            self._on_mag_angle_help)
                sizer.Add(orient_angle, (iy, ix), (1, 1),
                          wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
                iy += 1
                sizer.Add(mag_on_button, (iy, ix), (1, 1),
                          wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
                ix += 1
                sizer.Add(mag_angle_help_button, (iy, ix), (1, 1),
                          wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
                sizer.Add(mag_help_button, (iy, ix + 1), (1, 1),
                          wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

                # handle the magnetic buttons
                # clean this up so that assume mag is off then turn
                # all buttons on IF mag has mag and has 2D
                if not self._has_magnetic:
                    mag_on_button.Show(False)
                elif not self.data.__class__.__name__ == "Data2D":
                    mag_on_button.Show(False)
                else:
                    mag_on_button.Show(True)
                mag_help_button.Show(False)
                mag_angle_help_button.Show(False)
                if mag_on_button.IsShown():
                    if self.magnetic_on:
                        mag_on_button.SetLabel("Magnetic OFF")
                        mag_help_button.Show(True)
                        mag_angle_help_button.Show(True)
                    else:
                        mag_on_button.SetLabel("Magnetic ON")
                        mag_help_button.Show(False)
                        mag_angle_help_button.Show(False)

                if not self.data.__class__.__name__ == "Data2D" and \
                        not self.enable2D:
                    orient_angle.Hide()
                else:
                    orient_angle.Show(True)
                break

        # For Gaussian only
        if type.lower() != "array":
            for item in self.model.orientation_params:
                if not self.magnetic_on:
                    if item in self.model.magnetic_params:
                        continue
                if item not in self.disp_list:
                    # prepare a spot to store min max
                    if item not in self.model.details:
                        self.model.details[item] = ["", None, None]

                    iy += 1
                    ix = 0
                    # add parameters name with checkbox for selecting to fit
                    cb = wx.CheckBox(self, wx.ID_ANY, item)
                    cb.SetValue(CHECK_STATE)
                    cb.SetToolTipString("Check mark to fit")
                    wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                    if self.data.__class__.__name__ == "Data2D" or \
                            self.enable2D:
                        cb.Show(True)
                    else:
                        cb.Hide()
                    sizer.Add(cb, (iy, ix), (1, 1),
                              wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)

                    # add parameter value
                    ix += 1
                    value = self.model.getParam(item)
                    ctl1 = ModelTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                         style=wx.TE_PROCESS_ENTER)
                    ctl1.SetToolTipString(
                                "Hit 'Enter' after typing to update the plot.")
                    ctl1.SetValue(format_number(value, True))
                    if self.data.__class__.__name__ == "Data2D" or \
                            self.enable2D:
                        ctl1.Show(True)
                    else:
                        ctl1.Hide()
                    sizer.Add(ctl1, (iy, ix), (1, 1), wx.EXPAND)
                    # text to show error sign
                    ix += 1
                    text2 = wx.StaticText(self, -1, '+/-')
                    sizer.Add(text2, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                    text2.Hide()
                    ix += 1
                    ctl2 = wx.TextCtrl(self, -1,
                                       size=(_BOX_WIDTH / 1.2, 20), style=0)
                    sizer.Add(ctl2, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                    ctl2.Hide()

                    ix += 1
                    ctl3 = ModelTextCtrl(self, -1,
                                         size=(_BOX_WIDTH / 1.8, 20),
                                         style=wx.TE_PROCESS_ENTER,
                                text_enter_callback=self._onparamRangeEnter)

                    sizer.Add(ctl3, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                    ctl3.Hide()

                    ix += 1
                    ctl4 = ModelTextCtrl(self, -1,
                                         size=(_BOX_WIDTH / 1.8, 20),
                                         style=wx.TE_PROCESS_ENTER,
                            text_enter_callback=self._onparamRangeEnter)
                    sizer.Add(ctl4, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                    ctl4.Hide()

                    if self.data.__class__.__name__ == "Data2D" or \
                            self.enable2D:
                        if self.is_mac:
                            text2.Show(True)
                            ctl2.Show(True)
                        ctl3.Show(True)
                        ctl4.Show(True)

                    ix += 1
                    # Units
                    if item in self.model.details:
                        units = wx.StaticText(self, -1,
                                              self.model.details[item][0],
                                              style=wx.ALIGN_LEFT)
                    else:
                        units = wx.StaticText(self, -1, "",
                                              style=wx.ALIGN_LEFT)
                    if self.data.__class__.__name__ == "Data2D" or \
                            self.enable2D:
                        units.Show(True)
                    else:
                        units.Hide()

                    sizer.Add(units, (iy, ix), (1, 1),
                              wx.EXPAND | wx.ADJUST_MINSIZE, 0)

                    self.parameters.append([cb, item, ctl1,
                                            text2, ctl2, ctl3, ctl4, units])
                    self.orientation_params.append([cb, item, ctl1,
                                            text2, ctl2, ctl3, ctl4, units])

        iy += 1
        box_description.SetForegroundColour(wx.BLUE)
        # Display units text on panel
        for item in keys:
            if item in self.model.details:
                self.text2_4.Show()
        # Fill the list of fittable parameters
        self.get_all_checked_params()
        self.save_current_state_fit()
        boxsizer1.Add(sizer)
        self.sizer3.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)
        self.sizer3.Layout()
        self.Layout()

    def on_right_down(self, event):
        """
        Get key stroke event
        """
        if self.data is None:
            return
        # Figuring out key combo: Cmd for copy, Alt for paste
        if event.AltDown() and event.ShiftDown():
            flag = True
        elif event.AltDown() or event.ShiftDown():
            flag = False
        else:
            return
        # make event free
        event.Skip()
        # messages depending on the flag
        if not flag:
            infor = 'warning'
            # inform msg to wx
            wx.PostEvent(self._manager.parent,
                        StatusEvent(status=msg, info=infor))

    def _onModel2D(self, event):
        """
        toggle view of model from 1D to 2D  or 2D from 1D
        """
        if self.model_view.GetLabelText() == "Show 2D":
            self.model_view.SetLabel("Show 1D")
            self.enable2D = True

        else:
            self.model_view.SetLabel("Show 2D")
            self.enable2D = False
        self.Show(False)
        self.create_default_data()
        self._manager.store_data(self.uid, data_list=[self.data])

        self.set_model_param_sizer(self.model)
        self._set_sizer_dispersion()
        self._set_weight(is_2D=self.enable2D)
        self._set_smear_buttons()
        self.Show(True)
        self.SetupScrolling()
        self._draw_model()

        self.state.enable2D = copy.deepcopy(self.enable2D)

    def _set_smear_buttons(self):
        """
        Set semarer radio buttons
        """
        # more disables for 2D
        if self.data.__class__.__name__ == "Data2D" or \
                    self.enable2D:
            self.slit_smearer.Disable()
            self.pinhole_smearer.Enable(True)
            self.default_mask = copy.deepcopy(self.data.mask)
        else:
            self.slit_smearer.Enable(True)
            self.pinhole_smearer.Enable(True)


class BGTextCtrl(wx.TextCtrl):
    """
    Text control used to display outputs.
    No editing allowed. The background is
    grayed out. User can't select text.
    """
    def __init__(self, *args, **kwds):
        wx.TextCtrl.__init__(self, *args, **kwds)
        self.SetEditable(False)
        self.SetBackgroundColour(self.GetParent().parent.GetBackgroundColour())

        # Bind to mouse event to avoid text highlighting
        # The event will be skipped once the call-back
        # is called.
        self.Bind(wx.EVT_MOUSE_EVENTS, self._click)

    def _click(self, event):
        """
        Prevent further handling of the mouse event
        by not calling Skip().
        """
        pass
