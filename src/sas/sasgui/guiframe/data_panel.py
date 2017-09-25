################################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
#
# See the license text in license.txt
#
# copyright 2010, University of Tennessee
################################################################################
"""
This module provides Graphic interface for the data_manager module.
"""
from __future__ import print_function

import wx
from wx.build import build_options

import sys
from wx.lib.scrolledpanel import ScrolledPanel
import wx.lib.agw.customtreectrl as CT
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.guiframe.events import StatusEvent
from sas.sasgui.guiframe.events import EVT_DELETE_PLOTPANEL
from sas.sasgui.guiframe.events import NewLoadDataEvent
from sas.sasgui.guiframe.events import NewPlotEvent
from sas.sasgui.guiframe.gui_style import GUIFRAME
from sas.sasgui.guiframe.events import NewBatchEvent
from sas.sascalc.dataloader.loader import Loader
# from sas.sasgui.guiframe.local_perspectives.plotting.masking \
#    import FloatPanel as QucikPlotDialog
from sas.sasgui.guiframe.local_perspectives.plotting.SimplePlot \
    import PlotFrame as QucikPlotDialog
from sas import get_local_config

config = get_local_config()

# Check version
toks = str(wx.__version__).split('.')
if int(toks[1]) < 9:
    if int(toks[2]) < 12:
        wx_version = 811
    else:
        wx_version = 812
else:
    wx_version = 900

extension_list = []
if config.APPLICATION_STATE_EXTENSION is not None:
    extension_list.append(config.APPLICATION_STATE_EXTENSION)
EXTENSIONS = config.PLUGIN_STATE_EXTENSIONS + extension_list
PLUGINS_WLIST = config.PLUGINS_WLIST
APPLICATION_WLIST = config.APPLICATION_WLIST

# Control panel width
if sys.platform.count("win32") > 0:
    PANEL_WIDTH = 235
    PANEL_HEIGHT = 700
    CBOX_WIDTH = 140
    BUTTON_WIDTH = 80
    FONT_VARIANT = 0
    IS_MAC = False
else:
    PANEL_WIDTH = 255
    PANEL_HEIGHT = 750
    CBOX_WIDTH = 155
    BUTTON_WIDTH = 100
    FONT_VARIANT = 1
    IS_MAC = True

STYLE_FLAG = (wx.RAISED_BORDER | CT.TR_HAS_BUTTONS |
                    wx.WANTS_CHARS | CT.TR_HAS_VARIABLE_ROW_HEIGHT)


class DataTreeCtrl(CT.CustomTreeCtrl):
    """
    Check list control to be used for Data Panel
    """
    def __init__(self, parent, root, *args, **kwds):
        # agwstyle is introduced in wx.2.8.11 but is not working for mac
        if IS_MAC and wx_version < 812:
            try:
                kwds['style'] = STYLE_FLAG
                CT.CustomTreeCtrl.__init__(self, parent, *args, **kwds)
            except:
                del kwds['style']
                CT.CustomTreeCtrl.__init__(self, parent, *args, **kwds)
        else:
            # agwstyle is introduced in wx.2.8.11
            # argument working only for windows
            try:
                kwds['agwStyle'] = STYLE_FLAG
                CT.CustomTreeCtrl.__init__(self, parent, *args, **kwds)
            except:
                try:
                    del kwds['agwStyle']
                    kwds['style'] = STYLE_FLAG
                    CT.CustomTreeCtrl.__init__(self, parent, *args, **kwds)
                except:
                    del kwds['style']
                    CT.CustomTreeCtrl.__init__(self, parent, *args, **kwds)
        self.root = self.AddRoot(root)

    def OnCompareItems(self, item1, item2):
        """
        Overrides OnCompareItems in wx.TreeCtrl.
        Used by the SortChildren method.
        """
        # Get the item data
        data_1 = self.GetItemText(item1)
        data_2 = self.GetItemText(item2)
        # Compare the item data
        if data_1 < data_2:
            return -1
        elif data_1 > data_2:
            return 1
        else:
            return 0


class DataPanel(ScrolledPanel, PanelBase):
    """
    This panel displays data available in the application and widgets to
    interact with data.
    """
    # Internal name for the AUI manager
    window_name = "Data Panel"
    # Title to appear on top of the window
    window_caption = "Data Explorer"
    # type of window
    window_type = "Data Panel"
    # Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    # ALWAYS_ON = True

    def __init__(self, parent,
                 list=None,
                 size=(PANEL_WIDTH, PANEL_HEIGHT),
                 id=-1,
                 list_of_perspective=None, manager=None, *args, **kwds):
        # kwds['size'] = size
        # kwds['style'] = STYLE_FLAG
        ScrolledPanel.__init__(self, parent=parent, id=id, *args, **kwds)
        PanelBase.__init__(self, parent)
        self.SetupScrolling()
        # Set window's font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.loader = Loader()
        # Default location
        self._default_save_location = None
        self.all_data1d = True
        self.parent = parent.parent
        self._manager = manager
        self.frame = parent
        if list is None:
            list = []
        self.list_of_data = list
        if list_of_perspective is None:
            list_of_perspective = []
        self.list_of_perspective = list_of_perspective
        self.list_rb_perspectives = []
        self.list_cb_data = {}
        self.list_cb_theory = {}
        self.tree_ctrl = None
        self.tree_ctrl_theory = None
        self.perspective_cbox = None
        # Create context menu for page
        self.data_menu = None
        self.popUpMenu = None
        self.plot3d_id = None
        self.editmask_id = None
        # Default attr
        self.vbox = None
        self.sizer1 = None
        self.sizer2 = None
        self.sizer3 = None
        self.sizer4 = None
        self.sizer5 = None
        self.selection_cbox = None
        self.bt_add = None
        self.bt_remove = None
        self.bt_import = None
        self.bt_append_plot = None
        self.bt_plot = None
        self.bt_freeze = None
        self.cb_plotpanel = None
        self.rb_single_mode = None
        self.rb_batch_mode = None

        self.owner = None
        self.do_layout()
        self.fill_cbox_analysis(self.list_of_perspective)
        self.Bind(wx.EVT_SHOW, self.on_close_page)
        if self.parent is not None:
            self.parent.Bind(EVT_DELETE_PLOTPANEL, self._on_delete_plot_panel)

    def do_layout(self):
        """
            Create the panel layout
        """
        self.define_panel_structure()
        self.layout_selection()
        self.layout_data_list()
        self.layout_batch()
        self.layout_button()

    def disable_app_combo(self, enable):
        """
        Disable app combo box
        """
        self.perspective_cbox.Enable(enable)

    def define_panel_structure(self):
        """
        Define the skeleton of the panel
        """
        w, h = self.parent.GetSize()
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer1.SetMinSize(wx.Size(w/13, h*2/5))

        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer3 = wx.FlexGridSizer(9, 2, 4, 1)
        self.sizer4 = wx.BoxSizer(wx.VERTICAL)
        self.sizer5 = wx.BoxSizer(wx.VERTICAL)

        self.vbox.Add(self.sizer5, 0, wx.EXPAND | wx.ALL, 1)
        self.vbox.Add(self.sizer1, 1, wx.EXPAND | wx.ALL, 0)
        self.vbox.Add(self.sizer2, 0, wx.EXPAND | wx.ALL, 1)
        self.vbox.Add(self.sizer3, 0, wx.EXPAND | wx.ALL, 10)
        # self.vbox.Add(self.sizer4, 0, wx.EXPAND|wx.ALL,5)

        self.SetSizer(self.vbox)

    def layout_selection(self):
        """
            Create selection option combo box
        """
        select_txt = wx.StaticText(self, -1, 'Selection Options')
        select_txt.SetForegroundColour('blue')
        self.selection_cbox = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        list_of_options = ['Select all Data',
                           'Unselect all Data',
                           'Select all Data 1D',
                           'Unselect all Data 1D',
                           'Select all Data 2D',
                           'Unselect all Data 2D']
        for option in list_of_options:
            self.selection_cbox.Append(str(option))
        self.selection_cbox.SetValue('Select all Data')
        wx.EVT_COMBOBOX(self.selection_cbox, -1, self._on_selection_type)
        self.sizer5.AddMany([(select_txt, 0, wx.ALL, 5),
                            (self.selection_cbox, 0, wx.ALL, 5)])
        self.enable_selection()

    def _on_selection_type(self, event):
        """
            Select data according to patterns
            :param event: UI event
        """
        def check_item_and_children(control, check_value=True):
            self.tree_ctrl.CheckItem(data_ctrl, check_value)
            if data_ctrl.HasChildren():
                if check_value and not control.IsExpanded():
                    # Only select children if control is expanded
                    # Always deselect children, regardless (see ticket #259)
                    return
                for child_ctrl in data_ctrl.GetChildren():
                    self.tree_ctrl.CheckItem(child_ctrl, check_value)

        option = self.selection_cbox.GetValue()

        pos = self.selection_cbox.GetSelection()
        if pos == wx.NOT_FOUND:
            return
        option = self.selection_cbox.GetString(pos)
        for item in self.list_cb_data.values():
            data_ctrl, _, _, _, _, _, _, _ = item
            _, data_class, _ = self.tree_ctrl.GetItemPyData(data_ctrl)
            if option == 'Select all Data':
                check_item_and_children(data_ctrl, check_value=True)
            elif option == 'Unselect all Data':
                check_item_and_children(data_ctrl, check_value=False)
            elif option == 'Select all Data 1D':
                if data_class == 'Data1D':
                    check_item_and_children(data_ctrl, check_value=True)
            elif option == 'Unselect all Data 1D':
                if data_class == 'Data1D':
                    check_item_and_children(data_ctrl, check_value=False)
            elif option == 'Select all Data 2D':
                if data_class == 'Data2D':
                    check_item_and_children(data_ctrl, check_value=True)
            elif option == 'Unselect all Data 2D':
                if data_class == 'Data2D':
                    check_item_and_children(data_ctrl, check_value=False)
        self.enable_append()
        self.enable_freeze()
        self.enable_plot()
        self.enable_import()
        self.enable_remove()

    def layout_button(self):
        """
        Layout widgets related to buttons
        """
        # Load Data Button
        self.bt_add = wx.Button(self, wx.NewId(), "Load Data",
                                size=(BUTTON_WIDTH, -1))
        self.bt_add.SetToolTipString("Load data files")
        wx.EVT_BUTTON(self, self.bt_add.GetId(), self._load_data)

        # Delete Data Button
        self.bt_remove = wx.Button(self, wx.NewId(), "Delete Data",
                                   size=(BUTTON_WIDTH, -1))
        self.bt_remove.SetToolTipString("Delete data from the application")
        wx.EVT_BUTTON(self, self.bt_remove.GetId(), self.on_remove)

        # Send data to perspective button
        self.bt_import = wx.Button(self, wx.NewId(), "Send To",
                                   size=(BUTTON_WIDTH, -1))
        self.bt_import.SetToolTipString("Send Data set to active perspective")
        wx.EVT_BUTTON(self, self.bt_import.GetId(), self.on_import)

        # Choose perspective to be send data to combo box
        self.perspective_cbox = wx.ComboBox(self, -1,
                                            style=wx.CB_READONLY)
        if not IS_MAC:
            self.perspective_cbox.SetMinSize((BUTTON_WIDTH*1.6, -1))
        wx.EVT_COMBOBOX(self.perspective_cbox, -1,
                        self._on_perspective_selection)

        # Append data to current Graph Button
        self.bt_append_plot = wx.Button(self, wx.NewId(), "Append Plot To",
                                        size=(BUTTON_WIDTH, -1))
        self.bt_append_plot.SetToolTipString(
            "Plot the selected data in the active panel")
        wx.EVT_BUTTON(self, self.bt_append_plot.GetId(), self.on_append_plot)

        # Create a new graph and send data to that new graph button
        self.bt_plot = wx.Button(self, wx.NewId(), "New Plot",
                                 size=(BUTTON_WIDTH, -1))
        self.bt_plot.SetToolTipString("To trigger plotting")
        wx.EVT_BUTTON(self, self.bt_plot.GetId(), self.on_plot)

        # Freeze current theory button - becomes a data set and stays on graph
        self.bt_freeze = wx.Button(self, wx.NewId(), "Freeze Theory",
                                   size=(BUTTON_WIDTH, -1))
        freeze_tip = "To trigger freeze a theory: making a copy\n"
        freeze_tip += "of the theory checked to Data box,\n"
        freeze_tip += "     so that it can act like a real data set."
        self.bt_freeze.SetToolTipString(freeze_tip)
        wx.EVT_BUTTON(self, self.bt_freeze.GetId(), self.on_freeze)

        # select plot to send to combo box (blank if no data)
        if sys.platform == 'darwin':
            self.cb_plotpanel = wx.ComboBox(self, -1,
                                            style=wx.CB_READONLY)
        else:
            self.cb_plotpanel = wx.ComboBox(self, -1,
                                            style=wx.CB_READONLY | wx.CB_SORT)
        wx.EVT_COMBOBOX(self.cb_plotpanel, -1, self._on_plot_selection)
        self.cb_plotpanel.Disable()

        # Help button
        self.bt_help = wx.Button(self, wx.NewId(), "HELP",
                                 size=(BUTTON_WIDTH, -1))
        self.bt_help.SetToolTipString("Help for the Data Explorer.")
        wx.EVT_BUTTON(self, self.bt_help.GetId(), self.on_help)

        self.sizer3.AddMany([(self.bt_add),
                             ((10, 10)),
                             (self.bt_remove),
                             ((10, 10)),
                             (self.bt_freeze),
                             ((10, 10)),
                             (self.bt_plot),
                             ((10, 10)),
                             (self.bt_append_plot),
                             (self.cb_plotpanel,
                              wx.EXPAND | wx.ADJUST_MINSIZE, 5),
                             ((5, 5)),
                             ((5, 5)),
                             (self.bt_import, 0, wx.EXPAND | wx.RIGHT, 5),
                             (self.perspective_cbox,
                              wx.EXPAND | wx.ADJUST_MINSIZE, 5),
                             ((10, 10)),
                             (self.sizer4),
                             ((10, 10)),
                             (self.bt_help, 0, wx.RIGHT, 5)])

        self.sizer3.AddGrowableCol(1, 1)
        self.show_data_button()
        self.enable_remove()
        self.enable_import()
        self.enable_plot()
        self.enable_append()
        self.enable_freeze()
        self.enable_remove_plot()

    def layout_batch(self):
        """
            Set up batch mode options
        """
        self.rb_single_mode = wx.RadioButton(self, -1, 'Single Mode',
                                             style=wx.RB_GROUP)
        self.rb_batch_mode = wx.RadioButton(self, -1, 'Batch Mode')
        self.Bind(wx.EVT_RADIOBUTTON, self.on_single_mode,
                  id=self.rb_single_mode.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.on_batch_mode,
                  id=self.rb_batch_mode.GetId())

        self.rb_single_mode.SetValue(not self.parent.batch_on)
        self.rb_batch_mode.SetValue(self.parent.batch_on)
        self.sizer4.AddMany([(self.rb_single_mode, 0, wx.ALL, 4),
                             (self.rb_batch_mode, 0, wx.ALL, 4)])

    def on_single_mode(self, event):
        """
            Change to single mode
            :param event: UI event
        """
        if self.parent is not None:
            wx.PostEvent(self.parent, NewBatchEvent(enable=False))

    def on_batch_mode(self, event):
        """
            Change to batch mode
            :param event: UI event
        """
        if self.parent is not None:
            wx.PostEvent(self.parent,
                         NewBatchEvent(enable=True))

    def _get_data_selection(self, event):
        """
            Get data selection from the right click
            :param event: UI event
        """
        data = None
        # selection = event.GetSelection()
        id, _, _ = self.FindFocus().GetSelection().GetData()
        data_list, theory_list = \
            self.parent.get_data_manager().get_by_id(id_list=[id])
        if data_list:
            data = data_list.values()[0]
        if data is None:
            data = theory_list.values()[0][0]
        return data

    def on_edit_data(self, event):
        """
        Pop Up Data Editor
        """
        data = self._get_data_selection(event)
        from sas.sasgui.guiframe.local_perspectives.plotting.masking \
            import MaskPanel as MaskDialog

        panel = MaskDialog(parent=self.parent, base=self,
                           data=data, id=wx.NewId())
        panel.ShowModal()

    def on_plot_3d(self, event):
        """
        Frozen image of 3D
        """
        data = self._get_data_selection(event)
        from sas.sasgui.guiframe.local_perspectives.plotting.masking \
            import FloatPanel as Float3dDialog

        panel = Float3dDialog(base=self, data=data,
                              dimension=3, id=wx.NewId())
        panel.ShowModal()

    def on_quick_plot(self, event):
        """
        Frozen plot
        """
        data = self._get_data_selection(event)
        if data.__class__.__name__ == "Data2D":
            dimension = 2
        else:
            dimension = 1
        # panel = QucikPlotDialog(base=self, data=data,
        #                        dimension=dimension, id=wx.NewId())
        frame = QucikPlotDialog(self, -1, "Plot " + data.name, 'log_{10}')
        self.parent.put_icon(frame)
        frame.add_plot(data)
        # frame.SetTitle(title)
        frame.Show(True)
        frame.SetFocus()
        # panel.ShowModal()

    def on_data_info(self, event):
        """
        Data Info panel
        """
        data = self._get_data_selection(event)
        if data.__class__.__name__ == "Data2D":
            self.parent.show_data2d(data, data.name)
        else:
            self.parent.show_data1d(data, data.name)

    def on_save_as(self, event):
        """
        Save data as a file
        """
        data = self._get_data_selection(event)
        # path = None
        default_name = data.name
        if default_name.count('.') > 0:
            default_name = default_name.split('.')[0]
        default_name += "_out"
        if self.parent is not None:
            if issubclass(data.__class__, Data1D):
                self.parent.save_data1d(data, default_name)
            elif issubclass(data.__class__, Data2D):
                self.parent.save_data2d(data, default_name)
            else:
                print("unable to save this type of data")

    def layout_data_list(self):
        """
        Add a listcrtl in the panel
        """
        # Add splitter
        w, h = self.parent.GetSize()
        splitter = wx.SplitterWindow(self)
        splitter.SetMinimumPaneSize(50)
        splitter.SetSashGravity(1.0)

        file_sizer = wx.BoxSizer(wx.VERTICAL)
        file_sizer.SetMinSize(wx.Size(w/13, h*2/5))
        theory_sizer = wx.BoxSizer(wx.VERTICAL)
        theory_sizer.SetMinSize(wx.Size(w/13, h*2/5))

        self.tree_ctrl = DataTreeCtrl(parent=splitter,
                                      style=wx.SUNKEN_BORDER,
                                      root="Available Data")

        self.tree_ctrl.Bind(CT.EVT_TREE_ITEM_CHECKING, self.on_check_item)
        self.tree_ctrl.Bind(CT.EVT_TREE_ITEM_MENU, self.on_right_click_data)
        # Create context menu for page
        self.data_menu = wx.Menu()
        id = wx.NewId()
        name = "Data Info"
        msg = "Show Data Info"
        self.data_menu.Append(id, name, msg)
        wx.EVT_MENU(self, id, self.on_data_info)

        id = wx.NewId()
        name = "Save As"
        msg = "Save Theory/Data as a file"
        self.data_menu.Append(id, name, msg)
        wx.EVT_MENU(self, id, self.on_save_as)

        quickplot_id = wx.NewId()
        name = "Quick Plot"
        msg = "Plot the current Data"
        self.data_menu.Append(quickplot_id, name, msg)
        wx.EVT_MENU(self, quickplot_id, self.on_quick_plot)

        self.plot3d_id = wx.NewId()
        name = "Quick 3DPlot (Slow)"
        msg = "Plot3D the current 2D Data"
        self.data_menu.Append(self.plot3d_id, name, msg)
        wx.EVT_MENU(self, self.plot3d_id, self.on_plot_3d)

        self.editmask_id = wx.NewId()
        name = "Edit Mask"
        msg = "Edit Mask for the current 2D Data"
        self.data_menu.Append(self.editmask_id, name, msg)
        wx.EVT_MENU(self, self.editmask_id, self.on_edit_data)

        self.tree_ctrl_theory = DataTreeCtrl(parent=splitter,
                                             style=wx.SUNKEN_BORDER,
                                             root="Available Theory")
        self.tree_ctrl_theory.Bind(CT.EVT_TREE_ITEM_CHECKING,
                                   self.on_check_item)
        self.tree_ctrl_theory.Bind(CT.EVT_TREE_ITEM_MENU,
                                   self.on_right_click_theory)
        splitter.SplitHorizontally(self.tree_ctrl, self.tree_ctrl_theory)
        self.sizer1.Add(splitter, 1, wx.EXPAND | wx.ALL, 10)

    def on_right_click_theory(self, event):
        """
        On click theory data
        """
        try:
            id, data_class_name, _ = \
                            self.tree_ctrl_theory.GetSelection().GetData()
            _, _ = self.parent.get_data_manager().get_by_id(id_list=[id])
        except:
            return
        if self.data_menu is not None:
            menu_enable = (data_class_name == "Data2D")
            self.data_menu.Enable(self.editmask_id, False)
            self.data_menu.Enable(self.plot3d_id, menu_enable)
            self.PopupMenu(self.data_menu)

    def on_right_click_data(self, event):
        """
        Allow Editing Data
        """
        # selection = event.GetSelection()
        is_data = True
        try:
            id, data_class_name, _ = self.tree_ctrl.GetSelection().GetData()
            data_list, _ = \
                self.parent.get_data_manager().get_by_id(id_list=[id])
            if not data_list:
                is_data = False
        except:
            return
        if self.data_menu is not None:
            menu_enable = (data_class_name == "Data2D")
            maskmenu_enable = (menu_enable and is_data)
            self.data_menu.Enable(self.editmask_id, maskmenu_enable)
            self.data_menu.Enable(self.plot3d_id, menu_enable)
            self.PopupMenu(self.data_menu)

    def onContextMenu(self, event):
        """
        Retrieve the state selected state
        """
        # Skipping the save state functionality for release 0.9.0
        # return
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.popUpMenu, pos)

    def on_check_item(self, event):
        """
        On check item
        """
        item = event.GetItem()
        item.Check(not item.IsChecked())
        self.enable_append()
        self.enable_freeze()
        self.enable_plot()
        self.enable_import()
        self.enable_remove()
        event.Skip()

    def fill_cbox_analysis(self, plugin):
        """
        fill the combobox with analysis name
        """
        self.list_of_perspective = plugin
        if self.parent is None or \
            not hasattr(self.parent, "get_current_perspective") or \
                        len(self.list_of_perspective) == 0:
            return
        if self.parent is not None and self.perspective_cbox is not None:
            for plug in self.list_of_perspective:
                if plug.get_perspective():
                    self.perspective_cbox.Append(plug.sub_menu, plug)

            curr_pers = self.parent.get_current_perspective()
            if curr_pers:
                self.perspective_cbox.SetStringSelection(curr_pers.sub_menu)
                self.enable_import()

    def load_data_list(self, list):
        """
        add need data with its theory under the tree
        """
        if list:
            for state_id, dstate in list.iteritems():
                data = dstate.get_data()
                theory_list = dstate.get_theory()
                if data is not None:
                    data_name = str(data.name)
                    data_title = str(data.title)
                    data_run = str(data.run)
                    data_class = data.__class__.__name__
                    path = dstate.get_path()
                    process_list = data.process
                    data_id = data.id
                    s_path = str(path)
                    if state_id not in self.list_cb_data:
                        # new state
                        data_c = self.tree_ctrl.InsertItem(self.tree_ctrl.root,
                                                           0, data_name,
                                                           ct_type=1,
                                        data=(data_id, data_class, state_id))
                        data_c.Check(True)
                        d_i_c = self.tree_ctrl.AppendItem(data_c, 'Info')
                        d_t_c = self.tree_ctrl.AppendItem(d_i_c,
                                                          'Title: %s' %
                                                          data_title)
                        r_n_c = self.tree_ctrl.AppendItem(d_i_c,
                                                          'Run: %s' % data_run)
                        i_c_c = self.tree_ctrl.AppendItem(d_i_c,
                                                          'Type: %s' %
                                                          data_class)
                        p_c_c = self.tree_ctrl.AppendItem(d_i_c,
                                                          "Path: '%s'" % s_path)
                        d_p_c = self.tree_ctrl.AppendItem(d_i_c, 'Process')

                        for process in process_list:
                            process_str = str(process).replace('\n', ' ')
                            if len(process_str) > 20:
                                process_str = process_str[:20] + ' [...]'
                            self.tree_ctrl.AppendItem(d_p_c, process_str)
                        theory_child = self.tree_ctrl.AppendItem(data_c,
                                                                 "THEORIES")
                        self.list_cb_data[state_id] = [data_c,
                                                       d_i_c,
                                                       d_t_c,
                                                       r_n_c,
                                                       i_c_c,
                                                       p_c_c,
                                                       d_p_c,
                                                       theory_child]
                    else:
                        data_ctrl_list = self.list_cb_data[state_id]
                        # This state is already display replace it contains
                        data_c, d_i_c, d_t_c, r_n_c,  i_c_c, p_c_c, d_p_c, _ \
                                = data_ctrl_list
                        self.tree_ctrl.SetItemText(data_c, data_name)
                        temp = (data_id, data_class, state_id)
                        self.tree_ctrl.SetItemPyData(data_c, temp)
                        self.tree_ctrl.SetItemText(i_c_c,
                                                   'Type: %s' % data_class)
                        self.tree_ctrl.SetItemText(p_c_c,
                                                   'Path: %s' % s_path)
                        self.tree_ctrl.DeleteChildren(d_p_c)
                        for process in process_list:
                            if not process.is_empty():
                                _ = self.tree_ctrl.AppendItem(d_p_c,
                                                    process.single_line_desc())
                wx.CallAfter(self.append_theory, state_id, theory_list)
            # Sort by data name
            if self.tree_ctrl.root:
                self.tree_ctrl.SortChildren(self.tree_ctrl.root)
            # Expand root if # of data sets > 0
            if self.tree_ctrl.GetCount() > 0:
                self.tree_ctrl.root.Expand()
        self.enable_remove()
        self.enable_import()
        self.enable_plot()
        self.enable_freeze()
        self.enable_selection()

    def _uncheck_all(self):
        """
        Uncheck all check boxes
        """
        for item in self.list_cb_data.values():
            data_ctrl, _, _, _, _, _, _, _ = item
            self.tree_ctrl.CheckItem(data_ctrl, False)
        self.enable_append()
        self.enable_freeze()
        self.enable_plot()
        self.enable_import()
        self.enable_remove()

    def append_theory(self, state_id, theory_list):
        """
        append theory object under data from a state of id = state_id
        replace that theory if  already displayed
        """
        if not theory_list:
            return
        if state_id not in self.list_cb_data.keys():
            root = self.tree_ctrl_theory.root
            tree = self.tree_ctrl_theory
        else:
            item = self.list_cb_data[state_id]
            data_c, _, _, _, _, _, _, _ = item
            root = data_c
            tree = self.tree_ctrl
        if root is not None:
            wx.CallAfter(self.append_theory_helper, tree=tree, root=root,
                                       state_id=state_id,
                                       theory_list=theory_list)
        if self.tree_ctrl_theory.GetCount() > 0:
            self.tree_ctrl_theory.root.Expand()

    def append_theory_helper(self, tree, root, state_id, theory_list):
        """
        Append theory helper
        """
        if state_id in self.list_cb_theory.keys():
            # update current list of theory for this data
            theory_list_ctrl = self.list_cb_theory[state_id]

            for theory_id, item in theory_list.iteritems():
                theory_data, _ = item
                if theory_data is None:
                    name = "Unknown"
                    theory_class = "Unknown"
                    theory_id = "Unknown"
                    temp = (None, None, None)
                else:
                    name = theory_data.name
                    theory_class = theory_data.__class__.__name__
                    theory_id = theory_data.id
                    # if theory_state is not None:
                    #    name = theory_state.model.name
                    temp = (theory_id, theory_class, state_id)
                if theory_id not in theory_list_ctrl:
                    # add new theory
                    t_child = tree.AppendItem(root,
                                                    name, ct_type=1, data=temp)
                    t_i_c = tree.AppendItem(t_child, 'Info')
                    i_c_c = tree.AppendItem(t_i_c,
                                                  'Type: %s' % theory_class)
                    t_p_c = tree.AppendItem(t_i_c, 'Process')

                    for process in theory_data.process:
                        tree.AppendItem(t_p_c, process.__str__())
                    theory_list_ctrl[theory_id] = [t_child,
                                                   i_c_c,
                                                   t_p_c]
                else:
                    # replace theory
                    t_child, i_c_c, t_p_c = theory_list_ctrl[theory_id]
                    tree.SetItemText(t_child, name)
                    tree.SetItemPyData(t_child, temp)
                    tree.SetItemText(i_c_c, 'Type: %s' % theory_class)
                    tree.DeleteChildren(t_p_c)
                    for process in theory_data.process:
                        tree.AppendItem(t_p_c, process.__str__())

        else:
            # data didn't have a theory associated it before
            theory_list_ctrl = {}
            for theory_id, item in theory_list.iteritems():
                theory_data, _ = item
                if theory_data is not None:
                    name = theory_data.name
                    theory_class = theory_data.__class__.__name__
                    theory_id = theory_data.id
                    # if theory_state is not None:
                    #    name = theory_state.model.name
                    temp = (theory_id, theory_class, state_id)
                    t_child = tree.AppendItem(root,
                            name, ct_type=1,
                            data=(theory_data.id, theory_class, state_id))
                    t_i_c = tree.AppendItem(t_child, 'Info')
                    i_c_c = tree.AppendItem(t_i_c,
                                                  'Type: %s' % theory_class)
                    t_p_c = tree.AppendItem(t_i_c, 'Process')

                    for process in theory_data.process:
                        tree.AppendItem(t_p_c, process.__str__())

                    theory_list_ctrl[theory_id] = [t_child, i_c_c, t_p_c]
                # self.list_cb_theory[data_id] = theory_list_ctrl
                self.list_cb_theory[state_id] = theory_list_ctrl

    def set_data_helper(self):
        """
        Set data helper
        """
        data_to_plot = []
        state_to_plot = []
        theory_to_plot = []
        for value in self.list_cb_data.values():
            item, _, _, _, _, _, _,  _ = value
            if item.IsChecked():
                data_id, _, state_id = self.tree_ctrl.GetItemPyData(item)
                data_to_plot.append(data_id)
                if state_id not in state_to_plot:
                    state_to_plot.append(state_id)

        for theory_dict in self.list_cb_theory.values():
            for _, value in theory_dict.iteritems():
                item, _, _ = value
                if item.IsChecked():
                    theory_id, _, state_id = self.tree_ctrl.GetItemPyData(item)
                    theory_to_plot.append(theory_id)
                    if state_id not in state_to_plot:
                        state_to_plot.append(state_id)
        return data_to_plot, theory_to_plot, state_to_plot

    def remove_by_id(self, id):
        """
        Remove_dat by id
        """
        for item in self.list_cb_data.values():
            data_c, _, _, _, _, _,  _, _ = item
            data_id, _, state_id = self.tree_ctrl.GetItemPyData(data_c)
            if id == data_id:
                self.tree_ctrl.Delete(data_c)
                del self.list_cb_data[state_id]
                del self.list_cb_theory[data_id]

    def load_error(self, error=None):
        """
        Pop up an error message.

        :param error: details error message to be displayed
        """
        if error is not None or str(error).strip() != "":
            dial = wx.MessageDialog(self.parent, str(error),
                                    'Error Loading File',
                                    wx.OK | wx.ICON_EXCLAMATION)
            dial.ShowModal()

    def _load_data(self, event):
        """
        send an event to the parent to trigger load from plugin module
        """
        if self.parent is not None:
            wx.PostEvent(self.parent, NewLoadDataEvent())

    def on_remove(self, event, prompt=True):
        """
        Get a list of item checked and remove them from the treectrl
        Ask the parent to remove reference to this item
        """
        if prompt:
            msg = "This operation will delete the data sets checked "
            msg += "and all the dependents."
            msg_box = wx.MessageDialog(None, msg, 'Warning', wx.OK|wx.CANCEL)
            if msg_box.ShowModal() != wx.ID_OK:
                return

        data_to_remove, theory_to_remove, _ = self.set_data_helper()
        data_key = []
        theory_key = []
        # remove  data from treectrl
        for d_key, item in self.list_cb_data.iteritems():
            data_c, _, _, _,  _, _, _, _ = item
            if data_c.IsChecked():
                self.tree_ctrl.Delete(data_c)
                data_key.append(d_key)
                if d_key in self.list_cb_theory.keys():
                    theory_list_ctrl = self.list_cb_theory[d_key]
                    theory_to_remove += theory_list_ctrl.keys()
        # Remove theory from treectrl
        for _, theory_dict in self.list_cb_theory.iteritems():
            for key, value in theory_dict.iteritems():
                item, _, _ = value
                if item.IsChecked():
                    try:
                        self.tree_ctrl.Delete(item)
                    except:
                        pass
                    theory_key.append(key)

        # Remove data and related theory references
        for key in data_key:
            del self.list_cb_data[key]
            if key in theory_key:
                del self.list_cb_theory[key]
        # remove theory  references independently of data
        for key in theory_key:
            for _, theory_dict in self.list_cb_theory.iteritems():
                if key in theory_dict:
                    for key, value in theory_dict.iteritems():
                        item, _, _ = value
                        if item.IsChecked():
                            try:
                                self.tree_ctrl_theory.Delete(item)
                            except:
                                pass
                    del theory_dict[key]

        self.parent.remove_data(data_id=data_to_remove,
                                  theory_id=theory_to_remove)
        self.enable_remove()
        self.enable_freeze()
        self.enable_remove_plot()

    def on_import(self, event=None):
        """
        Get all select data and set them to the current active perspetive
        """
        if event is not None:
            event.Skip()
        data_id, theory_id, state_id = self.set_data_helper()
        temp = data_id + state_id
        self.parent.set_data(data_id=temp, theory_id=theory_id)

    def on_append_plot(self, event=None):
        """
        append plot to plot panel on focus
        """
        self._on_plot_selection()
        data_id, theory_id, state_id = self.set_data_helper()
        self.parent.plot_data(data_id=data_id,
                              state_id=state_id,
                              theory_id=theory_id,
                              append=True)

    def on_plot(self, event=None):
        """
        Send a list of data names to plot
        """
        data_id, theory_id, state_id = self.set_data_helper()
        self.parent.plot_data(data_id=data_id,
                              state_id=state_id,
                              theory_id=theory_id,
                              append=False)
        self.enable_remove_plot()

    def on_close_page(self, event=None):
        """
        On close
        """
        if event is not None:
            event.Skip()
        # send parent to update menu with no show nor hide action
        self.parent.show_data_panel(action=False)

    def on_freeze(self, event):
        """
        On freeze to make a theory to a data set
        """
        _, theory_id, state_id = self.set_data_helper()
        if len(theory_id) > 0:
            self.parent.freeze(data_id=state_id, theory_id=theory_id)
            msg = "Freeze Theory:"
            msg += " The theory(s) copied to the Data box as a data set."
        else:
            msg = "Freeze Theory: Requires at least one theory checked."
        wx.PostEvent(self.parent, StatusEvent(status=msg))

    def set_active_perspective(self, name):
        """
        set the active perspective
        """
        self.perspective_cbox.SetStringSelection(name)
        self.enable_import()

    def _on_delete_plot_panel(self, event):
        """
        get an event with attribute name and caption to delete existing name
        from the combobox of the current panel
        """
        # name = event.name
        caption = event.caption
        if self.cb_plotpanel is not None:
            pos = self.cb_plotpanel.FindString(str(caption))
            if pos != wx.NOT_FOUND:
                self.cb_plotpanel.Delete(pos)
        self.enable_append()

    def set_panel_on_focus(self, name=None):
        """
        set the plot panel on focus
        """
        if self.cb_plotpanel and self.cb_plotpanel.IsBeingDeleted():
            return
        for _, value in self.parent.plot_panels.iteritems():
            name_plot_panel = str(value.window_caption)
            if name_plot_panel not in self.cb_plotpanel.GetItems():
                self.cb_plotpanel.Append(name_plot_panel, value)
            if name is not None and name == name_plot_panel:
                self.cb_plotpanel.SetStringSelection(name_plot_panel)
                break
        self.enable_append()
        self.enable_remove_plot()

    def set_plot_unfocus(self):
        """
        Unfocus plot
        """
        return

    def _on_perspective_selection(self, event=None):
        """
        select the current perspective for guiframe
        """
        selection = self.perspective_cbox.GetSelection()
        if self.perspective_cbox.GetValue() != 'None':
            perspective = self.perspective_cbox.GetClientData(selection)
            perspective.on_perspective(event=None)
            self.parent.check_multimode(perspective=perspective)

    def _on_plot_selection(self, event=None):
        """
        On source combobox selection
        """
        if event is not None:
            combo = event.GetEventObject()
            event.Skip()
        else:
            combo = self.cb_plotpanel
        selection = combo.GetSelection()

        if combo.GetValue() != 'None':
            panel = combo.GetClientData(selection)
            self.parent.on_set_plot_focus(panel)

    def on_close_plot(self, event):
        """
        clseo the panel on focus
        """
        self.enable_append()
        selection = self.cb_plotpanel.GetSelection()
        if self.cb_plotpanel.GetValue() != 'None':
            panel = self.cb_plotpanel.GetClientData(selection)
            if self.parent is not None and panel is not None:
                wx.PostEvent(self.parent,
                             NewPlotEvent(group_id=panel.group_id,
                                          action="delete"))
        self.enable_remove_plot()

    def set_frame(self, frame):
        """
        """
        self.frame = frame

    def get_frame(self):
        """
        """
        return self.frame

    def on_help(self, event):
        """
        Bring up the data manager Documentation whenever
        the HELP button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param event: Triggers on clicking the help button
    """

        #import documentation window here to avoid circular imports
        #if put at top of file with rest of imports.
        from documentation_window import DocumentationWindow

        _TreeLocation = "user/sasgui/guiframe/data_explorer_help.html"
        _doc_viewer = DocumentationWindow(self, -1, _TreeLocation, "",
                                          "Data Explorer Help")

    def on_close(self, event):
        """
        On close event
        """
        self.parent.show_data_panel(event)

    def set_schedule_full_draw(self, panel=None, func='del'):
        """
        Send full draw to guimanager
        """
        self.parent.set_schedule_full_draw(panel, func)

    def enable_remove_plot(self):
        """
        enable remove plot button if there is a plot panel on focus
        """
        pass
        #if self.cb_plotpanel.GetCount() == 0:
        #    self.bt_close_plot.Disable()
        #else:
        #    self.bt_close_plot.Enable()

    def enable_remove(self):
        """
        enable or disable remove button
        """
        n_t = self.tree_ctrl.GetCount()
        n_t_t = self.tree_ctrl_theory.GetCount()
        if n_t + n_t_t <= 0:
            self.bt_remove.Disable()
        else:
            self.bt_remove.Enable()

    def enable_import(self):
        """
        enable or disable send button
        """
        n_t = 0
        if self.tree_ctrl is not None:
            n_t = self.tree_ctrl.GetCount()
        if n_t > 0 and len(self.list_of_perspective) > 0:
            self.bt_import.Enable()
        else:
            self.bt_import.Disable()
        if len(self.list_of_perspective) <= 0 or \
            self.perspective_cbox.GetValue()  in ["None",
                                                "No Active Application"]:
            self.perspective_cbox.Disable()
        else:
            self.perspective_cbox.Enable()

    def enable_plot(self):
        """
        enable or disable plot button
        """
        n_t = 0
        n_t_t = 0
        if self.tree_ctrl is not None:
            n_t = self.tree_ctrl.GetCount()
        if self.tree_ctrl_theory is not None:
            n_t_t = self.tree_ctrl_theory.GetCount()
        if n_t + n_t_t <= 0:
            self.bt_plot.Disable()
        else:
            self.bt_plot.Enable()
        self.enable_append()

    def enable_append(self):
        """
        enable or disable append button
        """
        n_t = 0
        n_t_t = 0
        if self.tree_ctrl is not None:
            n_t = self.tree_ctrl.GetCount()
        if self.tree_ctrl_theory is not None:
            n_t_t = self.tree_ctrl_theory.GetCount()
        if n_t + n_t_t <= 0:
            self.bt_append_plot.Disable()
            self.cb_plotpanel.Disable()
        elif self.cb_plotpanel.GetCount() <= 0:
            self.cb_plotpanel.Disable()
            self.bt_append_plot.Disable()
        else:
            self.bt_append_plot.Enable()
            self.cb_plotpanel.Enable()

    def check_theory_to_freeze(self):
        """
        Check_theory_to_freeze
        """
    def enable_freeze(self):
        """
        enable or disable the freeze button
        """
        n_t_t = 0
        n_l = 0
        if self.tree_ctrl_theory is not None:
            n_t_t = self.tree_ctrl_theory.GetCount()
        n_l = len(self.list_cb_theory)
        if (n_t_t + n_l > 0):
            self.bt_freeze.Enable()
        else:
            self.bt_freeze.Disable()

    def enable_selection(self):
        """
        enable or disable combobo box selection
        """
        n_t = 0
        n_t_t = 0
        if self.tree_ctrl is not None:
            n_t = self.tree_ctrl.GetCount()
        if self.tree_ctrl_theory is not None:
            n_t_t = self.tree_ctrl_theory.GetCount()
        if n_t + n_t_t > 0 and self.selection_cbox is not None:
            self.selection_cbox.Enable()
        else:
            self.selection_cbox.Disable()

    def show_data_button(self):
        """
        show load data and remove data button if
        dataloader on else hide them
        """
        try:
            gui_style = self.parent.get_style()
            style = gui_style & GUIFRAME.DATALOADER_ON
            if style == GUIFRAME.DATALOADER_ON:
                #self.bt_remove.Show(True)
                self.bt_add.Show(True)
            else:
                #self.bt_remove.Hide()
                self.bt_add.Hide()
        except:
            #self.bt_remove.Hide()
            self.bt_add.Hide()


WIDTH = 400
HEIGHT = 300


class DataDialog(wx.Dialog):
    """
    Allow file selection at loading time
    """
    def __init__(self, data_list, parent=None, text='', *args, **kwds):
        wx.Dialog.__init__(self, parent, *args, **kwds)
        self.SetTitle("Data Selection")
        self.SetSize((WIDTH, HEIGHT))
        self.list_of_ctrl = []
        if not data_list:
            return
        self._sizer_main = wx.BoxSizer(wx.VERTICAL)
        self._sizer_txt = wx.BoxSizer(wx.VERTICAL)
        self._sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer = wx.GridBagSizer(5, 5)
        self._panel = ScrolledPanel(self, style=wx.RAISED_BORDER,
                               size=(WIDTH-20, HEIGHT-50))
        self._panel.SetupScrolling()
        self.__do_layout(data_list, text=text)

    def __do_layout(self, data_list, text=''):
        """
        layout the dialog
        """
        if not data_list or len(data_list) <= 1:
            return
        # add text

        text = "Deleting these file reset some panels.\n"
        text += "Do you want to proceed?\n"
        text_ctrl = wx.StaticText(self, -1, str(text))
        self._sizer_txt.Add(text_ctrl)
        iy = 0
        ix = 0
        # data_count = 0
        for (data_name, in_use, sub_menu) in range(len(data_list)):
            if in_use:
                ctrl_name = wx.StaticBox(self, -1, str(data_name))
                ctrl_in_use = wx.StaticBox(self, -1, " is used by ")
                plug_name = str(sub_menu) + "\n"
                # ctrl_sub_menu = wx.StaticBox(self, -1, plug_name)
                self.sizer.Add(ctrl_name, (iy, ix),
                           (1, 1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                ix += 1
                self._sizer_button.Add(ctrl_in_use, 1,
                                        wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ix += 1
                self._sizer_button.Add(plug_name, 1,
                                        wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            iy += 1
        self._panel.SetSizer(self.sizer)
        # add sizer
        self._sizer_button.Add((20, 20), 1, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        button_cancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self._sizer_button.Add(button_cancel, 0,
                          wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        button_OK = wx.Button(self, wx.ID_OK, "Ok")
        button_OK.SetFocus()
        self._sizer_button.Add(button_OK, 0,
                                wx.LEFT|wx.RIGHT|wx.ADJUST_MINSIZE, 10)
        static_line = wx.StaticLine(self, -1)

        self._sizer_txt.Add(self._panel, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        self._sizer_main.Add(self._sizer_txt, 1, wx.EXPAND|wx.ALL, 10)
        #self._sizer_main.Add(self._data_text_ctrl, 0,
        #                     wx.EXPAND|wx.LEFT|wx.RIGHT, 10)
        self._sizer_main.Add(static_line, 0, wx.EXPAND, 0)
        self._sizer_main.Add(self._sizer_button, 0, wx.EXPAND|wx.ALL, 10)
        self.SetSizer(self._sizer_main)
        self.Layout()

    def get_data(self):
        """
        return the selected data
        """
        temp = []
        for item in self.list_of_ctrl:
            cb, data = item
            if cb.GetValue():
                temp.append(data)
        return temp

class DataFrame(wx.Frame):
    """
    Data Frame
    """
    ## Internal name for the AUI manager
    window_name = "Data Panel"
    ## Title to appear on top of the window
    window_caption = "Data Panel"
    ## Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    ALWAYS_ON = True

    def __init__(self, parent=None, owner=None, manager=None, size=(300, 800),
                         list_of_perspective=[], list=[], *args, **kwds):
        kwds['size'] = size
        kwds['id'] = -1
        kwds['title'] = "Loaded Data"
        wx.Frame.__init__(self, parent=parent, *args, **kwds)
        self.parent = parent
        self.owner = owner
        self._manager = manager
        self.panel = DataPanel(parent=self,
                               manager=manager,
                               list_of_perspective=list_of_perspective)

    def load_data_list(self, list=[]):
        """
        Fill the list inside its panel
        """
        self.panel.load_data_list(list=list)


from sas.sasgui.guiframe.dataFitting import Theory1D
from sas.sasgui.guiframe.data_state import DataState


class State():
    """
    DataPanel State
    """
    def __init__(self):
        self.msg = ""
    def __str__(self):
        self.msg = "model mane : model1\n"
        self.msg += "params : \n"
        self.msg += "name  value\n"
        return self.msg


def set_data_state(data=None, path=None, theory=None, state=None):
    """
    Set data state
    """
    dstate = DataState(data=data)
    dstate.set_path(path=path)
    dstate.set_theory(theory, state)

    return dstate

if __name__ == "__main__":

    app = wx.App()
    try:
        # list_of_perspective = [('perspective2', False), ('perspective1', True)]
        data_list1 = {}
        # state 1
        data1 = Data2D()
        data1.name = "data2"
        data1.id = 1
        data1.append_empty_process()
        process1 = data1.process[len(data1.process)-1]
        process1.data = "07/01/2010"
        theory1 = Data2D()
        theory1.id = 34
        theory1.name = "theory1"
        path1 = "path1"
        state1 = State()
        data_list1['1'] = set_data_state(data1, path1, theory1, state1)
        # state 2
        data1 = Data2D()
        data1.name = "data2"
        data1.id = 76
        theory1 = Data2D()
        theory1.id = 78
        theory1.name = "CoreShell 07/24/25"
        path1 = "path2"
        # state3
        state1 = State()
        data_list1['2'] = set_data_state(data1, path1, theory1, state1)
        data1 = Data1D()
        data1.id = 3
        data1.name = "data2"
        theory1 = Theory1D()
        theory1.name = "CoreShell"
        theory1.id = 4
        theory1.append_empty_process()
        process1 = theory1.process[len(theory1.process)-1]
        process1.description = "this is my description"
        path1 = "path3"
        data1.append_empty_process()
        process1 = data1.process[len(data1.process)-1]
        process1.data = "07/22/2010"
        data_list1['4'] = set_data_state(data1, path1, theory1, state1)
        # state 4
        temp_data_list = {}
        data1.name = "data5 erasing data2"
        temp_data_list['4'] = set_data_state(data1, path1, theory1, state1)
        # state 5
        data1 = Data2D()
        data1.name = "data3"
        data1.id = 5
        data1.append_empty_process()
        process1 = data1.process[len(data1.process)-1]
        process1.data = "07/01/2010"
        theory1 = Theory1D()
        theory1.name = "Cylinder"
        path1 = "path2"
        state1 = State()
        dstate1 = set_data_state(data1, path1, theory1, state1)
        theory1 = Theory1D()
        theory1.id = 6
        theory1.name = "CoreShell"
        dstate1.set_theory(theory1)
        theory1 = Theory1D()
        theory1.id = 6
        theory1.name = "CoreShell replacing coreshell in data3"
        dstate1.set_theory(theory1)
        data_list1['3'] = dstate1
        #state 6
        data_list1['6'] = set_data_state(None, path1, theory1, state1)
        data_list1['6'] = set_data_state(theory=theory1, state=None)
        theory1 = Theory1D()
        theory1.id = 7
        data_list1['6'] = set_data_state(theory=theory1, state=None)
        data_list1['7'] = set_data_state(theory=theory1, state=None)
        window = DataFrame(list=data_list1)
        window.load_data_list(list=data_list1)
        window.Show(True)
        window.load_data_list(list=temp_data_list)
    except:
        # raise
        print("error", sys.exc_value)

    app.MainLoop()
