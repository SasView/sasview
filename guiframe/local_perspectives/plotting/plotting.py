"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""


import wx
import sys
from sans.guitools.PlotPanel import PlotPanel
from sans.guitools.plottables import Graph
from sans.guicomm.events import EVT_NEW_PLOT

class PanelMenu(wx.Menu):
    plots = None
    graph = None
    
    def set_plots(self, plots):
        self.plots = plots
    
    def set_graph(self, graph):
        self.graph = graph

class View1DPanel(PlotPanel):
    """
        Plot panel for use with the GUI manager
    """
    
    ## Internal name for the AUI manager
    window_name = "plotpanel"
    ## Title to appear on top of the window
    window_caption = "Plot Panel"
    ## Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    ALWAYS_ON = True
    ## Group ID
    group_id = None
    
    def __init__(self, parent, id = -1, color = None,\
        dpi = None, style = wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        """
            Initialize the panel
        """
        PlotPanel.__init__(self, parent, id = id, style = style, **kwargs)
        
        ## Reference to the parent window
        self.parent = parent
        ## Plottables
        self.plots = {}
        
        ## Unique ID (from gui_manager)
        self.uid = None
        
        ## Action IDs for internal call-backs
        self.action_ids = {}
        
        ## Graph        
        self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        self.graph.render(self)
        
    def _onEVT_1DREPLOT(self, event):
        """
            Data is ready to be displayed
            @param event: data event
        """
        #TODO: Check for existence of plot attribute
        
        is_new = True
        if event.plot.name in self.plots.keys():
            # Check whether the class of plottable changed
            if not event.plot.__class__==self.plots[event.plot.name].__class__:
                self.graph.delete(self.plots[event.plot.name])
            else:
                is_new = False
        
        if is_new:
            self.plots[event.plot.name] = event.plot
            self.graph.add(self.plots[event.plot.name])
        else:
            self.plots[event.plot.name].x = event.plot.x    
            self.plots[event.plot.name].y = event.plot.y    
            self.plots[event.plot.name].dy = event.plot.dy  
            if hasattr(event.plot, 'dx') and hasattr(self.plots[event.plot.name], 'dx'):
                self.plots[event.plot.name].dx = event.plot.dx    
 
        
        # Check axis labels
        #TODO: Should re-factor this
        #if event.plot._xunit != self.graph.prop["xunit"]:
        self.graph.xaxis(event.plot._xaxis, event.plot._xunit)
            
        #if event.plot._yunit != self.graph.prop["yunit"]:
        self.graph.yaxis(event.plot._yaxis, event.plot._yunit)
      
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()

    def onContextMenu(self, event):
        """
            1D plot context menu
            @param event: wx context event
        """
        #slicerpop = wx.Menu()
        slicerpop = PanelMenu()
        slicerpop.set_plots(self.plots)
        slicerpop.set_graph(self.graph)
                
        # Option to save the data displayed
        
        #for plot in self.graph.plottables:
        if self.graph.selected_plottable in self.plots:
            plot = self.plots[self.graph.selected_plottable]
            id = wx.NewId()
            name = plot.name
            slicerpop.Append(id, "&Save %s points" % name)
            self.action_ids[str(id)] = plot
            wx.EVT_MENU(self, id, self._onSave)
                
        # Various plot options
        id = wx.NewId()
        slicerpop.Append(id,'&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, id, self.onSaveImage)
        
        
        item_list = self.parent.get_context_menu(self.graph)
        if (not item_list==None) and (not len(item_list)==0):
                slicerpop.AppendSeparator()
                for item in item_list:
                    try:
                        id = wx.NewId()
                        slicerpop.Append(id, item[0], item[1])
                        wx.EVT_MENU(self, id, item[2])
                    except:
                        print sys.exc_value
                        print RuntimeError, "View1DPanel.onContextMenu: bad menu item"
        
        slicerpop.AppendSeparator()
        
        #id = wx.NewId()
        #slicerpop.Append(id, '&Toggle Linear/Log scale')
        #wx.EVT_MENU(self, id, self._onToggleScale)

        if self.graph.selected_plottable in self.plots:
            if self.plots[self.graph.selected_plottable].__class__.__name__=="Theory1D":
                id = wx.NewId()
                slicerpop.Append(id, '&Add errors to data')
                wx.EVT_MENU(self, id, self._on_add_errors)

        id = wx.NewId()
        slicerpop.Append(id, '&Change scale')
        wx.EVT_MENU(self, id, self._onProperties)
        
        id = wx.NewId()
        #slicerpop.AppendSeparator()
        slicerpop.Append(id, '&Reset Graph')
        wx.EVT_MENU(self, id, self.onResetGraph)        

        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
    
    def _on_add_errors(self, evt):
        """
            Compute reasonable errors for a data set without 
            errors and transorm the plottable to a Data1D
        """
        import math
        import numpy
        from sans.guitools.plottables import Data1D
        
        if not self.graph.selected_plottable == None:
            length = len(self.plots[self.graph.selected_plottable].x)
            dy = numpy.zeros(length)
            for i in range(length):
                dy[i] = math.sqrt(self.plots[self.graph.selected_plottable].y[i])
                
            new_plot = Data1D(self.plots[self.graph.selected_plottable].x,
                              self.plots[self.graph.selected_plottable].y,
                              dy=dy)
            new_plot.interactive = True
            new_plot.name = self.plots[self.graph.selected_plottable].name
            label, unit = self.plots[self.graph.selected_plottable].get_xaxis()
            new_plot.xaxis(label, unit)
            label, unit = self.plots[self.graph.selected_plottable].get_yaxis()
            new_plot.yaxis(label, unit)
            
            self.graph.delete(self.plots[self.graph.selected_plottable])
            
            self.graph.add(new_plot)
            self.plots[self.graph.selected_plottable]=new_plot
            
            self.graph.render(self)
            self.subplot.figure.canvas.draw_idle()    
    
    def _onSave(self, evt):
        """
            Save a data set to a text file
            @param evt: Menu event
        """
        import os
        id = str(evt.GetId())
        if id in self.action_ids:         
            
            path = None
            dlg = wx.FileDialog(self, "Choose a file", os.getcwd(), "", "*.txt", wx.SAVE)
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                mypath = os.path.basename(path)
                print path
            dlg.Destroy()
            
            if not path == None:
                out = open(path, 'w')
                has_errors = True
                if self.action_ids[id].dy==None or self.action_ids[id].dy==[]:
                    has_errors = False
                    
                # Sanity check
                if has_errors:
                    try:
                        if len(self.action_ids[id].y) != len(self.action_ids[id].dy):
                            print "Y and dY have different lengths"
                            has_errors = False
                    except:
                        has_errors = False
                
                if has_errors:
                    out.write("<X>   <Y>   <dY>\n")
                else:
                    out.write("<X>   <Y>\n")
                    
                for i in range(len(self.action_ids[id].x)):
                    if has_errors:
                        out.write("%g  %g  %g\n" % (self.action_ids[id].x[i], 
                                                    self.action_ids[id].y[i],
                                                    self.action_ids[id].dy[i]))
                    else:
                        out.write("%g  %g\n" % (self.action_ids[id].x[i], 
                                                self.action_ids[id].y[i]))
                        
                out.close()
    
    
    def _onToggleScale(self, event):
        if self.get_yscale() == 'log':
            self.set_yscale('linear')
        else:
            self.set_yscale('log')
        self.subplot.figure.canvas.draw_idle()    
    
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
            if event.plot._xunit == panel.graph.prop["xunit"] \
            and event.plot._yunit == panel.graph.prop["yunit"]:
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
            new_panel = View1DPanel(self.parent, -1, style=wx.RAISED_BORDER)
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
        