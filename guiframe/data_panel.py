################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2010, University of Tennessee
################################################################################
"""
This module provides Graphic interface for the data_manager module.
"""
import os
import wx
import sys
import warnings
from wx.lib.scrolledpanel import ScrolledPanel
import  wx.lib.agw.customtreectrl as CT
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import Data2D
from sans.guiframe.panel_base import PanelBase
from sans.guiframe.events import StatusEvent
from DataLoader.loader import Loader

try:
    # Try to find a local config
    import imp
    path = os.getcwd()
    if(os.path.isfile("%s/%s.py" % (path, 'local_config'))) or \
        (os.path.isfile("%s/%s.pyc" % (path, 'local_config'))):
        fObj, path, descr = imp.find_module('local_config', [path])
        config = imp.load_module('local_config', fObj, path, descr)  
    else:
        # Try simply importing local_config
        import local_config as config
except:
    # Didn't find local config, load the default 
    import config
 
extension_list = []
if config.APPLICATION_STATE_EXTENSION is not None:
    extension_list.append(config.APPLICATION_STATE_EXTENSION)
EXTENSIONS = config.PLUGIN_STATE_EXTENSIONS + extension_list   

PANEL_WIDTH = 180
#PANEL_HEIGHT = 560
PANEL_HEIGHT = 700
STYLE_FLAG =wx.RAISED_BORDER|CT.TR_HAS_BUTTONS| CT.TR_HIDE_ROOT|\
                    wx.WANTS_CHARS|CT.TR_HAS_VARIABLE_ROW_HEIGHT
                    
                    
class DataTreeCtrl(CT.CustomTreeCtrl):
    """
    Check list control to be used for Data Panel
    """
    def __init__(self, parent,*args, **kwds):
        #agwstyle is introduced in wx.2.8.11 but is not working for mac
        if sys.platform.count("darwin") != 0:
            try:
                kwds['style'] = STYLE_FLAG
            except:
                raise
        else:
            #agwstyle is introduced in wx.2.8.11 .argument working only for windows
            try:
                kwds['agwStyle'] = STYLE_FLAG
            except:
                try:
                    kwds['style'] = STYLE_FLAG
                except:
                    raise
        
        CT.CustomTreeCtrl.__init__(self, parent, *args, **kwds)
        self.root = self.AddRoot("Available Data")
        
class DataPanel(ScrolledPanel, PanelBase):
    """
    This panel displays data available in the application and widgets to 
    interact with data.
    """
    ## Internal name for the AUI manager
    window_name = "Data Panel"
    ## Title to appear on top of the window
    window_caption = "Data Explorer"
    #type of window 
    window_type = "Data Panel"
    ## Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    #ALWAYS_ON = True
    def __init__(self, parent, list=[],list_of_perspective=[],
                 size=(PANEL_WIDTH,PANEL_HEIGHT), manager=None, *args, **kwds):
        kwds['size']= size
        kwds['style'] = STYLE_FLAG
        ScrolledPanel.__init__(self, parent=parent, *args, **kwds)
        PanelBase.__init__(self)
        self.SetupScrolling()
        self.loader = Loader()  
        #Default location
        self._default_save_location = None  
        self.all_data1d = True
        self.parent = parent
        self.manager = manager
        self.list_of_data = list
        self.list_of_perspective = list_of_perspective
        self.list_rb_perspectives= []
        self.list_cb_data = {}
        self.list_cb_theory = {}
        
        self.owner = None
        self.do_layout()
        self.Bind(wx.EVT_SHOW, self.on_close_page)
        self.enable_remove()
        self.enable_import()
        
    def do_layout(self):
        """
        """
        self.define_panel_structure()
        self.layout_selection()
        self.layout_data_list()
        self.layout_button()
        self.layout_batch()
   
    def define_panel_structure(self):
        """
        Define the skeleton of the panel
        """
        w, h = self.parent.GetSize()
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer1.SetMinSize((w/13, h*2/5))
      
        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer3 = wx.GridBagSizer(5,5)
        self.sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer5 = wx.BoxSizer(wx.VERTICAL)
       
        self.vbox.Add(self.sizer5, 0, wx.EXPAND|wx.ALL,1)
        self.vbox.Add(self.sizer1, 0, wx.EXPAND|wx.ALL,0)
        self.vbox.Add(self.sizer2, 0, wx.EXPAND|wx.ALL,1)
        self.vbox.Add(self.sizer3, 0, wx.EXPAND|wx.ALL,1)
        self.vbox.Add(self.sizer4, 0, wx.EXPAND|wx.ALL,5)
        
        self.SetSizer(self.vbox)
        
    def layout_selection(self):
        """
        """
        select_txt = wx.StaticText(self, -1, 'Selection Options')
        select_txt.SetForegroundColour('blue')
        self.selection_cbox = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        list_of_options = ['Select all Data',
                            'Unselect all Data',
                           'Select all Data 1D',
                           'Unselect all Data 1D',
                           'Select all Data 2D',
                           'Unselect all Data 2D' ]
        for option in list_of_options:
            self.selection_cbox.Append(str(option))
        self.selection_cbox.SetValue('Select all Data')
        wx.EVT_COMBOBOX(self.selection_cbox,-1, self._on_selection_type)
        self.sizer5.AddMany([(select_txt,0, wx.ALL,5),
                            (self.selection_cbox,0, wx.ALL,5)])
    def layout_perspective(self, list_of_perspective=[]):
        """
        Layout widgets related to the list of plug-ins of the gui_manager 
        """
        if len(list_of_perspective)==0:
            return
        w, h = self.parent.GetSize()
        box_description_2= wx.StaticBox(self, -1, "Set Active Perspective")
        self.boxsizer_2 = wx.StaticBoxSizer(box_description_2, wx.HORIZONTAL)
        self.sizer_perspective = wx.GridBagSizer(5,5)
        self.boxsizer_2.Add(self.sizer_perspective)
        self.sizer2.Add(self.boxsizer_2,1, wx.ALL, 10)
        self.list_of_perspective = list_of_perspective
        self.sizer_perspective.Clear(True)
        self.list_rb_perspectives = []
       
        nb_active_perspective = 0
        if list_of_perspective:
            ix = 0 
            iy = 0
            for perspective_name, is_active in list_of_perspective:
                
                if is_active:
                    nb_active_perspective += 1
                if nb_active_perspective == 1:
                    rb = wx.RadioButton(self, -1, perspective_name,
                                        style=wx.RB_GROUP)
                    rb.SetToolTipString("Data will be applied to this perspective")
                    rb.SetValue(is_active)
                else:
                    rb = wx.RadioButton(self, -1, perspective_name)
                    rb.SetToolTipString("Data will be applied to this perspective")
                    #only one perpesctive can be active
                    rb.SetValue(False)
                
                self.Bind(wx.EVT_RADIOBUTTON, self.on_set_active_perspective,
                                                     id=rb.GetId())
                self.list_rb_perspectives.append(rb)
                self.sizer_perspective.Add(rb,(iy, ix),(1,1),
                               wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
                iy += 1
        else:
            rb = wx.RadioButton(self, -1, 'No Perspective',
                                                      style=wx.RB_GROUP)
            rb.SetValue(True)
            rb.Disable()
            ix = 0 
            iy = 0
            self.sizer_perspective.Add(rb,(iy, ix),(1,1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
            
    def _on_selection_type(self, event):
        """
        Select data according to patterns
        """
        
        list_of_options = ['Select all Data',
                            'Unselect all Data',
                           'Select all Data 1D',
                           'Unselect all Data 1D',
                           'Select all Data 2D',
                           'Unselect all Data 2D' ]
        option = self.selection_cbox.GetValue()
        
        pos = self.selection_cbox.GetSelection()
        if pos == wx.NOT_FOUND:
            return 
        option = self.selection_cbox.GetString(pos)
        for item in self.list_cb_data.values():
            data_ctrl, _, _, _,_, _ = item
            data_id, data_class, _ = self.tree_ctrl.GetItemPyData(data_ctrl) 
            if option == 'Select all Data':
                self.tree_ctrl.CheckItem(data_ctrl, True) 
            elif option == 'Unselect all Data':
                self.tree_ctrl.CheckItem(data_ctrl, False)
            elif option == 'Select all Data 1D':
                if data_class == 'Data1D':
                    self.tree_ctrl.CheckItem(data_ctrl, True) 
            elif option == 'Unselect all Data 1D':
                if data_class == 'Data1D':
                    self.tree_ctrl.CheckItem(data_ctrl, False) 
            elif option == 'Select all Data 1D':
                if data_class == 'Data1D':
                    self.tree_ctrl.CheckItem(data_ctrl, True) 
            elif option == 'Select all Data 2D':
                if data_class == 'Data2D':
                    self.tree_ctrl.CheckItem(data_ctrl, True) 
            elif option == 'Unselect all Data 2D':
                if data_class == 'Data2D':
                    self.tree_ctrl.CheckItem(data_ctrl, False) 
               
    def on_set_active_perspective(self, event):
        """
        Select the active perspective
        """
        ctrl = event.GetEventObject()
        
    def layout_button(self):
        """
        Layout widgets related to buttons
        """
        self.bt_add = wx.Button(self, wx.NewId(), "Load Data")
        self.bt_add.SetToolTipString("Add data from the application")
        wx.EVT_BUTTON(self, self.bt_add.GetId(), self._load_data)
        self.bt_remove = wx.Button(self, wx.NewId(), "Remove Data")
        self.bt_remove.SetToolTipString("Remove data from the application")
        wx.EVT_BUTTON(self, self.bt_remove.GetId(), self.on_remove)
        self.bt_import = wx.Button(self, wx.NewId(), "Send To")
        self.bt_import.SetToolTipString("Send set of Data to active perspective")
        wx.EVT_BUTTON(self, self.bt_import.GetId(), self.on_import)
        
        self.bt_append_plot = wx.Button(self, wx.NewId(), "Append Plot To")
        self.bt_append_plot.SetToolTipString("Plot the selected data in the active panel")
        wx.EVT_BUTTON(self, self.bt_append_plot.GetId(), self.on_append_plot)
        
        self.bt_plot = wx.Button(self, wx.NewId(), "New Plot")
        self.bt_plot.SetToolTipString("To trigger plotting")
        wx.EVT_BUTTON(self, self.bt_plot.GetId(), self.on_plot)
        
        self.bt_freeze = wx.Button(self, wx.NewId(), "Freeze Theory")
        self.bt_freeze.SetToolTipString("To trigger freeze a theory")
        wx.EVT_BUTTON(self, self.bt_freeze.GetId(), self.on_freeze)
        
        self.tctrl_perspective = wx.StaticText(self, -1, 
                            'No Active Application',
                        style=wx.SUNKEN_BORDER|wx.ALIGN_LEFT)
        self.tctrl_perspective.SetToolTipString("Active Application")
        perspective_font = self.tctrl_perspective.GetFont()
        perspective_font.SetWeight(wx.BOLD)
        self.tctrl_perspective.SetFont(perspective_font)
        self.tctrl_perspective.SetClientSize((80,20))
        self.cb_plotpanel = wx.ComboBox(self, -1, 
                                style=wx.CB_READONLY|wx.CB_SORT)
        wx.EVT_COMBOBOX(self.cb_plotpanel,-1, self._on_plot_selection)
        self.cb_plotpanel.Append('None')
        self.cb_plotpanel.SetStringSelection('None')

        #self.tctrl_plotpanel = wx.StaticText(self, -1, 'No Plot panel on focus')
        #self.tctrl_plotpanel.SetToolTipString("Active Plot Panel")
    
        ix = 0
        iy = 0
        self.sizer3.Add(self.bt_add,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        ix += 1          
        self.sizer3.Add(self.bt_remove,( iy, ix),(1,1),  
                             wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        ix = 0   
        iy += 1
        self.sizer3.Add(self.bt_import,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        ix += 1
        self.sizer3.Add(self.tctrl_perspective,(iy, ix),(1,1),
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)      
        ix = 0          
        iy += 1 
        self.sizer3.Add(self.bt_append_plot,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        ix += 1
        self.sizer3.Add(self.cb_plotpanel,(iy, ix),(1,1),
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        ix = 0          
        iy += 1 
        self.sizer3.Add(self.bt_plot,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        ix = 0          
        iy += 1 
        self.sizer3.Add(self.bt_freeze,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        
    def layout_batch(self):
        """
        """
        return
        self.rb_single_mode = wx.RadioButton(self, -1, 'Single Mode',
                                             style=wx.RB_GROUP)
        self.rb_batch_mode = wx.RadioButton(self, -1, 'Batch Mode')
        
        self.rb_single_mode.SetValue(True)
        self.rb_batch_mode.SetValue(False)
        self.sizer4.AddMany([(self.rb_single_mode,0, wx.ALL,5),
                            (self.rb_batch_mode,0, wx.ALL,5)])
      
    def old_layout_data_list(self):
        """
        Add a listcrtl in the panel
        """
        self.tree_ctrl = DataTreeCtrl(parent=self)
        self.tree_ctrl.Bind(CT.EVT_TREE_ITEM_CHECKING, self.on_check_item)
        self.sizer1.Add(self.tree_ctrl,1, wx.EXPAND|wx.ALL, 10)
        self.theory_root = self.tree_ctrl.InsertItem(self.tree_ctrl.root,0,
                                                   "THEORIES", ct_type=0)
    
    def layout_data_list(self):
        """
        Add a listcrtl in the panel
        """
        tree_ctrl_label = wx.StaticText(self, -1, "Data")
        tree_ctrl_label.SetForegroundColour('blue')
        self.tree_ctrl = DataTreeCtrl(parent=self)
        self.tree_ctrl.Bind(CT.EVT_TREE_ITEM_CHECKING, self.on_check_item)
        tree_ctrl_theory_label = wx.StaticText(self, -1, "Theory")
        tree_ctrl_theory_label.SetForegroundColour('blue')
        self.tree_ctrl_theory = DataTreeCtrl(parent=self)
        self.tree_ctrl_theory.Bind(CT.EVT_TREE_ITEM_CHECKING, self.on_check_item)
        self.sizer1.Add(tree_ctrl_label, 0, wx.LEFT, 10)
        self.sizer1.Add(self.tree_ctrl, 1, wx.EXPAND|wx.ALL, 10)
        self.sizer1.Add(tree_ctrl_theory_label, 0,  wx.LEFT, 10)
        self.sizer1.Add(self.tree_ctrl_theory, 1, wx.EXPAND|wx.ALL, 10)
           
    def onContextMenu(self, event): 
        """
        Retrieve the state selected state
        """
        # Skipping the save state functionality for release 0.9.0
        #return
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self.popUpMenu, pos) 
      
  
    def on_check_item(self, event):
        """
        """
        item = event.GetItem()
        item.Check(not item.IsChecked()) 
        self.enable_button(item)
        event.Skip()
        
    def enable_button(self, item):
        """
        """
        # Not implemented
        return
        """
        _, data_class, _= self.tree_ctrl.GetItemPyData(item) 
        if item.IsChecked():
            self.all_data1d &= (data_class != "Data2D")
            if self.all_data1d:
                self.bt_freeze.Enable()
            else:
                self.bt_freeze.Disable()
        else:
            self.all_data1d |= True
            self.all_data1d &= (data_class != "Data2D")
            if self.all_data1d:
                self.bt_freeze.Enable()
            else:
                self.bt_freeze.Disable()
        """       
    def load_data_list(self, list):
        """
        add need data with its theory under the tree
        """
        if not list:
            self.enable_remove()
            return
        # uncheck previous items
        #self._uncheck_all()    
           
        for state_id, dstate in list.iteritems():
            data = dstate.get_data()
            theory_list = dstate.get_theory()
            if data is not None:
                data_name = data.name
                data_class = data.__class__.__name__
                path = dstate.get_path() 
                process_list = data.process
                data_id = data.id
                
                if state_id not in self.list_cb_data:
                    #new state
                    data_c = self.tree_ctrl.InsertItem(self.tree_ctrl.root,0,
                                                       data_name, ct_type=1, 
                                         data=(data_id, data_class, state_id))
                    data_c.Check(True)
                    self.enable_button(data_c)
                    d_i_c = self.tree_ctrl.AppendItem(data_c, 'Info')
                    i_c_c = self.tree_ctrl.AppendItem(d_i_c, 
                                                  'Type: %s' % data_class)
                    p_c_c = self.tree_ctrl.AppendItem(d_i_c,
                                                  'Path: %s' % str(path))
                    d_p_c = self.tree_ctrl.AppendItem(d_i_c, 'Process')
                    
                    for process in process_list:
                        i_t_c = self.tree_ctrl.AppendItem(d_p_c,
                                                          process.__str__())
                    theory_child = self.tree_ctrl.AppendItem(data_c, "THEORIES")
                   
                    self.list_cb_data[state_id] = [data_c, 
                                                   d_i_c,
                                                   i_c_c,
                                                    p_c_c,
                                                     d_p_c,
                                                     theory_child]
                else:
                    data_ctrl_list =  self.list_cb_data[state_id]
                    #This state is already display replace it contains
                    data_c, d_i_c, i_c_c, p_c_c, d_p_c, t_c = data_ctrl_list
                    self.tree_ctrl.SetItemText(data_c, data_name) 
                    temp = (data_id, data_class, state_id)
                    self.tree_ctrl.SetItemPyData(data_c, temp) 
                    self.tree_ctrl.SetItemText(i_c_c, 'Type: %s' % data_class)
                    self.tree_ctrl.SetItemText(p_c_c, 'Path: %s' % str(path)) 
                    self.tree_ctrl.DeleteChildren(d_p_c) 
                    for process in process_list:
                        i_t_c = self.tree_ctrl.AppendItem(d_p_c,
                                                          process.__str__())
            self.append_theory(state_id, theory_list)
        self.enable_remove()
        
    def _uncheck_all(self):
        """
        Uncheck all check boxes
        """
        for item in self.list_cb_data.values():
            data_ctrl, _, _, _,_, _ = item
            self.tree_ctrl.CheckItem(data_ctrl, False) 
        
    def old_append_theory(self, state_id, theory_list):
        """
        append theory object under data from a state of id = state_id
        replace that theory if  already displayed
        """
        if not theory_list:
            return 
        if state_id not in self.list_cb_data.keys():
            root = self.theory_root
        else:
            item = self.list_cb_data[state_id]
            data_c, _, _, _, _, _ = item
            root = data_c
        if root is not None:
             self.append_theory_helper(root=root, 
                                       state_id=state_id, 
                                       theory_list=theory_list)
    def append_theory(self, state_id, theory_list):
        """
        append theory object under data from a state of id = state_id
        replace that theory if  already displayed
        """
        if not theory_list:
            return 
        if state_id not in self.list_cb_data.keys():
            root = self.tree_ctrl_theory.root
            tree = self.tree_ctrl_theory
        else:
            item = self.list_cb_data[state_id]
            data_c, _, _, _, _, _ = item
            root = data_c
            tree = self.tree_ctrl
        if root is not None:
             self.append_theory_helper(tree=tree, root=root, 
                                       state_id=state_id, 
                                       theory_list=theory_list)
      
      
    def append_theory_helper(self, tree, root, state_id, theory_list):
        """
        """
        if state_id in self.list_cb_theory.keys():
            #update current list of theory for this data
            theory_list_ctrl = self.list_cb_theory[state_id]

            for theory_id, item in theory_list.iteritems():
                theory_data, theory_state = item
                if theory_data is None:
                    name = "Unknown"
                    theory_class = "Unknown"
                    theory_id = "Unknown"
                    temp = (None, None, None)
                else:
                    name = theory_data.name
                    theory_class = theory_data.__class__.__name__
                    theory_id = theory_data.id
                    #if theory_state is not None:
                    #    name = theory_state.model.name
                    temp = (theory_id, theory_class, state_id)
                if theory_id not in theory_list_ctrl:
                    #add new theory
                    t_child = tree.AppendItem(root,
                                                    name, ct_type=1, data=temp)
                    t_i_c = tree.AppendItem(t_child, 'Info')
                    i_c_c = tree.AppendItem(t_i_c, 
                                                  'Type: %s' % theory_class)
                    t_p_c = tree.AppendItem(t_i_c, 'Process')
                    
                    for process in theory_data.process:
                        i_t_c = tree.AppendItem(t_p_c,
                                                          process.__str__())
                    theory_list_ctrl[theory_id] = [t_child, 
                                                   i_c_c, 
                                                   t_p_c]
                else:
                    #replace theory
                    t_child, i_c_c, t_p_c = theory_list_ctrl[theory_id]
                    tree.SetItemText(t_child, name) 
                    tree.SetItemPyData(t_child, temp) 
                    tree.SetItemText(i_c_c, 'Type: %s' % theory_class) 
                    tree.DeleteChildren(t_p_c) 
                    for process in theory_data.process:
                        i_t_c = tree.AppendItem(t_p_c,
                                                          process.__str__())
              
        else:
            #data didn't have a theory associated it before
            theory_list_ctrl = {}
            for theory_id, item in theory_list.iteritems():
                theory_data, theory_state = item
                if theory_data is not None:
                    name = theory_data.name
                    theory_class = theory_data.__class__.__name__
                    theory_id = theory_data.id
                    #if theory_state is not None:
                    #    name = theory_state.model.name 
                    temp = (theory_id, theory_class, state_id)
                    t_child = tree.AppendItem(root,
                            name, ct_type=1, 
                            data=(theory_data.id, theory_class, state_id))
                    t_i_c = tree.AppendItem(t_child, 'Info')
                    i_c_c = tree.AppendItem(t_i_c, 
                                                  'Type: %s' % theory_class)
                    t_p_c = tree.AppendItem(t_i_c, 'Process')
                    
                    for process in theory_data.process:
                        i_t_c = tree.AppendItem(t_p_c,
                                                          process.__str__())
            
                    theory_list_ctrl[theory_id] = [t_child, i_c_c, t_p_c]
                #self.list_cb_theory[data_id] = theory_list_ctrl
                self.list_cb_theory[state_id] = theory_list_ctrl
        
            
   
    def set_data_helper(self):
        """
        """
        data_to_plot = []
        state_to_plot = []
        theory_to_plot = []
        for value in self.list_cb_data.values():
            item, _, _, _, _, _ = value
            if item.IsChecked():
                data_id, _, state_id = self.tree_ctrl.GetItemPyData(item)
                data_to_plot.append(data_id)
                if state_id not in state_to_plot:
                    state_to_plot.append(state_id)
           
        for theory_dict in self.list_cb_theory.values():
            for key, value in theory_dict.iteritems():
                item, _, _ = value
                if item.IsChecked():
                    theory_id, _, state_id = self.tree_ctrl.GetItemPyData(item)
                    theory_to_plot.append(theory_id)
                    if state_id not in state_to_plot:
                        state_to_plot.append(state_id)
        return data_to_plot, theory_to_plot, state_to_plot
    
    def remove_by_id(self, id):
        """
        """
        for item in self.list_cb_data.values():
            data_c, _, _, _, _, theory_child = item
            data_id, _, state_id = self.tree_ctrl.GetItemPyData(data_c) 
            if id == data_id:
                self.tree_ctrl.Delete(data_c)
                del self.list_cb_data[state_id]
                del self.list_cb_theory[data_id]
              
    def load_error(self, error=None):
        """
        Pop up an error message.
        
        :param error: details error message to be displayed
        """
        message = "The data file you selected could not be loaded.\n"
        message += "Make sure the content of your file"
        message += " is properly formatted.\n\n"
        
        if error is not None:
            message += "When contacting the DANSE team, mention the"
            message += " following:\n%s" % str(error)
        dial = wx.MessageDialog(self.parent, message, 'Error Loading File',
                                wx.OK | wx.ICON_EXCLAMATION)
        dial.ShowModal()  
        
    def _load_data(self, event):
        """
        Load data
        """
        path = None
        if self._default_save_location == None:
            self._default_save_location = os.getcwd()
        
        cards = self.loader.get_wildcards()
        wlist =  '|'.join(cards)
        style = wx.OPEN|wx.FD_MULTIPLE
        dlg = wx.FileDialog(self.parent, 
                            "Choose a file", 
                            self._default_save_location, "",
                             wlist,
                             style=style)
        if dlg.ShowModal() == wx.ID_OK:
            file_list = dlg.GetPaths()
            if len(file_list) >= 0 and not(file_list[0]is None):
                self._default_save_location = os.path.dirname(file_list[0])
                path = self._default_save_location
        dlg.Destroy()
        
        if path is None or not file_list or file_list[0] is None:
            return
        self.get_data(file_list)
        
    def get_data(self, path, format=None):
        """
        """
        message = ""
        log_msg = ''
        output = {}
        error_message = ""
        for p_file in path:
            basename  = os.path.basename(p_file)
            root, extension = os.path.splitext(basename)
            if extension.lower() in EXTENSIONS:
                log_msg = "Data Loader cannot "
                log_msg += "load: %s\n" % str(p_file)
                log_msg += "Try File opening ...."
                logging.info(log_msg)
                continue
        
            try:
                temp =  self.loader.load(p_file, format)
                if temp.__class__.__name__ == "list":
                    for item in temp:
                        data = self.parent.create_gui_data(item, p_file)
                        output[data.id] = data
                else:
                    data = self.parent.create_gui_data(temp, p_file)
                    output[data.id] = data
                message = "Loading Data..." + str(p_file) + "\n"
                self.load_update(output=output, message=message)
            except:
                error_message = "Error while loading Data: %s\n" % str(p_file)
                error_message += str(sys.exc_value) + "\n"
                self.load_update(output=output, message=error_message)
                
        message = "Loading Data Complete! "
        message += log_msg
        self.load_complete(output=output, error_message=error_message,
                       message=message, path=path)
            
    def load_update(self, output=None, message=""):
        """
        print update on the status bar
        """
        if message != "" and self.parent is not None:
            wx.PostEvent(self.parent, StatusEvent(status=message,
                                                  type="progress",
                                                   info="warning"))
            
    def load_complete(self, output, message="", error_message="", path=None):
        """
         post message to  status bar and return list of data
        """
        if self.parent is not None:
            wx.PostEvent(self.parent, StatusEvent(status=message,
                                              info="warning",
                                              type="stop"))
        if error_message != "":
            self.load_error(error_message)
        if self.parent is not None:
            self.parent.add_data(data_list=output)
            
    def on_remove(self, event):
        """
        Get a list of item checked and remove them from the treectrl
        Ask the parent to remove reference to this item 
        """
        data_to_remove, theory_to_remove, _ = self.set_data_helper()
        data_key = []
        theory_key = []
        #remove  data from treectrl
        for d_key, item in self.list_cb_data.iteritems():
            data_c, d_i_c, i_c_c, p_c_c, d_p_c, t_c = item
            if data_c.IsChecked():
                self.tree_ctrl.Delete(data_c)
                data_key.append(d_key)
                if d_key in self.list_cb_theory.keys():
                    theory_list_ctrl = self.list_cb_theory[d_key]
                    theory_to_remove += theory_list_ctrl.keys()
        # Remove theory from treectrl       
        for t_key, theory_dict in self.list_cb_theory.iteritems():
            for  key, value in theory_dict.iteritems():
                item, _, _ = value
                if item.IsChecked():
                    self.tree_ctrl.Delete(item)
                    theory_key.append(key)
        #Remove data and related theory references
        for key in data_key:
            del self.list_cb_data[key]
            if key in theory_key:
                del self.list_cb_theory[key]
        #remove theory  references independently of data
        for key in theory_key:
            for t_key, theory_dict in self.list_cb_theory.iteritems():
                if key in theory_dict:
                    del theory_dict[key]
            
        self.parent.remove_data(data_id=data_to_remove,
                                  theory_id=theory_to_remove)
        self.enable_remove()
        
    def on_import(self, event=None):
        """
        Get all select data and set them to the current active perspetive
        """
        data_id, theory_id, state_id = self.set_data_helper()
        self.parent.set_data(data_id)
        self.parent.set_data(data_id=state_id, theory_id=theory_id)
        
    def on_append_plot(self, event=None):
        """
        append plot to plot panel on focus
        """
        self._on_plot_selection()
        data_id, theory_id, state_id = self.set_data_helper()
        self.parent.plot_data(data_id=data_id,  
                              state_id=state_id,
                              theory_id=theory_id,
                              append=True)
   
    def on_plot(self, event=None):
        """
        Send a list of data names to plot
        """
        data_id, theory_id, state_id = self.set_data_helper()
        self.parent.plot_data(data_id=data_id,  
                              state_id=state_id,
                              theory_id=theory_id,
                              append=False)
         
    def on_close_page(self, event=None):
        """
        On close
        """
        if event != None:
            event.Skip()

        # send parent to update menu with no show nor hide action
        self.parent.show_data_panel(action=False)
    
        
    def on_freeze(self, event):
        """
        """
        _, theory_id, state_id = self.set_data_helper()
        self.parent.freeze(data_id=state_id, theory_id=theory_id)
        
    def set_active_perspective(self, name):
        """
        set the active perspective
        """
        self.tctrl_perspective.SetLabel(str(name))
        #perspective_font = self.tctrl_perspective.GetFont()
        #perspective_font.SetWeight(wx.BOLD)
        self.tctrl_perspective.SetClientSize((80,20))#SetFont(perspective_font)
        self.enable_import()
        
    def set_panel_on_focus(self, name):
        """
        set the plot panel on focus
        """
        for key, value in self.parent.plot_panels.iteritems():
            name_plot_panel = str(value.window_caption)
            if name_plot_panel not in self.cb_plotpanel.GetItems():
                self.cb_plotpanel.Append(name_plot_panel, value)
            self.cb_plotpanel.SetStringSelection(name_plot_panel)

 
    def _on_plot_selection(self, event = None):
        """
        On source combobox selection
        """
        if event != None:
            combo = event.GetEventObject()
            event.Skip()
        else:
            combo = self.cb_plotpanel
        selection = combo.GetSelection()

        if combo.GetValue() != 'None':
            panel = combo.GetClientData(selection)
            self.parent.on_set_plot_focus(panel)   
            
    def enable_remove(self):
        """
        enable or disable remove button
        """
        n_t = self.tree_ctrl.GetCount()
        n_t_t = self.tree_ctrl_theory.GetCount()
        
        if n_t + n_t_t <= 0:
            self.bt_remove.Disable()
        else:
            self.bt_remove.Enable()
            
    def enable_import(self):
        """
        enable or disable send button
        """
        if self.tctrl_perspective.GetLabelText() == "No Active Application":
            self.bt_import.Disable()
        else:
            self.bt_import.Enable()


class DataFrame(wx.Frame):
    ## Internal name for the AUI manager
    window_name = "Data Panel"
    ## Title to appear on top of the window
    window_caption = "Data Panel"
    ## Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    ALWAYS_ON = True
    
    def __init__(self, parent=None, owner=None, manager=None,size=(200, 800),
                         list_of_perspective=[],list=[], *args, **kwds):
        kwds['size'] = size
        kwds['id'] = -1
        kwds['title']= "Loaded Data"
        wx.Frame.__init__(self, parent=parent, *args, **kwds)
        self.parent = parent
        self.owner = owner
        self.manager = manager
        self.panel = DataPanel(parent=self, 
                               #size=size,
                               list_of_perspective=list_of_perspective)
     
    def load_data_list(self, list=[]):
        """
        Fill the list inside its panel
        """
        self.panel.load_data_list(list=list)
        
    def layout_perspective(self, list_of_perspective=[]):
        """
        """
        self.panel.layout_perspective(list_of_perspective=list_of_perspective)
    
    
        
    
from dataFitting import Data1D
from dataFitting import Data2D, Theory1D
from data_state import DataState
import sys
class State():
    def __init__(self):
        self.msg = ""
    def __str__(self):
        self.msg = "model mane : model1\n"
        self.msg += "params : \n"
        self.msg += "name  value\n"
        return msg
def set_data_state(data=None, path=None, theory=None, state=None):
    dstate = DataState(data=data)
    dstate.set_path(path=path)
    dstate.set_theory(theory, state)
  
    return dstate
"""'
data_list = [1:('Data1', 'Data1D', '07/01/2010', "theory1d", "state1"), 
            ('Data2', 'Data2D', '07/03/2011', "theory2d", "state1"), 
            ('Data3', 'Theory1D', '06/01/2010', "theory1d", "state1"), 
            ('Data4', 'Theory2D', '07/01/2010', "theory2d", "state1"), 
            ('Data5', 'Theory2D', '07/02/2010', "theory2d", "state1")] 
"""      
if __name__ == "__main__":
    
    app = wx.App()
    try:
        list_of_perspective = [('perspective2', False), ('perspective1', True)]
        data_list = {}
        # state 1
        data = Data2D()
        data.name = "data2"
        data.id = 1
        data.append_empty_process()
        process = data.process[len(data.process)-1]
        process.data = "07/01/2010"
        theory = Data2D()
        theory.id = 34
        theory.name = "theory1"
        path = "path1"
        state = State()
        data_list['1']=set_data_state(data, path,theory, state)
        #state 2
        data = Data2D()
        data.name = "data2"
        data.id = 76
        theory = Data2D()
        theory.id = 78
        theory.name = "CoreShell 07/24/25"
        path = "path2"
        #state3
        state = State()
        data_list['2']=set_data_state(data, path,theory, state)
        data = Data1D()
        data.id = 3
        data.name = "data2"
        theory = Theory1D()
        theory.name = "CoreShell"
        theory.id = 4
        theory.append_empty_process()
        process = theory.process[len(theory.process)-1]
        process.description = "this is my description"
        path = "path3"
        data.append_empty_process()
        process = data.process[len(data.process)-1]
        process.data = "07/22/2010"
        data_list['4']=set_data_state(data, path,theory, state)
        #state 4
        temp_data_list = {}
        data.name = "data5 erasing data2"
        temp_data_list['4'] = set_data_state(data, path,theory, state)
        #state 5
        data = Data2D()
        data.name = "data3"
        data.id = 5
        data.append_empty_process()
        process = data.process[len(data.process)-1]
        process.data = "07/01/2010"
        theory = Theory1D()
        theory.name = "Cylinder"
        path = "path2"
        state = State()
        dstate= set_data_state(data, path,theory, state)
        theory = Theory1D()
        theory.id = 6
        theory.name = "CoreShell"
        dstate.set_theory(theory)
        theory = Theory1D()
        theory.id = 6
        theory.name = "CoreShell replacing coreshell in data3"
        dstate.set_theory(theory)
        data_list['3'] = dstate
        #state 6
        data_list['6']=set_data_state(None, path,theory, state)
        data_list['6']=set_data_state(theory=theory, state=None)
        theory = Theory1D()
        theory.id = 7
        data_list['6']=set_data_state(theory=theory, state=None)
        data_list['7']=set_data_state(theory=theory, state=None)
        window = DataFrame(list=data_list)
        window.load_data_list(list=data_list)
        #window.layout_perspective(list_of_perspective=list_of_perspective)
        window.Show(True)
        window.load_data_list(list=temp_data_list)
    except:
        #raise
        print "error",sys.exc_value
        
    app.MainLoop()  
    
    