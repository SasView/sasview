
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
from danse.common.plottools.plottables import Graph
from sans.guiframe import dataFitting 
from sans.guiframe.events import EVT_NEW_PLOT
from sans.guiframe.events import StatusEvent 
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.events import SlicerEvent
from sans.guiframe.events import RemoveDataEvent
from sans.guiframe.events import PanelOnFocusEvent
from sans.guiframe.events import EVT_NEW_LOADED_DATA
from sans.guiframe.utils import PanelMenu
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.panel_base import PanelBase
from binder import BindArtist

DEFAULT_QMAX = 0.05
DEFAULT_QSTEP = 0.001
DEFAULT_BEAM = 0.005
BIN_WIDTH = 1


class ModelPanel1D(PlotPanel, PanelBase):
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
      
        self.hide_menu = None
        ## Unique ID (from gui_manager)
        self.uid = None
       
        ## Default locations
        self._default_save_location = os.getcwd()        
        ## Graph        
        self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ", "cm^{-1}")
        self.graph.render(self)
        
        # In resizing event
        self.resizing = False
        self.canvas.set_resizing(self.resizing)
        self.Bind(wx.EVT_SIZE, self._OnReSize)
       
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
        
    def _OnReSize(self, event):   
        """
        On response of the resize of a panel, set axes_visiable False
        """
        # ready for another event
        event.Skip()  
        # set the resizing flag
        self.resizing = True
        self.canvas.set_resizing(self.resizing)
        self.parent.set_schedule(True)
        
        
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
            else:
                data = theory_list[id]
           
            del self.plots[id]
            self.graph.render(self)
            self.subplot.figure.canvas.draw_idle()    
            event = RemoveDataEvent(data=data)
            wx.PostEvent(self.parent, event)
            if len(self.graph.plottables) == 0:
                #onRemove: graph is empty must be the panel must be destroyed
                self.parent.delete_panel(self.uid)
        
    def plot_data(self, data):
        """
        Data is ready to be displayed
        
        :param event: data event
        """
        if data.id in self.plots.keys():
            #replace
            self.graph.replace(data)
            self.plots[data.id] = data
        else:
            self.plots[data.id] = data
            self.graph.add(self.plots[data.id]) 
        
        x_label, x_unit = data.get_xaxis()
        y_label, y_unit = data.get_yaxis()
        self.graph.xaxis(x_unit, x_label)
        self.graph.yaxis(y_unit, y_label)
        ## Set the view scale for all plots
        self._onEVT_FUNC_PROPERTY()
        ## render the graph<=No need this done in canvas
        #self.graph.render(self)
        #self.subplot.figure.canvas.draw_idle()
    
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
            position = "x: %8.3g    y: %8.3g" % (event.xdata, event.ydata)
            wx.PostEvent(self.parent, StatusEvent(status=position))
        
        self.on_set_focus(None)    
        #post nd event to notify guiframe that this panel is on focus
        wx.PostEvent(self.parent, PanelOnFocusEvent(panel=self))

        
    def _ontoggle_hide_error(self, event):
        """
        Toggle error display to hide or show
        """
        
        selected_plot = self.plots[self.graph.selected_plottable]
        if self.hide_menu.GetText() == "Hide Error":
            selected_plot.hide_error = True
        else:
            selected_plot.hide_error = False
        ## increment graph color
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()  
          
    def _onRemove(self, event):
        """
        Remove a plottable from the graph and render the graph 
        
        :param event: Menu event
        
        """
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
        self._slicerpop.Append(id, '&Copy to Clipboard', 'Copy to the clipboard')
        wx.EVT_MENU(self, id, self.OnCopyFigureMenu)
        
        self._slicerpop.AppendSeparator()

        #add menu of other plugins
        item_list = self.parent.get_context_menu(self)

        if (not item_list == None) and (not len(item_list) == 0):
            for item in item_list:
                try:
                    id = wx.NewId()
                    self._slicerpop.Append(id, item[0], item[1])
                    wx.EVT_MENU(self, id, item[2])
                except:
                    msg = "ModelPanel1D.onContextMenu: "
                    msg += "bad menu item  %s" % sys.exc_value
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
                    pass
            self._slicerpop.AppendSeparator()
        #id = wx.NewId()
        #self._slicerpop.Append(id, '&Print image', 'Print image')
        if self.graph.selected_plottable in self.plots:
            plot = self.plots[self.graph.selected_plottable]

            id = wx.NewId()
            self._slicerpop.Append(id, '&Linear Fit')
            wx.EVT_MENU(self, id, self.onFitting)
            self._slicerpop.AppendSeparator()
            id = wx.NewId()
            name = plot.name
            self._slicerpop.Append(id, "&Save Points as a File")
            wx.EVT_MENU(self, id, self._onSave)
            id = wx.NewId()
            self._slicerpop.Append(id, "Remove %s Curve" % name)
            wx.EVT_MENU(self, id, self._onRemove)
            if not plot.is_data:
                id = wx.NewId()
                self._slicerpop.Append(id, '&Freeze', 'Freeze')
                wx.EVT_MENU(self, id, self.onFreeze)
            symbol_menu = wx.Menu()
            for label in self._symbol_labels:
                id = wx.NewId()
                symbol_menu.Append(id, str(label), str(label))
                wx.EVT_MENU(self, id, self.onChangeSymbol)
            id = wx.NewId()
            self._slicerpop.AppendMenu(id,'&Modify Symbol',  symbol_menu)
            self._slicerpop.AppendSeparator()

            id = wx.NewId()
            self.hide_menu = self._slicerpop.Append(id, "Hide Error")
            if plot.dy is not None or plot.dy != []:
                if plot.hide_error :
                    self.hide_menu.SetText('Show Error')
                else:
                    self.hide_menu.SetText('Hide Error')
            else:
                self.hide_menu.Disable()
            wx.EVT_MENU(self, id, self._ontoggle_hide_error)
            
            self._slicerpop.AppendSeparator()
            # Option to hide
            #TODO: implement functionality to hide a plottable (legend click)
        
        
        id = wx.NewId()
        self._slicerpop.Append(id, '&Change scale')
        wx.EVT_MENU(self, id, self._onProperties)
        id = wx.NewId()
        self._slicerpop.Append(id, '&Reset Graph')
        wx.EVT_MENU(self, id, self.onResetGraph)  
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self._slicerpop, pos)
     
    def onFreeze(self, event):
        """
        """
        plot = self.plots[self.graph.selected_plottable]
        self.parent.onfreeze([plot.id])
        
    def onChangeSymbol(self, event):
        """
        """
        menu = event.GetEventObject()
        id = event.GetId()
        label =  menu.GetLabel(id)
        selected_plot = self.plots[self.graph.selected_plottable]
        selected_plot.symbol = self._symbol_labels[label]
        ## Set the view scale for all plots
        self._onEVT_FUNC_PROPERTY()
        ## render the graph
        #self.graph.render(self)
        #self.subplot.figure.canvas.draw_idle()
        
    def _onsaveTXT(self, path):
        """
        Save file as txt
            
        :TODO: Refactor and remove this method. See TODO in _onSave.
        
        """
        data = self.plots[self.graph.selected_plottable]
       
        if not path == None:
            out = open(path, 'w')
            has_errors = True
            if data.dy == None or data.dy == []:
                has_errors = False
            # Sanity check
            if has_errors:
                try:
                    if len(data.y) != len(data.dy):
                        has_errors = False
                except:
                    has_errors = False
            if has_errors:
                if data.dx != None:
                    out.write("<X>   <Y>   <dY>   <dX>\n")
                else:
                    out.write("<X>   <Y>   <dY>\n")
            else:
                out.write("<X>   <Y>\n")
                
            for i in range(len(data.x)):
                if has_errors:
                    if data.dx != None:
                        out.write("%g  %g  %g  %g\n" % (data.x[i], 
                                                    data.y[i],
                                                    data.dy[i],
                                                    data.dx[i]))
                    else:
                        out.write("%g  %g  %g\n" % (data.x[i], 
                                                    data.y[i],
                                                    data.dy[i]))
                else:
                    out.write("%g  %g\n" % (data.x[i], 
                                            data.y[i]))
            out.close()                 
            try:
                self._default_save_location = os.path.dirname(path)
            except:
                pass    
                
    def _onSave(self, evt):
        """
        Save a data set to a text file
        
        :param evt: Menu event
        
        """
       
        path = None
        wildcard = "Text files (*.txt)|*.txt|"\
        "CanSAS 1D files(*.xml)|*.xml" 
        dlg = wx.FileDialog(self, "Choose a file",
                            self._default_save_location,
                             "", wildcard , wx.SAVE)
       
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            mypath = os.path.basename(path)
            
            #TODO: This is bad design. The DataLoader is designed 
            #to recognize extensions.
            # It should be a simple matter of calling the .
            #save(file, data, '.xml') method
            # of the DataLoader.loader.Loader class.
            from DataLoader.loader import  Loader
            #Instantiate a loader 
            loader = Loader() 
            data = self.plots[self.graph.selected_plottable]
            format = ".txt"
            if os.path.splitext(mypath)[1].lower() == format:
                 self._onsaveTXT( path)
            format = ".xml"
            if os.path.splitext(mypath)[1].lower() == format:
                loader.save(path, data, format)
            try:
                self._default_save_location = os.path.dirname(path)
            except:
                pass    
        dlg.Destroy()
