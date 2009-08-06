

import sys
import wx
import wx.lib.newevent
import numpy
import copy
import math
from sans.models.dispersion_models import ArrayDispersion, GaussianDispersion

from sans.guicomm.events import StatusEvent   
from sans.guiframe.utils import format_number,check_float

## event to post model to fit to fitting plugins
(ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()

## event to know the selected fit engine
(FitterTypeEvent, EVT_FITTER_TYPE)   = wx.lib.newevent.NewEvent()
(FitStopEvent, EVT_FIT_STOP)   = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 76

import basepage
from basepage import BasicPage
from basepage import PageInfoEvent
from DataLoader.qsmearing import smear_selection

class FitPage(BasicPage):
    """
        FitPanel class contains fields allowing to display results when
        fitting  a model and one data
        @note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.
  
    """
    def __init__(self,parent, page_info):
        BasicPage.__init__(self, parent, page_info)
        """ 
            Initialization of the Panel
        """
        ## fit page does not content npts txtcrtl
        self.npts=None
        ## thread for compute Chisqr
        self.calc_Chisqr=None
        ## default fitengine type
        self.engine_type = None
        ## draw sizer
        self._fill_datainfo_sizer()
       
        self._fill_model_sizer( self.sizer1)
        self._fill_range_sizer() 
        #self._on_select_model(event=None)
        if self.data !=None:
            self.smearer = smear_selection( self.data )
            if self.smearer ==None:
                self.enable_smearer.Disable()
                self.disable_smearer.Disable()
       
        ## to update the panel according to the fit engine type selected
        self.Bind(EVT_FITTER_TYPE,self._on_engine_change)
        self.Bind(EVT_FIT_STOP,self._on_fit_complete)
    
    def _on_fit_complete(self, event):
        """
            When fit is complete ,reset the fit button label.
        """
        #self.btFit.SetLabel("Fit")
        #self.btFit.Unbind(event=wx.EVT_BUTTON, id=self.btFit.GetId())
        #self.btFit.Bind(event=wx.EVT_BUTTON, handler=self._onFit,id=self.btFit.GetId())
        pass
        
        
    def _on_engine_change(self, event):
        """
            get an event containing the current name of the fit engine type
            @param event: FitterTypeEvent containing  the name of the current engine
        """
        self.engine_type = event.type
         
        if len(self.parameters)==0:
            return
        if event.type =="park":
            self.btFit.SetLabel("Fit")
        for item in self.parameters:
            if event.type =="scipy":
                item[5].SetValue("")
                item[5].Hide()
                item[6].SetValue("")
                item[6].Hide()
                self.text2_min.Hide()
                self.text2_max.Hide()
            else:
                item[5].Show(True)
                item[6].Show(True)
                self.text2_min.Show(True)
                self.text2_max.Show(True)
        for item in self.orientation_params:
            if event.type =="scipy":
                item[5].SetValue("")
                item[5].Hide()
                item[6].SetValue("")
                item[6].Hide()
                self.text2_min.Hide()
                self.text2_max.Hide()
            else:
                item[5].Show(True)
                item[6].Show(True)
                self.text2_min.Show(True)
                self.text2_max.Show(True)
            
        for item in self.orientation_params_disp:
            if event.type =="scipy":
                item[5].SetValue("")
                item[5].Hide()
                item[6].SetValue("")
                item[6].Hide()
                self.text2_min.Hide()
                self.text2_max.Hide()
            else:
                item[5].Show(True)
                item[6].Show(True)
                self.text2_min.Show(True)
                self.text2_max.Show(True)
                
        self.sizer3.Layout()
        self.SetScrollbars(20,20,200,100)
        
    
    def _fill_range_sizer(self):
        """
            Fill the sizer containing the plotting range
            add  access to npts
        """
        sizer_fit = wx.GridSizer(1, 1,0, 0)
    
        self.btFit = wx.Button(self,wx.NewId(),'Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit,id= self.btFit.GetId())
        self.btFit.SetToolTipString("Perform fit.")
      
        
        sizer_fit.Add((5,5),1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)        
        sizer_fit.Add(self.btFit,0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5) 
        
        sizer_smearer = wx.BoxSizer(wx.HORIZONTAL)
        #Filling the sizer containing instruments smearing info.
        self.disable_smearer = wx.RadioButton(self, -1, 'No', style=wx.RB_GROUP)
        self.enable_smearer = wx.RadioButton(self, -1, 'Yes')
        self.Bind(wx.EVT_RADIOBUTTON, self.onSmear, id=self.disable_smearer.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSmear, id=self.enable_smearer.GetId())
        
        sizer_smearer.Add(wx.StaticText(self,-1,'Instrument Smearing? '))
        sizer_smearer.Add((10, 10))
        sizer_smearer.Add( self.enable_smearer )
        sizer_smearer.Add((10,10))
        sizer_smearer.Add( self.disable_smearer )
        
        #Display Chi^2/dof
        sizer_smearer.Add((68,10))
        box_description= wx.StaticBox(self, -1,'Chi2/dof')
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        boxsizer1.SetMinSize((60,-1))
        temp_smearer = None
        if self.enable_smearer.GetValue():
            temp_smearer= self.smearer
        
        self.tcChi    =  wx.StaticText(self, -1, "-", style=wx.ALIGN_LEFT)
         
        boxsizer1.Add( self.tcChi )   
        sizer_smearer.Add( boxsizer1 )
               
        #Set sizer for Fitting section
        self._set_range_sizer( title="Fitting",object1=sizer_smearer, object= sizer_fit)
  
       
    def _fill_datainfo_sizer(self):
        """
            fill sizer 0 with data info
        """
        self.sizer0.Clear(True)
        ## no loaded data , don't fill the sizer
        if self.data== None:
            self.sizer0.Layout()
            return
        
        box_description= wx.StaticBox(self, -1, 'Data')
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        #----------------------------------------------------------
        sizer_data = wx.GridSizer(3, 3,5, 5)
        #Filling the sizer containing data related fields
        DataSource  =wx.StaticText(self, -1,str(self.data.name))

        sizer_data.Add(wx.StaticText(self, -1, 'Source Name : '))
        sizer_data.Add(DataSource )
        sizer_data.Add( (0,5) )
        
        #---------sizer 2 draw--------------------------------
        #set maximum range for x in linear scale
        if not hasattr(self.data,"data"): #Display only for 1D data fit
            # Minimum value of data   
            data_min = min(self.data.x)
            # Maximum value of data  
            data_max = max(self.data.x)
            text4_3 = wx.StaticText(self, -1, 'Total Q Range (1/A)',
                                     style=wx.ALIGN_LEFT)
            sizer_data.Add( text4_3 )
            sizer_data.Add(wx.StaticText(self, -1, "Min : %s"%str(data_min)))
            sizer_data.Add(wx.StaticText(self, -1, "Max : %s"%str(data_max)))
            
        else:
            ## Minimum value of data 
            data_min= 0
            x= max(math.fabs(self.data.xmin), math.fabs(self.data.xmax)) 
            y= max(math.fabs(self.data.ymin), math.fabs(self.data.ymax))
            ## Maximum value of data  
            data_max = math.sqrt(x*x + y*y)
          
            #For qmin and qmax, do not use format_number
            #.(If do, qmin and max could be different from what is in the data.)
            text4_3 = wx.StaticText(self, -1, "Total Q Range (1/A)",
                                     style=wx.ALIGN_LEFT)
            sizer_data.Add( text4_3 )
            sizer_data.Add(wx.StaticText(self, -1, "Min : %s"%str(data_min)))
            sizer_data.Add(wx.StaticText(self, -1, "Max : %s"%str(data_max)))
        ## set q range to plot
        self.qmin_x= data_min
        self.qmax_x= data_max

        boxsizer1.Add(sizer_data)
        #------------------------------------------------------------
        self.sizer0.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        self.sizer0.Layout()
       
        
       
    def _fill_model_sizer(self, sizer):
        """
            fill sizer containing model info
        """
       
        ## class base method  to add view 2d button    
        self._set_model_sizer(sizer=sizer, title="Model",object=None )    
        
    
    #def _set_sizer_gaussian(self):
    def _set_sizer_dispersion(self, dispersity):
        """
            draw sizer with gaussian dispersity parameters
        """
        self.fittable_param=[]
        self.fixed_param=[]
        self.orientation_params_disp=[]
       
        self.sizer4_4.Clear(True)
       
        if self.model==None:
            ##no model is selected
            return
        if not self.enable_disp.GetValue():
            ## the user didn't select dispersity display
            return 
        
        self._reset_dispersity()
        # Create the dispersion objects
        for item in self.model.dispersion.keys():
            #disp_model =  GaussianDispersion()
            disp_model = dispersity()
            self._disp_obj_dict[item] = disp_model
            self.model.set_dispersion(item, disp_model)
            self.state._disp_obj_dict[item]= disp_model

        ix=0
        iy=1
        disp = wx.StaticText(self, -1, 'Names')
        self.sizer4_4.Add(disp,( iy, ix),(1,1), 
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1 
        values = wx.StaticText(self, -1, 'Values')
        self.sizer4_4.Add(values,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix +=2 
        self.text_disp_1 = wx.StaticText(self, -1, 'Errors')
        self.sizer4_4.Add( self.text_disp_1,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text_disp_1.Hide()
        ix += 1 
        npts = wx.StaticText(self, -1, 'Npts')
        self.sizer4_4.Add(npts,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1 
        nsigmas = wx.StaticText(self, -1, 'Nsigmas')
        self.sizer4_4.Add(nsigmas,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)

        for item in self.model.dispersion.keys():
            if not item in self.model.orientation_params:
                self.disp_cb_dict[item]= None
                name1=item+".width"
                name2=item+".npts"
                name3=item+".nsigmas"
                iy += 1
                for p in self.model.dispersion[item].keys(): 
        
                    if p=="width":
                        ix = 0
                        cb = wx.CheckBox(self, -1, name1, (10, 10))
                        wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                        self.sizer4_4.Add( cb,( iy, ix),(1,1),  
                                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                        ix = 1
                        value= self.model.getParam(name1)
                        ctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                            style=wx.TE_PROCESS_ENTER)
                        ctl1.SetValue(str (format_number(value)))
                        self.sizer4_4.Add(ctl1, (iy,ix),(1,1),wx.EXPAND)
                        ## text to show error sign
                        ix = 2
                        text2=wx.StaticText(self, -1, '+/-')
                        self.sizer4_4.Add(text2,(iy, ix),(1,1),
                                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        text2.Hide() 
                        ## txtcrtl to add error from fit
                        ix = 3
                        ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                        self.sizer4_4.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        ctl2.Hide()
                        self.fittable_param.append([cb,name1,ctl1,text2,
                                                    ctl2, None, None,None])
                    elif p=="npts":
                            ix = 4
                            value= self.model.getParam(name2)
                            Tctl = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            
                            Tctl.SetValue(str (format_number(value)))
                            self.sizer4_4.Add(Tctl, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name2, Tctl,None,None,
                                                      None, None,None])
                    elif p=="nsigmas":
                            ix = 5
                            value= self.model.getParam(name3)
                            Tctl = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            Tctl.SetValue(str (format_number(value)))
                            self.sizer4_4.Add(Tctl, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            ix +=1
                            self.sizer4_4.Add((20,20), (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            
                            self.fixed_param.append([None,name3, Tctl
                                                     ,None,None, None, None,None])
        ix =0
        iy +=1 
        self.sizer4_4.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)  
        for item in self.model.dispersion.keys():
            if  item in self.model.orientation_params:
                self.disp_cb_dict[item]= None
                name1=item+".width"
                name2=item+".npts"
                name3=item+".nsigmas"
                iy += 1
                for p in self.model.dispersion[item].keys(): 
        
                    if p=="width":
                        ix = 0
                        cb = wx.CheckBox(self, -1, name1, (10, 10))
                        wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                        self.sizer4_4.Add( cb,( iy, ix),(1,1),  
                                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                        if self.data.__class__.__name__ =="Data2D":
                            cb.Show(True)
                            cb.Enable()
                        else:
                            cb.Hide()
                            cb.Disable()
                        ix = 1
                        value= self.model.getParam(name1)
                        ctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                            style=wx.TE_PROCESS_ENTER)
                        ctl1.SetValue(str (format_number(value)))
                        if self.data.__class__.__name__ =="Data2D":
                            ctl1.Show(True)
                            ctl1.Enable()
                        else:
                            ctl1.Hide()
                            ctl1.Disable()
                        self.sizer4_4.Add(ctl1, (iy,ix),(1,1),wx.EXPAND)
                        ## text to show error sign
                        ix = 2
                        text2=wx.StaticText(self, -1, '+/-')
                        self.sizer4_4.Add(text2,(iy, ix),(1,1),
                                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        text2.Hide() 
                        ## txtcrtl to add error from fit
                        ix = 3
                        ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                        self.sizer4_4.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        ctl2.Hide()
                        if self.data.__class__.__name__ =="Data2D":
                            #ctl2.Show(True)
                            ctl2.Enable()
                        else:
                            #ctl2.Hide()
                            ctl2.Disable()
                        self.fittable_param.append([cb,name1,ctl1,text2,
                                                    ctl2, None, None,None])
                        self.orientation_params_disp.append([cb,name1,ctl1,text2,
                                                    ctl2, None, None,None])
                    elif p=="npts":
                            ix = 4
                            value= self.model.getParam(name2)
                            Tctl = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            
                            Tctl.SetValue(str (format_number(value)))
                            if self.data.__class__.__name__ =="Data2D":
                                Tctl.Show(True)
                                Tctl.Enable()
                            else:
                                Tctl.Hide()
                                Tctl.Disable()
                            self.sizer4_4.Add(Tctl, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name2, Tctl,None,None,
                                                      None, None,None])
                            self.orientation_params_disp.append([None,name2, Tctl,None,None,
                                                      None, None,None])
                    elif p=="nsigmas":
                            ix = 5
                            value= self.model.getParam(name3)
                            Tctl = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            Tctl.SetValue(str (format_number(value)))
                            if self.data.__class__.__name__ =="Data2D":
                                Tctl.Show(True)
                                Tctl.Enable()
                            else:
                                Tctl.Hide()
                                Tctl.Disable()
                            self.sizer4_4.Add(Tctl, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            ix +=1
                            self.sizer4_4.Add((20,20), (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name3, Tctl
                                                     ,None,None, None, None,None])    
                            self.orientation_params_disp.append([None,name3, Tctl
                                                     ,None,None, None, None,None])
   
        self.state.disp_cb_dict = copy.deepcopy(self.disp_cb_dict)      
        self.state.model = self.model.clone()  
         ## save state into
        self._copy_parameters_state(self.orientation_params_disp,
                                     self.state.orientation_params_disp)
        self._copy_parameters_state(self.fittable_param, self.state.fittable_param)
        self._copy_parameters_state(self.fixed_param, self.state.fixed_param)
                         
        wx.PostEvent(self.parent, StatusEvent(status=\
                        " Selected Distribution: Gaussian"))   
        ix =0
        iy +=1 
        self.sizer4_4.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)        
        self.sizer4_4.Layout()
        self.sizer4.Layout()
        self.Layout()
        self.SetScrollbars(20,20,200,100)
        self.Refresh()
     
        
    def _onFit(self, event):     
        """
            Allow to fit
        """
        from sans.guiframe.utils import check_value
        flag = check_value( self.qmin, self.qmax) 
        
        if not flag:
            msg= "Fitting range invalid"
            wx.PostEvent(self.parent.parent, StatusEvent(status= msg ))
            return 
        
        if len(self.param_toFit) <= 0:
            msg= "Select at least one parameter to fit"
            wx.PostEvent(self.parent.parent, StatusEvent(status= msg ))
            return 

        # Remove or do not allow fitting on the Q=0 point, especially when y(q=0)=None at x[0].
        #ToDo: Fix this.                
        self.qmin_x = float(self.qmin.GetValue())
        self.qmax_x =float( self.qmax.GetValue())
        self.manager._reset_schedule_problem( value=0)
        self.manager.schedule_for_fit( value=1,page=self,fitproblem =None) 
        self.manager.set_fit_range(page= self,qmin= self.qmin_x, qmax= self.qmax_x)
        
        #single fit 
        self.manager.onFit()
        ## allow stopping the fit 
        #if self.engine_type=="scipy":
        #    self.btFit.SetLabel("Stop")
        #    self.btFit.Unbind(event=wx.EVT_BUTTON, id= self.btFit.GetId())
        #    self.btFit.Bind(event= wx.EVT_BUTTON, handler=self._StopFit, id=self.btFit.GetId())
        #else:
        #    self.btFit.SetLabel("Fit")
        #    self.btFit.Bind(event= wx.EVT_BUTTON, handler=self._onFit, id=self.btFit.GetId())
        self.btFit.SetFocus()    
        self.sizer5.Layout()
        self.SetScrollbars(20,20,55,40)
        
    def _StopFit(self, event):
        """
            Stop fit 
        """
        self.btFit.SetLabel("Fit")
        if self.engine_type=="scipy":
            self.manager.stop_fit()
        self.btFit.Unbind(event=wx.EVT_BUTTON, id=self.btFit.GetId())
        self.btFit.Bind(event=wx.EVT_BUTTON, handler=self._onFit,id=self.btFit.GetId())
       
            
        self.btFit.SetFocus()    
        self.sizer5.Layout()
        self.SetScrollbars(20,20,55,40)    
            
    def _on_select_model(self, event): 
        """
             call back for model selection
        """    
        self._on_select_model_helper() 
        self.set_model_param_sizer(self.model)                   
       
        self.enable_disp.SetValue(False)
        self.disable_disp.SetValue(True)
        self.set_dispers_sizer()
        if self.model !=None:
            try:
                temp_smear= None
                if self.enable_smearer.GetValue():
                    temp_smear= self.smearer
                self.compute_chisqr(temp_smear)
            except:
                ## error occured on chisqr computation
                pass
            evt = ModelEventbox(model=self.model)
            wx.PostEvent(self.event_owner, evt)   
        self.btFit.SetFocus() 
        self.state.enable_disp = self.enable_disp.GetValue()
        self.state.disable_disp = self.disable_disp.GetValue()
        
        self.state.structurecombobox = self.structurebox.GetCurrentSelection()
        self.state.formfactorcombobox = self.formfactorbox.GetCurrentSelection()
      
       
        if event !=None:
            self._undo.Enable(True)
            ## post state to fit panel
            event = PageInfoEvent(page = self)
            wx.PostEvent(self.parent, event) 
     
   
    def _onparamRangeEnter(self, event):
        """
            Check validity of value enter in the parameters range field
        """
        tcrtl= event.GetEventObject()
        if tcrtl.GetValue().lstrip().rstrip()!="":
            try:
                value = float(tcrtl.GetValue())
                tcrtl.SetBackgroundColour(wx.WHITE)
                tcrtl.Refresh()
            except:
                tcrtl.SetBackgroundColour("pink")
                tcrtl.Refresh()
                return
        else:
           tcrtl.SetBackgroundColour(wx.WHITE)
           tcrtl.Refresh()  
        self._onparamEnter_helper() 
        
        ##compute chisqr for range change
        temp_smearer = None
        if self.enable_smearer.GetValue():
            msg=""
            temp_smearer= self.smearer   
         ##Calculate chi2
       
        self.compute_chisqr(smearer= temp_smearer)  
        ## new state posted
        if self.state_change:
            self._undo.Enable(True)
            event = PageInfoEvent(page = self)
            wx.PostEvent(self.parent, event)
            self.state_change= False
        
        
    def _onparamEnter(self,event):
        """ 
            when enter value on panel redraw model according to changed
        """
        tcrtl= event.GetEventObject()
       
        if check_float(tcrtl):
            self._onparamEnter_helper()
            temp_smearer = None
            if self.enable_smearer.GetValue():
                temp_smearer= self.smearer
            
            self.compute_chisqr(smearer= temp_smearer)
            ## new state posted
            if self.state_change:
                self._undo.Enable(True)
                event = PageInfoEvent(page = self)
                wx.PostEvent(self.parent, event)
                self.state_change= False
        else:
            msg= "Cannot Plot :Must enter a number!!!  "
            wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
            return 
        
        
    def set_data(self, data ):
        """
            reset the current data 
        """
        if data ==None:
            return 
        self.data =data
        self.state.data= data 
        self._fill_datainfo_sizer()
        self.SetScrollbars(20,20,200,100)
        self.Layout()   
        
    def reset_page(self, state,first=False):
        """
            reset the state
        """
        if first:
            self._undo.Enable(False)
           
        self.reset_page_helper(state)
        evt = ModelEventbox(model=state.model)
        wx.PostEvent(self.event_owner, evt)   
            
            
    def get_range(self):
        """
            return the fitting range
        """
        return float(self.qmin_x) , float(self.qmax_x)
        
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
      
    def onsetValues(self,chisqr, out,cov):
        """
            Build the panel from the fit result
            @param chisqr:Value of the goodness of fit metric
            @param out:list of parameter with the best value found during fitting
            @param cov:Covariance matrix
       
        """
        self.tcChi.SetLabel(format_number(chisqr))
        params = {}
        is_modified = False
        has_error = False
        self.text2_3.Hide()
        try:
            n = self.disp_box.GetCurrentSelection()
            dispersity= self.disp_box.GetClientData(n)
            name= dispersity.__name__
            if name == "GaussianDispersion":
                if hasattr(self,"text_disp_1" ):
                    if self.text_disp_1 !=None:
                        self.text_disp_1.Hide()
        except:
            pass
        #set the panel when fit result are float not list
        if out.__class__==numpy.float64:
            self.param_toFit[0][2].SetValue(format_number(out))
            self.param_toFit[0][2].Refresh()
            
            self.param_toFit[0][4].Clear()
            self.param_toFit[0][4].Hide()
            if cov !=None :
                self.text2_3.Show(True)
                try:
                    name= dispersity.__name__
                    if name == "GaussianDispersion":
                        if hasattr(self,"text_disp_1" ):
                            if self.text_disp_1 !=None:
                                self.text_disp_1.Show(True)
                except:
                    pass
                if cov[0]==None or  not numpy.isfinite(cov[0]): 
                    self.param_toFit[0][3].Hide()
                    self.param_toFit[0][4].Clear()
                    self.param_toFit[0][4].Hide()
                    self.param_toFit[0][4].Refresh()
                else:
                    self.param_toFit[0][3].Show(True)
                    self.param_toFit[0][4].Clear()
                    self.param_toFit[0][4].SetValue(format_number(cov[0]))
                    self.param_toFit[0][4].Show(True)
                    self.param_toFit[0][4].Refresh()
        else:
            i=0
            j=0
            #Set the panel when fit result are list
            for item in self.param_toFit:
                ## reset error value to initial state
                item[4].Clear()
                item[4].Hide()
                item[4].Refresh()
                if( out != None ) and len(out)<=len(self.param_toFit)and i < len(out):
                    item[2].SetValue(format_number(self.model.getParam(item[1])))
                    item[2].Refresh()
                if(cov !=None)and len(cov)<=len(self.param_toFit)and i < len(cov):
                    self.text2_3.Show(True) 
                    try:
                        name= dispersity.__name__
                        if name == "GaussianDispersion":
                            if hasattr(self,"text_disp_1" ):
                                if self.text_disp_1!=None:
                                    self.text_disp_1.Show(True)
                    except:
                        pass
                    item[3].Show(True)
                    item[4].Clear()
                    for j in range(len(out)):
                        if out[j]==self.model.getParam(item[1]):
                            break
                    ## unable to compare cov[j]==numpy.nan so switch to None
                    if cov[j]==None or not numpy.isfinite(cov[j]):
                        item[3].Hide()
                        item[4].Refresh()
                        item[4].Clear()
                        item[4].Hide()
                    else:
                        item[4].SetValue(format_number(cov[j]))
                        item[4].Refresh()
                        item[4].Show(True)   
                i+=1
        
        self.sizer3.Layout()
        self.sizer4.Layout()
        self.Layout()
        self.Refresh()
        self.SetScrollbars(20,20,200,100)
        
        
    def onSmear(self, event):
        """
            Create a smear object that will change the way residuals
            are compute when fitting
        """
        temp_smearer = None
        if self.enable_smearer.GetValue():
            msg=""
            temp_smearer= self.smearer
            if hasattr(self.data,"dxl"):
                msg= ": Resolution smearing parameters"
            if hasattr(self.data,"dxw"):
                msg= ": Slit smearing parameters"
            if self.smearer ==None:
                wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Data contains no smearing information"))
            else:
                wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Data contains smearing information %s"%msg))
       
        ## set smearing value whether or not the data contain the smearing info
        self.manager.set_smearer(smearer=temp_smearer, qmin= float(self.qmin_x),
                                     qmax= float(self.qmax_x)) 
        ##Calculate chi2
        self.compute_chisqr(smearer= temp_smearer)  
        ## save the state enable smearing
        self.state.smearer= temp_smearer
        #self.save_current_state() 
   
   
    def complete_chisqr(self, output, elapsed=None):  
        """
            print result chisqr
        """
        try:
            if output ==None:
                output= "-"
            self.tcChi.SetLabel(str(format_number(output)))
           
            self.sizer5.Layout()
            self.Layout()
            self.Refresh
            ## post state to fit panel
            self.state.tcChi =output
            #event = PageInfoEvent(page = self)
            #wx.PostEvent(self.parent, event)
        except:
            pass
        
        
    def compute_chisqr1D(self, smearer=None):
        """
            Compute chisqr for 1D
        """
        from sans.guiframe.utils import check_value
        flag = check_value( self.qmin, self.qmax)
        
        if not flag:
            return 
        
        try:
            self.qmin_x = float(self.qmin.GetValue())
            self.qmax_x = float(self.qmax.GetValue())
            ##return residuals within self.qmin_x and self.qmax_x
            from gui_thread import CalcChisqr1D
            ## If a thread is already started, stop it
            if self.calc_Chisqr!= None and self.calc_Chisqr.isrunning():
                self.calc_Chisqr.stop()
                
            self.calc_Chisqr= CalcChisqr1D( data1d= self.data,
                                            model= self.model,
                                            smearer=smearer,
                                            qmin=self.qmin_x,
                                            qmax=self.qmax_x,
                                            completefn = self.complete_chisqr,
                                            updatefn   = None)
    
            self.calc_Chisqr.queue()
            
        except:
            raise ValueError," Could not compute Chisqr for %s Model 2D: "%self.model.name
           
            
   
        
        
    def compute_chisqr2D(self):
        """ 
            compute chi square given a model and data 2D and set the value
            to the tcChi txtcrl
        """
        from sans.guiframe.utils import check_value
        flag = check_value( self.qmin, self.qmax)
        if not flag:
            return 
      
        try:
            self.qmin_x = float(self.qmin.GetValue())
            self.qmax_x = float(self.qmax.GetValue())
           
            ##return residuals within self.qmin_x and self.qmax_x
            from gui_thread import CalcChisqr2D
            ## If a thread is already started, stop it
            if self.calc_Chisqr!= None and self.calc_Chisqr.isrunning():
                self.calc_Chisqr.stop()
           
            self.calc_Chisqr= CalcChisqr2D( data2d= self.data,
                                            model= self.model,
                                            qmin= self.qmin_x,
                                            qmax = self.qmax_x,
                                            completefn = self.complete_chisqr,
                                            updatefn   = None)
    
            self.calc_Chisqr.queue()
          
        except:
           raise

        
    def compute_chisqr(self , smearer=None):
        """ 
            compute chi square given a model and data 1D and set the value
            to the tcChi txtcrl
        """
        from sans.guiframe.utils import check_value
        flag = check_value( self.qmin, self.qmax)
        if flag== True:
            try:
                if hasattr(self.data,"data"):
                    self.compute_chisqr2D()
                    return
                else:
                    self.compute_chisqr1D(smearer=smearer)
                    return
            except:
                wx.PostEvent(self.parent.parent, StatusEvent(status=\
                            "Chisqr Error: %s"% sys.exc_value))
                return 
            
    
    def select_all_param(self,event): 
        """
             set to true or false all checkBox given the main checkbox value cb1
        """            

        self.param_toFit=[]
        if  self.parameters !=[]:
            if  self.cb1.GetValue():
                for item in self.parameters:
                    ## for data2D select all to fit
                    if self.data.__class__.__name__=="Data2D":
                        item[0].SetValue(True)
                        self.param_toFit.append(item )
                    else:
                        ## for 1D all parameters except orientation
                        if not item in self.orientation_params:
                            item[0].SetValue(True)
                            self.param_toFit.append(item )
                if len(self.fittable_param)>0:
                    for item in self.fittable_param:
                        if self.data.__class__.__name__=="Data2D":
                            item[0].SetValue(True)
                            self.param_toFit.append(item )
                        else:
                            ## for 1D all parameters except orientation
                            if not item in self.orientation_params_disp:
                                item[0].SetValue(True)
                                self.param_toFit.append(item )
            else:
                for item in self.parameters:
                    item[0].SetValue(False)
                for item in self.fittable_param:
                    item[0].SetValue(False)
                self.param_toFit=[]
        self._copy_parameters_state(self.orientation_params,
                                     self.state.orientation_params)
        self._copy_parameters_state(self.orientation_params_disp,
                                     self.state.orientation_params_disp)
        self._copy_parameters_state(self.parameters, self.state.parameters)
        self._copy_parameters_state(self.fittable_param, self.state.fittable_param)
        self._copy_parameters_state(self.fixed_param, self.state.fixed_param)
           
        #self.save_current_state()  
        if event !=None:
            self._undo.Enable(True)
            ## post state to fit panel
            event = PageInfoEvent(page = self)
            wx.PostEvent(self.parent, event) 
     
                
                
    def select_param(self,event):
        """ 
            Select TextCtrl  checked for fitting purpose and stores them
            in  self.param_toFit=[] list
        """
        self.param_toFit=[]
        for item in self.parameters:
            #Select parameters to fit for list of primary parameters
            if item[0].GetValue():
                if not (item in self.param_toFit):
                    self.param_toFit.append(item )  
            else:
                #remove parameters from the fitting list
                if item in self.param_toFit:
                    self.param_toFit.remove(item)
        #Select parameters to fit for list of fittable parameters with dispersion          
        for item in self.fittable_param:
            if item[0].GetValue():
                if not (item in self.param_toFit):
                    self.param_toFit.append(item)  
            else:
                #remove parameters from the fitting list
                if item in self.param_toFit:
                    self.param_toFit.remove(item)           
        #Set the value of checkbox that selected every checkbox or not            
        if len(self.parameters)+len(self.fittable_param) ==len(self.param_toFit):
            self.cb1.SetValue(True)
        else:
            self.cb1.SetValue(False)
        ## save current state of the page
        self._copy_parameters_state(self.orientation_params,
                                     self.state.orientation_params)
        self._copy_parameters_state(self.orientation_params_disp,
                                     self.state.orientation_params_disp)
        self._copy_parameters_state(self.parameters, self.state.parameters)
        self._copy_parameters_state(self.fittable_param, self.state.fittable_param)
        self._copy_parameters_state(self.fixed_param, self.state.fixed_param)
        
        #self.save_current_state()
        if event !=None:
            self._undo.Enable(True)
            ## post state to fit panel
            event = PageInfoEvent(page = self)
            wx.PostEvent(self.parent, event) 
     
    
        
    def set_model_param_sizer(self, model):
        """
            Build the panel from the model content
            @param model: the model selected in combo box for fitting purpose
        """
        self.sizer3.Clear(True)
        self.parameters = []
        self.param_toFit=[]
        self.fittable_param=[]
        self.fixed_param=[]
        self.orientation_params=[]
        self.orientation_params_disp=[]
        
        if model ==None:
            self.sizer3.Layout()
            self.SetScrollbars(20,20,200,100)
            return
        ## the panel is drawn using the current value of the fit engine
        if self.engine_type==None and self.manager !=None:
            self.engine_type= self.manager._return_engine_type()
            
        box_description= wx.StaticBox(self, -1,str("Model Parameters"))
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer = wx.GridBagSizer(5,5)
        ## save the current model
        self.model = model
           
        keys = self.model.getParamList()
        #list of dispersion paramaters
        self.disp_list=self.model.getDispParamList()
       
        keys.sort()
    
        iy = 0
        ix = 0
        self.cb1 = wx.CheckBox(self, -1,"Select all", (10, 10))
        wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.select_all_param)
        self.cb1.SetValue(False)
        
        sizer.Add(self.cb1,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        ix +=1
        self.text2_2 = wx.StaticText(self, -1, 'Values')
        sizer.Add(self.text2_2,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix +=2 
        self.text2_3 = wx.StaticText(self, -1, 'Errors')
        sizer.Add(self.text2_3,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_3.Hide()
        ix +=1 
        self.text2_min = wx.StaticText(self, -1, 'Min')
        sizer.Add(self.text2_min,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_min.Hide()
        ix +=1 
        self.text2_max = wx.StaticText(self, -1, 'Max')
        sizer.Add(self.text2_max,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_max.Hide()
        ix += 1
        self.text2_4 = wx.StaticText(self, -1, '[Units]')
        sizer.Add(self.text2_4,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_4.Hide()
        if self.engine_type=="park":
            self.text2_max.Show(True)
            self.text2_min.Show(True)

        for item in keys:
            if not item in self.disp_list and not item in self.model.orientation_params:
               
                iy += 1
                ix = 0
                ## add parameters name with checkbox for selecting to fit
                cb = wx.CheckBox(self, -1, item )
                cb.SetValue(False)
                wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                sizer.Add( cb,( iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
                
                ## add parameter value
                ix += 1
                value= self.model.getParam(item)
                ctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                    style=wx.TE_PROCESS_ENTER)
                
                ctl1.SetValue(format_number(value))
                sizer.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                ## text to show error sign
                ix += 1
                text2=wx.StaticText(self, -1, '+/-')
                sizer.Add(text2,(iy, ix),(1,1),\
                                wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
                text2.Hide() 
                ## txtcrtl to add error from fit
                ix += 1
                ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                sizer.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ctl2.Hide()
                
                param_min, param_max= self.model.details[item][1:]
                ix += 1
                ctl3 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                               kill_focus_callback = self._onparamRangeEnter,
                                               set_focus_callback  = self._onparamRangeEnter)
                if param_min ==None:
                    ctl3.SetValue("")
                else:
                    ctl3.SetValue(str(param_min))
                sizer.Add(ctl3, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ctl3.Hide()
        
                ix += 1
                ctl4 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                               kill_focus_callback = self._onparamRangeEnter,
                                               set_focus_callback  = self._onparamRangeEnter)
                sizer.Add(ctl4, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                if param_max==None:
                    ctl4.SetValue("")
                else:
                    ctl4.SetValue(str(param_max))
                ctl4.Hide()
                
                if self.engine_type=="park":
                    ctl3.Show(True)
                    ctl4.Show(True)
                ix +=1
                # Units
                try:
                    units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                except:
                    units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
                sizer.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                    
                ##[cb state, name, value, "+/-", error of fit, min, max , units]
                self.parameters.append([cb,item, ctl1,
                                        text2,ctl2, ctl3, ctl4,units])
              
        iy+=1
        sizer.Add((10,10),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
        # type can be either Guassian or Array
        if len(self.model.dispersion.values())>0:
            type= self.model.dispersion.values()[0]["type"]
        else:
            type = "Gaussian"
            
        iy += 1
        ix = 0
        #Add tile for orientational angle
        for item in keys:
            if item in self.model.orientation_params:       
                orient_angle = wx.StaticText(self, -1, '[For 2D only]:')
                sizer.Add(orient_angle,(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15) 
                if not self.data.__class__.__name__ =="Data2D":
                    orient_angle.Hide()
                else:
                    orient_angle.Show(True)
                break
      
        #For Gaussian only
        if type.lower() != "array":
            for item in self.model.orientation_params:
                if not item in self.disp_list:
                    iy += 1
                    ix = 0
                    ## add parameters name with checkbox for selecting to fit
                    cb = wx.CheckBox(self, -1, item )
                    cb.SetValue(False)
                    wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                    if self.data.__class__.__name__ =="Data2D":
                        cb.Show(True)
                        cb.Enable()
                    else:
                        cb.Hide()
                        cb.Disable()
                    sizer.Add( cb,( iy, ix),(1,1),
                                 wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
    
                    ## add parameter value
                    ix += 1
                    value= self.model.getParam(item)
                    ctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                        style=wx.TE_PROCESS_ENTER)
                    
                    ctl1.SetValue(format_number(value))
                    if self.data.__class__.__name__ =="Data2D":
                        #ctl1.Show(True)
                        ctl1.Enable()
                    else:
                        #ctl1.Hide()
                        ctl1.Disable()
                    sizer.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                    ## text to show error sign
                    ix += 1
                    text2=wx.StaticText(self, -1, '+/-')
                    sizer.Add(text2,(iy, ix),(1,1),\
                                    wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
                    text2.Hide() 
                    ## txtcrtl to add error from fit
                    ix += 1
                    ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=wx.TE_PROCESS_ENTER)
                    sizer.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                    ctl2.Hide()
                    if self.data.__class__.__name__ =="Data2D":
                        ctl1.Show(True)
                        ctl1.Enable()
                    else:
                        ctl1.Hide()
                        ctl1.Disable()
                    param_min, param_max= self.model.details[item][1:]
                    ix += 1
                    ctl3 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                                   kill_focus_callback = self._onparamRangeEnter,
                                                   set_focus_callback  = self._onparamRangeEnter)
                    if param_min ==None:
                        ctl3.SetValue("")
                    else:
                        ctl3.SetValue(str(param_min))
                    sizer.Add(ctl3, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                    ctl3.Hide()
                    if self.data.__class__.__name__ =="Data2D":
                        #ctl3.Show(True)
                        ctl3.Enable()
                    else:
                        #ctl3.Hide()
                        ctl3.Disable()
                    ix += 1
                    ctl4 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                                   kill_focus_callback = self._onparamRangeEnter,
                                                   set_focus_callback  = self._onparamRangeEnter)
                    sizer.Add(ctl4, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                    if param_max ==None:
                        ctl4.SetValue("")
                    else:
                        ctl4.SetValue(str(param_max))
                    ctl4.Hide()
                    if self.data.__class__.__name__ =="Data2D":
                        #ctl4.Show(True)
                        ctl4.Enable()
                    else:
                        #ctl4.Hide()
                        ctl4.Disable()
                    if self.engine_type=="park":
                        ctl3.Show(True)
                        ctl4.Show(True)
                    ix +=1
                    # Units
                    try:
                        units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                    except:
                        units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
                    if self.data.__class__.__name__ =="Data2D":
                        units.Show(True)
                        units.Enable()
                    else:
                        units.Hide()
                        units.Disable()
                    sizer.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        
                    
                    ##[cb state, name, value, "+/-", error of fit, min, max , units]
                    self.parameters.append([cb,item, ctl1,
                                            text2,ctl2, ctl3, ctl4,units])
                    self.orientation_params.append([cb,item, ctl1,
                                            text2,ctl2, ctl3, ctl4,units])
              
        iy+=1
        sizer.Add((10,10),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
        #Display units text on panel
        for item in keys:   
            if self.model.details[item][0]!='':
                self.text2_4.Show()
                break
            else:
                self.text2_4.Hide()
                
        self._copy_parameters_state(self.orientation_params,
                                     self.state.orientation_params)
        self._copy_parameters_state(self.orientation_params_disp,
                                     self.state.orientation_params_disp)
        self._copy_parameters_state(self.parameters, self.state.parameters)
        self._copy_parameters_state(self.fittable_param, self.state.fittable_param)
        self._copy_parameters_state(self.fixed_param, self.state.fixed_param)
        
        boxsizer1.Add(sizer)
        self.sizer3.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        self.sizer3.Layout()
        self.Layout()
        self.Refresh()
        self.SetScrollbars(20,20,200,100)
       
            
        
class HelpWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(570, 400))
       
        from sans.models.CylinderModel import CylinderModel
        model = CylinderModel()
       
        from danse.common.plottools.plottables import Data1D
        data= Data1D(x=[1,2], y=[3,4], dy=[0.1, 0,1])
    
        from fitpanel import PageInfo
        myinfo = PageInfo(self,  model, data=data )
        
        ## add data
        
        from models import ModelList
        mylist= ModelList()

        from sans.models.SphereModel import SphereModel
        from sans.models.SquareWellStructure import SquareWellStructure
        from sans.models.DebyeModel import DebyeModel
        from sans.models.LineModel import LineModel
        name= "shapes"
        list1= [SphereModel]
        mylist.set_list( name, list1)
        
        name= "Shape-independent"
        list1= [DebyeModel]
        mylist.set_list( name, list1)
        
        name= "Structure Factors"
        list1= [SquareWellStructure]
        mylist.set_list( name, list1)
        
        name= "Added models"
        list1= [LineModel]
        mylist.set_list( name, list1)
        
        myinfo.model_list_box = mylist.get_list()
        
        self.page = FitPage(self, myinfo) 
        
        
        
        self.Centre()
        self.Show(True)


   
if __name__=="__main__":
    app = wx.App()
    HelpWindow(None, -1, 'HelpWindow')
    app.MainLoop()
                