

import sys
import wx
import wx.lib.newevent
import numpy
import copy
import math
import time
from sans.models.dispersion_models import ArrayDispersion, GaussianDispersion
from DataLoader.data_info import Data1D
from sans.guicomm.events import StatusEvent   
from sans.guiframe.utils import format_number,check_float
#from sans.guiframe.local_perspectives.plotting.Masking import ModelPanel2D as panel2D

## event to post model to fit to fitting plugins
(ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()

## event to know the selected fit engine
(FitterTypeEvent, EVT_FITTER_TYPE)   = wx.lib.newevent.NewEvent()
(FitStopEvent, EVT_FIT_STOP)   = wx.lib.newevent.NewEvent()
(Chi2UpdateEvent, EVT_CHI2_UPDATE)   = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 76
_DATA_BOX_WIDTH = 300
SMEAR_SIZE_L = 0.005
SMEAR_SIZE_H = 0.01

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
        ## total number of point: float
        self.npts=None
        ## thread for compute Chisqr
        self.calc_Chisqr=None
        ## default fitengine type
        self.engine_type = None
        ## smear default
        self.smearer = None
        self.current_smearer = None
        ## 2D smear accuracy default
        self.smear2d_accuracy = 'Low'
        ## slit smear: 
        self.dxl = None
        self.dxw = None
        ## pinhole smear 
        self.dx_min = None
        self.dx_max = None
        
        ## model data (theory) calculated on drawing.
        self.theory_data = None
      
        ## draw sizer
        self._fill_datainfo_sizer()
        
        # get smear info from data
        self._get_smear_info()
        
        self._fill_model_sizer( self.sizer1)
        
        self._get_defult_custom_smear()
        
        self._fill_range_sizer() 
        
        if self.data is None:
            self.formfactorbox.Disable()
            self.structurebox.Disable()
        else:
            self.smearer = smear_selection( self.data )
            if self.smearer ==None:
                self.enable_smearer.Disable()
            #if self.data.__class__.__name__ =="Data2D":
                #if self.model != None:
                    #self.smear_description_2d.Show(True)
                    
        self.disp_cb_dict = {}
        ## to update the panel according to the fit engine type selected
        self.Bind(EVT_FITTER_TYPE,self._on_engine_change)
        self.Bind(EVT_FIT_STOP,self._on_fit_complete)
        self.Bind(EVT_CHI2_UPDATE, self.on_complete_chisqr)

    def _on_fit_complete(self, event):
        """
            When fit is complete ,reset the fit button label.
        """
        #self.btFit.SetLabel("Fit")
        #self.btFit.Unbind(event=wx.EVT_BUTTON, id=self.btFit.GetId())
        #self.btFit.Bind(event=wx.EVT_BUTTON, handler=self._onFit,id=self.btFit.GetId())
        pass
        
    def _is_2D(self):
        """
            Check if data_name is Data2D
            @return: True or False
        """
        
        if self.data.__class__.__name__ =="Data2D":
            return True
        return False
            
    def _on_engine_change(self, event):
        """
            get an event containing the current name of the fit engine type
            @param event: FitterTypeEvent containing  the name of the current engine
        """
        self.engine_type = event.type
        if len(self.parameters)==0:
            self.Layout()
            return
        if event.type =="park":
            self.btFit.SetLabel("Fit")

        for item in self.parameters:
            if event.type =="scipy" :
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
        for item in self.fittable_param:
            if item[5]!=None and item[6]!=None and not item in self.orientation_params_disp:
                if event.type =="scipy" and not item in self.orientation_params:
                    item[5].SetValue("")
                    item[5].Hide()
                    item[6].SetValue("")
                    item[6].Hide()
                    self.text2_min.Hide()
                    self.text2_max.Hide()
                    self.text_disp_min.Hide()
                    self.text_disp_max.Hide()
                else:
                    item[5].Show(True)
                    item[6].Show(True)
                    self.text2_min.Show(True)
                    self.text2_max.Show(True)
                    self.text_disp_min.Show(True)
                    self.text_disp_max.Show(True)
            
        for item in self.orientation_params:
            if item[5]!=None and item[6]!=None:
                if event.type =="scipy" or self.data.__class__.__name__ !="Data2D":
                    item[5].SetValue("")
                    item[5].Hide()
                    item[6].SetValue("")
                    item[6].Hide()
                else:
                    item[5].Show(True)
                    item[6].Show(True)
                    
        for item in self.orientation_params_disp:         
            if item[5]!=None and item[6]!=None:
                if event.type =="scipy" or self.data.__class__.__name__ !="Data2D":
                    item[5].SetValue("")
                    item[5].Hide()
                    item[6].SetValue("")
                    item[6].Hide()
                else:
                    item[5].Show(True)
                    item[6].Show(True)
        self.Layout()
        self.Refresh()

    def _fill_range_sizer(self):
        """
            Fill the sizer containing the plotting range
            add  access to npts
        """
        is_2Ddata = False
        
        # Check if data is 2D
        if self.data.__class__.__name__ == 'Data2D':
            is_2Ddata = True
            
        title = "Fitting"
        #smear messages & titles
        smear_message_none  =  "No smearing is selected..."
        smear_message_dqdata  =  "The dQ data is being used for smearing..."
        smear_message_2d  =  "Higher accuracy is very time-expensive. Use it with care..."
        smear_message_new_ssmear  =  "Please enter only the value of interest to customize smearing..."
        smear_message_new_psmear  =  "Please enter both; the dQ will be generated by interpolation..."
        smear_message_2d_x_title = "<dQx>[1/A]:"
        smear_message_2d_y_title = "<dQy>[1/A]:"
        smear_message_pinhole_min_title = "dQ_low[1/A]:"
        smear_message_pinhole_max_title = "dQ_high[1/A]:"
        smear_message_slit_height_title = "Slit height[1/A]:"
        smear_message_slit_width_title = "Slit width[1/A]:"
        
        self._get_smear_info()
        
        #Sizers
        box_description_range = wx.StaticBox(self, -1,str(title))
        boxsizer_range = wx.StaticBoxSizer(box_description_range, wx.VERTICAL)      
        self.sizer_set_smearer = wx.BoxSizer(wx.VERTICAL)
        sizer_smearer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_new_smear= wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_set_masking = wx.BoxSizer(wx.HORIZONTAL)
        sizer_chi2 = wx.BoxSizer(wx.VERTICAL)
        smear_set_box= wx.StaticBox(self, -1,'Set Instrumental Smearing')
        sizer_smearer_box = wx.StaticBoxSizer(smear_set_box, wx.HORIZONTAL)
        sizer_smearer_box.SetMinSize((_DATA_BOX_WIDTH,85))
        sizer_fit = wx.GridSizer(2, 4,2,6)
        
        # combobox for smear2d accuracy selection
        self.smear_accuracy = wx.ComboBox(self, -1,size=(50,-1),style=wx.CB_READONLY)
        self._set_accuracy_list()
        self.smear_accuracy.SetValue(self.smear2d_accuracy)
        self.smear_accuracy.SetSelection(0)
        self.smear_accuracy.SetToolTipString("'Higher' uses more Gaussian points for smearing computation.")
                   
        
             
        wx.EVT_COMBOBOX(self.smear_accuracy,-1, self._on_select_accuracy)

        #Fit button
        self.btFit = wx.Button(self,wx.NewId(),'Fit', size=(88,25))
        self.btFit.Bind(wx.EVT_BUTTON, self._onFit,id= self.btFit.GetId())
        self.btFit.SetToolTipString("Start fitting.")
        
        #textcntrl for custom resolution
        self.smear_pinhole_max = self.ModelTextCtrl(self, -1,size=(_BOX_WIDTH-25,20),style=wx.TE_PROCESS_ENTER,
                                            text_enter_callback = self.onPinholeSmear)
        self.smear_pinhole_min = self.ModelTextCtrl(self, -1,size=(_BOX_WIDTH-25,20),style=wx.TE_PROCESS_ENTER,
                                            text_enter_callback = self.onPinholeSmear)
        self.smear_slit_height= self.ModelTextCtrl(self, -1,size=(_BOX_WIDTH-25,20),style=wx.TE_PROCESS_ENTER,
                                            text_enter_callback = self.onSlitSmear)
        self.smear_slit_width = self.ModelTextCtrl(self, -1,size=(_BOX_WIDTH-25,20),style=wx.TE_PROCESS_ENTER,
                                            text_enter_callback = self.onSlitSmear)

        ## smear
        self.smear_data_left= BGTextCtrl(self, -1, size=(_BOX_WIDTH-25,20), style=0)
        self.smear_data_left.SetValue(str(self.dq_l))
        self.smear_data_right = BGTextCtrl(self, -1, size=(_BOX_WIDTH-25,20), style=0)
        self.smear_data_right.SetValue(str(self.dq_r))

        #set default values for smear
        self.smear_pinhole_max.SetValue(str(self.dx_max))
        self.smear_pinhole_min.SetValue(str(self.dx_min))
        self.smear_slit_height.SetValue(str(self.dxl))
        self.smear_slit_width.SetValue(str(self.dxw))

        #Filling the sizer containing instruments smearing info.
        self.disable_smearer = wx.RadioButton(self, -1, 'None', style=wx.RB_GROUP)
        self.enable_smearer = wx.RadioButton(self, -1, 'Use dQ Data')
        #self.enable_smearer.SetToolTipString("Click to use the loaded dQ data for smearing.")
        self.pinhole_smearer = wx.RadioButton(self, -1, 'Custom Pinhole Smear')
        #self.pinhole_smearer.SetToolTipString("Click to input custom resolution for pinhole smearing.")
        self.slit_smearer = wx.RadioButton(self, -1, 'Custom Slit Smear')
        #self.slit_smearer.SetToolTipString("Click to input custom resolution for slit smearing.")
        self.Bind(wx.EVT_RADIOBUTTON, self.onSmear, id=self.disable_smearer.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSmear, id=self.enable_smearer.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onPinholeSmear, id=self.pinhole_smearer.GetId())
        self.Bind(wx.EVT_RADIOBUTTON, self.onSlitSmear, id=self.slit_smearer.GetId())
        self.disable_smearer.SetValue(True)
        
        # add 4 types of smearing to the sizer
        sizer_smearer.Add( self.disable_smearer,0, wx.LEFT, 10)
        sizer_smearer.Add((10,10))
        sizer_smearer.Add( self.enable_smearer)
        sizer_smearer.Add((10,10))
        sizer_smearer.Add( self.pinhole_smearer ) 
        sizer_smearer.Add((10,10))
        sizer_smearer.Add( self.slit_smearer ) 
        sizer_smearer.Add((10,10))       
        
        # StaticText for chi2, N(for fitting), Npts
        self.tcChi    =  BGTextCtrl(self, -1, "-", size=(75,20), style=0)
        self.tcChi.SetToolTipString("Chi2/Npts")
        self.Npts_fit    =  BGTextCtrl(self, -1, "-", size=(75,20), style=0)
        self.Npts_fit.SetToolTipString(" Npts : number of points selected for fitting")
        self.Npts_total  =  BGTextCtrl(self, -1, "-", size=(75,20), style=0)
        self.Npts_total.SetToolTipString(" Total Npts : total number of data points")
        box_description_1= wx.StaticText(self, -1,'    Chi2/Npts')
        box_description_2= wx.StaticText(self, -1,'  Npts')
        box_description_3= wx.StaticText(self, -1,'  Total Npts')
        box_description_4= wx.StaticText(self, -1,' ')
        
        
        sizer_fit.Add(box_description_1,0,0)
        sizer_fit.Add(box_description_2,0,0)
        sizer_fit.Add(box_description_3,0,0)       
        sizer_fit.Add(box_description_4,0,0)
        sizer_fit.Add(self.tcChi,0,0)
        sizer_fit.Add(self.Npts_fit ,0,0)
        sizer_fit.Add(self.Npts_total,0,0)
        sizer_fit.Add(self.btFit,0,0) 

        # StaticText for smear
        #self.tcChi    =  wx.StaticText(self, -1, "-", style=wx.ALIGN_LEFT)
        self.smear_description_none    =  wx.StaticText(self, -1, smear_message_none , style=wx.ALIGN_LEFT)
        self.smear_description_dqdata    =  wx.StaticText(self, -1, smear_message_dqdata , style=wx.ALIGN_LEFT)
        self.smear_description_type    =  wx.StaticText(self, -1, "Type:" , style=wx.ALIGN_LEFT)
        self.smear_description_accuracy_type    =  wx.StaticText(self, -1, "Accuracy:" , style=wx.ALIGN_LEFT)
        self.smear_description_smear_type    =  BGTextCtrl(self, -1, size=(57,20), style=0)
        self.smear_description_smear_type.SetValue(str(self.dq_l))
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())
        self.smear_description_2d     =  wx.StaticText(self, -1, smear_message_2d  , style=wx.ALIGN_LEFT)
        self.smear_message_new_s = wx.StaticText(self, -1, smear_message_new_ssmear  , style=wx.ALIGN_LEFT)
        self.smear_message_new_p = wx.StaticText(self, -1, smear_message_new_psmear  , style=wx.ALIGN_LEFT)
        self.smear_description_2d_x     =  wx.StaticText(self, -1, smear_message_2d_x_title  , style=wx.ALIGN_LEFT)
        self.smear_description_2d_y     =  wx.StaticText(self, -1, smear_message_2d_y_title  , style=wx.ALIGN_LEFT)
        self.smear_description_pin_min     =  wx.StaticText(self, -1, smear_message_pinhole_min_title  , style=wx.ALIGN_LEFT)
        self.smear_description_pin_max     =  wx.StaticText(self, -1, smear_message_pinhole_max_title  , style=wx.ALIGN_LEFT)
        self.smear_description_slit_height    =  wx.StaticText(self, -1, smear_message_slit_height_title   , style=wx.ALIGN_LEFT)
        self.smear_description_slit_width    =  wx.StaticText(self, -1, smear_message_slit_width_title   , style=wx.ALIGN_LEFT)
        
        #arrange sizers 
        #boxsizer1.Add( self.tcChi )  
        self.sizer_set_smearer.Add(sizer_smearer )
        self.sizer_set_smearer.Add((10,10))
        self.sizer_set_smearer.Add( self.smear_description_none,0, wx.CENTER, 10 ) 
        self.sizer_set_smearer.Add( self.smear_description_dqdata,0, wx.CENTER, 10 )
        self.sizer_set_smearer.Add( self.smear_description_2d,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_description_type,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_description_accuracy_type,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_accuracy )
        self.sizer_new_smear.Add( self.smear_description_smear_type,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add((15,-1))
        self.sizer_new_smear.Add( self.smear_description_2d_x,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_description_pin_min,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_description_slit_height,0, wx.CENTER, 10 )

        self.sizer_new_smear.Add( self.smear_pinhole_min,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_slit_height,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_data_left,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add((20,-1))
        self.sizer_new_smear.Add( self.smear_description_2d_y,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_description_pin_max,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_description_slit_width,0, wx.CENTER, 10 )

        self.sizer_new_smear.Add( self.smear_pinhole_max,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_slit_width,0, wx.CENTER, 10 )
        self.sizer_new_smear.Add( self.smear_data_right,0, wx.CENTER, 10 )
           
        self.sizer_set_smearer.Add( self.smear_message_new_s,0, wx.CENTER, 10)
        self.sizer_set_smearer.Add( self.smear_message_new_p,0, wx.CENTER, 10)
        self.sizer_set_smearer.Add((5,2))
        self.sizer_set_smearer.Add( self.sizer_new_smear,0, wx.CENTER, 10 )
        
        # add all to chi2 sizer 
        sizer_smearer_box.Add(self.sizer_set_smearer)       
        sizer_chi2.Add(sizer_smearer_box)
        sizer_chi2.Add((-1,5))

        # hide all smear messages and textctrl
        self._hide_all_smear_info()
        
        # get smear_selection
        self.current_smearer= smear_selection( self.data )

        # Show only the relevant smear messages, etc
        if self.current_smearer == None:
            if not is_2Ddata:
                self.smear_description_none.Show(True)
                self.enable_smearer.Disable()  
            else:
                self.smear_description_none.Show(True)
                #self.smear_description_2d.Show(True) 
                #self.pinhole_smearer.Disable() 
                self.slit_smearer.Disable()   
                #self.enable_smearer.Disable() 
        else: self._show_smear_sizer()
        boxsizer_range.Add(self.sizer_set_masking)
            
        #Set sizer for Fitting section
        self._set_range_sizer( title=title,box_sizer=boxsizer_range, object1=sizer_chi2, object= sizer_fit)
        
    def _fill_datainfo_sizer(self):
        """
            fill sizer 0 with data info
        """
        ## no loaded data , don't fill the sizer
        if self.data is None:
            data_min = ""
            data_max = ""
            data_name = ""
        else:
            data_name = self.data.name
            #set maximum range for x in linear scale
            if not hasattr(self.data,"data"): #Display only for 1D data fit
                # Minimum value of data   
                data_min = min(self.data.x)
                # Maximum value of data  
                data_max = max(self.data.x)
            else:
                ## Minimum value of data 
                data_min = 0
                x = max(math.fabs(self.data.xmin), math.fabs(self.data.xmax)) 
                y = max(math.fabs(self.data.ymin), math.fabs(self.data.ymax))
                ## Maximum value of data  
                data_max = math.sqrt(x*x + y*y)
        
        box_description= wx.StaticBox(self, -1, 'Data')
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        #----------------------------------------------------------
        sizer_data = wx.BoxSizer(wx.HORIZONTAL)
        #Filling the sizer containing data related fields
        #self.dataSource = wx.StaticText(self, -1,str(self.data.name))
        self.dataSource = BGTextCtrl(self, -1)
        self.dataSource.SetValue(str(data_name))
        #self.dataSource.SetEditable(False)
        self.dataSource.SetMinSize((_DATA_BOX_WIDTH, -1))
        sizer_data.Add(wx.StaticText(self, -1, 'Source Name : '))
        sizer_data.Add(self.dataSource )
        sizer_data.Add( (0,5) )
        
        #---------sizer 2 draw--------------------------------
        text4_3 = wx.StaticText(self, -1, 'Total Q Range (1/A)',
                                 style=wx.ALIGN_LEFT)
        sizer_range = wx.BoxSizer(wx.HORIZONTAL)
        sizer_range.Add( text4_3 ,0, wx.RIGHT, 10)
        self.minimum_q = BGTextCtrl(self, -1, size=(_BOX_WIDTH,20))
        self.minimum_q.SetValue(str(data_min))
        #self.minimum_q.SetEditable(False)
        self.maximum_q = BGTextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.maximum_q.SetValue(str(data_max))
        #self.maximum_q.SetEditable(False)
        sizer_range.Add(wx.StaticText(self, -1, "Min: "),0, wx.LEFT, 10)
        sizer_range.Add(self.minimum_q,0, wx.LEFT, 10)
        sizer_range.Add(wx.StaticText(self, -1, "Max: "),0, wx.LEFT, 10)
        sizer_range.Add(self.maximum_q,0, wx.LEFT, 10)

        ## set q range to plot
        self.qmin_x = data_min
        self.qmax_x = data_max

        boxsizer1.Add(sizer_data,0, wx.ALL, 10)
        boxsizer1.Add(sizer_range, 0 , wx.LEFT, 10)
        #------------------------------------------------------------
        self.sizer0.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        self.sizer0.Layout()
       
    def _fill_model_sizer(self, sizer):
        """
            fill sizer containing model info
        """
        ##Add model function Details button in fitpanel.
        ##The following 3 lines are for Mac. Let JHC know before modifying... 
        title = "Model"
        box_description= wx.StaticBox(self, -1,str(title))
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
         
        id = wx.NewId()
        self.model_help =wx.Button(self,id,'Details', size=(80,23))
        self.model_help.Bind(wx.EVT_BUTTON, self.on_model_help_clicked,id=id)
        self.model_help.SetToolTipString("Model Function Help")
        
        ## class base method  to add view 2d button    
        self._set_model_sizer(sizer=sizer, box_sizer=boxsizer1, title="Model",object=self.model_help )   

    
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
        disp = wx.StaticText(self, -1, ' ')
        self.sizer4_4.Add(disp,( iy, ix),(1,1), 
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1 
        values = wx.StaticText(self, -1, 'Sigma (STD)')
        values.SetToolTipString("Polydispersity multiplied by the value of the original parameter.")
        self.sizer4_4.Add(values,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix +=2 
        self.text_disp_1 = wx.StaticText(self, -1, '')
        self.sizer4_4.Add( self.text_disp_1,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text_disp_1.Hide()
        
        
        ix +=1 
        self.text_disp_min = wx.StaticText(self, -1, 'Min')
        self.sizer4_4.Add(self.text_disp_min,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text_disp_min.Hide()
        ix +=1 
        self.text_disp_max = wx.StaticText(self, -1, 'Max')
        self.sizer4_4.Add(self.text_disp_max,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text_disp_max.Hide()
                        
        
        ix += 1 
        npts = wx.StaticText(self, -1, 'Npts')
        npts.SetToolTipString("Number of points for weighting.")
        self.sizer4_4.Add(npts,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        ix += 1 
        nsigmas = wx.StaticText(self, -1, 'Nsigmas')
        nsigmas.SetToolTipString("Number of sigmas between which the range of the distribution function will be used for weighting. The value '3' covers 99.5% for Gaussian distribution function.")
        self.sizer4_4.Add(nsigmas,( iy, ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        
        if self.engine_type=="park":
            self.text_disp_max.Show(True)
            self.text_disp_min.Show(True)

        for item in self.model.dispersion.keys():
            if not item in self.model.orientation_params:
                if not self.disp_cb_dict.has_key(item):
                    self.disp_cb_dict[item]= None
                name1=item+".width"
                name2=item+".npts"
                name3=item+".nsigmas"
                if not self.model.details.has_key(name1):
                    self.model.details [name1] = ["",None,None] 

                iy += 1
                for p in self.model.dispersion[item].keys(): 
        
                    if p=="width":
                        ix = 0
                        cb = wx.CheckBox(self, -1, name1, (10, 10))
                        cb.SetToolTipString("Check for fitting")
                        wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                        self.sizer4_4.Add( cb,( iy, ix),(1,1),  
                                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                        ix = 1
                        value= self.model.getParam(name1)
                        ctl1 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                            style=wx.TE_PROCESS_ENTER)
                        ctl1.SetToolTipString("Polydispersity multiplied by the value of '%s'."%item)
                        ctl1.SetValue(str (format_number(value)))
                        self.sizer4_4.Add(ctl1, (iy,ix),(1,1),wx.EXPAND)
                        ## text to show error sign
                        ix = 2
                        text2=wx.StaticText(self, -1, '+/-')
                        self.sizer4_4.Add(text2,(iy, ix),(1,1),
                                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        text2.Hide() 

                        ix = 3
                        ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=0)
                  
                        self.sizer4_4.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                     
                        ctl2.Hide()

                        ix = 4
                        ctl3 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                                       text_enter_callback = self._onparamRangeEnter)
                        
                        self.sizer4_4.Add(ctl3, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        ctl3.Hide()
                
                        ix = 5
                        ctl4 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                                       text_enter_callback = self._onparamRangeEnter)
                        
                        self.sizer4_4.Add(ctl4, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)

                        ctl4.Hide()
                        
                        if self.engine_type=="park":
                            ctl3.Show(True)
                            ctl4.Show(True)
                                          
                        self.fittable_param.append([cb,name1,ctl1,text2,
                                                    ctl2, ctl3, ctl4,None])                    
                    
                    elif p=="npts":
                            ix = 6
                            value= self.model.getParam(name2)
                            Tctl = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            
                            Tctl.SetValue(str (format_number(value)))
                            self.sizer4_4.Add(Tctl, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name2, Tctl,None,None,
                                                      None, None,None])
                    elif p=="nsigmas":
                            ix = 7
                            value= self.model.getParam(name3)
                            Tct2 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            
                            Tct2.SetValue(str (format_number(value)))
                            self.sizer4_4.Add(Tct2, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            ix +=1
                            self.sizer4_4.Add((20,20), (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            
                            self.fixed_param.append([None,name3, Tct2
                                                     ,None,None,None, None,None])
                            
        ix =0
        iy +=1 
        self.sizer4_4.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)  
        for item in self.model.dispersion.keys():
            if  item in self.model.orientation_params:
                if not self.disp_cb_dict.has_key(item):
                    self.disp_cb_dict[item]= None
                name1=item+".width"
                name2=item+".npts"
                name3=item+".nsigmas"
                if not self.model.details.has_key(name1):
                    self.model.details [name1] = ["",None,None]                  
 

                iy += 1
                for p in self.model.dispersion[item].keys(): 
        
                    if p=="width":
                        ix = 0
                        cb = wx.CheckBox(self, -1, name1, (10, 10))
                        cb.SetToolTipString("Check for fitting")
                        wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                        self.sizer4_4.Add( cb,( iy, ix),(1,1),  
                                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                        if self.data.__class__.__name__ =="Data2D":
                            cb.Show(True)
                        elif cb.IsShown():
                            cb.Hide()
                        ix = 1
                        value= self.model.getParam(name1)
                        ctl1 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                            style=wx.TE_PROCESS_ENTER)
                        ctl1.SetToolTipString("Polydispersity multiplied by the value of '%s'."%item)
                        ctl1.SetValue(str (format_number(value)))
                        if self.data.__class__.__name__ =="Data2D":
                            ctl1.Show(True)
                        elif ctl1.IsShown():
                            ctl1.Hide()
                        self.sizer4_4.Add(ctl1, (iy,ix),(1,1),wx.EXPAND)
                        ## text to show error sign
                        ix = 2
                        text2=wx.StaticText(self, -1, '+/-')
                        self.sizer4_4.Add(text2,(iy, ix),(1,1),
                                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        text2.Hide() 

                        ix = 3
                        ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=0)
                    
                        self.sizer4_4.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        ctl2.Hide()
                            
                        ix = 4
                        ctl3 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                                       text_enter_callback = self._onparamRangeEnter)

                        self.sizer4_4.Add(ctl3, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)

                        ctl3.Hide()
                
                        ix = 5
                        ctl4 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                                       text_enter_callback = self._onparamRangeEnter)
                        self.sizer4_4.Add(ctl4, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                        ctl4.Hide()
                        #if self.data.__class__.__name__ =="Data2D":
                            #ctl4.Enable(True)
                        #elif ctl4.Shown():
                            #ctl4.Hide()
                        
                        if self.engine_type=="park" and self.data.__class__.__name__ =="Data2D":
                            ctl3.Show(True)
                            ctl4.Show(True) 
                            
                            
                            
                            
                        self.fittable_param.append([cb,name1,ctl1,text2,
                                                    ctl2, ctl3, ctl4,None])
                        self.orientation_params_disp.append([cb,name1,ctl1,text2,
                                                    ctl2, ctl3, ctl4,None])
                    elif p=="npts":
                            ix = 6
                            value= self.model.getParam(name2)
                            Tctl = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            
                            Tctl.SetValue(str (format_number(value)))
                            if self.data.__class__.__name__ =="Data2D":
                                Tctl.Show(True)
                            else:
                                Tctl.Hide()
                            self.sizer4_4.Add(Tctl, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name2, Tctl,None,None,
                                                      None, None,None])
                            self.orientation_params_disp.append([None,name2, Tctl,None,None,
                                                      None, None,None])
                    elif p=="nsigmas":
                            ix = 7
                            value= self.model.getParam(name3)
                            Tct2 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            
                            Tct2.SetValue(str (format_number(value)))
                            if self.data.__class__.__name__ =="Data2D":
                                Tct2.Show(True)
                            else:
                                Tct2.Hide()
                            self.sizer4_4.Add(Tct2, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            ix +=1

                            self.fixed_param.append([None,name3, Tct2
                                                     ,None,None, None, None,None])    
                                                       
                            self.orientation_params_disp.append([None,name3, Tct2
                                                     ,None,None, None, None,None])
       

        self.state.disp_cb_dict = copy.deepcopy(self.disp_cb_dict)  
          
        self.state.model = self.model.clone()  
         ## save state into
        self.state.cb1 = self.cb1.GetValue()
        self._copy_parameters_state(self.parameters, self.state.parameters)
        self._copy_parameters_state(self.orientation_params_disp,
                                     self.state.orientation_params_disp)
        self._copy_parameters_state(self.fittable_param, self.state.fittable_param)
        self._copy_parameters_state(self.fixed_param, self.state.fixed_param)


        wx.PostEvent(self.parent, StatusEvent(status=\
                        " Selected Distribution: Gaussian"))   
        #Fill the list of fittable parameters
        self.select_all_param(event=None)
        
        self.Layout()


    def _onFit(self, event):     
        """
            Allow to fit
        """
        #make sure all parameter values are updated.
        if self.check_invalid_panel():
            return
        flag = self._update_paramv_on_fit() 
                
        if not flag:
            msg= "Fitting range or parameters are invalid"
            wx.PostEvent(self.parent.parent, StatusEvent(status= msg ))
            return 
        
        if len(self.param_toFit) <= 0:
            msg= "Select at least one parameter to fit"
            wx.PostEvent(self.parent.parent, StatusEvent(status= msg ))
            return 
      

        self.select_param(event =None)
        
        #Clear errors if exist from previous fitting
        #self._clear_Err_on_Fit() 

        # Remove or do not allow fitting on the Q=0 point, especially when y(q=0)=None at x[0].         
        self.qmin_x = float(self.qmin.GetValue())
        self.qmax_x = float( self.qmax.GetValue())
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
           

        
    def _StopFit(self, event):
        """
            Stop fit 
        """
        self.btFit.SetLabel("Fit")
        if self.engine_type=="scipy":
            self.manager.stop_fit()
        self.btFit.Unbind(event=wx.EVT_BUTTON, id=self.btFit.GetId())
        self.btFit.Bind(event=wx.EVT_BUTTON, handler=self._onFit,id=self.btFit.GetId())
        
            
    def _on_select_model(self, event): 
        """
             call back for model selection
        """  
        self._on_select_model_helper() 
        self.set_model_param_sizer(self.model)                   
        
        self.enable_disp.SetValue(False)
        self.disable_disp.SetValue(True)
        try:
            self.set_dispers_sizer()
        except:
            pass
        self.btFit.SetFocus() 
        self.state.enable_disp = self.enable_disp.GetValue()
        self.state.disable_disp = self.disable_disp.GetValue()
        self.state.pinhole_smearer = self.pinhole_smearer.GetValue()
        self.state.slit_smearer = self.slit_smearer.GetValue()
    
        self.state.structurecombobox = self.structurebox.GetCurrentSelection()
        self.state.formfactorcombobox = self.formfactorbox.GetCurrentSelection()
      
        if self.model != None:
            try:
                temp_smear= None
                if self.enable_smearer.GetValue():
                    temp_smear= self.smearer
                #self.compute_chisqr(temp_smear)
            except:
                ## error occured on chisqr computation
                pass
            if self.data is not None and self.data.__class__.__name__ !="Data2D":
                ## set smearing value whether or not the data contain the smearing info
                evt = ModelEventbox(model=self.model, 
                                        smearer=temp_smear, 
                                        qmin= float(self.qmin_x),
                                     qmax= float(self.qmax_x)) 
            else:   
                 evt = ModelEventbox(model=self.model)
            wx.PostEvent(self.event_owner, evt)  
            
        if event !=None:
            #self._undo.Enable(True)
            ## post state to fit panel
            event = PageInfoEvent(page = self)
            wx.PostEvent(self.parent, event) 
     
                
    def _onparamEnter(self,event):
        """ 
            when enter value on panel redraw model according to changed
        """
        #default flag
        flag = False
        self.fitrange = True
        #get event object
        tcrtl= event.GetEventObject()

        #Clear msg if previously shown.
        msg= ""
        wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))

        if check_float(tcrtl):
            flag = self._onparamEnter_helper() 
            self.set_npts2fit() 
            if self.fitrange:             
                temp_smearer = None
                if not self.disable_smearer.GetValue():
                    temp_smearer= self.current_smearer
                    ## set smearing value whether or not the data contain the smearing info
                    if self.slit_smearer.GetValue():
                        flag1 = self.update_slit_smear()
                        flag = flag or flag1
                    elif self.pinhole_smearer.GetValue():
                        flag1 = self.update_pinhole_smear()
                        flag = flag or flag1
                elif self.data.__class__.__name__ !="Data2D":
                    self.manager.set_smearer(smearer=temp_smearer, qmin= float(self.qmin_x),
                                                             qmax= float(self.qmax_x)) 
                if flag:   
                    #self.compute_chisqr(smearer= temp_smearer)
        
                    ## new state posted
                    if self.state_change:
                        #self._undo.Enable(True)
                        event = PageInfoEvent(page = self)
                        wx.PostEvent(self.parent, event)
                    self.state_change= False 
            else: 
                return    # invalid fit range: do nothing here: msg already displayed in validate    
        else:
            self.save_current_state()
            msg= "Cannot Plot :Must enter a number!!!  "
            wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
             
        self.save_current_state() 
        return 
   
    def _onparamRangeEnter(self, event):
        """
            Check validity of value enter in the parameters range field
        """
        if self.check_invalid_panel():
            return
        tcrtl= event.GetEventObject()
        #Clear msg if previously shown.
        msg= ""
        wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
        # Flag to register when a parameter has changed.
        is_modified = False
        if tcrtl.GetValue().lstrip().rstrip()!="":
            try:
                value = float(tcrtl.GetValue())
                tcrtl.SetBackgroundColour(wx.WHITE)
                self._check_value_enter(self.fittable_param ,is_modified)
                self._check_value_enter(self.parameters ,is_modified) 
            except:
                tcrtl.SetBackgroundColour("pink")
                msg= "Model Error:wrong value entered : %s"% sys.exc_value
                wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
                return 
        else:
           tcrtl.SetBackgroundColour(wx.WHITE)
           
        #self._undo.Enable(True)
        self.save_current_state()
        event = PageInfoEvent(page = self)
        wx.PostEvent(self.parent, event)
        self.state_change= False

                    
    def _onQrangeEnter(self, event):
        """
            Check validity of value enter in the Q range field
        """
        if self.check_invalid_panel():
            return
        tcrtl= event.GetEventObject()
        #Clear msg if previously shown.
        msg= ""
        wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
        # Flag to register when a parameter has changed.
        is_modified = False
        if tcrtl.GetValue().lstrip().rstrip()!="":
            try:
                value = float(tcrtl.GetValue())
                tcrtl.SetBackgroundColour(wx.WHITE)

                # If qmin and qmax have been modified, update qmin and qmax
                if self._validate_qrange( self.qmin, self.qmax):
                    tempmin = float(self.qmin.GetValue())
                    if tempmin != self.qmin_x:
                        self.qmin_x = tempmin
                    tempmax = float(self.qmax.GetValue())
                    if tempmax != self.qmax_x:
                        self.qmax_x = tempmax
                else:
                    tcrtl.SetBackgroundColour("pink")
                    msg= "Model Error:wrong value entered : %s"% sys.exc_value
                    wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
                    return 
                
            except:
                tcrtl.SetBackgroundColour("pink")
                msg= "Model Error:wrong value entered : %s"% sys.exc_value
                wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
                return 
            #Check if # of points for theory model are valid(>0).
            # check for 2d
            if self.data.__class__.__name__ =="Data2D":
                # set mask   
                radius= numpy.sqrt( self.data.qx_data*self.data.qx_data + self.data.qy_data*self.data.qy_data )
                index_data = ((self.qmin <= radius)&(radius<= self.qmax))
                index_data = (index_data)&(self.data.mask)
                index_data = (index_data)&(numpy.isfinite(self.data.data))
                if len(index_data[index_data]) < 10:
                    msg= "Cannot Plot :No or too little npts in that data range!!!  "
                    wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
                    return
                else:
                    self.data.mask = index_data
                    self.Npts_fit.Setvalue(str(len(self.data.mask)))
            else:
                index_data = ((self.qmin <= self.data.x)&(self.data.x <= self.qmax))
                self.Npts_fit.SetValue(str(len(self.data.x[index_data])))
           
        else:
           tcrtl.SetBackgroundColour("pink")
           msg= "Model Error:wrong value entered!!!"
           wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
        
        self._draw_model()
        ##update chi2
        #self.compute_chisqr(smearer= temp_smearer)
        #self._undo.Enable(True)
        self.save_current_state()
        event = PageInfoEvent(page = self)
        wx.PostEvent(self.parent, event)
        self.state_change= False

        return
    def _clear_Err_on_Fit(self):
        """
            hide the error text control shown 
            after fitting
        """
        
        if hasattr(self,"text2_3"):
            self.text2_3.Hide()

        if len(self.parameters)>0:
            for item in self.parameters:
                #Skip t ifhe angle parameters if 1D data
                if self.data.__class__.__name__ !="Data2D":
                    if item in self.orientation_params:
                        continue
                if item in self.param_toFit:
                    continue
                ## hide statictext +/-    
                if item[3]!=None and item[3].IsShown():
                    item[3].Hide()
                ## hide textcrtl  for error after fit
                if item[4]!=None and item[4].IsShown():                   
                    item[4].Hide()
  
        if len(self.fittable_param)>0:
            for item in self.fittable_param:
                #Skip t ifhe angle parameters if 1D data
                if self.data.__class__.__name__ !="Data2D":
                    if item in self.orientation_params:
                        continue
                if item in self.param_toFit:
                    continue
                ## hide statictext +/-    
                if item[3]!=None and item[3].IsShown():
                    item[3].Hide()
                ## hide textcrtl  for error after fit
                if item[4]!=None and item[4].IsShown():
                    item[4].Hide()
        return        
                
    def _get_defult_custom_smear(self):
        """
           Get the defult values for custum smearing.
        """

        # get the default values
        if self.dxl == None: self.dxl = 0.0
        if self.dxw == None: self.dxw = ""
        if self.dx_min == None: self.dx_min = SMEAR_SIZE_L
        if self.dx_max == None: self.dx_max = SMEAR_SIZE_H
        
    def _get_smear_info(self):
        """
           Get the smear info from data.
           @return: self.smear_type, self.dq_l and self.dq_r, 
            respectively the type of the smear, dq_min and dq_max for pinhole smear data 
            while dxl and dxw for slit smear
        """

        # default
        self.smear_type = None
        self.dq_l = None
        self.dq_r = None
        data = self.data
        if self.data is None:
            return
        elif self.data.__class__.__name__ == 'Data2D':  
            if data.dqx_data == None or  data.dqy_data ==None: 
                return
            elif self.smearer != None and all(data.dqx_data !=0)and all(data.dqy_data !=0): 
                self.smear_type = "Pinhole2d"
                self.dq_l = format_number(numpy.average(data.dqx_data)) 
                self.dq_r = format_number(numpy.average(data.dqy_data))  
                return 
            else: 
                return

       

        # check if it is pinhole smear and get min max if it is.
        if data.dx != None and all(data.dx !=0): 
            self.smear_type = "Pinhole" 
            self.dq_l = data.dx[0]
            self.dq_r = data.dx[-1]
            
        # check if it is slit smear and get min max if it is.
        elif data.dxl != None or data.dxw != None: 
            self.smear_type = "Slit" 
            if data.dxl != None and all(data.dxl !=0):
                self.dq_l = data.dxl[0]
            if data.dxw != None and all(data.dxw !=0): 
                self.dq_r = data.dxw[0]
                
        #return self.smear_type,self.dq_l,self.dq_r       
    
    def _show_smear_sizer(self):    
        """
            Show only the sizers depending on smear selection
        """
        # smear disabled
        if self.disable_smearer.GetValue():
            self.smear_description_none.Show(True)
        # 2Dsmear
        elif self._is_2D():
            self.smear_description_accuracy_type.Show(True)
            self.smear_accuracy.Show(True)
            self.smear_description_accuracy_type.Show(True)
            self.smear_description_2d.Show(True)
            self.smear_description_2d_x.Show(True)
            self.smear_description_2d_y.Show(True)
            if self.pinhole_smearer.GetValue():
                self.smear_pinhole_min.Show(True)
                self.smear_pinhole_max.Show(True)
        # smear from data
        elif self.enable_smearer.GetValue():

            self.smear_description_dqdata.Show(True)
            if self.smear_type != None:
                self.smear_description_smear_type.Show(True)
                if self.smear_type == 'Slit':
                    self.smear_description_slit_height.Show(True)
                    self.smear_description_slit_width.Show(True)                
                elif self.smear_type == 'Pinhole':
                    self.smear_description_pin_min.Show(True)
                    self.smear_description_pin_max.Show(True)
                self.smear_description_smear_type.Show(True)
                self.smear_description_type.Show(True)
                self.smear_data_left.Show(True)
                self.smear_data_right.Show(True)
        # custom pinhole smear
        elif self.pinhole_smearer.GetValue():
            if self.smear_type == 'Pinhole':
                self.smear_message_new_p.Show(True)
                self.smear_description_pin_min.Show(True)
                self.smear_description_pin_max.Show(True)

            self.smear_pinhole_min.Show(True)
            self.smear_pinhole_max.Show(True)
        # custom slit smear
        elif self.slit_smearer.GetValue():
            self.smear_message_new_s.Show(True)
            self.smear_description_slit_height.Show(True)
            self.smear_slit_height.Show(True)
            self.smear_description_slit_width.Show(True)
            self.smear_slit_width.Show(True)

    def _hide_all_smear_info(self):
        """
           Hide all smearing messages in the set_smearer sizer
        """
        self.smear_description_none.Hide()
        self.smear_description_dqdata.Hide()
        self.smear_description_type.Hide()
        self.smear_description_smear_type.Hide()
        self.smear_description_accuracy_type.Hide()
        self.smear_description_2d_x.Hide()
        self.smear_description_2d_y.Hide()
        self.smear_description_2d.Hide()
        
        self.smear_accuracy.Hide()
        self.smear_data_left.Hide()
        self.smear_data_right.Hide()
        self.smear_description_pin_min.Hide()
        self.smear_pinhole_min.Hide()
        self.smear_description_pin_max.Hide()
        self.smear_pinhole_max.Hide()
        self.smear_description_slit_height.Hide()
        self.smear_slit_height.Hide()
        self.smear_description_slit_width.Hide()
        self.smear_slit_width.Hide()
        self.smear_message_new_p.Hide()
        self.smear_message_new_s.Hide()
    
    def _set_accuracy_list(self):
        """
            Set the list of an accuracy in 2D custum smear: Xhigh, High, Med, or Low
        """
        # list of accuracy choices
        list = ['Low','Med','High','Xhigh']
        for idx in range(len(list)):
            self.smear_accuracy.Append(list[idx],idx)
            
    def _on_select_accuracy(self,event):
        """
            Select an accuracy in 2D custom smear: Xhigh, High, Med, or Low
        """
        #event.Skip()
        accuracy = event.GetEventObject()
        
        self.smear2d_accuracy = accuracy.GetValue()
        if self.pinhole_smearer.GetValue():
            self.onPinholeSmear(event=None)
        
        else:    self.onSmear(event=None)
        if self.current_smearer !=None:
                self.current_smearer.set_accuracy(accuracy = self.smear2d_accuracy)
        event.Skip()
    def _onMask(self, event):     
        """
            Build a panel to allow to edit Mask
        """
        
        from sans.guiframe.local_perspectives.plotting.masking import MaskPanel as MaskDialog
        
        self.panel = MaskDialog(self, data=self.data,id =-1 )
        self.panel.Bind(wx.EVT_CLOSE, self._draw_masked_model)
        self.panel.ShowModal()
        #wx.PostEvent(self.parent, event)
        
    def _draw_masked_model(self,event):
        """
        Draw model image w/mask
        """
        event.Skip()

        is_valid_qrange = self._update_paramv_on_fit()

        if is_valid_qrange:
            # try re draw the model plot if it exists
            self._draw_model()
            self.panel.Destroy() # frame
            self.set_npts2fit()
        elif self.model == None:
            self.panel.Destroy()
            self.set_npts2fit()
            msg= "No model is found on updating MASK in the model plot... "
            wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
        else:
            msg = ' Please consider your Q range, too.'
            self.panel.ShowMessage(msg)
        
    def set_data(self, data):
        """
            reset the current data 
        """
        self.data = data

        
        if self.data is None:
            data_min = ""
            data_max = ""
            data_name = ""
            self.formfactorbox.Disable()
            self.structurebox.Disable()
        else:
            self.smearer = smear_selection( self.data )
            self.disable_smearer.SetValue(True)
            if self.smearer == None:
                self.enable_smearer.Disable()
            else:
                self.enable_smearer.Enable()
            
            # more disables for 2D
            if self.data.__class__.__name__ =="Data2D":
                self.slit_smearer.Disable()
                self.default_mask = copy.deepcopy(self.data.mask)
                
                
            self.formfactorbox.Enable()
            self.structurebox.Enable()
            data_name = self.data.name
            #set maximum range for x in linear scale
            if not hasattr(self.data,"data"): #Display only for 1D data fit
                # Minimum value of data   
                data_min = min(self.data.x)
                # Maximum value of data  
                data_max = max(self.data.x)
                #number of total data points
                self.Npts_total.SetValue(str(len(self.data.x)))
                #default:number of data points selected to fit
                self.Npts_fit.SetValue(str(len(self.data.x)))
                self.btEditMask.Disable()  
                self.EditMask_title.Disable()
            else:
                ## Minimum value of data 
                data_min = 0
                x = max(math.fabs(self.data.xmin), math.fabs(self.data.xmax)) 
                y = max(math.fabs(self.data.ymin), math.fabs(self.data.ymax))
                ## Maximum value of data  
                data_max = math.sqrt(x*x + y*y)
                #number of total data points
                self.Npts_total.SetValue(str(len(self.data.data)))
                #default:number of data points selected to fit
                self.Npts_fit.SetValue(str(len(self.data.data)))
                self.btEditMask.Enable()  
                self.EditMask_title.Enable() 

            
        self.dataSource.SetValue(data_name)
        self.qmin_x = data_min
        self.qmax_x = data_max
        self.minimum_q.SetValue(str(data_min))
        self.maximum_q.SetValue(str(data_max))
        self.qmin.SetValue(str(data_min))
        self.qmax.SetValue(str(data_max))
        self.qmin.SetBackgroundColour("white")
        self.qmax.SetBackgroundColour("white")
        self.state.data = data
        self.state.qmin = self.qmin_x
        self.state.qmax = self.qmax_x
        

    def reset_page(self, state,first=False):
        """
            reset the state
        """
        self.reset_page_helper(state)
        import sans.guiframe.gui_manager
        evt = ModelEventbox(model=state.model)
        wx.PostEvent(self.event_owner, evt)  
   
        if self.engine_type != None:
            self.manager._on_change_engine(engine=self.engine_type)

        self.select_param(event = None) 
        #Save state_fit
        self.save_current_state_fit()
        self._lay_out()
        self.Refresh()
        
    def get_range(self):
        """
            return the fitting range
        """
        return float(self.qmin_x) , float(self.qmax_x)
    
    def get_npts2fit(self):
        """
            return numbers of data points within qrange
            Note: This is for Park where chi2 is not normalized by Npts of fit
        """
        npts2fit = 0
        qmin,qmax = self.get_range()
        if self.data.__class__.__name__ =="Data2D": 
            radius= numpy.sqrt( self.data.qx_data*self.data.qx_data + self.data.qy_data*self.data.qy_data )
            index_data = (self.qmin_x <= radius)&(radius<= self.qmax_x)
            index_data= (index_data)&(self.data.mask)
            index_data = (index_data)&(numpy.isfinite(self.data.data))
            npts2fit = len(self.data.data[index_data])
        else:
            for qx in self.data.x:
                   if qx >= qmin and qx <= qmax:
                       npts2fit += 1
        return npts2fit

    def set_npts2fit(self):
        """
            setValue Npts for fitting 
        """
        self.Npts_fit.SetValue(str(self.get_npts2fit()))
        
        
    def get_chi2(self):
        """
            return the current chi2
        """
        return self.tcChi.GetValue()
        
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
      
    def onsetValues(self,chisqr,p_name, out,cov):
        """
            Build the panel from the fit result
            @param chisqr:Value of the goodness of fit metric
            @p_name: the name of parameters
            @param out:list of parameter with the best value found during fitting
            @param cov:Covariance matrix
       
        """
        if out == None or not numpy.isfinite(chisqr):
            raise ValueError,"Fit error occured..." 
        
        is_modified = False
        has_error = False    
        
        #Hide textctrl boxes of errors.
        self._clear_Err_on_Fit()    
        
        #Check if chi2 is finite
        if chisqr != None or numpy.isfinite(chisqr):
        #format chi2  
            if self.engine_type == "park":  
                npt_fit = float(self.get_npts2fit()) 
                if npt_fit > 0:
                    chisqr =chisqr/npt_fit    
            chi2 = format_number(chisqr)    
            self.tcChi.SetValue(chi2)    
            self.tcChi.Refresh()    
        else:
            self.tcChi.SetValue("-")
        
        #Hide error title
        if self.text2_3.IsShown():
            self.text2_3.Hide()
      
        try:
            n = self.disp_box.GetCurrentSelection()
            dispersity= self.disp_box.GetClientData(n)
            if dispersity !=None and self.enable_disp.GetValue():
                name= dispersity.__name__
                if name == "GaussianDispersion":
                    if hasattr(self,"text_disp_1" ):
                        if self.text_disp_1 !=None:
                            self.text_disp_1.Hide()
        except:
            dispersty = None
            pass
        #set the panel when fit result are float not list
        if out.__class__== numpy.float64:
            self.param_toFit[0][2].SetValue(format_number(out))
            
            if self.param_toFit[0][4].IsShown:
                self.param_toFit[0][4].Hide()
            if cov !=None :
                self.text2_3.Show(True)
                try:
                    if dispersity !=None:
                        name= dispersity.__name__
                        if name == "GaussianDispersion" and self.enable_disp.GetValue():
                            if hasattr(self,"text_disp_1" ):
                                if self.text_disp_1 !=None:
                                    self.text_disp_1.Show(True)
                except:
                    pass

                if cov[0]==None or  not numpy.isfinite(cov[0]): 
                    if self.param_toFit[0][3].IsShown:
                        self.param_toFit[0][3].Hide()
                else:                    
                    self.param_toFit[0][3].Show(True)               
                    self.param_toFit[0][4].Show(True)
                    self.param_toFit[0][4].SetValue(format_number(cov[0]))
                    has_error = True
        else:

            i = 0
            #Set the panel when fit result are list
            for item in self.param_toFit:     
                if len(item)>5 and item != None:     
                    ## reset error value to initial state
                    item[3].Hide()
                    item[4].Hide()
                    
                    for ind in range(len(out)):
                        
                        if item[1] == p_name[ind]:
                            break        
                    if len(out)<=len(self.param_toFit) and out[ind] !=None:   
                        val_out = format_number(out[ind])                  
                        item[2].SetValue(val_out)

                    if(cov !=None):
                        
                        try:
                            if dispersity !=None:
                                name= dispersity.__name__
                                if name == "GaussianDispersion" and self.enable_disp.GetValue():
                                    if hasattr(self,"text_disp_1" ):
                                        if self.text_disp_1!=None:
                                            if not self.text_disp_1.IsShown():
                                                self.text_disp_1.Show(True)
                        except:
                            pass    
                   
                        if cov[ind]!=None :
                            if numpy.isfinite(float(cov[ind])):
                                val_err = format_number(cov[ind])
                                item[3].Show(True)
                                item[4].Show(True)
                                item[4].SetValue(val_err)

                                has_error = True
                    i += 1         
        #Show error title when any errors displayed
        if has_error: 
            if not self.text2_3.IsShown():
                self.text2_3.Show(True) 
                
        ## save current state  
        self.save_current_state()          
        #plot model
        self._draw_model()   
        self._lay_out()      
        #PostStatusEvent     
        msg = "Fit completed! "
        wx.PostEvent(self.manager.parent, StatusEvent(status=msg))

    def onPinholeSmear(self, event):
        """
            Create a custom pinhole smear object that will change the way residuals
            are compute when fitting
        """

        if self.check_invalid_panel():
            return
        if self.model ==None:
            msg="Need model and data to smear plot"
            wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Smear: %s"%msg))
            return
        
        # Need update param values
        self._update_paramv_on_fit()     

        # msg default
        msg = None
        if event != None:
            tcrtl= event.GetEventObject()
            # event case of radio button
            if tcrtl.GetValue()== True:
                self.dx_min = 0.0
                self.dx_max = 0.0
                is_new_pinhole = True
            else:
                is_new_pinhole = self._is_changed_pinhole()
        else:
            is_new_pinhole = True 
        # if any value is changed
        if is_new_pinhole:
            msg = self._set_pinhole_smear()
        # hide all silt sizer    
        self._hide_all_smear_info()
        
        ##Calculate chi2
        temp_smearer = self.current_smearer
        #self.compute_chisqr(smearer= temp_smearer)
            
        # show relevant slit sizers 
        self._show_smear_sizer()

        self.sizer_set_smearer.Layout()
        self.Layout()   
        
        if event != None: 
            event.Skip()                  
        #self._undo.Enable(True)
        self.save_current_state()
        event = PageInfoEvent(page = self)
        wx.PostEvent(self.parent, event)
        
    def _is_changed_pinhole(self):  
        """
            check if any of pinhole smear is changed
            return: True or False
        """
        # get the values
        pin_min = self.smear_pinhole_min.GetValue()
        pin_max = self.smear_pinhole_max.GetValue()
                    
        # Check changes in slit width    
        try:
            dx_min = float(pin_min)
        except:
            return True
        if self.dx_min != dx_min:
            return True
        
        # Check changes in slit heigth
        try:
            dx_max = float(pin_max)
        except:
            return True
        if self.dx_max != dx_max:
            return True
        return False
    
    def _set_pinhole_smear(self):
        """
            Set custom pinhole smear
            return: msg
        """
        # copy data
        data = copy.deepcopy(self.data)
        if self._is_2D():
            self.smear_type = 'Pinhole2d'
            len_data = len(data.data)
            data.dqx_data = numpy.zeros(len_data)
            data.dqy_data = numpy.zeros(len_data)
        else:
            self.smear_type = 'Pinhole'
            len_data = len(data.x)
            data.dx = numpy.zeros(len_data)
            data.dxl = None
            data.dxw = None
        msg = None
   
        get_pin_min = self.smear_pinhole_min
        get_pin_max = self.smear_pinhole_max        

        if not check_float(get_pin_min):
            get_pin_min.SetBackgroundColour("pink")
            msg= "Model Error:wrong value entered!!!"
        elif not check_float(get_pin_max ):
            get_pin_max.SetBackgroundColour("pink")
            msg= "Model Error:wrong value entered!!!"
        else:
            if len_data < 2: len_data = 2     
            self.dx_min = float(get_pin_min.GetValue())
            self.dx_max = float(get_pin_max.GetValue())
            if self.dx_min < 0:
                get_pin_min.SetBackgroundColour("pink")
                msg= "Model Error:This value can not be negative!!!"
            elif self.dx_max <0:
                get_pin_max.SetBackgroundColour("pink")
                msg= "Model Error:This value can not be negative!!!"
            elif self.dx_min != None and self.dx_max != None:   
                if self._is_2D():
                    data.dqx_data[data.dqx_data==0] = self.dx_min
                    data.dqy_data[data.dqy_data==0] = self.dx_max          
                elif self.dx_min == self.dx_max:
                    data.dx[data.dx==0] = self.dx_min
                else:
                    step = (self.dx_max - self.dx_min)/(len_data-1)    
                    data.dx = numpy.arange(self.dx_min,self.dx_max+step/1.1,step)            
            elif self.dx_min != None: 
                if self._is_2D(): data.dqx_data[data.dqx_data==0] = self.dx_min
                else: data.dx[data.dx==0] = self.dx_min 
            elif self.dx_max != None:
                if self._is_2D(): data.dqy_data[data.dqy_data==0] = self.dx_max
                else: data.dx[data.dx==0] = self.dx_max          
            self.current_smearer = smear_selection(data)

        if msg != None:
            wx.PostEvent(self.manager.parent, StatusEvent(status = msg ))
        else:
            get_pin_min.SetBackgroundColour("white")
            get_pin_max.SetBackgroundColour("white")
        ## set smearing value whether or not the data contain the smearing info
        self.manager.set_smearer(smearer=self.current_smearer, qmin= float(self.qmin_x),qmax= float(self.qmax_x))
 
        return msg
        
    def update_pinhole_smear(self):
        """
            called by kill_focus on pinhole TextCntrl
            to update the changes 
            return: msg: False when wrong value was entered
        """
        # msg default
        msg = None
        # check if any value is changed
        if self._is_changed_pinhole():
            msg = self._set_pinhole_smear()           
        #self._undo.Enable(True)
        self.save_current_state()

        if msg != None:
            return False   
        else:
            return True
                     
    def onSlitSmear(self, event):
        """
            Create a custom slit smear object that will change the way residuals
            are compute when fitting
        """

               
        if self.check_invalid_panel():
            return
        if self.model ==None:
            msg="Need model and data to smear plot"
            wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Smear: %s"%msg))
            return
        # Need update param values
        self._update_paramv_on_fit()

        # msg default
        msg = None
        # for event given
        if event != None:
            tcrtl= event.GetEventObject()
            # event case of radio button
            if tcrtl.GetValue():
                self.dxl = 0.0
                self.dxw = 0.0
                is_new_slit = True
            else:
                is_new_slit = self._is_changed_slit()
        else:
            is_new_slit = True 
                
        # if any value is changed
        if is_new_slit:
            msg = self._set_slit_smear()
        # hide all silt sizer
        self._hide_all_smear_info()        
        ##Calculate chi2
        #self.compute_chisqr(smearer= self.current_smearer)  
        # show relevant slit sizers       
        self._show_smear_sizer()
        self.sizer_set_smearer.Layout()
        self.Layout()
        
        if event != None:
            event.Skip()     
        #self._undo.Enable(True)
        self.save_current_state()
        event = PageInfoEvent(page = self)
        wx.PostEvent(self.parent, event)
        if msg != None:
            wx.PostEvent(self.manager.parent, StatusEvent(status = msg))

            
    def _is_changed_slit(self):  
        """
            check if any of slit lengths is changed
            return: True or False
        """
        # get the values
        width = self.smear_slit_width.GetValue()
        height = self.smear_slit_height.GetValue()
        
        # check and change the box bg color if it was pink but it should be white now
        # because this is the case that _set_slit_smear() will not handle
        if height.lstrip().rstrip()=="":
            self.smear_slit_height.SetBackgroundColour(wx.WHITE)
        if width.lstrip().rstrip()=="":
            self.smear_slit_width.SetBackgroundColour(wx.WHITE)
            
        # Check changes in slit width    
        if width == "": 
            dxw = 0.0
        else:
            try:
                dxw = float(width)
            except:
                return True
        if self.dxw != dxw:
            return True
        
        # Check changes in slit heigth
        if height == "": 
            dxl = 0.0
        else:
            try:
                dxl = float(height)
            except:
                return True
        if self.dxl != dxl:
            return True
        return False
    
    def _set_slit_smear(self):
        """
            Set custom slit smear
            return: msg
        """
        temp_smearer = None
        # make sure once more if it is smearer
        data = copy.deepcopy(self.data)
        data_len = len(data.x)
        data.dx = None
        data.dxl = None
        data.dxw = None
        msg = None
   
        try:
            self.dxl = float(self.smear_slit_height.GetValue())
            data.dxl = self.dxl* numpy.ones(data_len)
            self.smear_slit_height.SetBackgroundColour(wx.WHITE)
        except: 
            data.dxl = numpy.zeros(data_len)
            if self.smear_slit_height.GetValue().lstrip().rstrip()!="":
                self.smear_slit_height.SetBackgroundColour("pink")
                msg = "Wrong value entered... "  
            else:
                self.smear_slit_height.SetBackgroundColour(wx.WHITE)
        try:
            self.dxw = float(self.smear_slit_width.GetValue())
            self.smear_slit_width.SetBackgroundColour(wx.WHITE)
            data.dxw = self.dxw* numpy.ones(data_len)
        except: 
            data.dxw = numpy.zeros(data_len)
            if self.smear_slit_width.GetValue().lstrip().rstrip()!="":
                self.smear_slit_width.SetBackgroundColour("pink")
                msg = "Wrong Fit value entered... "
            else:
                self.smear_slit_width.SetBackgroundColour(wx.WHITE)
                
        self.current_smearer = smear_selection(data)
        #temp_smearer = self.current_smearer
        ## set smearing value whether or not the data contain the smearing info
        self.manager.set_smearer(smearer=self.current_smearer, qmin= float(self.qmin_x), qmax= float(self.qmax_x)) 

        return msg
    
    
    def update_slit_smear(self):
        """
            called by kill_focus on pinhole TextCntrl
            to update the changes 
            return: msg: False when wrong value was entered
        """             
        # msg default
        msg = None
        # check if any value is changed
        if self._is_changed_slit():
            msg = self._set_slit_smear()           
        #self._undo.Enable(True)
        self.save_current_state()

        if msg != None:
            return False   
        else:
            return True
                            
    
    def onSmear(self, event):
        """
            Create a smear object that will change the way residuals
            are compute when fitting
        """
        if event != None: 
            event.Skip()    
        if self.check_invalid_panel():
            return
        if self.model ==None:
            msg="Need model and data to smear plot"
            wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Smear: %s"%msg))
            return
        
        # Need update param values
        self._update_paramv_on_fit()
              
        temp_smearer = None
        self._get_smear_info()
        
        #renew smear sizer
        if self.smear_type != None:
            self.smear_description_smear_type.SetValue(str(self.smear_type))
            self.smear_data_left.SetValue(str(self.dq_l))   
            self.smear_data_right.SetValue(str(self.dq_r))       

        self._hide_all_smear_info()
        
        data = copy.deepcopy(self.data)
        # make sure once more if it is smearer
        self.current_smearer = smear_selection(data)
        
        if self.enable_smearer.GetValue():
            if hasattr(self.data,"dxl"):
                
                msg= ": Resolution smearing parameters"
            if hasattr(self.data,"dxw"):
                msg= ": Slit smearing parameters"
            if self.smearer ==None:
                wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Data contains no smearing information"))
            else:
                wx.PostEvent(self.manager.parent, StatusEvent(status=\
                            "Data contains smearing information"))

            #self.smear_description_dqdata.Show(True)
            self.smear_data_left.Show(True)
            self.smear_data_right.Show(True)
            temp_smearer= self.current_smearer
        elif self.disable_smearer.GetValue():
            self.smear_description_none.Show(True)
            
        self._show_smear_sizer()
        
        self.sizer_set_smearer.Layout()
        self.Layout()
        ## set smearing value whether or not the data contain the smearing info
        self.manager.set_smearer(smearer=temp_smearer, qmin= float(self.qmin_x),
                                     qmax= float(self.qmax_x)) 

        ##Calculate chi2
        #self.compute_chisqr(smearer= temp_smearer)
        
        self.state.enable_smearer=  self.enable_smearer.GetValue()
        self.state.disable_smearer=self.disable_smearer.GetValue()
        self.state.pinhole_smearer = self.pinhole_smearer.GetValue()
        self.state.slit_smearer = self.slit_smearer.GetValue()
      
    def on_complete_chisqr(self, event):  
        """
            print result chisqr 
            @event: activated by fitting/ complete after draw
        """
        try:
            if event ==None:
                output= "-"
            else:
                output = event.output
            self.tcChi.SetValue(str(format_number(output)))

            self.state.tcChi =self.tcChi
        except:
            pass  
        
    def complete_chisqr(self, output, elapsed=None):  
        """
            print result chisqr
        """
        try:
            if output ==None:
                output= "-"

            self.tcChi.SetValue(str(format_number(output)))

            self.state.tcChi =self.tcChi

        except:
            pass
        
        
    def compute_chisqr1D(self, smearer=None):
        """
            Compute chisqr for 1D
        """
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
           
            
   
        
        
    def compute_chisqr2D(self,smearer=None):
        """ 
            compute chi square given a model and data 2D and set the value
            to the tcChi txtcrl
        """
        try:
            self.qmin_x = float(self.qmin.GetValue())
            self.qmax_x = float(self.qmax.GetValue())
           
            ##return residuals within self.qmin_x and self.qmax_x
            from gui_thread import CalcChisqr2D
            ## If a thread is already started, stop it
            if self.calc_Chisqr!= None and self.calc_Chisqr.isrunning():
                self.calc_Chisqr.stop()
            if smearer !=None:
                smearer.set_accuracy(accuracy = self.smear2d_accuracy)
            self.calc_Chisqr= CalcChisqr2D( data2d= self.data,
                                            model= self.model,
                                            smearer=smearer,
                                            qmin= self.qmin_x,
                                            qmax = self.qmax_x,
                                            completefn = self.complete_chisqr,
                                            updatefn   = None)
    
            self.calc_Chisqr.queue()
          
        except:
           raise

        
    def compute_chisqr(self ,output=None, smearer=None):
        """ 
            compute chi square given a model and data 1D and set the value
            to the tcChi txtcrl
        """
        flag = self._validate_qrange( self.qmin, self.qmax)
        if flag== True:
            try:
                if hasattr(self.data,"data"):
                    self.compute_chisqr2D(smearer=smearer)
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
                #if len(self.fittable_param)>0:
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
           
        self.save_current_state_fit()  
       
        if event !=None:
            #self._undo.Enable(True)
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
            #Skip t ifhe angle parameters if 1D data
            if self.data.__class__.__name__ !="Data2D":
                if item in self.orientation_params:
                    continue
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
            #Skip t ifhe angle parameters if 1D data
            if self.data.__class__.__name__ !="Data2D":
                if item in self.orientation_params:
                    continue
            if item[0].GetValue():
                if not (item in self.param_toFit):
                    self.param_toFit.append(item)  
            else:
                #remove parameters from the fitting list
                if item in self.param_toFit:
                    self.param_toFit.remove(item)

        #Calculate num. of angle parameters 
        if self.data.__class__.__name__ =="Data2D":  
            len_orient_para = 0
        else:
            len_orient_para = len(self.orientation_params)  #assume even len 
        #Total num. of angle parameters
        if len(self.fittable_param) > 0:
            len_orient_para *= 2
        #Set the value of checkbox that selected every checkbox or not            
        if len(self.parameters)+len(self.fittable_param)-len_orient_para ==len(self.param_toFit):
            self.cb1.SetValue(True)
        else:
            self.cb1.SetValue(False)
        self.save_current_state_fit()
        if event !=None:
            #self._undo.Enable(True)
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
            self.SetScrollbars(20,20,25,65)
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
        select_text = "Select All"
        self.cb1 = wx.CheckBox(self, -1,str(select_text), (10, 10))
        wx.EVT_CHECKBOX(self, self.cb1.GetId(), self.select_all_param)
        self.cb1.SetToolTipString("To check/uncheck all the boxes below.")
        #self.cb1.SetValue(True)
        
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
                
                ##prepare a spot to store errors
                if not self.model.details.has_key(item):
                    self.model.details [item] = ["",None,None] 
         
                iy += 1
                ix = 0
                ## add parameters name with checkbox for selecting to fit
                cb = wx.CheckBox(self, -1, item )              
                cb.SetToolTipString(" Check for fitting.")
                #cb.SetValue(True)
                wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                
                sizer.Add( cb,( iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
                
                ## add parameter value
                ix += 1
                value= self.model.getParam(item)
                ctl1 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                    style=wx.TE_PROCESS_ENTER)
                ctl1.SetToolTipString("Hit 'Enter' after typing.")
                ctl1.SetValue(format_number(value))
                sizer.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                ## text to show error sign
                ix += 1
                text2=wx.StaticText(self, -1, '+/-')
                sizer.Add(text2,(iy, ix),(1,1),\
                                wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
                text2.Hide() 
                ix += 1
                ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=0)
                sizer.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ctl2.Hide()
                
                ix += 1
                ctl3 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                               text_enter_callback = self._onparamRangeEnter)
     
                sizer.Add(ctl3, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ctl3.Hide()
        
                ix += 1
                ctl4 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                               text_enter_callback = self._onparamRangeEnter)
                sizer.Add(ctl4, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
      
                ctl4.Hide()

                if self.engine_type=="park":
                    ctl3.Show(True)
                    ctl4.Show(True)
                ix +=1
                # Units
                if self.model.details.has_key(item):
                    units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                else:
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
                    ##prepare a spot to store min max
                    if not self.model.details.has_key(item):
                        self.model.details [item] = ["",None,None] 
                          
                    iy += 1
                    ix = 0
                    ## add parameters name with checkbox for selecting to fit
                    cb = wx.CheckBox(self, -1, item )
                    cb.SetValue(False)
                    cb.SetToolTipString("Check for fitting")
                    wx.EVT_CHECKBOX(self, cb.GetId(), self.select_param)
                    if self.data.__class__.__name__ =="Data2D":
                        cb.Show(True)
                    else:
                        cb.Hide()
                    sizer.Add( cb,( iy, ix),(1,1),
                                 wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
    
                    ## add parameter value
                    ix += 1
                    value= self.model.getParam(item)
                    ctl1 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                        style=wx.TE_PROCESS_ENTER)
                    ctl1.SetToolTipString("Hit 'Enter' after typing.")
                    ctl1.SetValue(format_number(value))
                    if self.data.__class__.__name__ =="Data2D":
                        ctl1.Show(True)
                    else:
                        ctl1.Hide()
                    sizer.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                    ## text to show error sign
                    ix += 1
                    text2=wx.StaticText(self, -1, '+/-')
                    sizer.Add(text2,(iy, ix),(1,1),\
                                    wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
                    text2.Hide() 
                    ix += 1
                    ctl2 = wx.TextCtrl(self, -1, size=(_BOX_WIDTH,20), style=0)
                    sizer.Add(ctl2, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                    ctl2.Hide()
                    
                    
                    ix += 1
                    ctl3 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                                   text_enter_callback = self._onparamRangeEnter)
                    
                    sizer.Add(ctl3, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                    ctl3.Hide()
                 
                    ix += 1
                    ctl4 = self.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20), style=wx.TE_PROCESS_ENTER,
                                                   text_enter_callback = self._onparamRangeEnter)
                    sizer.Add(ctl4, (iy,ix),(1,1), wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                   
                    ctl4.Hide()
                    
                    if self.engine_type =="park" and self.data.__class__.__name__ =="Data2D":                      
                        ctl3.Show(True)
                        ctl4.Show(True)
                    
                    ix +=1
                    # Units
                    if self.model.details.has_key(item):
                        units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                    else:
                        units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
                    if self.data.__class__.__name__ =="Data2D":
                        units.Show(True)
                    
                    else:
                        units.Hide()
                    
                    sizer.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                                          
                    ##[cb state, name, value, "+/-", error of fit, min, max , units]
                    self.parameters.append([cb,item, ctl1,
                                            text2,ctl2, ctl3, ctl4,units])
                    self.orientation_params.append([cb,item, ctl1,
                                            text2,ctl2, ctl3, ctl4,units])
              
        iy+=1
        
        #Display units text on panel
        for item in keys:   
            if self.model.details.has_key(item):
                self.text2_4.Show()
        #Fill the list of fittable parameters
        self.select_all_param(event=None)

        self.save_current_state_fit()
        boxsizer1.Add(sizer)
        self.sizer3.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        self.sizer3.Layout()
        self.Layout()
        self.Refresh()
        self.SetScrollbars(20,20,25,65)

class BGTextCtrl(wx.TextCtrl):
    """
        Text control used to display outputs.
        No editing allowed. The background is 
        grayed out. User can't select text.
    """
    def __init__(self, *args, **kwds):
        wx.TextCtrl.__init__(self, *args, **kwds)
        self.SetEditable(False)
        self.SetBackgroundColour(self.GetParent().GetBackgroundColour())
        
        # Bind to mouse event to avoid text highlighting
        # The event will be skipped once the call-back
        # is called.
        self.Bind(wx.EVT_MOUSE_EVENTS, self._click)
        
    def _click(self, event):
        """
            Prevent further handling of the mouse event
            by not calling Skip().
        """ 
        pass
        
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
                