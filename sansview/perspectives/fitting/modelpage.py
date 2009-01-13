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
        self.event_owner=None
        #panel interface
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer3 = wx.GridBagSizer(5,5)
        self.sizer1 = wx.GridBagSizer(5,5)
        self.sizer2 = wx.GridBagSizer(5,5)
        self.sizer4 = wx.GridBagSizer(5,5)
        self.sizer5 = wx.GridBagSizer(5,5)
        self.static_line_1 = wx.StaticLine(self, -1)
        self.modelbox = wx.ComboBox(self, -1)
        id = wx.NewId()
        self.vbox.Add(self.sizer3)
        self.vbox.Add(self.sizer1)
        self.vbox.Add(self.sizer2)
        self.vbox.Add(self.static_line_1, 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer5)
        self.vbox.Add(self.sizer4)
        
        id = wx.NewId()
        self.btClose =wx.Button(self,id,'Close')
        self.btClose.Bind(wx.EVT_BUTTON, self.onClose,id=id)
        self.btClose.SetToolTipString("Close page.")
        ix = 1
        iy = 1 
        self.sizer4.Add(wx.StaticText(self, -1, 'Min'),(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 2
        self.sizer4.Add(wx.StaticText(self, -1, 'Max'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix = 0
        iy += 1
        self.sizer4.Add(wx.StaticText(self, -1, 'x range'),(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ## Q range
        self.qmin= 0.001
        self.qmax= 0.1
        
        ix += 1
        self.xmin    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.xmin.SetValue(format_number(self.qmin))
        self.xmin.SetToolTipString("Minimun value of x in linear scale.")
        self.xmin.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
        self.xmin.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
        self.sizer4.Add(self.xmin,(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
       
        ix += 2
        self.xmax    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.xmax.SetValue(format_number(self.qmax))
        self.xmax.SetToolTipString("Maximum value of x in linear scale.")
        self.xmax.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
        self.xmax.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
       
        self.sizer4.Add(self.xmax,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix = 0
        iy += 1
        self.sizer4.Add((20,20),(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=3
        self.sizer4.Add( self.btClose,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix = 0
        iy = 1
        self.sizer3.Add(wx.StaticText(self,-1,'Model'),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer3.Add(self.modelbox,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #ix = 0
        #iy += 1
        ix += 1
        id = wx.NewId()
        self.model_view =wx.Button(self,id,'View 2D')
        self.model_view.Bind(wx.EVT_BUTTON, self.onModel2D,id=id)
        self.model_view.SetToolTipString("View model in 2D")
        self.sizer3.Add(self.model_view,(iy,ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        # contains link between  model ,all its parameters, and panel organization
        self.parameters=[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit=[]
        # model on which the fit would be performed
        self.model=model
        try:
            #print"init modelpage",model.name
            self.set_panel(model)
        except:
            raise
        # preview selected model name
        self.prevmodel_name=name
        print "model view prev_model",name
        self.modelbox.SetValue(self.prevmodel_name)
        # flag to check if the user has selected a new model in the combox box
        self.model_hasChanged=False
        #dictionary of model name and model class
        self.model_list_box={}
       
        #enable model 2D draw
        self.enable2D= False
        # Data1D to make a deep comparison between 2 Data1D for checking data
        #change
        self.vbox.Layout()
        self.vbox.Fit(self) 
        
        self.SetSizer(self.vbox)
        self.SetScrollbars(20,20,55,40)
        self.Centre()
       
        
    def onClose(self,event):
        """ close the page associated with this panel"""
        self.GrandParent.onClose()
        
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
        
    def onModel2D(self, event):
        """
         call manager to plot model in 2D
        """
        # If the 2D display is not currently enabled, plot the model in 2D 
        # and set the enable2D flag.
        if self.enable2D==False:
            self.enable2D=True
            self.manager.draw_model(model=self.model,
                                    name=self.model.name,
                                    description=None,
                                     enable2D=self.enable2D,
                                     qmin=float(self.qmin),
                                    qmax=float(self.qmax))
            
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
    
  
   
    def _on_select_model(self,event):
        """
            react when a model is selected from page's combo box
            post an event to its owner to draw an appropriate theory
        """
        #print "modelpage: self.model_list_box ",self.model_list_box
        for item in self.model_list_box.itervalues():
            name = item.__name__
            if hasattr(item, "name"):
                name = item.name
            if name ==event.GetString():
                model=item()
                #print "fitpage: _on_select_model model name",name ,event.GetString()
                self.model= model
                self.set_panel(model)
                print "name in model page", name,event.GetString()
                self.name= name
                self.manager.draw_model(model, name)
                
            self.model_view.SetFocus()
            
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
        
        self.sizer2.Clear(True)
        self.sizer1.Clear(True)
        self.sizer5.Clear(True)
        self.parameters = []
        self.param_toFit=[]
        self.model = model
        keys = self.model.getParamList()
        keys.sort()
        description=None
        if hasattr(self.model,'description'):
            description =model.description
        disp_list=self.model.getDispParamList()
        ip=0
        iq=1
        if len(disp_list)>0:
            disp = wx.StaticText(self, -1, 'Dispersion')
            self.sizer5.Add(disp,( iq, ip),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            ip += 1 
            values = wx.StaticText(self, -1, 'Values')
            self.sizer5.Add(values,( iq, ip),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            
        disp_list.sort()
        #print "went here",self.model.name,model.description
        iy = 1
        ix = 0
        self.cb0 = wx.StaticText(self, -1,'Model Description:')
        self.sizer1.Add(self.cb0,(iy, ix),(1,1),\
                          wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        
        self.cb01 = wx.StaticText(self, -1,str(description),style=wx.ALIGN_LEFT)
        self.cb01.Wrap(400) 
        #self.cb01 = wx.StaticText(self, -1,str(description),(45, 25),style=wx.ALIGN_LEFT)
        
        self.sizer1.Add(self.cb01,(iy, ix),(1,1),\
                          wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix = 0
        iy = 1
        self.cb1 = wx.StaticText(self, -1,'Parameters')
        self.sizer2.Add(self.cb1,(iy, ix),(1,1),\
                          wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        self.text2_2 = wx.StaticText(self, -1, 'Values')
        self.sizer2.Add(self.text2_2,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        self.text2_4 = wx.StaticText(self, -1, 'Units')
        self.sizer2.Add(self.text2_4,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_4.Hide()
        for item in keys:
            if not item in disp_list:
                iy += 1
                ix = 0
                cb=wx.StaticText(self, -1, item)
                self.sizer2.Add( cb,( iy, ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                ix += 1
                value= self.model.getParam(item)
                ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                ctl1.SetValue(str (format_number(value)))
                ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                ctl1.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
                self.sizer2.Add(ctl1, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ix +=1
                
                # Units
                try:
                    units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                except:
                    units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
                self.sizer2.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            else:
                ip = 0
                iq += 1
                cb = wx.CheckBox(self, -1, item, (10, 10))
                cb.SetValue(False)
                self.sizer5.Add( cb,( iq, ip),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                wx.EVT_CHECKBOX(self, cb.GetId(), self._on_select_model)
                
                ip += 1
                value= self.model.getParam(item)
                ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                ctl1.SetValue(str (format_number(value)))
                ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                ctl1.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                self.sizer5.Add(ctl1, (iq,ip),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            #save data
            self.parameters.append([cb,ctl1])
        iy+=1
        self.sizer2.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
        #Display units text on panel
        for item in keys:   
            if self.model.details[item][0]!='':
                self.text2_4.Show()
                break
            else:
                self.text2_4.Hide()
        self.vbox.Layout()
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
            
            if is_modified:
                self.manager.draw_model(self.model, self.model.name, 
                                        qmin=self.qmin, qmax=self.qmax,
                                        enable2D=self.enable2D)
            #self.manager.draw_model(self,model,description=None,
            # enable1D=True,qmin=None,qmax=None, qstep=None)
            
            
            
            
              