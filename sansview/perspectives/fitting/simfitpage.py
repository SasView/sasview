
import sys,re,string, wx  
import wx.lib.newevent 
from sans.guicomm.events import StatusEvent    

class FitConstraint:
    """
        Contains info on selected model to fit 
        via simultaneous page
    """
    def __init__(self, model, page=None):
        """
            initialization
        """
        self.model= model
        self.page = page
        self.fittable_param =[]
        self.selected_params=[]
        self._set_fittableParam()
        
    def _set_fittableParam(self):
        """
            fill self.fittable_param
        """
        for item in self.model.getParamList():
            if not item  in self.model.getDispParamList():
                self.fittable_param.append(item)
        for item in self.model.fixed:
            self.fittable_param.append(item)
      

class SimultaneousFitPage(wx.ScrolledWindow):
    """
        Simultaneous fitting panel
        All that needs to be defined are the
        two data members window_name and window_caption
    """
    ## Internal name for the AUI manager
    window_name = "simultaneous Fit page"
    ## Title to appear on top of the window
    window_caption = "Simultaneous Fit Page"
    
    
    def __init__(self, parent,page_finder ={}, *args, **kwargs):
        wx.ScrolledWindow.__init__(self, parent, *args, **kwargs)
        """
             Simultaneous page display
        """
        self.parent = parent
        ## store page_finder
        self.page_finder=page_finder
        ## list contaning info to set constraint 
        ## look like self.constraint_dict[page]=[ model_name, parameter_name, constraint(string)]
        self.constraint_dict={}
        ## item list  self.constraints_list=[combobox1, combobox2,=,textcrtl, button ]
        self.constraints_list=[]
        ## list of current model 
        self.model_list=[]
        ## selected mdoel to fit
        self.model_toFit=[]
        
        
        ## draw
        self.define_page_structure()
        self.draw_page(self.page_finder)
        
        self.set_layout()
        
       
        
    def define_page_structure(self):
        """
            Create empty sizer for a panel
        """
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
      
        self.vbox.Add(self.sizer1)
        self.vbox.Add(self.sizer2)
        
    def set_scroll(self):
        self.SetScrollbars(20,20,200,100)
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
        
    def onFit(self,event):
        """ signal for fitting"""
        ## making sure all parameters content a constraint
        ## validity of the constraint expression is own by fit engine
        self._set_constraint()
        ## get the fit range of very fit problem        
        for page, value in self.page_finder.iteritems():
            qmin, qmax= page.get_range()
            value.set_range(qmin, qmax)
        ## model was actually selected from this page to be fit
        if len(self.model_toFit) >= 1 :
            self.manager.on_simul_fit()
        else:
            msg= "Select at least one model to fit "
            wx.PostEvent(self.parent.Parent, StatusEvent(status= msg ))
           
            
            
    def set_manager(self, manager):
        """
            set panel manager
            @param manager: instance of plugin fitting
        """
        self.manager = manager
        self.draw_page( self.manager.page_finder)
        
        
    def check_all_model_name(self,event):
        """
            check all models names
        """
        self.model_toFit=[] 
        if self.cb1.GetValue()==True:
            for item in self.model_list:
                item[0].SetValue(True)
                self.manager.schedule_for_fit( value=1,fitproblem =item[1]) 
                self.model_toFit.append(item)
                
            ## constraint info
            self._store_model()
            ## display constraint fields
            if self.show_constraint.GetValue():
                self.sizer_couples.Clear(True) 
                self._show_constraint()
                return
        else:
            for item in self.model_list:
                item[0].SetValue(False) 
                self.manager.schedule_for_fit( value=0,fitproblem =item[1]) 
                
            self.model_toFit=[]
            ##constraint info
            self._hide_constraint()
        
  
    def check_model_name(self,event):
        """
            Save information related to checkbox and their states
        """
        self.model_toFit=[]
        for item in self.model_list:
            if item[0].GetValue()==True:
                self.model_toFit.append(item)
                self.manager.schedule_for_fit( value=1,fitproblem =item[1]) 
            else:
                self.manager.schedule_for_fit( value=0,fitproblem =item[1]) 
                if item in self.model_toFit:
                    self.model_toFit.remove(item)
                    self.cb1.SetValue(False)
        ## display constraint fields
        if len(self.model_toFit)>=2:
            self._store_model()
            if self.show_constraint.GetValue():
                self._show_constraint()
                          
       
        ## set the value of the main check button          
        if len(self.model_list)==len(self.model_toFit):
            self.cb1.SetValue(True)
            ## constraint info
            self._store_model()
            ## display constraint fields
            if self.show_constraint.GetValue():
                self.sizer_couples.Clear(True) 
                self._show_constraint()
                return
        else:
            self.cb1.SetValue(False)
            ##constraint info
            self._hide_constraint()
        
  
    def draw_page(self, page_finder={}):      
        """
            Draw a sizer containing couples of data and model 
        """   
        ## receive a new page_finder  
        self.page_finder = page_finder  
       
        self.model_list=[]
        self.model_toFit=[]
        if len(self.model_list)>0:
            for item in self.model_list:
                item[0].SetValue(False) 
                self.manager.schedule_for_fit( value=0,fitproblem =item[1])
                
        self.sizer1.Clear(True)
        
                
        box_description= wx.StaticBox(self, -1,"Fit Couples")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        sizer_couples = wx.GridBagSizer(5,5)
        
        #------------------------------------------------------
        if len(self.page_finder)==0:
            sizer_title.Add(wx.StaticText(self,-1," No fit couple available !"))
        else:
            ## store model  
            self._store_model()
        
            self.cb1 = wx.CheckBox(self, -1,'Select all Fit Couples')
            self.cb1.SetValue(False)
            wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.check_all_model_name)
            
            sizer_title.Add((15,15))
            sizer_title.Add(self.cb1)
            ## draw list of model name
            self._fill_sizer_model_list(sizer_couples)
            ## draw the sizer containing constraint info
            self._fill_sizer_constraint()
        #--------------------------------------------------------
        boxsizer1.Add((5, 5))  
        boxsizer1.Add(sizer_title)
        boxsizer1.Add((5, 5))  
        boxsizer1.Add(sizer_couples)
        boxsizer1.Add((5,5))
       
        self.sizer1.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        self.sizer1.Layout()
        self.SetScrollbars(20,20,200,100)
        self.AdjustScrollbars()
        
    def _store_model(self):
        """
            Store selected model
        """
        if len(self.model_toFit) < 2:
            return
        for page, value in self.page_finder.iteritems():
            model = value.get_model()
            for item in self.model_toFit:
                if model in item and not model in self.constraint_dict.keys():
                    self.constraint_dict[model]=FitConstraint(model=model, page=page)
                   
        
    def _display_constraint(self, event):
        """
            Show fields to add constraint
        """
        if len(self.model_toFit)< 2:
            msg= "Select at least 2 models to add constraint "
            wx.PostEvent(self.parent.Parent, StatusEvent(status= msg ))
            ## hide button
            self._hide_constraint()
            return
        if self.show_constraint.GetValue():
            self.sizer_couples.Clear(True) 
            self._show_constraint()
            return
        else:
           self._hide_constraint()
           return 
            
   
    def _show_constraint(self):
        """
            Show constraint fields
        """
        flag = False
        if len(self.constraints_list)!= 0:
            nb_fit_param = 0
            for value in self.constraint_dict.values():
                nb_fit_param += len(value.fittable_param)
            ##Don't add anymore
            if len(self.constraints_list) == nb_fit_param:
                flag = True
        if len(self.model_toFit) < 2 or flag:
            msg= "Select at least 2 model to add constraint "
            wx.PostEvent(self.parent.Parent, StatusEvent(status= msg ))
            self.sizer_couples.Layout()
            self.sizer2.Layout()
            self.SetScrollbars(20,20,200,100)
            return
            
        sizer_constraint =  wx.BoxSizer(wx.HORIZONTAL)
        
        model_cbox = wx.ComboBox(self, -1)
        model_cbox.Clear()

        param_cbox = wx.ComboBox(self, -1)
        wx.EVT_COMBOBOX(param_cbox,-1, self._on_select_param)
        param_cbox.Hide()
        
        ctl2 = wx.TextCtrl(self, -1)
        ctl2.Bind(wx.EVT_TEXT_ENTER,self._onTextEnter)
        ctl2.Hide()
        
        egal_txt= wx.StaticText(self,-1," = ")
        egal_txt.Hide()
       
        
        for model, value in self.constraint_dict.iteritems():
            ## check if all parameters have been selected for constraint
            ## then do not allow add constraint on parameters
            if len(value.fittable_param)!= len(value.selected_params):
                    ## the user can apply constraint only on model select to fit
                    model_cbox.Append( str(model.name), model)
            
           
        wx.EVT_COMBOBOX(model_cbox,-1, self._on_select_model)
        
        ##[combobox1, combobox2,=,textcrtl ]
        self.constraints_list.append([model_cbox, param_cbox, egal_txt, ctl2])
        
        sizer_constraint.Add(model_cbox)
        sizer_constraint.Add((10,10))
        sizer_constraint.Add(param_cbox)
        sizer_constraint.Add(egal_txt)
        sizer_constraint.Add(ctl2)
        sizer_constraint.Add((10,10))
        
        
        self.sizer_couples.Add(sizer_constraint)
        self.sizer_couples.Add((10,10))
        self.sizer_couples.Layout()
        self.sizer2.Layout()
        self.SetScrollbars(20,20,200,100)
        
    def _hide_constraint(self): 
        """
            hide buttons related constraint 
        """
        if len(self.constraint_dict)>0:
            for value in self.constraint_dict.itervalues():
                value.selected_params=[]
                param = value.fittable_param## list of parameter name
                ## reset the constraint to None on fitproblem
                for item in param:
                    self.page_finder[value.page].set_model_param(item,None)
                   
        self.btAdd.Hide()
        self.constraints_list=[]         
        self.sizer_couples.Clear(True) 
        self.sizer_couples.Layout()    
        self.sizer2.Layout()
        self.SetScrollbars(20,20,200,100)
        self.AdjustScrollbars()    
                
        
        
    def _on_select_model(self, event):
        """
         fill combox box with list of parameters
        """
        model = event.GetClientData()
        param_list= self.constraint_dict[model].fittable_param
        length = len(self.constraints_list)
        if length < 1:
            return 
        
        param_cbox = self.constraints_list[length-1][1]
        param_cbox.Clear()
        ## insert only fittable paramaters
        for param in param_list:
            if not param in self.constraint_dict[model].selected_params:
                param_cbox.Append( str(param), model)
        param_cbox.Show(True)
       
       
        self.sizer2.Layout()
        self.SetScrollbars(20,20,200,100)
        
        
    def _on_select_param(self, event):
        """
            Store the appropriate constraint in the page_finder
        """
        model = event.GetClientData()
        param = event.GetString()
        self.constraint_dict[model].selected_params.append(param)
        
        length = len(self.constraints_list)
        if length < 1:
            return 
        egal_txt = self.constraints_list[length-1][2]
        egal_txt.Show(True)       
        
        ctl2 = self.constraints_list[length-1][3]
        ctl2.Show(True)
        
        self.btAdd.Show(True)
        self.sizer2.Layout()
        self.SetScrollbars(20,20,200,100)
        
        
    def _onAdd_constraint(self, event):  
        """
            Add another line for constraint
        """
        msg= " "
        wx.PostEvent(self.parent.Parent, StatusEvent(status= msg ))
        
        ## check that a constraint is added before allow to add another cosntraint
        
        for item in self.constraints_list:
            model_cbox = item[0]
            if model_cbox.GetString(0)=="":
                msg= " Select a model Name! "
                wx.PostEvent(self.parent.Parent, StatusEvent(status= msg ))
                return 
            param_cbox = item[1]
            if param_cbox.GetString(0)=="":
                msg= " Select a parameter Name! "
                wx.PostEvent(self.parent.Parent, StatusEvent(status= msg ))
                return 
            ctl2 = item[3]
            if ctl2.GetValue().lstrip().rstrip()=="":
                 msg= " Enter a constraint for %s.%s! "%(model_cbox.GetString(0),
                                              param_cbox.GetString(0))           
                 wx.PostEvent(self.parent.Parent, StatusEvent(status= msg ))
                 return 
       
        ## some model or parameters can be constrained
        self._show_constraint()
        
        
   
       
        
    def _fill_sizer_constraint(self):
        """
            Fill sizer containing constraint info
        """
        msg= "Select at least 2 model to add constraint "
        wx.PostEvent(self.parent.Parent, StatusEvent(status= msg ))
        
        self.sizer2.Clear(True)
 
        box_description= wx.StaticBox(self, -1,"Fit Constraints")
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer_title = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_couples = wx.BoxSizer(wx.VERTICAL)
        sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        
        self.hide_constraint = wx.RadioButton(self, -1, 'No', (10, 10), style=wx.RB_GROUP)
        self.show_constraint = wx.RadioButton(self, -1, 'Yes', (10, 30))
        
        self.Bind( wx.EVT_RADIOBUTTON, self._display_constraint,
                    id= self.hide_constraint.GetId() )
        
        self.Bind(  wx.EVT_RADIOBUTTON, self._display_constraint,
                         id= self.show_constraint.GetId()    )
        
          
       
        
        sizer_title.Add( wx.StaticText(self,-1," Model") )
        sizer_title.Add(( 10,10) )
        sizer_title.Add( wx.StaticText(self,-1," Parameter") )
        sizer_title.Add(( 10,10) )
        sizer_title.Add( wx.StaticText(self,-1," Add Constraint?") )
        sizer_title.Add(( 10,10) )
        sizer_title.Add( self.show_constraint )
        sizer_title.Add( self.hide_constraint )
        sizer_title.Add(( 10,10) )
       
        
        
        ## Draw combobox box related to model name and model parameters
        if self.show_constraint.GetValue():
            self._fill_sizer_constraint_helper(self.sizer_couples)
       
        self.btAdd =wx.Button(self,wx.NewId(),'Add')
        self.btAdd.Bind(wx.EVT_BUTTON, self._onAdd_constraint,id= self.btAdd.GetId())
        self.btAdd.SetToolTipString("Add another constraint?")
        self.btAdd.Hide()
        
        self.btFit = wx.Button(self,wx.NewId(),'Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self.onFit,id= self.btFit.GetId())
        self.btFit.SetToolTipString("Perform fit.")
        
        text_hint = wx.StaticText(self,-1,"Example: M0.paramter = M1.parameter") 
        sizer_button.Add(text_hint, 0 , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.btAdd, 0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        sizer_button.Add(self.btFit, 0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
       
        boxsizer1.Add(sizer_title)
        boxsizer1.Add((10,10))
        boxsizer1.Add(self.sizer_couples)
        boxsizer1.Add((10,10))
        boxsizer1.Add(sizer_button)
        
        self.sizer2.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        self.sizer2.Layout()
        self.SetScrollbars(20,20,200,100)
        
        
        
    def _onTextEnter(self, event):
        """
            callback function for textcrtl
        """
        self.btAdd.Show(True)
        self.sizer2.Layout()
        self.SetScrollbars(20,20,200,100)
        self._set_constraint()
        
    def _set_constraint(self):
        """
            get values from the constrainst textcrtl ,parses them into model name
            parameter name and parameters values.
            store them in a list self.params .when when params is not empty set_model 
            uses it to reset the appropriate model and its appropriates parameters
        """
        for item in self.constraints_list:
            model = item[0].GetClientData(0)
            param = item[1].GetString(0)
            constraint = item[3].GetValue().lstrip().rstrip()
            if model  in self.constraint_dict.keys():
                page = self.constraint_dict[model].page
                if constraint != "":
                    self.page_finder[page].set_model_param(param,constraint)
        
   
              
    def _fill_sizer_model_list(self,sizer):
        """
            Receive a dictionary containing information to display model name
            @param page_finder: the dictionary containing models information
        """
        ix = 0
        iy = 0
        list=[]
        sizer.Clear(True)
        
        new_name = wx.StaticText(self, -1, 'New Model Name', style=wx.ALIGN_CENTER)
        new_name.SetBackgroundColour('orange')
        sizer.Add(new_name,(iy, ix),(1,1),
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
        ix +=2 
        model_type = wx.StaticText(self, -1, '  Model Type')
        model_type.SetBackgroundColour('grey')
        sizer.Add(model_type,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1 
        data_used = wx.StaticText(self, -1, '  Used Data')
        data_used.SetBackgroundColour('grey')
        sizer.Add(data_used,(iy, ix),(1,1),
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        
        for page, value in self.page_finder.iteritems():
            try:
                ix = 0
                iy += 1 
                model = value.get_model()
                cb = wx.CheckBox(self, -1, str(model.name))
                cb.SetValue(False)
                sizer.Add( cb,( iy,ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                wx.EVT_CHECKBOX(self, cb.GetId(), self.check_model_name)
                
               
                ix +=2 
                type = model.__class__.__name__
                model_type = wx.StaticText(self, -1, str(type))
                sizer.Add(model_type,( iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                
                ix +=1 
                data = value.get_fit_data()
                data_used= wx.StaticText(self, -1, str(data.name))
                sizer.Add(data_used,( iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                
                
                self.model_list.append([cb,value,page,model])
                
            except:
                pass
        iy +=1
        sizer.Add((20,20),( iy,ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        sizer.Layout()    
        
   
  
        
class HelpWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(570, 400))
        
        page_finder ={}
        ## create random data
        from danse.common.plottools.plottables import Data1D
        data= Data1D(x=[1,2], y=[3,4], dy=[0.1, 0,1])
        data.name="mydata.txt"
        ## create model
        from sans.models.CylinderModel import CylinderModel
        model = CylinderModel()
        model.name="M0"
        
        
        from fitproblem import FitProblem
        page_finder["page"]= FitProblem()
        ## fill the page_finder
        page_finder["page"].add_fit_data(data)
        page_finder["page"].set_model(model)
        self.page = SimultaneousFitPage(self, page_finder=page_finder) 
        
        
        
        self.Centre()
        self.Show(True)


   
if __name__=="__main__":
    app = wx.App()
    HelpWindow(None, -1, 'HelpWindow')
    app.MainLoop()
    
