import sys
import wx
import wx.lib
import numpy,math
import copy

from sans.guicomm.events import StatusEvent 
from sans.guiframe.utils import format_number
from modelpage import ModelPage  
from modelpage import format_number
(ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 80



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
    name=None
    
    def __init__(self, parent,data, *args, **kwargs):
        wx.ScrolledWindow.__init__(self, parent, *args, **kwargs)
        
        """ 
            Initialization of the Panel
        """
        self.data = data
        self.enable2D=False
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
        #combox box for type of dispersion
        self.vbox.Add(self.sizer7)
        #dispersion parameters layer
        self.vbox.Add(self.sizer8)
        #fit info layer
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer9)
       
        
        #---------sizer 1 draw--------------------------------
        self.DataSource  =wx.StaticText(self, -1,str(data.name))
        #Filing the sizer containing data related fields
        ix = 0
        iy = 1
        self.sizer1.Add(wx.StaticText(self, -1, 'Data Source Name : '),(iy,ix),\
                 (1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
       
        ix += 1
        self.sizer1.Add(self.DataSource,(iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        #---------sizer 2 draw--------------------------------
        #set maximum range for x in linear scale
        if not hasattr(self.data,"data"): #Display only for 1D data fit
            ix = 0
            iy = 1
            # Minimum value of data   
            self.data_min    = wx.StaticText(self, -1,str(format_number(numpy.min(data.x))))
            # Maximum value of data  
            self.data_max    =  wx.StaticText(self, -1,str(format_number(numpy.max(data.x))))   
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
        self.disable_smearer = wx.RadioButton(self, -1, 'No', (10, 10), style=wx.RB_GROUP)
        self.enable_smearer = wx.RadioButton(self, -1, 'Yes', (10, 30))
        self.Bind(wx.EVT_RADIOBUTTON, self.onSmear, id=self.disable_smearer.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSmear, id=self.enable_smearer.GetId())
        ix = 0
        iy = 1
        self.sizer3.Add(wx.StaticText(self,-1,'Instrument Smearing'),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer3.Add(self.enable_smearer,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer3.Add(self.disable_smearer,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix =0
        iy+=1
        self.sizer3.Add((20,20),(iy,ix),(1,1),wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)  
            
        #------------------ sizer 4  draw------------------------   
        self.modelbox = wx.ComboBox(self, -1)
        self.tcChi    =  wx.StaticText(self, -1, str(0), style=wx.ALIGN_LEFT)
        self.tcChi.Hide()
        self.text1_1 = wx.StaticText(self, -1, 'Chi2/dof', style=wx.ALIGN_LEFT)
        self.text1_1.Hide()
        #filling sizer2
        ix = 0
        iy = 1
        self.sizer4.Add(wx.StaticText(self,-1,'Model'),(iy,ix),(1,1)\
                  , wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer4.Add(self.modelbox,(iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer4.Add(self.text1_1,(iy,ix),(1,1),\
                   wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer4.Add(self.tcChi,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
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
        
        
        id = wx.NewId()
        self.btFit =wx.Button(self,id,'Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self.onFit,id=id)
        self.btFit.SetToolTipString("Perform fit.")
         ## Q range
        #print "self.data fitpage1D" , self.data,hasattr(self.data,"data")
        # Reversed to the codes; Need to think  carefully about consistency in q between 2D plot and fitting
        if not hasattr(self.data,"data"):
            self.qmin_x= numpy.min(self.data.x)
            self.qmax_x= numpy.max(self.data.x)
            self.num_points= len(self.data.x)
        else:
            # Reversed to the codes; Need to think  carefully about consistency in q between 2D plot and fitting
            radius1= math.sqrt(math.pow(self.data.xmin, 2)+ math.pow(self.data.ymin, 2))
            radius2= math.sqrt(math.pow(self.data.xmax, 2)+ math.pow(self.data.ymin, 2))
            radius3= math.sqrt(math.pow(self.data.xmin, 2)+ math.pow(self.data.ymax, 2))
            radius4= math.sqrt(math.pow(self.data.xmax, 2)+ math.pow(self.data.ymax, 2))
            #self.qmin_x = 0
            #self.qmax_x = max(radius1, radius2, radius3, radius4)
            self.qmin_x= 0#self.data.xmin
            self.qmax_x= math.sqrt(math.pow(max(math.fabs(self.data.xmax),math.fabs(self.data.xmin)),2)
                            +math.pow(max(math.fabs(self.data.ymax),math.fabs(self.data.ymin)),2))#self.data.xmax           
            #print "data2D range",self.qmax_x
        
        self.num_points= 100
         
        
        
        self.qmin    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.qmin.SetValue(str(format_number(self.qmin_x)))
        self.qmin.SetToolTipString("Minimun value of x in linear scale.")
        self.qmin.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
        self.qmin.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
        self.qmin.Enable()
        
        self.qmax    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.qmax.SetValue(str(format_number(self.qmax_x)))
        self.qmax.SetToolTipString("Maximum value of x in linear scale.")
        self.qmax.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
        self.qmax.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
        self.qmax.Enable()

        self.npts    = wx.TextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.npts.SetValue(format_number(self.num_points))
        self.npts.SetToolTipString("Number of point to plot.")
        self.npts.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
        self.npts.Bind(wx.EVT_TEXT_ENTER, self._onparamEnter)
        self.npts.Disable()
        self.npts.Hide()
        ix = 0
        iy = 1 
        self.sizer9.Add(wx.StaticText(self, -1, 'Fitting Range'),(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1 
        self.sizer9.Add(wx.StaticText(self, -1, 'Min'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer9.Add(wx.StaticText(self, -1, 'Max'),(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        #ix += 1
        #self.sizer9.Add(wx.StaticText(self, -1, 'Npts'),(iy, ix),(1,1),\
        #                    wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix = 0
        iy += 1
        self.sizer9.Add(wx.StaticText(self, -1, 'Q range'),(iy, ix),(1,1),\
                            wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer9.Add(self.qmin,(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer9.Add(self.qmax,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1
        self.sizer9.Add(self.npts,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        ix += 1
        self.sizer9.Add(self.btFit,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        """
        id = wx.NewId()
        self.btStopFit =wx.Button(self,id,'Stop')
        self.btStopFit.Bind(wx.EVT_BUTTON, self.onStopFit,id=id)
        self.btStopFit.SetToolTipString("Stop the current fitting job.")
        self.btStopFit.Hide()
        ix += 1
        self.sizer9.Add(self.btStopFit,(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        """
        ix =0
        iy+=1 
        self.sizer9.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        # contains link between  model ,all its parameters, and panel organization
        self.parameters=[]
        self.fixed_param=[]
        self.fittable_param=[]
        #list of dispersion paramaters
        self.disp_list=[]
        #contains link between a model and selected parameters to fit 
        self.param_toFit=[]
        # model on which the fit would be performed
        self.model=None
        self.back_up_model= None
        #dictionary of model name and model class
        self.model_list_box={}    
                     
        if self.model == None:
            self.qmin.Disable()
            self.qmax.Disable() 
        else:
            self.qmin.Enable()
            self.qmax.Enable() 

       
        self.vbox.Layout()
        self.vbox.Fit(self) 
        self.SetSizer(self.vbox)
        self.SetScrollbars(20,20,55,40)
        
        self.Centre()
        self.Layout()
        self.GrandParent.GetSizer().Layout()
   
    def compute_chisqr2D(self):
        """ @param fn: function that return model value
            @return residuals
        """
        flag=self.checkFitRange()
        res=[]
        if flag== True:
            try:
                print "compute",self.data.err_data
                self.qmin_x = float(self.qmin.GetValue())
                self.qmax_x = float(self.qmax.GetValue())
                for i in range(len(self.data.x_bins)):
                    #if self.data.x_bins[i]>= self.qmin_x and self.data.x_bins[i]<= self.qmax_x:
                        for j in range(len(self.data.y_bins)):
                            if math.pow(self.data.x_bins[i],2)+math.pow(self.data.y_bins[j],2)>=math.pow(self.qmin_x,2):
                                if math.pow(self.data.x_bins[i],2)+math.pow(self.data.y_bins[j],2)<=math.pow(self.qmax_x,2):
                            #if self.data.y_bins[j]>= self.qmin_x and self.data.y_bins[j]<= self.qmax_x:
                                    chisqrji=(self.data.data[j][i]- self.model.runXY(\
                                                                                        [self.data.y_bins[j],self.data.x_bins[i]]))\
                                                                                        /self.data.err_data[j][i]
                                    res.append( math.pow(chisqrji,2) )
                sum=0
               
                for item in res:
                    if numpy.isfinite(item):
                        sum +=item
                #print "chisqr : sum 2D", xmin, xmax, ymin, ymax,sum
                #print len(res)
                self.tcChi.SetLabel(format_number(math.fabs(sum/ len(res))))
            except:
                raise
                wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Chisqr cannot be compute: %s"% sys.exc_value))
        
    def onStopFit(self, event):
        self.manager.stop_fit()
        self.btStopFit.Hide()
        self.btFit.Show(True)
        self.vbox.Layout()
        self.SetScrollbars(20,20,55,40)
        self.Layout()
        self.parent.GetSizer().Layout()
        
    def compute_chisqr(self):
        """ @param fn: function that return model value
            @return residuals
        """
        
        flag=self.checkFitRange()
        #print "flag", flag
        if flag== True:
            try:
                if hasattr(self.data,"data"):
                    self.compute_chisqr2D()
                    return
                else:
                    self.qmin_x = float(self.qmin.GetValue())
                    self.qmax_x = float(self.qmax.GetValue())
                    #print "self.qmin_x, self.qmax_x",self.qmin_x,self.qmax_x
                    x,y,dy = [numpy.asarray(v) for v in (self.data.x,self.data.y,self.data.dy)]
                    if self.qmin_x==None and self.qmax_x==None: 
                        fx =numpy.asarray([self.model.run(v) for v in x])
                        temp=(y - fx)/dy
                        res= temp*temp
                    else:
                        idx = (x>= self.qmin_x) & (x <=self.qmax_x)
                        fx = numpy.asarray([self.model.run(item)for item in x[idx ]])
                        temp=(y[idx] - fx)/dy[idx]
                        res= temp*temp
                   
                    sum=0
                    for item in res:
                        if numpy.isfinite(item):
                            sum +=item
                    self.tcChi.SetLabel(format_number(math.fabs(sum/ len(res))))
            except:
                wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Chisqr cannot be compute: %s"% sys.exc_value))
            
    def _on_select_model(self,event):
        """
            react when a model is selected from page's combo box
            post an event to its owner to draw an appropriate theory
        """
        self.btFit.SetFocus()
        self.disable_disp.SetValue(True)
        self.sizer8.Clear(True)
        self.sizer7.Clear(True)       
        self.vbox.Layout()
        self.SetScrollbars(20,20,55,40)
        self.Layout()
        self.parent.GetSizer().Layout()

        for item in self.model_list_box.itervalues():
            name = item.__name__
            if hasattr(item, "name"):
                name = item.name
            #print "fitpage: _on_select_model model name",name ,event.GetString()
            if name == None:
                self.qmin.Disable()
                self.qmax.Disable() 
            else:
                self.qmin.Enable()
                self.qmax.Enable() 
            
            if name ==event.GetString():
                try:
                    self.model=item()
                    self.back_up_model= self.model.clone()
                    evt = ModelEventbox(model=self.model,name=name)
                    wx.PostEvent(self.event_owner, evt)
                    self.text1_1.Show()
                    self.compute_chisqr()
                    self.tcChi.Show()
                except:
                    raise #ValueError,"model.name is not equal to model class name"
                break       
    def onFit(self,event):
        """ signal for fitting"""
         
        flag=self.checkFitRange()
        self.set_manager(self.manager)
     
        self.qmin_x=float(self.qmin.GetValue())
        self.qmax_x =float( self.qmax.GetValue())
        if len(self.param_toFit) >0 and flag==True:
            #if self.data.name == self.model.__class__.__name__:
                #print "when here have the same name "
                #wx.PostEvent(self.parent.parent, StatusEvent(status=\
                            #"Attempt to fit model %s with itself. fit will\
                            #not be performed"%self.data.name))
                #return 
            self.manager.schedule_for_fit( value=1,fitproblem =None) 
            if hasattr(self.data, "data"):
                self.manager._on_single_fit(qmin=self.qmin_x,qmax=self.qmax_x,
                                            ymin=self.data.ymin, ymax=self.data.ymax,
                                            xmin=self.data.xmin,xmax=self.data.xmax)
                #self.btStopFit.Show()
                #self.btFit.Hide()
            else:
                 self.manager._on_single_fit(qmin=self.qmin_x,qmax=self.qmax_x)
                 #self.btStopFit.Show()
                 #self.btFit.Hide()
            self.vbox.Layout()
            self.SetScrollbars(20,20,55,40)
            self.Layout()
            self.parent.GetSizer().Layout()
        else:
              wx.PostEvent(self.parent.parent, StatusEvent(status=\
                            "Select at least one parameter to fit "))
  
   
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
                    #enter dispersion value 
                    pass
        self.set_model_parameter()
        
    
    def select_all_param(self,event): 
        """
             set to true or false all checkBox given the main checkbox value cb1
        """
        self.select_all_param_helper()
                
                
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
                    
        for item in self.fittable_param:
            if item[0].GetValue()==True:
                list= [item[0],item[1],item[2],item[3]]
                if not (list  in self.param_toFit):
                    self.param_toFit.append(list )  
            else:
                if item in self.param_toFit:
                    self.param_toFit.remove(item)           
                    
                    
        if len(self.parameters)+len(self.fittable_param) ==len(self.param_toFit):
            self.cb1.SetValue(True)
        else:
            self.cb1.SetValue(False)
        """    
        #qmax, qmin Input enabled all the time   
        self.qmin.Enable()
        self.qmax.Enable()      
        """
  
    def onsetValues(self,chisqr, out,cov):
        """
            Build the panel from the fit result
            @param chisqr:Value of the goodness of fit metric
            @param out:list of parameter with the best value found during fitting
            @param cov:Covariance matrix
       
        """
        #print "fitting : onsetvalues out",out
        self.tcChi.SetLabel(format_number(chisqr))
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
            j=0
            #print  "fitpage: list param  model",list
            #for item in self.param_toFit:
            #print "fitpage: list display",item[0].GetLabelText()
            for item in self.param_toFit:
                if( out != None ) and len(out)<=len(self.param_toFit)and i < len(out):
                    #item[1].SetValue(format_number(out[i]))
                    item[1].SetValue(format_number(self.model.getParam(item[0].GetLabelText())))
                    item[1].Refresh()
                if(cov !=None)and len(cov)<=len(self.param_toFit)and i < len(cov):
                    self.text2_3.Show() 
                    item[2].Show()
                    item[3].Clear()
                    for j in range(len(out)):
                        if out[j]==self.model.getParam(item[0].GetLabelText()):#.SetValue(format_number(self.model.getParam(item[0].GetLabelText()))):
                            #print "jjj", j,item[1],item[1].SetValue(format_number(self.model.getParam(item[0].GetLabelText())))
                            break
                    item[3].SetValue(format_number(cov[j]))
                    item[3].Show()   
                i+=1
        
        self.vbox.Layout()
        self.SetScrollbars(20,20,55,40)
        self.Layout()
        self.GrandParent.GetSizer().Layout()
        
        
    def onSmear(self, event):
        #print "in smearer",self.enable_smearer.GetValue()
        smear =None
        msg=""
        if self.enable_smearer.GetValue():
            from DataLoader.qsmearing import smear_selection
            smear =smear_selection( self.data )
            if hasattr(self.data,"dxl"):
                msg= ": Resolution smearing parameters"
            if hasattr(self.data,"dxw"):
                msg= ": Slit smearing parameters"
            if smear ==None:
                wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Data contains no smearing information"))
            else:
                wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Data contains smearing information %s"%msg))
        self.manager.set_smearer(smear)   
            
              
        
       