

import os
import wx
import wx.lib.newevent
from sas.sascalc.dataloader.readers.cansas_reader import Reader
from sas.sasgui.guiframe.utils import format_number
from sas.sasgui.guiframe.events import EVT_SLICER_PARS, EVT_SLICER
from sas.sasgui.guiframe.events import SlicerParameterEvent, StatusEvent
from Plotter2D import ModelPanel2D
apply_params, EVT_APPLY_PARAMS = wx.lib.newevent.NewEvent()
save_files, EVT_AUTO_SAVE = wx.lib.newevent.NewEvent()

FIT_OPTIONS = ["No fitting", "Fitting", "Batch Fitting"]
CONVERT_KEYS = ["SectorInteractor", "AnnulusInteractor", "BoxInteractorX",
                "BoxInteractorY"]
CONVERT_DICT = {"SectorInteractor": "SectorQ",
                "AnnulusInteractor": "AnnulusPhi",
                "BoxInteractorX": "SlabX",
                "BoxInteractorY": "SlabY"}
BINNING_OPTIONS = {"Linear" : 0,
                   "Logarithmic" : 10,}


class SlicerParameterPanel(wx.Dialog):
    """
    Panel for dynamically changing slicer parameters and apply the same slicer
    to multiple 2D plot panels
    """

    def __init__(self, parent, *args, **kwargs):
        """
        Dialog window that allow to edit parameters slicer
        by entering new values
        """
        wx.Dialog.__init__(self, parent, *args, **kwargs)
        self.params = {}
        self.iter = 0
        self.parent = parent
        self.main_window = parent.parent
        self.data_panel = self.main_window._data_panel
        self.type = None
        self.listeners = []
        self.parameters = []
        self.bck = wx.GridBagSizer(5, 5)
        self.SetSizer(self.bck)
        self.auto_save = None
        self.path = None
        self.fitting_options = None
        self.bin_ctl = None
        self.type_list = []
        self.loaded_data = []
        self.always_on = None
        self.type_select = None
        self.append_name = None
        self.data_list = None
        self.default_value = ""
        self.batch_slicer_button = None
        label = "Right-click on 2D plot for slicer options"
        title = wx.StaticText(self, -1, label, style=wx.ALIGN_LEFT)
        self.bck.Add(title, (0, 0), (1, 2),
                     flag=wx.LEFT | wx.ALIGN_CENTER_VERTICAL, border=15)
        # Bindings
        self.parent.Bind(EVT_SLICER, self.on_evt_slicer)
        self.Bind(EVT_SLICER_PARS, self.on_param_change)
        self.Bind(EVT_APPLY_PARAMS, self.apply_params_list_and_process)
        self.Bind(EVT_AUTO_SAVE, self.save_files)

    def on_evt_slicer(self, event):
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
                ix = 0
                iy += 1
                if item not in ["count", "errors", "binning base"]:
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
                    self.Bind(wx.EVT_TEXT_ENTER, self.on_text_enter)
                    self.parameters.append([item, ctl])
                    self.bck.Add(ctl, (iy, ix), (1, 1),
                                 wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                    ix = 3
                    self.bck.Add((20, 20), (iy, ix), (1, 1),
                                 wx.EXPAND | wx.ADJUST_MINSIZE, 0)
                elif item == 'binning base':
                    text = wx.StaticText(self, -1, item, style=wx.ALIGN_LEFT)
                    self.bck.Add(text, (iy, ix), (1, 1),
                                 wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
                    options = BINNING_OPTIONS.keys()
                    self.bin_ctl = wx.ComboBox(parent=self, choices=options)
                    hint_msg = "Modify the value of %s to change" % item
                    hint_msg += " the 2D slicer"
                    self.bin_ctl.SetToolTipString(hint_msg)
                    ix = 1
                    result = ""
                    value = 0
                    for name, value in BINNING_OPTIONS.items():
                        if value == params[item]:
                            result = name
                            break
                    index = self.bin_ctl.FindString(result)
                    self.bin_ctl.SetSelection(index)
                    self.parameters.append([item, self.bin_ctl])
                    self.Bind(wx.EVT_COMBOBOX, self.on_text_enter)
                    self.bck.Add(self.bin_ctl, (iy, ix), (1, 1),
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

            # Change slicer within the window
            ix = 0
            iy += 1
            txt = "Slicer type"
            text = wx.StaticText(self, -1, txt, style=wx.ALIGN_LEFT)
            self.bck.Add(text, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            self.type_list = CONVERT_KEYS
            self.type_select = wx.ComboBox(parent=self, choices=self.type_list)
            self.type_select.Bind(wx.EVT_COMBOBOX, self.on_change_slicer)
            index = self.type_select.FindString(type)
            self.type_select.SetSelection(index)
            self.bck.Add(self.type_select, (iy, 1), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

            # batch slicing parameters
            title_text = "Batch Slicing Options:"
            title = wx.StaticText(self, -1, title_text, style=wx.ALIGN_LEFT)
            iy += 1
            line = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)
            line.SetSize((60, 60))
            self.bck.Add(line, (iy, ix), (1, 2),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            iy += 1
            self.bck.Add(title, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

            # Create a list box with all of the 2D plots
            iy += 1
            self.process_list()
            self.bck.Add(self.data_list, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

            # Checkbox to enable saving and fitting options
            iy += 1
            self.auto_save = wx.CheckBox(parent=self, id=wx.NewId(),
                                         label="Auto save generated 1D:")
            self.Bind(wx.EVT_CHECKBOX, self.on_auto_save_checked)
            self.bck.Add(self.auto_save, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            iy += 1
            # File browser
            save_to = "Save files to:"
            save = wx.StaticText(self, -1, save_to, style=wx.ALIGN_LEFT)
            path = os.getcwd()
            self.path = wx.DirPickerCtrl(self, id=wx.NewId(), path=path,
                                         message=save_to)
            self.path.Enable(False)
            self.bck.Add(save, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            self.bck.Add(self.path, (iy, 1), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            # Append to file
            iy += 1
            self.update_file_append(params)
            append_text = "Append to file name:"
            append = wx.StaticText(self, -1, append_text, style=wx.ALIGN_LEFT)
            self.append_name = wx.TextCtrl(parent=self, id=wx.NewId(),
                                           name="Append to file name:")
            append_tool_tip = "Files will be saved as <SlicerType><FileName>"
            append_tool_tip += "<AppendToText>.txt"
            self.append_name.SetToolTipString(append_tool_tip)
            self.append_name.SetValue(self.default_value)
            self.append_name.Enable(False)
            self.bck.Add(append, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            self.bck.Add(self.append_name, (iy, 1), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

            # Combobox for selecting fitting options
            iy += 1
            fit_text = "Fitting Options:"
            fit_text_item = wx.StaticText(self, -1, fit_text,
                                          style=wx.ALIGN_LEFT)
            self.bck.Add(fit_text_item, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            self.fitting_options = wx.ComboBox(parent=self, choices=FIT_OPTIONS)
            self.fitting_options.SetSelection(0)
            self.bck.Add(self.fitting_options, (iy, 1), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            self.fitting_options.Enable(False)
            self.fitting_options.Bind(wx.EVT_COMBOBOX, None)

            # Button to start batch slicing
            iy += 1
            button_label = "Apply Slicer to Selected Plots"
            self.batch_slicer_button = wx.Button(parent=self,
                                                 label=button_label)
            self.Bind(wx.EVT_BUTTON, self.on_batch_slicer)
            self.bck.Add(self.batch_slicer_button, (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            iy += 1
            self.bck.Add((5, 5), (iy, ix), (1, 1),
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 5)
        self.bck.Layout()
        self.bck.Fit(self)
        self.parent.GetSizer().Layout()

    def on_param_change(self, evt):
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

    def on_text_enter(self, evt):
        """
        Parameters have changed
        """
        params = {}
        has_error = False
        for item in self.parameters:
            try:
                if item[0] == "binning base":
                    title = self.bin_ctl.GetValue()
                    params["binning base"] = BINNING_OPTIONS.get(title)
                    continue
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
            self.update_file_append(params)
            self.append_name.SetValue(self.default_value)
            self.append_name.Refresh()
            event = SlicerParameterEvent(type=self.type, params=params)
            wx.PostEvent(self.parent, event)

    def on_batch_slicer(self, evt=None):
        """
        Event triggered when batch slicing button is pressed
        :param evt: Event triggering the batch slicing
        """
        apply_to_list = []
        spp = self.parent.parent
        params = self.parent.slicer.get_params()
        slicer_type = self.type_select.GetStringSelection()
        save = self.auto_save.IsChecked()
        append = self.append_name.GetValue()
        path = self.path.GetPath()
        fit = self.fitting_options.GetValue()

        # Find desired 2D data panels
        for key, mgr in spp.plot_panels.iteritems():
            if mgr.graph.prop['title'] in self.data_list.CheckedStrings:
                apply_to_list.append(mgr)

        # Apply slicer type to selected panels
        for item in apply_to_list:
            self._apply_slicer_to_plot(item, slicer_type)

        # Post an event to apply appropriate slicer params to each slicer
        # Pass all variables, including class variables
        event_params = apply_params(params=params, apply_to_list=apply_to_list,
                                    auto_save=save, append=append, fit=fit,
                                    path=path, type=slicer_type)
        wx.PostEvent(self, event_params)

    def on_change_slicer(self, evt):
        """
        Event driven slicer change when self.type_select changes
        :param evt: Event triggering this change
        """
        self._apply_slicer_to_plot(self.parent)

    def _apply_slicer_to_plot(self, plot, slicer_type=None):
        """
        Apply a slicer to *any* plot window, not just parent window
        :param plot: 2D plot panel to apply a slicer to
        :param slicer_type: The type of slicer to apply to the panel
        """
        # Skip redrawing the current plot if no change in slicer type
        if self.parent == plot and self.type == slicer_type:
            return
        # Do not draw a slicer on a 1D plot
        if not isinstance(plot, ModelPanel2D):
            return
        if slicer_type is None:
            slicer_type = self.type_select.GetStringSelection()
        if slicer_type == self.type_list[0]:
            plot.onSectorQ(None)
        elif slicer_type == self.type_list[1]:
            plot.onSectorPhi(None)
        elif slicer_type == self.type_list[2]:
            plot.onBoxavgX(None)
        elif slicer_type == self.type_list[3]:
            plot.onBoxavgY(None)

    def process_list(self):
        """
        Populate the check list from the currently plotted 2D data
        """
        # Reinitialize loaded data list on redraw
        self.loaded_data = []
        # Iterate over the loaded plots and find all 2D panels
        for key, value in self.main_window.plot_panels.iteritems():
            if isinstance(value, ModelPanel2D):
                self.loaded_data.append(value.data2D.name)
                if value.data2D.id == self.parent.data2D.id:
                    # Set current plot panel as uncheckable
                    self.always_on = self.loaded_data.index(value.data2D.name)
        self.data_list = wx.CheckListBox(parent=self, id=wx.NewId(),
                                         choices=self.loaded_data,
                                         name="Apply Slicer to 2D Plots:")
        # Check all items by default
        for item in range(len(self.data_list.Items)):
            self.data_list.Check(item)
        self.data_list.Bind(wx.EVT_CHECKLISTBOX, self.on_check_box_list)

    def on_check_box_list(self, evt=None):
        """
        Prevent a checkbox item from being unchecked
        :param evt: Event triggered when a checkbox list item is checked
        """
        if evt is None:
            return
        index = evt.GetSelection()
        if index == self.always_on:
            self.data_list.Check(index)

    def apply_params_list_and_process(self, evt=None):
        """
        Event based parameter setting.

        :param evt: Event triggered to apply parameters to a list of plots
           evt should have attrs plot_list and params

        """
        if evt is None:
            return
        # Apply parameter list to each plot as desired
        for item in evt.apply_to_list:
            event = SlicerParameterEvent(type=evt.type, params=evt.params)
            wx.PostEvent(item, event)
        # Post an event to save each data set to file
        if evt.auto_save:
            event = save_files(append_to_name=evt.append, path=evt.path,
                               type=evt.type, file_list=evt.apply_to_list,
                               fit=evt.fit)
            wx.PostEvent(self, event)

    def save_files(self, evt=None):
        """
        Automatically save the sliced data to file.
        :param evt: Event that triggered the call to the method
        """

        # Events triggered after this event pass other events to wx that are
        # necessary before this event is called. If this is the first time
        # reaching this event, send it to the end of the wx event queue
        if self.iter < 2:
            clone = evt.Clone()
            wx.PostEvent(self, clone)
            self.iter += 1
            return
        if evt is None:
            return

        # Start definitions
        writer = Reader()
        data_dic = {}
        append = evt.append_to_name
        names = []
        f_name_list = []
        f_path_list = []

        # Get list of 2D data names for saving
        for f_name in evt.file_list:
            names.append(f_name.data2D.label)

        # Find the correct plots to save
        for key, plot in self.main_window.plot_panels.iteritems():
            if not hasattr(plot, "data2D"):
                for item in plot.plots:
                    base = item.replace(CONVERT_DICT[evt.type], "")
                    if base in names:
                        data_dic[item] = plot.plots[item]

        # Save files as Text
        for item, data1d in data_dic.iteritems():
            base = '.'.join(item.split('.')[:-1])
            file_name = base + append + ".txt"
            save_to = evt.path + "\\" + file_name
            writer.write(save_to, data1d)
            f_path_list.append(save_to)
            f_name_list.append(file_name)

        # Load files into GUI
        for item in f_path_list:
            self.main_window.load_data(item)

        # Send to fitting
        self.send_to_fitting(evt.fit, f_name_list)

    def send_to_fitting(self, fit=FIT_OPTIONS[0], file_list=None):
        """
        Send a list of data to the fitting perspective
        :param fit: fit type desired
        :param file_list: list of loaded file names to send to fit
        """
        if fit in FIT_OPTIONS and fit != FIT_OPTIONS[0] and \
                        file_list is not None:
            # Set perspective to fitting
            int = self.data_panel.perspective_cbox.FindString("Fitting")
            self.data_panel.perspective_cbox.SetSelection(int)
            self.data_panel._on_perspective_selection(None)
            # Unselect all loaded data
            self.data_panel.selection_cbox.SetValue('Unselect all Data')
            self.data_panel._on_selection_type(None)
            # Click each sliced data file
            for f_name in file_list:
                num = len(f_name)
                data_list = self.data_panel.list_cb_data
                for key in data_list:
                    loaded_key = (key[:num]) if len(key) > num else key
                    if loaded_key == f_name:
                        selection = key
                        data_ctrl = data_list[selection][0]
                        self.check_item_and_children(data_ctrl=data_ctrl,
                                                     check_value=True)
            # Switch to batch mode if selected
            if fit == FIT_OPTIONS[2]:
                self.data_panel.rb_single_mode.SetValue(False)
                self.data_panel.rb_batch_mode.SetValue(True)
                self.data_panel.on_batch_mode(None)
            else:
                self.data_panel.rb_single_mode.SetValue(True)
                self.data_panel.rb_batch_mode.SetValue(False)
                self.data_panel.on_single_mode(None)

            # Post button click event to send data to fitting
            evt = wx.PyCommandEvent(wx.EVT_BUTTON.typeId,
                                    self.data_panel.bt_import.GetId())
            wx.PostEvent(self.data_panel, evt)

    def on_auto_save_checked(self, evt=None):
        """
        Enable/Disable auto append when checkbox is checked
        :param evt: Event
        """
        self.append_name.Enable(self.auto_save.IsChecked())
        self.path.Enable(self.auto_save.IsChecked())
        self.fitting_options.Enable(self.auto_save.IsChecked())

    def check_item_and_children(self, data_ctrl, check_value=True):
        self.data_panel.tree_ctrl.CheckItem(data_ctrl, check_value)
        if data_ctrl.HasChildren():
            if check_value and not data_ctrl.IsExpanded():
                return
            for child_ctrl in data_ctrl.GetChildren():
                self.data_panel.CheckItem(child_ctrl, check_value)

    def update_file_append(self, params=None):
        """
        Update default_value when any parameters are changed
        :param params: dictionary of parameters
        """
        self.default_value = ""
        if params is None:
            params = self.params
        for key in params:
            self.default_value += "_{0}".format(key).split(" [")[0]
            self.default_value += "-{:.2f}".format(params[key])
