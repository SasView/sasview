


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

class Plugin(PluginBase):
    """
    Plug-in class to be instantiated by the GUI manager
    """
    
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="Plotting", standalone=standalone)
      
        ## Plot panels
        self.plot_panels = []
       
    def is_always_active(self):
        """
        return True is this plugin is always active even if the user is 
        switching between perspectives
        """
        return True
    
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
        self.parent.Bind(EVT_NEW_PLOT, self._on_plot_event)
        # We have no initial panels for this plug-in
        return []
   
    def _on_show_panel(self, event):
        """show plug-in panel"""
        pass
    
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
                    if not event.plot.group_id == None \
                        and event.plot.group_id == panel.group_id:
                        is_available = True
                        panel._onEVT_1DREPLOT(event)
                        self.parent.show_panel(panel.uid)   
                else:
                    # Check that the plot panel has no group ID
                    ## Use a panel with group_id ==None to plot
                    if panel.group_id == None:
                        is_available = True
                        panel._onEVT_1DREPLOT(event)
                        self.parent.show_panel(panel.uid)
        # Create a new plot panel if none was available        
        if not is_available:
            #print"event.plot",hasattr(event.plot,'data')
            if not hasattr(event.plot, 'data'):
                from Plotter1D import ModelPanel1D
                ## get the data representation label of the data to plot
                ## when even the user select "change scale"
                if hasattr(event.plot, "xtransform"):
                    xtransform = event.plot.xtransform
                else:
                    xtransform = None
                    
                if hasattr(event.plot, "ytransform"):
                    ytransform = event.plot.ytransform
                else:
                    ytransform = None
                ## create a plotpanel for 1D Data
                new_panel = ModelPanel1D(self.parent, -1, xtransform=xtransform,
                         ytransform=ytransform, style=wx.RAISED_BORDER)
            else:
                ##Create a new plotpanel for 2D data
                from Plotter2D import ModelPanel2D
                if hasattr(event.plot, "scale"):
                    scale = event.plot.scale
                else:
                    scale = 'log'
                new_panel = ModelPanel2D(self.parent, id = -1,
                                    data2d=event.plot, scale = scale, 
                                    style=wx.RAISED_BORDER)
            ## Set group ID if available
            ## Assign data properties to the new create panel
            group_id_str = ''
            if hasattr(event.plot, "group_id"):
                if not event.plot.group_id == None:
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
        