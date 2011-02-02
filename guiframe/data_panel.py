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
import wx
import sys
import warnings
from wx.lib.scrolledpanel import ScrolledPanel
import  wx.lib.agw.customtreectrl as CT
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import Data2D
from sans.guiframe.panel_base import PanelBase

PANEL_WIDTH = 200

class DataTreeCtrl(CT.CustomTreeCtrl):
    """
    Check list control to be used for Data Panel
    """
    def __init__(self, parent,*args, **kwds):
        kwds['style']= wx.SUNKEN_BORDER|CT.TR_HAS_BUTTONS| CT.TR_HIDE_ROOT|   \
                    CT.TR_HAS_VARIABLE_ROW_HEIGHT|wx.WANTS_CHARS
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
    window_caption = "Data Panel"
    #type of window 
    window_type = "Data Panel"
    ## Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    #ALWAYS_ON = True
    def __init__(self, parent, list=[],list_of_perspective=[],
                 size=(PANEL_WIDTH,560), manager=None, *args, **kwds):
        kwds['size']= size
        ScrolledPanel.__init__(self, parent=parent, *args, **kwds)
        PanelBase.__init__(self)
        self.SetupScrolling()
      
        self.parent = parent
        self.manager = manager
        self.list_of_data = list
        self.list_of_perspective = list_of_perspective
        self.list_rb_perspectives= []
        self.list_cb_data =[]
        self.list_cb_theory =[]
        self.owner = None
        self.do_layout()
       
    def do_layout(self):
        """
        """
        self.define_panel_structure()
        self.layout_selection()
        self.layout_list()
        self.layout_button()
        self.layout_batch()
   
    def define_panel_structure(self):
        """
        Define the skeleton of the panel
        """
        w, h = self.parent.GetSize()
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        self.sizer1.SetMinSize((w/12, h/2))
        self.sizer2 = wx.BoxSizer(wx.VERTICAL)
        self.sizer3 = wx.GridBagSizer(5,5)
        self.sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        #self.sizer3.SetMinSize((w-60, -1))
        
        self.vbox.Add(self.sizer5, 0,wx.EXPAND|wx.ALL,10)
        self.vbox.Add(self.sizer1, 0,wx.EXPAND|wx.ALL,0)
        self.vbox.Add(self.sizer2, 0,wx.EXPAND|wx.ALL,10)
        self.vbox.Add(self.sizer3, 0,wx.EXPAND|wx.ALL,10)
        self.vbox.Add(self.sizer4, 0,wx.EXPAND|wx.ALL,10)
        
        self.SetSizer(self.vbox)
        
    def layout_selection(self):
        """
        """
        select_txt = wx.StaticText(self, -1, 'Selection Options')
        self.selection_cbox = wx.ComboBox(self, -1, style=wx.CB_READONLY)
        list_of_options = ['Select all Data',
                            'Unselect all Data',
                           'Select all Data 1D',
                           'Unselect all Data 1D',
                           'Select all Data 2D',
                           'Unselect all Data 2D' ]
        for option in list_of_options:
            self.selection_cbox.Append(str(option))
        self.selection_cbox.SetValue('None')
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
                    rb = wx.RadioButton(self, -1, perspective_name, style=wx.RB_GROUP)
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
        option = self.selection_cbox.GetValue()
        if option == 'Select all Data':
            print "on select"
            
    def on_set_active_perspective(self, event):
        """
        Select the active perspective
        """
        ctrl = event.GetEventObject()
        
    def layout_button(self):
        """
        Layout widgets related to buttons
        """
        self.bt_import = wx.Button(self, wx.NewId(), "Send To")
        self.bt_import.SetToolTipString("Send set of Data to active perspective")
        wx.EVT_BUTTON(self, self.bt_import.GetId(), self.on_import)
        
        self.bt_append_plot = wx.Button(self, wx.NewId(), "Append Plot To")
        self.bt_append_plot.SetToolTipString("Plot the selected data in the active panel")
        wx.EVT_BUTTON(self, self.bt_append_plot.GetId(), self.on_append_plot)
        
        self.bt_plot = wx.Button(self, wx.NewId(), "New Plot")
        self.bt_plot.SetToolTipString("To trigger plotting")
        wx.EVT_BUTTON(self, self.bt_plot.GetId(), self.on_plot)
        
        self.bt_remove = wx.Button(self, wx.NewId(), "Delete Data")
        self.bt_remove.SetToolTipString("Delete data from the application")
        wx.EVT_BUTTON(self, self.bt_remove.GetId(), self.on_remove)
        
        self.tctrl_perspective = wx.StaticText(self, -1, 'No Active Application')
        self.tctrl_perspective.SetToolTipString("Active Application")
        self.tctrl_plotpanel = wx.StaticText(self, -1, 'No Plot panel on focus')
        self.tctrl_plotpanel.SetToolTipString("Active Plot Panel")
        #self.sizer3.AddMany([(self.bt_import,0, wx.ALL,5),
        #                     (self.bt_append_plot,0, wx.ALL,5),
        #                     (self.bt_plot, 0, wx.ALL,5),
        # (self.bt_remove,0, wx.ALL,5)])
        ix = 0
        iy = 0
        self.sizer3.Add(self.bt_import,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer3.Add(self.tctrl_perspective,(iy, ix),(1,1),
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)      
        ix = 0          
        iy += 1 
        self.sizer3.Add(self.bt_append_plot,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix += 1
        self.sizer3.Add(self.tctrl_plotpanel,(iy, ix),(1,1),
                          wx.EXPAND|wx.ADJUST_MINSIZE, 0)  
        ix = 0          
        iy += 1 
        self.sizer3.Add(self.bt_plot,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        ix = 0          
        iy += 1 
        self.sizer3.Add(self.bt_remove,( iy, ix),(1,1),  
                             wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 15)
        
     
    def layout_batch(self):
        """
        """
       
        self.rb_single_mode = wx.RadioButton(self, -1, 'Single Mode',
                                             style=wx.RB_GROUP)
        self.rb_batch_mode = wx.RadioButton(self, -1, 'Batch Mode')
        
        self.rb_single_mode.SetValue(True)
        self.rb_batch_mode.SetValue(False)
        self.sizer4.AddMany([(self.rb_single_mode,0, wx.ALL,5),
                            (self.rb_batch_mode,0, wx.ALL,5)])
      
    def layout_list(self):
        """
        Add a listcrtl in the panel
        """
        self.tree_ctrl = DataTreeCtrl(parent=self)
        self.tree_ctrl.Bind(CT.EVT_TREE_ITEM_CHECKED, self.on_check_item)
        self.tree_ctrl.Bind(CT.EVT_TREE_ITEM_RIGHT_CLICK, self.on_right_click)
        self.sizer1.Add(self.tree_ctrl,1, wx.EXPAND|wx.ALL, 20)

    def on_right_click(self, event):
        """
        """
        ## Create context menu for data 
        self.popUpMenu = wx.Menu()
        msg = "Edit %s"%str(self.tree_ctrl.GetItemText(event.GetItem()))
        id = wx.NewId()
        self.edit_data_mitem = wx.MenuItem(self.popUpMenu,id,msg,
                                 "Edit meta data")
        wx.EVT_MENU(self, id, self.on_edit_data)
        self.popUpMenu.AppendItem(self.edit_data_mitem)
        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)
        
    def on_edit_data(self, event):
        """
        """
        print "editing data"
        
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
        name = self.tree_ctrl.GetItemText(item)
  
    def load_data_list(self, list):
        """
        
        """
        if not list:
            return
        
        for dstate in list.values():
            data = dstate.get_data()
            if data is None:
                data_name = str(data)
                data_class = "unkonwn"
            else:
                data_name = data.name
            data_class = data.__class__.__name__
            path = dstate.get_path() 
            theory_list = dstate.get_theory()
            theory = None
            if  theory_list:
                theory = theory_list[len(theory_list)-1]
            data_child = None
            for item in self.list_cb_data:
                if self.tree_ctrl.GetItemText(item) == data_name:
                    data_child = item
                    for process in data.process:
                        theory_child = self.tree_ctrl.FindItem(data_child,
                                                        "Available Theories")#,
                        if theory is not None:
                            av_theory_child =self.tree_ctrl.AppendItem(theory_child,
                                                theory.name,ct_type=1, data=theory.id)
                            self.list_cb_theory.append(av_theory_child)
                            av_theory_child_info =self.tree_ctrl.AppendItem(av_theory_child,
                                                     'info')
                            for process in theory.process:
                                info_time_child =self.tree_ctrl.AppendItem(av_theory_child_info,
                                         process.__str__())
                   
                    break
            if data_child is None:
                data_child =self.tree_ctrl.InsertItem(self.tree_ctrl.root,0,
                                                   data_name,ct_type=1, data=data.id)
                cb_data = self.tree_ctrl.GetFirstChild(self.tree_ctrl.root) 
                item, id = cb_data
                item.Check(True)
                self.list_cb_data.append(item)                         
                data_info_child =self.tree_ctrl.AppendItem(data_child, 'info')#,
                                                            #wnd=data_info_txt)
                info_class_child =self.tree_ctrl.AppendItem(data_info_child, 
                                                            'Type: %s'%data_class)
                path_class_child =self.tree_ctrl.AppendItem(data_info_child,
                                                             'Path: %s'%str(path))
                for process in data.process:
                    info_time_child =self.tree_ctrl.AppendItem(data_info_child,process.__str__())
                theory_child =self.tree_ctrl.AppendItem(data_child, "Available Theories")
                
                if  theory_list:
                    theory = theory_list[len(theory_list)-1]
                    if theory is not None:
                        av_theory_child =self.tree_ctrl.AppendItem(theory_child,
                                                    theory.name,ct_type=1)
                        self.list_cb_theory.append(av_theory_child)
                        av_theory_child_info =self.tree_ctrl.AppendItem(av_theory_child,
                                                         'info')
                        for process in theory.process:
                            info_time_child =self.tree_ctrl.AppendItem(av_theory_child_info,
                                             process.__str__())
                   
    def set_data_helper(self):
        """
        """
        data_to_plot = []
        for item in self.list_cb_data:
            if item.IsChecked():
                
               data_to_plot.append(self.tree_ctrl.GetItemPyData(item))
        theory_to_plot = []
        for item in self.list_cb_theory:
            if item.IsChecked():
                theory_to_plot.append(self.tree_ctrl.GetItemPyData(item))
        return data_to_plot, theory_to_plot
    
    def on_remove(self, event):
        data_to_remove, theory_to_remove = self.set_data_helper()
        for item in self.list_cb_data:
            if item.IsChecked()and \
                self.tree_ctrl.GetItemText(item) in data_to_remove:
                self.tree_ctrl.Delete(item)
        for item in self.list_cb_theory:
            if item.IsChecked()and \
                self.tree_ctrl.GetItemText(item) in theory_to_remove:
                self.tree_ctrl.Delete(item)
        delete_all = False
        if data_to_remove:
            delete_all = True
        self.parent.delete_data(data_id=data_to_remove,
                                  theory_id=theory_to_remove,
                                  delete_all=delete_all)
        
    def on_import(self, event=None):
        """
        Get all select data and set them to the current active perspetive
        """
        self.post_helper(plot=False)
       
    def on_append_plot(self, event=None):
        """
        append plot to plot panel on focus
        """
        self.post_helper(plot=True, append=True)
   
    def on_plot(self, event=None):
        """
        Send a list of data names to plot
        """
        self.post_helper(plot=True)
       
    def set_active_perspective(self, name):
        """
        set the active perspective
        """
        self.tctrl_perspective.SetLabel(str(name))
     
    def set_panel_on_focus(self, name):
        """
        set the plot panel on focus
        """
        self.tctrl_plotpanel.SetLabel(str(name))
        
    def post_helper(self, plot=False, append=False):
        """
        """
        data_to_plot, theory_to_plot = self.set_data_helper()
      
        if self.parent is not None:
            self.parent.get_data_from_panel(data_id=data_to_plot, plot=plot,
                                            append=append)


class DataFrame(wx.Frame):
    ## Internal name for the AUI manager
    window_name = "Data Panel"
    ## Title to appear on top of the window
    window_caption = "Data Panel"
    ## Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    ALWAYS_ON = True
    
    def __init__(self, parent=None, owner=None, manager=None,size=(600, 600),
                         list_of_perspective=[],list=[], *args, **kwds):
        #kwds['size'] = size
        kwds['id'] = -1
        kwds['title']= "Loaded Data"
        wx.Frame.__init__(self, parent=parent, *args, **kwds)
        self.parent = parent
        self.owner = owner
        self.manager = manager
        self.panel = DataPanel(parent=self, 
                               size=size,
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
def set_data_state(data, path, theory, state):
    dstate = DataState(data=data)
    dstate.set_path(path=path)
    dstate.set_theory(theory)
    dstate.set_state(state)
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
        data = Data1D()
        data.name = "data1"
        data.id = 1
        #data.append_process()
        #process = data.process[len(data.process)-1]
        #process.data = "07/01/2010"
        theory = Theory1D()
        theory.id = 34
        theory.pseudo_name = "theory1"
        path = "path1"
        state = State()
        data_list['1']=set_data_state(data, path,theory, state)
        
        data = Data1D()
        data.name = "data2"
        data.id = 76
        theory = Theory1D()
        theory.id = 78
        theory.name = "CoreShell 07/24/25"
        theory.pseudo_name = "CoreShell"
        path = "path2"
        state = State()
        data_list['2']=set_data_state(data, path,theory, state)
        data = Data1D()
        data.id = 3
        data.name = "data2"
        theory = Theory1D()
        theory.name = "CoreShell"
        theory.pseudo_name = "CoreShell"
        theory.id = 4
        #theory.append_process()
        #process = theory.process[len(theory.process)-1]
        #process.description = "this is my description"
        path = "path3"
        #data.append_process()
        #process = data.process[len(data.process)-1]
        #process.data = "07/22/2010"
        data_list['4']=set_data_state(data, path,theory, state)
        
        data = Data2D()
        data.name = "data3"
        data.id = 5
        #data.append_process()
        #process = data.process[len(data.process)-1]
        #process.data = "07/01/2010"
        theory = Theory1D()
        theory.pseudo_name = "Cylinder"
        path = "path2"
        state = State()
        dstate= set_data_state(data, path,theory, state)
        theory = Theory1D()
        theory.id = 6
        theory.pseudo_name = "Sphere"
        dstate.set_theory(theory)
        data_list['3']=dstate
        
        window = DataFrame(list=data_list)
        window.load_data_list(list=data_list)
        window.layout_perspective(list_of_perspective=list_of_perspective)
        window.Show(True)
    except:
        #raise
        print "error",sys.exc_value
    app.MainLoop()  
    
    