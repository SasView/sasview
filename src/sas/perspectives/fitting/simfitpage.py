"""
    Simultaneous fit page
"""
import sys
from collections import namedtuple

import wx
import wx.lib.newevent
from wx.lib.scrolledpanel import ScrolledPanel

from sas.guiframe.events import StatusEvent
from sas.guiframe.panel_base import PanelBase
from sas.guiframe.events import PanelOnFocusEvent
from sas.guiframe.utils import IdList
from sas.guiframe.documentation_window import DocumentationWindow

#Control panel width 
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
    ## Internal name for the AUI manager
    window_name = "simultaneous Fit page"
    ## Title to appear on top of the window
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
        ##Font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.uid = wx.NewId()
        self.parent = parent
        self.batch_on = batch_on
        ## store page_finder
        self.page_finder = page_finder
        ## list containing info to set constraint
        ## look like self.constraint_dict[page_id]= page
        self.constraint_dict = {}
        ## item list
        ## self.constraints_list=[combobox1, combobox2,=,textcrtl, button ]
        self.constraints_list = []
        ## list of current model
        self.model_list = []
        ## selected mdoel to fit
        self.model_toFit = []
        ## number of constraint
        self.nb_constraint = 0
        self.model_cbox_left = None
        self.model_cbox_right = None
        ## draw page
        self.define_page_structure()
        self.draw_page()
        self._set_save_flag(False)

    def define_page_structure(self):
        """
        Create empty sizers, their hierarchy and set the sizer for the panel
        """
        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer3 = wx.BoxSizer(wx.VERTICAL)

        self.sizer1.SetMinSize((PANEL_WID, -1))
        self.sizer2.SetMinSize((PANEL_WID, -1))
        self.sizer3.SetMinSize((PANEL_WID, -1))
        self.vbox.Add(self.sizer1)
        self.vbox.Add(self.sizer2)
        self.vbox.Add(self.sizer3)
        self.SetSizer(self.vbox)
        self.Centre()

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
        self.model_toFit = []
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
        ## setup sizer1 (which fitpages to include)
        self.sizer1.Clear(True)
        box_description = wx.StaticBox(self, wx.ID_ANY, "Fit Combinations")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        sizer_couples = wx.GridBagSizer(5, 5)

        #This if statement should be obsolete and can be removed in version 4
        #Leave it here for now as no time to thoroughly test.  However if no
        #fit page is found the menu item that calls this page is inactive 
        # Nov. 22 2015  --PDB
        if len(self.page_finder) == 0:
            msg = " No fit combinations are found! \n\n"
            msg += " Please load data and set up "
            msg += "at least one fit panels first..."
            sizer_title.Add(wx.StaticText(self, wx.ID_ANY, msg))
        else:
            ## store model
            self._store_model()

            self.cb1 = wx.CheckBox(self, wx.ID_ANY, 'Select all')
            self.cb1.SetValue(False)
            wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.check_all_model_name)

            sizer_title.Add((10, 10), 0,
                wx.TOP | wx.BOTTOM | wx.EXPAND | wx.ADJUST_MINSIZE, border=5)
            sizer_title.Add(self.cb1, 0,
                wx.TOP | wx.BOTTOM | wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, border=5)

            ## draw list of model and data names
            self._fill_sizer_model_list(sizer_couples)

        boxsizer1.Add(sizer_title, flag=wx.TOP | wx.BOTTOM, border=5)
        boxsizer1.Add(sizer_couples, 1, flag=wx.TOP | wx.BOTTOM, border=5)
        self.sizer1.Add(boxsizer1, 1, wx.EXPAND | wx.ALL, 10)
#        self.sizer1.Layout()

        #--------------------------------------------------------
        ## set up the other 2 sizers: the constraints list and the
        ## buttons (fit, help etc) sizer at the bottom of the page.
        ## Note: the if statement should be removed along with the above
        ## if statement as soon as it can be properly tested.
        ## Nov. 22 2015  --PDB
        if len(self.page_finder) > 0:
            ## draw the sizer containing constraint info
            if not self.batch_on:
                self._fill_sizer_constraint()
            ## draw fit button sizer
            self._fill_sizer_fit()


    def _fill_sizer_model_list(self, sizer):
        """
        Receive a dictionary containing information to display model name
        """
        ix = 0
        iy = 0
        list = []
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
        for id, value in self.page_finder.iteritems():
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

        self.sizer2.Clear(True)
        if self.batch_on:
            if self.sizer2.IsShown():
                self.sizer2.Show(False)
            return
        box_description = wx.StaticBox(self, wx.ID_ANY, "Fit Constraints")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
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
        self.btAdd.Bind(wx.EVT_BUTTON, self._onAdd_constraint,
                        id=self.btAdd.GetId())
        self.btAdd.SetToolTipString("Add another constraint?")
        self.btAdd.Hide()

        text_hint = wx.StaticText(self, wx.ID_ANY,
                                  "Example: [M0][paramter] = M1.parameter")
        sizer_button.Add(text_hint, 0,
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.btAdd, 0,
                         wx.LEFT | wx.EXPAND | wx.ADJUST_MINSIZE, 10)

        boxsizer1.Add(sizer_title, flag=wx.TOP | wx.BOTTOM, border=10)
        boxsizer1.Add(self.sizer_all_constraints, flag=wx.TOP | wx.BOTTOM,
                      border=10)
        boxsizer1.Add(self.sizer_constraints, flag=wx.TOP | wx.BOTTOM,
                      border=10)
        boxsizer1.Add(sizer_button, flag=wx.TOP | wx.BOTTOM, border=10)

        self.sizer2.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)


    def _fill_sizer_fit(self):
        """
        Draw fit button
        """
        self.sizer3.Clear(True)
        box_description = wx.StaticBox(self, wx.ID_ANY, "Fit ")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)

        #Fit button
        self.btFit = wx.Button(self, self.ID_FIT, 'Fit', size=wx.DefaultSize)
        self.btFit.Bind(wx.EVT_BUTTON, self.onFit, id=self.btFit.GetId())
        self.btFit.SetToolTipString("Perform fit.")

        #General Help button
        self.btHelp = wx.Button(self, wx.ID_HELP, 'HELP')
        self.btHelp.SetToolTipString("Simultaneous/Constrained Fitting help.")
        self.btHelp.Bind(wx.EVT_BUTTON, self._onHelp)

        #hint text on button line
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
        self.sizer3.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)

    def onRemove(self, event):
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
        #self._onAdd_constraint(None)

    def _remove_after(self, id):
        for item in self.constraints_list:
            if id == item.btRemove.GetId():
                self.sizer_constraints.Hide(item.sizer)
                item.sizer.Clear(True)
                self.sizer_constraints.Remove(item.sizer)
                self.constraints_list.remove(item)
                self.nb_constraint -= 1
                self.sizer2.Layout()
                self.FitInside()
                break

    def onFit(self, event):
        """
        signal for fitting

        """
        flag = False
        # check if the current page a simultaneous fit page or a batch page
        if self == self._manager.sim_page:
            flag = (self._manager.sim_page.uid == self.uid)

        ## making sure all parameters content a constraint
        if not self.batch_on and self.show_constraint.GetValue():
            if not self._set_constraint():
                return
        ## model was actually selected from this page to be fit
        if len(self.model_toFit) >= 1:
            self.manager._reset_schedule_problem(value=0)
            for item in self.model_list:
                if item[0].GetValue():
                    self.manager.schedule_for_fit(value=1, uid=item[2])
            try:
                if not self.manager.onFit(uid=self.uid):
                    return
            except:
                msg = "Select at least one parameter to fit in the FitPages."
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
        else:
            msg = "Select at least one model check box to fit "
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))

    def _onHelp(self, event):
        """
        Bring up the simultaneous Fitting Documentation whenever the HELP
        button is clicked.

        Calls DocumentationWindow with the path of the location within the
        documentation tree (after /doc/ ....".  Note that when using old
        versions of Wx (before 2.9) and thus not the release version of
        installers, the help comes up at the top level of the file as
        webbrowser does not pass anything past the # to the browser when it is
        running "file:///...."

    :param evt: Triggers on clicking the help button
    """
        _TreeLocation = "user/perspectives/fitting/fitting_help.html"
        _PageAnchor = "#simultaneous-fit-mode"
        _doc_viewer = DocumentationWindow(self, self.ID_DOC, _TreeLocation,
                                          _PageAnchor,
                                          "Simultaneous/Constrained Fitting Help")

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
        self.model_toFit = []
        if self.cb1.GetValue() == True:
            for item in self.model_list:
                if item[0].IsEnabled():
                    item[0].SetValue(True)
                    self.model_toFit.append(item)

            ## constraint info
            self._store_model()
            if not self.batch_on:
                ## display constraint fields
                if (self.show_constraint.GetValue() and
                                 len(self.constraints_list) == 0):
                    self._show_all_constraint()
                    self._show_constraint()
        else:
            for item in self.model_list:
                item[0].SetValue(False)

            if not self.batch_on:
                ##constraint info
                self._hide_constraint()

        self._update_easy_setup_cb()
        self.FitInside()


    def check_model_name(self, event):
        """
        Save information related to checkbox and their states
        """
        self.model_toFit = []
        cbox = event.GetEventObject()
        for item in self.model_list:
            if item[0].GetValue() == True:
                self.model_toFit.append(item)
            else:
                if item in self.model_toFit:
                    self.model_toFit.remove(item)
                    self.cb1.SetValue(False)

        ## display constraint fields
        if len(self.model_toFit) >= 1:
            self._store_model()
            if not self.batch_on and self.show_constraint.GetValue() and\
                             len(self.constraints_list) == 0:
                self._show_all_constraint()
                self._show_constraint()

        elif len(self.model_toFit) < 1:
            ##constraint info
            self._hide_constraint()

        self._update_easy_setup_cb()
        ## set the value of the main check button
        if len(self.model_list) == len(self.model_toFit):
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
        if self.model_cbox_left == None or self.model_cbox_right == None:
            return

        models = [(item[3].name, item[3]) for item in self.model_toFit]
        setComboBoxItems(self.model_cbox_left, models)
        setComboBoxItems(self.model_cbox_right, models)
        for item in self.constraints_list:
            setComboBoxItems(item[0], models)
        if self.model_cbox_left.GetSelection() == wx.NOT_FOUND:
            self.model_cbox_left.SetSelection(0)
        self.sizer2.Layout()

    def _store_model(self):
        """
         Store selected model
        """
        if len(self.model_toFit) < 1:
            return
        for item in self.model_toFit:
            model = item[3]
            page_id = item[2]
            self.constraint_dict[page_id] = model

    def _display_constraint(self, event):
        """
        Show fields to add constraint
        """
        if len(self.model_toFit) < 1:
            msg = "Select at least 1 model to add constraint "
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
            ## hide button
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
        boxsizer = wx.StaticBoxSizer(box_description, wx.HORIZONTAL)
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

        for id, model in self.constraint_dict.iteritems():
            ## check if all parameters have been selected for constraint
            ## then do not allow add constraint on parameters
            self.model_cbox_left.Append(str(model.name), model)
        self.model_cbox_left.Select(0)
        for id, model in self.constraint_dict.iteritems():
            ## check if all parameters have been selected for constraint
            ## then do not allow add constraint on parameters
            self.model_cbox_right.Append(str(model.name), model)
        boxsizer.Add(self.model_cbox_left,
                             flag=wx.RIGHT | wx.EXPAND, border=10)
        #boxsizer.Add(wx.StaticText(self, wx.ID_ANY, ".parameters"),
        #                     flag=wx.RIGHT | wx.EXPAND, border=5)
        boxsizer.Add(egal_txt, flag=wx.RIGHT | wx.EXPAND, border=5)
        boxsizer.Add(self.model_cbox_right,
                             flag=wx.RIGHT | wx.EXPAND, border=10)
        #boxsizer.Add(wx.StaticText(self, wx.ID_ANY, ".parameters"),
        #                     flag=wx.RIGHT | wx.EXPAND, border=5)
        boxsizer.Add((20, -1))
        boxsizer.Add(self.set_button, flag=wx.RIGHT | wx.EXPAND, border=5)
        sizer_constraint.Add(boxsizer, flag=wx.RIGHT | wx.EXPAND, border=5)
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
        param_listB = []
        selection = self.model_cbox_left.GetCurrentSelection()
        model_left = self.model_cbox_left.GetValue()
        model = self.model_cbox_left.GetClientData(selection)
        selectionB = self.model_cbox_right.GetCurrentSelection()
        model_right = self.model_cbox_right.GetValue()
        modelB = self.model_cbox_right.GetClientData(selectionB)
        for id, dic_model in self.constraint_dict.iteritems():
            if model == dic_model:
                param_list = self.page_finder[id].get_param2fit()
            if modelB == dic_model:
                param_listB = self.page_finder[id].get_param2fit()
            if len(param_list) > 0 and len(param_listB) > 0:
                break
        num_cbox = 0
        has_param = False
        for param in param_list:
            num_cbox += 1
            if param in param_listB:
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
        """
        self.btAdd.Show(True)
        if len(self.constraints_list) != 0:
            nb_fit_param = 0
            for id, model in self.constraint_dict.iteritems():
                nb_fit_param += len(self.page_finder[id].get_param2fit())
            ##Don't add anymore
            if len(self.constraints_list) == nb_fit_param:
                msg = "Cannot add another constraint. Maximum of number "
                msg += "Parameters name reached %s" % str(nb_fit_param)
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                self.sizer_constraints.Layout()
                self.sizer2.Layout()
                return
        if len(self.model_toFit) < 1:
            msg = "Select at least 1 model to add constraint "
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
            self.sizer_constraints.Layout()
            self.sizer2.Layout()
            return

        sizer_constraint = wx.BoxSizer(wx.HORIZONTAL)

        # Model list
        model_cbox = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        model_cbox.Clear()
        for id, model in self.constraint_dict.iteritems():
            ## check if all parameters have been selected for constraint
            ## then do not allow add constraint on parameters
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
        btRemove = wx.Button(self, self._ids.next(), 'Remove')
        btRemove.Bind(wx.EVT_BUTTON, self.onRemove,
                      id=btRemove.GetId())
        btRemove.SetToolTipString("Remove constraint.")
        btRemove.Hide()

        # Hid the add button, if it exists
        if hasattr(self, "btAdd"):
            self.btAdd.Hide()

        sizer_constraint.Add((5, -1))
        sizer_constraint.Add(model_cbox, flag=wx.RIGHT | wx.EXPAND, border=10)
        sizer_constraint.Add(param_cbox, flag=wx.RIGHT | wx.EXPAND, border=5)
        sizer_constraint.Add(egal_txt, flag=wx.RIGHT | wx.EXPAND, border=5)
        sizer_constraint.Add(constraint, flag=wx.RIGHT | wx.EXPAND, border=10)
        sizer_constraint.Add(btRemove, flag=wx.RIGHT | wx.EXPAND, border=10)

        self.sizer_constraints.Insert(before=self.nb_constraint,
                item=sizer_constraint, flag=wx.TOP | wx.BOTTOM | wx.EXPAND,
                border=5)
        c = ConstraintLine(model_cbox, param_cbox, egal_txt,
                           constraint, btRemove, sizer_constraint)
        self.constraints_list.append(c)

        self.nb_constraint += 1
        self.sizer_constraints.Layout()
        self.sizer2.Layout()
        self.Layout

    def _hide_constraint(self):
        """
        hide buttons related constraint
        """
        for id in self.page_finder.iterkeys():
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
        self.sizer2.Layout()
        self.Layout
        self.FitInside()

    def _on_select_model(self, event):
        """
        fill combox box with list of parameters
        """
        if not self.constraints_list:
            return

        ##This way PC/MAC both work, instead of using event.GetClientData().
        model_cbox = self.constraints_list[-1].model_cbox
        n = model_cbox.GetCurrentSelection()
        if n == wx.NOT_FOUND:
            return

        model = model_cbox.GetClientData(n)
        param_list = []
        for id, dic_model in self.constraint_dict.iteritems():
            if model == dic_model:
                param_list = self.page_finder[id].get_param2fit()
                break

        param_cbox = self.constraints_list[-1].param_cbox
        param_cbox.Clear()
        ## insert only fittable paramaters
        for param in param_list:
            param_cbox.Append(str(param), model)
        param_cbox.Show(True)

        btRemove = self.constraints_list[-1].btRemove
        btRemove.Show(True)
        self.btAdd.Show(True)
#        self.Layout()
        self.FitInside()

    def _on_select_param(self, event):
        """
        Store the appropriate constraint in the page_finder
        """
        ##This way PC/MAC both work, instead of using event.GetClientData().
        #n = self.param_cbox.GetCurrentSelection()
        #model = self.param_cbox.GetClientData(n)
        #param = event.GetString()

        if self.constraints_list:
            self.constraints_list[-1].egal_txt.Show(True)
            self.constraints_list[-1].constraint.Show(True)

    def _onAdd_constraint(self, event):
        """
        Add another line for constraint
        """
        if not self.show_constraint.GetValue():
            msg = " Select Yes to add Constraint "
            wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
            return
        ## check that a constraint is added
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
                if model != None:
                    msg = " Enter a constraint for %s.%s! " % (model.name,
                                        item.param_cbox.GetString(0))
                else:
                    msg = " Enter a constraint"
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                return
        ## some model or parameters can be constrained
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
            for id, value in self.constraint_dict.iteritems():
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

                    for fid in self.page_finder[id].iterkeys():
                        # wrap in param/constraint in str() to remove unicode
                        self.page_finder[id].set_model_param(str(param),
                                str(constraint), fid=fid)
                    break
        return True

    def on_set_focus(self, event=None):
        """
        The  derivative class is on focus if implemented
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
