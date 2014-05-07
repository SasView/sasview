"""
    Simultaneous fit page
"""
import sys,re,string, wx
import wx.lib.newevent
from sans.guiframe.events import StatusEvent 
from sans.guiframe.panel_base import PanelBase
from wx.lib.scrolledpanel import ScrolledPanel
from sans.guiframe.events import PanelOnFocusEvent
#Control panel width 
if sys.platform.count("darwin") == 0:
    PANEL_WID = 420
    FONT_VARIANT = 0
else:
    PANEL_WID = 490
    FONT_VARIANT = 1
       
            
def get_fittableParam(model):
    """
    return list of fittable parameters name of a model
    
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
    
    def __init__(self, parent, page_finder={}, id=-1, batch_on=False,
                     *args, **kwargs):
        ScrolledPanel.__init__(self, parent, id=id,
                               style=wx.FULL_REPAINT_ON_RESIZE,
                               *args, **kwargs)
        PanelBase.__init__(self, parent)
        """
        Simultaneous page display
        """
        self.SetupScrolling()
        ##Font size
        self.SetWindowVariant(variant=FONT_VARIANT)
        self.uid = wx.NewId()
        self.parent = parent
        self.batch_on = batch_on
        ## store page_finder
        self.page_finder = page_finder
        ## list contaning info to set constraint
        ## look like self.constraint_dict[page_id]= page
        self.constraint_dict = {}
        ## item list
        # self.constraints_list=[combobox1, combobox2,=,textcrtl, button ]
        self.constraints_list = []
        ## list of current model
        self.model_list = []
        ## selected mdoel to fit
        self.model_toFit = []
        ## number of constraint
        self.nb_constraint = 0
        self.model_cbox_left = None
        self.model_cbox_right = None
        self.uid = wx.NewId()
        ## draw page
        self.define_page_structure()
        self.draw_page()
        self.set_layout()
        self._set_save_flag(False)
        
    def define_page_structure(self):
        """
        Create empty sizer for a panel
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
        
    def set_scroll(self):
        """
        """
        self.Layout()
         
    def set_layout(self):
        """
        layout
        """
        self.vbox.Layout()
        self.vbox.Fit(self)
        self.SetSizer(self.vbox)
        self.set_scroll()
        self.Centre()
        
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
        for item in self.constraints_list:
            length = len(item)
            if event.GetId() == item[length - 2].GetId():
                sizer = item[length - 1]
                sizer.Clear(True)
                self.sizer_constraints.Remove(sizer)
                #self.SetScrollbars(20,20,25,65)
                self.constraints_list.remove(item)
                self.nb_constraint -= 1
                self.sizer2.Layout()
                self.Layout()
                break
        self._onAdd_constraint(None)
             
    def onFit(self, event):
        """
        signal for fitting
        
        """
        flag = False
        # check if the current page a simultaneous fit page or a batch page
        if self == self._manager.sim_page:
            flag = (self._manager.sim_page.uid == self.uid)

        ## making sure all parameters content a constraint
        ## validity of the constraint expression is own by fit engine
        if self.parent._manager._fit_engine != "park" and flag:
            msg = "The FitEnging will be set to 'Park' fit engine\n"
            msg += " for the simultaneous fit..."
            #wx.MessageBox(msg, 'Info')
            wx.PostEvent(self._manager.parent, StatusEvent(status=\
                            "Fitting: %s" % msg, info="info"))
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
                if self.show_constraint.GetValue() and\
                                 len(self.constraints_list) == 0:
                    self._show_all_constraint() 
                    self._show_constraint()
        else:
            for item in self.model_list:
                item[0].SetValue(False) 
                
            self.model_toFit = []
            if not self.batch_on:
                ##constraint info
                self._hide_constraint()
            
        self._update_easy_setup_cb()
        self.Layout()
        self.Refresh()
        
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
            self.Layout()
            return
        else:
            self.cb1.SetValue(False)
            self.Layout()
            
    def _update_easy_setup_cb(self):
        """
        Update easy setup combobox on selecting a model
        """
        if self.model_cbox_left != None and self.model_cbox_right != None:
            try:
                # when there is something
                self.model_cbox_left.Clear()
                self.model_cbox_right.Clear()
                self.model_cbox.Clear()
            except:
                # when there is nothing
                pass
            #for id, model in self.constraint_dict.iteritems():
            for item in self.model_toFit:
                model = item[3]
                ## check if all parameters have been selected for constraint
                ## then do not allow add constraint on parameters
                if str(model.name) not in self.model_cbox_left.GetItems():
                    self.model_cbox_left.Append(str(model.name), model)
                if str(model.name) not in self.model_cbox_right.GetItems():
                    self.model_cbox_right.Append(str(model.name), model)
                if str(model.name) not in self.model_cbox.GetItems():
                    self.model_cbox.Append(str(model.name), model)
            self.model_cbox_left.SetSelection(0)
            self.sizer2.Layout()
            self.sizer3.Layout()
        
    def draw_page(self):
        """
        Draw a sizer containing couples of data and model 
        """
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
                
        self.sizer1.Clear(True)
        box_description = wx.StaticBox(self, -1, "Fit Combinations")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        sizer_couples = wx.GridBagSizer(5, 5)
        #------------------------------------------------------
        if len(self.page_finder) == 0:
            msg = " No fit combinations are found! \n\n"
            msg += " Please load data and set up "
            msg += "at least two fit panels first..."
            sizer_title.Add(wx.StaticText(self, -1, msg))
        else:
            ## store model
            self._store_model()
        
            self.cb1 = wx.CheckBox(self, -1, 'Select all')
            self.cb1.SetValue(False)
            
            wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.check_all_model_name)
            
            sizer_title.Add((10, 10), 0,
                wx.TOP|wx.BOTTOM|wx.EXPAND|wx.ADJUST_MINSIZE, border=5)
            sizer_title.Add(self.cb1, 0,
                wx.TOP|wx.BOTTOM|wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, border=5)
            
            ## draw list of model and data name
            self._fill_sizer_model_list(sizer_couples)
            ## draw the sizer containing constraint info
            if not self.batch_on:
                self._fill_sizer_constraint()
            ## draw fit button
            self._fill_sizer_fit()
        #--------------------------------------------------------
        boxsizer1.Add(sizer_title, flag = wx.TOP|wx.BOTTOM, border=5) 
        boxsizer1.Add(sizer_couples, 1, flag = wx.TOP|wx.BOTTOM, border=5)
       
        self.sizer1.Add(boxsizer1, 1, wx.EXPAND | wx.ALL, 10)
        self.sizer1.Layout()
        #self.SetScrollbars(20,20,25,65)
        self.AdjustScrollbars()
        self.Layout()
        
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
            self.Layout()
            return
        else:
            self._hide_constraint()
            self.Layout()
            return
       
    def _show_all_constraint(self):
        """
        Show constraint fields
        """
        box_description = wx.StaticBox(self, -1,"Easy Setup ")
        boxsizer = wx.StaticBoxSizer(box_description, wx.HORIZONTAL)     
        sizer_constraint = wx.BoxSizer(wx.HORIZONTAL)
        self.model_cbox_left = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        self.model_cbox_left.Clear()
        self.model_cbox_right = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        self.model_cbox_right.Clear()
        wx.EVT_COMBOBOX(self.model_cbox_left, -1, self._on_select_modelcb)
        wx.EVT_COMBOBOX(self.model_cbox_right, -1, self._on_select_modelcb)
        egal_txt = wx.StaticText(self, -1, " = ")
        self.set_button = wx.Button(self, wx.NewId(), 'Set All')
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
                             flag=wx.RIGHT|wx.EXPAND, border=10)
        boxsizer.Add(wx.StaticText(self, -1, ".parameters"),
                             flag=wx.RIGHT|wx.EXPAND, border=5)
        boxsizer.Add(egal_txt, flag= wx.RIGHT|wx.EXPAND, border=5)
        boxsizer.Add(self.model_cbox_right,
                             flag=wx.RIGHT|wx.EXPAND, border=10)
        boxsizer.Add(wx.StaticText(self, -1, ".parameters"),
                             flag=wx.RIGHT|wx.EXPAND,border=5)
        boxsizer.Add((20, -1))
        boxsizer.Add(self.set_button, flag=wx.RIGHT|wx.EXPAND, border=5)
        sizer_constraint.Add(boxsizer, flag=wx.RIGHT|wx.EXPAND, border=5)
        self.sizer_all_constraints.Insert(before=0,
                             item=sizer_constraint,
                             flag=wx.TOP|wx.BOTTOM|wx.EXPAND, border=5)

        self.sizer_all_constraints.Layout()
        self.sizer2.Layout()
        #self.SetScrollbars(20,20,25,65)
    
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
        if self.model_cbox_left.GetValue() ==\
                self.model_cbox_right.GetValue():
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
                self.model_cbox.SetStringSelection(model_left)
                self._on_select_model(None)
                self.param_cbox.Clear()
                self.param_cbox.Append(str(param), model)
                self.param_cbox.SetStringSelection(str(param))
                self.ctl2.SetValue(str(model_right + "." + str(param)))
                has_param = True
                if num_cbox == (len(param_list) + 1):
                    break
                self._show_constraint()
        
        self.sizer_constraints.Layout()
        self.sizer2.Layout()
        self.SetScrollbars(20, 20, 25, 65)
        self.Layout()
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
                msg = "Cannot add another constraint .Maximum of number "
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
        model_cbox = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        model_cbox.Clear()
        param_cbox = wx.ComboBox(self, -1,style=wx.CB_READONLY, size=(100, -1), )
        param_cbox.Hide()
        
        #This is for GetCLientData() _on_select_param: Was None return on MAC.
        self.param_cbox = param_cbox
        
        wx.EVT_COMBOBOX(param_cbox,-1, self._on_select_param)
        self.ctl2 = wx.TextCtrl(self, -1)
        egal_txt = wx.StaticText(self, -1, " = ")
        self.btRemove = wx.Button(self,wx.NewId(),'Remove')
        self.btRemove.Bind(wx.EVT_BUTTON, self.onRemove, 
                           id=self.btRemove.GetId())
        self.btRemove.SetToolTipString("Remove constraint.")
        self.btRemove.Hide()
        if hasattr(self, "btAdd"):
            self.btAdd.Hide()
        for id, model in self.constraint_dict.iteritems():
            ## check if all parameters have been selected for constraint
            ## then do not allow add constraint on parameters
            model_cbox.Append(str(model.name), model)
            
        #This is for GetCLientData() passing to self._on_select_param: Was None return on MAC.
        self.model_cbox = model_cbox
           
        wx.EVT_COMBOBOX(model_cbox, -1, self._on_select_model)
        sizer_constraint.Add((5, -1))
        sizer_constraint.Add(model_cbox, flag=wx.RIGHT|wx.EXPAND, border=10)
        sizer_constraint.Add(param_cbox, flag=wx.RIGHT|wx.EXPAND, border=5)
        sizer_constraint.Add(egal_txt, flag=wx.RIGHT|wx.EXPAND, border=5)
        sizer_constraint.Add(self.ctl2, flag=wx.RIGHT|wx.EXPAND, border=10)
        sizer_constraint.Add(self.btRemove, flag=wx.RIGHT|wx.EXPAND, border=10)
      
        self.sizer_constraints.Insert(before=self.nb_constraint,
                        item=sizer_constraint, flag=wx.TOP|wx.BOTTOM|wx.EXPAND,
                        border=5)
        self.constraints_list.append([model_cbox, param_cbox, egal_txt,
                                    self.ctl2, self.btRemove, sizer_constraint])
    
        self.nb_constraint += 1
        self.sizer_constraints.Layout()
        self.sizer2.Layout()
        
    def _hide_constraint(self):
        """
        hide buttons related constraint
        """
        for id in  self.page_finder.iterkeys():
            self.page_finder[id].clear_model_param()
               
        self.nb_constraint = 0
        self.constraint_dict = {}
        if hasattr(self, "btAdd"):
            self.btAdd.Hide()
        self._store_model()
        if self.model_cbox_left != None:
            try:
                self.model_cbox_left.Clear()
            except:
                pass
            self.model_cbox_left = None
        if self.model_cbox_right != None:
            try:
                self.model_cbox_right.Clear()
            except:
                pass
            self.model_cbox_right = None
        self.constraints_list = []
        self.sizer_all_constraints.Clear(True)
        self.sizer_all_constraints.Layout()
        self.sizer_constraints.Clear(True)
        self.sizer_constraints.Layout()
        self.sizer2.Layout()
            
    def _on_select_model(self, event):
        """
        fill combox box with list of parameters
        """
        param_list = []
        ##This way PC/MAC both work, instead of using event.GetClientData().
        n = self.model_cbox.GetCurrentSelection()
        model = self.model_cbox.GetClientData(n)
        for id, dic_model in self.constraint_dict.iteritems():
            if model == dic_model:
                param_list = self.page_finder[id].get_param2fit()
                #break
        length = len(self.constraints_list)
        if length < 1:
            return
        param_cbox = self.constraints_list[length - 1][1]
        param_cbox.Clear()
        ## insert only fittable paramaters
        for param in param_list:
            param_cbox.Append(str(param), model)

        param_cbox.Show(True)
        self.btRemove.Show(True)
        self.btAdd.Show(True)
        self.sizer2.Layout()
        
    def _on_select_param(self, event):
        """
        Store the appropriate constraint in the page_finder
        """
        ##This way PC/MAC both work, instead of using event.GetClientData().
        #n = self.param_cbox.GetCurrentSelection()
        #model = self.param_cbox.GetClientData(n)
        #param = event.GetString()
      
        length = len(self.constraints_list)
        if length < 1:
            return
        egal_txt = self.constraints_list[length - 1][2]
        egal_txt.Show(True)
        
        ctl2 = self.constraints_list[length - 1][3]
        ctl2.Show(True)
        
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
            model_cbox = item[0]
            if model_cbox.GetString(0) == "":
                msg = " Select a model Name! "
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                return 
            param_cbox = item[1]
            if param_cbox.GetString(0) == "":
                msg = " Select a parameter Name! "
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                return 
            ctl2 = item[3]
            if ctl2.GetValue().lstrip().rstrip() == "":
                model = param_cbox.GetClientData(\
                                            param_cbox.GetCurrentSelection())
                if model != None:
                    msg = " Enter a constraint for %s.%s! "%(model.name, 
                                                        param_cbox.GetString(0))
                else:
                     msg = " Enter a constraint"
                wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
                return
        ## some model or parameters can be constrained
        self._show_constraint()
        self.sizer3.Layout()
        self.Layout()
        self.Refresh()
        
    def _fill_sizer_fit(self):
        """
        Draw fit button
        """
        self.sizer3.Clear(True)
        box_description= wx.StaticBox(self, -1, "Fit ")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
          
        self.btFit = wx.Button(self, wx.NewId(), 'Fit', size=wx.DefaultSize)
        self.btFit.Bind(wx.EVT_BUTTON, self.onFit, id=self.btFit.GetId())
        self.btFit.SetToolTipString("Perform fit.")
        if self.batch_on:
            text = " Fit in Parallel all Data set and model selected.\n"
        else:
            text = "     Note: Park fitting engine will be used automatically. \n"
            text += "     This page requires at least one FitPage with a data \n"
            text += "       and a model set for fitting."
            #text+= "automatically for more than 2 combinations checked"
        text_hint = wx.StaticText(self, -1, text)
        
        sizer_button.Add(text_hint, wx.RIGHT|wx.EXPAND, 10)
        sizer_button.Add(self.btFit, 0, wx.LEFT|wx.ADJUST_MINSIZE, 10)
        
        boxsizer1.Add(sizer_button, flag= wx.TOP|wx.BOTTOM,border=10)
        self.sizer3.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)
        self.sizer3.Layout()
        
    def _fill_sizer_constraint(self):
        """
        Fill sizer containing constraint info
        """
        msg = "Select at least 2 model to add constraint "
        wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
        
        self.sizer2.Clear(True)
        if self.batch_on:
            if self.sizer2.IsShown():
                self.sizer2.Show(False)
            return
        box_description= wx.StaticBox(self, -1, "Fit Constraints")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_all_constraints = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_constraints = wx.BoxSizer(wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        
        self.hide_constraint = wx.RadioButton(self, -1, 'No', (10, 10),
                                              style=wx.RB_GROUP)
        self.show_constraint = wx.RadioButton(self, -1, 'Yes', (10, 30))
        self.Bind(wx.EVT_RADIOBUTTON, self._display_constraint,
                  id=self.hide_constraint.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self._display_constraint,
                  id=self.show_constraint.GetId())
        if self.batch_on:
            self.hide_constraint.Enable(False)
            self.show_constraint.Enable(False)
        self.hide_constraint.SetValue(True)
        self.show_constraint.SetValue(False)
        
        sizer_title.Add(wx.StaticText(self, -1, " Model"))
        sizer_title.Add((10, 10))
        sizer_title.Add(wx.StaticText(self, -1, " Parameter"))
        sizer_title.Add((10, 10))
        sizer_title.Add( wx.StaticText(self,-1," Add Constraint?") )
        sizer_title.Add((10, 10))
        sizer_title.Add(self.show_constraint)
        sizer_title.Add(self.hide_constraint)
        sizer_title.Add((10, 10))
        
        self.btAdd = wx.Button(self, wx.NewId(), 'Add')
        self.btAdd.Bind(wx.EVT_BUTTON, self._onAdd_constraint,
                        id=self.btAdd.GetId())
        self.btAdd.SetToolTipString("Add another constraint?")
        self.btAdd.Hide()
     
        text_hint = wx.StaticText(self, -1,
                                  "Example: [M0][paramter] = M1.parameter")
        sizer_button.Add(text_hint, 0 , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.btAdd, 0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
       
        boxsizer1.Add(sizer_title, flag=wx.TOP|wx.BOTTOM,border=10)
        boxsizer1.Add(self.sizer_all_constraints, flag=wx.TOP|wx.BOTTOM,
                      border=10)
        boxsizer1.Add(self.sizer_constraints, flag=wx.TOP|wx.BOTTOM,
                      border=10)
        boxsizer1.Add(sizer_button, flag=wx.TOP|wx.BOTTOM, border=10)
        
        self.sizer2.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)
        self.sizer2.Layout()
       
        #self.SetScrollbars(20,20,25,65)
    
    def _set_constraint(self):
        """
        get values from the constrainst textcrtl ,parses them into model name
        parameter name and parameters values.
        store them in a list self.params .when when params is not empty
        set_model uses it to reset the appropriate model
        and its appropriates parameters
        """
        for item in self.constraints_list:
            select0 = item[0].GetSelection()
            if select0 == wx.NOT_FOUND:
                continue
            model = item[0].GetClientData(select0)
            select1 = item[1].GetSelection()
            if select1 == wx.NOT_FOUND:
                continue
            param = item[1].GetString(select1)
            constraint = item[3].GetValue().lstrip().rstrip()
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
                        self.page_finder[id].set_model_param(param,
                                                        constraint, fid=fid)
                    break
        return True
    
    def _fill_sizer_model_list(self, sizer):
        """
        Receive a dictionary containing information to display model name
        """
        ix = 0
        iy = 0
        list = []
        sizer.Clear(True)
        
        new_name = wx.StaticText(self, -1, '  Model Title ',
                                 style=wx.ALIGN_CENTER)
        new_name.SetBackgroundColour('orange')
        new_name.SetForegroundColour(wx.WHITE)
        sizer.Add(new_name,(iy, ix),(1,1),
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 2
        model_type = wx.StaticText(self, -1, '  Model ')
        model_type.SetBackgroundColour('grey')
        model_type.SetForegroundColour(wx.WHITE)
        sizer.Add(model_type, (iy, ix), (1, 1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        data_used = wx.StaticText(self, -1, '  Data ')
        data_used.SetBackgroundColour('grey')
        data_used.SetForegroundColour(wx.WHITE)
        sizer.Add(data_used, (iy, ix), (1, 1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        tab_used = wx.StaticText(self, -1, '  FitPage ')
        tab_used.SetBackgroundColour('grey')
        tab_used.SetForegroundColour(wx.WHITE)
        sizer.Add(tab_used, (iy, ix), (1, 1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
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
            cb = wx.CheckBox(self, -1, name)
            cb.SetValue(False)
            cb.Enable(model is not None and data.is_data)
            sizer.Add(cb, (iy, ix), (1, 1), 
                       wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            wx.EVT_CHECKBOX(self, cb.GetId(), self.check_model_name)
            ix += 2 
            type = model.__class__.__name__
            model_type = wx.StaticText(self, -1, str(type))
            sizer.Add(model_type, (iy, ix), (1, 1),
                      wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            if self.batch_on:
                data_used = wx.ComboBox(self, -1, style=wx.CB_READONLY)
                data_used.AppendItems(data_list)
                data_used.SetSelection(0)
            else:
                data_used = wx.StaticText(self, -1, data_list[0])
            
            ix += 1
            sizer.Add(data_used, (iy, ix), (1, 1),
                      wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            ix += 1
            caption = value.get_fit_tab_caption()
            tab_caption_used = wx.StaticText(self, -1, str(caption))
            sizer.Add(tab_caption_used, (iy, ix), (1, 1),
                      wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            
            self.model_list.append([cb, value, id, model])
            
        iy += 1
        sizer.Add((20, 20), (iy, ix), (1, 1),
                  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer.Layout()
    
    def on_set_focus(self, event=None):
        """
        The  derivative class is on focus if implemented
        """
        if self.parent is not None:
            if self.parent.parent is not None:
                wx.PostEvent(self.parent.parent, PanelOnFocusEvent(panel=self))
            self.page_finder = self.parent._manager.get_page_finder()
