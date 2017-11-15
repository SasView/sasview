


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
from copy import deepcopy
from sas.sasgui.guiframe.events import EVT_NEW_PLOT
from sas.sasgui.guiframe.events import EVT_PLOT_QRANGE
from sas.sasgui.guiframe.events import EVT_PLOT_LIM
from sas.sasgui.guiframe.events import DeletePlotPanelEvent
from sas.sasgui.guiframe.plugin_base import PluginBase
from sas.sasgui.guiframe.dataFitting import Data1D
from sas.sasgui.guiframe.dataFitting import Data2D
from sas.sasgui.guiframe.gui_manager import MDIFrame
DEFAULT_MENU_ITEM_LABEL = "No graph available"
DEFAULT_MENU_ITEM_ID = wx.NewId()

IS_WIN = True
if sys.platform.count("win32") == 0:
    if int(str(wx.__version__).split('.')[0]) == 2:
        if int(str(wx.__version__).split('.')[1]) < 9:
            IS_WIN = False


class Plugin(PluginBase):
    """
    Plug-in class to be instantiated by the GUI manager
    """

    def __init__(self):
        PluginBase.__init__(self, name="Plotting")

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
        return []

    def get_panels(self, parent):
        """
        Create and return a list of panel objects
        """
        ## Save a reference to the parent
        self.parent = parent
        # Connect to plotting events
        self.parent.Bind(EVT_NEW_PLOT, self._on_plot_event)
        self.parent.Bind(EVT_PLOT_QRANGE, self._on_plot_qrange)
        self.parent.Bind(EVT_PLOT_LIM, self._on_plot_lim)
        # We have no initial panels for this plug-in
        return []

    def _on_plot_qrange(self, event=None):
        """
        On Qmin Qmax vertical line event
        """
        if event is None:
            return
        if event.id in self.plot_panels.keys():
            panel = self.plot_panels[event.id]
        elif event.group_id in self.plot_panels.keys():
            panel = self.plot_panels[event.group_id]
        else:
            return
        panel.on_plot_qrange(event)

    def _on_plot_lim(self, event=None):
        if event is None:
            return
        if event.id in self.plot_panels.keys():
            panel = self.plot_panels[event.id]
        elif event.group_id in self.plot_panels.keys():
            panel = self.plot_panels[event.group_id]
        else:
            return
        if hasattr(event, 'xlim'):
            panel.subplot.set_xlim(event.xlim)
        if hasattr(event, 'ylim'):
            panel.subplot.set_ylim(event.ylim)


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
            self.clear_panel_by_id(group_id)
        self.plot_panels = {}

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
        # Not implemeted
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

        # Set UID to allow us to reference the panel later
        new_panel.uid = event_id
        # Ship the plottable to its panel
        wx.CallAfter(new_panel.plot_data, data)
        #new_panel.canvas.set_resizing(new_panel.resizing)
        self.plot_panels[new_panel.group_id] = new_panel

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
            win = MDIFrame(self.parent, None, 'None', (100, 200))
            new_panel = ModelPanel1D(win, -1, xtransform=xtransform,
                                     ytransform=ytransform, style=wx.RAISED_BORDER)
            win.set_panel(new_panel)
            win.Show(False)
            new_panel.frame = win
            #win.Show(True)
            return  new_panel

        msg = "1D Panel of group ID %s could not be created" % str(group_id)
        raise (ValueError, msg)

    def create_2d_panel(self, data, group_id):
        """
        """
        if issubclass(data.__class__, Data2D):
            ##Create a new plotpanel for 2D data
            from Plotter2D import ModelPanel2D
            scale = data.scale
            win = MDIFrame(self.parent, None, 'None', (200, 150))
            win.Show(False)
            new_panel = ModelPanel2D(win, id=-1,
                                     data2d=data, scale=scale,
                                     style=wx.RAISED_BORDER)
            win.set_panel(new_panel)
            new_panel.frame = win
            return new_panel
        msg = "2D Panel of group ID %s could not be created" % str(group_id)
        raise (ValueError, msg)

    def update_panel(self, data, panel):
        """
        update the graph of a given panel
        """
        # Check whether we already have a graph with the same units
        # as the plottable we just received.
        _, x_unit = data.get_xaxis()
        _, y_unit = data.get_yaxis()
        flag_x = (panel.graph.prop["xunit"] is not None) and \
                    (panel.graph.prop["xunit"].strip() != "") and\
                    (x_unit != panel.graph.prop["xunit"]) and False
        flag_y = (panel.graph.prop["yunit"] is not None) and \
                    (panel.graph.prop["yunit"].strip() != "") and\
                    (y_unit != panel.graph.prop["yunit"]) and False
        if flag_x and flag_y:
            msg = "Cannot add %s" % str(data.name)
            msg += " to panel %s\n" % str(panel.window_caption)
            msg += "Please edit %s's units, labels" % str(data.name)
            raise (ValueError, msg)
        else:
            if panel.group_id not in data.list_group_id:
                data.list_group_id.append(panel.group_id)
            wx.CallAfter(panel.plot_data, data)

    def delete_panel(self, group_id):
        """
        """
        if group_id in self.plot_panels.keys():
            panel = self.plot_panels[group_id]
            uid = panel.uid
            wx.PostEvent(self.parent,
                         DeletePlotPanelEvent(name=panel.window_caption,
                                              caption=panel.window_caption))
            del self.plot_panels[group_id]
            if uid in self.parent.plot_panels.keys():
                del self.parent.plot_panels[uid]
                panel.frame.Destroy()
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
                if action_string == 'update':
                    # Update all existing plots of data with this ID
                    for data in event.plots:
                        for panel in self.plot_panels.values():
                            if data.id in panel.plots.keys():
                                plot_exists = True
                                # Pass each panel it's own copy of the data
                                # that's being updated, otherwise things like
                                # colour and line thickness are unintentionally
                                # synced across panels
                                self.update_panel(deepcopy(data), panel)
                    return
                    
                group_id = event.group_id
                if group_id in self.plot_panels:
                    #remove data from panel
                    if action_string == 'remove':
                        return self.remove_plot(group_id, event.id)
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
            title = 'Graph'  #event.title
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
            if hasattr(event, 'xlim'):
                new_panel.subplot.set_xlim(event.xlim)
            if hasattr(event, 'ylim'):
                new_panel.subplot.set_ylim(event.ylim)
        return
