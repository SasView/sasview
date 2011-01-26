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
#import warnings
from wx.lib.scrolledpanel import ScrolledPanel
import  wx.lib.mixins.listctrl  as  listmix
#from sans.guicomm.events import NewPlotEvent

class CheckListCtrl(wx.ListCtrl, listmix.CheckListCtrlMixin, 
                    listmix.ListCtrlAutoWidthMixin):
    """
    Check list control to be used for Data Panel
    """
    def __init__(self, parent, *args, **kwds):
        kwds['style'] = wx.LC_REPORT|wx.SUNKEN_BORDER
        wx.ListCtrl.__init__(self, parent, -1, *args, **kwds)
        listmix.CheckListCtrlMixin.__init__(self)
        listmix.ListCtrlAutoWidthMixin.__init__(self)
        
class DataPanel(ScrolledPanel):
    """
    This panel displays data available in the application and widgets to 
    interact with data.
    """
    def __init__(self, parent, list=None, list_of_perspective=[],
                    *args, **kwds):
        ScrolledPanel.__init__(self, parent=parent, *args, **kwds)
        self.SetupScrolling()
        self.parent = parent
        self.manager = None
        self.owner = None
        if list is None:
            list = []
        self.list_of_data = list
        self.perspectives = []
        #layout widgets
        self.sizer4 = None
        self.sizer5 = None
        self.sizer1 = None
        self.sizer2 = None
        self.sizer3 = None
        self.sizer4 = None
        self.sizer5 = None
        self.vbox = None
        self.list_ctrl = None
        self.boxsizer_2_2 = None
        self.cb_select_data1d = None
        self.cb_select_data2d = None
        self.cb_select_all = None
        self.cb_theory = None
        self.bt_import = None
        self.bt_plot = None
        self.bt_close = None
        
        self.define_panel_structure()
        self.layout_list()
        self.layout_selection()
        self.layout_perspective(list_of_perspective=list_of_perspective)
        self.load_list()
        self.layout_theory()
        self.layout_button()
        
    def define_panel_structure(self):
        """
        Define the skeleton of the panel
        """
        self.vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer1 = wx.BoxSizer(wx.VERTICAL)
        
        box_description_2 = wx.StaticBox(self, -1, "Selection Patterns")
        self.boxsizer_2 = wx.StaticBoxSizer(box_description_2, wx.HORIZONTAL)
        box_description_2_2 = wx.StaticBox(self, -1, "Set Active Perspective")
        self.boxsizer_2_2 = wx.StaticBoxSizer(box_description_2_2,
                                              wx.HORIZONTAL)
       
        w, h = self.parent.GetSize()
        self.sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer2.Add(self.boxsizer_2, 1, wx.ALL, 10)
        self.sizer2.Add(self.boxsizer_2_2, 1, wx.ALL, 10)
        
        box_description_3 = wx.StaticBox(self, -1,
                                         "Import to Active perspective")
        self.boxsizer_3 = wx.StaticBoxSizer(box_description_3, wx.HORIZONTAL)
        self.sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer3.Add(self.boxsizer_3, 1, wx.ALL, 10)
        
        self.sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer1.SetMinSize((w-10, h/3))
        self.sizer2.SetMinSize((w-10, -1))
        self.sizer3.SetMinSize((w-10, -1))
        self.sizer4.SetMinSize((w-10, -1))
        self.sizer5.SetMinSize((w-10, -1))
        self.vbox.Add(self.sizer1)
        self.vbox.Add(self.sizer2)
        self.vbox.Add(self.sizer3)
        self.vbox.Add(wx.StaticLine(self, -1), 0, wx.EXPAND, 0)
        self.vbox.Add(self.sizer4)
        self.vbox.Add(self.sizer5)
        self.SetSizer(self.vbox)
        
    def GetListCtrl(self):
        """
        """
        return self.list_ctrl
    
    def layout_list(self):
        """
        Add a listcrtl in the panel
        """
        self.list_ctrl = CheckListCtrl(parent=self)
        
        self.list_ctrl.InsertColumn(0, 'Name')
        self.list_ctrl.InsertColumn(1, 'Type')
        self.list_ctrl.InsertColumn(2, 'Date Modified')
        self.sizer1.Add(self.list_ctrl, 1, wx.EXPAND|wx.ALL, 10)
        
    def layout_perspective(self, list_of_perspective=None):
        """
        Layout widgets related to the list of plug-ins of the gui_manager 
        """
        if list_of_perspective is None:
            list_of_perspective = []
        self.boxsizer_2_2.Clear(True)
        self.perspectives = []
        sizer = wx.GridBagSizer(5, 5)
        
        if list_of_perspective:
            item = list_of_perspective[0].sub_menu
            rb = wx.RadioButton(self, -1, item, style=wx.RB_GROUP)
            rb.SetToolTipString("Data will be applied to this perspective")
            if hasattr(item, "set_default_perspective"):
                if item.set_default_perspective():
                    rb.SetValue(item.set_default_perspective())
            self.Bind(wx.EVT_RADIOBUTTON, self.on_set_active_perspective,
                                                 id=rb.GetId())
            self.perspectives.append(rb)
            ix = 0 
            iy = 0
            sizer.Add(rb, (iy, ix), (1, 1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
            for index in range(1, len(list_of_perspective)):
                item = list_of_perspective[index].sub_menu
                rb = wx.RadioButton(self, -1, item)
                rb.SetToolTipString("Data will be applied to this perspective")
                self.Bind(wx.EVT_RADIOBUTTON, self.on_set_active_perspective, 
                                        id=rb.GetId())
                self.perspectives.append(rb)
                iy += 1
                sizer.Add(rb, (iy, ix), (1, 1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
                if hasattr(item,"set_default_perspective"):
                    if item.set_default_perspective():
                        rb.SetValue(item.set_default_perspective())
        else:
            rb = wx.RadioButton(self, -1, 'No Perspective',
                                                      style=wx.RB_GROUP)
            rb.SetValue(True)
            rb.Disable()
            ix = 0 
            iy = 0
            sizer.Add(rb, (iy, ix), (1, 1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        self.boxsizer_2_2.Add(sizer)
      
    def layout_selection(self):
        """
        Layout widgets related to selection patterns
        """
        sizer = wx.GridBagSizer(5, 5)
        self.cb_select_data1d = wx.CheckBox(self, -1, 
                                "Select/Unselect Data 1D", (10, 10))
        msg_data1d = "To check/uncheck to select/unselect all Data 1D"
        self.cb_select_data1d.SetToolTipString(msg_data1d)
        wx.EVT_CHECKBOX(self, self.cb_select_data1d.GetId(),
                                        self.on_select_all_data1d)
        self.cb_select_data2d = wx.CheckBox(self, -1, 
                               "Select/Unselect all Data 2D", (10, 10))
        msg_data2d = "To check/uncheck to select/unselect all Data 2D"
        self.cb_select_data2d.SetToolTipString(msg_data2d)
        wx.EVT_CHECKBOX(self, self.cb_select_data2d.GetId(),
                         self.on_select_all_data2d)
        self.cb_select_theory1d = wx.CheckBox(self, -1, 
                                    "Select/Unselect all Theory 1D", (10, 10))
        msg_theory1d = "To check/uncheck to select/unselect all Theory 1D"
        self.cb_select_theory1d.SetToolTipString(msg_theory1d)
        wx.EVT_CHECKBOX(self, self.cb_select_theory1d.GetId(),
                         self.on_select_all_theory1d)
        self.cb_select_theory2d = wx.CheckBox(self, -1, 
                                    "Select/Unselect all Theory 2D", (10, 10))
        msg_theory2d = "To check/uncheck to select/unselect all Theory 2D"
        self.cb_select_theory2d.SetToolTipString(msg_theory2d)
        wx.EVT_CHECKBOX(self, self.cb_select_theory2d.GetId(),
                                self.on_select_all_theory2d)
        self.cb_select_all = wx.CheckBox(self, -1, "Select/Unselect all",
                                         (10, 10))
        msg_select_all = "To check/uncheck to  select/unselect all"
        self.cb_select_all.SetToolTipString(msg_select_all)
        wx.EVT_CHECKBOX(self, self.cb_select_all.GetId(), self.on_select_all)
        iy = 0
        ix = 0
        sizer.Add(self.cb_select_data1d, (iy, ix), (1, 1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        iy += 1
        sizer.Add(self.cb_select_data2d, (iy, ix), (1, 1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        iy += 1
        sizer.Add(self.cb_select_theory1d, (iy, ix), (1, 1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        iy += 1
        sizer.Add( self.cb_select_theory2d, (iy, ix), (1, 1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        iy += 1
        sizer.Add(self.cb_select_all,(iy, ix), (1, 1),
                           wx.LEFT|wx.EXPAND|wx.ADJUST_MINSIZE, 10)
        self.boxsizer_2.Add(sizer)
       
    def layout_theory(self):
        """
        Layout widget related to theory to import
        """
        msg = "Import the Selected Theory\n"
        msg += "to active perspective."
        st_description = wx.StaticText(self, -1, msg)
        self.cb_theory = wx.ComboBox(self, -1)
        wx.EVT_COMBOBOX(self.cb_theory,-1, self.on_select_theory) 
        
        self.boxsizer_3.AddMany([(st_description, 0, wx.ALL, 10),
                             (self.cb_theory, 0, wx.ALL, 10)])
        self.load_theory(list=[])
        
    def layout_button(self):
        """
        Layout widgets related to buttons
        """
        self.bt_import = wx.Button(self, wx.NewId(), "Import", (30, 10))
        hint_msg = "Import set of Data to active perspective"
        self.bt_import.SetToolTipString(hint_msg)
        wx.EVT_BUTTON(self, self.bt_import.GetId(), self.on_import)
        
        self.bt_plot = wx.Button(self, wx.NewId(), "Plot", (30, 10))
        self.bt_plot.SetToolTipString("To trigger plotting")
        wx.EVT_BUTTON(self, self.bt_plot.GetId(), self.on_plot)
        
        self.bt_close = wx.Button(self, wx.NewId(), "Close", (30, 10))
        self.bt_close.SetToolTipString("close the current window")
        wx.EVT_BUTTON(self, self.bt_close.GetId(), self.on_close)
        
        self.sizer5.AddMany([((40, 40), 0, wx.LEFT|wx.ADJUST_MINSIZE, 180),
                             (self.bt_import, 0, wx.ALL,5),
                             (self.bt_plot, 0, wx.ALL,5),
                             (self.bt_close, 0, wx.ALL, 5 )])
        
    def set_manager(self, manager):
        """
        :param manager: object responsible of filling on empty the listcrtl of 
        this panel. for sansview manager is data_manager
        """
        self.manager = manager
        
    def set_owner(self, owner):
        """
         :param owner: is the main widget creating this frame
         for sansview owner is gui_manager
        """
        self.owner = owner
        
    def load_theory(self, list=None):
        """
        Recieve a list of theory name and fill the combobox with that list
        """
        if list is None:
            list = []
        for theory in list:
            self.cb_theory.Append(theory)
        if list:
            self.cb_theory.Enable()
        else:
            self.cb_theory.Disable()
            
    def load_list(self, list=None):
        """
        Get a list of turple and store each string in these turples in 
        the column of the listctrl.
        
        :param list: list of turples containing string only. 
        """
        if list is None:
            return
        for i in list:
            index = self.list_ctrl.InsertStringItem(sys.maxint, i[0])
            self.list_ctrl.SetStringItem(index, 1, i[1])
            self.list_ctrl.SetStringItem(index, 2, i[2])
       
    def set_perspective(self, sub_menu):
        """
        Receive the name of the current perspective and set 
        the active perspective
        """
        for item in self.perspectives:
            if item.GetLabelText()== sub_menu:
                item.SetValue(True)
            else:
                item.SetValue(False)
                
    def select_data_type(self, type='Data1D', check=False):
        """
        check item in the list according to a type.
        :param check: if check true set checkboxes toTrue else to False
        :param type: type of data to select
        """
        num = self.list_ctrl.GetItemCount()
        for index in range(num):
            if self.list_ctrl.GetItem(index, 1).GetText() == type:
                self.list_ctrl.CheckItem(index, check)
                
    def on_select_all_data1d(self, event):
        """
        check/ uncheck list of all data 1D
        """
        ctrl = event.GetEventObject()
        self.select_data_type(type='Data1D', check=ctrl.GetValue())
        
    def on_select_all_data2d(self, event):
        """
        check/ uncheck list of all data 2D
        """
        ctrl = event.GetEventObject()
        self.select_data_type(type='Data2D', check=ctrl.GetValue())
        
    def on_select_all_theory1d(self, event):
        """
        check/ uncheck list of all theory 1D
        """
        ctrl = event.GetEventObject()
        self.select_data_type(type='Theory1D', check=ctrl.GetValue())
        
    def on_select_all_theory2d(self, event):
        """
        check/ uncheck list of all theory 2D
        """
        ctrl = event.GetEventObject()
        self.select_data_type(type='Theory2D', check=ctrl.GetValue())
        
    def on_select_all(self, event):
        """
        Check or uncheck all data listed 
        """
        ctrl = event.GetEventObject()
        self.cb_select_data1d.SetValue(ctrl.GetValue())
        self.cb_select_data2d.SetValue(ctrl.GetValue())
        self.cb_select_theory1d.SetValue(ctrl.GetValue())
        self.cb_select_theory2d.SetValue(ctrl.GetValue())
        num = self.list_ctrl.GetItemCount()
        for i in range(num):
            self.list_ctrl.CheckItem(i, ctrl.GetValue())
      
    def on_select_theory(self, event):
        """
        Select the theory to import in the active perspective
        """
        
    def on_set_active_perspective(self, event):
        """
        Select the active perspective
        """
        ctrl = event.GetEventObject()
        
    def set_data_helper(self):
        """
        """
        data_to_plot = []
        
        num = self.list_ctrl.GetItemCount()
        for index in range(num):
            if self.list_ctrl.IsChecked(index):
                data_to_plot.append(self.list_ctrl.GetItemText(index))
        return data_to_plot
    
    def on_import(self, event=None):
        """
        Get all select data and set them to the current active perspetive
        """
        data_to_plot = self.set_data_helper()
        current_perspective = None
        if self.perspectives:
            for item in self.perspectives:
                if item.GetValue():
                    current_perspective = item.GetLabelText()
        if self.manager is not None:
            self.manager.post_data(data_name_list=data_to_plot,
                        perspective=current_perspective, plot=False)
       
    def on_plot(self, event=None):
        """
        Send a list of data names to plot
        """
        data_to_plot = self.set_data_helper()
        if self.manager is not None:
            self.manager.post_data(data_name_list=data_to_plot, plot=True)
      
    def on_close(self, event):
        """
        Close the current panel's parent
        """
        self.parent._onClose()
        
    
from sans.guiframe.dataFitting import Data1D
from DataLoader.loader import Loader
            
list  = Loader().load('latex_smeared.xml')
data_list = [('Data1', list[0], '07/01/2010'), 
            ('Data2', list[1], '07/03/2011'),
            ('Data3', 'Theory1D', '06/01/2010'),
            ('Data4', 'Theory2D', '07/01/2010'),
            ('Data5', 'Theory2D', '07/02/2010')]

class DataFrame(wx.Frame):
    def __init__(self, parent=None, owner=None,
                 list_of_perspective=None, list=None,
                  manager=None, *args, **kwds):
        kwds['size'] = (500, 500)
        kwds['id'] = -1
        kwds['title'] = "Loaded Data"
        wx.Frame.__init__(self, parent=parent, *args, **kwds)
        self.parent = parent
        self.owner = owner
        self.manager = manager
        self.panel = DataPanel(parent=self, 
                               list_of_perspective=list_of_perspective)
        self.panel.load_list(list=list)
        wx.EVT_CLOSE(self, self._onClose)
        
    def set_owner(self, owner):
        """
        :param owner: is the main widget creating this frame
         for sansview owner is gui_manager
        """
        self.owner = owner
        self.panel.set_owner(owner=self.owner)
        
    def set_manager(self, manager):
        """
        :param manager: object responsible of filling on empty the listcrtl of 
         this panel. for sansview manager is data_manager
         
        """
        self.manager = manager
        self.panel.set_manager(manager=self.manager)
        
    def load_list(self, list=None):
        """
        Fill the list inside its panel
        """
        self.panel.load_list(list=list)
        
    def layout_perspective(self, list_of_perspective=None):
        """
        fill the panel with list of perspective
        """
        self.panel.layout_perspective(list_of_perspective=list_of_perspective)
    
    def set_perspective(self, sub_menu):
        """
        Receive the name of the current perspective and set 
        the active perspective
        """
        self.panel.set_perspective(sub_menu=sub_menu)
        
    def _onClose(self, event=None):
        """
        this frame can only be hidden unless the application destroys it
        """
        self.Hide()
      
if __name__ == "__main__":
    app = wx.App()
    window = DataFrame(list=data_list)
    window.Show(True)
    app.MainLoop()  
    
    