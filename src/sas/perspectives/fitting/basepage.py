"""
Base Page for fitting
"""
import sys
import os
import wx
import numpy
import time
import copy
import math
import string
import json
import logging
from collections import defaultdict
from wx.lib.scrolledpanel import ScrolledPanel
from sas.guiframe.panel_base import PanelBase
from sas.guiframe.utils import format_number, check_float, IdList
from sas.guiframe.events import PanelOnFocusEvent
from sas.guiframe.events import StatusEvent
from sas.guiframe.events import AppendBookmarkEvent
from sas.guiframe.dataFitting import Data2D
from sas.guiframe.dataFitting import Data1D
from sas.guiframe.dataFitting import check_data_validity
from sas.guiframe.gui_style import GUIFRAME_ID
from sas.dataloader.data_info import Detector
from sas.dataloader.data_info import Source
from sas.perspectives.fitting.pagestate import PageState
from sas.guiframe.CategoryInstaller import CategoryInstaller
from sas.guiframe.documentation_window import DocumentationWindow


(PageInfoEvent, EVT_PAGE_INFO) = wx.lib.newevent.NewEvent()
(PreviousStateEvent, EVT_PREVIOUS_STATE) = wx.lib.newevent.NewEvent()
(NextStateEvent, EVT_NEXT_STATE) = wx.lib.newevent.NewEvent()

_BOX_WIDTH = 76
_QMIN_DEFAULT = 0.0005
_QMAX_DEFAULT = 0.5
_NPTS_DEFAULT = 50
#Control panel width
if sys.platform.count("win32") > 0:
    PANEL_WIDTH = 450
    FONT_VARIANT = 0
    ON_MAC = False
else:
    PANEL_WIDTH = 500
    FONT_VARIANT = 1
    ON_MAC = True


class BasicPage(ScrolledPanel, PanelBase):
    """
    This class provide general structure of  fitpanel page
    """
    ## Internal name for the AUI manager
    window_name = "Fit Page"
    ## Title to appear on top of the window
    window_caption = "Fit Page "
    # These two buttons have specific IDs since they seem to be created more
    # frequently than they need to.  In particular, set_dispers_sizer() is
    # called by _on_select_model
    ID_BOOKMARK = wx.NewId()
    ID_DISPERSER_HELP = wx.NewId()
    _id_pool = IdList()

    def __init__(self, parent, color='blue', **kwargs):
        """
        """
        ScrolledPanel.__init__(self, parent, **kwargs)
        PanelBase.__init__(self, parent)
        self.SetupScrolling()
        #Set window's font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.SetBackgroundColour(color)

        self._ids = iter(self._id_pool)
        ## parent of the page
        self.parent = parent
        ## manager is the fitting plugin
        ## owner of the page (fitting plugin)
        self.event_owner = None
        ## current model
        self.model = None
        self.m_name = None
        self.index_model = None
        self.panel = None
        ## data
        self.data = None
        #list of available data
        self.data_list = []
        self.mask = None
        self.uid = wx.NewId()
        self.graph_id = None
        #Q range for data set
        self.qmin_data_set = numpy.inf
        self.qmax_data_set = None
        self.npts_data_set = 0
        ## Q range
        self.qmin = None
        self.qmax = None
        self.qmax_x = _QMAX_DEFAULT
        self.qmin_x = _QMIN_DEFAULT
        self.npts_x = _NPTS_DEFAULT
        ## total number of point: float
        self.npts = None
        self.num_points = None
        ## smear default
        self.current_smearer = None
        ## 2D smear accuracy default
        self.smear2d_accuracy = 'Low'
        ## slit smear:
        self.dxl = None
        self.dxw = None
        ## pinhole smear
        self.dx_min = None
        self.dx_max = None
        ##semar attrbs
        self.enable_smearer = None
        self.disable_smearer = None
        self.pinhole_smearer = None
        self.slit_smearer = None
        ##weigth attrbs
        self.dI_noweight = None
        self.dI_didata = None
        self.dI_sqrdata = None
        self.dI_idata = None
        ##other attrbs
        self.dq_l = None
        self.dq_r = None
        self.tcChi = None
        self.disp_box = None
        self.model_disp = None
        self.Npts_fit = None
        self.Npts_total = None
        self.theory_qmin = None
        self.theory_qmax = None
        self.theory_qmin_x = None
        self.theory_qmax_x = None
        self.cb1 = None
        self.btEditMask = None
        self.btFit = None
        self.sld_axes = None
        self.multi_factor = None

        self.disp_cb_dict = {}

        #self.state = PageState(parent=parent)
        ## dictionary containing list of models
        self.model_list_box = {}

        ## Data member to store the dispersion object created
        self._disp_obj_dict = {}
        ## selected parameters to apply dispersion
        self.disp_cb_dict = {}
        ## smearer object
        self.enable2D = False
        self._has_magnetic = False
        self.magnetic_on = False
        self.is_mac = ON_MAC
        self.formfactorbox = None
        self.structurebox = None
        self.categorybox = None
        ##list of model parameters. each item must have same length
        ## each item related to a given parameters
        ##[cb state, name, value, "+/-", error of fit, min, max , units]
        self.parameters = []
        # non-fittable parameter whose value is astring
        self.str_parameters = []
        ## list of parameters to fit , must be like self.parameters
        self.param_toFit = []
        ## list of looking like parameters but with non fittable parameters info
        self.fixed_param = []
        ## list of looking like parameters but with  fittable parameters info
        self.fittable_param = []
        ##list of dispersion parameters
        self.disp_list = []
        self.disp_name = ""

        ## list of orientation parameters
        self.orientation_params = []
        self.orientation_params_disp = []
#       Self.model should ALWAYS be None here.  It was set to none above in
#       this long init setting.  no obvious function call in between setting
#       and this - commenting out on 4/8/2014 by PDB.  Remove once clear
#       it is pointless.
#        if self.model != None:
#            self.disp_list = self.model.getDispParamList()
        self.temp_multi_functional = False
        ##enable model 2D draw
        self.enable2D = False
        ## check that the fit range is correct to plot the model again
        self.fitrange = True
        ## Create memento to save the current state
        self.state = PageState(parent=self.parent,
                               model=self.model, data=self.data)
        ## flag to determine if state has change
        self.state_change = False
        ## save customized array
        self.values = []
        self.weights = []
        ## retrieve saved state
        self.number_saved_state = 0
        ## dictionary of saved state
        self.saved_states = {}
        ## Create context menu for page
        self.popUpMenu = wx.Menu()

        wx_id = self._ids.next()
        self._keep = wx.MenuItem(self.popUpMenu, wx_id, "Add bookmark",
                                 " Keep the panel status to recall it later")
        self.popUpMenu.AppendItem(self._keep)
        self._keep.Enable(False)
        self._set_bookmark_flag(False)
        self._set_save_flag(False)
        wx.EVT_MENU(self, wx_id, self.on_bookmark)
        self.popUpMenu.AppendSeparator()

        ## Default locations
        self._default_save_location = os.getcwd()
        ## save initial state on context menu
        #self.onSave(event=None)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)

        # bind key event
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

        ## create the basic structure of the panel with empty sizer
        self.define_page_structure()
        ## drawing Initial dispersion parameters sizer
        self.set_dispers_sizer()

        ## layout
        self.set_layout()

    def set_index_model(self, index):
        """
        Index related to this page
        """
        self.index_model = index

    def create_default_data(self):
        """
        Given the user selection, creates a 1D or 2D data
        Only when the page is on theory mode.
        """
        if not hasattr(self, "model_view"):
            return
        toggle_mode_on = self.model_view.IsEnabled()
        if toggle_mode_on:
            if self.enable2D and not check_data_validity(self.data):
                self._create_default_2d_data()
            else:
                if self.pointsbox.GetValue():
                    self._create_log_1d_data()
                else:
                    self._create_default_1d_data()

            if self.model != None:
                if not self.data.is_data:
                    self._manager.page_finder[self.uid].set_fit_data(data=\
                                                                [self.data])
            self.on_smear_helper(update=True)
            self.state.enable_smearer = self.enable_smearer.GetValue()
            self.state.disable_smearer = self.disable_smearer.GetValue()
            self.state.pinhole_smearer = self.pinhole_smearer.GetValue()
            self.state.slit_smearer = self.slit_smearer.GetValue()

    def _create_default_1d_data(self):
        """
        Create default data for fitting perspective
        Only when the page is on theory mode.
        :warning: This data is never plotted.

        """
        x = numpy.linspace(start=self.qmin_x, stop=self.qmax_x,
                           num=self.npts_x, endpoint=True)
        self.data = Data1D(x=x)
        self.data.xaxis('\\rm{Q}', "A^{-1}")
        self.data.yaxis('\\rm{Intensity}', "cm^{-1}")
        self.data.is_data = False
        self.data.id = str(self.uid) + " data"
        self.data.group_id = str(self.uid) + " Model1D"

    def _create_log_1d_data(self):
        """
        Create log-spaced data for fitting perspective
        Only when the page is on theory mode.
        :warning: This data is never plotted.

        """
        if self.qmin_x >= 1.e-10:
            qmin = numpy.log10(self.qmin_x)
        else:
            qmin = -10.

        if self.qmax_x <= 1.e10:
            qmax = numpy.log10(self.qmax_x)
        else:
            qmax = 10.

        x = numpy.logspace(start=qmin, stop=qmax,
                           num=self.npts_x, endpoint=True, base=10.0)
        self.data = Data1D(x=x)
        self.data.xaxis('\\rm{Q}', "A^{-1}")
        self.data.yaxis('\\rm{Intensity}', "cm^{-1}")
        self.data.is_data = False
        self.data.id = str(self.uid) + " data"
        self.data.group_id = str(self.uid) + " Model1D"

    def _create_default_2d_data(self):
        """
        Create 2D data by default
        Only when the page is on theory mode.
        :warning: This data is never plotted.
        """
        self.data = Data2D()
        qmax = self.qmax_x / math.sqrt(2)
        self.data.xaxis('\\rm{Q_{x}}', 'A^{-1}')
        self.data.yaxis('\\rm{Q_{y}}', 'A^{-1}')
        self.data.is_data = False
        self.data.id = str(self.uid) + " data"
        self.data.group_id = str(self.uid) + " Model2D"
        ## Default values
        self.data.detector.append(Detector())
        index = len(self.data.detector) - 1
        self.data.detector[index].distance = 8000   # mm
        self.data.source.wavelength = 6             # A
        self.data.detector[index].pixel_size.x = 5  # mm
        self.data.detector[index].pixel_size.y = 5  # mm
        self.data.detector[index].beam_center.x = qmax
        self.data.detector[index].beam_center.y = qmax
        ## create x_bins and y_bins of the model 2D
        #pixel_width_x = self.data.detector[index].pixel_size.x
        #pixel_width_y = self.data.detector[index].pixel_size.y
        #center_x = self.data.detector[index].beam_center.x/pixel_width_x
        #center_y = self.data.detector[index].beam_center.y/pixel_width_y
        # theory default: assume the beam
        #center is located at the center of sqr detector
        xmax = qmax
        xmin = -qmax
        ymax = qmax
        ymin = -qmax
        qstep = self.npts_x

        x = numpy.linspace(start=xmin, stop=xmax, num=qstep, endpoint=True)
        y = numpy.linspace(start=ymin, stop=ymax, num=qstep, endpoint=True)
        ## use data info instead
        new_x = numpy.tile(x, (len(y), 1))
        new_y = numpy.tile(y, (len(x), 1))
        new_y = new_y.swapaxes(0, 1)
        # all data reuire now in 1d array
        qx_data = new_x.flatten()
        qy_data = new_y.flatten()
        q_data = numpy.sqrt(qx_data * qx_data + qy_data * qy_data)
        # set all True (standing for unmasked) as default
        mask = numpy.ones(len(qx_data), dtype=bool)
        # calculate the range of qx and qy: this way,
        # it is a little more independent
        #x_size = xmax - xmin
        #y_size = ymax - ymin
        # store x and y bin centers in q space
        x_bins = x
        y_bins = y
        # bin size: x- & y-directions
        #xstep = x_size / len(x_bins - 1)
        #ystep = y_size / len(y_bins - 1)

        self.data.source = Source()
        self.data.data = numpy.ones(len(mask))
        self.data.err_data = numpy.ones(len(mask))
        self.data.qx_data = qx_data
        self.data.qy_data = qy_data
        self.data.q_data = q_data
        self.data.mask = mask
        self.data.x_bins = x_bins
        self.data.y_bins = y_bins
        # max and min taking account of the bin sizes
        self.data.xmin = xmin
        self.data.xmax = xmax
        self.data.ymin = ymin
        self.data.ymax = ymax

    def on_set_focus(self, event):
        """
        On Set Focus, update guimanger and menu
        """
        if self._manager is not None:
            wx.PostEvent(self._manager.parent, PanelOnFocusEvent(panel=self))
            self.on_tap_focus()

    def on_tap_focus(self):
        """
        Update menu1 on cliking the page tap
        """
        if self._manager.menu1 != None:
            chain_menu = self._manager.menu1.FindItemById(\
                                                   self._manager.id_reset_flag)
            chain_menu.Enable(self.batch_on)
            sim_menu = self._manager.menu1.FindItemById(self._manager.id_simfit)
            flag = self.data.is_data\
                            and (self.model != None)
            sim_menu.Enable(not self.batch_on and flag)
            batch_menu = \
                    self._manager.menu1.FindItemById(self._manager.id_batchfit)
            batch_menu.Enable(self.batch_on and flag)

    def set_page_info(self, page_info):
        """
        set some page important information at once
        """
#       THIS METHOD/FUNCTION NO LONGE APPEARS TO BE CALLED.  Started up program
#       and started new fit window and PR and Invariant and a fit in fitting
#       but never entered this routine which should be an initialization
#       routine.  Leave for a while but probably something to clean up at
#       some point?
#
#       PDB April 13 2014
#
        ##window_name
        self.window_name = page_info.window_name
        ##window_caption
        self.window_caption = page_info.window_caption
        ## manager is the fitting plugin
        self._manager = page_info.manager
        ## owner of the page (fitting plugin)
        self.event_owner = page_info.event_owner
        ## current model
        self.model = page_info.model
        ## data
        self.data = page_info.data
        ## dictionary containing list of models
        self.model_list_box = page_info.model_list_box
        ## Data member to store the dispersion object created
        self.populate_box(model_dict=self.model_list_box)

    def onContextMenu(self, event):
        """
        Retrieve the state selected state
        """
        # Skipping the save state functionality for release 0.9.0
        #return

        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)

        self.PopupMenu(self.popUpMenu, pos)

    def onUndo(self, event):
        """
        Cancel the previous action
        """
        event = PreviousStateEvent(page=self)
        wx.PostEvent(self.parent, event)

    def onRedo(self, event):
        """
        Restore the previous action cancelled
        """
        event = NextStateEvent(page=self)
        wx.PostEvent(self.parent, event)

    def define_page_structure(self):
        """
        Create empty sizer for a panel
        """
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.sizer0 = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer3 = wx.BoxSizer(wx.VERTICAL)
        self.sizer4 = wx.BoxSizer(wx.VERTICAL)
        self.sizer5 = wx.BoxSizer(wx.VERTICAL)
        self.sizer6 = wx.BoxSizer(wx.VERTICAL)

        self.sizer0.SetMinSize((PANEL_WIDTH, -1))
        self.sizer1.SetMinSize((PANEL_WIDTH, -1))
        self.sizer2.SetMinSize((PANEL_WIDTH, -1))
        self.sizer3.SetMinSize((PANEL_WIDTH, -1))
        self.sizer4.SetMinSize((PANEL_WIDTH, -1))
        self.sizer5.SetMinSize((PANEL_WIDTH, -1))
        self.sizer6.SetMinSize((PANEL_WIDTH, -1))

        self.vbox.Add(self.sizer0)
        self.vbox.Add(self.sizer1)
        self.vbox.Add(self.sizer2)
        self.vbox.Add(self.sizer3)
        self.vbox.Add(self.sizer4)
        self.vbox.Add(self.sizer5)
        self.vbox.Add(self.sizer6)

    def set_layout(self):
        """
        layout
        """
        self.vbox.Layout()
        self.vbox.Fit(self)
        self.SetSizer(self.vbox)
        self.Centre()

    def set_owner(self, owner):
        """
        set owner of fitpage

        :param owner: the class responsible of plotting

        """
        self.event_owner = owner
        self.state.event_owner = owner

    def get_state(self):
        """
        return the current page state
        """
        return self.state

    def get_data(self):
        """
        return the current data
        """
        return self.data

    def get_data_list(self):
        """
        return the current data
        """
        return self.data_list

    def set_manager(self, manager):
        """
        set panel manager

        :param manager: instance of plugin fitting

        """
        self._manager = manager
        self.state.manager = manager

    def populate_box(self, model_dict):
        """
        Store list of model

        :param model_dict: dictionary containing list of models

        """
        self.model_list_box = model_dict
        self.state.model_list_box = self.model_list_box
        self.initialize_combox()

    def set_model_dictionary(self, model_dict):
        """
        Store a dictionary linking model name -> model object

        :param model_dict: dictionary containing list of models
        """
        self.model_dict = model_dict

    def initialize_combox(self):
        """
        put default value in the combobox
        """
        ## fill combox box
        if self.model_list_box is None:
            return
        if len(self.model_list_box) > 0:
        ## This is obsolete code since form factor box is no longer static.
        ## It is now set dynamically through _show_combox and _show_combos_helper
        ## These are called for first time by formfactor_combo_init
        ## itself called from fitpanel only.  If we find that I'm wrong and
        ## we DO need to initialize somehow here - do it by a call to
        ## formfactor_combo_init
        ## self.formfator_combo_init()
        ## BUT NOT HERE -- make it last line of this
        ## method so that structure box is populated before _show_comboox_helper
        ## is called.  Otherwise wx will complain mightily:-)
        ##
        ## Also change the name to initiatlize_structurebox along with changes
        ## to other combobox methods (_populate_listbox --> _populate_categorybox
        ## etc )
        ##
        ##     PDB 4/26/2014
#            self._populate_box(self.formfactorbox,
#                               self.model_list_box["Shapes"])
            self._populate_box(self.structurebox,
                               self.model_list_box["Structure Factors"])
            self.structurebox.Insert("None", 0, None)
            self.structurebox.SetSelection(0)
            self.structurebox.Hide()
            self.text2.Hide()
            self.structurebox.Disable()
            self.text2.Disable()

            if self.model.__class__ in self.model_list_box["P(Q)*S(Q)"]:
                self.structurebox.Show()
                self.text2.Show()
                self.structurebox.Enable()
                self.text2.Enable()


    def set_dispers_sizer(self):
        """
        fill sizer containing dispersity info
        """
        #print "==== entering set_dispers_sizer ==="
        self.sizer4.Clear(True)
        name = "Polydispersity and Orientational Distribution"
        box_description = wx.StaticBox(self, wx.ID_ANY, name)
        box_description.SetForegroundColour(wx.BLUE)
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        #----------------------------------------------------
        self.disable_disp = wx.RadioButton(self, wx.ID_ANY, 'Off', (10, 10),
                                           style=wx.RB_GROUP)
        self.enable_disp = wx.RadioButton(self, wx.ID_ANY, 'On', (10, 30))
        # best size for MAC and PC
        if ON_MAC:
            size_q = (30, 20)
        else:
            size_q = (20, 15)
        self.disp_help_bt = wx.Button(self, self.ID_DISPERSER_HELP, '?',
                                      style=wx.BU_EXACTFIT,
                                      size=size_q)
        self.disp_help_bt.Bind(wx.EVT_BUTTON, self.on_pd_help_clicked,
                               id=self.disp_help_bt.GetId())
        self.disp_help_bt.SetToolTipString("Helps for Polydispersion.")

        self.Bind(wx.EVT_RADIOBUTTON, self._set_dipers_Param,
                  id=self.disable_disp.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self._set_dipers_Param,
                  id=self.enable_disp.GetId())
        #MAC needs SetValue
        self.disable_disp.SetValue(True)
        sizer_dispersion = wx.BoxSizer(wx.HORIZONTAL)
        sizer_dispersion.Add((20, 20))
        name = ""  # Polydispersity and \nOrientational Distribution "
        sizer_dispersion.Add(wx.StaticText(self, wx.ID_ANY, name))
        sizer_dispersion.Add(self.enable_disp)
        sizer_dispersion.Add((20, 20))
        sizer_dispersion.Add(self.disable_disp)
        sizer_dispersion.Add((25, 20))
        sizer_dispersion.Add(self.disp_help_bt)

        ## fill a sizer for dispersion
        boxsizer1.Add(sizer_dispersion, 0,
                      wx.TOP|wx.BOTTOM|wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE,
                      border=5)
        self.sizer4_4 = wx.GridBagSizer(6, 5)

        boxsizer1.Add(self.sizer4_4)
        #-----------------------------------------------------
        self.sizer4.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)
        self.sizer4_4.Layout()
        self.sizer4.Layout()
        self.Layout()

        self.Refresh()
        ## saving the state of enable dispersity button
        self.state.enable_disp = self.enable_disp.GetValue()
        self.state.disable_disp = self.disable_disp.GetValue()
        self.SetupScrolling()

    def onResetModel(self, event):
        """
        Reset model state
        """
        menu = event.GetEventObject()
        ## post help message for the selected model
        msg = menu.GetHelpString(event.GetId())
        msg += " reloaded"
        wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        self.Show(False)
        name = menu.GetLabel(event.GetId())
        self._on_select_model_helper()
        if self.model != None:
            self.m_name = self.model.name
        if name in self.saved_states.keys():
            previous_state = self.saved_states[name]
            ## reset state of checkbox,textcrtl  and  regular parameters value

            self.reset_page(previous_state)
        self.state.m_name = self.m_name
        self.Show(True)

    def on_preview(self, event):
        """
        Report the current fit results
        """
        # Get plot image from plotpanel
        images, canvases = self.get_images()
        # get the report dialog
        self.state.report(images, canvases)

    def on_save(self, event):
        """
        Save the current state into file
        """
        self.save_current_state()
        new_state = self.state.clone()
        # Ask the user the location of the file to write to.
        path = None
        if self.parent != None:
            self._default_save_location = \
                        self._manager.parent._default_save_location
        dlg = wx.FileDialog(self, "Choose a file", self._default_save_location,
                            self.window_caption, "*.fitv", wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self._default_save_location = os.path.dirname(path)
            self._manager.parent._default_save_location = \
                                self._default_save_location
        else:
            return None
        # MAC always needs the extension for saving
        extens = ".fitv"
        # Make sure the ext included in the file name
        fName = os.path.splitext(path)[0] + extens
        #the manager write the state into file
        self._manager.save_fit_state(filepath=fName, fitstate=new_state)
        return new_state

    def on_copy(self, event):
        """
        Copy Parameter values to the clipboad
        """
        if event != None:
            event.Skip()
        # It seems MAC needs wxCallAfter
        if event.GetId() == GUIFRAME_ID.COPYEX_ID:
            print "copy excel"
            wx.CallAfter(self.get_copy_excel)
        elif event.GetId() == GUIFRAME_ID.COPYLAT_ID:
            print "copy latex"
            wx.CallAfter(self.get_copy_latex)
        else:
            wx.CallAfter(self.get_copy)


    def on_paste(self, event):
        """
        Paste Parameter values to the panel if possible
        """
        #if event != None:
        #    event.Skip()
        # It seems MAC needs wxCallAfter for the setvalues
        # for multiple textctrl items, otherwise it tends to crash once a while
        wx.CallAfter(self.get_paste)
        # messages depending on the flag
        #self._copy_info(True)

    def _copy_info(self, flag):
        """
        Send event dpemding on flag

        : Param flag: flag that distinguish event
        """
        # messages depending on the flag
        if flag == None:
            msg = " Parameter values are copied to the clipboard..."
            infor = 'warning'
        elif flag:
            msg = " Parameter values are pasted from the clipboard..."
            infor = "warning"
        else:
            msg = "Error occurred: "
            msg += "No valid parameter values to paste from the clipboard..."
            infor = "warning"
        # inform msg to wx
        wx.PostEvent(self._manager.parent,
                     StatusEvent(status=msg, info=infor))

    def _get_time_stamp(self):
        """
        return time and date stings
        """
        # date and time
        year, month, day, hour, minute, second, _, _, _ = time.localtime()
        current_time = str(hour) + ":" + str(minute) + ":" + str(second)
        current_date = str(month) + "/" + str(day) + "/" + str(year)
        return current_time, current_date

    def on_bookmark(self, event):
        """
        save history of the data and model
        """
        if self.model == None:
            msg = "Can not bookmark; Please select Data and Model first..."
            wx.MessageBox(msg, 'Info')
            return
        self.save_current_state()
        new_state = self.state.clone()
        ##Add model state on context menu
        self.number_saved_state += 1
        current_time, current_date = self._get_time_stamp()
        #name= self.model.name+"[%g]"%self.number_saved_state
        name = "Fitting: %g]" % self.number_saved_state
        name += self.model.__class__.__name__
        name += "bookmarked at %s on %s" % (current_time, current_date)
        self.saved_states[name] = new_state

        ## Add item in the context menu
        msg = "Model saved at %s on %s" % (current_time, current_date)
        ## post help message for the selected model
        msg += " Saved! right click on this page to retrieve this model"
        wx.PostEvent(self._manager.parent, StatusEvent(status=msg))

        self.popUpMenu.Append(self.ID_BOOKMARK, name, str(msg))
        wx.EVT_MENU(self, self.ID_BOOKMARK, self.onResetModel)
        wx.PostEvent(self._manager.parent,
                     AppendBookmarkEvent(title=name,
                                         hint=str(msg),
                                         handler=self._back_to_bookmark))

    def _back_to_bookmark(self, event):
        """
        Back to bookmark
        """
        self._manager.on_perspective(event)
        self.onResetModel(event)
        self._draw_model()

    def onSetFocus(self, evt):
        """
        highlight the current textcrtl and hide the error text control shown
        after fitting
        """
        return

    def read_file(self, path):
        """
        Read two columns file

        :param path: the path to the file to read

        """
        try:
            if path == None:
                status = " Selected Distribution was not loaded: %s" % path
                wx.PostEvent(self._manager.parent,
                             StatusEvent(status=status))
                return None, None
            input_f = open(path, 'r')
            buff = input_f.read()
            lines = buff.split('\n')
            input_f.close()
            angles = []
            weights = []
            for line in lines:
                toks = line.split()
                try:
                    angle = float(toks[0])
                    weight = float(toks[1])
                    angles.append(angle)
                    weights.append(weight)
                except:
                    # Skip non-data lines
                    logging.error(sys.exc_info()[1])
            return numpy.array(angles), numpy.array(weights)
        except:
            raise

    def createMemento(self):
        """
        return the current state of the page
        """
        return self.state.clone()

    def save_current_state(self):
        """
        Store current state
        """
        ## save model option
        if self.model != None:
            self.disp_list = self.model.getDispParamList()
            self.state.disp_list = copy.deepcopy(self.disp_list)
            self.state.model = self.model.clone()

            #model combobox: complex code because of mac's silent error
            if self.structurebox != None:
                if self.structurebox.IsShown():
                    self.state.structurecombobox = 'None'
                    s_select = self.structurebox.GetSelection()
                    if s_select > 0:
                        self.state.structurecombobox = self.structurebox.\
                        GetString(s_select)
            if self.formfactorbox != None:
                f_select = self.formfactorbox.GetSelection()
                if f_select > 0:
                    self.state.formfactorcombobox = self.formfactorbox.\
                    GetString(f_select)
        if self.categorybox != None:
            cb_select = self.categorybox.GetSelection()
            if cb_select > 0:
                self.state.categorycombobox = self.categorybox.\
                GetString(cb_select)

        self.state.enable2D = copy.deepcopy(self.enable2D)
        self.state.values = copy.deepcopy(self.values)
        self.state.weights = copy.deepcopy(self.weights)
        ## save data
        self.state.data = copy.deepcopy(self.data)
        self.state.qmax_x = self.qmax_x
        self.state.qmin_x = self.qmin_x
        self.state.dI_noweight = copy.deepcopy(self.dI_noweight.GetValue())
        self.state.dI_didata = copy.deepcopy(self.dI_didata.GetValue())
        self.state.dI_sqrdata = copy.deepcopy(self.dI_sqrdata.GetValue())
        self.state.dI_idata = copy.deepcopy(self.dI_idata.GetValue())
        self.state.dq_l = self.dq_l
        self.state.dq_r = self.dq_r
        if hasattr(self, "enable_disp"):
            self.state.enable_disp = self.enable_disp.GetValue()
            self.state.disable_disp = self.disable_disp.GetValue()

        self.state.smearer = copy.deepcopy(self.current_smearer)
        if hasattr(self, "enable_smearer"):
            self.state.enable_smearer = \
                                copy.deepcopy(self.enable_smearer.GetValue())
            self.state.disable_smearer = \
                                copy.deepcopy(self.disable_smearer.GetValue())

        self.state.pinhole_smearer = \
                                copy.deepcopy(self.pinhole_smearer.GetValue())
        self.state.dx_max = copy.deepcopy(self.dx_max)
        self.state.dx_min = copy.deepcopy(self.dx_min)
        self.state.dxl = copy.deepcopy(self.dxl)
        self.state.dxw = copy.deepcopy(self.dxw)
        self.state.slit_smearer = copy.deepcopy(self.slit_smearer.GetValue())

        if len(self._disp_obj_dict) > 0:
            for k, v in self._disp_obj_dict.iteritems():
                self.state._disp_obj_dict[k] = v

            self.state.values = copy.deepcopy(self.values)
            self.state.weights = copy.deepcopy(self.weights)
        ## save plotting range
        self._save_plotting_range()

        self.state.orientation_params = []
        self.state.orientation_params_disp = []
        self.state.parameters = []
        self.state.fittable_param = []
        self.state.fixed_param = []
        self.state.str_parameters = []

        ## save checkbutton state and txtcrtl values
        self._copy_parameters_state(self.str_parameters,
                                    self.state.str_parameters)
        self._copy_parameters_state(self.orientation_params,
                                     self.state.orientation_params)
        self._copy_parameters_state(self.orientation_params_disp,
                                     self.state.orientation_params_disp)

        self._copy_parameters_state(self.parameters, self.state.parameters)
        self._copy_parameters_state(self.fittable_param,
                                     self.state.fittable_param)
        self._copy_parameters_state(self.fixed_param, self.state.fixed_param)
        #save chisqr
        self.state.tcChi = self.tcChi.GetValue()

    def save_current_state_fit(self):
        """
        Store current state for fit_page
        """
        ## save model option
        if self.model != None:
            self.disp_list = self.model.getDispParamList()
            self.state.disp_list = copy.deepcopy(self.disp_list)
            self.state.model = self.model.clone()

        self.state.enable2D = copy.deepcopy(self.enable2D)
        self.state.values = copy.deepcopy(self.values)
        self.state.weights = copy.deepcopy(self.weights)
        ## save data
        self.state.data = copy.deepcopy(self.data)

        if hasattr(self, "enable_disp"):
            self.state.enable_disp = self.enable_disp.GetValue()
            self.state.disable_disp = self.disable_disp.GetValue()

        self.state.smearer = copy.deepcopy(self.current_smearer)
        if hasattr(self, "enable_smearer"):
            self.state.enable_smearer = \
                                copy.deepcopy(self.enable_smearer.GetValue())
            self.state.disable_smearer = \
                                copy.deepcopy(self.disable_smearer.GetValue())

        self.state.pinhole_smearer = \
                                copy.deepcopy(self.pinhole_smearer.GetValue())
        self.state.slit_smearer = copy.deepcopy(self.slit_smearer.GetValue())
        self.state.dI_noweight = copy.deepcopy(self.dI_noweight.GetValue())
        self.state.dI_didata = copy.deepcopy(self.dI_didata.GetValue())
        self.state.dI_sqrdata = copy.deepcopy(self.dI_sqrdata.GetValue())
        self.state.dI_idata = copy.deepcopy(self.dI_idata.GetValue())
        if hasattr(self, "disp_box") and self.disp_box != None:
            self.state.disp_box = self.disp_box.GetCurrentSelection()

            if len(self.disp_cb_dict) > 0:
                for k, v in self.disp_cb_dict.iteritems():
                    if v == None:
                        self.state.disp_cb_dict[k] = v
                    else:
                        try:
                            self.state.disp_cb_dict[k] = v.GetValue()
                        except:
                            self.state.disp_cb_dict[k] = None
            if len(self._disp_obj_dict) > 0:
                for k, v in self._disp_obj_dict.iteritems():
                    self.state._disp_obj_dict[k] = v

            self.state.values = copy.deepcopy(self.values)
            self.state.weights = copy.deepcopy(self.weights)

        ## save plotting range
        self._save_plotting_range()

        ## save checkbutton state and txtcrtl values
        self._copy_parameters_state(self.orientation_params,
                                    self.state.orientation_params)
        self._copy_parameters_state(self.orientation_params_disp,
                                    self.state.orientation_params_disp)
        self._copy_parameters_state(self.parameters, self.state.parameters)
        self._copy_parameters_state(self.fittable_param,
                                    self.state.fittable_param)
        self._copy_parameters_state(self.fixed_param, self.state.fixed_param)

    def check_invalid_panel(self):
        """
        check if the user can already perform some action with this panel
        """
        if self.data is None:
            self.disable_smearer.SetValue(True)
            self.disable_disp.SetValue(True)
            msg = "Please load Data and select Model to start..."
            wx.MessageBox(msg, 'Info')
            return  True

    def set_model_state(self, state):
        """
        reset page given a model state
        """
        self.disp_cb_dict = state.disp_cb_dict
        self.disp_list = state.disp_list

        ## set the state of the radio box
        #self.shape_rbutton.SetValue(state.shape_rbutton)
        #self.shape_indep_rbutton.SetValue(state.shape_indep_rbutton)
        #self.struct_rbutton.SetValue(state.struct_rbutton)
        #self.plugin_rbutton.SetValue(state.plugin_rbutton)

        ## fill model combobox
        self._show_combox_helper()
        #select the current model
        try:
            # to support older version
            category_pos = int(state.categorycombobox)
        except:
            category_pos = 0
            for ind_cat in range(self.categorybox.GetCount()):
                if self.categorycombobox.GetString(ind_cat) == \
                                        state.categorycombobox:
                    category_pos = int(ind_cat)
                    break

        self.categorybox.Select(category_pos)
        try:
            # to support older version
            formfactor_pos = int(state.formfactorcombobox)
        except:
            formfactor_pos = 0
            for ind_form in range(self.formfactorbox.GetCount()):
                if self.formfactorbox.GetString(ind_form) == \
                                        state.formfactorcombobox:
                    formfactor_pos = int(ind_form)
                    break

        self.formfactorbox.Select(formfactor_pos)

        try:
            # to support older version
            structfactor_pos = int(state.structurecombobox)
        except:
            structfactor_pos = 0
            for ind_struct in range(self.structurebox.GetCount()):
                if self.structurebox.GetString(ind_struct) == \
                                        state.structurecombobox:
                    structfactor_pos = int(ind_struct)
                    break

        self.structurebox.SetSelection(structfactor_pos)

        if state.multi_factor != None:
            self.multifactorbox.SetSelection(state.multi_factor)

        ## reset state of checkbox,textcrtl  and  regular parameters value
        self._reset_parameters_state(self.orientation_params_disp,
                                     state.orientation_params_disp)
        self._reset_parameters_state(self.orientation_params,
                                     state.orientation_params)
        self._reset_parameters_state(self.str_parameters,
                                     state.str_parameters)
        self._reset_parameters_state(self.parameters, state.parameters)
        ## display dispersion info layer
        self.enable_disp.SetValue(state.enable_disp)
        self.disable_disp.SetValue(state.disable_disp)

        if hasattr(self, "disp_box") and self.disp_box != None:
            self.disp_box.SetSelection(state.disp_box)
            n = self.disp_box.GetCurrentSelection()
            dispersity = self.disp_box.GetClientData(n)
            name = dispersity.__name__

            self._set_dipers_Param(event=None)

            if name == "ArrayDispersion":

                for item in self.disp_cb_dict.keys():

                    if hasattr(self.disp_cb_dict[item], "SetValue"):
                        self.disp_cb_dict[item].SetValue(\
                                                    state.disp_cb_dict[item])
                        # Create the dispersion objects
                        from sas.models.dispersion_models import ArrayDispersion
                        disp_model = ArrayDispersion()
                        if hasattr(state, "values") and \
                                 self.disp_cb_dict[item].GetValue() == True:
                            if len(state.values) > 0:
                                self.values = state.values
                                self.weights = state.weights
                                disp_model.set_weights(self.values,
                                                       state.weights)
                            else:
                                self._reset_dispersity()

                        self._disp_obj_dict[item] = disp_model
                        # Set the new model as the dispersion object
                        #for the selected parameter
                        self.model.set_dispersion(item, disp_model)

                        self.model._persistency_dict[item] = \
                                                [state.values, state.weights]

            else:
                keys = self.model.getParamList()
                for item in keys:
                    if item in self.disp_list and \
                        not item in self.model.details:
                        self.model.details[item] = ["", None, None]
                self.disp_cb_dict = copy.deepcopy(state.disp_cb_dict)
                self.state.disp_cb_dict = copy.deepcopy(state.disp_cb_dict)
        ## smearing info  restore
        if hasattr(self, "enable_smearer"):
            ## set smearing value whether or not the data
            #contain the smearing info
            self.enable_smearer.SetValue(state.enable_smearer)
            self.disable_smearer.SetValue(state.disable_smearer)
            self.onSmear(event=None)
        self.pinhole_smearer.SetValue(state.pinhole_smearer)
        self.slit_smearer.SetValue(state.slit_smearer)

        self.dI_noweight.SetValue(state.dI_noweight)
        self.dI_didata.SetValue(state.dI_didata)
        self.dI_sqrdata.SetValue(state.dI_sqrdata)
        self.dI_idata.SetValue(state.dI_idata)

        ## we have two more options for smearing
        if self.pinhole_smearer.GetValue():
            self.onPinholeSmear(event=None)
        elif self.slit_smearer.GetValue():
            self.onSlitSmear(event=None)

        ## reset state of checkbox,textcrtl  and dispersity parameters value
        self._reset_parameters_state(self.fittable_param, state.fittable_param)
        self._reset_parameters_state(self.fixed_param, state.fixed_param)

        ## draw the model with previous parameters value
        self._onparamEnter_helper()
        self.select_param(event=None)
        #Save state_fit
        self.save_current_state_fit()
        self._lay_out()
        self.Refresh()

    def reset_page_helper(self, state):
        """
        Use page_state and change the state of existing page

        :precondition: the page is already drawn or created

        :postcondition: the state of the underlying data change as well as the
            state of the graphic interface
        """
        if state == None:
            return
        # set data, etc. from the state
        # reset page between theory and fitting from bookmarking
        #if state.data == None:
        #    data = None
        #else:
        data = state.data

        if data == None:
            data_min = state.qmin
            data_max = state.qmax
            self.qmin_x = data_min
            self.qmax_x = data_max
            self.qmin.SetValue(str(data_min))
            self.qmax.SetValue(str(data_max))

            self.state.data = data
            self.state.qmin = self.qmin_x
            self.state.qmax = self.qmax_x
        else:
            self.set_data(data)

        self.enable2D = state.enable2D
        try:
            self.magnetic_on = state.magnetic_on
        except:
            # Backward compatibility (for older state files)
            self.magnetic_on = False

        self.disp_cb_dict = state.disp_cb_dict
        self.disp_list = state.disp_list

        ## set the state of the radio box
        #self.shape_rbutton.SetValue(state.shape_rbutton)
        #self.shape_indep_rbutton.SetValue(state.shape_indep_rbutton)
        #self.struct_rbutton.SetValue(state.struct_rbutton)
        #self.plugin_rbutton.SetValue(state.plugin_rbutton)

        ## fill model combobox
        self._show_combox_helper()
        #select the current model
        try:
            # to support older version
            category_pos = int(state.categorycombobox)
        except:
            category_pos = 0
            for ind_cat in range(self.categorybox.GetCount()):
                if self.categorybox.GetString(ind_cat) == \
                                        state.categorycombobox:
                    category_pos = int(ind_cat)
                    break

        self.categorybox.Select(category_pos)
        self._show_combox(None)
        try:
            # to support older version
            formfactor_pos = int(state.formfactorcombobox)
        except:
            formfactor_pos = 0
            for ind_form in range(self.formfactorbox.GetCount()):
                if self.formfactorbox.GetString(ind_form) == \
                                                    (state.formfactorcombobox):
                    formfactor_pos = int(ind_form)
                    break

        self.formfactorbox.Select(formfactor_pos)

        try:
            # to support older version
            structfactor_pos = int(state.structurecombobox)
        except:
            structfactor_pos = 0
            for ind_struct in range(self.structurebox.GetCount()):
                if self.structurebox.GetString(ind_struct) == \
                                                    (state.structurecombobox):
                    structfactor_pos = int(ind_struct)
                    break

        self.structurebox.SetSelection(structfactor_pos)

        if state.multi_factor != None:
            self.multifactorbox.SetSelection(state.multi_factor)

        #draw the panel according to the new model parameter
        self._on_select_model(event=None)

        # take care of 2D button
        if data == None and self.model_view.IsEnabled():
            if self.enable2D:
                self.model_view.SetLabel("2D Mode")
            else:
                self.model_view.SetLabel("1D Mode")
        
        ## set the select all check box to the a given state
        self.cb1.SetValue(state.cb1)

        ## reset state of checkbox,textcrtl  and  regular parameters value
        self._reset_parameters_state(self.orientation_params_disp,
                                     state.orientation_params_disp)
        self._reset_parameters_state(self.orientation_params,
                                     state.orientation_params)
        self._reset_parameters_state(self.str_parameters,
                                     state.str_parameters)
        self._reset_parameters_state(self.parameters, state.parameters)
        ## display dispersion info layer
        self.enable_disp.SetValue(state.enable_disp)
        self.disable_disp.SetValue(state.disable_disp)
        # If the polydispersion is ON
        if state.enable_disp:
            # reset dispersion according the state
            self._set_dipers_Param(event=None)
            self._reset_page_disp_helper(state)
        ##plotting range restore
        self._reset_plotting_range(state)
        ## smearing info  restore
        if hasattr(self, "enable_smearer"):
            ## set smearing value whether or not the data
            #contain the smearing info
            self.enable_smearer.SetValue(state.enable_smearer)
            self.disable_smearer.SetValue(state.disable_smearer)
            self.onSmear(event=None)
        self.pinhole_smearer.SetValue(state.pinhole_smearer)
        self.slit_smearer.SetValue(state.slit_smearer)
        try:
            self.dI_noweight.SetValue(state.dI_noweight)
            self.dI_didata.SetValue(state.dI_didata)
            self.dI_sqrdata.SetValue(state.dI_sqrdata)
            self.dI_idata.SetValue(state.dI_idata)
        except:
            # to support older state file formats
            self.dI_noweight.SetValue(False)
            self.dI_didata.SetValue(True)
            self.dI_sqrdata.SetValue(False)
            self.dI_idata.SetValue(False)

        ## we have two more options for smearing
        if self.pinhole_smearer.GetValue():
            self.dx_min = state.dx_min
            self.dx_max = state.dx_max
            if self.dx_min != None:
                self.smear_pinhole_min.SetValue(str(self.dx_min))
            if self.dx_max != None:
                self.smear_pinhole_max.SetValue(str(self.dx_max))
            self.onPinholeSmear(event=None)
        elif self.slit_smearer.GetValue():
            self.dxl = state.dxl
            self.dxw = state.dxw
            if self.dxl != None:
                self.smear_slit_height.SetValue(str(self.dxl))
            if self.dxw != None:
                self.smear_slit_width.SetValue(str(self.dxw))
            else:
                self.smear_slit_width.SetValue('')
            self.onSlitSmear(event=None)

        ## reset state of checkbox,textcrtl  and dispersity parameters value
        self._reset_parameters_state(self.fittable_param, state.fittable_param)
        self._reset_parameters_state(self.fixed_param, state.fixed_param)

        ## draw the model with previous parameters value
        self._onparamEnter_helper()
        #reset the value of chisqr when not consistent with the value computed
        self.tcChi.SetValue(str(self.state.tcChi))
        ## reset context menu items
        self._reset_context_menu()

        ## set the value of the current state to the state given as parameter
        self.state = state.clone()
        self.state.m_name = self.m_name

    def _reset_page_disp_helper(self, state):
        """
        Help to rest page for dispersions
        """
        keys = self.model.getParamList()
        for item in keys:
            if item in self.disp_list and \
                not item in self.model.details:
                self.model.details[item] = ["", None, None]
        #for k,v in self.state.disp_cb_dict.iteritems():
        self.disp_cb_dict = copy.deepcopy(state.disp_cb_dict)
        self.state.disp_cb_dict = copy.deepcopy(state.disp_cb_dict)
        self.values = copy.deepcopy(state.values)
        self.weights = copy.deepcopy(state.weights)

        for key, disp in state._disp_obj_dict.iteritems():
            # From saved file, disp_model can not be sent in model obj.
            # it will be sent as a string here, then converted to model object.
            if disp.__class__.__name__ == 'str':
                disp_model = None
                com_str = "from sas.models.dispersion_models "
                com_str += "import %s as disp_func \ndisp_model = disp_func()"
                exec com_str % disp
            else:
                disp_model = disp
            self._disp_obj_dict[key] = disp_model
            param_name = key.split('.')[0]
            # Try to set dispersion only when available
            # for eg., pass the orient. angles for 1D Cal
            try:
                self.model.set_dispersion(param_name, disp_model)
                self.model._persistency_dict[key] = \
                                 [state.values, state.weights]
            except:
                logging.error(sys.exc_info()[1])
            selection = self._find_polyfunc_selection(disp_model)
            for list in self.fittable_param:
                if list[1] == key and list[7] != None:
                    list[7].SetSelection(selection)
                    # For the array disp_model, set the values and weights
                    if selection == 1:
                        disp_model.set_weights(self.values[key],
                                               self.weights[key])
                        try:
                            # Diables all fittable params for array
                            list[0].SetValue(False)
                            list[0].Disable()
                            list[2].Disable()
                            list[5].Disable()
                            list[6].Disable()
                        except:
                            logging.error(sys.exc_info()[1])
            # For array, disable all fixed params
            if selection == 1:
                for item in self.fixed_param:
                    if item[1].split(".")[0] == key.split(".")[0]:
                        # try it and pass it for the orientation for 1D
                        try:
                            item[2].Disable()
                        except:
                            logging.error(sys.exc_info()[1])

        # Make sure the check box updated when all checked
        if self.cb1.GetValue():
            self.select_all_param(None)

    def _selectDlg(self):
        """
        open a dialog file to selected the customized dispersity
        """
        if self.parent != None:
            self._default_save_location = \
                        self._manager.parent.get_save_location()
        dlg = wx.FileDialog(self, "Choose a weight file",
                            self._default_save_location, "",
                            "*.*", wx.OPEN)
        path = None
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
        dlg.Destroy()
        return path

    def _reset_context_menu(self):
        """
        reset the context menu
        """
        ids = iter(self._id_pool)  # Reusing ids for context menu
        for name, _ in self.state.saved_states.iteritems():
            self.number_saved_state += 1
            ## Add item in the context menu
            wx_id = ids.next()
            msg = 'Save model and state %g' % self.number_saved_state
            self.popUpMenu.Append(wx_id, name, msg)
            wx.EVT_MENU(self, wx_id, self.onResetModel)

    def _reset_plotting_range(self, state):
        """
        Reset the plotting range to a given state
        """
        self.qmin.SetValue(str(state.qmin))
        self.qmax.SetValue(str(state.qmax))

    def _save_typeOfmodel(self):
        """
        save radiobutton containing the type model that can be selected
        """
        #self.state.shape_rbutton = self.shape_rbutton.GetValue()
        #self.state.shape_indep_rbutton = self.shape_indep_rbutton.GetValue()
        #self.state.struct_rbutton = self.struct_rbutton.GetValue()
        #self.state.plugin_rbutton = self.plugin_rbutton.GetValue()
        self.state.structurecombobox = self.structurebox.GetLabel()
        self.state.formfactorcombobox = self.formfactorbox.GetLabel()
        self.state.categorycombobox = self.categorybox.GetLabel()

        ## post state to fit panel
        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)

    def _save_plotting_range(self):
        """
        save the state of plotting range
        """
        self.state.qmin = self.qmin_x
        self.state.qmax = self.qmax_x
        self.state.npts = self.npts_x

    def _onparamEnter_helper(self):
        """
        check if values entered by the user are changed and valid to replot
        model
        """
        # Flag to register when a parameter has changed.
        is_modified = False
        self.fitrange = True
        is_2Ddata = False
        #self._undo.Enable(True)
        # check if 2d data
        if self.data.__class__.__name__ == "Data2D":
            is_2Ddata = True
        if self.model != None:
            try:
                is_modified = self._check_value_enter(self.fittable_param,
                                                      is_modified)
                is_modified = self._check_value_enter(self.fixed_param,
                                                      is_modified)
                is_modified = self._check_value_enter(self.parameters,
                                                      is_modified)
            except:
                logging.error(sys.exc_info()[1])

            # Here we should check whether the boundaries have been modified.
            # If qmin and qmax have been modified, update qmin and qmax and
            # set the is_modified flag to True
            if self._validate_qrange(self.qmin, self.qmax):
                tempmin = float(self.qmin.GetValue())
                if tempmin != self.qmin_x:
                    self.qmin_x = tempmin
                    is_modified = True
                tempmax = float(self.qmax.GetValue())
                if tempmax != self.qmax_x:
                    self.qmax_x = tempmax
                    is_modified = True

                if is_2Ddata:
                    # set mask
                    is_modified = self._validate_Npts()

            else:
                self.fitrange = False

            if not self.data.is_data:
                is_modified = True

            ## if any value is modify draw model with new value
            if not self.fitrange:
                #self.btFit.Disable()
                if is_2Ddata:
                    self.btEditMask.Disable()
            else:
                if is_2Ddata and self.data.is_data and not self.batch_on:
                    self.btEditMask.Enable(True)
            if is_modified and self.fitrange:
                # Theory case: need to get npts value to draw
                self.npts_x = float(self.Npts_total.GetValue())
                self.create_default_data()
                self.state_change = True
                self._draw_model()
                self.Refresh()
        return is_modified

    def _update_paramv_on_fit(self):
        """
        make sure that update param values just before the fitting
        """
        #flag for qmin qmax check values
        flag = True
        self.fitrange = True
        is_modified = False

        #wx.PostEvent(self._manager.parent, StatusEvent(status=" \
        #updating ... ",type="update"))

        ##So make sure that update param values on_Fit.
        #self._undo.Enable(True)
        if self.model != None:
            if self.Npts_total.GetValue() != self.Npts_fit.GetValue():
                if not self.data.is_data:
                    self._manager.page_finder[self.uid].set_fit_data(data=\
                                                                [self.data])
            ##Check the values
            self._check_value_enter(self.fittable_param, is_modified)
            self._check_value_enter(self.fixed_param, is_modified)
            self._check_value_enter(self.parameters, is_modified)

            # If qmin and qmax have been modified, update qmin and qmax and
            # Here we should check whether the boundaries have been modified.
            # If qmin and qmax have been modified, update qmin and qmax and
            # set the is_modified flag to True
            self.fitrange = self._validate_qrange(self.qmin, self.qmax)
            if self.fitrange:
                tempmin = float(self.qmin.GetValue())
                if tempmin != self.qmin_x:
                    self.qmin_x = tempmin
                tempmax = float(self.qmax.GetValue())
                if tempmax != self.qmax_x:
                    self.qmax_x = tempmax
                if tempmax == tempmin:
                    flag = False
                temp_smearer = None
                if not self.disable_smearer.GetValue():
                    temp_smearer = self.current_smearer
                    if self.slit_smearer.GetValue():
                        flag = self.update_slit_smear()
                    elif self.pinhole_smearer.GetValue():
                        flag = self.update_pinhole_smear()
                    else:
                        enable_smearer = not self.disable_smearer.GetValue()
                        self._manager.set_smearer(smearer=temp_smearer,
                                                  uid=self.uid,
                                                  fid=self.data.id,
                                                  qmin=float(self.qmin_x),
                                                  qmax=float(self.qmax_x),
                                                  enable_smearer=enable_smearer,
                                                  draw=False)
                elif not self._is_2D():
                    enable_smearer = not self.disable_smearer.GetValue()
                    self._manager.set_smearer(smearer=temp_smearer,
                                              qmin=float(self.qmin_x),
                                              uid=self.uid,
                                              fid=self.data.id,
                                              qmax=float(self.qmax_x),
                                              enable_smearer=enable_smearer,
                                              draw=False)
                    if self.data != None:
                        index_data = ((self.qmin_x <= self.data.x) & \
                                      (self.data.x <= self.qmax_x))
                        val = str(len(self.data.x[index_data == True]))
                        self.Npts_fit.SetValue(val)
                    else:
                        # No data in the panel
                        try:
                            self.npts_x = float(self.Npts_total.GetValue())
                        except:
                            flag = False
                            return flag
                    flag = True
                if self._is_2D():
                    # only 2D case set mask
                    flag = self._validate_Npts()
                    if not flag:
                        return flag
            else:
                flag = False
        else:
            flag = False

        #For invalid q range, disable the mask editor and fit button, vs.
        if not self.fitrange:
            if self._is_2D():
                self.btEditMask.Disable()
        else:
            if self._is_2D() and  self.data.is_data and not self.batch_on:
                self.btEditMask.Enable(True)

        if not flag:
            msg = "Cannot Plot or Fit :Must select a "
            msg += " model or Fitting range is not valid!!!  "
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))

        try:
            self.save_current_state()
        except:
            logging.error(sys.exc_info()[1])

        return flag

    def _is_modified(self, is_modified):
        """
        return to self._is_modified
        """
        return is_modified

    def _reset_parameters_state(self, listtorestore, statelist):
        """
        Reset the parameters at the given state
        """
        if len(statelist) == 0 or len(listtorestore) == 0:
            return
        if len(statelist) != len(listtorestore):
            return

        for j in range(len(listtorestore)):
            item_page = listtorestore[j]
            item_page_info = statelist[j]
            ##change the state of the check box for simple parameters
            if item_page[0] != None:
                item_page[0].SetValue(item_page_info[0])
            if item_page[2] != None:
                item_page[2].SetValue(item_page_info[2])
                if item_page[2].__class__.__name__ == "ComboBox":
                    if item_page_info[2] in self.model.fun_list:
                        fun_val = self.model.fun_list[item_page_info[2]]
                        self.model.setParam(item_page_info[1], fun_val)
            if item_page[3] != None:
                ## show or hide text +/-
                if item_page_info[2]:
                    item_page[3].Show(True)
                else:
                    item_page[3].Hide()
            if item_page[4] != None:
                ## show of hide the text crtl for fitting error
                if item_page_info[4][0]:
                    item_page[4].Show(True)
                    item_page[4].SetValue(item_page_info[4][1])
                else:
                    item_page[3].Hide()
            if item_page[5] != None:
                ## show of hide the text crtl for fitting error
                item_page[5].Show(item_page_info[5][0])
                item_page[5].SetValue(item_page_info[5][1])

            if item_page[6] != None:
                ## show of hide the text crtl for fitting error
                item_page[6].Show(item_page_info[6][0])
                item_page[6].SetValue(item_page_info[6][1])

    def _reset_strparam_state(self, listtorestore, statelist):
        """
        Reset the string parameters at the given state
        """
        if len(statelist) == 0:
            return

        listtorestore = copy.deepcopy(statelist)

        for j in range(len(listtorestore)):
            item_page = listtorestore[j]
            item_page_info = statelist[j]
            ##change the state of the check box for simple parameters

            if item_page[0] != None:
                item_page[0].SetValue(format_number(item_page_info[0], True))

            if item_page[2] != None:
                param_name = item_page_info[1]
                value = item_page_info[2]
                selection = value
                if value in self.model.fun_list:
                    selection = self.model.fun_list[value]
                item_page[2].SetValue(selection)
                self.model.setParam(param_name, selection)

    def _copy_parameters_state(self, listtocopy, statelist):
        """
        copy the state of button

        :param listtocopy: the list of check button to copy
        :param statelist: list of state object to store the current state

        """
        if len(listtocopy) == 0:
            return

        for item in listtocopy:

            checkbox_state = None
            if item[0] != None:
                checkbox_state = item[0].GetValue()
            parameter_name = item[1]
            parameter_value = None
            if item[2] != None:
                parameter_value = item[2].GetValue()
            static_text = None
            if item[3] != None:
                static_text = item[3].IsShown()
            error_value = None
            error_state = None
            if item[4] != None:
                error_value = item[4].GetValue()
                error_state = item[4].IsShown()

            min_value = None
            min_state = None
            if item[5] != None:
                min_value = item[5].GetValue()
                min_state = item[5].IsShown()

            max_value = None
            max_state = None
            if item[6] != None:
                max_value = item[6].GetValue()
                max_state = item[6].IsShown()
            unit = None
            if item[7] != None:
                unit = item[7].GetLabel()

            statelist.append([checkbox_state, parameter_name, parameter_value,
                              static_text, [error_state, error_value],
                              [min_state, min_value],
                              [max_state, max_value], unit])


    def _draw_model(self, update_chisqr=True, source='model'):
        """
        Method to draw or refresh a plotted model.
        The method will use the data member from the model page
        to build a call to the fitting perspective manager.

        :param chisqr: update chisqr value [bool]
        """
        wx.CallAfter(self._draw_model_after, update_chisqr, source)

    def _draw_model_after(self, update_chisqr=True, source='model'):
        """
        Method to draw or refresh a plotted model.
        The method will use the data member from the model page
        to build a call to the fitting perspective manager.

        :param chisqr: update chisqr value [bool]
        """
        #if self.check_invalid_panel():
        #    return
        if self.model != None:
            temp_smear = None
            if hasattr(self, "enable_smearer"):
                if not self.disable_smearer.GetValue():
                    temp_smear = self.current_smearer
            # compute weight for the current data
            from sas.perspectives.fitting.utils import get_weight
            flag = self.get_weight_flag()
            weight = get_weight(data=self.data, is2d=self._is_2D(), flag=flag)
            toggle_mode_on = self.model_view.IsEnabled()
            is_2d = self._is_2D()
            self._manager.draw_model(self.model,
                                    data=self.data,
                                    smearer=temp_smear,
                                    qmin=float(self.qmin_x),
                                    qmax=float(self.qmax_x),
                                    page_id=self.uid,
                                    toggle_mode_on=toggle_mode_on,
                                    state=self.state,
                                    enable2D=is_2d,
                                    update_chisqr=update_chisqr,
                                    source='model',
                                    weight=weight)

    def _on_show_sld(self, event=None):
        """
        Plot SLD profile
        """
        # get profile data
        x, y = self.model.getProfile()

        from sas.plottools import Data1D as pf_data1d
        #from sas.perspectives.theory.profile_dialog import SLDPanel
        from sas.guiframe.local_perspectives.plotting.profile_dialog \
        import SLDPanel
        sld_data = pf_data1d(x, y)
        sld_data.name = 'SLD'
        sld_data.axes = self.sld_axes
        self.panel = SLDPanel(self, data=sld_data, axes=self.sld_axes,
                              id=wx.ID_ANY)
        self.panel.ShowModal()

    def _set_multfactor_combobox(self, multiplicity=10):
        """
        Set comboBox for muitfactor of CoreMultiShellModel
        :param multiplicit: no. of multi-functionality
        """
        # build content of the combobox
        for idx in range(0, multiplicity):
            self.multifactorbox.Append(str(idx), int(idx))
        self._hide_multfactor_combobox()

    def _show_multfactor_combobox(self):
        """
        Show the comboBox of muitfactor of CoreMultiShellModel
        """
        if not self.mutifactor_text.IsShown():
            self.mutifactor_text.Show(True)
            self.mutifactor_text1.Show(True)
        if not self.multifactorbox.IsShown():
            self.multifactorbox.Show(True)

    def _hide_multfactor_combobox(self):
        """
        Hide the comboBox of muitfactor of CoreMultiShellModel
        """
        if self.mutifactor_text.IsShown():
            self.mutifactor_text.Hide()
            self.mutifactor_text1.Hide()
        if self.multifactorbox.IsShown():
            self.multifactorbox.Hide()

    def formfactor_combo_init(self):
        """
        First time calls _show_combox_helper
        """
        self._show_combox(None)

    def _show_combox_helper(self):
        """
        Fill panel's combo box according to the type of model selected
        """
        custom_model = 'Customized Models'
        mod_cat = self.categorybox.GetStringSelection()
        self.structurebox.SetSelection(0)
        self.structurebox.Disable()
        self.formfactorbox.Clear()
        if mod_cat == None:
            return
        m_list = []
        try:
            if mod_cat == custom_model:
                for model in self.model_list_box[mod_cat]:
                    str_m = str(model).split(".")[0]
                    #self.model_box.Append(str_m)
                    m_list.append(self.model_dict[str_m])
            else:
                cat_dic = self.master_category_dict[mod_cat]
                for (model, enabled) in cat_dic:
                    if enabled:
                        m_list.append(self.model_dict[model])
                    #else:
                    #    msg = "This model is disabled by Category Manager." 
                    #    wx.PostEvent(self.parent.parent,
                    #                 StatusEvent(status=msg, info="error"))
        except:
            msg = "%s\n" % (sys.exc_info()[1])
            wx.PostEvent(self._manager.parent,
                         StatusEvent(status=msg, info="error"))
        self._populate_box(self.formfactorbox, m_list)

    def _on_modify_cat(self, event=None):
        """
        Called when category manager is opened
        """
        self._manager.parent.on_category_panel(event)

    def _show_combox(self, event=None):
        """
        Show combox box associate with type of model selected
        """
        self.Show(False)
        self._show_combox_helper()
        self._on_select_model(event=None)
        self.Show(True)
        self._save_typeOfmodel()
        self.sizer4_4.Layout()
        self.sizer4.Layout()
        self.Layout()
        self.Refresh()

    def _populate_box(self, combobox, list):
        """
        fill combox box with dict item

        :param list: contains item to fill the combox
            item must model class
        """
        mlist = []
        for models in list:
            model = models()
            name = model.__class__.__name__
            if models.__name__ != "NoStructure":
                if hasattr(model, "name"):
                    name = model.name
                mlist.append((name, models))

        # Sort the models
        mlist_sorted = sorted(mlist)
        for item in mlist_sorted:
            combobox.Append(item[0], item[1])
        return 0

    def _onQrangeEnter(self, event):
        """
        Check validity of value enter in the Q range field

        """
        tcrtl = event.GetEventObject()
        #Clear msg if previously shown.
        msg = ""
        wx.PostEvent(self.parent, StatusEvent(status=msg))
        # Flag to register when a parameter has changed.
        #is_modified = False
        if tcrtl.GetValue().lstrip().rstrip() != "":
            try:
                float(tcrtl.GetValue())
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
                    msg = "Model Error: wrong value entered: %s" % \
                                    sys.exc_info()[1]
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
                    return
            except:
                tcrtl.SetBackgroundColour("pink")
                msg = "Model Error: wrong value entered: %s" % sys.exc_info()[1]
                wx.PostEvent(self.parent, StatusEvent(status=msg))
                return
            #Check if # of points for theory model are valid(>0).
            if self.npts != None:
                if check_float(self.npts):
                    temp_npts = float(self.npts.GetValue())
                    if temp_npts != self.num_points:
                        self.num_points = temp_npts
                        #is_modified = True
                else:
                    msg = "Cannot plot: No points in Q range!!!  "
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
        else:
            tcrtl.SetBackgroundColour("pink")
            msg = "Model Error: wrong value entered!!!"
            wx.PostEvent(self.parent, StatusEvent(status=msg))
        self.save_current_state()
        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)
        self.state_change = False
        #Draw the model for a different range
        if not self.data.is_data:
            self.create_default_data()
        self._draw_model()

    def _theory_qrange_enter(self, event):
        """
        Check validity of value enter in the Q range field
        """

        tcrtl = event.GetEventObject()
        #Clear msg if previously shown.
        msg = ""
        wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        # Flag to register when a parameter has changed.
        is_modified = False
        if tcrtl.GetValue().lstrip().rstrip() != "":
            try:
                value = float(tcrtl.GetValue())
                tcrtl.SetBackgroundColour(wx.WHITE)

                # If qmin and qmax have been modified, update qmin and qmax
                if self._validate_qrange(self.theory_qmin, self.theory_qmax):
                    tempmin = float(self.theory_qmin.GetValue())
                    if tempmin != self.theory_qmin_x:
                        self.theory_qmin_x = tempmin
                    tempmax = float(self.theory_qmax.GetValue())
                    if tempmax != self.qmax_x:
                        self.theory_qmax_x = tempmax
                else:
                    tcrtl.SetBackgroundColour("pink")
                    msg = "Model Error: wrong value entered: %s" % \
                                        sys.exc_info()[1]
                    wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
                    return
            except:
                tcrtl.SetBackgroundColour("pink")
                msg = "Model Error: wrong value entered: %s" % sys.exc_info()[1]
                wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
                return
            #Check if # of points for theory model are valid(>0).
            if self.Npts_total.IsEditable():
                if check_float(self.Npts_total):
                    temp_npts = float(self.Npts_total.GetValue())
                    if temp_npts != self.num_points:
                        self.num_points = temp_npts
                        is_modified = True
                else:
                    msg = "Cannot Plot: No points in Q range!!!  "
                    wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        else:
            tcrtl.SetBackgroundColour("pink")
            msg = "Model Error: wrong value entered!!!"
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        self.save_current_state()
        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)
        self.state_change = False
        #Draw the model for a different range
        self.create_default_data()
        self._draw_model()

    def _on_select_model_helper(self):
        """
        call back for model selection
        """
        ## reset dictionary containing reference to dispersion
        self._disp_obj_dict = {}
        self.disp_cb_dict = {}
        self.temp_multi_functional = False
        f_id = self.formfactorbox.GetCurrentSelection()
        #For MAC
        form_factor = None
        if f_id >= 0:
            form_factor = self.formfactorbox.GetClientData(f_id)

        if not form_factor in  self.model_list_box["multiplication"]:
            self.structurebox.Hide()
            self.text2.Hide()
            self.structurebox.Disable()
            self.structurebox.SetSelection(0)
            self.text2.Disable()
        else:
            self.structurebox.Show()
            self.text2.Show()
            self.structurebox.Enable()
            self.text2.Enable()

        if form_factor != None:
            # set multifactor for Mutifunctional models
            if form_factor().__class__ in \
                                        self.model_list_box["Multi-Functions"]:
                m_id = self.multifactorbox.GetCurrentSelection()
                multiplicity = form_factor().multiplicity_info[0]
                self.multifactorbox.Clear()
                self._set_multfactor_combobox(multiplicity)
                self._show_multfactor_combobox()
                #ToDo:  this info should be called directly from the model
                text = form_factor().multiplicity_info[1]  # 'No. of Shells: '

                self.mutifactor_text.SetLabel(text)
                if m_id > multiplicity - 1:
                    # default value
                    m_id = 1

                self.multi_factor = self.multifactorbox.GetClientData(m_id)
                if self.multi_factor == None:
                    self.multi_factor = 0
                form_factor = form_factor(int(self.multi_factor))
                self.multifactorbox.SetSelection(m_id)
                # Check len of the text1 and max_multiplicity
                text = ''
                if form_factor.multiplicity_info[0] == \
                                        len(form_factor.multiplicity_info[2]):
                    text = form_factor.multiplicity_info[2][self.multi_factor]
                self.mutifactor_text1.SetLabel(text)
                # Check if model has  get sld profile.
                if len(form_factor.multiplicity_info[3]) > 0:
                    self.sld_axes = form_factor.multiplicity_info[3]
                    self.show_sld_button.Show(True)
                else:
                    self.sld_axes = ""

            else:
                self._hide_multfactor_combobox()
                self.show_sld_button.Hide()
                form_factor = form_factor()
                self.multi_factor = None
        else:
            self._hide_multfactor_combobox()
            self.show_sld_button.Hide()
            self.multi_factor = None

        s_id = self.structurebox.GetCurrentSelection()
        struct_factor = self.structurebox.GetClientData(s_id)

        if  struct_factor != None:
            from sas.models.MultiplicationModel import MultiplicationModel
            self.model = MultiplicationModel(form_factor, struct_factor())
            # multifunctional form factor
            if len(form_factor.non_fittable) > 0:
                self.temp_multi_functional = True
        else:
            if form_factor != None:
                self.model = form_factor
            else:
                self.model = None
                return self.model
        # check if model has magnetic parameters
        if len(self.model.magnetic_params) > 0:
            self._has_magnetic = True
        else:
            self._has_magnetic = False
        ## post state to fit panel
        self.state.parameters = []
        self.state.model = self.model
        self.state.qmin = self.qmin_x
        self.state.multi_factor = self.multi_factor
        self.disp_list = self.model.getDispParamList()
        self.state.disp_list = self.disp_list
        self.on_set_focus(None)
        self.Layout()

    def _validate_qrange(self, qmin_ctrl, qmax_ctrl):
        """
        Verify that the Q range controls have valid values
        and that Qmin < Qmax.

        :param qmin_ctrl: text control for Qmin
        :param qmax_ctrl: text control for Qmax

        :return: True is the Q range is value, False otherwise

        """
        qmin_validity = check_float(qmin_ctrl)
        qmax_validity = check_float(qmax_ctrl)
        if not (qmin_validity and qmax_validity):
            return False
        else:
            qmin = float(qmin_ctrl.GetValue())
            qmax = float(qmax_ctrl.GetValue())
            if qmin < qmax:
                #Make sure to set both colours white.
                qmin_ctrl.SetBackgroundColour(wx.WHITE)
                qmin_ctrl.Refresh()
                qmax_ctrl.SetBackgroundColour(wx.WHITE)
                qmax_ctrl.Refresh()
            else:
                qmin_ctrl.SetBackgroundColour("pink")
                qmin_ctrl.Refresh()
                qmax_ctrl.SetBackgroundColour("pink")
                qmax_ctrl.Refresh()
                msg = "Invalid Q range: Q min must be smaller than Q max"
                wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
                return False
        return True

    def _validate_Npts(self):
        """
        Validate the number of points for fitting is more than 10 points.
        If valid, setvalues Npts_fit otherwise post msg.
        """
        #default flag
        flag = True
        # Theory
        if self.data == None and self.enable2D:
            return flag
        for data in self.data_list:
            # q value from qx and qy
            radius = numpy.sqrt(data.qx_data * data.qx_data +
                                data.qy_data * data.qy_data)
            #get unmasked index
            index_data = (float(self.qmin.GetValue()) <= radius) & \
                            (radius <= float(self.qmax.GetValue()))
            index_data = (index_data) & (data.mask)
            index_data = (index_data) & (numpy.isfinite(data.data))

            if len(index_data[index_data]) < 10:
                # change the color pink.
                self.qmin.SetBackgroundColour("pink")
                self.qmin.Refresh()
                self.qmax.SetBackgroundColour("pink")
                self.qmax.Refresh()
                msg = "Data Error: "
                msg += "Too few points in %s." % data.name
                wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
                self.fitrange = False
                flag = False
            else:
                self.Npts_fit.SetValue(str(len(index_data[index_data == True])))
                self.fitrange = True

        return flag

    def _validate_Npts_1D(self):
        """
        Validate the number of points for fitting is more than 5 points.
        If valid, setvalues Npts_fit otherwise post msg.
        """
        #default flag
        flag = True
        # Theory
        if self.data == None:
            return flag
        for data in self.data_list:
            # q value from qx and qy
            radius = data.x
            #get unmasked index
            index_data = (float(self.qmin.GetValue()) <= radius) & \
                            (radius <= float(self.qmax.GetValue()))
            index_data = (index_data) & (numpy.isfinite(data.y))

            if len(index_data[index_data]) < 5:
                # change the color pink.
                self.qmin.SetBackgroundColour("pink")
                self.qmin.Refresh()
                self.qmax.SetBackgroundColour("pink")
                self.qmax.Refresh()
                msg = "Data Error: "
                msg += "Too few points in %s." % data.name
                wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
                self.fitrange = False
                flag = False
            else:
                self.Npts_fit.SetValue(str(len(index_data[index_data == True])))
                self.fitrange = True

        return flag

    def _check_value_enter(self, list, modified):
        """
        :param list: model parameter and panel info
        :Note: each item of the list should be as follow:
            item=[check button state, parameter's name,
                paramater's value, string="+/-",
                parameter's error of fit,
                parameter's minimum value,
                parrameter's maximum value ,
                parameter's units]
        """
        is_modified = modified
        if len(list) == 0:
            return is_modified
        for item in list:
            #skip angle parameters for 1D
            if not self.enable2D:
                if item in self.orientation_params:
                    continue
            #try:
            name = str(item[1])

            if string.find(name, ".npts") == -1 and \
                                        string.find(name, ".nsigmas") == -1:
                ## check model parameters range
                param_min = None
                param_max = None

                ## check minimun value
                if item[5] != None and item[5] != "":
                    if item[5].GetValue().lstrip().rstrip() != "":
                        try:
                            param_min = float(item[5].GetValue())
                            if not self._validate_qrange(item[5], item[2]):
                                if numpy.isfinite(param_min):
                                    item[2].SetValue(format_number(param_min))

                            item[5].SetBackgroundColour(wx.WHITE)
                            item[2].SetBackgroundColour(wx.WHITE)

                        except:
                            msg = "Wrong fit parameter range entered"
                            wx.PostEvent(self._manager.parent,
                                         StatusEvent(status=msg))
                            raise ValueError, msg
                        is_modified = True
                ## check maximum value
                if item[6] != None and item[6] != "":
                    if item[6].GetValue().lstrip().rstrip() != "":
                        try:
                            param_max = float(item[6].GetValue())
                            if not self._validate_qrange(item[2], item[6]):
                                if numpy.isfinite(param_max):
                                    item[2].SetValue(format_number(param_max))

                            item[6].SetBackgroundColour(wx.WHITE)
                            item[2].SetBackgroundColour(wx.WHITE)
                        except:
                            msg = "Wrong Fit parameter range entered "
                            wx.PostEvent(self._manager.parent,
                                         StatusEvent(status=msg))
                            raise ValueError, msg
                        is_modified = True

                if param_min != None and param_max != None:
                    if not self._validate_qrange(item[5], item[6]):
                        msg = "Wrong Fit range entered for parameter "
                        msg += "name %s of model %s " % (name, self.model.name)
                        wx.PostEvent(self._manager.parent,
                                     StatusEvent(status=msg))

                if name in self.model.details.keys():
                    self.model.details[name][1:3] = param_min, param_max
                    is_modified = True
                else:
                    self.model.details[name] = ["", param_min, param_max]
                    is_modified = True
            try:
                # Check if the textctr is enabled
                if item[2].IsEnabled():
                    value = float(item[2].GetValue())
                    item[2].SetBackgroundColour("white")
                    # If the value of the parameter has changed,
                    # +update the model and set the is_modified flag
                    if value != self.model.getParam(name) and \
                                                numpy.isfinite(value):
                        self.model.setParam(name, value)
            except:
                item[2].SetBackgroundColour("pink")
                msg = "Wrong Fit parameter value entered "
                wx.PostEvent(self._manager.parent, StatusEvent(status=msg))

        return is_modified

    def _set_dipers_Param(self, event):
        """
        respond to self.enable_disp and self.disable_disp radio box.
        The dispersity object is reset inside the model into Gaussian.
        When the user select yes , this method display a combo box for
        more selection when the user selects No,the combo box disappears.
        Redraw the model with the default dispersity (Gaussian)
        """
        ## On selction if no model exists.
        if self.model == None:
            self.disable_disp.SetValue(True)
            msg = "Please select a Model first..."
            wx.MessageBox(msg, 'Info')
            wx.PostEvent(self._manager.parent,
                         StatusEvent(status="Polydispersion: %s" % msg))
            return

        self._reset_dispersity()

        if self.model == None:
            self.model_disp.Hide()
            self.sizer4_4.Clear(True)
            return

        if self.enable_disp.GetValue():
            ## layout for model containing no dispersity parameters

            self.disp_list = self.model.getDispParamList()

            if len(self.disp_list) == 0 and len(self.disp_cb_dict) == 0:
                self._layout_sizer_noDipers()
            else:
                ## set gaussian sizer
                self._on_select_Disp(event=None)
        else:
            self.sizer4_4.Clear(True)

        ## post state to fit panel
        self.save_current_state()
        if event != None:
            event = PageInfoEvent(page=self)
            wx.PostEvent(self.parent, event)
        #draw the model with the current dispersity
        self._draw_model()
        ## Need to use FitInside again here to replace the next four lines.
        ## Otherwised polydispersity off does not resize the scrollwindow. 
        ## PDB Nov 28, 2015
        self.FitInside()
#        self.sizer4_4.Layout()
#        self.sizer5.Layout()
#        self.Layout()
#        self.Refresh()

    def _layout_sizer_noDipers(self):
        """
        Draw a sizer with no dispersity info
        """
        ix = 0
        iy = 1
        self.fittable_param = []
        self.fixed_param = []
        self.orientation_params_disp = []

        self.sizer4_4.Clear(True)
        text = "No polydispersity available for this model"
        model_disp = wx.StaticText(self, wx.ID_ANY, text)
        self.sizer4_4.Add(model_disp, (iy, ix), (1, 1),
                          wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 10)
        self.sizer4_4.Layout()
        self.sizer4.Layout()

    def _reset_dispersity(self):
        """
        put gaussian dispersity into current model
        """
        if len(self.param_toFit) > 0:
            for item in self.fittable_param:
                if item in self.param_toFit:
                    self.param_toFit.remove(item)

            for item in self.orientation_params_disp:
                if item in self.param_toFit:
                    self.param_toFit.remove(item)

        self.fittable_param = []
        self.fixed_param = []
        self.orientation_params_disp = []
        self.values = {}
        self.weights = {}

        from sas.models.dispersion_models import GaussianDispersion
        if len(self.disp_cb_dict) == 0:
            self.save_current_state()
            self.sizer4_4.Clear(True)
            self.Layout()
            return
        if (len(self.disp_cb_dict) > 0):
            for p in self.disp_cb_dict:
                # The parameter was un-selected.
                # Go back to Gaussian model (with 0 pts)
                disp_model = GaussianDispersion()

                self._disp_obj_dict[p] = disp_model
                # Set the new model as the dispersion object
                # for the selected parameter
                try:
                    self.model.set_dispersion(p, disp_model)
                except:
                    logging.error(sys.exc_info()[1])

        ## save state into
        self.save_current_state()
        self.Layout()
        self.Refresh()

    def _on_select_Disp(self, event):
        """
        allow selecting different dispersion
        self.disp_list should change type later .now only gaussian
        """
        self._set_sizer_dispersion()

        ## Redraw the model
        self._draw_model()
        #self._undo.Enable(True)
        event = PageInfoEvent(page=self)
        wx.PostEvent(self.parent, event)

        self.sizer4_4.Layout()
        self.sizer4.Layout()
        self.SetupScrolling()

    def _on_disp_func(self, event=None):
        """
        Select a distribution function for the polydispersion

        :Param event: ComboBox event
        """
        # get ready for new event
        if event != None:
            event.Skip()
        # Get event object
        disp_box = event.GetEventObject()

        # Try to select a Distr. function
        try:
            disp_box.SetBackgroundColour("white")
            selection = disp_box.GetCurrentSelection()
            param_name = disp_box.Name.split('.')[0]
            disp_name = disp_box.GetValue()
            dispersity = disp_box.GetClientData(selection)

            #disp_model =  GaussianDispersion()
            disp_model = dispersity()
            # Get param names to reset the values of the param
            name1 = param_name + ".width"
            name2 = param_name + ".npts"
            name3 = param_name + ".nsigmas"
            # Check Disp. function whether or not it is 'array'
            if disp_name.lower() == "array":
                value2 = ""
                value3 = ""
                value1 = self._set_array_disp(name=name1, disp=disp_model)
            else:
                self._del_array_values(name1)
                #self._reset_array_disp(param_name)
                self._disp_obj_dict[name1] = disp_model
                self.model.set_dispersion(param_name, disp_model)
                self.state._disp_obj_dict[name1] = disp_model

                value1 = str(format_number(self.model.getParam(name1), True))
                value2 = str(format_number(self.model.getParam(name2)))
                value3 = str(format_number(self.model.getParam(name3)))
            # Reset fittable polydispersin parameter value
            for item in self.fittable_param:
                if item[1] == name1:
                    item[2].SetValue(value1)
                    item[5].SetValue("")
                    item[6].SetValue("")
                    # Disable for array
                    if disp_name.lower() == "array":
                        item[0].SetValue(False)
                        item[0].Disable()
                        item[2].Disable()
                        item[3].Show(False)
                        item[4].Show(False)
                        item[5].Disable()
                        item[6].Disable()
                    else:
                        item[0].Enable()
                        item[2].Enable()
                        item[5].Enable()
                        item[6].Enable()
                    break
            # Reset fixed polydispersion params
            for item in self.fixed_param:
                if item[1] == name2:
                    item[2].SetValue(value2)
                    # Disable Npts for array
                    if disp_name.lower() == "array":
                        item[2].Disable()
                    else:
                        item[2].Enable()
                if item[1] == name3:
                    item[2].SetValue(value3)
                    # Disable Nsigs for array
                    if disp_name.lower() == "array":
                        item[2].Disable()
                    else:
                        item[2].Enable()

            # Make sure the check box updated when all checked
            if self.cb1.GetValue():
                #self.select_all_param(None)
                self.get_all_checked_params()

            # update params
            self._update_paramv_on_fit()
            # draw
            self._draw_model()
            self.Refresh()
        except:
            # Error msg
            msg = "Error occurred:"
            msg += " Could not select the distribution function..."
            msg += " Please select another distribution function."
            disp_box.SetBackgroundColour("pink")
            # Focus on Fit button so that users can see the pinky box
            self.btFit.SetFocus()
            wx.PostEvent(self._manager.parent,
                         StatusEvent(status=msg, info="error"))

    def _set_array_disp(self, name=None, disp=None):
        """
        Set array dispersion

        :param name: name of the parameter for the dispersion to be set
        :param disp: the polydisperion object
        """
        # The user wants this parameter to be averaged.
        # Pop up the file selection dialog.
        path = self._selectDlg()
        # Array data
        values = []
        weights = []
        # If nothing was selected, just return
        if path is None:
            self.disp_cb_dict[name].SetValue(False)
            #self.noDisper_rbox.SetValue(True)
            return
        self._default_save_location = os.path.dirname(path)
        if self._manager != None:
            self._manager.parent._default_save_location = \
                             self._default_save_location

        basename = os.path.basename(path)
        values, weights = self.read_file(path)

        # If any of the two arrays is empty, notify the user that we won't
        # proceed
        if len(self.param_toFit) > 0:
            if name in self.param_toFit:
                self.param_toFit.remove(name)

        # Tell the user that we are about to apply the distribution
        msg = "Applying loaded %s distribution: %s" % (name, path)
        wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        self._set_array_disp_model(name=name, disp=disp,
                                    values=values, weights=weights)
        return basename

    def _set_array_disp_model(self, name=None, disp=None,
                              values=[], weights=[]):
        """
        Set array dispersion model

        :param name: name of the parameter for the dispersion to be set
        :param disp: the polydisperion object
        """
        disp.set_weights(values, weights)
        self._disp_obj_dict[name] = disp
        self.model.set_dispersion(name.split('.')[0], disp)
        self.state._disp_obj_dict[name] = disp
        self.values[name] = values
        self.weights[name] = weights
        # Store the object to make it persist outside the
        # scope of this method
        #TODO: refactor model to clean this up?
        self.state.values = {}
        self.state.weights = {}
        self.state.values = copy.deepcopy(self.values)
        self.state.weights = copy.deepcopy(self.weights)

        # Set the new model as the dispersion object for the
        #selected parameter
        #self.model.set_dispersion(p, disp_model)
        # Store a reference to the weights in the model object
        #so that
        # it's not lost when we use the model within another thread.
        self.state.model = self.model.clone()
        self.model._persistency_dict[name.split('.')[0]] = \
                                        [values, weights]
        self.state.model._persistency_dict[name.split('.')[0]] = \
                                        [values, weights]

    def _del_array_values(self, name=None):
        """
        Reset array dispersion

        :param name: name of the parameter for the dispersion to be set
        """
        # Try to delete values and weight of the names array dic if exists
        try:
            del self.values[name]
            del self.weights[name]
            # delete all other dic
            del self.state.values[name]
            del self.state.weights[name]
            del self.model._persistency_dict[name.split('.')[0]]
            del self.state.model._persistency_dict[name.split('.')[0]]
        except:
            logging.error(sys.exc_info()[1])

    def _lay_out(self):
        """
        returns self.Layout

        :Note: Mac seems to like this better when self.
            Layout is called after fitting.
        """
        self._sleep4sec()
        self.Layout()
        return

    def _sleep4sec(self):
        """
            sleep for 1 sec only applied on Mac
            Note: This 1sec helps for Mac not to crash on self.
            Layout after self._draw_model
        """
        if ON_MAC == True:
            time.sleep(1)

    def _find_polyfunc_selection(self, disp_func=None):
        """
        FInd Comboox selection from disp_func

        :param disp_function: dispersion distr. function
        """
        # List of the poly_model name in the combobox
        list = ["RectangleDispersion", "ArrayDispersion",
                "LogNormalDispersion", "GaussianDispersion",
                "SchulzDispersion"]

        # Find the selection
        try:
            selection = list.index(disp_func.__class__.__name__)
            return selection
        except:
            return 3

    def on_reset_clicked(self, event):
        """
        On 'Reset' button  for Q range clicked
        """
        flag = True
        ##For 3 different cases: Data2D, Data1D, and theory
        if self.model == None:
            msg = "Please select a model first..."
            wx.MessageBox(msg, 'Info')
            flag = False
            return

        elif self.data.__class__.__name__ == "Data2D":
            data_min = 0
            x = max(math.fabs(self.data.xmin), math.fabs(self.data.xmax))
            y = max(math.fabs(self.data.ymin), math.fabs(self.data.ymax))
            self.qmin_x = data_min
            self.qmax_x = math.sqrt(x * x + y * y)
            #self.data.mask = numpy.ones(len(self.data.data),dtype=bool)
            # check smearing
            if not self.disable_smearer.GetValue():
                ## set smearing value whether or
                # not the data contain the smearing info
                if self.pinhole_smearer.GetValue():
                    flag = self.update_pinhole_smear()
                else:
                    flag = True

        elif self.data == None:
            self.qmin_x = _QMIN_DEFAULT
            self.qmax_x = _QMAX_DEFAULT
            self.num_points = _NPTS_DEFAULT
            self.state.npts = self.num_points

        elif self.data.__class__.__name__ != "Data2D":
            self.qmin_x = min(self.data.x)
            self.qmax_x = max(self.data.x)
            # check smearing
            if not self.disable_smearer.GetValue():
                ## set smearing value whether or
                # not the data contain the smearing info
                if self.slit_smearer.GetValue():
                    flag = self.update_slit_smear()
                elif self.pinhole_smearer.GetValue():
                    flag = self.update_pinhole_smear()
                else:
                    flag = True
        else:
            flag = False

        if flag == False:
            msg = "Cannot Plot :Must enter a number!!!  "
            wx.PostEvent(self._manager.parent, StatusEvent(status=msg))
        else:
            # set relative text ctrs.
            self.qmin.SetValue(str(self.qmin_x))
            self.qmax.SetValue(str(self.qmax_x))
            self.show_npts2fit()
            # At this point, some button and variables satatus (disabled?)
            # should be checked such as color that should be reset to
            # white in case that it was pink.
            self._onparamEnter_helper()

        self.save_current_state()
        self.state.qmin = self.qmin_x
        self.state.qmax = self.qmax_x

        #reset the q range values
        self._reset_plotting_range(self.state)
        self._draw_model()

    def select_log(self, event):
        """
        Log checked to generate log spaced points for theory model
        """

    def get_images(self):
        """
        Get the images of the plots corresponding this panel for report

        : return graphs: list of figures
        : Need Move to guiframe
        """
        # set list of graphs
        graphs = []
        canvases = []
        res_item = None
        # call gui_manager
        gui_manager = self._manager.parent
        # loops through the panels [dic]
        for _, item2 in gui_manager.plot_panels.iteritems():
            data_title = self.data.group_id
            # try to get all plots belonging to this control panel
            try:
                g_id = item2.group_id
                if g_id == data_title or \
                        str(g_id).count("res" + str(self.graph_id)) or \
                        str(g_id).count(str(self.uid)) > 0:
                    if str(g_id).count("res" + str(self.graph_id)) > 0:
                        res_item = [item2.figure, item2.canvas]
                    else:
                        # append to the list
                        graphs.append(item2.figure)
                        canvases.append(item2.canvas)
            except:
                # Not for control panels
                logging.error(sys.exc_info()[1])
        # Make sure the resduals plot goes to the last
        if res_item != None:
            graphs.append(res_item[0])
            canvases.append(res_item[1])
        # return the list of graphs
        return graphs, canvases

    def on_function_help_clicked(self, event):
        """
        Function called when 'Help' button is pressed next to model
        of interest.  This calls DocumentationWindow from
        documentation_window.py. It will load the top level of the model
        help documenation sphinx generated html if no model is presented.
        If a model IS present then if documention for that model exists
        it will load to that  point otherwise again it will go to the top.
        For Wx2.8 and below is used (i.e. non-released through installer)
        a browser is loaded and the top of the model documentation only is
        accessible because webbrowser module does not pass anything after
        the # to the browser.

        :param evt: on Help Button pressed event
        """

        _TreeLocation = 'user/models/model_functions.html'
        if self.model != None:
            name = self.formfactorbox.GetValue()
            _PageAnchor = '#' + name.lower()
            _doc_viewer = DocumentationWindow(self, wx.ID_ANY, _TreeLocation,
                                              _PageAnchor, name + " Help")
        else:
            _doc_viewer = DocumentationWindow(self, wx.ID_ANY, _TreeLocation,
                                              "", "General Model Help")


    def on_model_help_clicked(self, event):
        """
        Function called when 'Description' button is pressed next to model
        of interest.  This calls the Description embedded in the model. This
        should work with either Wx2.8 and lower or higher. If no model is
        selected it will give the message that a model must be chosen first
        in the box that would normally contain the description.  If a badly
        behaved model is encountered which has no description then it will
        give the message that none is available.

        :param evt: on Description Button pressed event
        """

        if self.model == None:
            name = 'index.html'
        else:
            name = self.formfactorbox.GetValue()

        msg = 'Model description:\n'
        info = "Info"
        if self.model != None:
#                frame.Destroy()
            if str(self.model.description).rstrip().lstrip() == '':
                msg += "Sorry, no information is available for this model."
            else:
                msg += self.model.description + '\n'
            wx.MessageBox(msg, info)
        else:
            msg += "You must select a model to get information on this"
            wx.MessageBox(msg, info)

    def _on_mag_angle_help(self, event):
        """
        Bring up Magnetic Angle definition bmp image whenever the ? button
        is clicked. Calls DocumentationWindow with the path of the location
        within the documentation tree (after /doc/ ....". When using old
        versions of Wx (i.e. before 2.9 and therefore not part of release
        versions distributed via installer) it brings up an image viewer
        box which allows the user to click through the rest of the images in
        the directory.  Not ideal but probably better than alternative which
        would bring up the entire discussion of how magnetic models work?
        Specially since it is not likely to be accessed.  The normal release
        versions bring up the normal image box.

        :param evt: Triggers on clicking ? in Magnetic Angles? box
        """

        _TreeLocation = "_images/M_angles_pic.bmp"
        _doc_viewer = DocumentationWindow(self, wx.ID_ANY, _TreeLocation, "",
                                          "Magnetic Angle Defintions")

    def _on_mag_help(self, event):
        """
        Bring up Magnetic Angle definition bmp image whenever the ? button
        is clicked. Calls DocumentationWindow with the path of the location
        within the documentation tree (after /doc/ ....". When using old
        versions of Wx (i.e. before 2.9 and therefore not part of release
        versions distributed via installer) it brings up an image viewer
        box which allows the user to click through the rest of the images in
        the directory.  Not ideal but probably better than alternative which
        would bring up the entire discussion of how magnetic models work?
        Specially since it is not likely to be accessed.  The normal release
        versions bring up the normal image box.

        :param evt: Triggers on clicking ? in Magnetic Angles? box
        """

        _TreeLocation = "user/perspectives/fitting/mag_help.html"
        _doc_viewer = DocumentationWindow(self, wx.ID_ANY, _TreeLocation, "",
                                          "Polarized Beam/Magnetc Help")

    def _on_mag_on(self, event):
        """
        Magnetic Parameters ON/OFF
        """
        button = event.GetEventObject()

        if button.GetLabel().count('ON') > 0:
            self.magnetic_on = True
            button.SetLabel("Magnetic OFF")
            m_value = 1.0e-06
            for key in self.model.magnetic_params:
                if key.count('M0') > 0:
                    self.model.setParam(key, m_value)
                    m_value += 0.5e-06
        else:
            self.magnetic_on = False
            button.SetLabel("Magnetic ON")
            for key in self.model.magnetic_params:
                if key.count('M0') > 0:
                    #reset mag value to zero fo safety
                    self.model.setParam(key, 0.0)

        self.Show(False)
        self.set_model_param_sizer(self.model)
        #self._set_sizer_dispersion() 
        self.state.magnetic_on = self.magnetic_on
        self.SetupScrolling()
        self.Show(True)

    def on_pd_help_clicked(self, event):
        """
        Bring up Polydispersity Documentation whenever the ? button is clicked.
        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        istallers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

        :param evt: Triggers on clicking ? in polydispersity box
        """

        _TreeLocation = "user/perspectives/fitting/pd_help.html"
        _PageAnchor = ""
        _doc_viewer = DocumentationWindow(self, wx.ID_ANY, _TreeLocation,
                                          _PageAnchor, "Polydispersity Help")

    def on_left_down(self, event):
        """
        Get key stroke event
        """
        # Figuring out key combo: Cmd for copy, Alt for paste
        if event.CmdDown() and event.ShiftDown():
            self.get_paste()
        elif event.CmdDown():
            self.get_copy()
        else:
            event.Skip()
            return
        # make event free
        event.Skip()

    def get_copy(self):
        """
        Get copy params to clipboard
        """
        content = self.get_copy_params()
        flag = self.set_clipboard(content)
        self._copy_info(flag)
        return flag

    def get_copy_params(self):
        """
        Get the string copies of the param names and values in the tap
        """
        content = 'sasview_parameter_values:'
        # Do it if params exist
        if  self.parameters != []:

            # go through the parameters
            strings = self._get_copy_helper(self.parameters,
                                           self.orientation_params)
            content += strings

            # go through the fittables
            strings = self._get_copy_helper(self.fittable_param,
                                           self.orientation_params_disp)
            content += strings

            # go through the fixed params
            strings = self._get_copy_helper(self.fixed_param,
                                           self.orientation_params_disp)
            content += strings

            # go through the str params
            strings = self._get_copy_helper(self.str_parameters,
                                           self.orientation_params)
            content += strings
            return content
        else:
            return False

    def get_copy_excel(self):
        """
        Get copy params to clipboard
        """
        content = self.get_copy_params_excel()
        flag = self.set_clipboard(content)
        self._copy_info(flag)
        return flag

    def get_copy_params_excel(self):
        """
        Get the string copies of the param names and values in the tap
        """
        content = ''

        crlf = chr(13) + chr(10)
        tab = chr(9)

        # Do it if params exist
        if  self.parameters != []:

            for param in self.parameters:
                content += param[1] #parameter name
                content += tab
                content += param[1] + "_err"
                content += tab

            content += crlf

            #row of values and errors...
            for param in self.parameters:
                content += param[2].GetValue() #value
                content += tab
                content += param[4].GetValue() #error
                content += tab

            return content
        else:
            return False


    def get_copy_latex(self):
        """
        Get copy params to clipboard
        """
        content = self.get_copy_params_latex()
        flag = self.set_clipboard(content)
        self._copy_info(flag)
        return flag

    def get_copy_params_latex(self):
        """
        Get the string copies of the param names and values in the tap
        """
        content = '\\begin{table}'
        content += '\\begin{tabular}[h]'

        crlf = chr(13) + chr(10)
        tab = chr(9)

        # Do it if params exist
        if  self.parameters != []:

            content += '{|'
            for param in self.parameters:
                content += 'l|l|'
            content += '}\hline'
            content += crlf

            for index, param in enumerate(self.parameters):
                content += param[1].replace('_', '\_') #parameter name
                content += ' & '
                content += param[1].replace('_', '\_') + "\_err"
                if index < len(self.parameters) - 1:
                    content += ' & '
            content += '\\\\ \\hline'
            content += crlf

            #row of values and errors...
            for index, param in enumerate(self.parameters):
                content += param[2].GetValue() #parameter value
                content += ' & '
                content += param[4].GetValue() #parameter error
                if index < len(self.parameters) - 1:
                    content += ' & '
            content += '\\\\ \\hline'
            content += crlf

            content += '\\end{tabular}'
            content += '\\end{table}'
            return content
        else:
            return False


    def set_clipboard(self, content=None):
        """
        Put the string to the clipboard
        """
        if not content:
            return False
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(str(content)))
            wx.TheClipboard.Close()
            return True
        return None

    def _get_copy_helper(self, param, orient_param):
        """
        Helping get value and name of the params

        : param param:  parameters
        : param orient_param = oritational params
        : return content: strings [list] [name,value:....]
        """
        content = ''
        # go through the str params
        for item in param:
            # copy only the params shown
            if not item[2].IsShown():
                continue
            disfunc = ''
            try:
                if item[7].__class__.__name__ == 'ComboBox':
                    disfunc = str(item[7].GetValue())
            except:
                logging.error(sys.exc_info()[1])

            # 2D
            if self.data.__class__.__name__ == "Data2D":
                try:
                    check = item[0].GetValue()
                except:
                    check = None
                name = item[1]
                value = item[2].GetValue()
            # 1D
            else:
                ## for 1D all parameters except orientation
                if not item[1] in orient_param:
                    try:
                        check = item[0].GetValue()
                    except:
                        check = None
                    name = item[1]
                    value = item[2].GetValue()

            # add to the content
            if disfunc != '':

                disfunc = ',' + disfunc
            # Need to support array func for copy/paste
            try:
                if disfunc.count('array') > 0:
                    disfunc += ','
                    for val in self.values[name]:
                        disfunc += ' ' + str(val)
                    disfunc += ','
                    for weight in self.weights[name]:
                        disfunc += ' ' + str(weight)
            except:
                logging.error(sys.exc_info()[1])
            content += name + ',' + str(check) + ',' + value + disfunc + ':'

        return content

    def get_clipboard(self):
        """
        Get strings in the clipboard
        """
        text = ""
        # Get text from the clip board
        if wx.TheClipboard.Open():
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                # get wx dataobject
                success = wx.TheClipboard.GetData(data)
                # get text
                if success:
                    text = data.GetText()
                else:
                    text = ''
            # close clipboard
            wx.TheClipboard.Close()
        return text

    def get_paste(self):
        """
        Paste params from the clipboard
        """
        text = self.get_clipboard()
        flag = self.get_paste_params(text)
        self._copy_info(flag)
        return flag

    def get_paste_params(self, text=''):
        """
        Get the string copies of the param names and values in the tap
        """
        context = {}
        # put the text into dictionary
        lines = text.split(':')
        if lines[0] != 'sasview_parameter_values':
            self._copy_info(False)
            return False
        for line in lines[1:-1]:
            if len(line) != 0:
                item = line.split(',')
                check = item[1]
                name = item[0]
                value = item[2]
                # Transfer the text to content[dictionary]
                context[name] = [check, value]
            # ToDo: PlugIn this poly disp function for pasting
            try:
                poly_func = item[3]
                context[name].append(poly_func)
                try:
                    # take the vals and weights for  array
                    array_values = item[4].split(' ')
                    array_weights = item[5].split(' ')
                    val = [float(a_val) for a_val in array_values[1:]]
                    weit = [float(a_weit) for a_weit in array_weights[1:]]

                    context[name].append(val)
                    context[name].append(weit)
                except:
                    raise
            except:
                poly_func = ''
                context[name].append(poly_func)

        # Do it if params exist
        if  self.parameters != []:
            # go through the parameters
            self._get_paste_helper(self.parameters,
                                   self.orientation_params, context)

            # go through the fittables
            self._get_paste_helper(self.fittable_param,
                                   self.orientation_params_disp,
                                   context)

            # go through the fixed params
            self._get_paste_helper(self.fixed_param,
                                   self.orientation_params_disp, context)

            # go through the str params
            self._get_paste_helper(self.str_parameters,
                                   self.orientation_params, context)

            return True
        return None

    def _get_paste_helper(self, param, orient_param, content):
        """
        Helping set values of the params

        : param param:  parameters
        : param orient_param: oritational params
        : param content: dictionary [ name, value: name1.value1,...]
        """
        # go through the str params
        for item in param:
            # 2D
            if self.data.__class__.__name__ == "Data2D":
                name = item[1]
                if name in content.keys():
                    check = content[name][0]
                    pd = content[name][1]
                    if name.count('.') > 0:
                        try:
                            float(pd)
                        except:
                            #continue
                            if not pd and pd != '':
                                continue
                    item[2].SetValue(str(pd))
                    if item in self.fixed_param and pd == '':
                        # Only array func has pd == '' case.
                        item[2].Enable(False)
                    if item[2].__class__.__name__ == "ComboBox":
                        if content[name][1] in self.model.fun_list:
                            fun_val = self.model.fun_list[content[name][1]]
                            self.model.setParam(name, fun_val)

                    value = content[name][1:]
                    self._paste_poly_help(item, value)
                    if check == 'True':
                        is_true = True
                    elif check == 'False':
                        is_true = False
                    else:
                        is_true = None
                    if is_true != None:
                        item[0].SetValue(is_true)
            # 1D
            else:
                ## for 1D all parameters except orientation
                if not item[1] in orient_param:
                    name = item[1]
                    if name in content.keys():
                        check = content[name][0]
                        # Avoid changing combox content
                        value = content[name][1:]
                        pd = value[0]
                        if name.count('.') > 0:
                            try:
                                pd = float(pd)
                            except:
                                #continue
                                if not pd and pd != '':
                                    continue
                        item[2].SetValue(str(pd))
                        if item in self.fixed_param and pd == '':
                            # Only array func has pd == '' case.
                            item[2].Enable(False)
                        if item[2].__class__.__name__ == "ComboBox":
                            if value[0] in self.model.fun_list:
                                fun_val = self.model.fun_list[value[0]]
                                self.model.setParam(name, fun_val)
                                # save state
                        self._paste_poly_help(item, value)
                        if check == 'True':
                            is_true = True
                        elif check == 'False':
                            is_true = False
                        else:
                            is_true = None
                        if is_true != None:
                            item[0].SetValue(is_true)

    def _paste_poly_help(self, item, value):
        """
        Helps get paste for poly function

        :param item: Gui param items
        :param value: the values for parameter ctrols
        """
        is_array = False
        if len(value[1]) > 0:
            # Only for dispersion func.s
            try:
                item[7].SetValue(value[1])
                selection = item[7].GetCurrentSelection()
                name = item[7].Name
                param_name = name.split('.')[0]
                dispersity = item[7].GetClientData(selection)
                disp_model = dispersity()
                # Only for array disp
                try:
                    pd_vals = numpy.array(value[2])
                    pd_weights = numpy.array(value[3])
                    if len(pd_vals) > 0 and len(pd_vals) > 0:
                        if len(pd_vals) == len(pd_weights):
                            self._set_disp_array_cb(item=item)
                            self._set_array_disp_model(name=name,
                                                       disp=disp_model,
                                                       values=pd_vals,
                                                       weights=pd_weights)
                            is_array = True
                except:
                    logging.error(sys.exc_info()[1])
                if not is_array:
                    self._disp_obj_dict[name] = disp_model
                    self.model.set_dispersion(name,
                                              disp_model)
                    self.state._disp_obj_dict[name] = \
                                              disp_model
                    self.model.set_dispersion(param_name, disp_model)
                    self.state.values = self.values
                    self.state.weights = self.weights
                    self.model._persistency_dict[param_name] = \
                                            [self.state.values,
                                             self.state.weights]

            except:
                logging.error(sys.exc_info()[1])
                print "Error in BasePage._paste_poly_help: %s" % \
                                        sys.exc_info()[1]

    def _set_disp_array_cb(self, item):
        """
        Set cb for array disp
        """
        item[0].SetValue(False)
        item[0].Enable(False)
        item[2].Enable(False)
        item[3].Show(False)
        item[4].Show(False)
        item[5].SetValue('')
        item[5].Enable(False)
        item[6].SetValue('')
        item[6].Enable(False)

    def update_pinhole_smear(self):
        """
            Method to be called by sub-classes
            Moveit; This method doesn't belong here
        """
        print "BasicPage.update_pinhole_smear was called: skipping"
        return

    def _read_category_info(self):
        """
        Reads the categories in from file
        """
        # # ILL mod starts here - July 2012 kieranrcampbell@gmail.com
        self.master_category_dict = defaultdict(list)
        self.by_model_dict = defaultdict(list)
        self.model_enabled_dict = defaultdict(bool)

        try:
            categorization_file = CategoryInstaller.get_user_file()
            if not os.path.isfile(categorization_file):
                categorization_file = CategoryInstaller.get_default_file()
            cat_file = open(categorization_file, 'rb')
            self.master_category_dict = json.load(cat_file)
            self._regenerate_model_dict()
            cat_file.close()
        except IOError:
            raise
            print 'Problem reading in category file.'
            print 'We even looked for it, made sure it was there.'
            print 'An existential crisis if there ever was one.'

    def _regenerate_model_dict(self):
        """
        regenerates self.by_model_dict which has each model name as the
        key and the list of categories belonging to that model
        along with the enabled mapping
        """
        self.by_model_dict = defaultdict(list)
        for category in self.master_category_dict:
            for (model, enabled) in self.master_category_dict[category]:
                self.by_model_dict[model].append(category)
                self.model_enabled_dict[model] = enabled

    def _populate_listbox(self):
        """
        fills out the category list box
        """
        uncat_str = 'Customized Models'
        self._read_category_info()

        self.categorybox.Clear()
        cat_list = sorted(self.master_category_dict.keys())
        if not uncat_str in cat_list:
            cat_list.append(uncat_str)

        for category in cat_list:
            if category != '':
                self.categorybox.Append(category)

        if self.categorybox.GetSelection() == wx.NOT_FOUND:
            self.categorybox.SetSelection(0)
        else:
            self.categorybox.SetSelection(\
                self.categorybox.GetSelection())
        #self._on_change_cat(None)

    def _on_change_cat(self, event):
        """
        Callback for category change action
        """
        self.model_name = None
        category = self.categorybox.GetStringSelection()
        if category == None:
            return
        self.model_box.Clear()

        if category == 'Customized Models':
            for model in self.model_list_box[category]:
                str_m = str(model).split(".")[0]
                self.model_box.Append(str_m)

        else:
            for (model, enabled) in sorted(self.master_category_dict[category],
                                      key=lambda name: name[0]):
                if(enabled):
                    self.model_box.Append(model)

    def _fill_model_sizer(self, sizer):
        """
        fill sizer containing model info
        """
        # This should only be called once per fit tab
        #print "==== Entering _fill_model_sizer"
        ##Add model function Details button in fitpanel.
        ##The following 3 lines are for Mac. Let JHC know before modifying...
        title = "Model"
        self.formfactorbox = None
        self.multifactorbox = None
        self.mbox_description = wx.StaticBox(self, wx.ID_ANY, str(title))
        boxsizer1 = wx.StaticBoxSizer(self.mbox_description, wx.VERTICAL)
        sizer_cat = wx.BoxSizer(wx.HORIZONTAL)
        self.mbox_description.SetForegroundColour(wx.RED)
        wx_id = self._ids.next()
        self.model_func = wx.Button(self, wx_id, 'Help', size=(80, 23))
        self.model_func.Bind(wx.EVT_BUTTON, self.on_function_help_clicked,
                             id=wx_id)
        self.model_func.SetToolTipString("Full Model Function Help")
        wx_id = self._ids.next()
        self.model_help = wx.Button(self, wx_id, 'Description', size=(80, 23))
        self.model_help.Bind(wx.EVT_BUTTON, self.on_model_help_clicked,
                             id=wx_id)
        self.model_help.SetToolTipString("Short Model Function Description")
        wx_id = self._ids.next()
        self.model_view = wx.Button(self, wx_id, "Show 2D", size=(80, 23))
        self.model_view.Bind(wx.EVT_BUTTON, self._onModel2D, id=wx_id)
        hint = "toggle view of model from 1D to 2D  or 2D to 1D"
        self.model_view.SetToolTipString(hint)

        cat_set_box = wx.StaticBox(self, wx.ID_ANY, 'Category')
        sizer_cat_box = wx.StaticBoxSizer(cat_set_box, wx.HORIZONTAL)
        sizer_cat_box.SetMinSize((200, 50))
        self.categorybox = wx.ComboBox(self, wx.ID_ANY,
                                       style=wx.CB_READONLY)
        self.categorybox.SetToolTip(wx.ToolTip("Select a Category/Type"))
        self._populate_listbox()
        wx.EVT_COMBOBOX(self.categorybox, wx.ID_ANY, self._show_combox)
        #self.shape_rbutton = wx.RadioButton(self, wx.ID_ANY, 'Shapes',
        #                                     style=wx.RB_GROUP)
        #self.shape_indep_rbutton = wx.RadioButton(self, wx.ID_ANY,
        #                                          "Shape-Independent")
        #self.struct_rbutton = wx.RadioButton(self, wx.ID_ANY,
        #                                     "Structure Factor ")
        #self.plugin_rbutton = wx.RadioButton(self, wx.ID_ANY,
        #                                     "Uncategorized")

        #self.Bind(wx.EVT_RADIOBUTTON, self._show_combox,
        #                   id=self.shape_rbutton.GetId())
        #self.Bind(wx.EVT_RADIOBUTTON, self._show_combox,
        #                    id=self.shape_indep_rbutton.GetId())
        #self.Bind(wx.EVT_RADIOBUTTON, self._show_combox,
        #                    id=self.struct_rbutton.GetId())
        #self.Bind(wx.EVT_RADIOBUTTON, self._show_combox,
        #                    id=self.plugin_rbutton.GetId())
        #MAC needs SetValue

        show_cat_button = wx.Button(self, wx.ID_ANY, "Modify")
        cat_tip = "Modify model categories \n"
        cat_tip += "(also accessible from the menu bar)."
        show_cat_button.SetToolTip(wx.ToolTip(cat_tip))
        show_cat_button.Bind(wx.EVT_BUTTON, self._on_modify_cat)
        sizer_cat_box.Add(self.categorybox, 1, wx.RIGHT, 3)
        sizer_cat_box.Add((10, 10))
        sizer_cat_box.Add(show_cat_button)
        #self.shape_rbutton.SetValue(True)

        sizer_radiobutton = wx.GridSizer(2, 2, 5, 5)
        #sizer_radiobutton.Add(self.shape_rbutton)
        #sizer_radiobutton.Add(self.shape_indep_rbutton)
        sizer_radiobutton.Add((5, 5))
        sizer_radiobutton.Add(self.model_view, 1, wx.RIGHT, 5)
        #sizer_radiobutton.Add(self.plugin_rbutton)
        #sizer_radiobutton.Add(self.struct_rbutton)
#        sizer_radiobutton.Add((5,5))
        sizer_radiobutton.Add(self.model_help, 1, wx.RIGHT | wx.LEFT, 5)
#        sizer_radiobutton.Add((5,5))
        sizer_radiobutton.Add(self.model_func, 1, wx.RIGHT, 5)
        sizer_cat.Add(sizer_cat_box, 1, wx.LEFT, 2.5)
        sizer_cat.Add(sizer_radiobutton)
        sizer_selection = wx.BoxSizer(wx.HORIZONTAL)
        mutifactor_selection = wx.BoxSizer(wx.HORIZONTAL)

        self.text1 = wx.StaticText(self, wx.ID_ANY, "")
        self.text2 = wx.StaticText(self, wx.ID_ANY, "P(Q)*S(Q)")
        self.mutifactor_text = wx.StaticText(self, wx.ID_ANY, "No. of Shells: ")
        self.mutifactor_text1 = wx.StaticText(self, wx.ID_ANY, "")
        self.show_sld_button = wx.Button(self, wx.ID_ANY, "Show SLD Profile")
        self.show_sld_button.Bind(wx.EVT_BUTTON, self._on_show_sld)

        self.formfactorbox = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        self.formfactorbox.SetToolTip(wx.ToolTip("Select a Model"))
        if self.model != None:
            self.formfactorbox.SetValue(self.model.name)
        self.structurebox = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        self.multifactorbox = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        self.initialize_combox()
        wx.EVT_COMBOBOX(self.formfactorbox, wx.ID_ANY, self._on_select_model)

        wx.EVT_COMBOBOX(self.structurebox, wx.ID_ANY, self._on_select_model)
        wx.EVT_COMBOBOX(self.multifactorbox, wx.ID_ANY, self._on_select_model)
        ## check model type to show sizer
        if self.model != None:
            print "_set_model_sizer_selection: disabled."
            #self._set_model_sizer_selection(self.model)

        sizer_selection.Add(self.text1)
        sizer_selection.Add((10, 5))
        sizer_selection.Add(self.formfactorbox)
        sizer_selection.Add((5, 5))
        sizer_selection.Add(self.text2)
        sizer_selection.Add((5, 5))
        sizer_selection.Add(self.structurebox)

        mutifactor_selection.Add((13, 5))
        mutifactor_selection.Add(self.mutifactor_text)
        mutifactor_selection.Add(self.multifactorbox)
        mutifactor_selection.Add((5, 5))
        mutifactor_selection.Add(self.mutifactor_text1)
        mutifactor_selection.Add((10, 5))
        mutifactor_selection.Add(self.show_sld_button)

        boxsizer1.Add(sizer_cat)
        boxsizer1.Add((10, 10))
        boxsizer1.Add(sizer_selection)
        boxsizer1.Add((10, 10))
        boxsizer1.Add(mutifactor_selection)

        self._set_multfactor_combobox()
        self.multifactorbox.SetSelection(1)
        self.show_sld_button.Hide()
        sizer.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)
        sizer.Layout()

    def on_smear_helper(self, update=False):
        """
        Help for onSmear if implemented

        :param update: force or not to update
        """
    def reset_page(self, state, first=False):
        """
        reset the state  if implemented
        """
    def onSmear(self, event):
        """
        Create a smear object if implemented
        """
    def onPinholeSmear(self, event):
        """
        Create a custom pinhole smear object if implemented
        """
    def onSlitSmear(self, event):
        """
        Create a custom slit smear object if implemented
        """
    def update_slit_smear(self):
        """
        called by kill_focus on pinhole TextCntrl
        to update the changes if implemented
        """
    def select_param(self, event):
        """
        Select TextCtrl  checked if implemented
        """
    def set_data(self, data=None):
        """
        Sets data if implemented
        """
    def _is_2D(self):
        """
        Check if data_name is Data2D if implemented
        """
    def _on_select_model(self, event=None):
        """
        call back for model selection if implemented
        """
    def select_all_param(self, event):
        """
        set to true or false all checkBox if implemented
        """
    def get_weight_flag(self):
        """
        Get flag corresponding to a given weighting dI data if implemented
        """
    def _set_sizer_dispersion(self):
        """
        draw sizer for dispersity if implemented
        """
    def get_all_checked_params(self):
        """
        Found all parameters current check and add them to list of parameters
        to fit if implemented
        """
    def show_npts2fit(self):
        """
        setValue Npts for fitting if implemented
        """
    def _onModel2D(self, event):
        """
        toggle view of model from 1D to 2D  or 2D from 1D if implemented
        """

class ModelTextCtrl(wx.TextCtrl):
    """
    Text control for model and fit parameters.
    Binds the appropriate events for user interactions.
    Default callback methods can be overwritten on initialization

    :param kill_focus_callback: callback method for EVT_KILL_FOCUS event
    :param set_focus_callback:  callback method for EVT_SET_FOCUS event
    :param mouse_up_callback:   callback method for EVT_LEFT_UP event
    :param text_enter_callback: callback method for EVT_TEXT_ENTER event

    """
    ## Set to True when the mouse is clicked while whole string is selected
    full_selection = False
    ## Call back for EVT_SET_FOCUS events
    _on_set_focus_callback = None

    def __init__(self, parent, id=-1,
                 value=wx.EmptyString,
                 pos=wx.DefaultPosition,
                 size=wx.DefaultSize,
                 style=0,
                 validator=wx.DefaultValidator,
                 name=wx.TextCtrlNameStr,
                 kill_focus_callback=None,
                 set_focus_callback=None,
                 mouse_up_callback=None,
                 text_enter_callback=None):

        wx.TextCtrl.__init__(self, parent, id, value, pos,
                             size, style, validator, name)

        # Bind appropriate events
        self._on_set_focus_callback = parent.onSetFocus \
            if set_focus_callback is None else set_focus_callback
        self.Bind(wx.EVT_SET_FOCUS, self._on_set_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self._silent_kill_focus \
            if kill_focus_callback is None else kill_focus_callback)
        self.Bind(wx.EVT_TEXT_ENTER, parent._onparamEnter \
            if text_enter_callback is None else text_enter_callback)
        if not ON_MAC:
            self.Bind(wx.EVT_LEFT_UP, self._highlight_text \
                if mouse_up_callback is None else mouse_up_callback)

    def _on_set_focus(self, event):
        """
        Catch when the text control is set in focus to highlight the whole
        text if necessary

        :param event: mouse event

        """
        event.Skip()
        self.full_selection = True
        return self._on_set_focus_callback(event)

    def _highlight_text(self, event):
        """
        Highlight text of a TextCtrl only of no text has be selected

        :param event: mouse event

        """
        # Make sure the mouse event is available to other listeners
        event.Skip()
        control = event.GetEventObject()
        if self.full_selection:
            self.full_selection = False
            # Check that we have a TextCtrl
            if issubclass(control.__class__, wx.TextCtrl):
                # Check whether text has been selected,
                # if not, select the whole string
                (start, end) = control.GetSelection()
                if start == end:
                    control.SetSelection(-1, -1)

    def _silent_kill_focus(self, event):
        """
        Save the state of the page
        """

        event.Skip()
        #pass

