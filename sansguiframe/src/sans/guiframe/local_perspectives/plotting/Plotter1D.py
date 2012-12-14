
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
import os
import pylab
import math
import numpy
import time

from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.SizeDialog import SizeDialog
from danse.common.plottools.LabelDialog import LabelDialog
#from danse.common.plottools.plottables import Graph
from sans.guiframe import dataFitting 
from sans.guiframe.events import EVT_NEW_PLOT
from sans.guiframe.events import StatusEvent 
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.events import NewColorEvent
from sans.guiframe.events import SlicerEvent
from sans.guiframe.events import PanelOnFocusEvent
from sans.guiframe.events import EVT_NEW_LOADED_DATA
from sans.guiframe.utils import PanelMenu
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.panel_base import PanelBase
from sans.guiframe.gui_style import GUIFRAME_ICON
from danse.common.plottools.binder import BindArtist
from appearanceDialog import appearanceDialog
from graphAppearance import graphAppearance

DEFAULT_QMAX = 0.05
DEFAULT_QSTEP = 0.001
DEFAULT_BEAM = 0.005
BIN_WIDTH = 1
IS_MAC = (sys.platform == 'darwin')


def find_key(dic, val):
    """return the key of dictionary dic given the value"""
    return [k for k, v in dic.iteritems() if v == val][0]



class ModelPanel1D(PlotPanel, PanelBase):
    """
    Plot panel for use with the GUI manager
    """
    
    ## Internal name for the AUI manager
    window_name = "plotpanel"
    ## Title to appear on top of the window
    window_caption = "Graph"
    ## Flag to tell the GUI manager that this panel is not
    #  tied to any perspective
    ALWAYS_ON = True
    ## Group ID
    group_id = None
    
    def __init__(self, parent, id=-1, color = None,
                 dpi=None, style=wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        PlotPanel.__init__(self, parent, id=id, style=style, **kwargs)
        PanelBase.__init__(self, parent)
        ## Reference to the parent window
        self.parent = parent
        ## Plottables
        self.plots = {}
        #context menu
        self._slicerpop = None
        
        self._available_data = []
        self._menu_add_ids = []
        self._symbol_labels = self.get_symbol_label()
        self._color_labels = self.get_color_label()
        self.currColorIndex = ""
        self._is_changed_legend_label = False
        self.is_xtick = False
        self.is_ytick = False
      
        self.hide_menu = None
        ## Unique ID (from gui_manager)
        self.uid = None
        self.x_size = None
        ## Default locations
        #self._default_save_location = os.getcwd() 
        self.size = None       
        ## Graph        
        #self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ", "cm^{-1}")
        self.graph.render(self)
        
        # In resizing event
        self.resizing = False
        self.canvas.set_resizing(self.resizing)
        self.Bind(wx.EVT_SIZE, self._OnReSize)
        self._add_more_tool()
        self.parent.SetFocus()
        
        
    def get_symbol_label(self):
        """
        Associates label to symbol
        """
        _labels = {}
        i = 0
        _labels['Circle'] = i
        i += 1
        _labels['Cross X '] = i
        i += 1
        _labels['Triangle Down'] = i
        i += 1
        _labels['Triangle Up'] = i
        i += 1
        _labels['Triangle Left'] = i
        i += 1
        _labels['Triangle Right'] = i
        i += 1
        _labels['Cross +'] = i
        i += 1
        _labels['Square'] = i
        i += 1
        _labels['Diamond'] = i
        i += 1
        _labels['Diamond'] = i
        i += 1
        _labels['Hexagon1'] = i
        i += 1
        _labels['Hexagon2'] = i
        i += 1
        _labels['Pentagon'] = i
        i += 1
        _labels['Line'] = i
        i += 1
        _labels['Dash'] = i
        i += 1
        _labels['Vline'] = i
        i += 1
        _labels['Step'] = i
        return _labels
    
    def get_color_label(self):
        """
        Associates label to a specific color
        """
        _labels = {}
        i = 0
        _labels['Blue'] = i
        i += 1
        _labels['Green'] = i
        i += 1
        _labels['Red'] = i
        i += 1
        _labels['Cyan'] = i
        i += 1
        _labels['Magenta'] = i
        i += 1
        _labels['Yellow'] = i
        i += 1
        _labels['Black'] = i
        return _labels

    
    def set_data(self, list=None):
        """
        """
        pass
    
    def _reset(self):
        """
        Resets internal data and graph
        """    
        self.graph.reset()
        self.plots      = {}
        if self.is_zoomed:
            self.is_zoomed = False
        
    def _OnReSize(self, event):   
        """
        On response of the resize of a panel, set axes_visiable False
        """
        # It was found that wx >= 2.9.3 sends an event even if no size changed.
        # So manually recode the size (=x_size) and compare here.
        # Massy code to work around:<
        if self.parent._mgr != None:
            max_panel = self.parent._mgr.GetPane(self)
            if max_panel.IsMaximized():
                self.parent._mgr.RestorePane(max_panel)
                max_panel.Maximize()
        if self.x_size != None:
            if self.x_size == self.GetSize():
                self.resizing = False
                self.canvas.set_resizing(self.resizing)
                return
        self.x_size = self.GetSize()

        # Ready for another event
        # Do not remove this Skip. Otherwise it will get runtime error on wx>=2.9.
        event.Skip() 
        # set the resizing flag
        self.resizing = True
        self.canvas.set_resizing(self.resizing)
        self.parent.set_schedule(True)
        pos_x, pos_y = self.GetPositionTuple()
        if pos_x != 0 and pos_y != 0:
            self.size, _ = self.GetClientSizeTuple()
        self.SetSizer(self.sizer)
        wx.CallAfter(self.parent.disable_app_menu,self)
        
    def set_resizing(self, resizing=False):
        """
        Set the resizing (True/False)
        """
        self.resizing = resizing
        #self.canvas.set_resizing(resizing)
    
    def schedule_full_draw(self, func='append'):    
        """
        Put self in schedule to full redraw list
        """
        # append/del this panel in the schedule list
        self.parent.set_schedule_full_draw(self, func)
        

    def remove_data_by_id(self, id):
        """'
        remove data from plot
        """
        if id in self.plots.keys():
            data =  self.plots[id]
            self.graph.delete(data)
            data_manager = self._manager.parent.get_data_manager()
            data_list, theory_list = data_manager.get_by_id(id_list=[id])
            
            if id in data_list.keys():
                data = data_list[id]
            if id in theory_list.keys():
                data = theory_list[id]
            # Update Graph menu and help string        
            h_id = self.parent._window_menu.FindItem(self.window_caption)
            if data != None:
                if data.__class__.__name__ == 'list':
                    label = data[0].label
                else:
                    label = data.label
            else:
                label = '???'
            helpString = self.parent._window_menu.GetHelpString(h_id) 
            d_string = (' ' + str(label) +';')
            new_tip = helpString.replace(d_string, '')
            self.parent._window_menu.SetHelpString(h_id, new_tip)  

            del self.plots[id]
            self.graph.render(self)
            self.subplot.figure.canvas.draw_idle()    
            if len(self.graph.plottables) == 0:
                #onRemove: graph is empty must be the panel must be destroyed
                self.parent.delete_panel(self.uid)
            
        
    def plot_data(self, data):
        """
        Data is ready to be displayed
        
        :param event: data event
        """
        if data.__class__.__name__ == 'Data2D':
            return
        plot_keys = self.plots.keys()
        if data.id in plot_keys:
            #Recover panel prop.s
            xlo, xhi = self.subplot.get_xlim()
            ylo, yhi = self.subplot.get_ylim()
            old_data = self.plots[data.id]
            if self._is_changed_legend_label:
                data.label = old_data.label
            if old_data.__class__.__name__ == 'Data1D':
                data.custom_color = old_data.custom_color
                data.symbol = old_data.symbol
                data.markersize = old_data.markersize
                data.zorder = len(plot_keys)
            # Replace data
            self.graph.replace(data)
            self.plots[data.id] = data
            ## Set the view scale for all plots
            try:
                self._onEVT_FUNC_PROPERTY()
            except:
                msg=" Encountered singular points..."
                wx.PostEvent(self.parent, StatusEvent(status=\
                    "Plotting Error: %s"% msg, info="error")) 
            # Check if zoomed
            toolbar_zoomed = self.toolbar.GetToolEnabled(self.toolbar._NTB2_BACK)
            if self.is_zoomed or toolbar_zoomed:
                # Recover the x,y limits
                self.subplot.set_xlim((xlo, xhi))     
                self.subplot.set_ylim((ylo, yhi))  
        else:
            self.plots[data.id] = data
            self.graph.add(self.plots[data.id]) 
            data.zorder = len(plot_keys)
            ## Set the view scale for all plots
            try:
                self._onEVT_FUNC_PROPERTY()
                if IS_MAC:
                    # MAC: forcing to plot 2D avg
                    self.canvas._onDrawIdle()
            except:
                msg=" Encountered singular points..."
                wx.PostEvent(self.parent, StatusEvent(status=\
                    "Plotting Error: %s"% msg, info="error")) 
            self.toolbar.update()
            if self.is_zoomed:
                self.is_zoomed = False
            # Update Graph menu and help string        
            pos = self.parent._window_menu.FindItem(self.window_caption)
            helpString = 'Show/Hide Graph: '
            for plot in  self.plots.itervalues():
                helpString += (' ' + str(plot.label) +';')
            self.parent._window_menu.SetHelpString(pos, helpString)      
          
    def draw_plot(self):
        """
        Draw plot
        """
        self.draw()  

    def onLeftDown(self,event): 
        """ 
        left button down and ready to drag
        Display the position of the mouse on the statusbar
        """
        PlotPanel.onLeftDown(self, event)
        ax = event.inaxes
        if ax != None:
            try:
                pos_x = float(event.xdata)# / size_x
                pos_y = float(event.ydata)# / size_y
                pos_x = "%8.3g"% pos_x
                pos_y = "%8.3g"% pos_y
                self.position = str(pos_x), str(pos_y)
                wx.PostEvent(self.parent, StatusEvent(status=self.position))
            except:
                self.position = None  
        # unfocus all
        self.parent.set_plot_unfocus()  
        #post nd event to notify guiframe that this panel is on focus
        wx.PostEvent(self.parent, PanelOnFocusEvent(panel=self))

        
    def _ontoggle_hide_error(self, event):
        """
        Toggle error display to hide or show
        """
        menu = event.GetEventObject()
        id = event.GetId()
        self.set_selected_from_menu(menu, id)
        # Check zoom
        xlo, xhi = self.subplot.get_xlim()
        ylo, yhi = self.subplot.get_ylim()

        selected_plot = self.plots[self.graph.selected_plottable]
        if self.hide_menu.GetText() == "Hide Error Bar":
            selected_plot.hide_error = True
        else:
            selected_plot.hide_error = False
        ## increment graph color
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()  
        # Check if zoomed
        toolbar_zoomed = self.toolbar.GetToolEnabled(self.toolbar._NTB2_BACK)
        if self.is_zoomed or toolbar_zoomed:
            # Recover the x,y limits
            self.subplot.set_xlim((xlo, xhi))     
            self.subplot.set_ylim((ylo, yhi)) 

          
    def _onRemove(self, event):
        """
        Remove a plottable from the graph and render the graph 
        
        :param event: Menu event
        
        """
        menu = event.GetEventObject()
        id = event.GetId()
        self.set_selected_from_menu(menu, id)
        ## Check if there is a selected graph to remove
        if self.graph.selected_plottable in self.plots.keys():
            selected_plot = self.plots[self.graph.selected_plottable]
            id = self.graph.selected_plottable
            self.remove_data_by_id(id)
            
    def onContextMenu(self, event):
        """
        1D plot context menu
        
        :param event: wx context event
        
        """
        self._slicerpop = PanelMenu()
        self._slicerpop.set_plots(self.plots)
        self._slicerpop.set_graph(self.graph)   
        if not self.graph.selected_plottable in self.plots:  
            # Various plot options
            id = wx.NewId()
            self._slicerpop.Append(id, '&Save Image', 'Save image as PNG')
            wx.EVT_MENU(self, id, self.onSaveImage)
            id = wx.NewId()
            self._slicerpop.Append(id, '&Print Image', 'Print image ')
            wx.EVT_MENU(self, id, self.onPrint)
            id = wx.NewId()
            self._slicerpop.Append(id, '&Print Preview', 'Print preview')
            wx.EVT_MENU(self, id, self.onPrinterPreview)
            
            id = wx.NewId()
            self._slicerpop.Append(id, '&Copy to Clipboard', 
                                   'Copy to the clipboard')
            wx.EVT_MENU(self, id, self.OnCopyFigureMenu)
                    
            self._slicerpop.AppendSeparator()

        for plot in self.plots.values():
            #title = plot.title
            name = plot.name
            plot_menu = wx.Menu()
            if self.graph.selected_plottable:
                if not self.graph.selected_plottable in self.plots.keys():
                    continue
                if plot != self.plots[self.graph.selected_plottable]:
                    continue
                
            id = wx.NewId()
            plot_menu.Append(id, "&DataInfo", name)
            wx.EVT_MENU(self, id, self. _onDataShow)
            id = wx.NewId()
            plot_menu.Append(id, "&Save Points as a File", name)
            wx.EVT_MENU(self, id, self._onSave)
            plot_menu.AppendSeparator()
            
            #add menu of other plugins
            item_list = self.parent.get_current_context_menu(self)
              
            if (not item_list == None) and (not len(item_list) == 0):
                for item in item_list:

                    try:
                        id = wx.NewId()
                        plot_menu.Append(id, item[0], name)
                        wx.EVT_MENU(self, id, item[2])
                    except:
                        msg = "ModelPanel1D.onContextMenu: "
                        msg += "bad menu item  %s" % sys.exc_value
                        wx.PostEvent(self.parent, StatusEvent(status=msg))
                        pass
                plot_menu.AppendSeparator()
            
            if self.parent.ClassName.count('wxDialog') == 0: 
                id = wx.NewId()
                plot_menu.Append(id, '&Linear Fit', name)
                wx.EVT_MENU(self, id, self.onFitting)
                plot_menu.AppendSeparator()
    
                id = wx.NewId()
                plot_menu.Append(id, "Remove", name)
                wx.EVT_MENU(self, id, self._onRemove)
                if not plot.is_data:
                    id = wx.NewId()
                    plot_menu.Append(id, '&Freeze', name)
                    wx.EVT_MENU(self, id, self.onFreeze)
                plot_menu.AppendSeparator()    
                symbol_menu = wx.Menu()
                
                if plot.is_data:
                    id = wx.NewId()
                    self.hide_menu = plot_menu.Append(id, 
                                                    "Hide Error Bar", name)
        
                    if plot.dy is not None and plot.dy != []:
                        if plot.hide_error :
                            self.hide_menu.SetText('Show Error Bar')
                        else:
                            self.hide_menu.SetText('Hide Error Bar')
                    else:
                        self.hide_menu.Enable(False)
                    wx.EVT_MENU(self, id, self._ontoggle_hide_error)
                
                    plot_menu.AppendSeparator()

                id = wx.NewId()
                plot_menu.Append(id, '&Modify Plot Property', name)
                wx.EVT_MENU(self, id, self.createAppDialog)



            id = wx.NewId()
            #plot_menu.SetTitle(name)
            self._slicerpop.AppendMenu(id, '&%s'% name, plot_menu)
            # Option to hide
            #TODO: implement functionality to hide a plottable (legend click)
        if not self.graph.selected_plottable in self.plots:  
            self._slicerpop.AppendSeparator()
            loc_menu = wx.Menu()
            for label in self._loc_labels:
                id = wx.NewId()
                loc_menu.Append(id, str(label), str(label))
                wx.EVT_MENU(self, id, self.onChangeLegendLoc)
            
            id = wx.NewId()
            self._slicerpop.Append(id, '&Modify Graph Appearance',
                                   'Modify graph appearance')
            wx.EVT_MENU(self, id, self.modifyGraphAppearance)
            self._slicerpop.AppendSeparator()

            
            if self.position != None:
                id = wx.NewId()
                self._slicerpop.Append(id, '&Add Text')
                wx.EVT_MENU(self, id, self._on_addtext)
                id = wx.NewId()
                self._slicerpop.Append(id, '&Remove Text')
                wx.EVT_MENU(self, id, self._on_removetext)
                self._slicerpop.AppendSeparator()
            id = wx.NewId()
            self._slicerpop.Append(id, '&Change Scale')
            wx.EVT_MENU(self, id, self._onProperties)
            self._slicerpop.AppendSeparator()
            id = wx.NewId()
            self._slicerpop.Append(id, '&Reset Graph Range')
            wx.EVT_MENU(self, id, self.onResetGraph)  
            
            if self.parent.ClassName.count('wxDialog') == 0:    
                self._slicerpop.AppendSeparator()
                id = wx.NewId()
                self._slicerpop.Append(id, '&Window Title')
                wx.EVT_MENU(self, id, self.onChangeCaption)
        try:
            pos_evt = event.GetPosition()
            pos = self.ScreenToClient(pos_evt)
        except:
            pos_x, pos_y = self.toolbar.GetPositionTuple()
            pos = (pos_x, pos_y + 5)
        self.PopupMenu(self._slicerpop, pos)
            
    def onFreeze(self, event):
        """
        on Freeze data
        """
        menu = event.GetEventObject()
        id = event.GetId()
        self.set_selected_from_menu(menu, id)
        plot = self.plots[self.graph.selected_plottable]
        self.parent.onfreeze([plot.id])
        
                       
    def _onSave(self, evt):
        """
        Save a data set to a text file
        
        :param evt: Menu event
        
        """
        menu = evt.GetEventObject()
        id = evt.GetId()
        self.set_selected_from_menu(menu, id)
        data = self.plots[self.graph.selected_plottable]
        default_name = data.label
        if default_name.count('.') > 0:
            default_name = default_name.split('.')[0]
        default_name += "_out"
        if self.parent != None:
            self.parent.save_data1d(data, default_name)

                       
    def _onDataShow(self, evt):
        """
        Show the data set in text
        
        :param evt: Menu event
        
        """
        menu = evt.GetEventObject()
        id = evt.GetId()
        self.set_selected_from_menu(menu, id)
        data = self.plots[self.graph.selected_plottable]
        default_name = data.label
        if default_name.count('.') > 0:
            default_name = default_name.split('.')[0]
        #default_name += "_out"
        if self.parent != None:
            self.parent.show_data1d(data, default_name)
            
    def _add_more_tool(self):
        """
        Add refresh, add/hide button in the tool bar
        """
        if self.parent.__class__.__name__ != 'ViewerFrame':
            return
        self.toolbar.AddSeparator()
        id_hide = wx.NewId()
        hide = wx.Bitmap(GUIFRAME_ICON.HIDE_ID_PATH, wx.BITMAP_TYPE_PNG)
        self.toolbar.AddSimpleTool(id_hide, hide, 'Hide', 'Hide')
        self.toolbar.Realize()
        wx.EVT_TOOL(self, id_hide,  self._on_hide)
        
    def _on_hide(self, event):
        """
        Hides the plot when button is pressed
        """     
        if self.parent is not None:
            self.parent.hide_panel(self.uid)

    def createAppDialog(self, event):
        """
        Create the custom dialog for fit appearance modification
        """
        menu = event.GetEventObject()
        id = event.GetId()
        self.set_selected_from_menu(menu, id)
        self.appearance_selected_plot = \
                        self.plots[self.graph.selected_plottable]
        # find current properties
        curr_color = self.appearance_selected_plot.custom_color
        curr_symbol = self.appearance_selected_plot.symbol
        curr_size = self.appearance_selected_plot.markersize
        curr_label = self.appearance_selected_plot.label

        if curr_color == None:
            curr_color = self._color_labels['Blue']
            curr_symbol = 13

        self.appD = appearanceDialog(self, 'Modify Plot Property')
        icon = self.parent.GetIcon()
        self.appD.SetIcon(icon)
        self.appD.set_defaults(float(curr_size), int(curr_color), 
                    str(appearanceDialog.find_key(self.get_symbol_label(), 
                    int(curr_symbol))), curr_label)
        self.appD.Bind(wx.EVT_CLOSE, self.on_AppDialog_close)    

    def on_AppDialog_close(self, event):
        """
        on_Modify Plot Property_close
        """
        if(self.appD.okay_clicked == True):
            # returns (size,color,symbol,datalabel)
            info = self.appD.get_current_values() 
            self.appearance_selected_plot.custom_color = \
                        self._color_labels[info[1].encode('ascii', 'ignore')]

            self.appearance_selected_plot.markersize = float(info[0])
            self.appearance_selected_plot.symbol = \
                        self.get_symbol_label()[info[2]] 
            self.appearance_selected_plot.label = str(info[3])

            pos = self.parent._window_menu.FindItem(self.window_caption)
            helpString = 'Show/Hide Graph: '
            for plot in  self.plots.itervalues():
                helpString += (' ' + str(plot.label) + ';')
                self.parent._window_menu.SetHelpString(pos, helpString)
                self._is_changed_legend_label = True
                
        self.appD.Destroy()
        self._check_zoom_plot()


    def modifyGraphAppearance(self, event):
        """
        On Modify Graph Appearance 
        """
        self.graphApp = graphAppearance(self, 'Modify Graph Appearance')
        icon = self.parent.GetIcon()
        self.graphApp.SetIcon(icon)
        self.graphApp.setDefaults(self.grid_on, self.legend_on, 
                                  self.xaxis_label, self.yaxis_label, 
                                  self.xaxis_unit, self.yaxis_unit, 
                                  self.xaxis_font, self.yaxis_font, 
                                  find_key(self.get_loc_label(), 
                                  self.legendLoc), 
                                  self.xcolor, self.ycolor, 
                                  self.is_xtick, self.is_ytick)
        self.graphApp.Bind(wx.EVT_CLOSE, self.on_graphApp_close)
    

    def on_graphApp_close(self, event):
        """
        Gets values from graph appearance dialog and sends them off
        to modify the plot
        """
        graph_app = self.graphApp
        toggle_grid = graph_app.get_togglegrid()
        legend_loc = graph_app.get_legend_loc()
        toggle_legend = graph_app.get_togglelegend()
        
        self.onGridOnOff(toggle_grid )
        self.ChangeLegendLoc(legend_loc)
        self.onLegend(toggle_legend)

        self.xaxis_label = graph_app.get_xlab()
        self.yaxis_label = graph_app.get_ylab()
        self.xaxis_unit = graph_app.get_xunit()
        self.yaxis_unit = graph_app.get_yunit()
        self.xaxis_font = graph_app.get_xfont()
        self.yaxis_font = graph_app.get_yfont()
        self.is_xtick =  graph_app.get_xtick_check()
        self.is_ytick =  graph_app.get_ytick_check()
        if self.is_xtick:
            self.xaxis_tick = self.xaxis_font
        if self.is_ytick:
            self.yaxis_tick = self.yaxis_font

        self.xaxis(self.xaxis_label, self.xaxis_unit, 
                   graph_app.get_xfont(), graph_app.get_xcolor(), 
                   self.xaxis_tick)
        self.yaxis(self.yaxis_label, self.yaxis_unit, 
                   graph_app.get_yfont(), graph_app.get_ycolor(),
                   self.yaxis_tick)

        graph_app.Destroy()
