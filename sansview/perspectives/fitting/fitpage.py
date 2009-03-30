import sys
import wx
import wx.lib.newevent
import numpy
import copy
import math
from sans.models.dispersion_models import ArrayDispersion, GaussianDispersion

from sans.guicomm.events import StatusEvent   
from sans.guiframe.utils import format_number
(ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 80

import basepage
from basepage import BasicPage


class FitPage(BasicPage):
    """
        FitPanel class contains fields allowing to display results when
        fitting  a model and one data
        @note: For Fit to be performed the user should check at least one parameter
        on fit Panel window.
  
    """
    def __init__(self,parent, page_info, name=""):
        BasicPage.__init__(self, parent, page_info,name)
        """ 
            Initialization of the Panel
        """
        self.name= self.data.name
        ## fit page does not content npts txtcrtl
        self.npts=None
        ## if no dispersity parameters is avaible 
        self.text_disp_1=None
        
        self._fill_datainfo_sizer()
        self._fill_model_sizer( self.sizer1)
        self._fill_range_sizer() 
        if hasattr(self.page_info,"model"):
            self.set_model_param_sizer(self.model)
            
        
    def _on_display_description(self, event):
        """
            Show or Hide description
            @param event: wx.EVT_RADIOBUTTON
        """
        self._on_display_description_helper()
        
        
        
    def _on_display_description_helper(self):
        """
            Show or Hide description
            @param event: wx.EVT_RADIOBUTTON
        """
        ## save state of radiobox
        self.page_info. save_radiobox_state( self.description_hide )
        self.page_info. save_radiobox_state( self.description_show )
        ## Show description
        if not self.description_show.GetValue():
            self.sizer_description.Clear(True)
            
        else:
            model=self.page_info.model
            description=""
            if model!=None:
                description = self.page_info.model.description
            self.description = wx.StaticText( self,-1,str(description) )
            self.sizer_description.Add( self.description, 1, wx.EXPAND | wx.ALL, 10 )
           
        self.Layout()
    
    
    def _fill_range_sizer(self):
        """
            Fill the sizer containing the plotting range
            add  access to npts
        """
        sizer_fit = wx.GridSizer(1, 1,0, 0)
    
        self.btFit = wx.Button(self,wx.NewId(),'Fit')
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit,id= self.btFit.GetId())
        self.btFit.SetToolTipString("Perform fit.")
        
        #self.btStopFit = wx.Button(self,wx.NewId(),'Stop Fit')
        #self.btStopFit.Bind(wx.EVT_BUTTON, self.onStopFit,id= self.btStopFit.GetId())
        #self.btStopFit.SetToolTipString("Stop Current fit job.")
        #self.btStopFit.Hide()
        
        sizer_fit.Add((5,5),1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)        
        sizer_fit.Add(self.btFit,0, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5) 
        #sizer_fit.Add(self.btStopFit,1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5) 
        
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
        
        self._set_range_sizer( title="Fitted Q Range",
                               object1=sizer_smearer, object= sizer_fit)
       
       
    def _fill_datainfo_sizer(self):
        """
            fill sizer 0 with data info
        """
        self.sizer0.Clear(True)
        ## no loaded data , don't fill the sizer
        if self.data== None:
            self.sizer0.Layout()
            return
        
        box_description= wx.StaticBox(self, -1, 'Loaded Data')
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        #----------------------------------------------------------
        sizer_data = wx.GridSizer(3, 3,5, 5)
        #Filling the sizer containing data related fields
        DataSource  =wx.StaticText(self, -1,str(self.data.name))

        sizer_data.Add(wx.StaticText(self, -1, 'Data Source Name : '))
        sizer_data.Add(DataSource )
        sizer_data.Add( (5,5) )
        
        #---------sizer 2 draw--------------------------------
        #set maximum range for x in linear scale
        if not hasattr(self.data,"data"): #Display only for 1D data fit
            # Minimum value of data   
            data_min = str(format_number(numpy.min(self.data.x)))
            # Maximum value of data  
            data_max = str(format_number(numpy.max(self.data.x)))
            text4_3 = wx.StaticText(self, -1, 'Maximum Q Range(Linear)',
                                     style=wx.ALIGN_LEFT)
            sizer_data.Add( text4_3 )
            sizer_data.Add(wx.StaticText(self, -1, "Min : %s"%data_min))
            sizer_data.Add(wx.StaticText(self, -1, "Max : %s"%data_max))
            
        else:
            radius_min= 0
            x= numpy.max(self.data.xmin, self.data.xmax)
            y= numpy.max(self.data.ymin, self.data.ymax)
            radius_max = math.sqrt(x*x + y*y)
            # Minimum value of data   
            data_min = str(format_number(radius_min))
            # Maximum value of data  
            data_max = str(format_number(radius_max))
            text4_3 = wx.StaticText(self, -1, 'Maximum Q Range',
                                     style=wx.ALIGN_LEFT)
            sizer_data.Add( text4_3 )
            sizer_data.Add(wx.StaticText(self, -1, "Min : %s"%data_min))
            sizer_data.Add(wx.StaticText(self, -1, "Max : %s"%data_max))
            
        boxsizer1.Add(sizer_data)
        #------------------------------------------------------------
        self.sizer0.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        self.sizer0.Layout()
        
        self.qmin_x= data_min
        self.qmax_x= data_max
        
    def _fill_model_sizer(self, sizer):
        """
            fill sizer containing model info
        """
        sizer_tcChi = wx.GridSizer(2, 2,5, 5)
        self.tcChi    =  wx.StaticText(self, -1, str(0), style=wx.ALIGN_LEFT)
        #self.tcChi.Hide()
        
        self.text1_1 = wx.StaticText(self, -1, 'Chi2/dof', style=wx.ALIGN_LEFT)
        #self.text1_1.Hide()
        
        self.btChi = wx.Button(self,wx.NewId(),'View Chi')
        self.btChi.Bind(wx.EVT_BUTTON, self._onFit,id= self.btChi.GetId())
        self.btChi.SetToolTipString("View data - model.")
        
        sizer_tcChi.Add(self.text1_1,1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        sizer_tcChi.Add(self.btChi,1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)        
        sizer_tcChi.Add(self.tcChi,1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)        
        sizer_tcChi.Add((5,5),1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
            
        ## class base method  to add view 2d button    
        self._set_model_sizer(sizer=sizer, title="Model",object=  sizer_tcChi )    
    
    
    def _set_sizer_gaussian(self):
        """
            draw sizer with gaussian dispersity parameters
        """
        self.fittable_param=[]
        self.fixed_param=[]
        ##reset model dispersity to gaussian
        self._reset_gaussian_dispers()
        
        self.sizer4_4.Clear(True)
       
        if self.model==None:
            ##no model is selected
            return
        if not self.enable_disp.GetValue():
            ## the user didn't select dispersity display
            return 
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
                    ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                        style=wx.TE_PROCESS_ENTER)
                    
                    ctl1.SetValue(str (format_number(value)))
                    ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                    ctl1.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
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
                        Tctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                            style=wx.TE_PROCESS_ENTER)
                        
                        Tctl.SetValue(str (format_number(value)))
                        Tctl.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                        Tctl.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                        self.sizer4_4.Add(Tctl, (iy,ix),(1,1),
                                           wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        
                        self.fixed_param.append([None,name2, Tctl,None,None,
                                                  None, None,None])
                
                elif p=="nsigmas":
                        ix = 5
                        value= self.model.getParam(name3)
                        Tctl = wx.TextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                            style=wx.TE_PROCESS_ENTER)
                        Tctl.SetValue(str (format_number(value)))
                        Tctl.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                        Tctl.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                        self.sizer4_4.Add(Tctl, (iy,ix),(1,1),
                                           wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        ix +=1
                        self.sizer4_4.Add((20,20), (iy,ix),(1,1),
                                           wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        
                        self.fixed_param.append([None,name3, Tctl
                                                 ,None,None, None, None,None])
                
        wx.PostEvent(self.parent, StatusEvent(status=\
                        " Selected Distribution: Gaussian"))   
        ix =0
        iy +=1 
        self.sizer4_4.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)        
        self.sizer4_4.Layout()
        self.sizer4.Layout()
        self.SetScrollbars(20,20,200,100)
     
        
    def _onFit(self, event):     
        """
            Allow to fit
        """
        #self.btFit.SetLabel("Stop")
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
        
        self.qmin_x=float(self.qmin.GetValue())
        self.qmax_x =float( self.qmax.GetValue())
        self.manager._reset_schedule_problem( value=0)
        self.manager.schedule_for_fit( value=1,page=self,fitproblem =None) 
        self.manager.set_fit_range(page= self,qmin= self.qmin_x, qmax= self.qmax_x)
        #single fit 
        #self.manager.on_single_fit(qmin=self.qmin_x,qmax=self.qmax_x)
        self.manager.onFit()
            
        self.sizer5.Layout()
        self.SetScrollbars(20,20,55,40)
        
        
    def _on_select_model(self, event): 
        """
             call back for model selection
        """    
        self._on_select_model_helper(event) 
        self.set_model_param_sizer(self.model)
        self._set_sizer_gaussian()
        
        evt = ModelEventbox(model=self.model)
        wx.PostEvent(self.event_owner, evt)   
        try:
            self.compute_chisqr()
            self.text1_1.Show()
            self.tcChi.Show()
        except:
            ## error occured on chisqr computation
            pass
    def get_range(self):
        """
            return the fitting range
        """
        return self.qmin_x , self.qmax_x
        
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
        if self.text_disp_1 !=None:
            self.text_disp_1.Hide()
        #set the panel when fit result are float not list
        if out.__class__==numpy.float64:
            self.param_toFit[0][2].SetValue(format_number(out))
            self.param_toFit[0][2].Refresh()
            
            self.param_toFit[0][4].Clear()
            self.param_toFit[0][4].Hide()
            if cov !=None :
                self.text2_3.Show(True)
                if self.text_disp_1 !=None:
                    self.text_disp_1.Show(True)
                    
                self.param_toFit[0][3].Show(True)
                self.param_toFit[0][4].Clear()
                self.param_toFit[0][4].SetValue(format_number(cov[0]))
                self.param_toFit[0][4].Show(True)
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
                    if self.text_disp_1!=None:
                        self.text_disp_1.Show(True)
                    item[3].Show(True)
                    item[4].Clear()
                    for j in range(len(out)):
                        if out[j]==self.model.getParam(item[1]):
                            break
                    item[4].SetValue(format_number(cov[j]))
                    item[4].Refresh()
                    item[4].Show(True)   
                i+=1
        
        self.sizer3.Layout()
        self.sizer4.Layout()
        self.SetScrollbars(20,20,200,100)
        
        
      
    def onSmear(self, event):
        """
            Create a smear object that will change the way residuals
            are compute when fitting
        """
        smear =None
        msg=""
        if self.enable_smearer.GetValue():
            from DataLoader.qsmearing import smear_selection
            smear = smear_selection( self.data )
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
            self.manager.set_smearer(smear, qmin= self.qmin_x, qmax= self.qmax_x)   
              
        
        
    def compute_chisqr2D(self):
        """ 
            compute chi square given a model and data 2D and set the value
            to the tcChi txtcrl
        """
        from sans.guiframe.utils import check_value
        flag = check_value( self.qmin, self.qmax)
       
        res=[]
        if flag== True:
            try:
                self.qmin_x = float(self.qmin.GetValue())
                self.qmax_x = float(self.qmax.GetValue())
                for i in range(len(self.data.x_bins)):
                    for j in range(len(self.data.y_bins)):
                        #Check the range containing data between self.qmin_x and self.qmax_x
                        if math.pow(self.data.x_bins[i],2)+math.pow(self.data.y_bins[j],2)>=math.pow(self.qmin_x,2):
                            if math.pow(self.data.x_bins[i],2)+math.pow(self.data.y_bins[j],2)<=math.pow(self.qmax_x,2):
                                chisqrji=(self.data.data[j][i]- self.model.runXY(\
                                                                                    [self.data.x_bins[i],self.data.y_bins[j]]))\
                                                                                    /self.data.err_data[j][i]
                                #Vector containing residuals
                                res.append( math.pow(chisqrji,2) )
                # compute sum of residual
                sum=0
                for item in res:
                    if numpy.isfinite(item):
                        sum +=item
                self.tcChi.SetLabel(format_number(math.fabs(sum/ len(res))))
            except:
                wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Chisqr cannot be compute: %s"% sys.exc_value))
                return
    
        
    def compute_chisqr(self):
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
                    self.qmin_x = float(self.qmin.GetValue())
                    self.qmax_x = float(self.qmax.GetValue())
                    # return residuals within self.qmin_x and self.qmax_x
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
                    #sum of residuals
                    sum=0
                    for item in res:
                        if numpy.isfinite(item):
                            sum +=item
                    self.tcChi.SetLabel(format_number(math.fabs(sum/ len(res))))
            except:
                wx.PostEvent(self.parent.GrandParent, StatusEvent(status=\
                            "Chisqr cannot be compute: %s"% sys.exc_value))
                return 
            
    
    def select_all_param(self,event): 
        """
             set to true or false all checkBox given the main checkbox value cb1
        """
        self.param_toFit=[]
        if  self.parameters !=[]:
            if  self.cb1.GetValue()==True:
                for item in self.parameters:
                    item[0].SetValue(True)
                    self.param_toFit.append(item )
                if len(self.fittable_param)>0:
                    for item in self.fittable_param:
                        item[0].SetValue(True)
                        self.param_toFit.append(item )
            else:
                for item in self.parameters:
                    item[0].SetValue(False)
                for item in self.fittable_param:
                    item[0].SetValue(False)
                self.param_toFit=[]
               
                
                
    def select_param(self,event):
        """ 
            Select TextCtrl  checked for fitting purpose and stores them
            in  self.param_toFit=[] list
        """
        self.param_toFit=[]
        for item in self.parameters:
            #Select parameters to fit for list of primary parameters
            if item[0].GetValue()==True:
                if not (item in self.param_toFit):
                    self.param_toFit.append(item )  
            else:
                #remove parameters from the fitting list
                if item in self.param_toFit:
                    self.param_toFit.remove(item)
        #Select parameters to fit for list of fittable parameters with dispersion          
        for item in self.fittable_param:
            if item[0].GetValue()==True:
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
    
    
    def set_model_description(self,description,sizer):
        """
            fill a sizer with description
            @param description: of type string
            @param sizer: wx.BoxSizer()
        """
    
        sizer.Clear(True)
        box_description= wx.StaticBox(self, -1, 'Model Description')
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
                
        self.description = wx.StaticText( self,-1,str(description) )
        sizer_selection=wx.BoxSizer(wx.HORIZONTAL)
        
        
        self.description_show = wx.RadioButton(self, -1, 'Show', style=wx.RB_GROUP)
        self.description_hide = wx.RadioButton(self, -1, 'Hide')
        
        self.Bind( wx.EVT_RADIOBUTTON, self._on_display_description,
                   id=self.description_hide.GetId() )
        
        self.Bind( wx.EVT_RADIOBUTTON, self._on_display_description,
                   id=self.description_show.GetId() )
        
        self.model_description = wx.Button(self, -1, "More Details")
     
        
        self.page_info.save_radiobox_state( self.description_hide )
        self.page_info.save_radiobox_state( self.description_show )
        
        sizer_selection.Add( self.description_show )
        sizer_selection.Add( (20,20)) 
        sizer_selection.Add( self.description_hide )
        sizer_selection.Add( (20,20)) 
        sizer_selection.Add( self.model_description )
        
         
        self.sizer_description=wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_description.Add( self.description, 1, wx.EXPAND | wx.ALL, 10 )
       
        boxsizer1.Add( sizer_selection) 
        boxsizer1.Add( (20,20)) 
        boxsizer1.Add( self.sizer_description) 
    

        sizer.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        sizer.Layout()
   
   
        
        
    def set_model_param_sizer(self, model, engine_type="park"):
        """
            Build the panel from the model content
            @param model: the model selected in combo box for fitting purpose
        """
        self.sizer3.Clear(True)
        self.parameters = []
        self.param_toFit=[]
        self.fittable_param=[]
        self.fixed_param=[]
        
        if model ==None:
            self.sizer3.Layout()
            self.SetScrollbars(20,20,200,100)
            return
        box_description= wx.StaticBox(self, -1,str("Model Parameters"))
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer = wx.GridBagSizer(5,5)
        ## save the current model
        self.model = model
           
        keys = self.model.getParamList()
        #list of dispersion paramaters
        self.disp_list=self.model.getDispParamList()
       
        keys.sort()
    
        iy = 1
        ix = 0
        self.cb1 = wx.CheckBox(self, -1,"Select all", (10, 10))
        wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.select_all_param)
        self.cb1.SetValue(False)
        
        sizer.Add(self.cb1,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
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
        self.text2_4 = wx.StaticText(self, -1, 'Units')
        sizer.Add(self.text2_4,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_4.Hide()
        if  engine_type == "park":
            self.text2_max.Show(True)
            self.text2_min.Show(True)

        for item in keys:
            if not item in self.disp_list:
                iy += 1
                ix = 0
                ## add parameters name with checkbox for selecting to fit
                cb = wx.CheckBox(self, -1, item )
                cb.SetValue(False)
                wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                sizer.Add( cb,( iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                ## add parameter value
                ix += 1
                value= self.model.getParam(item)
                ctl1 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                    style=wx.TE_PROCESS_ENTER)
                
                ctl1.SetValue(str (format_number(value)))
                ctl1.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                ctl1.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
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
                
                ix += 1
                ctl3 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER)
                ctl3.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                ctl3.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                sizer.Add(ctl3, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ctl3.Hide()
                
                ix += 1
                ctl4 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER)
                ctl4.Bind(wx.EVT_KILL_FOCUS, self._onparamEnter)
                ctl4.Bind(wx.EVT_TEXT_ENTER,self._onparamEnter)
                sizer.Add(ctl4, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ctl4.Hide()
                if  engine_type == "park":
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
                                        text2,ctl2, ctl3, ctl4,None])
                
        iy+=1
        sizer.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
        #Display units text on panel
        for item in keys:   
            if self.model.details[item][0]!='':
                self.text2_4.Show()
                break
            else:
                self.text2_4.Hide()
    
        boxsizer1.Add(sizer)
        
        self.sizer3.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        self.sizer3.Layout()
        self.SetScrollbars(20,20,200,100)
        
    
            
        
class HelpWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(570, 400))
       
        from sans.models.CylinderModel import CylinderModel
        model = CylinderModel()
        #from sans.models.LineModel import LineModel
        #model = LineModel()
        from danse.common.plottools.plottables import Data1D
        data= Data1D(x=[1,2], y=[3,4], dy=[0.1, 0,1])
    
        from pageInfo import PageInfo
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
                