


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
from sans.guiframe.events import EVT_NEW_PLOT
from sans.guiframe.events import StatusEvent 
from sans.guiframe.plugin_base import PluginBase
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import Data2D

class Plugin(PluginBase):
    """
    Plug-in class to be instantiated by the GUI manager
    """
    
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="Plotting", standalone=standalone)
      
        ## Plot panels
        self.plot_panels = []
        self.new_plot_panels = {}
        self._panel_on_focus = None
     
    def set_panel_on_focus(self, panel):
        """
        """
        self._panel_on_focus = panel
        
    def is_always_active(self):
        """
        return True is this plugin is always active even if the user is 
        switching between perspectives
        """
        return True
    
    def populate_menu(self, parent):
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
        return [(self.menu, "Plot")]
    
    def get_panels(self, parent):
        """
        Create and return a list of panel objects
        """
        ## Save a reference to the parent
        self.parent = parent
        # Connect to plotting events
        self.parent.Bind(EVT_NEW_PLOT, self._on_plot_event)
        # We have no initial panels for this plug-in
        return []
   
    def _on_show_panel(self, event):
        """show plug-in panel"""
        pass
    
    #def _on_plot_event(self, event):
    #     return profile(self.tested_on_plot_event, event)
    
    def _on_plot_event(self, event):
        """
        A new plottable is being shipped to the plotting plug-in.
        Check whether we have a panel to put in on, or create
        a new one
        
        :param event: EVT_NEW_PLOT event
        
        """
        if hasattr(event, 'remove'):
            group_id = event.group_id
            id = event.id
            if group_id in self.new_plot_panels.keys():
                panel = self.new_plot_panels[group_id]
                panel.remove_data_by_id(id=id)
            else:
                msg = "Panel with GROUP_ID: %s canot be located" % str(group_id)
                raise ValueError, msg
            return
        # Check whether we already have a graph with the same units
        # as the plottable we just received. 
        data = event.plot
        
        group_id_list = data.group_id
        group_id = None
        if group_id_list:
            group_id = group_id_list[len(group_id_list)-1]
        if group_id in self.new_plot_panels.keys():
            panel = self.new_plot_panels[group_id]
            _, x_unit =  data.get_xaxis()
            _, y_unit =  data.get_yaxis()
           
            if x_unit != panel.graph.prop["xunit"] \
                or  y_unit != panel.graph.prop["yunit"]:
                msg = "Cannot add %s" % str(data.name)
                msg += " to panel %s\n" % str(panel.window_caption)
                msg += "Please edit %s's units, labels" % str(data.name)
                raise ValueError, msg
            else:
                panel.plot_data( data)
                self.parent.show_panel(panel.uid)   
        else:
            # Create a new plot panel if none was available        
            if issubclass(data.__class__, Data1D):
                from Plotter1D import ModelPanel1D
                ## get the data representation label of the data to plot
                ## when even the user select "change scale"
                xtransform = data.xtransform
                ytransform = data.ytransform
                ## create a plotpanel for 1D Data
                new_panel = ModelPanel1D(self.parent, -1, xtransform=xtransform,
                         ytransform=ytransform, style=wx.RAISED_BORDER)
                new_panel.set_manager(self)
                new_panel.group_id = group_id
            elif issubclass(data.__class__, Data2D):
                ##Create a new plotpanel for 2D data
                from Plotter2D import ModelPanel2D
                scale = data.scale
                new_panel = ModelPanel2D(self.parent, id = -1,
                                    data2d=event.plot, scale = scale, 
                                    style=wx.RAISED_BORDER)
                new_panel.set_manager(self)
                new_panel.group_id = group_id
            else:
                msg = "Plotting received unexpected"
                msg += " data type : %s" % str(data.__class__)
                raise ValueError, msg
            ## Set group ID if available
            ## Assign data properties to the new create panel
            title = data.title
            new_panel.window_caption = title
            new_panel.window_name = title
            event_id = self.parent.popup_panel(new_panel)
            #remove the default item in the menu
            if len(self.new_plot_panels) == 0:
                self.menu.RemoveItem(self.menu.FindItemByPosition(0))
            self.menu.Append(event_id, new_panel.window_caption, 
                             "Show %s plot panel" % new_panel.window_caption)
            # Set UID to allow us to reference the panel later
            new_panel.uid = event_id
            # Ship the plottable to its panel
            new_panel.plot_data(data)
            self.plot_panels.append(new_panel)       
            self.new_plot_panels[new_panel.group_id] = new_panel
            
        return

def profile(fn, *args, **kw):
    import cProfile, pstats, os
    global call_result
    def call():
        global call_result
        call_result = fn(*args, **kw)
    cProfile.runctx('call()', dict(call=call), {}, 'profile.txt')
    stats = pstats.Stats('profile.txt')
    stats.sort_stats('time')
    #stats.sort_stats('calls')
    stats.print_stats()
    #os.unlink('profile.out')
    return call_result

   