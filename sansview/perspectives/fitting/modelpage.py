
import wx
import wx.lib.newevent
import numpy
import copy
import math
from sans.models.dispersion_models import ArrayDispersion, GaussianDispersion

from sans.guicomm.events import StatusEvent   
from sans.guiframe.utils import format_number
(ModelEventbox, EVT_MODEL_BOX) = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 76

import basepage
from basepage import BasicPage
from basepage import PageInfoEvent

class ModelPage(BasicPage):
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
        self._fill_model_sizer( self.sizer1)  
        self._fill_range_sizer() 
         
        description=""
        if self.model!=None:
            
            description = self.model.description
            
            self.select_model(self.model)
            self.set_model_description(description,self.sizer2)
            
     
        
        
    def _on_display_description(self, event):
        """
            Show or Hide description
            @param event: wx.EVT_RADIOBUTTON
        """
        self._on_display_description_helper()
        
        self.SetScrollbars(20,20,200,100)
        self.Refresh()

        
        
    def _on_display_description_helper(self):
        """
            Show or Hide description
            @param event: wx.EVT_RADIOBUTTON
        """
        
        ## Show description
        if self.description_hide.GetValue():
            self.sizer_description.Clear(True)
            
        else:
            description="Model contains no description"
            if self.model!=None:
                description = self.model.description
            if description.lstrip().rstrip() =="": 
                description="Model contains no description"
            self.description = wx.StaticText( self,-1,str(description) )
            self.sizer_description.Add( self.description, 1, wx.EXPAND | wx.ALL, 10 )
           
        self.Layout()
    
    
    def _fill_range_sizer(self):
        """
            Fill the sizer containing the plotting range
            add  access to npts
        """
        sizer_npts= wx.GridSizer(1, 1,5, 5)
    
        self.npts    = BasicPage.ModelTextCtrl(self, -1,size=(_BOX_WIDTH,20))
        self.npts.SetValue(format_number(self.num_points))
        self.npts.SetToolTipString("Number of point to plot.")
        
        sizer_npts.Add(wx.StaticText(self, -1, 'Npts'),1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)        
        sizer_npts.Add(self.npts,1, wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5) 
        self._set_range_sizer( title="Plotted Q Range", object= sizer_npts)
       
       
    def _on_select_model(self, event): 
        """
             call back for model selection
        """    
        self._on_select_model_helper() 

        self.select_model(self.model)
        
       
    def _fill_model_sizer(self, sizer):
        """
            fill sizer containing model info
        """
        id = wx.NewId()
        self.model_view =wx.Button(self,id,'View 2D')
        self.model_view.Bind(wx.EVT_BUTTON, self._onModel2D,id=id)
        self.model_view.SetToolTipString("View model in 2D")
        
        ## class base method  to add view 2d button   
        self._set_model_sizer(sizer=sizer, title="Model",object= self.model_view )    
    
  
    #def _set_sizer_gaussian(self):
    def _set_sizer_dispersion(self, dispersity):
        """
            draw sizer with gaussian, log or schulz dispersity parameters
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
                        name = wx.StaticText(self, -1,  name1)
                        self.sizer4_4.Add( name,( iy, ix),(1,1),  
                                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                        ix = 1
                        value= self.model.getParam(name1)
                        ctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                            style=wx.TE_PROCESS_ENTER)
                        ctl1.SetValue(str (format_number(value)))
                        self.sizer4_4.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                        self.fittable_param.append([None,name1,ctl1,None,
                                                    None, None, None,None])
                    elif p=="npts":
                            ix =2
                            value= self.model.getParam(name2)
                            Tctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            Tctl1.SetValue(str (format_number(value)))
                            self.sizer4_4.Add(Tctl1, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name2, Tctl1,None,None,
                                                      None, None,None])
                    elif p=="nsigmas":
                            ix =3 
                            value= self.model.getParam(name3)
                            Tctl2 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            Tctl2.SetValue(str (format_number(value)))
                            self.sizer4_4.Add(Tctl2, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            ix +=1
                            self.sizer4_4.Add((20,20), (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name3, Tctl2,
                                                     None,None, None, None,None])
        for item in self.model.dispersion.keys():
            if item in self.model.orientation_params:
                self.disp_cb_dict[item]= None
                name1=item+".width"
                name2=item+".npts"
                name3=item+".nsigmas"
                iy += 1
                for p in self.model.dispersion[item].keys():
                    if p=="width":
                        ix = 0
                        name = wx.StaticText(self, -1,  name1)
                        self.sizer4_4.Add( name,( iy, ix),(1,1),  
                                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                        if not self.enable2D:
                            name.Hide()
                        else:
                            name.Show(True)
                        ix = 1
                        value= self.model.getParam(name1)
                        ctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                                            style=wx.TE_PROCESS_ENTER)
                        ctl1.SetValue(str (format_number(value)))
                        if not self.enable2D:
                            ctl1.Hide()
                            ctl1.Disable()
                        else:
                            ctl1.Show(True)
                            ctl1.Enable()
                        self.sizer4_4.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                        self.fittable_param.append([None,name1,ctl1,None,
                                                    None, None, None,None])
                        self.orientation_params_disp.append([None,name1,ctl1,None,
                                                    None, None, None,None])
                    elif p=="npts":
                            ix =2
                            value= self.model.getParam(name2)
                            Tctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            Tctl1.SetValue(str (format_number(value)))
                            if not self.enable2D:
                                Tctl1.Hide()
                                Tctl1.Disable()
                            else:
                                Tctl1.Show(True)
                                Tctl1.Enable()
                            self.sizer4_4.Add(Tctl1, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name2, Tctl1,None,None,
                                                      None, None,None])
                            self.orientation_params_disp.append([None,name2, Tctl1,None,None,
                                                      None, None,None])
                    elif p=="nsigmas":
                            ix =3 
                            value= self.model.getParam(name3)
                            Tctl2 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH/2,20),
                                                style=wx.TE_PROCESS_ENTER)
                            Tctl2.SetValue(str (format_number(value)))
                            if not self.enable2D:
                                Tctl2.Hide()
                                Tctl2.Disable()
                            else:
                                Tctl2.Show(True)
                                Tctl2.Enable()
                            self.sizer4_4.Add(Tctl2, (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            ix +=1
                            self.sizer4_4.Add((20,20), (iy,ix),(1,1),
                                               wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                            self.fixed_param.append([None,name3, Tctl2,
                                                     None,None, None, None,None])
                            self.orientation_params_disp.append([None,name3, Tctl2,
                                                     None,None, None, None,None])
            
        msg = " Selected Distribution: Gaussian"        
        wx.PostEvent(self.parent.parent, StatusEvent( status= msg )) 
        self.state.disp_cb_dict = copy.deepcopy(self.disp_cb_dict)   
        ix =0
        iy +=1 
        self.sizer4_4.Add((20,20),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)   
        self.sizer4_4.Layout()
        self.sizer4.Layout()
        self.SetScrollbars(20,20,200,100)
             
 
    def _onModel2D(self, event):
        """
         call manager to plot model in 2D
        """
        # If the 2D display is not currently enabled, plot the model in 2D 
        # and set the enable2D flag.

        if self.fitrange:
            self.enable2D = True
 
        if self.enable2D:
            self._draw_model()
            self.model_view.Disable()
           
            #ToDo:cleanup this mess.           
            #self.set_model_param_sizer(self.model)
            #self._set_sizer_gaussian()
            
            if len(self.orientation_params)>0:
                for item in self.orientation_params:
                    if item[2]!=None:      
    
                        item[2].Enable()
            if  self.disp_name.lower() == "array":                
                self._set_sizer_arraydispersion()  
            else:
                if len(self.orientation_params_disp)>0:
                     for item in self.orientation_params_disp:
                        if item[2]!=None:
                            item[2].Enable()
        self.state.enable2D =  copy.deepcopy(self.enable2D)
        ## post state to fit panel
        self._undo.Enable(True)
        event = PageInfoEvent(page = self)
        wx.PostEvent(self.parent, event)
              
                
    def reset_page(self, state):
        """
            reset the state
        """
        self.reset_page_helper(state)
        
        
    def select_model(self, model):
        """
            Select a new model
            @param model: model object 
        """
        self.model = model
        if self.model !=None:
            self.disp_list= self.model.getDispParamList()
        self.set_model_param_sizer(self.model)
        ## keep the sizer view consistent with the model menu selecting
        self._set_model_sizer_selection( self.model )
        self.enable_disp.SetValue(False)
        self.disable_disp.SetValue(True)
        self.set_dispers_sizer()
        
        self.model_view.SetFocus()
        if self.model !=None:
            self._draw_model()
        self.state.structurecombobox = self.structurebox.GetCurrentSelection()
        self.state.formfactorcombobox = self.formfactorbox.GetCurrentSelection()
       
        ## post state to fit panel
        self._undo.Enable(True)
        event = PageInfoEvent(page = self)
        wx.PostEvent(self.parent, event)               
    
    
    def set_model_description(self,description,sizer):
        """
            fill a sizer with description
            @param description: of type string
            @param sizer: wx.BoxSizer()
        """
    
        sizer.Clear(True)
        box_description= wx.StaticBox(self, -1, 'Model Description')
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)

        sizer_selection=wx.BoxSizer(wx.HORIZONTAL)
        self.description_hide = wx.RadioButton(self, -1, 'Hide', style=wx.RB_GROUP)
        self.description_show = wx.RadioButton(self, -1, 'Show')
       
        
        if description=="":
            self.description_hide.SetValue(True)
            description=" Description unavailable. Click for details"
            
        self.description = wx.StaticText( self,-1,str(description) )
        
        self.Bind( wx.EVT_RADIOBUTTON, self._on_display_description,
                   id=self.description_hide.GetId() )
        
        self.Bind( wx.EVT_RADIOBUTTON, self._on_display_description,
                   id=self.description_show.GetId() )
        
        self.model_description = wx.Button(self,-1, label="Details")
        self.model_description.Bind(wx.EVT_BUTTON,self.on_button_clicked)
        self.model_description.SetToolTipString("Click Model Functions in HelpWindow...")
      
        sizer_selection.Add( self.description_show )
        sizer_selection.Add( (20,20)) 
        sizer_selection.Add( self.description_hide )
        sizer_selection.Add((20,20),0, wx.LEFT|wx.RIGHT|wx.EXPAND,67)
        sizer_selection.Add( self.model_description )
                     
         
        self.sizer_description=wx.BoxSizer(wx.HORIZONTAL)
        self.sizer_description.Add( self.description, 1, wx.EXPAND | wx.ALL, 10 )
        boxsizer1.Add( sizer_selection) 
        boxsizer1.Add( (20,20)) 
        boxsizer1.Add( self.sizer_description) 
    
        self._on_display_description(event=None)
        sizer.Add(boxsizer1,0, wx.EXPAND | wx.ALL, 10)
        sizer.Layout()
   
    def on_button_clicked(self,event):
        """
        #On 'More details' button
        """
        from helpPanel import  HelpWindow
        
        if self.model == None:
            name = 'FuncHelp'
        else:
            name = self.model.name
        frame = HelpWindow(None, -1, name)    
        frame.Show(True)
        if frame.rhelp.HasAnchor(name):
            frame.rhelp.ScrollToAnchor(name)
        else:
           msg= "Model does not contains an available description "
           msg +="Please.Search in the Help window"
           wx.PostEvent(self.parent.parent, StatusEvent(status = msg ))
                     
            
            
    def set_range(self, qmin_x, qmax_x, npts):
        """
            Set the range for the plotted models
            @param qmin: minimum Q
            @param qmax: maximum Q
            @param npts: number of Q bins
        """
        # Set the data members
        self.qmin_x = qmin_x
        self.qmax_x = qmax_x
        self.num_points = npts
        
        # Set the controls
        #For qmin and qmax, do not use format_number.(If do, qmin and max could be different from what is in the data.)
       
        self.qmin.SetValue(str(self.qmin_x))
        self.qmax.SetValue(str(self.qmax_x))
        self.npts.SetValue(format_number(self.num_points))
        
        
    def set_model_param_sizer(self, model):
        """
            Build the panel from the model content
            @param model: the model selected in combo box for fitting purpose
        """
        self.sizer3.Clear(True)
        self.parameters = []
        self.param_toFit=[]
        self.fixed_param=[]
        self.orientation_params=[]
        self.orientation_params_disp=[]
        if model ==None:
            ##no model avaiable to draw sizer 
            self.sizer3.Layout()
            self.SetScrollbars(20,20,200,100)
            return
        box_description= wx.StaticBox(self, -1,str("Model Parameters"))
        boxsizer1 = wx.StaticBoxSizer(box_description, wx.VERTICAL)
        sizer = wx.GridBagSizer(5,5)
        
        self.model = model
        self.set_model_description(self.model.description,self.sizer2)
       
        keys = self.model.getParamList()
        ##list of dispersion parameters
        self.disp_list=self.model.getDispParamList()
       
        keys.sort()
    
        iy = 0
        ix = 0
        self.text1_2 = wx.StaticText(self, -1, 'Names')
        sizer.Add(self.text1_2,(iy, ix),(1,1),\
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix +=1
        self.text2_2 = wx.StaticText(self, -1, 'Values')
        sizer.Add(self.text2_2,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        ix +=1
        self.text2_4 = wx.StaticText(self, -1, '[Units]')
        sizer.Add(self.text2_4,(iy, ix),(1,1),\
                            wx.EXPAND|wx.ADJUST_MINSIZE, 0) 
        self.text2_4.Hide()
        
        for item in keys:
            if not item in self.disp_list and not item in self.model.orientation_params:
                iy += 1
                ix = 0
                name = wx.StaticText(self, -1,item)
                sizer.Add( name,( iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)

                ix += 1
                value= self.model.getParam(item)
                ctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                    style=wx.TE_PROCESS_ENTER)
                
                ctl1.SetValue(str (format_number(value)))
                
                sizer.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                ix +=1
                # Units
                try:
                    units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                except:
                    units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
                sizer.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                ##[cb state, name, value, "+/-", error of fit, min, max , units]
                self.parameters.append([None,item, ctl1,
                                        None,None, None, None,None])
        iy+=1
        sizer.Add((10,10),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        iy += 1
        ix = 0
        
        #Add tile for orientational angle parameters
        for item in keys:
            if item in self.model.orientation_params:        
                orient_angle = wx.StaticText(self, -1, '[For 2D only]:')
                sizer.Add(orient_angle,(iy, ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15) 
                if not self.enable2D:
                    orient_angle.Hide()
                else:
                    orient_angle.Show(True)
                break
                                          
        for item  in self.model.orientation_params:
            if not item in self.disp_list and item in keys:
                iy += 1
                ix = 0
                name = wx.StaticText(self, -1,item)
                sizer.Add( name,( iy, ix),(1,1),
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
                if not self.enable2D:
                    name.Hide()
                else:
                    name.Show(True)

                ix += 1
                value= self.model.getParam(item)
                ctl1 = BasicPage.ModelTextCtrl(self, -1, size=(_BOX_WIDTH,20),
                    style=wx.TE_PROCESS_ENTER)
                
                ctl1.SetValue(str (format_number(value)))
                if not self.enable2D:
                    ctl1.Hide()
                    ctl1.Disable()
                else:
                    ctl1.Show(True)
                    ctl1.Enable()
                
                sizer.Add(ctl1, (iy,ix),(1,1), wx.EXPAND)
                ix +=1
                # Units
                try:
                    units = wx.StaticText(self, -1, self.model.details[item][0], style=wx.ALIGN_LEFT)
                except:
                    units = wx.StaticText(self, -1, "", style=wx.ALIGN_LEFT)
                if not self.enable2D:
                    units.Hide()
                    units.Disable()
                else:
                    units.Show(True)
                    units.Enable()

                sizer.Add(units, (iy,ix),(1,1),  wx.EXPAND|wx.ADJUST_MINSIZE, 0)
                
                ##[cb state, name, value, "+/-", error of fit, min, max , units]
                self.parameters.append([None,item, ctl1,
                                        None,None, None, None,None])
                self.orientation_params.append([None,item, ctl1,
                                        None,None, None, None,None])
                    
        iy+=1
        sizer.Add((10,10),(iy,ix),(1,1), wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
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
        from fitpanel import PageInfo
        myinfo = PageInfo(self,model)
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
        
        self.page = ModelPage(self, myinfo) 
        
        
        
        self.Centre()
        self.Show(True)


   
if __name__=="__main__":
    app = wx.App()
    HelpWindow(None, -1, 'HelpWindow')
    app.MainLoop()
                