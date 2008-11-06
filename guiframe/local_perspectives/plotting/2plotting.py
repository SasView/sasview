"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""


import wx
import sys
#import pylab
from sans.guicomm.events import EVT_NEW_PLOT


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
            @param id: next available unique ID for wx events
            @param parent: parent window
        """
        self.menu = wx.Menu()
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
        print "_on_show_panel"
    
    def _on_plot_event(self, event):
        """
            A new plottable is being shipped to the plotting plug-in.
            Check whether we have a panel to put in on, or create
            a new one
            @param event: EVT_NEW_PLOT event
        """
        # Check whether we already have a graph with the same units
        # as the plottable we just received. 
        is_available = False
        for panel in self.plot_panels:
            if event.plot._xunit == panel.graph.prop["xunit_base"] \
            and event.plot._yunit == panel.graph.prop["yunit_base"]:
                if hasattr(event.plot, "group_id"):
                    if not event.plot.group_id==None \
                        and event.plot.group_id==panel.group_id:
                        is_available = True
                        panel._onEVT_1DREPLOT(event)
                        self.parent.show_panel(panel.uid)
                else:
                    # Check that the plot panel has no group ID
                    if panel.group_id==None:
                        is_available = True
                        panel._onEVT_1DREPLOT(event)
                        self.parent.show_panel(panel.uid)
        
        # Create a new plot panel if none was available        
        if not is_available:
            if event.plot.__class__.__name__=='Data1D':
                from DataPanel import View1DPanel1D
                new_panel = View1DPanel1D(self.parent, -1, style=wx.RAISED_BORDER)
            if event.plot.__class__.__name__=='Data2D':
                from DataPanel import View1DPanel2D
               
                new_panel = View1DPanel2D(self.parent, -1,style=wx.RAISED_BORDER)
            #if event.plot.__class__.__name__=='Theory2D':
            else:
                from DataPanel import View1DModelPanel2D
                new_panel = View1DModelPanel2D(self.parent, -1, style=wx.RAISED_BORDER)
            # Set group ID if available
            group_id_str = ''
            if hasattr(event.plot, "group_id"):
                if not event.plot.group_id==None:
                    new_panel.group_id = event.plot.group_id
                    group_id_str = ' [%s]' % event.plot.group_id
            
            if hasattr(event, "title"):
                new_panel.window_caption = event.title
                new_panel.window_name = event.title
                #new_panel.window_caption = event.title+group_id_str
                #new_panel.window_name = event.title+group_id_str
            
            event_id = self.parent.popup_panel(new_panel)
            self.menu.Append(event_id, new_panel.window_caption, 
                             "Show %s plot panel" % new_panel.window_caption)
            # Set UID to allow us to reference the panel later
            new_panel.uid = event_id
            # Ship the plottable to its panel
            new_panel._onEVT_1DREPLOT(event)
            self.plot_panels.append(new_panel)        
            
        return
        