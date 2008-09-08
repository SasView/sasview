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

    
class ModelPage(wx.Panel):
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
    
    
    def __init__(self, parent,model, *args, **kwargs):
        wx.Panel.__init__(self, parent, *args, **kwargs)
        """ 
            Initialization of the Panel
        """
        self.manager = None
        self.parent  = parent
        self.event_owner=None
        #panel interface
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
       
        self.sizer3 = wx.GridBagSizer(5,5)
        self.sizer2 = wx.GridBagSizer(5,5)
       
        self.modelbox = wx.ComboBox(self, -1)
        id = wx.NewId()
       
        self.vbox.Add(self.sizer3)
        self.vbox.Add(self.sizer2)
      
        ix = 0
        iy = 1
        
        self.sizer3.Add(wx.StaticText(self,-1,'Model'),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer3.Add(self.modelbox,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
       
        # contains link between  model ,all its parameters, and panel organization
        self.parameters=[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit=[]
        # model on which the fit would be performed
        self.model=model
        self.set_panel(model)
        # preview selected model name
        self.prevmodel_name=model.__class__.__name__
        self.modelbox.SetValue(self.prevmodel_name)
        # flag to check if the user has selected a new model in the combox box
        self.model_hasChanged=False
       
        #dictionary of model name and model class
        self.model_list_box={}
        # Data1D to make a deep comparison between 2 Data1D for checking data
        #change
       
        self.vbox.Layout()
        self.vbox.Fit(self) 
        self.SetSizer(self.vbox)
        self.Centre()
        
        
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
        for item in self.model_list_box.itervalues():
            if hasattr(item, "name"):
                name = item.name
            else:
                name = item.__name__
            
            self.modelbox.Insert(name,int(id))
            id+=1
            
            wx.EVT_COMBOBOX(self.modelbox,-1, self._on_select_model) 
        return 0
    
    
    def _on_select_model(self,event):
        """
            react when a model is selected from page's combo box
            post an event to its owner to draw an appropriate theory
        """
        print "modelpage: self.model_list_box ",self.model_list_box
        for item in self.model_list_box.itervalues():
            model=item()
            print "modelpage:model",model
            if hasattr(model, "name"):
                name = model.name
            else:
                name = model.__class__.__name__
            try:
                if name ==event.GetString():
                    self.model=model
                    self.set_panel(self.model)
                    self.manager.draw_model(self.model)
            except:
                raise #ValueError,"model.name is not equal to model class name"
    def set_model_name(self,name):
        """ 
            set model name. set also self.model_hasChanged to true is the model 
            type has changed or false if it didn't
            @param name: model 's name
        """
        self.model_hasChanged=False
        if (name != self.prevmodel_name):
            self.model_hasChanged=True
       
        self.prevmodel_name=self.modelbox.GetValue()
       
            
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
        self.parameters = []
        self.param_toFit=[]
        self.model = model
        keys = self.model.getParamList()
        keys.sort()
        iy = 1
        ix = 0
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
            iy += 1
            ix = 0
            cb=wx.StaticText(self, -1, item)
            self.sizer2.Add( cb,( iy, ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            ix += 1
            value= self.model.getParam(item)
            ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
            ctl1.SetValue(str (format_number(value)))
            ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
            self.sizer2.Add(ctl1, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
           
            ix +=1
            # Units
            try:
                units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
            except:
                units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
            self.sizer2.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            #save data
            self.parameters.append([cb,ctl1])
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
            for item in self.parameters:
                try:
                     name=str(item[0])
                     value= float(item[1].GetValue())
                     
                     self.model.setParam(name,value)
                     self.manager.draw_model(self.model)
                except:
                     wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Drawing  Error:wrong value entered : %s"% sys.exc_value))
   
  