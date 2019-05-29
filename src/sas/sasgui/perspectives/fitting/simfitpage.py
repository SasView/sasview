"""
    Simultaneous or Batch fit page
"""
# Note that this is used for both Simultaneous/Constrained fit AND for
# combined batch fit.  This is done through setting of the batch_on parameter.
# There are the a half dozen or so places where an if statement is used as in
# if not batch_on:
#     xxxx
# else:
#     xxxx
# This is just wrong but dont have time to fix this go. Proper approach would be
# to strip all parts of the code that depend on batch_on and create the top
# level class from which a contrained/simultaneous fit page and a combined
# batch page inherit.
#
#            04/09/2017   --PDB

import sys
from collections import namedtuple

import wx
import wx.lib.newevent
from wx.lib.scrolledpanel import ScrolledPanel

from sas.sascalc.fit.pagestate import SimFitPageState
from sas.sasgui.guiframe.events import StatusEvent, PanelOnFocusEvent
from sas.sasgui.guiframe.panel_base import PanelBase
from sas.sasgui.guiframe.utils import IdList
from sas.sasgui.guiframe.documentation_window import DocumentationWindow

# Control panel width
if sys.platform.count("darwin") == 0:
    PANEL_WID = 420
    FONT_VARIANT = 0
else:
    PANEL_WID = 490
    FONT_VARIANT = 1


# Each constraint requires five widgets and sizer.  Package them in
# a named tuple for easy access.
ConstraintLine = namedtuple('ConstraintLine',
        'model_cbox param_cbox egal_txt constraint btRemove sizer')


def get_fittableParam(model):
    """
    return list of fittable parameters from a model

    :param model: the model used

    """
    fittable_param = []
    for item in model.getParamList():
        if not item  in model.getDispParamList():
            if not item in model.non_fittable:
                fittable_param.append(item)

    for item in model.fixed:
        fittable_param.append(item)

    return fittable_param

class SimultaneousFitPage(ScrolledPanel, PanelBase):
    """
    Simultaneous fitting panel
    All that needs to be defined are the
    two data members window_name and window_caption
    """
    # Internal name for the AUI manager
    window_name = "Simultaneous Fit Page"
    # Title to appear on top of the window
    window_caption = "Simultaneous Fit Page"
    ID_DOC = wx.NewId()
    ID_SET_ALL = wx.NewId()
    ID_FIT = wx.NewId()
    ID_ADD = wx.NewId()
    _id_pool = IdList()

    def __init__(self, parent, page_finder={}, id=wx.ID_ANY, batch_on=False,
                 *args, **kwargs):
        ScrolledPanel.__init__(self, parent, id=id,
                               style=wx.FULL_REPAINT_ON_RESIZE,
                               *args, **kwargs)
        PanelBase.__init__(self, parent)
        """
        Simultaneous page display
        """
        self._ids = iter(self._id_pool)
        self.SetupScrolling()
        # Font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.uid = wx.NewId()
        self.parent = parent
        self.batch_on = batch_on
        # store page_finder
        self.page_finder = page_finder
        # list containing info to set constraint
        # look like self.constraint_dict[page_id]= page
        self.constraint_dict = {}
        # item list
        # self.constraints_list=[combobox1, combobox2,=,textcrtl, button ]
        self.constraints_list = []
        # list of current model
        self.model_list = []
        # selected model to fit
        self.model_to_fit = []
        # Control the fit state
        self.fit_started = False
        # number of constraint
        self.nb_constraint = 0
        self.state = SimFitPageState()
        self.model_cbox_left = None
        self.model_cbox_right = None
        # draw page
        self.define_page_structure()
        self.draw_page()
        self._set_save_flag(False)

    def define_page_structure(self):
        """
        Create empty sizers, their hierarchy and set the sizer for the panel
        """
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.data_selection_sizer = wx.BoxSizer(wx.VERTICAL)
        self.constraints_sizer = wx.BoxSizer(wx.VERTICAL)
        self.run_fit_sizer = wx.BoxSizer(wx.VERTICAL)

        self.data_selection_sizer.SetMinSize((PANEL_WID, -1))
        self.constraints_sizer.SetMinSize((PANEL_WID, -1))
        self.run_fit_sizer.SetMinSize((PANEL_WID, -1))
        self.vbox.Add(self.data_selection_sizer)
        self.vbox.Add(self.constraints_sizer)
        self.vbox.Add(self.run_fit_sizer)
        self.SetSizer(self.vbox)
        self.Centre()

    def set_state(self):
        """
        Define a set of state parameters for saving simultaneous fits.
        """
        self._set_constraint()
        self.state.fit_page_no = self.uid
        self.state.select_all = self.cb1.GetValue()
        self.state.model_list = self.model_list
        self.state.model_to_fit = self.model_to_fit
        self.state.no_constraint = self.nb_constraint
        self.state.constraint_dict = self.constraint_dict
        self.state.constraints_list = self.constraints_list
        return self.get_state()

    def get_state(self):
        """
        Return the state of the current page
        :return: self.state
        """
        return self.state

    def load_from_save_state(self, sim_state):
        """
        Load in a simultaneous/constrained fit from a save state
        :param fit: Fitpanel object
        :return: None
        """
        init_map = {}
        final_map = {}
        # Process each model and associate old M# with new M#
        i = 0
        for model in self.model_list:
            model_id = self._format_id(list(model[1].keys())[0])
            for saved_model in sim_state.model_list:
                save_id = saved_model.pop('name')
                saved_model['name'] = save_id
                save_id = self._format_id(save_id)
                if save_id == model_id:
                    inter_id = str(i)*5
                    init_map[saved_model.pop('fit_page_source')] = inter_id
                    final_map[inter_id] = model[3].name
                    check = bool(saved_model.pop('checked'))
                    self.model_list[i][0].SetValue(check)
                    break
            i += 1

        self.check_model_name(None)

        if len(sim_state.constraints_list) > 0:
            self.hide_constraint.SetValue(False)
            self.show_constraint.SetValue(True)
            self._display_constraint(None)

        for index, item in enumerate(sim_state.constraints_list):
            model_cbox = item.pop('model_cbox')
            if model_cbox != "":
                constraint_value = item.pop('constraint')
                param = item.pop('param_cbox')
                equality = item.pop('egal_txt')
                for key, value in list(init_map.items()):
                    model_cbox = model_cbox.replace(key, value)
                    constraint_value = constraint_value.replace(key, value)
                for key, value in list(final_map.items()):
                    model_cbox = model_cbox.replace(key, value)
                    constraint_value = constraint_value.replace(key, value)

                self.constraints_list[index][0].SetValue(model_cbox)
                self._on_select_model(None)
                self.constraints_list[index][1].SetValue(param)
                self.constraints_list[index][2].SetLabel(equality)
                self.constraints_list[index][3].SetValue(constraint_value)
                self._on_add_constraint(None)
                self._manager.sim_page = self

    def _format_id(self, original_id):
        original_id = original_id.rstrip('1234567890.')
        new_id_list = original_id.split()
        new_id = ' '.join(new_id_list)
        return new_id



    def draw_page(self):
        """
        Construct the Simultaneous/Constrained fit page. fills the first
        region (sizer1) with the list of available fit page pairs of data
        and models.  Then fills sizer2 with the checkbox for adding
        constraints, and finally fills sizer3 with the fit button and
        instructions.
        """

        # create blank list of constraints
        self.model_list = []
        self.model_to_fit = []
        self.constraints_list = []
        self.constraint_dict = {}
        self.nb_constraint = 0
        self.model_cbox_left = None
        self.model_cbox_right = None

        if len(self.model_list) > 0:
            for item in self.model_list:
                item[0].SetValue(False)
                self.manager.schedule_for_fit(value=0, uid=item[2])

        #-------------------------------------------------------
        # setup sizer1 (which fitpages to include)
        self.data_selection_sizer.Clear(True)
        box_description = wx.StaticBox(self, wx.ID_ANY, "Fit Combinations")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        sizer_couples = wx.GridBagSizer(5, 5)

        # The wx GUI has a flag to enable a menu item, but can still be
        # reached via scripting. There is no guearantee future GUI
        # implementations force this check, either.
        # IMHO, this if statement should stay -- JRK 2016-OCT-05
        if len(self.page_finder) == 0:
            msg = " No fit combinations are found! \n\n"
            msg += " Please load data and set up "
            msg += "at least one fit panels first..."
            sizer_title.Add(wx.StaticText(self, wx.ID_ANY, msg))
        else:
            # store model
            self._store_model()

            self.cb1 = wx.CheckBox(self, wx.ID_ANY, 'Select all')
            self.cb1.SetValue(False)
            wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.check_all_model_name)

            sizer_title.Add((10, 10), 0,
                wx.TOP | wx.BOTTOM | wx.EXPAND | wx.ADJUST_MINSIZE, border=5)
            sizer_title.Add(self.cb1, 0,
                wx.TOP | wx.BOTTOM | wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE,
                border=5)

            # draw list of model and data names
            self._fill_sizer_model_list(sizer_couples)

        boxsizer1.Add(sizer_title, flag=wx.TOP | wx.BOTTOM, border=5)
        boxsizer1.Add(sizer_couples, 1, flag=wx.TOP | wx.BOTTOM, border=5)
        self.data_selection_sizer.Add(boxsizer1, 1, wx.EXPAND | wx.ALL, 10)
        # self.sizer1.Layout()

        #--------------------------------------------------------
        # set up the other 2 sizers: the constraints list and the
        # buttons (fit, help etc) sizer at the bottom of the page.
        # Note: the if statement should be removed along with the above
        # if statement as soon as it can be properly tested.
        # Nov. 22 2015  --PDB
        # As above, this page can be accessed through other means than the
        # base SasView GUI.
        # Oct. 5, 2016 --JRK
        if len(self.page_finder) > 0:
            # draw the sizer containing constraint info
            if not self.batch_on:
                self._fill_sizer_constraint()
            # draw fit button sizer
            self._fill_sizer_fit()

    def _fill_sizer_model_list(self, sizer):
        """
        Receive a dictionary containing information to display model name
        """
        ix = 0
        iy = 0
        sizer.Clear(True)

        new_name = wx.StaticText(self, wx.ID_ANY, '  Model Title ',
                                 style=wx.ALIGN_CENTER)
        new_name.SetBackgroundColour('orange')
        new_name.SetForegroundColour(wx.WHITE)
        sizer.Add(new_name, (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
        ix += 2
        model_type = wx.StaticText(self, wx.ID_ANY, '  Model ')
        model_type.SetBackgroundColour('grey')
        model_type.SetForegroundColour(wx.WHITE)
        sizer.Add(model_type, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        data_used = wx.StaticText(self, wx.ID_ANY, '  Data ')
        data_used.SetBackgroundColour('grey')
        data_used.SetForegroundColour(wx.WHITE)
        sizer.Add(data_used, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        ix += 1
        tab_used = wx.StaticText(self, wx.ID_ANY, '  FitPage ')
        tab_used.SetBackgroundColour('grey')
        tab_used.SetForegroundColour(wx.WHITE)
        sizer.Add(tab_used, (iy, ix), (1, 1),
                  wx.EXPAND | wx.ADJUST_MINSIZE, 0)
        for id, value in self.page_finder.items():
            if id not in self.parent.opened_pages:
                continue

            if self.batch_on != self.parent.get_page_by_id(id).batch_on:
                continue

            data_list = []
            model_list = []
            # get data name and model objetta
            for fitproblem in value.get_fit_problem():

                data = fitproblem.get_fit_data()
                if not data.is_data:
                    continue
                name = '-'
                if data is not None and data.is_data:
                    name = str(data.name)
                data_list.append(name)

                model = fitproblem.get_model()
                if model is None:
                    continue
                model_list.append(model)

            if len(model_list) == 0:
                continue
            # Draw sizer
            ix = 0
            iy += 1
            model = model_list[0]
            name = '_'
            if model is not None:
                name = str(model.name)
            cb = wx.CheckBox(self, wx.ID_ANY, name)
            cb.SetValue(False)
            cb.Enable(model is not None and data.is_data)
            sizer.Add(cb, (iy, ix), (1, 1),
                      wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)
            wx.EVT_CHECKBOX(self, cb.GetId(), self.check_model_name)
            ix += 2
            model_type = wx.StaticText(self, wx.ID_ANY,
                                       model.__class__.__name__)
            sizer.Add(model_type, (iy, ix), (1, 1),
                      wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            if self.batch_on:
                data_used = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
                data_used.AppendItems(data_list)
                data_used.SetSelection(0)
            else:
                data_used = wx.StaticText(self, wx.ID_ANY, data_list[0])

            ix += 1
            sizer.Add(data_used, (iy, ix), (1, 1),
                      wx.EXPAND | wx.ADJUST_MINSIZE, 0)
            ix += 1
            caption = value.get_fit_tab_caption()
            tab_caption_used = wx.StaticText(self, wx.ID_ANY, str(caption))
            sizer.Add(tab_caption_used, (iy, ix), (1, 1),
                      wx.EXPAND | wx.ADJUST_MINSIZE, 0)

            self.model_list.append([cb, value, id, model])

        iy += 1
        sizer.Add((20, 20), (iy, ix), (1, 1),
                  wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 15)

    def _fill_sizer_constraint(self):
        """
        Fill sizer containing constraint info
        """
        msg = "Select at least 1 model to add constraint "
        wx.PostEvent(self.parent.parent, StatusEvent(status=msg))

        self.constraints_sizer.Clear(True)
        if self.batch_on:
            if self.constraints_sizer.IsShown():
                self.constraints_sizer.Show(False)
            return
        box_description = wx.StaticBox(self, wx.ID_ANY, "Fit Constraints")
        box_sizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_all_constraints = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_constraints = wx.BoxSizer(wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)

        self.hide_constraint = wx.RadioButton(self, wx.ID_ANY, 'No', (10, 10),
                                              style=wx.RB_GROUP)
        self.show_constraint = wx.RadioButton(self, wx.ID_ANY, 'Yes', (10, 30))
        self.Bind(wx.EVT_RADIOBUTTON, self._display_constraint,
                  id=self.hide_constraint.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self._display_constraint,
                  id=self.show_constraint.GetId())
        if self.batch_on:
            self.hide_constraint.Enable(False)
            self.show_constraint.Enable(False)
        self.hide_constraint.SetValue(True)
        self.show_constraint.SetValue(False)

        sizer_title.Add(wx.StaticText(self, wx.ID_ANY, " Model"))
        sizer_title.Add((10, 10))
        sizer_title.Add(wx.StaticText(self, wx.ID_ANY, " Parameter"))
        sizer_title.Add((10, 10))
        sizer_title.Add(wx.StaticText(self, wx.ID_ANY, " Add Constraint?"))
        sizer_title.Add((10, 10))
        sizer_title.Add(self.show_constraint)
        sizer_title.Add(self.hide_constraint)
        sizer_title.Add((10, 10))

        self.btAdd = wx.Button(self, self.ID_ADD, 'Add')
        self.btAdd.Bind(wx.EVT_BUTTON, self._on_add_constraint,
                        id=self.btAdd.GetId())
        self.btAdd.SetToolTipString("Add another constraint?")
        self.btAdd.Hide()

        text_hint = wx.StaticText(self, wx.ID_ANY,
                                  "Example: [M0][parameter] = M1.parameter")
        sizer_button.Add(text_hint, 0,
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.btAdd, 0,
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 10)

        box_sizer1.Add(sizer_title, flag=wx.TOP | wx.BOTTOM, border=10)
        box_sizer1.Add(self.sizer_all_constraints, flag=wx.TOP | wx.BOTTOM,
                       border=10)
        box_sizer1.Add(self.sizer_constraints, flag=wx.TOP | wx.BOTTOM,
                       border=10)
        box_sizer1.Add(sizer_button, flag=wx.TOP | wx.BOTTOM, border=10)

        self.constraints_sizer.Add(box_sizer1, 0, wx.EXPAND | wx.ALL, 10)

    def _fill_sizer_fit(self):
        """
        Draw fit button
        """
        self.run_fit_sizer.Clear(True)
        box_description = wx.StaticBox(self, wx.ID_ANY, "Fit ")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)

        # Fit button
        self.btFit = wx.Button(self, self.ID_FIT, 'Fit', size=wx.DefaultSize)
        self.btFit.Bind(wx.EVT_BUTTON, self.on_fit, id=self.btFit.GetId())
        self.btFit.SetToolTipString("Perform fit.")

        # General Help button
        self.btHelp = wx.Button(self, wx.ID_HELP, 'HELP')
        if self.batch_on:
            self.btHelp.SetToolTipString("Combined Batch Fitting help.")
        else:
            self.btHelp.SetToolTipString("Simultaneous/Constrained Fitting help.")
        self.btHelp.Bind(wx.EVT_BUTTON, self._on_help)

        # hint text on button line
        if self.batch_on:
            text = " Fit in Parallel all Data sets\n"
            text += "and model selected."
        else:
            text = " At least one set of model and data\n"
            text += " must be selected for fitting."
        text_hint = wx.StaticText(self, wx.ID_ANY, text)

        sizer_button.Add(text_hint)
        sizer_button.Add(self.btFit, 0, wx.LEFT | wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.btHelp, 0, wx.LEFT | wx.ADJUST_MINSIZE, 10)

        boxsizer1.Add(sizer_button, flag=wx.TOP | wx.BOTTOM, border=10)
        self.run_fit_sizer.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)

    def on_remove(self, event):
        """
        Remove constraint fields
        """
        if len(self.constraints_list) == 1:
            self.hide_constraint.SetValue(True)
            self._hide_constraint()
            return
        if len(self.constraints_list) == 0:
            return
        wx.CallAfter(self._remove_after, event.GetId())
        # self._onAdd_constraint(None)

    def _remove_after(self, id):
        for item in self.constraints_list:
            if id == item.btRemove.GetId():
                self.sizer_constraints.Hide(item.sizer)
                item.sizer.Clear(True)
                self.sizer_constraints.Remove(item.sizer)
                self.constraints_list.remove(item)
                self.nb_constraint -= 1
                self.constraints_sizer.Layout()
                self.FitInside()
                break

    def on_fit(self, event):
        """
        signal for fitting

        """
        if self.fit_started:
            self._stop_fit()
            self.fit_started = False
            return

        flag = False
        # check if the current page a simultaneous fit page or a batch page
        if self == self._manager.sim_page:
            flag = (self._manager.sim_page.uid == self.uid)

        # making sure all parameters content a constraint
        if not self.batch_on and self.show_constraint.GetValue():
            if not self._set_constraint():
                return
        # model was actually selected from this page to be fit
        if len(self.model_to_fit) >= 1:
            self.manager._reset_schedule_problem(value=0)
            for item in self.model_list:
                if item[0].GetValue():
                    self.manager.schedule_for_fit(value=1, uid=item[2])
            try:
                self.fit_started = True
                wx.CallAfter(self.set_fitbutton)
                if not self.manager.onFit(uid=self.uid):
                    return
            except:
                msg = "Select at least one parameter to fit in the FitPages."
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
        else:
            msg = "Select at least one model check box to fit "
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
        self.set_state()

    def _on_fit_complete(self):
        """
        Set the completion flag and display the updated fit button label.
        """
        self.fit_started = False
        self.set_fitbutton()

    def _stop_fit(self, event=None):
        """
        Attempt to stop the fitting thread

        :param event: Event handler when stop fit is clicked
        """
        if event is not None:
            event.Skip()
        self.manager.stop_fit(self.uid)
        self.manager._reset_schedule_problem(value=0)
        self._on_fit_complete()

    def set_fitbutton(self):
        """
        Set fit button label depending on the fit_started
        """
        label = "Stop" if self.fit_started else "Fit"
        color = "red" if self.fit_started else "black"

        self.btFit.SetLabel(label)
        self.btFit.SetForegroundColour(color)
        self.btFit.Enable(True)

    def _on_help(self, event):
        """
        Bring up the simultaneous Fitting Documentation whenever the HELP
        button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        web browser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param event: Triggers on clicking the help button
    """
        _TreeLocation = "user/sasgui/perspectives/fitting/fitting_help.html"
        if not self.batch_on:
            _PageAnchor = "#simultaneous-fit-mode"
            _doc_viewer = DocumentationWindow(self, self.ID_DOC, _TreeLocation,
                                          _PageAnchor,
                                          "Simultaneous/Constrained Fitting Help")
        else:
            _PageAnchor = "#combined-batch-fit-mode"
            _doc_viewer = DocumentationWindow(self, self.ID_DOC, _TreeLocation,
                                          _PageAnchor,
                                          "Combined Batch Fit Help")

    def set_manager(self, manager):
        """
        set panel manager

        :param manager: instance of plugin fitting
        """
        self.manager = manager

    def check_all_model_name(self, event=None):
        """
        check all models names
        """
        self.model_to_fit = []
        if self.cb1.GetValue():
            for item in self.model_list:
                if item[0].IsEnabled():
                    item[0].SetValue(True)
                    self.model_to_fit.append(item)

            # constraint info
            self._store_model()
            if not self.batch_on:
                # display constraint fields
                if (self.show_constraint.GetValue() and
                                 len(self.constraints_list) == 0):
                    self._show_all_constraint()
                    self._show_constraint()
        else:
            for item in self.model_list:
                item[0].SetValue(False)

            if not self.batch_on:
                # constraint info
                self._hide_constraint()

        self._update_easy_setup_cb()
        self.FitInside()

    def check_model_name(self, event):
        """
        Save information related to checkbox and their states
        """
        self.model_to_fit = []
        for item in self.model_list:
            if item[0].GetValue():
                self.model_to_fit.append(item)
            else:
                if item in self.model_to_fit:
                    self.model_to_fit.remove(item)
                    self.cb1.SetValue(False)

        # display constraint fields
        if len(self.model_to_fit) >= 1:
            self._store_model()
            if not self.batch_on and self.show_constraint.GetValue() and\
                             len(self.constraints_list) == 0:
                self._show_all_constraint()
                self._show_constraint()

        elif len(self.model_to_fit) < 1:
            # constraint info
            self._hide_constraint()

        self._update_easy_setup_cb()
        # set the value of the main check button
        if len(self.model_list) == len(self.model_to_fit):
            self.cb1.SetValue(True)
            self.FitInside()
            return
        else:
            self.cb1.SetValue(False)
            self.FitInside()

    def _update_easy_setup_cb(self):
        """
        Update easy setup combobox on selecting a model
        """
        if self.model_cbox_left is None or self.model_cbox_right is None:
            return

        models = [(item[3].name, item[3]) for item in self.model_to_fit]
        setComboBoxItems(self.model_cbox_left, models)
        setComboBoxItems(self.model_cbox_right, models)
        for item in self.constraints_list:
            setComboBoxItems(item[0], models)
        if self.model_cbox_left.GetSelection() == wx.NOT_FOUND:
            self.model_cbox_left.SetSelection(0)
        self.constraints_sizer.Layout()

    def _store_model(self):
        """
         Store selected model
        """
        if len(self.model_to_fit) < 1:
            return
        for item in self.model_to_fit:
            model = item[3]
            page_id = item[2]
            self.constraint_dict[page_id] = model

    def _display_constraint(self, event):
        """
        Show fields to add constraint
        """
        if len(self.model_to_fit) < 1:
            msg = "Select at least 1 model to add constraint "
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
            # hide button
            self._hide_constraint()
            return
        if self.show_constraint.GetValue():
            self._show_all_constraint()
            self._show_constraint()
            self.FitInside()
            return
        else:
            self._hide_constraint()
            return

    def _show_all_constraint(self):
        """
        Show constraint fields
        """
        box_description = wx.StaticBox(self, wx.ID_ANY, "Easy Setup ")
        box_sizer = wx.StaticBoxSizer(box_description, wx.HORIZONTAL)
        sizer_constraint = wx.BoxSizer(wx.HORIZONTAL)
        self.model_cbox_left = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        self.model_cbox_left.Clear()
        self.model_cbox_right = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        self.model_cbox_right.Clear()
        wx.EVT_COMBOBOX(self.model_cbox_left, wx.ID_ANY, self._on_select_modelcb)
        wx.EVT_COMBOBOX(self.model_cbox_right, wx.ID_ANY, self._on_select_modelcb)
        egal_txt = wx.StaticText(self, wx.ID_ANY, " = ")
        self.set_button = wx.Button(self, self.ID_SET_ALL, 'Set All')
        self.set_button.Bind(wx.EVT_BUTTON, self._on_set_all_equal,
                             id=self.set_button.GetId())
        set_tip = "Add constraints for all the adjustable parameters "
        set_tip += "(checked in FitPages) if exist."
        self.set_button.SetToolTipString(set_tip)
        self.set_button.Disable()

        for id, model in self.constraint_dict.items():
            # check if all parameters have been selected for constraint
            # then do not allow add constraint on parameters
            self.model_cbox_left.Append(str(model.name), model)
        self.model_cbox_left.Select(0)
        for id, model in self.constraint_dict.items():
            # check if all parameters have been selected for constraint
            # then do not allow add constraint on parameters
            self.model_cbox_right.Append(str(model.name), model)
        box_sizer.Add(self.model_cbox_left,
                             flag=wx.RIGHT | wx.EXPAND, border=10)
        # box_sizer.Add(wx.StaticText(self, wx.ID_ANY, ".parameters"),
        #                     flag=wx.RIGHT | wx.EXPAND, border=5)
        box_sizer.Add(egal_txt, flag=wx.RIGHT | wx.EXPAND, border=5)
        box_sizer.Add(self.model_cbox_right,
                             flag=wx.RIGHT | wx.EXPAND, border=10)
        # box_sizer.Add(wx.StaticText(self, wx.ID_ANY, ".parameters"),
        #                     flag=wx.RIGHT | wx.EXPAND, border=5)
        box_sizer.Add((20, -1))
        box_sizer.Add(self.set_button, flag=wx.RIGHT | wx.EXPAND, border=5)
        sizer_constraint.Add(box_sizer, flag=wx.RIGHT | wx.EXPAND, border=5)
        self.sizer_all_constraints.Insert(before=0,
                             item=sizer_constraint,
                             flag=wx.TOP | wx.BOTTOM | wx.EXPAND, border=5)
        self.FitInside()

    def _on_select_modelcb(self, event):
        """
        On select model left or right combobox
        """
        event.Skip()
        flag = True
        if self.model_cbox_left.GetValue().strip() == '':
            flag = False
        if self.model_cbox_right.GetValue().strip() == '':
            flag = False
        if (self.model_cbox_left.GetValue() ==
                self.model_cbox_right.GetValue()):
            flag = False
        self.set_button.Enable(flag)

    def _on_set_all_equal(self, event):
        """
        On set button
        """
        event.Skip()
        length = len(self.constraints_list)
        if length < 1:
            return
        param_list = []
        param_list_b = []
        selection = self.model_cbox_left.GetCurrentSelection()
        model_left = self.model_cbox_left.GetValue()
        model = self.model_cbox_left.GetClientData(selection)
        selection_b = self.model_cbox_right.GetCurrentSelection()
        model_right = self.model_cbox_right.GetValue()
        model_b = self.model_cbox_right.GetClientData(selection_b)
        for id, dic_model in self.constraint_dict.items():
            if model == dic_model:
                param_list = self.page_finder[id].get_param2fit()
            if model_b == dic_model:
                param_list_b = self.page_finder[id].get_param2fit()
            if len(param_list) > 0 and len(param_list_b) > 0:
                break
        num_cbox = 0
        has_param = False
        for param in param_list:
            num_cbox += 1
            if param in param_list_b:
                item = self.constraints_list[-1]
                item.model_cbox.SetStringSelection(model_left)
                self._on_select_model(None)
                item.param_cbox.Clear()
                item.param_cbox.Append(str(param), model)
                item.param_cbox.SetStringSelection(str(param))
                item.constraint.SetValue(str(model_right + "." + str(param)))
                has_param = True
                if num_cbox == (len(param_list) + 1):
                    break
                self._show_constraint()

        self.FitInside()
        if not has_param:
            msg = " There is no adjustable parameter (checked to fit)"
            msg += " either one of the models."
            wx.PostEvent(self.parent.parent, StatusEvent(info="warning",
                                                         status=msg))
        else:
            msg = " The constraints are added."
            wx.PostEvent(self.parent.parent, StatusEvent(info="info",
                                                         status=msg))

    def _show_constraint(self):
        """
        Show constraint fields
        :param dict: dictionary mapping constraint values
        """
        self.btAdd.Show(True)
        if len(self.constraints_list) != 0:
            nb_fit_param = 0
            for id, model in self.constraint_dict.items():
                nb_fit_param += len(self.page_finder[id].get_param2fit())
            # Don't add anymore
            if len(self.constraints_list) == nb_fit_param:
                msg = "Cannot add another constraint. Maximum of number "
                msg += "Parameters name reached %s" % str(nb_fit_param)
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                self.sizer_constraints.Layout()
                self.constraints_sizer.Layout()
                return
        if len(self.model_to_fit) < 1:
            msg = "Select at least 1 model to add constraint "
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
            self.sizer_constraints.Layout()
            self.constraints_sizer.Layout()
            return

        sizer_constraint = wx.BoxSizer(wx.HORIZONTAL)

        # Model list
        model_cbox = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        model_cbox.Clear()
        for id, model in self.constraint_dict.items():
            # check if all parameters have been selected for constraint
            # then do not allow add constraint on parameters
            model_cbox.Append(str(model.name), model)
        wx.EVT_COMBOBOX(model_cbox, wx.ID_ANY, self._on_select_model)

        # Parameters in model
        param_cbox = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY,
                                 size=(100, -1))
        param_cbox.Hide()
        wx.EVT_COMBOBOX(param_cbox, wx.ID_ANY, self._on_select_param)

        egal_txt = wx.StaticText(self, wx.ID_ANY, " = ")

        # Parameter constraint
        constraint = wx.TextCtrl(self, wx.ID_ANY)

        # Remove button
        #btRemove = wx.Button(self, self.ID_REMOVE, 'Remove')
        bt_remove = wx.Button(self, next(self._ids), 'Remove')
        bt_remove.Bind(wx.EVT_BUTTON, self.on_remove,
                      id=bt_remove.GetId())
        bt_remove.SetToolTipString("Remove constraint.")
        bt_remove.Hide()

        # Hid the add button, if it exists
        if hasattr(self, "btAdd"):
            self.btAdd.Hide()

        sizer_constraint.Add((5, -1))
        sizer_constraint.Add(model_cbox, flag=wx.RIGHT | wx.EXPAND, border=10)
        sizer_constraint.Add(param_cbox, flag=wx.RIGHT | wx.EXPAND, border=5)
        sizer_constraint.Add(egal_txt, flag=wx.RIGHT | wx.EXPAND, border=5)
        sizer_constraint.Add(constraint, flag=wx.RIGHT | wx.EXPAND, border=10)
        sizer_constraint.Add(bt_remove, flag=wx.RIGHT | wx.EXPAND, border=10)

        self.sizer_constraints.Insert(before=self.nb_constraint,
                item=sizer_constraint, flag=wx.TOP | wx.BOTTOM | wx.EXPAND,
                border=5)
        c = ConstraintLine(model_cbox, param_cbox, egal_txt,
                           constraint, bt_remove, sizer_constraint)
        self.constraints_list.append(c)

        self.nb_constraint += 1
        self.sizer_constraints.Layout()
        self.constraints_sizer.Layout()
        self.Layout()

    def _hide_constraint(self):
        """
        hide buttons related constraint
        """
        for id in self.page_finder.keys():
            self.page_finder[id].clear_model_param()

        self.nb_constraint = 0
        self.constraint_dict = {}
        if hasattr(self, "btAdd"):
            self.btAdd.Hide()
        self._store_model()
        if self.model_cbox_left is not None:
            self.model_cbox_left.Clear()
            self.model_cbox_left = None
        if self.model_cbox_right is not None:
            self.model_cbox_right.Clear()
            self.model_cbox_right = None
        self.constraints_list = []
        self.sizer_all_constraints.Clear(True)
        self.sizer_all_constraints.Layout()
        self.sizer_constraints.Clear(True)
        self.sizer_constraints.Layout()
        self.constraints_sizer.Layout()
        self.Layout()
        self.FitInside()

    def _on_select_model(self, event):
        """
        fill combo box with list of parameters
        """
        if not self.constraints_list:
            return

        # This way PC/MAC both work, instead of using event.GetClientData().
        model_cbox = self.constraints_list[-1].model_cbox
        n = model_cbox.GetCurrentSelection()
        if n == wx.NOT_FOUND:
            return

        model = model_cbox.GetClientData(n)
        param_list = []
        for id, dic_model in self.constraint_dict.items():
            if model == dic_model:
                param_list = self.page_finder[id].get_param2fit()
                break

        param_cbox = self.constraints_list[-1].param_cbox
        param_cbox.Clear()
        # insert only fittable paramaters
        for param in param_list:
            param_cbox.Append(str(param), model)
        param_cbox.Show(True)

        bt_remove = self.constraints_list[-1].btRemove
        bt_remove.Show(True)
        self.btAdd.Show(True)
#        self.Layout()
        self.FitInside()

    def _on_select_param(self, event):
        """
        Store the appropriate constraint in the page_finder
        """
        # This way PC/MAC both work, instead of using event.GetClientData().
        # n = self.param_cbox.GetCurrentSelection()
        # model = self.param_cbox.GetClientData(n)
        # param = event.GetString()

        if self.constraints_list:
            self.constraints_list[-1].egal_txt.Show(True)
            self.constraints_list[-1].constraint.Show(True)

    def _on_add_constraint(self, event):
        """
        Add another line for constraint
        """
        if not self.show_constraint.GetValue():
            msg = " Select Yes to add Constraint "
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
            return
        # check that a constraint is added
        # before allow to add another constraint
        for item in self.constraints_list:
            if item.model_cbox.GetString(0) == "":
                msg = " Select a model Name! "
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                return
            if item.param_cbox.GetString(0) == "":
                msg = " Select a parameter Name! "
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                return
            if item.constraint.GetValue().lstrip().rstrip() == "":
                model = item.param_cbox.GetClientData(
                                        item.param_cbox.GetCurrentSelection())
                if model is not None:
                    msg = " Enter a constraint for %s.%s! " % (model.name,
                                        item.param_cbox.GetString(0))
                else:
                    msg = " Enter a constraint"
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                return
        # some model or parameters can be constrained
        self._show_constraint()
        self.FitInside()

    def _set_constraint(self):
        """
        get values from the constraint textcrtl ,parses them into model name
        parameter name and parameters values.
        store them in a list self.params .when when params is not empty
        set_model uses it to reset the appropriate model
        and its appropriates parameters
        """
        for item in self.constraints_list:
            select0 = item.model_cbox.GetSelection()
            if select0 == wx.NOT_FOUND:
                continue
            model = item.model_cbox.GetClientData(select0)
            select1 = item.param_cbox.GetSelection()
            if select1 == wx.NOT_FOUND:
                continue
            param = item.param_cbox.GetString(select1)
            constraint = item.constraint.GetValue().lstrip().rstrip()
            if param.lstrip().rstrip() == "":
                param = None
                msg = " Constraint will be ignored!. missing parameters"
                msg += " in combobox to set constraint! "
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
            for id, value in self.constraint_dict.items():
                if model == value:
                    if constraint == "":
                        msg = " Constraint will be ignored!. missing value"
                        msg += " in textcrtl to set constraint! "
                        wx.PostEvent(self.parent.parent,
                                     StatusEvent(status=msg))
                        constraint = None
                    if str(param) in self.page_finder[id].get_param2fit():
                        msg = " Checking constraint for parameter: %s ", param
                        wx.PostEvent(self.parent.parent,
                                     StatusEvent(info="info", status=msg))
                    else:
                        model_name = item[0].GetLabel()
                        fitpage = self.page_finder[id].get_fit_tab_caption()
                        msg = "All constrainted parameters must be set "
                        msg += " adjustable: '%s.%s' " % (model_name, param)
                        msg += "is NOT checked in '%s'. " % fitpage
                        msg += " Please check it to fit or"
                        msg += " remove the line of the constraint."
                        wx.PostEvent(self.parent.parent,
                                StatusEvent(info="error", status=msg))
                        return False

                    for fid in self.page_finder[id].keys():
                        # wrap in param/constraint in str() to remove unicode
                        self.page_finder[id].set_model_param(str(param),
                                str(constraint), fid=fid)
                    break
        return True

    def on_set_focus(self, event=None):
        """
        The derivative class is on focus if implemented
        """
        if self.parent is not None:
            if self.parent.parent is not None:
                wx.PostEvent(self.parent.parent, PanelOnFocusEvent(panel=self))
            self.page_finder = self.parent._manager.get_page_finder()


def setComboBoxItems(cbox, items):
    assert isinstance(cbox, wx.ComboBox)
    selected = cbox.GetStringSelection()
    cbox.Clear()
    for k, (name, value) in enumerate(items):
        cbox.Append(name, value)
    cbox.SetStringSelection(selected)
