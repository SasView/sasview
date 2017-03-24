

import wx
import wx.lib.newevent
#from copy import deepcopy
from sas.sasgui.guiframe.events import EVT_SLICER_PARS
from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.events import EVT_SLICER
from sas.sasgui.guiframe.events import SlicerParameterEvent, SlicerEvent
from Plotter2D import ModelPanel2D


class SlicerParameterPanel(wx.Dialog):
    """
    Panel class to show the slicer parameters
    """
    #TODO: show units
    #TODO: order parameters properly

    def __init__(self, parent, *args, **kwargs):
        """
        Dialog window that allow to edit parameters slicer
        by entering new values
        """
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        self.params = {}
        self.parent = parent
        self.type = None
        self.listeners = []
        self.parameters = []
        self.bck = wx.GridBagSizer(5, 5)
        self.SetSizer(self.bck)
        label = "Right-click on 2D plot for slicer options"
        title = wx.StaticText(self, -1, label, style=wx.ALIGN_LEFT)
        self.bck.Add(title, (0, 0), (1, 2),
                     flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
        # Bindings
        self.parent.Bind(EVT_SLICER, self.onEVT_SLICER)
        self.parent.Bind(EVT_SLICER_PARS, self.onParamChange)

    def onEVT_SLICER(self, event):
        """
        Process EVT_SLICER events
        When the slicer changes, update the panel

        :param event: EVT_SLICER event
        """
        event.Skip()
        if event.obj_class is None:
            self.set_slicer(None, None)
        else:
            self.set_slicer(event.type, event.params)

    def set_slicer(self, type, params):
        """
        Rebuild the panel
        """
        self.bck.Clear(True)
        self.bck.Add((5, 5), (0, 0), (1, 1),
                     wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)
        self.type = type
        if type is None:
            label = "Right-click on 2D plot for slicer options"
            title = wx.StaticText(self, -1, label, style=wx.ALIGN_LEFT)
            self.bck.Add(title, (1, 0), (1, 2),
                         flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
        else:
            title = wx.StaticText(self, -1,
                                  "Slicer Parameters:", style=wx.ALIGN_LEFT)
            self.bck.Add(title, (1, 0), (1, 2),
                         flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
            ix = 0
            iy = 1
            self.parameters = []
            keys = params.keys()
            keys.sort()
            for item in keys:
                iy += 1
                ix = 0
                if not item in ["count", "errors"]:
                    text = wx.StaticText(self, -1, item, style=wx.ALIGN_LEFT)
                    self.bck.Add(text, (iy, ix), (1, 1),
                                 wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
                    ctl = wx.TextCtrl(self, -1, size=(80, 20),
                                      style=wx.TE_PROCESS_ENTER)
                    hint_msg = "Modify the value of %s to change" % item
                    hint_msg += " the 2D slicer"
                    ctl.SetToolTipString(hint_msg)
                    ix = 1
                    ctl.SetValue(format_number(str(params[item])))
                    self.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
                    self.parameters.append([item, ctl])
                    self.bck.Add(ctl, (iy, ix), (1, 1),
                                 wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                    ix = 3
                    self.bck.Add((20, 20), (iy, ix), (1, 1),
                                 wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                else:
                    text = wx.StaticText(self, -1, item + " : ",
                                         style=wx.ALIGN_LEFT)
                    self.bck.Add(text, (iy, ix), (1, 1),
                                 wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
                    ctl = wx.StaticText(self, -1,
                                        format_number(str(params[item])),
                                        style=wx.ALIGN_LEFT)
                    ix = 1
                    self.bck.Add(ctl, (iy, ix), (1, 1),
                                 wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ix = 0
            iy += 1

            # Change slicer within the window
            txt = "Slicer"
            text = wx.StaticText(self, -1, txt, style=wx.ALIGN_LEFT)
            self.bck.Add(text, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            type_list = ["SectorInteractor", "AnnulusInteractor",
                         "BoxInteractorX", "BoxInteractorY"]
            self.type_select = wx.ComboBox(parent=self, choices=type_list)
            self.Bind(wx.EVT_COMBOBOX, self.onChangeSlicer)
            index = self.type_select.FindString(self.type)
            self.type_select.SetSelection(index)
            self.bck.Add(self.type_select, (iy, 1), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

            # batch slicing parameters
            title_text = "Batch Slicing Options:"
            title = wx.StaticText(self, -1, title_text, style=wx.ALIGN_LEFT)
            iy += 1
            ln = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)
            ln.SetSize((60,60))
            self.bck.Add(ln, (iy, ix), (1, 2),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            iy += 1
            self.bck.Add(title, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            iy += 1
            id = wx.NewId()
            main_window = self.parent.parent
            self.loaded_data = main_window._data_manager.data_name_dict
            # TODO: remove 1D data from choices
            # TODO: auto check current data set
            choices = self.loaded_data.keys()
            self.data_list = wx.CheckListBox(parent=self, id=id,
                                        choices=choices,
                                        name="Apply Slicer to Data Sets:")
            self.bck.Add(self.data_list, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            iy += 1
            button_label = "Apply Slicer to Selected Files"
            self.batch_slicer_button = wx.Button(parent=self,
                                                 label=button_label)
            self.Bind(wx.EVT_BUTTON, self.onBatchSlice)
            self.bck.Add(self.batch_slicer_button, (iy, ix), (1, 1),
                             wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            # TODO: Check box for saving file
            # TODO: append to file information and file type
            # TODO: Send to fitting options

            iy += 1
            self.bck.Add((5, 5), (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)
        self.bck.Layout()
        self.bck.Fit(self)
        self.parent.GetSizer().Layout()

    def onParamChange(self, evt):
        """
        receive an event end reset value text fields
        inside self.parameters
        """
        evt.Skip()
        if evt.type == "UPDATE":
            for item in self.parameters:
                if item[0] in evt.params:
                    item[1].SetValue("%-5.3g" % evt.params[item[0]])
                    item[1].Refresh()

    def onTextEnter(self, evt):
        """
        Parameters have changed
        """
        params = {}
        has_error = False
        for item in self.parameters:
            try:
                params[item[0]] = float(item[1].GetValue())
                item[1].SetBackgroundColour(
                    wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
                item[1].Refresh()
            except:
                has_error = True
                item[1].SetBackgroundColour("pink")
                item[1].Refresh()

        if not has_error:
            # Post parameter event
            # parent here is plotter2D
            event = SlicerParameterEvent(type=self.type, params=params)
            wx.PostEvent(self.parent, event)

    def onBatchSlice(self, evt=None):
        """
        Batch slicing button is pushed
        :param evt: Event triggering hide/show of the batch slicer parameters
        """
        # Process each data file individually
        for item in self.data_list.CheckedStrings:
            # Get data_id
            num = len(item)
            spp = self.parent.parent
            data_panel = spp._data_panel
            data_list = data_panel.list_cb_data
            for key in data_list:
                loaded_key = (key[:num]) if len(key) > num else key
                if loaded_key == item:
                    selection = key
                    break
            # Check the data checkbox
            data_ctrl = data_list[selection][0]
            self.check_item_and_children(data_ctrl=data_ctrl, check_value=True)
            # Plot all checked data
            data_panel.on_plot()
            panel = plot_mgr = None
            plot_mgrs = spp.plot_panels
            for key, mgr in plot_mgrs.iteritems():
                if isinstance(mgr, ModelPanel2D):
                    plot_mgr = mgr
                    break
            if plot_mgr is not None:
                # TODO: find proper plot window
                panels = plot_mgr._manager.plot_panels
                for _, pane in panels.iteritems():
                    if pane.window_name == item:
                        panel = pane
                # TODO: apply slicer
                print(panels)
                if panel is not None:
                    self._apply_slicer_to_plot(panel)
            # TODO: save file (if desired)
            # TODO: send to fitting (if desired)

    def onChangeSlicer(self, evt):
        """
        Event driven slicer change when self.type_select changes
        :param evt: Event triggering this change
        """
        self._apply_slicer_to_plot(self.parent)

    def _apply_slicer_to_plot(self, plot):
        """
        Apply a slicer to *any* plot window, not just parent window
        :param plot:
        :return:
        """
        type = self.type_select.GetStringSelection()
        if self.type != type:
            if type == "SectorInteractor":
                plot.onSectorQ(None)
            elif type == "AnnulusInteractor":
                plot.onSectorPhi(None)
            elif type == "BoxInteractorX":
                plot.onBoxavgX(None)
            elif type == "BoxInteractorY":
                plot.onBoxavgY(None)

    def check_item_and_children(self, data_ctrl, check_value=True):
        self.parent.parent._data_panel.tree_ctrl.CheckItem(data_ctrl, check_value)
        if data_ctrl.HasChildren():
            if check_value and not data_ctrl.IsExpanded():
                # Only select children if control is expanded
                # Always deselect children, regardless (see ticket #259)
                return
            for child_ctrl in data_ctrl.GetChildren():
                self.tree_ctrl.CheckItem(child_ctrl, check_value)