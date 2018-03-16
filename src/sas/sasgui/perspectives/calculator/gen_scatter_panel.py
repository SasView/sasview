"""
Generic Scattering panel.
This module relies on guiframe manager.
"""


import wx
import sys
import os
import numpy as np
#import math
import wx.aui as aui
#import wx.lib.agw.aui as aui
import logging
import time

import matplotlib
matplotlib.interactive(False)
#Use the WxAgg back end. The Wx one takes too long to render
matplotlib.use('WXAgg')

#from sas.sasgui.guiframe.gui_manager import MDIFrame
from sas.sascalc.data_util.calcthread import CalcThread
from sas.sasgui.guiframe.local_perspectives.plotting.SimplePlot import PlotFrame
from sas.sasgui.guiframe.dataFitting import Data2D
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sascalc.dataloader.data_info import Detector
from sas.sascalc.dataloader.data_info import Source
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.events import StatusEvent
from sas.sascalc.calculator import sas_gen
from sas.sasgui.perspectives.calculator.calculator_widgets import OutputTextCtrl
from sas.sasgui.perspectives.calculator.calculator_widgets import InputTextCtrl
from wx.lib.scrolledpanel import ScrolledPanel
from sas.sasgui.perspectives.calculator.load_thread import GenReader
from sas.sasgui.plottools.arrow3d import Arrow3D
from sas.sasgui.perspectives.calculator import calculator_widgets as widget
from sas.sasgui.guiframe.events import NewPlotEvent
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

logger = logging.getLogger(__name__)

_BOX_WIDTH = 76
#Slit length panel size 
if sys.platform.count("win32") > 0:
    PANEL_TOP = 0
    PANEL_WIDTH = 570
    PANEL_HEIGHT = 370
    FONT_VARIANT = 0
else:
    PANEL_TOP = 60
    PANEL_WIDTH = 620
    PANEL_HEIGHT = 370
    FONT_VARIANT = 1
_QMAX_DEFAULT = 0.3
_NPTS_DEFAULT = 50
_Q1D_MIN = 0.001

def add_icon(parent, frame):
    """
    Add icon in the frame
    """
    if parent is not None:
        if hasattr(frame, "IsIconized"):
            if not frame.IsIconized():
                try:
                    icon = parent.GetIcon()
                    frame.SetIcon(icon)
                except:
                    pass

def _set_error(panel, item, show_msg=False):
    """
    Set_error dialog
    """
    if item is not None:
        item.SetBackgroundColour("pink")
        item.Refresh()
    if show_msg:
        msg = "Error: wrong (or out of range) value entered."
        if panel.parent.parent is not None:
            wx.PostEvent(panel.parent.parent,
                     StatusEvent(status=msg, info='Error'))
            panel.SetFocus()
    return False



class CalcGen(CalcThread):
    """
    Computation
    """
    def __init__(self,
                 id= -1,
                 input=None,
                 completefn=None,
                 updatefn=None,
                 #elapsed = 0,
                 yieldtime=0.01,
                 worktime=0.01):
        """
        """
        CalcThread.__init__(self, completefn,
                 updatefn,
                 yieldtime,
                 worktime)
        self.starttime = 0
        self.id = id
        self.input = input
        self.update_fn = updatefn

    def compute(self):
        """
        excuting computation
        """
        #elapsed = time.time() - self.starttime
        self.starttime = time.time()
        self.complete(input=self.input, update=self.update_fn)

class SasGenPanel(ScrolledPanel, PanelBase):
    """
        Provides the sas gen calculator GUI.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "Generic SAS Calculator"
    ## Name to appear on the window title bar
    window_caption = "Generic SAS "

    def __init__(self, parent, *args, **kwds):
        ScrolledPanel.__init__(self, parent, style=wx.RAISED_BORDER,
                               *args, **kwds)
        #kwds['style'] = wx.SUNKEN_BORDER
        PanelBase.__init__(self)
        #Font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.SetupScrolling()
        #thread to read data 
        self.reader = None
        self.ext = None
        self.id = 'GenSAS'
        self.file_name = ''
        self.time_text = None
        self.orient_combo = None
        self.omfreader = sas_gen.OMFReader()
        self.sldreader = sas_gen.SLDReader()
        self.pdbreader = sas_gen.PDBReader()
        self.model = sas_gen.GenSAS()
        self.param_dic = self.model.params
        self.parameters = []
        self.data = None
        self.scale2d = None
        self.is_avg = False
        self.plot_frame = None
        self.qmax_x = _QMAX_DEFAULT
        self.npts_x = _NPTS_DEFAULT
        self.sld_data = None
        self.graph_num = 1
        self.default_shape = 'rectangular'
        # Object that receive status event
        self.parent = parent
        self._do_layout()
        self._create_default_sld_data()
        self._create_default_2d_data()
        wx.CallAfter(self._set_sld_data_helper)

    def _define_structure(self):
        """
            Define the main sizers building to build this application.
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.box_source = wx.StaticBox(self, -1, str("SLD Data File"))
        self.box_parameters = wx.StaticBox(self, -1, str("Input Parameters"))
        self.box_qrange = wx.StaticBox(self, -1, str("Q Range"))
        self.boxsizer_source = wx.StaticBoxSizer(self.box_source,
                                                    wx.VERTICAL)
        self.boxsizer_parameters = wx.StaticBoxSizer(self.box_parameters,
                                                    wx.VERTICAL)
        self.boxsizer_qrange = wx.StaticBoxSizer(self.box_qrange,
                                                    wx.VERTICAL)
        self.data_name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.param_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.shape_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.hint_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.qrange_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.VERTICAL)
        self.button_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer2 = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_data_name(self):
        """
            Fill the sizer containing data's name
        """
        data_name_txt = wx.StaticText(self, -1, 'Data: ')
        self.data_name_tcl = OutputTextCtrl(self, -1,
                                            size=(_BOX_WIDTH * 4, -1))
        data_hint = "Loaded data"
        self.data_name_tcl.SetToolTipString(data_hint)
        #control that triggers importing data
        id = wx.NewId()
        self.browse_button = wx.Button(self, id, "Load")
        hint_on_browse = "Click to load data into this panel."
        self.browse_button.SetToolTipString(hint_on_browse)
        self.Bind(wx.EVT_BUTTON, self.on_load_data, id=id)
        self.data_name_sizer.AddMany([(data_name_txt, 0, wx.LEFT, 15),
                                      (self.data_name_tcl, 0, wx.LEFT, 10),
                                      (self.browse_button, 0, wx.LEFT, 10)])
    def _layout_param_size(self):
        """
            Fill the sizer containing slit size information
        """
        self.parameters = []
        sizer = wx.GridBagSizer(3, 6)
        model = self.model
        details = self.model.details
        params = self.model.params
        ix = 0
        iy = 0
        param_title = wx.StaticText(self, -1, 'Parameter')
        sizer.Add(param_title, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        value_title = wx.StaticText(self, -1, 'Value')
        sizer.Add(value_title, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        unit_title = wx.StaticText(self, -1, 'Unit')
        sizer.Add(unit_title, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        key_list = list(params.keys())
        key_list.sort()
        for param in key_list:
            iy += 1
            ix = 0
            p_name = wx.StaticText(self, -1, param)
            sizer.Add(p_name, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ## add parameter value
            ix += 1
            value = model.getParam(param)
            ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH * 2, 20),
                                style=wx.TE_PROCESS_ENTER)
            #ctl.SetToolTipString(\
            #            "Hit 'Enter' after typing to update the plot.")
            ctl.SetValue(format_number(value, True))
            sizer.Add(ctl, (iy, ix), (1, 1), wx.EXPAND)
            ## add unit
            ix += 1
            unit = wx.StaticText(self, -1, details[param][0])
            sizer.Add(unit, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            self.parameters.append([p_name, ctl, unit])

        self.param_sizer.Add(sizer, 0, wx.LEFT, 10)

    def _layout_hint(self):
        """
            Fill the sizer containing hint
        """
        hint_msg = "We support omf, sld or pdb data files only."
        hint_msg += "         "
        if FONT_VARIANT < 1:
            hint_msg += "Very "
        hint_msg += "SLOW drawing -->"
        hint_txt = wx.StaticText(self, -1, hint_msg)

        id = wx.NewId()
        self.draw_button = wx.Button(self, id, "Arrow Draw")
        hint_on_draw = "Draw with arrows. Caution: it is a very slow drawing."
        self.draw_button.SetToolTipString(hint_on_draw)
        self.draw_button.Bind(wx.EVT_BUTTON, self.sld_draw, id=id)

        self.draw_button.Enable(False)
        self.hint_sizer.AddMany([(hint_txt, 0, wx.LEFT, 15),
                                 (self.draw_button, 0, wx.LEFT, 7)])

    def _layout_shape(self):
        """
        Fill the shape sizer
        """
        label_txt = wx.StaticText(self, -1, "Shape:")
        self.shape_combo = self._fill_shape_combo()
        self.shape_sizer.AddMany([(label_txt, 0, wx.LEFT, 15),
                                (self.shape_combo, 0, wx.LEFT, 5)])

    def _fill_shape_combo(self):
        """
        Fill up the shape combo box
        """
        shape_combo = wx.ComboBox(self, -1, size=(150, -1),
                                      style=wx.CB_READONLY)
        shape_combo.Append('Rectangular')
        shape_combo.Append('Ellipsoid')
        shape_combo.Bind(wx.EVT_COMBOBOX, self._on_shape_select)
        shape_combo.SetSelection(0)
        return shape_combo

    def _on_shape_select(self, event):
        """
        On selecting a shape
        """
        event.Skip()
        label = event.GetEventObject().GetValue().lower()
        self.default_shape = label
        self.parent.set_omfpanel_default_shap(self.default_shape)
        self.parent.set_omfpanel_npts()

    def _fill_orient_combo(self):
        """
        Fill up the orientation combo box: used only for atomic structure
        """
        orient_combo = wx.ComboBox(self, -1, size=(150, -1),
                                      style=wx.CB_READONLY)
        orient_combo.Append('Fixed orientation')
        orient_combo.Append('Debye full avg.')
        #orient_combo.Append('Debye sph. sym.')

        orient_combo.Bind(wx.EVT_COMBOBOX, self._on_orient_select)
        orient_combo.SetSelection(0)
        return orient_combo

    def _on_orient_select(self, event):
        """
        On selecting a orientation
        """
        event.Skip()
        cb = event.GetEventObject()
        if cb.GetCurrentSelection() == 2:
            self.is_avg = None
        else:
            is_avg = cb.GetCurrentSelection() == 1
            self.is_avg = is_avg
        self.model.set_is_avg(self.is_avg)
        self.set_est_time()

    def _layout_qrange(self):
        """
        Fill the sizer containing qrange
        """
        sizer = wx.GridBagSizer(2, 3)
        ix = 0
        iy = 0
        #key_list.sort()
        name = wx.StaticText(self, -1, 'No. of Qx (Qy) bins: ')
        sizer.Add(name, (iy, ix), (1, 1), \
                        wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ## add parameter value
        ix += 1
        self.npt_ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH * 1.5, 20),
                            style=wx.TE_PROCESS_ENTER)
        self.npt_ctl.Bind(wx.EVT_TEXT, self._onparamEnter)
        self.npt_ctl.SetValue(format_number(self.npts_x, True))
        sizer.Add(self.npt_ctl, (iy, ix), (1, 1), wx.EXPAND)
        ## add unit
        ix += 1
        unit = wx.StaticText(self, -1, '')
        sizer.Add(unit, (iy, ix), (1, 1), \
                        wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        iy += 1
        ix = 0
        name = wx.StaticText(self, -1, 'Qx (Qy) Max: ')
        sizer.Add(name, (iy, ix), (1, 1), \
                        wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ## add parameter value
        ix += 1
        self.qmax_ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH * 1.5, 20),
                            style=wx.TE_PROCESS_ENTER)
        self.qmax_ctl.Bind(wx.EVT_TEXT, self._onparamEnter)
        self.qmax_ctl.SetValue(format_number(self.qmax_x, True))
        sizer.Add(self.qmax_ctl, (iy, ix), (1, 1), wx.EXPAND)
        ## add unit
        ix += 1
        unit = wx.StaticText(self, -1, '[1/A]')
        sizer.Add(unit, (iy, ix), (1, 1), \
                        wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        self.qrange_sizer.Add(sizer, 0, wx.LEFT, 10)

    def _layout_button(self):
        """
            Do the layout for the button widgets
        """
        self.est_time = '*Estimated Computation time :\n  %s'
        self.time_text = wx.StaticText(self, -1, self.est_time % str('2 sec'))
        self.orient_combo = self._fill_orient_combo()
        self.orient_combo.Show(False)

        self.bt_compute = wx.Button(self, wx.NewId(), 'Compute')
        self.bt_compute.Bind(wx.EVT_BUTTON, self.on_compute)
        self.bt_compute.SetToolTipString("Compute 2D Scattering Pattern.")

        self.bt_help = wx.Button(self, wx.NewId(), 'HELP')
        self.bt_help.Bind(wx.EVT_BUTTON, self.on_help)
        self.bt_help.SetToolTipString("Help on Scatter Calculator")

        self.bt_close = wx.Button(self, wx.ID_CANCEL, 'Close')
        self.bt_close.Bind(wx.EVT_BUTTON, self.on_panel_close)
        self.bt_close.SetToolTipString("Close this window")

        self.button_sizer1.AddMany([(self.bt_compute, 0, wx.LEFT, 20),
                                   (self.orient_combo , 0, wx.LEFT, 20)])
        self.button_sizer2.AddMany([(self.time_text , 0, wx.LEFT, 20),
                                   (self.bt_help, 0, wx.LEFT, 20),
                                   (self.bt_close, 0, wx.LEFT, 20)])
        self.button_sizer.AddMany([(self.button_sizer1 , 0, wx.BOTTOM|wx.LEFT, 10),
                                   (self.button_sizer2 , 0, wx.LEFT, 10)])

    def estimate_ctime(self):
        """
        Calculation time estimation
        """
        # magic equation: not very accurate
        factor = 1
        n_qbins = float(self.npt_ctl.GetValue())
        n_qbins *= n_qbins
        n_pixs = float(self.parent.get_npix())
        if self.is_avg:
            factor = 6
            n_pixs *= (n_pixs / 200)
        x_in = n_qbins * n_pixs / 100000
        etime = factor + 0.085973 * x_in
        return int(etime)

    def set_est_time(self):
        """
        Set text for est. computation time
        """
        unit = 'sec'
        if self.time_text is not None:
            self.time_text.SetForegroundColour('black')
            etime = self.estimate_ctime()
            if etime > 60:
                etime /= 60
                unit = 'min'
                self.time_text.SetForegroundColour('red')
            time_str = str(etime) + ' ' + unit
            self.time_text.SetLabel(self.est_time % time_str)

    def _do_layout(self):
        """
        Draw window content
        """
        self._define_structure()
        self._layout_data_name()
        self._layout_param_size()
        self._layout_qrange()
        self._layout_hint()
        self._layout_shape()
        self._layout_button()
        self.boxsizer_source.AddMany([(self.data_name_sizer, 0,
                                        wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.hint_sizer, 0,
                                        wx.EXPAND | wx.TOP | wx.BOTTOM, 5),
                                      (self.shape_sizer, 0,
                                        wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.boxsizer_parameters.AddMany([(self.param_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5), ])
        self.boxsizer_qrange.AddMany([(self.qrange_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5), ])
        self.main_sizer.AddMany([(self.boxsizer_source, 0,
                                  wx.EXPAND | wx.ALL, 10),
                                 (self.boxsizer_parameters, 0,
                                  wx.EXPAND | wx.ALL, 10),
                                 (self.boxsizer_qrange, 0,
                                  wx.EXPAND | wx.ALL, 10),
                                 (self.button_sizer, 0,
                                  wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)

    def _create_default_sld_data(self):
        """
        Making default sld-data
        """
        sld_n_default = 6.97e-06
        omfdata = sas_gen.OMFData()
        omf2sld = sas_gen.OMF2SLD()
        omf2sld.set_data(omfdata, self.default_shape)
        self.sld_data = omf2sld.output
        self.sld_data.is_data = False
        self.sld_data.filename = "Default SLD Profile"
        self.sld_data.set_sldn(sld_n_default)
        self.data_name_tcl.SetValue(self.sld_data.filename)

    def choose_data_file(self, location=None):
        """
        Choosing a dtata file
        """
        path = None
        filename = ''
        if location is None:
            location = os.getcwd()

        exts = "*" + self.omfreader.ext[0]
        exts += ", *" + self.sldreader.ext[0]
        exts += ", *" + self.pdbreader.ext[0]
        all_type = "All GEN files (%s, %s) | %s" % (exts.upper(), exts.lower(),
                                               exts.lower().replace(',', ';'))
        wildcard = [all_type]
        omf_type = self.omfreader.type
        sld_type = self.sldreader.type
        pdb_type = self.pdbreader.type

        for type in sld_type:
            wildcard.append(type)
        for type in omf_type:
            wildcard.append(type)
        for type in pdb_type:
            wildcard.append(type)
        wildcard = '|'.join(wildcard)
        dlg = wx.FileDialog(self, "Choose a file", location,
                            "", wildcard, wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            filename = os.path.basename(path)
        dlg.Destroy()
        return path

    def on_load_data(self, event):
        """
        Open a file dialog to allow the user to select a given file.
        The user is only allow to load file with extension .omf, .txt, .sld.
        Display the slit size corresponding to the loaded data.
        """
        location = self.parent.get_path()
        path = self.choose_data_file(location=location)
        if path is None:
            return

        self.shape_sizer.ShowItems(False)
        self.default_shape = 'rectangular'
        self.parent.set_omfpanel_default_shap(self.default_shape)

        self.parent.set_file_location(os.path.dirname(path))
        try:
            #Load data
            self.ext = os.path.splitext(path)[-1]
            if self.ext in self.omfreader.ext:
                loader = self.omfreader
            elif self.ext in self.sldreader.ext:
                loader = self.sldreader
            elif self.ext in self.pdbreader.ext:
                loader = self.pdbreader
            else:
                loader = None
            if self.reader is not None and self.reader.isrunning():
                self.reader.stop()
            self.browse_button.Enable(False)
            self.browse_button.SetLabel("Loading...")
            if self.parent.parent is not None:
                wx.PostEvent(self.parent.parent,
                                StatusEvent(status="Loading...",
                                type="progress"))
            self.reader = GenReader(path=path, loader=loader,
                                    completefn=self.complete_loading,
                                    updatefn=self.load_update)
            self.reader.queue()
            #self.load_update()
        except:
            self.ext = None
            if self.parent.parent is None:
                return
            msg = "Generic SAS Calculator: %s" % (sys.exc_info()[1])
            wx.PostEvent(self.parent.parent,
                          StatusEvent(status=msg, type='stop'))
            self.SetFocus()
            return

    def load_update(self):
        """
        print update on the status bar
        """
        if self.parent.parent is None:
                return
        if self.reader.isrunning():
            type = "progress"
        else:
            type = "stop"
        wx.PostEvent(self.parent.parent, StatusEvent(status="",
                                                  type=type))

    def complete_loading(self, data=None, filename=''):
        """
        Complete the loading
        """
        #compute the slit size
        self.browse_button.Enable(True)
        self.browse_button.SetLabel('Load')
        try:
            is_pdbdata = False
            filename = data.filename
            self.data_name_tcl.SetValue(str(filename))
            self.file_name = filename.split('.')[0]
            self.orient_combo.SetSelection(0)
            self.is_avg = False
            if self.ext in self.omfreader.ext:
                gen = sas_gen.OMF2SLD()
                gen.set_data(data)
                #omf_data = data
                self.sld_data = gen.get_magsld()
            elif self.ext in self.sldreader.ext:
                self.sld_data = data
            elif self.ext in self.pdbreader.ext:
                self.sld_data = data
                is_pdbdata = True
                #omf_data = None
            else:
                raise
            self.orient_combo.Show(is_pdbdata)
            #self.button_sizer.Layout()
            self.FitInside()
            self._set_sld_data_helper(True)
        except:
            if self.parent.parent is None:
                raise
            msg = "Loading Error: This file format is not supported "
            msg += "for GenSAS."
            wx.PostEvent(self.parent.parent,
                          StatusEvent(status=msg, type='stop', info='Error'))
            self.SetFocus()
            return
        if self.parent.parent is None:
            return

        msg = "Load Complete"
        wx.PostEvent(self.parent.parent, StatusEvent(status=msg, type='stop'))
        self.SetFocus()

    def _set_sld_data_helper(self, is_draw=False):
        """
        Set sld data helper
        """
        #is_avg = self.orient_combo.GetCurrentSelection() == 1
        self.model.set_is_avg(self.is_avg)
        self.model.set_sld_data(self.sld_data)

        self.draw_button.Enable(self.sld_data is not None)
        wx.CallAfter(self.parent.set_sld_data, self.sld_data)
        self._update_model_params()
        if is_draw:
            wx.CallAfter(self.sld_draw, None, False)

    def _update_model_params(self):
        """
        Update the model parameter values
        """
        for list in self.parameters:
            param_name = list[0].GetLabelText()
            val = str(self.model.params[param_name])
            list[1].SetValue(val)

    def set_volume_ctl_val(self, val):
        """
        Set volume txtctrl value
        """
        for list in self.parameters:
            param_name = list[0].GetLabelText()
            if param_name.lower() == 'total_volume':
                list[1].SetValue(val)
                list[1].Refresh()
                break

    def _onparamEnter(self, event):
        """
        On param enter
        """
        try:
            item = event.GetEventObject()
            self._check_value()
            item.Refresh()
        except:
            pass

    def sld_draw(self, event=None, has_arrow=True):
        """
        Draw 3D sld profile
        """
        flag = self.parent.check_omfpanel_inputs()
        if not flag:
            infor = 'Error'
            msg = 'Error: Wrong inputs in the SLD info panel.'
            # inform msg to wx
            wx.PostEvent(self.parent.parent,
                    StatusEvent(status=msg, info=infor))
            self.SetFocus()
            return

        self.sld_data = self.parent.get_sld_from_omf()
        output = self.sld_data
        #frame_size = wx.Size(470, 470)    
        self.plot_frame = PlotFrame(self, -1, 'testView')
        frame = self.plot_frame
        frame.Show(False)
        add_icon(self.parent, frame)
        panel = frame.plotpanel
        try:
            # mpl >= 1.0.0
            ax = panel.figure.gca(projection='3d')
        except:
            # mpl < 1.0.0
            try:
                from mpl_toolkits.mplot3d import Axes3D
                ax = Axes3D(panel.figure)
            except:
                logger.error("PlotPanel could not import Axes3D")
                raise
        panel.dimension = 3
        graph_title = self._sld_plot_helper(ax, output, has_arrow)
        # Use y, z axes (in mpl 3d) as z, y axes 
        # that consistent with our SAS detector coords.
        ax.set_xlabel('x ($\A%s$)' % output.pos_unit)
        ax.set_ylabel('z ($\A%s$)' % output.pos_unit)
        ax.set_zlabel('y ($\A%s$)' % output.pos_unit)
        panel.subplot.figure.subplots_adjust(left=0.05, right=0.95,
                                             bottom=0.05, top=0.96)
        if output.pix_type == 'atom':
            ax.legend(loc='upper left', prop={'size':10})
        num_graph = str(self.graph_num)
        frame.SetTitle('Graph %s: %s' % (num_graph, graph_title))
        wx.CallAfter(frame.Show, True)
        self.graph_num += 1

    def _sld_plot_helper(self, ax, output, has_arrow=False):
        """
        Actual plot definition happens here
        :Param ax: axis3d
        :Param output: sld_data [MagSLD]
        :Param has_arrow: whether or not draws M vector [bool]
        """
        # Set the locals
        color_dic = {'H':'blue', 'D':'purple', 'N': 'orange',
                     'O':'red', 'C':'green', 'P':'cyan', 'Other':'k'}
        marker = ','
        m_size = 2
        graph_title = self.file_name
        graph_title += "   3D SLD Profile "
        pos_x = output.pos_x
        pos_y = output.pos_y
        pos_z = output.pos_z
        sld_mx = output.sld_mx
        sld_my = output.sld_my
        sld_mz = output.sld_mz
        pix_symbol = output.pix_symbol
        if output.pix_type == 'atom':
            marker = 'o'
            m_size = 3.5
        sld_tot = (np.fabs(sld_mx) + np.fabs(sld_my) + \
                   np.fabs(sld_mz) + np.fabs(output.sld_n))
        is_nonzero = sld_tot > 0.0
        is_zero = sld_tot == 0.0
        # I. Plot null points
        if is_zero.any():
            ax.plot(pos_x[is_zero], pos_z[is_zero], pos_y[is_zero], marker,
                    c="y", alpha=0.5, markeredgecolor='y', markersize=m_size)
            pos_x = pos_x[is_nonzero]
            pos_y = pos_y[is_nonzero]
            pos_z = pos_z[is_nonzero]
            sld_mx = sld_mx[is_nonzero]
            sld_my = sld_my[is_nonzero]
            sld_mz = sld_mz[is_nonzero]
            pix_symbol = output.pix_symbol[is_nonzero]
        # II. Plot selective points in color
        other_color = np.ones(len(pix_symbol), dtype='bool')
        for key in list(color_dic.keys()):
            chosen_color = pix_symbol == key
            if np.any(chosen_color):
                other_color = other_color & (chosen_color != True)
                color = color_dic[key]
                ax.plot(pos_x[chosen_color], pos_z[chosen_color],
                        pos_y[chosen_color], marker, c=color, alpha=0.5,
                        markeredgecolor=color, markersize=m_size, label=key)
        # III. Plot All others        
        if np.any(other_color):
            a_name = ''
            if output.pix_type == 'atom':
                # Get atom names not in the list
                a_names = [symb  for symb in pix_symbol \
                           if symb not in list(color_dic.keys())]
                a_name = a_names[0]
                for name in a_names:
                    new_name = ", " + name
                    if a_name.count(name) == 0:
                        a_name += new_name
            # plot in black
            ax.plot(pos_x[other_color], pos_z[other_color], pos_y[other_color],
                    marker, c="k", alpha=0.5, markeredgecolor="k",
                    markersize=m_size, label=a_name)
        # IV. Draws atomic bond with grey lines if any
        if output.has_conect:
            for ind in range(len(output.line_x)):
                ax.plot(output.line_x[ind], output.line_z[ind],
                        output.line_y[ind], '-', lw=0.6, c="grey", alpha=0.3)
        # V. Draws magnetic vectors
        if has_arrow and len(pos_x) > 0:
            graph_title += " - Magnetic Vector as Arrow -"
            panel = self.plot_frame.plotpanel
            def _draw_arrow(input=None, update=None):
                """
                draw magnetic vectors w/arrow
                """
                max_mx = max(np.fabs(sld_mx))
                max_my = max(np.fabs(sld_my))
                max_mz = max(np.fabs(sld_mz))
                max_m = max(max_mx, max_my, max_mz)
                try:
                    max_step = max(output.xstepsize, output.ystepsize,
                                   output.zstepsize)
                except:
                    max_step = 0
                if max_step <= 0:
                    max_step = 5
                try:
                    if max_m != 0:
                        unit_x2 = sld_mx / max_m
                        unit_y2 = sld_my / max_m
                        unit_z2 = sld_mz / max_m
                        # 0.8 is for avoiding the color becomes white=(1,1,1))
                        color_x = np.fabs(unit_x2 * 0.8)
                        color_y = np.fabs(unit_y2 * 0.8)
                        color_z = np.fabs(unit_z2 * 0.8)
                        x2 = pos_x + unit_x2 * max_step
                        y2 = pos_y + unit_y2 * max_step
                        z2 = pos_z + unit_z2 * max_step
                        x_arrow = np.column_stack((pos_x, x2))
                        y_arrow = np.column_stack((pos_y, y2))
                        z_arrow = np.column_stack((pos_z, z2))
                        colors = np.column_stack((color_x, color_y, color_z))
                        arrows = Arrow3D(panel, x_arrow, z_arrow, y_arrow,
                                        colors, mutation_scale=10, lw=1,
                                        arrowstyle="->", alpha=0.5)
                        ax.add_artist(arrows)
                except:
                    pass
                msg = "Arrow Drawing completed.\n"
                status_type = 'stop'
                self._status_info(msg, status_type)
            msg = "Arrow Drawing is in progress..."
            status_type = 'progress'
            self._status_info(msg, status_type)
            draw_out = CalcGen(input=ax,
                             completefn=_draw_arrow, updatefn=self._update)
            draw_out.queue()
        return graph_title

    def set_input_params(self):
        """
        Set model parameters
        """
        for list in self.parameters:
            param_name = list[0].GetLabelText()
            param_value = float(list[1].GetValue())
            self.model.setParam(param_name, param_value)

    def on_compute(self, event):
        """
        Compute I(qx, qy)
        """
        flag = self.parent.check_omfpanel_inputs()
        if not flag and self.parent.parent is not None:
            infor = 'Error'
            msg = 'Error: Wrong inputs in the SLD info panel.'
            # inform msg to wx
            wx.PostEvent(self.parent.parent,
                    StatusEvent(status=msg, info=infor))
            self.SetFocus()
            return
        self.sld_data = self.parent.get_sld_from_omf()
        if self.sld_data is None:
            if self.parent.parent is not None:
                infor = 'Error'
                msg = 'Error: No data has been selected.'
                # inform msg to wx
                wx.PostEvent(self.parent.parent,
                        StatusEvent(status=msg, info=infor))
                self.SetFocus()
            return
        flag = self._check_value()
        if not flag:
            _set_error(self, None, True)
            return
        try:
            self.model.set_sld_data(self.sld_data)
            self.set_input_params()
            if self.is_avg or self.is_avg is None:
                self._create_default_1d_data()
                i_out = np.zeros(len(self.data.y))
                inputs = [self.data.x, [], i_out]
            else:
                self._create_default_2d_data()
                i_out = np.zeros(len(self.data.data))
                inputs = [self.data.qx_data, self.data.qy_data, i_out]

            msg = "Computation is in progress..."
            status_type = 'progress'
            self._status_info(msg, status_type)
            cal_out = CalcGen(input=inputs,
                              completefn=self.complete,
                              updatefn=self._update)
            cal_out.queue()

        except:
            msg = "%s." % sys.exc_info()[1]
            status_type = 'stop'
            self._status_info(msg, status_type)
            wx.PostEvent(self.parent.parent,
                        StatusEvent(status=msg, info='Error'))
            self.SetFocus()

    def on_help(self, event):
        """
        Bring up the General scattering Calculator Documentation whenever
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
        _TreeLocation += "sas_calculator_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "General Scattering Calculator Help")

    def _check_value(self):
        """
        Check input values if float
        """
        flag = True
        self.npt_ctl.SetBackgroundColour("white")
        self.qmax_ctl.SetBackgroundColour("white")
        try:
            npt_val = float(self.npt_ctl.GetValue())
            if npt_val < 2 or npt_val > 1000:
                raise
            self.npt_ctl.SetValue(str(int(npt_val)))
            self.set_est_time()
        except:
            flag = _set_error(self, self.npt_ctl)
        try:
            qmax_val = float(self.qmax_ctl.GetValue())
            if qmax_val <= 0 or qmax_val > 1000:
                raise
        except:
            flag = _set_error(self, self.qmax_ctl)
        for list in self.parameters:
            list[1].SetBackgroundColour("white")
            param_name = list[0].GetLabelText()
            try:
                param_val = float(list[1].GetValue())
                if param_name.count('frac') > 0:
                    if param_val < 0 or param_val > 1:
                       raise
            except:
                flag = _set_error(self, list[1])
        return flag

    def _status_info(self, msg='', type="update"):
        """
        Status msg
        """
        if type == "stop":
            label = "Compute"
            able = True
        else:
            label = "Wait..."
            able = False
        self.bt_compute.Enable(able)
        self.bt_compute.SetLabel(label)
        self.bt_compute.SetToolTipString(label)
        if self.parent.parent is not None:
            wx.PostEvent(self.parent.parent,
                             StatusEvent(status=msg, type=type))

    def _update(self, time=None):
        """
        Update the progress bar
        """
        if self.parent.parent is None:
            return
        type = "progress"
        msg = "Please wait. Computing... (Note: Window may look frozen.)"
        wx.PostEvent(self.parent.parent, StatusEvent(status=msg,
                                                  type=type))

    def complete(self, input, update=None):
        """
        Gen compute complete function
        :Param input: input list [qx_data, qy_data, i_out]
        """
        out = np.empty(0)
        #s = time.time()
        for ind in range(len(input[0])):
            if self.is_avg:
                if ind % 1 == 0 and update is not None:
                    update()
                    time.sleep(0.1)
                inputi = [input[0][ind:ind + 1], [], input[2][ind:ind + 1]]
                outi = self.model.run(inputi)
                out = np.append(out, outi)
            else:
                if ind % 50 == 0  and update is not None:
                    update()
                    time.sleep(0.001)
                inputi = [input[0][ind:ind + 1], input[1][ind:ind + 1],
                          input[2][ind:ind + 1]]
                outi = self.model.runXY(inputi)
                out = np.append(out, outi)
        #print time.time() - s
        if self.is_avg or self.is_avg is None:
            self._draw1D(out)
        else:
            #out = self.model.runXY(input)
            self._draw2D(out)

        msg = "Gen computation completed.\n"
        status_type = 'stop'
        self._status_info(msg, status_type)

    def _create_default_2d_data(self):
        """
        Create 2D data by default
        Only when the page is on theory mode.
        :warning: This data is never plotted.
        """
        self.qmax_x = float(self.qmax_ctl.GetValue())
        self.npts_x = int(float(self.npt_ctl.GetValue()))
        self.data = Data2D()
        qmax = self.qmax_x #/ np.sqrt(2)
        self.data.xaxis('\\rm{Q_{x}}', '\AA^{-1}')
        self.data.yaxis('\\rm{Q_{y}}', '\AA^{-1}')
        self.data.is_data = False
        self.data.id = str(self.uid) + " GenData"
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
        xmax = qmax
        xmin = -qmax
        ymax = qmax
        ymin = -qmax
        qstep = self.npts_x

        x = np.linspace(start=xmin, stop=xmax, num=qstep, endpoint=True)
        y = np.linspace(start=ymin, stop=ymax, num=qstep, endpoint=True)
        ## use data info instead
        new_x = np.tile(x, (len(y), 1))
        new_y = np.tile(y, (len(x), 1))
        new_y = new_y.swapaxes(0, 1)
        # all data reuire now in 1d array
        qx_data = new_x.flatten()
        qy_data = new_y.flatten()
        q_data = np.sqrt(qx_data * qx_data + qy_data * qy_data)
        # set all True (standing for unmasked) as default
        mask = np.ones(len(qx_data), dtype=bool)
        # store x and y bin centers in q space
        x_bins = x
        y_bins = y
        self.data.source = Source()
        self.data.data = np.ones(len(mask))
        self.data.err_data = np.ones(len(mask))
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

    def _create_default_1d_data(self):
        """
        Create 2D data by default
        Only when the page is on theory mode.
        :warning: This data is never plotted.
                    residuals.x = data_copy.x[index]
            residuals.dy = np.ones(len(residuals.y))
            residuals.dx = None
            residuals.dxl = None
            residuals.dxw = None
        """
        self.qmax_x = float(self.qmax_ctl.GetValue())
        self.npts_x = int(float(self.npt_ctl.GetValue()))
        qmax = self.qmax_x #/ np.sqrt(2)
        ## Default values
        xmax = qmax
        xmin = qmax * _Q1D_MIN
        qstep = self.npts_x
        x = np.linspace(start=xmin, stop=xmax, num=qstep, endpoint=True)
        # store x and y bin centers in q space
        #self.data.source = Source()
        y = np.ones(len(x))
        dy = np.zeros(len(x))
        dx = np.zeros(len(x))
        self.data = Data1D(x=x, y=y)
        self.data.dx = dx
        self.data.dy = dy

    def _draw1D(self, y_out):
        """
        Complete get the result of modelthread and create model 2D
        that can be plot.
        """
        page_id = self.id
        data = self.data

        model = self.model
        state = None

        new_plot = Data1D(x=data.x, y=y_out)
        new_plot.dx = data.dx
        new_plot.dy = data.dy
        new_plot.xaxis('\\rm{Q_{x}}', '\AA^{-1}')
        new_plot.yaxis('\\rm{Intensity}', 'cm^{-1}')
        new_plot.is_data = False
        new_plot.id = str(self.uid) + " GenData1D"
        new_plot.group_id = str(self.uid) + " Model1D"
        new_plot.name = model.name + '1d'
        new_plot.title = "Generic model1D "
        new_plot.id = str(page_id) + ': ' + self.file_name \
                        + ' #%s' % str(self.graph_num) + "_1D"
        new_plot.group_id = str(page_id) + " Model1D" + \
                             ' #%s' % str(self.graph_num) + "_1D"
        new_plot.is_data = False

        title = new_plot.title
        _yaxis, _yunit = new_plot.get_yaxis()
        _xaxis, _xunit = new_plot.get_xaxis()
        new_plot.xaxis(str(_xaxis), str(_xunit))
        new_plot.yaxis(str(_yaxis), str(_yunit))

        if new_plot.is_data:
            data_name = str(new_plot.name)
        else:
            data_name = str(model.__class__.__name__) + '1d'

        if len(title) > 1:
            new_plot.title = "Gen Theory for %s " % model.name + data_name
        new_plot.name = new_plot.id
        new_plot.label = new_plot.id
        #theory_data = deepcopy(new_plot)
        if self.parent.parent is not None:
            self.parent.parent.update_theory(data_id=new_plot.id,
                                           theory=new_plot,
                                           state=state)
        title = new_plot.title
        num_graph = str(self.graph_num)
        wx.CallAfter(self.parent.draw_graph, new_plot,
                     title="GEN Graph %s: " % num_graph + new_plot.id)
        self.graph_num += 1

    def _draw2D(self, image):
        """
        Complete get the result of modelthread and create model 2D
        that can be plot.
        """
        page_id = self.id
        data = self.data

        model = self.model
        qmin = 0.0
        state = None

        np.nan_to_num(image)
        new_plot = Data2D(image=image, err_image=data.err_data)
        new_plot.name = model.name + '2d'
        new_plot.title = "Generic model 2D "
        new_plot.id = str(page_id) + ': ' + self.file_name \
                        + ' #%s' % str(self.graph_num) + "_2D"
        new_plot.group_id = str(page_id) + " Model2D" \
                        + ' #%s' % str(self.graph_num) + "_2D"
        new_plot.detector = data.detector
        new_plot.source = data.source
        new_plot.is_data = False
        new_plot.qx_data = data.qx_data
        new_plot.qy_data = data.qy_data
        new_plot.q_data = data.q_data
        new_plot.mask = data.mask
        ## plot boundaries
        new_plot.ymin = data.ymin
        new_plot.ymax = data.ymax
        new_plot.xmin = data.xmin
        new_plot.xmax = data.xmax
        title = data.title
        _yaxis, _yunit = data.get_yaxis()
        _xaxis, _xunit = data.get_xaxis()
        new_plot.xaxis(str(_xaxis), str(_xunit))
        new_plot.yaxis(str(_yaxis), str(_yunit))

        new_plot.is_data = False
        if data.is_data:
            data_name = str(data.name)
        else:
            data_name = str(model.__class__.__name__) + '2d'

        if len(title) > 1:
            new_plot.title = "Gen Theory for %s " % model.name + data_name
        new_plot.name = new_plot.id
        new_plot.label = new_plot.id
        #theory_data = deepcopy(new_plot)
        if self.parent.parent is not None:
            self.parent.parent.update_theory(data_id=data.id,
                                           theory=new_plot,
                                           state=state)
        title = new_plot.title
        num_graph = str(self.graph_num)
        wx.CallAfter(self.parent.draw_graph, new_plot,
                     title="GEN Graph %s: " % num_graph + new_plot.id)
        self.graph_num += 1

    def set_scale2d(self, scale):
        """
        Set SLD plot scale
        """
        self.scale2d = None

    def on_panel_close(self, event):
        """
        close the window containing this panel
        """
        self.parent.Close()

class OmfPanel(ScrolledPanel, PanelBase):
    """
        Provides the sas gen calculator GUI.
    """
    ## Internal nickname for the window, used by the AUI manager
    window_name = "SLD Pixel Info"
    ## Name to appear on the window title bar
    window_caption = "SLD Pixel Info "

    def __init__(self, parent, *args, **kwds):
        ScrolledPanel.__init__(self, parent, style=wx.RAISED_BORDER,
                               *args, **kwds)
        PanelBase.__init__(self)
        #Font size 
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.SetupScrolling()
        # Object that receive status event
        self.parent = parent
        self.sld_data = sas_gen.MagSLD([0], [0], [0])
        self.sld_ctl = None
        self.default_shape = 'rectangular'
        self._do_layout()

    def set_slddata(self, slddata):
        """
        Set sld data related items
        """
        self.sld_data = slddata
        self._set_slddata_ctr_val(slddata)
        # Make sure that self._set_slddata_ctr_val() is finished
        wx.CallAfter(self._set_omfdata_ctr, slddata)

    def get_sld_val(self):
        """
        Set sld_n of slddata on sld input
        """
        sld_sets = {}
        if not self.sld_data.is_data:
            self._get_other_val()
        for list in self.slds:
            if list[1].IsEnabled():
                list[1].SetBackgroundColour("white")
                list[1].Refresh()
                try:
                    val = float(list[1].GetValue())
                    sld_sets[list[0]] = val
                except:
                    flag = _set_error(self, list[1])
                    if not flag:
                        return self.sld_data
            else:
               sld_sets[list[0]] = None
        for key in list(sld_sets.keys()):
            key_low = key.lower()
            if key_low.count('mx') > 0:
                if sld_sets[key] is None:
                    sld_sets[key] = self.sld_data.sld_mx
                mx = sld_sets[key]
            elif key_low.count('my') > 0:
                if sld_sets[key] is None:
                    sld_sets[key] = self.sld_data.sld_my
                my = sld_sets[key]
            elif key_low.count('mz') > 0:
                if sld_sets[key] is None:
                    sld_sets[key] = self.sld_data.sld_mz
                mz = sld_sets[key]
            else:
                if sld_sets[key] is not None:
                    self.sld_data.set_sldn(sld_sets[key])
        self.sld_data.set_sldms(mx, my, mz)
        self._set_slddata_ctr_val(self.sld_data)

        return self.sld_data

    def get_pix_volumes(self):
        """
        Get the pixel volume
        """
        vol = self.sld_data.vol_pix

        return vol

    def _get_other_val(self):
        """
        """
        omfdata = sas_gen.OMFData()
        sets = {}
        try:
            for lst in self.stepsize:
                if lst[1].IsEnabled():
                    val = float(lst[1].GetValue())
                    sets[lst[0]] = val
                else:
                    sets[lst[0]] = None
                    return
            for lst in self.nodes:
                if lst[1].IsEnabled():
                    val = float(lst[1].GetValue())
                    sets[lst[0]] = val
                else:
                    sets[lst[0]] = None
                    return

            for key in list(sets.keys()):
                setattr(omfdata, key, sets[key])

            omf2sld = sas_gen.OMF2SLD()
            omf2sld.set_data(omfdata, self.default_shape)
            self.sld_data = omf2sld.output
            self.sld_data.is_data = False
            self.sld_data.filename = "Default SLD Profile"
        except:
            msg = "OMF Panel: %s" % sys.exc_info()[1]
            infor = 'Error'
            #logger.error(msg)
            if self.parent.parent is not None:
                # inform msg to wx
                wx.PostEvent(self.parent.parent,
                        StatusEvent(status=msg, info=infor))
                self.SetFocus()

    def _set_slddata_ctr_val(self, slddata):
        """
        Set slddata crl
        """
        try:
            val = str(len(slddata.sld_n))
        except:
            val = 'Unknown'
        self.npix_ctl.SetValue(val)

    def _set_omfdata_ctr(self, omfdata):
        """
        Set the textctr box values
        """

        if omfdata is None:
            self._set_none_text()
            return
        nodes_list = self._get_nodes_key_list(omfdata)
        step_list = self._get_step_key_list(omfdata)
        for ctr_list in self.nodes:
            for key in list(nodes_list.keys()):
                if ctr_list[0] == key:
                    ctr_list[1].SetValue(format_number(nodes_list[key], True))
                    ctr_list[1].Enable(not omfdata.is_data)
                    break
        for ctr_list in self.stepsize:
            for key in list(step_list.keys()):
                if ctr_list[0] == key:
                    ctr_list[1].SetValue(format_number(step_list[key], True))
                    ctr_list[1].Enable(not omfdata.is_data)
                    break

    def _set_none_text(self):
        """
        Set Unknown in textctrls
        """
        val = 'Unknown'
        for ctr_list in self.nodes:
            ctr_list[1].SetValue(val)
        for ctr_list in self.stepsize:
            ctr_list[1].SetValue(val)

    def _define_structure(self):
        """
        Define the main sizers building to build this application.
        """
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.npixels_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.box_sld = wx.StaticBox(self, -1,
                                    str("Mean SLD"))
        self.box_node = wx.StaticBox(self, -1, str("Nodes"))
        self.boxsizer_sld = wx.StaticBoxSizer(self.box_sld, wx.VERTICAL)
        self.box_stepsize = wx.StaticBox(self, -1, str("Step Size"))
        self.boxsizer_node = wx.StaticBoxSizer(self.box_node, wx.VERTICAL)
        self.boxsizer_stepsize = wx.StaticBoxSizer(self.box_stepsize,
                                                    wx.VERTICAL)
        self.sld_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.node_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.step_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.hint_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

    def _layout_npix(self):
        """
        Build No of pixels sizer
        """
        num_pix_text = wx.StaticText(self, -1, "No. of Pixels: ")
        self.npix_ctl = OutputTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER)
        self._set_slddata_ctr_val(self.sld_data)
        self._set_omfdata_ctr(self.sld_data)
        self.npixels_sizer.AddMany([(num_pix_text, 0,
                                          wx.EXPAND | wx.LEFT | wx.TOP, 5),
                                     (self.npix_ctl, 0,
                                     wx.EXPAND | wx.TOP, 5)])

    def _layout_slds(self):
        """
        Build nuclear sld sizer
        """
        self.slds = []
        omfdata = self.sld_data
        if omfdata is None:
            raise
        sld_key_list = self._get_slds_key_list(omfdata)
        # Dic is not sorted
        key_list = [key for key in list(sld_key_list.keys())]
        # Sort here
        key_list.sort()
        is_data = self.sld_data.is_data
        sizer = wx.GridBagSizer(2, 3)
        ix = 0
        iy = -1
        for key in key_list:
            value = sld_key_list[key]
            iy += 1
            ix = 0
            name = wx.StaticText(self, -1, key)
            sizer.Add(name, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ## add parameter value
            ix += 1
            ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER)
            ctl.SetValue(format_number(value, True))
            ctl.Enable(not is_data)
            sizer.Add(ctl, (iy, ix), (1, 1), wx.EXPAND)
            ## add unit
            ix += 1
            s_unit = '[' + omfdata.sld_unit + ']'
            unit = wx.StaticText(self, -1, s_unit)
            sizer.Add(unit, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            self.slds.append([key, ctl, unit])
        self.sld_sizer.Add(sizer, 0, wx.LEFT, 10)

    def _layout_nodes(self):
        """
        Fill the sizer containing data's name
        """
        self.nodes = []
        omfdata = self.sld_data
        if omfdata is None:
            raise
        key_list = self._get_nodes_key_list(omfdata)
        is_data = self.sld_data.is_data
        sizer = wx.GridBagSizer(2, 3)
        ix = 0
        iy = -1
        for key, value in key_list.items():
            iy += 1
            ix = 0
            name = wx.StaticText(self, -1, key)
            sizer.Add(name, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ## add parameter value
            ix += 1
            ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER)
            ctl.Bind(wx.EVT_TEXT, self._onparamEnter)
            ctl.SetValue(format_number(value, True))
            ctl.Enable(not is_data)
            sizer.Add(ctl, (iy, ix), (1, 1), wx.EXPAND)
            ## add unit
            ix += 1
            unit = wx.StaticText(self, -1, '')
            sizer.Add(unit, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            self.nodes.append([key, ctl, unit])
        self.node_sizer.Add(sizer, 0, wx.LEFT, 10)

    def _layout_stepsize(self):
        """
        Fill the sizer containing slit size information
        """
        self.stepsize = []
        omfdata = self.sld_data
        if omfdata is None:
            raise
        key_list = self._get_step_key_list(omfdata)
        is_data = self.sld_data.is_data
        sizer = wx.GridBagSizer(2, 3)
        ix = 0
        iy = -1
        #key_list.sort()
        for key, value in key_list.items():
            iy += 1
            ix = 0
            name = wx.StaticText(self, -1, key)
            sizer.Add(name, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ## add parameter value
            ix += 1
            ctl = InputTextCtrl(self, -1, size=(_BOX_WIDTH, 20),
                                style=wx.TE_PROCESS_ENTER)
            ctl.Bind(wx.EVT_TEXT, self._onstepsize)
            ctl.SetValue(format_number(value, True))
            ctl.Enable(not is_data)
            sizer.Add(ctl, (iy, ix), (1, 1), wx.EXPAND)
            ## add unit
            ix += 1
            p_unit = '[' + omfdata.pos_unit + ']'
            unit = wx.StaticText(self, -1, p_unit)
            sizer.Add(unit, (iy, ix), (1, 1), \
                            wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            self.stepsize.append([key, ctl, unit])
        self.step_sizer.Add(sizer, 0, wx.LEFT, 10)

    def _layout_hint(self):
        """
        Fill the sizer containing hint
        """
        hint_msg = "Load an omf or 3d sld profile data file."
        self.hint_txt = wx.StaticText(self, -1, hint_msg)
        self.hint_sizer.AddMany([(self.hint_txt, 0, wx.LEFT, 15)])

    def _layout_button(self):
        """
        Do the layout for the button widgets
        """
        self.bt_draw = wx.Button(self, wx.NewId(), 'Draw Points')
        self.bt_draw.Bind(wx.EVT_BUTTON, self.on_sld_draw)
        self.bt_draw.SetToolTipString("Draw a scatter plot for sld profile.")
        self.bt_save = wx.Button(self, wx.NewId(), 'Save SLD Data')
        self.bt_save.Bind(wx.EVT_BUTTON, self.on_save)
        self.bt_save.Enable(False)
        self.bt_save.SetToolTipString("Save SLD data.")
        self.button_sizer.AddMany([(self.bt_draw, 0, wx.LEFT, 10),
                                   (self.bt_save, 0, wx.LEFT, 10)])

    def _do_layout(self):
        """
        Draw omf panel content, used to define sld s.

        """
        self._define_structure()
        self._layout_nodes()
        self._layout_stepsize()
        self._layout_npix()
        self._layout_slds()
        #self._layout_hint()
        self._layout_button()
        self.boxsizer_node.AddMany([(self.node_sizer, 0,
                                    wx.EXPAND | wx.TOP, 5),
                                     (self.hint_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.boxsizer_stepsize.AddMany([(self.step_sizer, 0,
                                     wx.EXPAND | wx.TOP | wx.BOTTOM, 5), ])
        self.boxsizer_sld.AddMany([(self.sld_sizer, 0,
                                     wx.EXPAND | wx.BOTTOM, 5), ])
        self.main_sizer.AddMany([(self.npixels_sizer, 0, wx.EXPAND | wx.ALL, 10),
                        (self.boxsizer_sld, 0, wx.EXPAND | wx.ALL, 10),
                        (self.boxsizer_node, 0, wx.EXPAND | wx.ALL, 10),
                        (self.boxsizer_stepsize, 0, wx.EXPAND | wx.ALL, 10),
                        (self.button_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)])
        self.SetSizer(self.main_sizer)
        self.SetAutoLayout(True)

    def _get_nodes_key_list(self, data):
        """
        Return nodes key list

        :Param data: OMFData
        """
        key_list = {'xnodes' : data.xnodes,
                    'ynodes' : data.ynodes,
                    'znodes' : data.znodes}
        return key_list

    def _get_slds_key_list(self, data):
        """
        Return nodes key list

        :Param data: OMFData
        """
        key_list = {'Nucl.' : data.sld_n,
                    'Mx' : data.sld_mx,
                    'My' : data.sld_my,
                    'Mz' : data.sld_mz}
        return key_list

    def _get_step_key_list(self, data):
        """
        Return step key list

        :Param data: OMFData
        """
        key_list = {'xstepsize' : data.xstepsize,
                    'ystepsize' : data.ystepsize,
                    'zstepsize' : data.zstepsize}
        return key_list

    def set_sld_ctr(self, sld_data):
        """
        Set sld textctrls
        """
        if sld_data is None:
            for ctr_list in self.slds:
                ctr_list[1].Enable(False)
                #break   
            return

        self.sld_data = sld_data
        sld_list = self._get_slds_key_list(sld_data)
        for ctr_list in self.slds:
            for key in list(sld_list.keys()):
                if ctr_list[0] == key:
                    min_val = np.min(sld_list[key])
                    max_val = np.max(sld_list[key])
                    mean_val = np.mean(sld_list[key])
                    enable = (min_val == max_val) and \
                             sld_data.pix_type == 'pixel'
                    ctr_list[1].SetValue(format_number(mean_val, True))
                    ctr_list[1].Enable(enable)
                    #ctr_list[2].SetLabel("[" + sld_data.sld_unit + "]")
                    break

    def on_sld_draw(self, event):
        """
        Draw sld profile as scattered plot
        """
        self.parent.sld_draw()

    def on_save(self, event):
        """
        Close the window containing this panel
        """
        flag = True
        flag = self.check_inputs()
        if not flag:
            return
        self.sld_data = self.get_sld_val()
        self.parent.set_main_panel_sld_data(self.sld_data)

        reader = sas_gen.SLDReader()
        extension = '*.sld'
        path = None
        data = None
        location = self.parent.get_path()
        dlg = wx.FileDialog(self, "Save sld file",
                            location, "sld_file",
                             extension,
                             wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.parent.set_file_location(os.path.dirname(path))
        else:
            return None
        dlg.Destroy()
        try:
            if path is None:
                return

            data = self.parent.get_sld_data()
            fName = os.path.splitext(path)[0] + '.' + extension.split('.')[-1]
            if data is not None:
                try:
                    reader.write(fName, data)
                except:
                    raise
            else:
                msg = "%s cannot write %s\n" % ('Generic Scattering', str(path))
                infor = 'Error'
                #logger.error(msg)
                if self.parent.parent is not None:
                    # inform msg to wx
                    wx.PostEvent(self.parent.parent,
                            StatusEvent(status=msg, info=infor))
                    self.SetFocus()
            return
        except:
            msg = "Error occurred while saving. "
            infor = 'Error'
            if self.parent.parent is not None:
                # inform msg to wx
                wx.PostEvent(self.parent.parent,
                        StatusEvent(status=msg, info=infor))
                self.SetFocus()

    def _onparamEnter(self, event):
        """
        """
        flag = True
        if event is not None:
            event.Skip()
            ctl = event.GetEventObject()
            ctl.SetBackgroundColour("white")
            #_set_error(self, ctl)
        try:
            float(ctl.GetValue())
        except:
            flag = _set_error(self, ctl)
        if flag:
            npts = 1
            for item in self.nodes:
                n_val = float(item[1].GetValue())
                if n_val <= 0:
                    item[1].SetBackgroundColour("pink")
                    npts = -1
                    break
                if np.isfinite(n_val):
                    npts *= int(n_val)
            if npts > 0:
                nop = self.set_npts_from_slddata()
                if nop is None:
                    nop = npts
                self.display_npts(nop)

        ctl.Refresh()
        return flag

    def _set_volume_ctr_val(self, npts):
        """
        Set total volume
        """
        total_volume = npts * self.sld_data.vol_pix[0]
        self.parent.set_volume_ctr_val(total_volume)

    def _onstepsize(self, event):
        """
        On stepsize event
        """
        flag = True
        if event is not None:
            event.Skip()
            ctl = event.GetEventObject()
            ctl.SetBackgroundColour("white")

        if flag and not self.sld_data.is_data:#ctl.IsEnabled():
            s_size = 1.0
            try:
                for item in self.stepsize:
                    s_val = float(item[1].GetValue())
                    if s_val <= 0:
                        item[1].SetBackgroundColour("pink")
                        ctl.Refresh()
                        return
                    if np.isfinite(s_val):
                        s_size *= s_val
                self.sld_data.set_pixel_volumes(s_size)
                if ctl.IsEnabled():
                    total_volume = sum(self.sld_data.vol_pix)
                    self.parent.set_volume_ctr_val(total_volume)
            except:
                pass
        ctl.Refresh()


    def set_npts_from_slddata(self):
        """
        Set total n. of points form the sld data
        """
        try:
            sld_data = self.parent.get_sld_from_omf()
            #nop = (nop * np.pi) / 6
            nop = len(sld_data.sld_n)
        except:
            nop = None
        return nop

    def display_npts(self, nop):
        """
        Displays Npts ctrl
        """
        try:
            self.npix_ctl.SetValue(str(nop))
            self.npix_ctl.Refresh()
            self.parent.set_etime()
            wx.CallAfter(self._set_volume_ctr_val, nop)
        except:
            # On Init
            pass

    def check_inputs(self):
        """
        check if the inputs are valid
        """
        flag = self._check_input_helper(self.slds)
        if flag:
            flag = self._check_input_helper(self.nodes)
        if flag:
            flag = self._check_input_helper(self.stepsize)
        return flag

    def _check_input_helper(self, list):
        """
        Check list values
        """
        flag = True
        for item in list:
            item[1].SetBackgroundColour("white")
            item[1].Refresh()
            try:
                float(item[1].GetValue())
            except:
                flag = _set_error(self, item[1])
                break
        return flag

class SasGenWindow(widget.CHILD_FRAME):
    """
    GEN SAS main window
    """
    def __init__(self, parent=None, manager=None, title="Generic Scattering Calculator",
                size=(PANEL_WIDTH * 1.4, PANEL_HEIGHT * 1.65), *args, **kwds):
        """
        Init
        """
        kwds['size'] = size
        kwds['title'] = title
        widget.CHILD_FRAME.__init__(self, parent, *args, **kwds)
        self.parent = parent
        self.base = manager
        self.omfpanel = OmfPanel(parent=self)
        self.panel = SasGenPanel(parent=self)
        self.data = None
        self.omfdata = sas_gen.OMFData()
        self.sld_data = None
        self._default_save_location = os.getcwd()

        self._mgr = aui.AuiManager(self)
        self._mgr.SetDockSizeConstraint(0.5, 0.5)
        self._plot_title = ''
        self.scale2d = 'log_{10}'
        self.Bind(wx.EVT_CLOSE, self.on_close)


        self.build_panels()
        self.SetPosition((wx.LEFT, PANEL_TOP))
        self.Show(True)

    def build_panels(self):
        """
        """

        self.set_sld_data(self.sld_data)
        self._mgr.AddPane(self.panel, aui.AuiPaneInfo().
                              Name(self.panel.window_name).
                              CenterPane().
                              # This is where we set the size of
                              # the application window
                              BestSize(wx.Size(PANEL_WIDTH,
                                               PANEL_HEIGHT)).
                              Show())
        self._mgr.AddPane(self.omfpanel, aui.AuiPaneInfo().
                              Name(self.omfpanel.window_name).
                              Caption(self.omfpanel.window_caption).
                              CloseButton(False).
                              Right().
                              Floatable(False).
                              BestSize(wx.Size(PANEL_WIDTH / 2.5, PANEL_HEIGHT)).
                              Show())
        self._mgr.Update()

    def get_sld_data(self):
        """
        Return slddata
        """
        return self.sld_data

    def get_sld_from_omf(self):
        """
        """
        self.sld_data = self.omfpanel.get_sld_val()
        return self.sld_data

    def set_sld_n(self, sld):
        """
        """
        self.panel.sld_data = sld
        self.panel.model.set_sld_data(sld)

    def set_sld_data(self, data):
        """
        Set omfdata
        """
        if data is None:
            return
        self.sld_data = data
        enable = (data is not None)
        self._set_omfpanel_sld_data(self.sld_data)
        self.omfpanel.bt_save.Enable(enable)
        self.set_etime()

    def set_omfpanel_npts(self):
        """
        Set Npts in omf panel
        """
        nop = self.omfpanel.set_npts_from_slddata()
        self.omfpanel.display_npts(nop)

    def _set_omfpanel_sld_data(self, data):
        """
        Set sld_data in omf panel
        """
        self.omfpanel.set_slddata(data)
        self.omfpanel.set_sld_ctr(data)

    def check_omfpanel_inputs(self):
        """
        Check OMF panel inputs
        """
        return self.omfpanel.check_inputs()

    def set_main_panel_sld_data(self, sld_data):
        """
        """
        self.sld_data = sld_data

    def set_file_location(self, path):
        """
        File location
        """
        self._default_save_location = path

    def get_path(self):
        """
        File location
        """
        return self._default_save_location

    def draw_graph(self, plot, title=''):
        """
        """
        try:
            wx.PostEvent(self.parent, NewPlotEvent(plot=plot, title=title))
        except:
            # standalone
            frame = PlotFrame(self, -1, 'testView', self.scale2d)
            #add_icon(self.parent, frame)
            frame.add_plot(plot)
            frame.SetTitle(title)
            frame.Show(True)
            frame.SetFocus()

    def set_schedule_full_draw(self, panel=None, func='del'):
        """
        Send full draw to gui frame
        """
        if self.parent is not None:
            self.parent.set_schedule_full_draw(panel, func)

    def get_npix(self):
        """
        Get no. of pixels from omf panel
        """
        n_pix = self.omfpanel.npix_ctl.GetValue()
        return n_pix

    def get_pix_volumes(self):
        """
        Get a pixel volume
        """
        vol = self.omfpanel.get_pix_volumes()
        return vol

    def set_volume_ctr_val(self, val):
        """
        Set volume txtctl value
        """
        try:
            self.panel.set_volume_ctl_val(str(val))
        except:
            print("self.panel is not initialized yet")

    def set_omfpanel_default_shap(self, shape):
        """
        Set default_shape in omfpanel
        """
        self.omfpanel.default_shape = shape

    def set_etime(self):
        """
        Sets est. computation time on panel
        """
        self.panel.set_est_time()

    def get_sld_data_from_omf(self):
        """
        """
        data = self.omfpanel.get_sld_val()
        return data

    def set_scale2d(self, scale):
        """
        """
        self.scale2d = scale

    def on_panel_close(self, event):
        """
        """
        #Not implemented

    def on_open_file(self, event):
        """
        On Open
        """
        self.panel.on_load_data(event)

    def sld_draw(self):
        """
        sld draw
        """
        self.panel.sld_draw(event=None, has_arrow=False)

    def on_save_file(self, event):
        """
        On Close
        """
        self.omfpanel.on_save(event)

    def on_close(self, event):
        """
        Close
        """
        if self.base is not None:
            self.base.gen_frame = None
        self.Destroy()

if __name__ == "__main__":
    app = wx.PySimpleApp()
    widget.CHILD_FRAME = wx.Frame
    SGframe = SasGenWindow()
    SGframe.Show(True)
    app.MainLoop()
