import sys
import wx
import wx.lib
import numpy
import copy


from sans.guicomm.events import StatusEvent   
(ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 80

def format_number(value, high=False):
    """
        Return a float in a standardized, human-readable formatted string 
    """
    try: 
        value = float(value)
    except:
        print "returning 0"
        return "0"
    
    if high:
        return "%-6.4g" % value
    else:
        return "%-5.3g" % value


class ModelPage(wx.ScrolledWindow):
    """
        FitPanel class contains fields allowing to display results when
        fitting  a model and one data
        @note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.
  
    """
    ## Internal name for the AUI manager
    window_name = "Fit page"
    ## Title to appear on top of the window
    window_caption = "Fit Page"
    
    
    def __init__(self, parent,model,name, *args, **kwargs):
        wx.ScrolledWindow.__init__(self, parent, *args, **kwargs)
        """ 
            Initialization of the Panel
        """
        #self.scroll = wx.ScrolledWindow(self)
        
        self.manager = None
        self.parent  = parent
        self.event_owner = None
        # this panel does contain data .existing data allow a different drawing
        #on set_model parameters
        self.data=None
        #panel interface
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer10 = wx.GridBagSizer(5,5)
        self.sizer9 = wx.GridBagSizer(5,5)
        self.sizer8 = wx.GridBagSizer(5,5)
        self.sizer7 = wx.GridBagSizer(5,5)
        self.sizer6 = wx.GridBagSizer(5,5)
        self.sizer5 = wx.GridBagSizer(5,5)
        self.sizer4 = wx.GridBagSizer(5,5)
       
        #model selection
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer4)
        #model paramaters layer
        self.vbox.Add(self.sizer5)
        #polydispersion selected
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer6)
        #combox box for type of dispersion
        self.vbox.Add(self.sizer7)
        #dispersion parameters layer
        self.vbox.Add(self.sizer8)
        # plotting range
        self.vbox.Add(self.sizer9)
        #close layer
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer10)
        
      
        #------------------ sizer 4  draw------------------------   
        self.modelbox = wx.ComboBox(self, -1)
         # preview selected model name
        self.prevmodel_name=name
        #print "model view prev_model",name
        self.modelbox.SetValue(self.prevmodel_name)
        #filling sizer2
        ix = 0
        iy = 1
        self.sizer4.Add(wx.StaticText(self,-1,'Model'),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer4.Add(self.modelbox,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        id = wx.NewId()
        self.model_view =wx.Button(self,id,'View 2D')
        self.model_view.Bind(wx.EVT_BUTTON, self.onModel2D,id=id)
        self.model_view.SetToolTipString("View model in 2D")
        self.sizer4.Add(self.model_view,(iy,ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        self.model_view.SetFocus()
        #----------sizer6-------------------------------------------------
        self.disable_disp = wx.RadioButton(self, -1, 'No', (10, 10), style=wx.RB_GROUP)
        self.enable_disp = wx.RadioButton(self, -1, 'Yes', (10, 30))
        self.Bind(wx.EVT_RADIOBUTTON, self.Set_DipersParam, id=self.disable_disp.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.Set_DipersParam, id=self.enable_disp.GetId())
        ix= 0
        iy=1
        self.sizer6.Add(wx.StaticText(self,-1,'Polydispersity: '),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer6.Add(self.enable_disp ,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer6.Add(self.disable_disp ,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix =0
        iy+=1
        self.sizer6.Add((20,20),(iy,ix),(1,1),wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)  

        
        #---------sizer 9 draw----------------------------------------
       
         ## Q range
        self.qmin= 0.001
        self.qmax= 0.1
        self.num_points= 100
        
        
        self.xmin    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.xmin.SetValue(format_number(self.qmin))
        self.xmin.SetToolTipString("Minimun value of x in linear scale.")
        self.xmin.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
        self.xmin.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
        self.xmin.Disable()
        
        self.xmax    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.xmax.SetValue(format_number(self.qmax))
        self.xmax.SetToolTipString("Maximum value of x in linear scale.")
        self.xmax.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
        self.xmax.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
        self.xmax.Disable()

        self.npts    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.npts.SetValue(format_number(self.num_points))
        self.npts.SetToolTipString("Number of point to plot.")
        self.npts.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
        self.npts.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
        self.npts.Disable()
        ix = 0
        iy = 1 
        self.sizer9.Add(wx.StaticText(self, -1, 'Plotting Range'),(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1 
        self.sizer9.Add(wx.StaticText(self, -1, 'Min'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer9.Add(wx.StaticText(self, -1, 'Max'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer9.Add(wx.StaticText(self, -1, 'Npts'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix = 0
        iy += 1
        self.sizer9.Add(wx.StaticText(self, -1, 'x range'),(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer9.Add(self.xmin,(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer9.Add(self.xmax,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer9.Add(self.npts,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        ix =0
        iy+=1 
        self.sizer9.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #----------sizer 10 draw------------------------------------------------------
        id = wx.NewId()
        self.btClose =wx.Button(self,id,'Close')
        self.btClose.Bind(wx.EVT_BUTTON, self.onClose,id=id)
        self.btClose.SetToolTipString("Close page.")
        
        ix= 3
        iy= 1
        self.sizer10.Add((20,20),(iy,ix),(1,1),wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        self.sizer10.Add( self.btClose,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix =0
        iy+=1
        self.sizer10.Add((20,20),(iy,ix),(1,1),wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
       
        # contains link between  model ,all its parameters, and panel organization
        self.parameters=[]
        self.fixed_param=[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit=[]
        # model on which the fit would be performed
        self.model=None
        #dictionary of model name and model class
        self.model_list_box={}
       
        ## Q range
        self.qmin= 0.001
        self.qmax= 0.1
       
        self.vbox.Layout()
        self.vbox.Fit(self) 
        self.SetSizer(self.vbox)
        self.SetScrollbars(20,20,55,40)
        
        self.Centre()
        self.Layout()
        self.GrandParent.GetSizer().Layout()
        
    def set_owner(self,owner):
        """ 
            set owner of fitpage
            @param owner: the class responsible of plotting
        """
        self.event_owner=owner    
   
  
    def set_manager(self, manager):
        """
             set panel manager
             @param manager: instance of plugin fitting
        """
        self.manager = manager  
        
    def populate_box(self, dict):
        """
            Populate each combox box of each page
            @param page: the page to populate
        """
        id=0
        self.model_list_box=dict
        list_name=[]
        for item in  self.model_list_box.itervalues():
            name = item.__name__
            if hasattr(item, "name"):
                name = item.name
            list_name.append(name)
        list_name.sort() 
         
        for name in list_name:
            self.modelbox.Insert(name,int(id))
            id+=1
        wx.EVT_COMBOBOX(self.modelbox,-1, self._on_select_model) 
        return 0
    

    def Set_DipersParam(self, event):
        if self.enable_disp.GetValue():
            self.set_panel_dispers()
        else:
            self.sizer7.Clear(True)
            self.sizer8.Clear(True)
   
    def set_range(self, qmin, qmax, npts):
        """
            Set the range for the plotted models
            @param qmin: minimum Q
            @param qmax: maximum Q
            @param npts: number of Q bins
        """
        # Set the data members
        self.qmin = qmin
        self.qmax = qmax
        self.num_points = npts
        
        # Set the controls
        self.xmin.SetValue(format_number(self.qmin))
        self.xmax.SetValue(format_number(self.qmax))
        self.npts.SetValue(format_number(self.num_points))
    def checkFitRange(self):
        """
            Check the validity of fitting range
            @note: xmin should always be less than xmax or else each control box
            background is colored in pink.
        """
       
        flag = True
        valueMin = self.xmin.GetValue()
        valueMax = self.xmax.GetValue()
        # Check for possible values entered
        #print "fitpage: checkfitrange:",valueMin,valueMax
        try:
            if (float(valueMax)> float(valueMin)):
                self.xmax.SetBackgroundColour(wx.WHITE)
                self.xmin.SetBackgroundColour(wx.WHITE)
            else:
                flag = False
                self.xmin.SetBackgroundColour("pink")
                self.xmax.SetBackgroundColour("pink")      
        except:
            flag = False
            self.xmin.SetBackgroundColour("pink")
            self.xmax.SetBackgroundColour("pink")
            
        self.xmin.Refresh()
        self.xmax.Refresh()
        return flag
    

        
    def onClose(self,event):
        """ close the page associated with this panel"""
        self.GrandParent.onClose()
        
  
        
    def onModel2D(self, event):
        """
         call manager to plot model in 2D
        """
        # If the 2D display is not currently enabled, plot the model in 2D 
        # and set the enable2D flag.
        if self.enable2D==False:
            self.enable2D=True
            self._draw_model()
            
        else:
            print "enable is true:",self.enable2D
            #self.manager.parent. show_panel(147)
            self.manager.show_panel2D( id=None )
            #self.manager.menu1.Append(event_id, new_panel.window_caption, 
            #             "Show %s plot panel" % new_panel.window_caption)
            
    
    def select_model(self, model, name):
        """
            Select a new model
            @param model: model object 
        """
        self.model= model
        print "select_model", model.__class__
        self.set_panel(model)
        self._draw_model(name)
        
        # Select the model from the combo box
        items = self.modelbox.GetItems()
        for i in range(len(items)):
            print "model name",items[i],model.name, model.__class__.__name__
            #if items[i]==model.__class__.__name__:
            if items[i]==name:
                self.modelbox.SetSelection(i)
        
    def _on_select_model(self,event):
        """
            react when a model is selected from page's combo box
            post an event to its owner to draw an appropriate theory
        """
       
        for item in self.model_list_box.itervalues():
            name = item.__name__
            if hasattr(item, "name"):
                name = item.name
            if name ==event.GetString():
                model=item()
                self.model= model
                self.set_panel(model)
                self.name= name
                #self.manager.draw_model(model, name)
                self.enable2D=False
                self._draw_model(name)
            
            
    def get_model_box(self): 
        """ return reference to combox box self.model"""
        return self.modelbox

    
    def get_param_list(self):
        """
            @return self.param_toFit: list containing  references to TextCtrl
            checked.Theses TextCtrl will allow reference to parameters to fit.
            @raise: if return an empty list of parameter fit will nnote work 
            properly so raise ValueError,"missing parameter to fit"
        """
        if self.param_toFit !=[]:
            return self.param_toFit
        else:
            raise ValueError,"missing parameter to fit"
        
        
    def set_panel(self,model):
        """
            Build the panel from the model content
            @param model: the model selected in combo box for fitting purpose
        """
        self.sizer5.Clear(True)
        self.parameters = []
        self.param_toFit=[]
        self.model = model
        keys = self.model.getParamList()
        #print "fitpage1D : dispersion list",self.model.getDispParamList()
        keys.sort()
        ik=0
        im=1
        
        iy = 1
        ix = 0
        self.cb1 = wx.CheckBox(self, -1,"Select all", (10, 10))
        if self.data!=None:
            wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.select_all_param)
            self.cb1.SetValue(False)
        else:
            self.cb1.Disable()
            self.cb1.Hide()
       
        self.sizer5.Add(self.cb1,(iy, ix),(1,1),\
                          wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        self.text2_2 = wx.StaticText(self, -1, 'Values')
        self.sizer5.Add(self.text2_2,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=2
        self.text2_3 = wx.StaticText(self, -1, 'Errors')
        self.sizer5.Add(self.text2_3,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.text2_3.Hide() 
        ix +=1
        self.text2_4 = wx.StaticText(self, -1, 'Units')
        self.sizer5.Add(self.text2_4,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_4.Hide()
        disp_list=self.model.getDispParamList()
        for item in keys:
            if not item in disp_list:
                iy += 1
                ix = 0
    
                cb = wx.CheckBox(self, -1, item, (10, 10))
                if self.data!=None:
                    cb.SetValue(False)
                    wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                else:
                    cb.Disable()
                self.sizer5.Add( cb,( iy, ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
               
                ix += 1
                value= self.model.getParam(item)
                ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                ctl1.SetValue(str (format_number(value)))
                ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                ctl1.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                self.sizer5.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                
                ix += 1
                text2=wx.StaticText(self, -1, '+/-')
                self.sizer5.Add(text2,(iy, ix),(1,1),\
                                wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
                text2.Hide()  
                ix += 1
                ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                self.sizer5.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ctl2.Hide()
                ix +=1
                # Units
                try:
                    units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                except:
                    units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
                self.sizer5.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
           
            self.parameters.append([cb,ctl1,text2,ctl2])
                
        iy+=1
        self.sizer5.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
        #Display units text on panel
        for item in keys:   
            if self.model.details[item][0]!='':
                self.text2_4.Show()
                break
            else:
                self.text2_4.Hide()
        #Disable or enable fit button
        
        if not (len(self.param_toFit ) >0):
            self.xmin.Disable()
            self.xmax.Disable()
        else:
            self.xmin.Enable()
            self.xmax.Enable()
            
        self.vbox.Layout()
        self.SetScrollbars(20,20,55,40)
        self.Layout()
        self.GrandParent.GetSizer().Layout()
        
       
    def  set_panel_dispers(self):
        self.sizer7.Clear(True)
        self.sizer8.Clear(True)
        disp_list=self.model.getDispParamList()
        ix=0
        iy=1
        if len(disp_list)>0:
            model_disp = wx.StaticText(self, -1, 'Model Disp')
            self.sizer7.Add(model_disp,( iy, ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            ix += 1 
            self.disp_box = wx.ComboBox(self, -1)
            self.sizer7.Add(self.disp_box,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            ix = 0 
            iy = 1 
            disp = wx.StaticText(self, -1, 'Dispersion')
            self.sizer8.Add(disp,( iy, ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            ix += 1 
            values = wx.StaticText(self, -1, 'Values')
            self.sizer8.Add(values,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            ix += 1 
            npts = wx.StaticText(self, -1, 'Npts')
            self.sizer8.Add(npts,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            ix += 1 
            nsigmas = wx.StaticText(self, -1, 'Nsigmas')
            self.sizer8.Add(nsigmas,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            
            disp_list.sort()
            print disp_list,self.model.fixed
            for item in disp_list:
                if item in self.model.fixed:
                    ix = 0
                    iy += 1
                    cb = wx.CheckBox(self, -1, item, (10, 10))
                    if self.data !=None:
                        cb.SetValue(False)
                        wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                    else:
                        cb.Disable()
                    self.sizer7.Add( cb,( iy, ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                    
                   
                    ix += 1
                    value= self.model.getParam(item)
                    ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                    ctl1.SetValue(str (format_number(value)))
                    ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                    ctl1.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                    self.sizer7.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                    
                    self.parameters.append([cb,ctl1])
                iy+= 1
        self.vbox.Layout()
        self.SetScrollbars(20,20,55,40)
        self.Layout()
        self.GrandParent.GetSizer().Layout()
           
        
    def _onparamEnter(self,event):
        """ 
            when enter value on panel redraw model according to changed
        """
        self.set_model_parameter()
        
    def set_model_parameter(self):
        if len(self.parameters) !=0 and self.model !=None:
            # Flag to register when a parameter has changed.
            is_modified = False
            for item in self.parameters:
                try:
                     name=str(item[0].GetLabelText())
                     value= float(item[1].GetValue())
                     # If the value of the parameter has changed,
                     # update the model and set the is_modified flag
                     if value != self.model.getParam(name):
                         self.model.setParam(name,value)
                         is_modified = True
                except:
                     wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Model Drawing  Error:wrong value entered : %s"% sys.exc_value))
            
            # Here we should check whether the boundaries have been modified.
            # If qmin and qmax have been modified, update qmin and qmax and 
            # set the is_modified flag to True
            if float(self.xmin.GetValue()) != self.qmin:
                self.qmin = float(self.xmin.GetValue())
                is_modified = True
            if float(self.xmax.GetValue()) != self.qmax:
                self.qmax = float(self.xmax.GetValue())
                is_modified = True
            
            if float(self.npts.GetValue()) !=  self.num_points:
                self.num_points = float(self.npts.GetValue())
                is_modified = True
          
            if is_modified:
                self._draw_model()            
            
    def _draw_model(self, name=None):
        """
            Method to draw or refresh a plotted model.
            The method will use the data member from the model page
            to build a call to the fitting perspective manager.
            
            [Note to coder: This way future changes will be done in only one place.] 
        """
        if name==None:
            name= self.model.name
        self.manager.draw_model(self.model, name, data=self.data,
                                qmin=self.qmin, qmax=self.qmax,
                                qstep= self.num_points,
                                enable2D=self.enable2D)
        """
            self.manager.draw_model(self.model, self.model.name, 
                                    qmin=self.qmin, qmax=self.qmax,
                                    qstep= self.num_points,
                                    enable2D=self.enable2D)
        """
    def select_param(self,event):
        pass
    def select_all_param(self,event): 
        pass
        
       