"""
Batch panel
"""
import wx
import wx.lib.newevent
import math
from sas.guiframe.events import StatusEvent
from sas.guiframe.events import NewPlotEvent

(Chi2UpdateEvent, EVT_CHI2_UPDATE) = wx.lib.newevent.NewEvent()
_BOX_WIDTH = 76
_DATA_BOX_WIDTH = 300
SMEAR_SIZE_L = 0.00
SMEAR_SIZE_H = 0.00

from sas.perspectives.fitting.basepage import PageInfoEvent
from sas.models.qsmearing import smear_selection
from sas.perspectives.fitting.fitpage import FitPage
from sas.perspectives.fitting.fitpage import check_data_validity

class BatchFitPage(FitPage):
    """
    Batch Page
    """
    window_name = "BatchFit"
    window_caption = "BatchFit"

    def __init__(self, parent, color=None):
        """
        Initialization of the Panel
        """
        FitPage.__init__(self, parent, color=color)

        ## draw sizer

    def _fill_data_sizer(self):
        """
        fill sizer 0 with data info
        """
        self.data_box_description = wx.StaticBox(self, wx.ID_ANY, 'I(q) Data Source')
        if check_data_validity(self.data):
            dname_color = wx.BLUE
        else:
            dname_color = wx.RED
        self.data_box_description.SetForegroundColour(dname_color)
        boxsizer1 = wx.StaticBoxSizer(self.data_box_description, wx.VERTICAL)
        #----------------------------------------------------------
        sizer_data = wx.BoxSizer(wx.VERTICAL)
        text1 = wx.StaticText(self, wx.ID_ANY, ' - Choose a file to set initial fit parameters -')
        text1.SetForegroundColour(wx.RED)
        sizer_data.Add(text1)
        text2 = wx.StaticText(self, wx.ID_ANY, ' - This panel is not designed to view individual fits. - ')
        text2.SetForegroundColour(wx.RED)
        sizer_data.Add(text2)

        combo = wx.BoxSizer(wx.HORIZONTAL)
        self.dataSource = wx.ComboBox(self, wx.ID_ANY, style=wx.CB_READONLY)
        wx.EVT_COMBOBOX(self.dataSource, wx.ID_ANY, self.on_select_data)
        self.dataSource.SetMinSize((_DATA_BOX_WIDTH, -1))

        combo.Add(wx.StaticText(self, wx.ID_ANY, 'Name : '))
        combo.Add((0, 5))
        combo.Add(self.dataSource)

        sizer_data.Add(combo, 0, wx.ALL, 10)
        boxsizer1.Add(sizer_data, 0, wx.ALL, 0)
        self.sizer0.Add(boxsizer1, 0, wx.EXPAND | wx.ALL, 10)
        self.sizer0.Layout()

#    COMMENTED OUT TO USE METHODS INHERITED FROM fitpage.py

#     def _fill_range_sizer(self):
#         """
#         Fill the sizer containing the plotting range
#         add  access to npts
#         """
#         is_2Ddata = False
#         
#         # Check if data is 2D
#         if self.data.__class__.__name__ ==  "Data2D" or \
#                         self.enable2D:
#             is_2Ddata = True
#             
#         title = "Fitting"     
#         self._get_smear_info()
#         
#         #Sizers
#         box_description_range = wx.StaticBox(self, wx.ID_ANY, str(title))
#         boxsizer_range = wx.StaticBoxSizer(box_description_range, wx.VERTICAL)      
#         self.sizer_set_smearer = wx.BoxSizer(wx.VERTICAL)
#         #sizer_smearer = wx.BoxSizer(wx.HORIZONTAL)
#         self.sizer_new_smear = wx.BoxSizer(wx.HORIZONTAL)
#         self.sizer_set_masking = wx.BoxSizer(wx.HORIZONTAL)
#         sizer_chi2 = wx.BoxSizer(wx.VERTICAL)
# 
#         sizer_fit = wx.GridSizer(2, 4, 2, 6)
#         #Fit button
#         self.btFit = wx.Button(self, self._ids.next(), 'Fit', size=(88, 25))
#         self.default_bt_colour =  self.btFit.GetDefaultAttributes()
#         self.btFit.Bind(wx.EVT_BUTTON, self._onFit, id= self.btFit.GetId())
#         self.btFit.SetToolTipString("Start fitting.")
# 
#         # Update and Draw button
#         self.draw_button = wx.Button(self, self._ids.next(), 'Compute', size=(88, 24))
#         self.draw_button.Bind(wx.EVT_BUTTON, \
#                               self._onDraw,id=self.draw_button.GetId())
#         self.draw_button.SetToolTipString("Compute and Draw.")  
#         sizer_fit.Add(self.draw_button, 0, 0)
#         sizer_fit.Add(self.btFit, 0, 0) 
#         sizer_chi2.Add((-1, 5))
#         # get smear_selection
#         self.current_smearer = smear_selection( self.data, self.model )
#         boxsizer_range.Add(self.sizer_set_masking)
#          #2D data? default
#         is_2Ddata = False
#         
#         #check if it is 2D data
#         if self.data.__class__.__name__ ==  "Data2D" or \
#                         self.enable2D:
#             is_2Ddata = True
#             
#         self.sizer5.Clear(True)
#      
#         self.qmin  = ModelTextCtrl(self, wx.ID_ANY, size=(_BOX_WIDTH, 20),
#                                           style=wx.TE_PROCESS_ENTER, 
#                                     text_enter_callback = self._onQrangeEnter)
#         self.qmin.SetValue(str(self.qmin_x))
#         self.qmin.SetToolTipString("Minimun value of Q in linear scale.")
#      
#         self.qmax  = ModelTextCtrl(self, wx.ID_ANY, size=(_BOX_WIDTH, 20),
#                                           style=wx.TE_PROCESS_ENTER, 
#                                         text_enter_callback=self._onQrangeEnter)
#         self.qmax.SetValue(str(self.qmax_x))
#         self.qmax.SetToolTipString("Maximum value of Q in linear scale.")
#         
#         id = self._ids.next()
#         self.reset_qrange =wx.Button(self, id, 'Reset', size=(77, 20))
#       
#         self.reset_qrange.Bind(wx.EVT_BUTTON, self.on_reset_clicked, id=id)
#         self.reset_qrange.SetToolTipString(\
#                                     "Reset Q range to the default values")
#      
#         sizer_horizontal = wx.BoxSizer(wx.HORIZONTAL)
#         sizer = wx.GridSizer(2, 4, 2, 6)
# 
#         self.btEditMask = wx.Button(self, self._ids.next(),'Editor', size=(88, 23))
#         self.btEditMask.Bind(wx.EVT_BUTTON, 
#                              self._onMask,id=self.btEditMask.GetId())
#         self.btEditMask.SetToolTipString("Edit Mask.")
#         self.EditMask_title = wx.StaticText(self, wx.ID_ANY, ' Masking(2D)')
# 
#         sizer.Add(wx.StaticText(self, wx.ID_ANY, 'Q range'))
#         sizer.Add(wx.StaticText(self, wx.ID_ANY, ' Min[1/A]'))
#         sizer.Add(wx.StaticText(self, wx.ID_ANY, ' Max[1/A]'))
#         sizer.Add(self.EditMask_title)
#  
#         sizer.Add(self.reset_qrange)   
#         sizer.Add(self.qmin)
#         sizer.Add(self.qmax)
# 
#         sizer.Add(self.btEditMask)
#         boxsizer_range.Add(sizer_chi2) 
#         boxsizer_range.Add((10, 10))
#         boxsizer_range.Add(sizer)
#         
#         boxsizer_range.Add((10, 15))
#         boxsizer_range.Add(sizer_fit)
#         if is_2Ddata:
#             self.btEditMask.Enable()  
#             self.EditMask_title.Enable() 
#         else:
#             self.btEditMask.Disable()  
#             self.EditMask_title.Disable()
# 
#         ## save state
#         #self.save_current_state()
# 
#         self.sizer5.Add(boxsizer_range, 0, wx.EXPAND | wx.ALL, 10)
#         self.sizer5.Layout()
#        
#     def _on_select_model(self, event=None): 
#         """
#         call back for model selection
#         """  
#         
#         self.Show(False)    
#         self._on_select_model_helper() 
#         self.set_model_param_sizer(self.model)                   
#         if self.model is None:
#             self._set_bookmark_flag(False)
#             self._keep.Enable(False)
#             self._set_save_flag(False)
#         self.enable_disp.SetValue(False)
#         self.disable_disp.SetValue(True)
#         try:
#             self.set_dispers_sizer()
#         except:
#             pass
#         self.state.structurecombobox = self.structurebox.GetCurrentSelection()
#         self.state.formfactorcombobox = self.formfactorbox.GetCurrentSelection()
#       
#         if self.model != None:
#             self._set_copy_flag(True)
#             self._set_paste_flag(True)
#             if self.data != None:
#                 self._set_bookmark_flag(False)
#                 self._keep.Enable(False)
#                 
#             temp_smear = None
#             ## event to post model to fit to fitting plugins
#             (ModelEventbox, _) = wx.lib.newevent.NewEvent()
#          
#             ## set smearing value whether or not 
#             #    the data contain the smearing info
#             evt = ModelEventbox(model=self.model, 
#                                         smearer=temp_smear, 
#                                         qmin=float(self.qmin_x),
#                                         uid=self.uid,
#                                      qmax=float(self.qmax_x)) 
#    
#             self._manager._on_model_panel(evt=evt)
#             self.mbox_description.SetLabel("Model [%s]" % str(self.model.name))
#             self.state.model = self.model.clone()
#             self.state.model.name = self.model.name
# 
#             
#         if event != None:
#             ## post state to fit panel
#             new_event = PageInfoEvent(page = self)
#             wx.PostEvent(self.parent, new_event) 
#             #update list of plugins if new plugin is available
#             if self.plugin_rbutton.GetValue():
#                 temp = self.parent.update_model_list()
#                 if temp:
#                     self.model_list_box = temp
#                     current_val = self.formfactorbox.GetValue()
#                     pos = self.formfactorbox.GetSelection()
#                     self._show_combox_helper()
#                     self.formfactorbox.SetSelection(pos)
#                     self.formfactorbox.SetValue(current_val)
#             self._onDraw(event=None)
#         else:
#             self._draw_model()
#         self.SetupScrolling()
#         self.Show(True)   
#         
#     def _update_paramv_on_fit(self):
#         """
#         make sure that update param values just before the fitting
#         """
#         #flag for qmin qmax check values
#         flag = True
#         self.fitrange = True
#         is_modified = False
# 
#         if self.model != None:           
#             ##Check the values
#             self._check_value_enter( self.fittable_param, is_modified)
#             self._check_value_enter( self.fixed_param, is_modified)
#             self._check_value_enter( self.parameters, is_modified)
# 
#             # If qmin and qmax have been modified, update qmin and qmax and 
#              # Here we should check whether the boundaries have been modified.
#             # If qmin and qmax have been modified, update qmin and qmax and 
#             # set the is_modified flag to True
#             self.fitrange = self._validate_qrange(self.qmin, self.qmax)
#             if self.fitrange:
#                 tempmin = float(self.qmin.GetValue())
#                 if tempmin != self.qmin_x:
#                     self.qmin_x = tempmin
#                 tempmax = float(self.qmax.GetValue())
#                 if tempmax != self.qmax_x:
#                     self.qmax_x = tempmax
#                 if tempmax == tempmin:
#                     flag = False    
#                 #temp_smearer = None
#                 if self._is_2D():
#                     # only 2D case set mask  
#                     flag = self._validate_Npts()
#                     if not flag:
#                         return flag
#             else: flag = False
#         else: 
#             flag = False
# 
#         #For invalid q range, disable the mask editor and fit button, vs.    
#         if not self.fitrange:
#             #self.btFit.Disable()
#             if self._is_2D():
#                 self.btEditMask.Disable()
#         else:
#             #self.btFit.Enable(True)
#             if self._is_2D() and  self.data != None:
#                 self.btEditMask.Enable(True)
# 
#         if not flag:
#             msg = "Cannot Plot or Fit :Must select a "
#             msg += " model or Fitting range is not valid!!!  "
#             wx.PostEvent(self.parent.parent, StatusEvent(status=msg))
#         
#         self.save_current_state()
#    
#         return flag  
#     def save_current_state(self):
#         """
#         Currently no save option implemented for batch page
#         """
#         pass 
#     def save_current_state_fit(self):
#         """
#         Currently no save option implemented for batch page
#         """
#         pass
#     def set_data(self, data):
#         """
#         reset the current data 
#         """
#         #id = None
#         group_id = None
#         flag = False
#         if self.data is None and data is not None:
#             flag = True
#         if data is not None:
#             #id = data.id
#             group_id = data.group_id
#             if self.data is not None:
#                 flag = (data.id != self.data.id)
#         self.data = data
#         if self.data is None:
#             data_min = ""
#             data_max = ""
#             data_name = ""
#             self._set_bookmark_flag(False)
#             self._keep.Enable(False)
#             self._set_save_flag(False)
#         else:
#             if self.model != None:
#                 self._set_bookmark_flag(False)
#                 self._keep.Enable(False)
#             self._set_save_flag(False)
#             self._set_preview_flag(True)
#   
#             self.formfactorbox.Enable()
#             self.structurebox.Enable()
#             data_name = self.data.name
#             #set maximum range for x in linear scale
#             if not hasattr(self.data,"data"): #Display only for 1D data fit
#                 # Minimum value of data   
#                 data_min = min(self.data.x)
#                 # Maximum value of data  
#                 data_max = max(self.data.x)
#                 self.btEditMask.Disable()  
#                 self.EditMask_title.Disable()
#             else:
#                 
#                 ## Minimum value of data 
#                 data_min = 0
#                 x = max(math.fabs(self.data.xmin), math.fabs(self.data.xmax)) 
#                 y = max(math.fabs(self.data.ymin), math.fabs(self.data.ymax))
#                 ## Maximum value of data  
#                 data_max = math.sqrt(x*x + y*y)
#                 self.btEditMask.Enable()  
#                 self.EditMask_title.Enable() 
# 
#         self.dataSource.SetValue(data_name)
#         self.qmin_x = data_min
#         self.qmax_x = data_max
#         #self.minimum_q.SetValue(str(data_min))
#         #self.maximum_q.SetValue(str(data_max))
#         self.qmin.SetValue(str(data_min))
#         self.qmax.SetValue(str(data_max))
#         self.qmin.SetBackgroundColour("white")
#         self.qmax.SetBackgroundColour("white")
#         self.state.data = data
#         self.state.qmin = self.qmin_x
#         self.state.qmax = self.qmax_x
#         
#         #update model plot with new data information
#         if flag:
#             #set model view button
#             if self.data.__class__.__name__ == "Data2D":
#                 self.enable2D = True
#                 self.model_view.SetLabel("2D Mode")
#             else:
#                 self.enable2D = False
#                 self.model_view.SetLabel("1D Mode")
#                 
#             self.model_view.Disable()
#             
#             wx.PostEvent(self._manager.parent, 
#                              NewPlotEvent(group_id=group_id,
#                                                action="delete"))
#             #plot the current selected data
#             wx.PostEvent(self._manager.parent, NewPlotEvent(plot=self.data, 
#                                                     title=str(self.data.title)))
#             self._manager.store_data(uid=self.uid, data=data,
#                                      data_list=self.data_list,
#                                       caption=self.window_name)
#             self._draw_model()



class BGTextCtrl(wx.TextCtrl):
    """
    Text control used to display outputs.
    No editing allowed. The background is
    grayed out. User can't select text.
    """
    def __init__(self, *args, **kwds):
        wx.TextCtrl.__init__(self, *args, **kwds)
        self.SetEditable(False)
        self.SetBackgroundColour(self.GetParent().parent.GetBackgroundColour())

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

