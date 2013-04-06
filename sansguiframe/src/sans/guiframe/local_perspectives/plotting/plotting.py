


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
from sans.guiframe.events import EVT_PLOT_QRANGE
from sans.guiframe.events import StatusEvent 
from sans.guiframe.events import DeletePlotPanelEvent
from sans.guiframe.plugin_base import PluginBase
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import Data2D

DEFAULT_MENU_ITEM_LABEL = "No graph available"
DEFAULT_MENU_ITEM_ID = wx.NewId()

IS_WIN = True    
if sys.platform.count("win32")==0:
    if int(str(wx.__version__).split('.')[0]) == 2:
        if int(str(wx.__version__).split('.')[1]) < 9:
            IS_WIN = False


class Plugin(PluginBase):
    """
    Plug-in class to be instantiated by the GUI manager
    """
    
    def __init__(self, standalone=False):
        PluginBase.__init__(self, name="Plotting", standalone=standalone)
      
        ## Plot panels
        self.plot_panels = {}
        self._panel_on_focus = None
        self.menu_default_id = None
        # Plot menu
        self.menu = None

     
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
        self.menu.Append(DEFAULT_MENU_ITEM_ID, DEFAULT_MENU_ITEM_LABEL, 
                             "No graph available")
        self.menu.FindItemByPosition(0).Enable(False)
        return [(self.menu, "Show")]
    
    def get_panels(self, parent):
        """
        Create and return a list of panel objects
        """
        ## Save a reference to the parent
        self.parent = parent
        # Connect to plotting events
        self.parent.Bind(EVT_NEW_PLOT, self._on_plot_event)
        self.parent.Bind(EVT_PLOT_QRANGE, self._on_plot_qrange)
        # We have no initial panels for this plug-in
        return []
    
    def _on_plot_qrange(self, event= None):
        """
        On Qmin Qmax vertical line event
        """
        if event == None:
            return
        if event.id in self.plot_panels.keys():
            panel = self.plot_panels[event.id]
        elif event.group_id in self.plot_panels.keys():
            panel = self.plot_panels[event.group_id]
        else:
            return
        panel.on_plot_qrange(event)
            
    def _on_show_panel(self, event):
        """show plug-in panel"""
        pass
    
    def remove_plot(self, group_id, id):
        """
        remove plot of ID = id from a panel of group ID =group_id
        """
        
        if group_id in self.plot_panels.keys():
            panel = self.plot_panels[group_id]
            panel.remove_data_by_id(id=id)
            
            return True
        return False
        
    def clear_panel(self):
        """
        Clear and Hide all plot panels, and remove them from menu
        """
        for group_id in self.plot_panels.keys():
            panel = self.plot_panels[group_id]
            panel.graph.reset()
            self.hide_panel(group_id)
        self.plot_panels = {}
        item = self.menu.FindItemByPosition(0)
        while item != None:
            self.menu.DeleteItem(item) 
            try:
                item = self.menu.FindItemByPosition(0)
            except:
                item = None
               
    
    def clear_panel_by_id(self, group_id):
        """
        clear the graph
        """
        if group_id in self.plot_panels.keys():
            panel = self.plot_panels[group_id]
            for plottable in panel.graph.plottables.keys():
                self.remove_plot(group_id, plottable.id)
            panel.graph.reset()
            return True
        return False
            
    def hide_panel(self, group_id):
        """
        hide panel with group ID = group_id
        """
        if group_id in self.plot_panels.keys():
            panel = self.plot_panels[group_id]
            self.parent.hide_panel(panel.uid)
            return True
        return False
    
    def create_panel_helper(self, new_panel, data, group_id, title=None):
        """
        """
        ## Set group ID if available
        ## Assign data properties to the new create panel
        new_panel.set_manager(self)
        new_panel.group_id = group_id
        if group_id not in data.list_group_id:
            data.list_group_id.append(group_id)
        if title is None:
            title = data.title
        new_panel.window_caption = title
        new_panel.window_name = data.title
        event_id = self.parent.popup_panel(new_panel)
        #remove the default item in the menu
        if len(self.plot_panels) == 0:
            pos = self.menu.FindItem(DEFAULT_MENU_ITEM_LABEL)
            if pos != -1:
                self.menu.Delete(DEFAULT_MENU_ITEM_ID)
        # Set UID to allow us to reference the panel later
        new_panel.uid = event_id
        # Ship the plottable to its panel
        wx.CallAfter(new_panel.plot_data, data) 
        self.plot_panels[new_panel.group_id] = new_panel
        
        # Set Graph menu and help string        
        helpString = 'Show/Hide Graph: '
        for plot in  new_panel.plots.itervalues():
            helpString += (' ' + plot.label + ';')
        self.menu.AppendCheckItem(event_id, new_panel.window_caption, 
                                  helpString)
        self.menu.Check(event_id, IS_WIN)
        wx.EVT_MENU(self.parent, event_id, self._on_check_menu)

        
    def create_1d_panel(self, data, group_id):
        """
        """
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
            return  new_panel
        
        msg = "1D Panel of group ID %s could not be created" % str(group_id)
        raise ValueError, msg
    
    def create_2d_panel(self, data, group_id):
        """
        """
        if issubclass(data.__class__, Data2D):
            ##Create a new plotpanel for 2D data
            from Plotter2D import ModelPanel2D
            scale = data.scale
            new_panel = ModelPanel2D(self.parent, id = -1,
                                data2d=data, scale = scale, 
                                style=wx.RAISED_BORDER)
            return new_panel
        msg = "2D Panel of group ID %s could not be created" % str(group_id)
        raise ValueError, msg
    
    def update_panel(self, data, panel):
        """
        update the graph of a given panel
        """
        # Check whether we already have a graph with the same units
        # as the plottable we just received. 
        _, x_unit =  data.get_xaxis()
        _, y_unit =  data.get_yaxis()
        flag_x = (panel.graph.prop["xunit"] is not None) and \
                    (panel.graph.prop["xunit"].strip() != "") and\
                    (x_unit != panel.graph.prop["xunit"]) and False
        flag_y = (panel.graph.prop["yunit"] is not None) and \
                    (panel.graph.prop["yunit"].strip() != "") and\
                    (y_unit != panel.graph.prop["yunit"]) and False
        if (flag_x and flag_y):
            msg = "Cannot add %s" % str(data.name)
            msg += " to panel %s\n" % str(panel.window_caption)
            msg += "Please edit %s's units, labels" % str(data.name)
            raise ValueError, msg
        else:
            if panel.group_id not in data.list_group_id:
                data.list_group_id.append(panel.group_id)
            wx.CallAfter(panel.plot_data, data)
            #Do not show residual plot when it is hidden
            #ToDo: find better way
            if str(panel.group_id)[0:3] == 'res' and not panel.IsShown():
                return
            self.parent.show_panel(panel.uid)   
    
    def delete_menu_item(self, name, uid):
        """
        """
        #remove menu item
        pos = self.menu.FindItem(name) 
        if pos != -1:
            self.menu.Delete(uid)
        if self.menu.GetMenuItemCount() == 0:
            self.menu.Append(DEFAULT_MENU_ITEM_ID, DEFAULT_MENU_ITEM_LABEL, 
                             "No graph available")
            self.menu.FindItemByPosition(0).Enable(False)
        
    def delete_panel(self, group_id):
        """
        """
        if group_id in self.plot_panels.keys():
            panel = self.plot_panels[group_id]
            uid = panel.uid
            wx.PostEvent(self.parent, 
                         DeletePlotPanelEvent(name=panel.window_caption,
                                    caption=panel.window_caption))
            #remove menu item
            self.delete_menu_item(panel.window_caption, panel.uid)
            del self.plot_panels[group_id]
            if uid in self.parent.plot_panels.keys():
                del self.parent.plot_panels[uid]
            return True

        return False
    
    def _on_plot_event(self, event):
        """
        A new plottable is being shipped to the plotting plug-in.
        Check whether we have a panel to put in on, or create
        a new one
        
        :param event: EVT_NEW_PLOT event
        
        """
        action_check = False
        if hasattr(event, 'action'):
            action_string = event.action.lower().strip()
            if action_string == 'check':
                action_check = True
            else:
                group_id = event.group_id
                if group_id in self.plot_panels.keys():
                    #remove data from panel
                    if action_string == 'remove':
                        id = event.id
                        return self.remove_plot(group_id, id)
                    if action_string == 'hide':
                        return self.hide_panel(group_id)
                    if action_string == 'delete':
                        panel = self.plot_panels[group_id]
                        uid = panel.uid
                        return self.parent.delete_panel(uid)
                    if action_string == "clear":
                        return self.clear_panel_by_id(group_id)
                    
        if not hasattr(event, 'plot'):    
            return
        title = None
        if hasattr(event, 'title'):
            title = 'Graph'#event.title      
        data = event.plot
        group_id = data.group_id    
        if group_id in self.plot_panels.keys():
            if action_check:
                # Check if the plot already exist. if it does, do nothing.
                if data.id in self.plot_panels[group_id].plots.keys():
                    return 
            #update a panel graph 
            panel = self.plot_panels[group_id]
            self.update_panel(data, panel)
        else:
            #create a new panel
            if issubclass(data.__class__, Data1D):
                new_panel = self.create_1d_panel(data, group_id)
            else:
                # Need to make the group_id consistent with 1D thus no if below
                if len(self.plot_panels.values()) > 0:
                    for p_group_id in self.plot_panels.keys():
                        p_plot = self.plot_panels[p_group_id]
                        if data.id in p_plot.plots.keys():
                            p_plot.plots[data.id] = data
                            self.plot_panels[group_id] = p_plot
                            if group_id != p_group_id:
                                del self.plot_panels[p_group_id]
                                if p_group_id in data.list_group_id:
                                    data.list_group_id.remove(p_group_id)
                                if group_id not in data.list_group_id:
                                    data.list_group_id.append(group_id)
                            p_plot.group_id = group_id
                            return
                
                new_panel = self.create_2d_panel(data, group_id)
            self.create_panel_helper(new_panel, data, group_id, title) 
        return

    def _on_check_menu(self, event):
        """
        Check mark on menu
        """
        #event.Skip()
        event_id = event.GetId()

        if self.menu.IsChecked(event_id):
            self.parent.on_view(event)
            self.menu.Check(event_id, IS_WIN)
        else:
            self.parent.hide_panel(event_id)
            self.menu.Check(event_id, False)
        
    def help(self, evt):
        """
        Show a general help dialog. 
        """
        from help_panel import  HelpWindow
        frame = HelpWindow(None, -1) 
        if hasattr(frame, "IsIconized"):
            if not frame.IsIconized():
                try:
                    icon = self.parent.GetIcon()
                    frame.SetIcon(icon)
                except:
                    pass  
        frame.Show(True)