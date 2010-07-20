


################################################################################
#This software was developed by the University of Tennessee as part of the
#Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
#project funded by the US National Science Foundation. 
#
#See the license text in license.txt
#
#copyright 2008, University of Tennessee
################################################################################

import wx
import sys
from sans.guicomm.events import EVT_NEW_PLOT
from sans.guicomm.events import NewPlotEvent
from sans.guicomm.events import EVT_NEW_LOADED_DATA
from sans.guicomm.events import StatusEvent 


class PlottingDialog(wx.Dialog):
    """
    Dialog to display plotting option
    """
    def __init__(self, parent=None, panel_on_focus=None, list_of_data=[]):
        """
        """
        wx.Dialog.__init__(self, parent=parent,title="Plotting", size=(300, 280))
        self.parent = parent
        self.panel_on_focus = panel_on_focus
        self.list_of_data = list_of_data
        self.define_structure()
        self.layout_plot_on_panel(list_of_data=self.list_of_data)
        self.layout_data_name(list_of_data=self.list_of_data)
        self.layout_button()
        
    def define_structure(self):
        """
        """
        #Dialog interface
        vbox  = wx.BoxSizer(wx.VERTICAL)
        self.sizer_data = wx.BoxSizer(wx.HORIZONTAL)
        
        self.sizer_selection = wx.BoxSizer(wx.VERTICAL)
        self.sizer_button = wx.BoxSizer(wx.HORIZONTAL)
        vbox.Add(self.sizer_data)
        vbox.Add(self.sizer_selection)
        vbox.Add(self.sizer_button)
        self.SetSizer(vbox)
        self.Centre()
        
    def layout_button(self):
        """
        """
        self.bt_ok = wx.Button(self, wx.NewId(), "Ok", (30, 10))
        self.bt_ok.SetToolTipString("plot data")
        wx.EVT_BUTTON(self, self.bt_ok.GetId(), self.on_ok)
        
        self.sizer_button.AddMany([((40,40), 0,
                                     wx.LEFT|wx.ADJUST_MINSIZE, 100 ),
                                     (self.bt_ok, 0, wx.ALL,10)])
        
    def layout_data_name(self, list_of_data=[]):
        """
        """
        self.data_tcl = wx.TextCtrl(self, -1,size=(260,80), style=wx.TE_MULTILINE)
        hint_data = "Data to plot."
        self.data_tcl.SetToolTipString(hint_data)
        self.data_tcl.SetEditable(False)
        for item in list_of_data:
            self.data_tcl.AppendText(item.name+"\n")
            
        self.sizer_data.AddMany([(self.data_tcl, 1, wx.ALL, 10)])
        
    def layout_plot_on_panel(self, list_of_data=[]):
        """
        """
        if len(list_of_data) == 0:
            return
        elif len(list_of_data) ==1:
            self.layout_single_data(list_of_data=list_of_data)
        else:
            self.layout_multiple(list_of_data=list_of_data)
            
    def layout_single_data(self, list_of_data=[]):
        """
        """
        self.sizer_selection.Clear(True)
        if self.panel_on_focus is None and list_of_data < 1:
            return 
        else:
            name = "Plot data on new panel"
            self.rb_single_data_panel = wx.RadioButton(self, -1,name, 
                                                    style=wx.RB_GROUP)   
            msg = "Each data will be plotted separately on a new panel"
            self.rb_single_data_panel.SetToolTipString(msg)
            self.rb_single_data_panel.SetValue(True)
            self.Bind(wx.EVT_RADIOBUTTON, self.on_choose_panel, 
                                id=self.rb_single_data_panel.GetId())
            self.rb_panel_on_focus = wx.RadioButton(self, -1,"No Panel on Focus")
            msg = "All Data will be appended to panel on focus"
            self.rb_panel_on_focus.SetToolTipString(msg)
            self.rb_panel_on_focus.Disable()
            self.Bind(wx.EVT_RADIOBUTTON, self.on_choose_panel, 
                                id=self.rb_panel_on_focus.GetId())
            if self.panel_on_focus is not  None:
                self.rb_panel_on_focus.Enable()
                self.rb_panel_on_focus.SetLabel(str(panel.window_name))
            self.sizer_selection.AddMany([(self.rb_single_data_panel,
                                            1, wx.ALL, 10),
                     (self.rb_panel_on_focus,1, wx.ALL, 10)])
            
    def layout_multiple(self, list_of_data=[]):
        """
        """
        self.sizer_selection.Clear(True)
        if self.panel_on_focus is None and list_of_data <= 1:
            return 
        name = "Plot each data separately"
        self.rb_single_data_panel = wx.RadioButton(self, -1,name, 
                                                    style=wx.RB_GROUP)
        msg = "Each data will be plotted separately on a new panel"
        self.rb_single_data_panel.SetToolTipString(msg)
        self.rb_single_data_panel.SetValue(True)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_choose_panel, 
                            id=self.rb_single_data_panel.GetId())
        name = "Append all to new panel"
        self.rb_new_panel = wx.RadioButton(self, -1,name)
        msg = "All Data will be appended to a new panel"
        self.rb_new_panel.SetToolTipString(msg)
        self.Bind(wx.EVT_RADIOBUTTON, self.on_choose_panel, 
                            id=self.rb_new_panel.GetId())
        self.rb_panel_on_focus = wx.RadioButton(self, -1,"No Panel on Focus")
        msg = "All Data will be appended to panel on focus"
        self.rb_panel_on_focus.SetToolTipString(msg)
        self.rb_panel_on_focus.Disable()
        self.Bind(wx.EVT_RADIOBUTTON, self.on_choose_panel, 
                            id=self.rb_panel_on_focus.GetId())
        if self.panel_on_focus is not  None:
            self.rb_panel_on_focus.Enable()
            self.rb_panel_on_focus.SetLabel(str(panel.window_name))
       
        self.sizer_selection.AddMany([(self.rb_single_data_panel,
                                            1, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10),
                (self.rb_new_panel, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10),
                (self.rb_panel_on_focus, 1, wx.LEFT|wx.RIGHT|wx.BOTTOM, 10),])
    def on_ok(self, event):
        """
        """
    def on_choose_panel(self, event):
        """
        """
class Plugin:
    """
    Plug-in class to be instantiated by the GUI manager
    """
    
    def __init__(self):
        """
        Initialize the plug-in
        """
        ## Plug-in name
        self.sub_menu = "Plotting"
        
        ## Reference to the parent window
        self.parent = None
        
        ## List of panels for the simulation perspective (names)
        self.perspective = []
        
        ## Plot panels
        self.plot_panels = []
       
    def populate_menu(self, id, parent):
        """
        Create a 'Plot' menu to list the panels
        available for displaying
        
        :param id: next available unique ID for wx events
        :param parent: parent window
        
        """
        self.menu = wx.Menu()
        
        self.menu.Append(wx.NewId(), "No plot available", 
                             "No plot available")
        self.menu.FindItemByPosition(0).Enable(False)
        return [(id, self.menu, "Plot")]
    
    def get_panels(self, parent):
        """
        Create and return a list of panel objects
        """
        ## Save a reference to the parent
        self.parent = parent
        # Connect to plotting events
        self.parent.Bind(EVT_NEW_LOADED_DATA, self._on_plot)
        self.parent.Bind(EVT_NEW_PLOT, self._on_plot_event)
        # We have no initial panels for this plug-in
        return []
   
    def get_perspective(self):
        """
        Get the list of panel names for this perspective
        """
        return self.perspective
    
    def on_perspective(self, event):
        """
            Call back function for the perspective menu item.
            We notify the parent window that the perspective
            has changed.
            @param event: menu event
        """
        self.parent.set_perspective(self.perspective)
    
    def post_init(self):
        """
        Post initialization call back to close the loose ends
        [Somehow openGL needs this call]
        """
        pass
    
    def _on_show_panel(self, event):
        """show plug-in panel"""
        pass
    
    def _on_plot(self, event):
        """
        check the contains of event.
        if it is a list of data to plot plot each one at the time
        """
        list_of_data1d = []
        if hasattr(event, "plots"):
            for plot, path in event.plots:
                print "plotting _on_plot"
                if plot.__class__.__name__ == "Data2D":
                    wx.PostEvent(self.parent, 
                                 NewPlotEvent(plot=plot, title=plot.name))
                else:
                    list_of_data1d.append((plot, path))
  
    def _on_plot_event(self, event):
        """
        A new plottable is being shipped to the plotting plug-in.
        Check whether we have a panel to put in on, or create
        a new one
        
        :param event: EVT_NEW_PLOT event
        
        """
        # Check whether we already have a graph with the same units
        # as the plottable we just received. 
        
        is_available = False
        for panel in self.plot_panels:
            if event.plot._xunit == panel.graph.prop["xunit_base"] \
            and event.plot._yunit == panel.graph.prop["yunit_base"]:
                if hasattr(event.plot, "group_id"):
                    ## if same group_id used the same panel to plot
                    if not event.plot.group_id==None \
                        and event.plot.group_id==panel.group_id:
                        is_available = True
                        
                        panel._onEVT_1DREPLOT(event)
                        self.parent.show_panel(panel.uid)   
                else:
                    # Check that the plot panel has no group ID
                    ## Use a panel with group_id ==None to plot
                    
                    if panel.group_id==None:
                        is_available = True
                        panel._onEVT_1DREPLOT(event)
                        self.parent.show_panel(panel.uid)
        
        # Create a new plot panel if none was available        
        if not is_available:
            #print"event.plot",hasattr(event.plot,'data')
            if not hasattr(event.plot,'data'):
                from Plotter1D import ModelPanel1D
                ## get the data representation label of the data to plot
                ## when even the user select "change scale"
                if hasattr(event.plot,"xtransform"):
                    xtransform = event.plot.xtransform
                else:
                    xtransform =None
                    
                if hasattr(event.plot,"ytransform"):
                    ytransform=  event.plot.ytransform
                else:
                    ytransform=None
                ## create a plotpanel for 1D Data
                new_panel = ModelPanel1D(self.parent, -1,xtransform=xtransform,
                                         ytransform=ytransform, style=wx.RAISED_BORDER)

            else:
                ##Create a new plotpanel for 2D data
                from Plotter2D import ModelPanel2D
                new_panel = ModelPanel2D(self.parent, id = -1, data2d=event.plot,style=wx.RAISED_BORDER)
            
            ## Set group ID if available
            ## Assign data properties to the new create panel
            group_id_str = ''
            if hasattr(event.plot, "group_id"):
                if not event.plot.group_id==None:
                    new_panel.group_id = event.plot.group_id
                    group_id_str = ' [%s]' % event.plot.group_id
            
            if hasattr(event, "title"):
                new_panel.window_caption = event.title
                new_panel.window_name = event.title
               
            event_id = self.parent.popup_panel(new_panel)
            #remove the default item in the menu
            if len(self.plot_panels) == 0:
                self.menu.RemoveItem(self.menu.FindItemByPosition(0))
                
            self.menu.Append(event_id, new_panel.window_caption, 
                             "Show %s plot panel" % new_panel.window_caption)
            # Set UID to allow us to reference the panel later
            new_panel.uid = event_id
            # Ship the plottable to its panel
            new_panel._onEVT_1DREPLOT(event)
            self.plot_panels.append(new_panel)        
            
        return
        
class Data(object): 
    def __init__(self, name):
        self.name = str(name)
class MyApp(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        list =[Data(name="Data1D")]#,
                                   # Data(name="Data2D"),Data(name="Data3D")]
        dialog = PlottingDialog(list_of_data=list)
        if dialog.ShowModal() == wx.ID_OK:
            pass
        dialog.Destroy()
        
        return 1
  
# end of class MyApp

if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()      