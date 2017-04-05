

import wx
import wx.lib.newevent
import time
from sas.sasgui.guiframe.events import EVT_SLICER_PARS
from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.events import EVT_SLICER
from sas.sasgui.guiframe.events import SlicerParameterEvent, SlicerEvent
from Plotter2D import ModelPanel2D
from sas.sascalc.dataloader.data_info import Data1D, Data2D
ApplyParams, EVT_APPLY_PARAMS = wx.lib.newevent.NewEvent()


class SlicerParameterPanel(wx.Dialog):
    """
    Panel class to show the slicer parameters
    """
    # TODO: show units
    # TODO: order parameters properly

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
        self.Bind(EVT_APPLY_PARAMS, self.apply_params_list)

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
            # Create a list box with all of the 2D plots
            self.process_list()
            self.bck.Add(self.data_list, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            iy += 1
            # Button to start batch slicing
            button_label = "Apply Slicer to Selected Plots"
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
        Method invoked with batch slicing button is pressed
        :param evt: Event triggering hide/show of the batch slicer parameters
        """
        apply_to_list = []
        spp = self.parent.parent
        params = self.parent.slicer.get_params()
        type = self.type_select.GetStringSelection()

        # Find desired 2D data panels
        for key, mgr in spp.plot_panels.iteritems():
            if mgr.graph.prop['title'] in self.data_list.CheckedStrings:
                apply_to_list.append(mgr)

        # Apply slicer type to selected panels
        for item in apply_to_list:
            self._apply_slicer_to_plot(item, type)

        # Post an event to apply appropriate slicer params to each slicer
        # Event needed due to how apply_slicer_to_plot works
        event = ApplyParams(params=params, plot_list=apply_to_list)
        wx.PostEvent(self, event)
        # TODO: save file (if desired)
        # TODO: send to fitting (if desired)

    def onChangeSlicer(self, evt):
        """
        Event driven slicer change when self.type_select changes
        :param evt: Event triggering this change
        """
        self._apply_slicer_to_plot(self.parent)

    def _apply_slicer_to_plot(self, plot, type=None):
        """
        Apply a slicer to *any* plot window, not just parent window
        :param plot: 2D plot panel to apply a slicer to
        :param type: The type of slicer to apply to the panel
        """
        if type is None:
            type = self.type_select.GetStringSelection()
        if type == "SectorInteractor":
            plot.onSectorQ(None)
        elif type == "AnnulusInteractor":
            plot.onSectorPhi(None)
        elif type == "BoxInteractorX":
            plot.onBoxavgX(None)
        elif type == "BoxInteractorY":
            plot.onBoxavgY(None)

    def process_list(self):
        """
        Populate the check list from the currently plotted 2D data
        """
        self.checkme = None
        main_window = self.parent.parent
        self.loaded_data = []
        id = wx.NewId()
        # Iterate over the loaded plots and find all 2D panels
        for key, value in main_window.plot_panels.iteritems():
            if isinstance(value, ModelPanel2D):
                self.loaded_data.append(value.data2D.name)
                if value.data2D.id == self.parent.data2D.id:
                    # Set current plot panel as uncheckable
                    self.checkme = self.loaded_data.index(value.data2D.name)
        self.data_list = wx.CheckListBox(parent=self, id=id,
                                         choices=self.loaded_data,
                                         name="Apply Slicer to 2D Plots:")
        # Check all items bty default
        for item in range(len(self.data_list.Items)):
            self.data_list.Check(item)
        self.data_list.Bind(wx.EVT_CHECKLISTBOX, self.onCheckBoxList)

    def onCheckBoxList(self, e):
        """
        Prevent a checkbox item from being unchecked
        :param e: Event triggered when a checkbox list item is checked
        """
        index = e.GetSelection()
        if index == self.checkme:
            self.data_list.Check(index)

    def apply_params_list(self, evt=None):
        """
        Event based parameter setting.
        :param evt: Event triggered to apply parameters to a list of plots
                    evt should have attrs plot_list and params
        """
        # Apply parameter list to each plot as desired
        for item in evt.plot_list:
            item.slicer.set_params(evt.params)
            item.slicer.base.update()
        # Close the slicer window
        self.Destroy()
