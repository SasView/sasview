import sys
import wx
import wx.lib
import numpy,math
import copy
import sans.models.dispersion_models 
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

from modelpage import format_number
from modelpage import ModelPage
class FitPage1D(ModelPage):
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
    
    
    def __init__(self, parent,data, *args, **kwargs):
        wx.ScrolledWindow.__init__(self, parent, *args, **kwargs)
        """ 
            Initialization of the Panel
        """
        #self.scroll = wx.ScrolledWindow(self)
        
        self.manager = None
        self.parent  = parent
        self.event_owner = None
        #panel interface
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer9 = wx.GridBagSizer(5,5)
        self.sizer8 = wx.GridBagSizer(5,5)
        self.sizer7 = wx.GridBagSizer(5,5)
        self.sizer6 = wx.GridBagSizer(5,5)
        self.sizer5 = wx.GridBagSizer(5,5)
        self.sizer4 = wx.GridBagSizer(5,5)
        self.sizer3 = wx.GridBagSizer(5,5)
        self.sizer2 = wx.GridBagSizer(5,5)
        self.sizer1 = wx.GridBagSizer(5,5)
        # Add layer
        #data info layer
        self.vbox.Add(self.sizer1)
        #data range 
        self.vbox.Add(self.sizer2)
        #instrument smearing selection layer
        self.vbox.Add(self.sizer3)
        #model selection
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer4)
        #model paramaters layer
        self.vbox.Add(self.sizer5)
        #polydispersion selected
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer6)
        #dispersion parameters layer
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer7)
        #fit info layer
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer8)
        #close layer
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer9)
        
        #---------sizer 1 draw--------------------------------
        self.DataSource  =wx.StaticText(self, -1,str(data.name))
        self.smearer_box = wx.ComboBox(self, -1)
        wx.EVT_COMBOBOX( self.smearer_box,-1, self.onSmear ) 
        self.smeares= sans.models.dispersion_models.models
        i=0
        self.smearer_box.SetValue(str(None))
        self.smearer_box.Insert(str(None),i)
        
        for k,v in self.smeares.iteritems():
            if str(v)=="GaussianModel":
                self.smearer_box.Insert("Gaussian Resolution",i)
            else:
              self.smearer_box.Insert(str(v),i)  
            i+=1
            
        # Minimum value of data   
        self.data_min    = wx.StaticText(self, -1,str(format_number(numpy.min(data.x))))
        # Maximum value of data  
        self.data_max    =  wx.StaticText(self, -1,str(format_number(numpy.max(data.x))))
        #Filing the sizer containing data related fields
        ix = 0
        iy = 1
        self.sizer1.Add(wx.StaticText(self, -1, 'Data Source Name : '),(iy,ix),\
                 (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
       
        ix += 1
        self.sizer1.Add(self.DataSource,(iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        #---------sizer 2 draw--------------------------------
        ix = 0
        iy = 0
        #set maximum range for x in linear scale
        self.text4_3 = wx.StaticText(self, -1, 'Maximum Data Range(Linear)', style=wx.ALIGN_LEFT)
        self.sizer2.Add(self.text4_3,(iy,ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 2
        self.sizer2.Add(wx.StaticText(self, -1, 'Min :'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer2.Add(self.data_min,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer2.Add(wx.StaticText(self, -1, 'Max : '),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer2.Add(self.data_max,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        #----sizer 3 draw--------------------------------
        ix = 0
        iy = 0
        self.sizer3.Add(wx.StaticText(self,-1,'Instrument Smearing'),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer3.Add(self.smearer_box,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix =0
        iy+=1
        self.sizer3.Add((20,20),(iy,ix),(1,1),wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)  
            
        #------------------ sizer 4  draw------------------------   
        self.modelbox = wx.ComboBox(self, -1)
        
        #filling sizer2
        ix = 0
        iy = 1
        self.sizer4.Add(wx.StaticText(self,-1,'Model'),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer4.Add(self.modelbox,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        #----------sizer6-------------------------------------------------
        self.disable_disp = wx.RadioButton(self, -1, 'No', (10, 10), style=wx.RB_GROUP)
        self.enable_disp = wx.RadioButton(self, -1, 'Yes', (10, 30))
        #self.Bind(wx.EVT_RADIOBUTTON, self.Set_DipersParam, id=self.disable_disp.GetId())
        #self.Bind(wx.EVT_RADIOBUTTON, self.Set_DipersParam, id=self.enable_disp.GetId())
        ix= 0
        iy=1
        self.sizer6.Add(wx.StaticText(self,-1,'Polydispersity: '),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer6.Add(self.enable_disp ,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer6.Add(self.disable_disp ,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        
        #---------sizer 8 draw----------------------------------------
        self.tcChi    =  wx.StaticText(self, -1, str(0), style=wx.ALIGN_LEFT)
        self.tcChi.Hide()
        self.text1_1 = wx.StaticText(self, -1, 'Chi2/dof', style=wx.ALIGN_LEFT)
        self.text1_1.Hide()
        
        id = wx.NewId()
        self.btFit =wx.Button(self,id,'Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self.onFit,id=id)
        self.btFit.SetToolTipString("Perform fit.")
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
        self.sizer8.Add(wx.StaticText(self, -1, 'Fitting Range'),(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1 
        self.sizer8.Add(wx.StaticText(self, -1, 'Min'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer8.Add(wx.StaticText(self, -1, 'Max'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer8.Add(wx.StaticText(self, -1, 'Npts'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix = 0
        iy += 1
        self.sizer8.Add(wx.StaticText(self, -1, 'x range'),(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer8.Add(self.xmin,(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer8.Add(self.xmax,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer8.Add(self.npts,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix = 0
        iy += 1
        self.sizer8.Add(self.text1_1,(iy,ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer8.Add(self.tcChi,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix +=2
        self.sizer8.Add(self.btFit,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix =0
        iy+=1 
        self.sizer8.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #----------sizer 9 draw------------------------------------------------------
        id = wx.NewId()
        self.btClose =wx.Button(self,id,'Close')
        self.btClose.Bind(wx.EVT_BUTTON, self.onClose,id=id)
        self.btClose.SetToolTipString("Close page.")
        
        ix= 0
        iy= 1
        self.sizer9.Add((20,20),(iy,ix),(1,1),wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=3
        self.sizer9.Add( self.btClose,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix =0
        iy+=1
        self.sizer9.Add((20,20),(iy,ix),(1,1),wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
       
        # contains link between  model ,all its parameters, and panel organization
        self.parameters=[]
        self.fixed_param=[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit=[]
        # model on which the fit would be performed
        self.model=None
        #dictionary of model name and model class
        self.model_list_box={}
        self.data = data
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
       

  
  
 
        
    def compute_chisqr(self):
        """ @param fn: function that return model value
            @return residuals
        """
        
        flag=self.checkFitRange()
        if flag== True:
            try:
                qmin = float(self.xmin.GetValue())
                qmax = float(self.xmax.GetValue())
                x,y,dy = [numpy.asarray(v) for v in (self.data.x,self.data.y,self.data.dy)]
                if qmin==None and qmax==None: 
                    fx =numpy.asarray([self.model.run(v) for v in x])
                    res=(y - fx)/dy
                else:
                    idx = (x>= qmin) & (x <=qmax)
                    fx = numpy.asarray([self.model.run(item)for item in x[idx ]])
                    res= (y[idx] - fx)/dy[idx]  
                
               
                sum=0
                for item in res:
                    if numpy.isfinite(item):
                        sum +=item
                self.tcChi.SetValue(format_number(math.fabs(sum)))
            except:
                wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Chisqr cannot be compute: %s"% sys.exc_value))
            
            
    def onFit(self,event):
        """ signal for fitting"""
         
        flag=self.checkFitRange()
        self.set_manager(self.manager)
     
        qmin=float(self.xmin.GetValue())
        qmax =float( self.xmax.GetValue())
        if len(self.param_toFit) >0 and flag==True:
            self.manager.schedule_for_fit( value=1,fitproblem =None) 
            self.manager._on_single_fit(qmin=qmin,qmax=qmax)
        else:
              wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Select at least on parameter to fit "))
  
    
    def _on_select_model(self,event):
        """
            react when a model is selected from page's combo box
            post an event to its owner to draw an appropriate theory
        """
        self.btFit.SetFocus()
        for item in self.model_list_box.itervalues():
            name = item.__name__
            if hasattr(item, "name"):
                name = item.name
            #print "fitpage: _on_select_model model name",name ,event.GetString()
            if name ==event.GetString():
                try:
                    self.model=item()
                    evt = ModelEventbox(model=self.model,name=name)
                    wx.PostEvent(self.event_owner, evt)
                    #self.model= item()
                    #self.set_panel(self.model)
                except:
                    raise #ValueError,"model.name is not equal to model class name"
                break
    
    def _onTextEnter(self,event):
        """
            set a flag to determine if the fitting range entered by the user is valid
        """
      
        try:
            flag=self.checkFitRange()
            if flag==True and self.model!=None:
                #print"fit page",self.xmin.GetValue(),self.xmax.GetValue()
                self.manager.redraw_model(float(self.xmin.GetValue())\
                                               ,float(self.xmax.GetValue()))
        except:

            wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Drawing  Error:wrong value entered %s"% sys.exc_value))
        
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
        self.sizer5.Clear(True)
        self.sizer6.Clear(True)
        self.parameters = []
        self.param_toFit=[]
        self.model = model
        keys = self.model.getParamList()
        #print "fitpage1D : dispersion list",self.model.getDispParamList()
        keys.sort()
        disp_list=self.model.getDispParamList()
        fixed=self.model.fixed
        print "fixed",fixed
        #model.setParam("scale", 2)
        #print "model sphere scale fixed?", self.model.is_fittable("scale")
        ip=0
        iq=1
        
        ik=0
        im=1
        if len(disp_list)>0:
            disp = wx.StaticText(self, -1, 'Dispersion')
            self.sizer5.Add(disp,( iq, ip),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            ip += 1 
            values = wx.StaticText(self, -1, 'Values')
            self.sizer5.Add(values,( iq, ip),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            
        disp_list.sort()
        iy = 1
        ix = 0
        self.cb1 = wx.CheckBox(self, -1,"Select all", (10, 10))
        wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.select_all_param)
        self.sizer2.Add(self.cb1,(iy, ix),(1,1),\
                          wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        self.text2_2 = wx.StaticText(self, -1, 'Values')
        self.sizer2.Add(self.text2_2,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=2
        self.text2_3 = wx.StaticText(self, -1, 'Errors')
        self.sizer2.Add(self.text2_3,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.text2_3.Hide() 
        ix +=1
        self.text2_4 = wx.StaticText(self, -1, 'Units')
        self.sizer2.Add(self.text2_4,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_4.Hide()
        #print "keys", keys
        #print "disp_list", disp_list
        #print "fix_list",fixed
        for item in keys:
            if not item in disp_list:
                iy += 1
                ix = 0
    
                cb = wx.CheckBox(self, -1, item, (10, 10))
                cb.SetValue(False)
                self.sizer2.Add( cb,( iy, ix),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
            
                ix += 1
                value= self.model.getParam(item)
                ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                ctl1.SetValue(str (format_number(value)))
                ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                ctl1.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                self.sizer2.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                
                ix += 1
                text2=wx.StaticText(self, -1, '+/-')
                self.sizer2.Add(text2,(iy, ix),(1,1),\
                                wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
                text2.Hide()  
                ix += 1
                ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                self.sizer2.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ctl2.Hide()
                ix +=1
                # Units
                try:
                    units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                except:
                    units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
                self.sizer2.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
            else:
                if not item in fixed:
                    ip = 0
                    iq += 1
                    cb = wx.CheckBox(self, -1, item, (10, 10))
                    cb.SetValue(False)
                    self.sizer5.Add( cb,( iq, ip),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                    wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                    
                    ip += 1
                    value= self.model.getParam(item)
                    ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                    ctl1.SetValue(str (format_number(value)))
                    ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                    ctl1.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                    self.sizer5.Add(ctl1, (iq,ip),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                else:
                    ik = 0
                    text = wx.StaticText(self, -1, item, style=wx.ALIGN_LEFT)
                    self.sizer6.Add(text,( im, ik),(1,1),  wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
            
                    ik += 1
                    value= self.model.getParam(item)
                    Tctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                    Tctl.SetValue(str (format_number(value)))
                    Tctl.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                    Tctl.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                    self.sizer6.Add(Tctl, (im,ik),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                    self.fixed_param.append([item, Tctl])
                    im += 1
            #save data
            
            self.parameters.append([cb,ctl1,text2,ctl2])
                
        iy+=1
        self.sizer2.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
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
       
        self.compute_chisqr()
        self.vbox.Layout()
        self.SetScrollbars(20,20,55,40)
        self.Layout()
        self.GrandParent.GetSizer().Layout()
        
       
        
    def _onparamEnter(self,event):
        """ 
            when enter value on panel redraw model according to changed
        """
        self.set_model()
        self.compute_chisqr()
        
    def set_model(self): 
        if len(self.parameters) !=0 and self.model !=None:
            # Flag to register when a parameter has changed.
            for item in self.parameters:
                try:
                    self.text2_3.Hide()
                    item[2].Hide()
                    item[3].Clear()
                    item[3].Hide()
                except:
                     wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Drawing  Error:wrong value entered : %s"% sys.exc_value))
        self.set_model_parameter()
        
    def set_model_parameter(self):
        if len(self.parameters) !=0 and self.model !=None:
            # Flag to register when a parameter has changed.
            is_modified = False
            for item in self.fixed_param:
                
                try:
                     name=str(item[0])
                     value= float(item[1].GetValue())
#                     print "model para", name,value
                     # If the value of the parameter has changed,
                     # update the model and set the is_modified flag
                     if value != self.model.getParam(name):
                         self.model.setParam(name,value)
                         is_modified = True
                except:
                     wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Model Drawing  Error:wrong value entered : %s"% sys.exc_value))
                
            for item in self.parameters:
#                print "paramters",str(item[0].GetLabelText())
                try:
                     name=str(item[0].GetLabelText())
                     value= float(item[1].GetValue())
#                     print "model para", name,value
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
                self.manager.redraw_model(qmin=self.qmin, qmax=self.qmax)
         
    def select_all_param(self,event): 
        """
             set to true or false all checkBox given the main checkbox value cb1
        """
        self.param_toFit=[]
        if  self.parameters !=[]:
            if  self.cb1.GetValue()==True:
                for item in self.parameters:
                    item[0].SetValue(True)
                    list= [item[0],item[1],item[2],item[3]]
                    self.param_toFit.append(list )
               
                if not (len(self.param_toFit ) >0):
                    self.xmin.Disable()
                    self.xmax.Disable()
                else:
                    self.xmin.Enable()
                    self.xmax.Enable()
            else:
                for item in self.parameters:
                    item[0].SetValue(False)
                self.param_toFit=[]
              
                self.xmin.Disable()
                self.xmax.Disable()
                
                
    def select_param(self,event):
        """ 
            Select TextCtrl  checked for fitting purpose and stores them
            in  self.param_toFit=[] list
        """
        self.param_toFit=[]
        for item in self.parameters:
            if item[0].GetValue()==True:
                list= [item[0],item[1],item[2],item[3]]
                if not (list  in self.param_toFit):
                    self.param_toFit.append(list )  
            else:
                if item in self.param_toFit:
                    self.param_toFit.remove(item)
        if len(self.parameters)==len(self.param_toFit):
            self.cb1.SetValue(True)
        else:
            self.cb1.SetValue(False)
            
        if not (len(self.param_toFit ) >0):
            self.xmin.Disable()
            self.xmax.Disable()
        else:
            self.xmin.Enable()
            self.xmax.Enable()
       
   
       
  
    def onsetValues(self,chisqr, out,cov):
        """
            Build the panel from the fit result
            @param chisqr:Value of the goodness of fit metric
            @param out:list of parameter with the best value found during fitting
            @param cov:Covariance matrix
       
        """
        #print "fitting : onsetvalues out",out
        self.tcChi.Clear()
        self.tcChi.SetValue(format_number(chisqr))
        params = {}
        is_modified = False
        has_error = False
        if out.__class__==numpy.float64:
            self.param_toFit[0][1].SetValue(format_number(out))
            self.param_toFit[0][1].Refresh()
            if cov !=None :
                self.text2_3.Show()
                self.param_toFit[0][2].Show()
                self.param_toFit[0][3].Clear()
                self.param_toFit[0][3].SetValue(format_number(cov[0]))
                self.param_toFit[0][3].Show()
        #out is a list : set parameters and errors in TextCtrl
        else:
            i=0
            #print "fitpage: list param  model",list
            #for item in self.param_toFit:
            #    print "fitpage: list display",item[0].GetLabelText()
            for item in self.param_toFit:
                if( out != None ) and len(out)<=len(self.param_toFit)and i < len(out):
                    #item[1].SetValue(format_number(out[i]))
                    item[1].SetValue(format_number(self.model.getParam(item[0].GetLabelText())))
                    item[1].Refresh() 
                if (cov !=None)and len(cov)<=len(self.param_toFit)and i < len(cov):
                    self.text2_3.Show() 
                    item[2].Show()
                    item[3].Clear()
                    item[3].SetValue(format_number(cov[i]))
                    item[3].Show()   
                i+=1
        
        self.vbox.Layout()
        self.SetScrollbars(20,20,55,40)
        self.Layout()
        self.GrandParent.GetSizer().Layout()
        
        
    def onSmear(self, event):
        if event.GetString()=="None":
            self.manager.set_smearer(None)   
            
            
        if event.GetString()=="Gaussian Resolution":
            from DataLoader.qsmearing import smear_selection
            smear =smear_selection( self.data )
            self.manager.set_smearer(smear)   
#            print "on smearing"
       