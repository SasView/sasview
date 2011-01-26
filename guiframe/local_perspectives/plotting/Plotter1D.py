
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
import danse.common.plottools
from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.plottables import Graph
from sans.guiframe import dataFitting 
from sans.guiframe.events import EVT_NEW_PLOT
from sans.guiframe.events import StatusEvent 
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.events import SlicerEvent
from sans.guiframe.events import ErrorDataEvent
from sans.guiframe.events import RemoveDataEvent
from sans.guiframe.events import AddManyDataEvent
from sans.guiframe.events import EVT_NEW_LOADED_DATA
from sans.guiframe.utils import PanelMenu
from sans.guiframe.dataFitting import Data1D
from sans.guiframe.dataFitting import Theory1D
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
        PanelBase.__init__(self)
        ## Reference to the parent window
        self.parent = parent
        ## Plottables
        self.plots = {}
        #context menu
        self._slicerpop = None
        self._menu_add_plot = None
        self._available_data = []
        self._menu_add_ids = []
        ## save errors dy  for each data plotted
        self.err_dy = {}
        ## flag to determine if the hide or show context menu item should
        ## be displayed
        self.errors_hide = False
        ## Unique ID (from gui_manager)
        self.uid = None
        ## Action IDs for internal call-backs
        self.action_ids = {}
        ## Default locations
        self._default_save_location = os.getcwd()        
        ## Graph        
        self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ", "cm^{-1}")
        self.graph.render(self)
        #bind with event to contrst context menu
        self.parent.Bind(EVT_NEW_LOADED_DATA, self._add_new_plot)
        
    def on_add_new_plot(self, event):
        """
        """
    def _add_new_plot(self, event):
        """
        Construct the context menu given available data
        """
        self._available_data = event.data_to_add
    
    def _fill_menu_add_plot(self):
        """
        """
        if self._menu_add_plot is not None:
            if self._available_data:
                for id in self._menu_add_ids:
                    item = self._menu_add_plot.FindItemById(id)
                    if item is None:
                        for data in self._available_data:
                            new_id = wx.NewId()
                            hint = 'Add %s to this panel' % str(data.name)
                            self._menu_add_plot.Append(new_id, str(data.name), hint)
                            wx.EVT_MENU(self, id, self.on_add_new_plot)
                            self._menu_add_ids.append(new_id)
                    else:
                        if item.GetLabel() == 'No Loaded Data':
                            self._menu_add_plot.RemoveItem(item)
                        
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
        self.action_ids = {}
    
    def _onEVT_1DREPLOT(self, event):
        """
        Data is ready to be displayed
        
        :param event: data event
        """
        #TODO: Check for existence of plot attribute
        # Check whether this is a replot. If we ask for a replot
        # and the plottable no longer exists, ignore the event.
        if hasattr(event, "update") and event.update == True \
            and event.plot.name not in self.plots.keys():
            return
        if hasattr(event, "reset"):
            self._reset()
        # Check whether the plottable is empty
        is_empty = len(event.plot.x) == 0
                
        is_new = True
        if event.plot.name in self.plots.keys():
            # If the plottable is empty, just remove the plottable from the graph
            if is_empty:
                self.graph.delete(self.plots[event.plot.name])
                del self.plots[event.plot.name]
            else:  
                # Check whether the class of plottable changed
                if not event.plot.__class__ == self.plots[event.plot.name].__class__:
                    #overwrite a plottable using the same name
                    self.graph.delete(self.plots[event.plot.name])              
                else:
                    # plottable is already draw on the panel
                    is_new = False
        
        if not is_empty:
            if is_new:
                # a new plottable overwrites a plotted one  using the same id
                for plottable in self.plots.itervalues():
                    if hasattr(event.plot, "id") and hasattr(plottable, "id"):
                        #remove the existing plot and same id and same name
                        if event.plot.id == plottable.id and \
                            event.plot.name == plottable.name:
                            self.graph.delete(plottable)
                
                self.plots[event.plot.name] = event.plot
                self.graph.add(self.plots[event.plot.name])
            else:
                #replot the graph
                self.plots[event.plot.name].x = event.plot.x    
                self.plots[event.plot.name].y = event.plot.y    
                self.plots[event.plot.name].dy = event.plot.dy  
                if hasattr(event.plot, 'dx') and \
                    hasattr(self.plots[event.plot.name], 'dx'):
                    self.plots[event.plot.name].dx = event.plot.dx    
          
        #TODO: Should re-factor this
        ## for all added plot the option to hide error show be displayed first
        #self.errors_hide = 0
        ## Set axis labels
        self.graph.xaxis(event.plot._xaxis, event.plot._xunit)
        self.graph.yaxis(event.plot._yaxis, event.plot._yunit)
        ## Set the view scale for all plots
        self._onEVT_FUNC_PROPERTY()
        ## render the graph
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
        #if self.errors_hide:
        #    self._on_remove_errors(evt=None)
        #else:
        #    self._on_add_errors( evt=None)
    
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
            
        #post nd event to notify guiframe that this panel is on focus
        wx.PostEvent(self.parent, AddManyDataEvent(panel=self))
        
    def _onRemove(self, event):
        """
        Remove a plottable from the graph and render the graph 
        
        :param event: Menu event
        
        """
        selected_plot = self.plots[self.graph.selected_plottable]
        ## Check if there is a selected graph to remove
        if not self.graph.selected_plottable == None and\
            self.graph.selected_plottable in self.plots.keys():
            color = self.graph.plottables[selected_plot]
            event = RemoveDataEvent(data=selected_plot)
            wx.PostEvent(self.parent, event)
            self.graph.delete(selected_plot)
            del selected_plot
            ## increment graph color
            self.graph.color += color
            self.graph.render(self)
            self.subplot.figure.canvas.draw_idle()    
           
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
        self._slicerpop.Append(id, '&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, id, self.onSaveImage)
        id = wx.NewId()
        self._slicerpop.Append(id, '&Print image', 'Print image ')
        wx.EVT_MENU(self, id, self.onPrint)
        id = wx.NewId()
        self._slicerpop.Append(id, '&Print Preview', 'image preview for print')
        wx.EVT_MENU(self, id, self.onPrinterPreview)
        #add plot
        self._menu_add_plot = wx.Menu()
        id = wx.NewId()
        self._menu_add_plot.Append(id, '&No Loaded Data', 'Add new plot')
        self._menu_add_plot.FindItemByPosition(0).Enable(False)
        self._menu_add_ids.append(id)
        
        self._slicerpop.AppendSubMenu(self._menu_add_plot, '&Add New Plot')
        self._fill_menu_add_plot()
        self._slicerpop.AppendSeparator()
        #add menu of other plugins
        item_list = self.parent.get_context_menu(self.graph)
        if (not item_list == None) and (not len(item_list) == 0):
            for item in item_list:
                try:
                    id = wx.NewId()
                    self._slicerpop.Append(id, item[0], item[1])
                    wx.EVT_MENU(self, id, item[2])
                except:
                    msg = "ModelPanel1D.onContextMenu: "
                    msg += "bad menu item  %s"%sys.exc_value
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
                    pass
            self._slicerpop.AppendSeparator()
        id = wx.NewId()
        self._menu_add_plot = wx.Menu()
        self._slicerpop.Append(id, '&Print image', 'Print image')
        if self.graph.selected_plottable in self.plots:
            plot = self.plots[self.graph.selected_plottable]
            id = wx.NewId()
            name = plot.name
            self._slicerpop.Append(id, "&Save points")
            self.action_ids[str(id)] = plot
            wx.EVT_MENU(self, id, self._onSave)
            id = wx.NewId()
            self._slicerpop.Append(id, "Remove %s curve" % name)
            self.action_ids[str(id)] = plot
            wx.EVT_MENU(self, id, self._onRemove)
            self._slicerpop.AppendSeparator()
            # Option to hide
            #TODO: implement functionality to hide a plottable (legend click)
        if self.graph.selected_plottable in self.plots:
            selected_plot = self.plots[self.graph.selected_plottable]
            id = wx.NewId()
            self._slicerpop.Append(id, '&Linear fit')
            wx.EVT_MENU(self, id, self.onFitting)
            self._slicerpop.AppendSeparator()
        id = wx.NewId()
        self._slicerpop.Append(id, '&Change scale')
        wx.EVT_MENU(self, id, self._onProperties)
        id = wx.NewId()
        self._slicerpop.Append(id, '&Reset Graph')
        wx.EVT_MENU(self, id, self.onResetGraph)  
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(self._slicerpop, pos)
        
    def _on_remove_errors(self, evt):
        """
        Save name and dy of data in dictionary self.err_dy
        Create a new data1D with the same x, y
        vector and dy with zeros.
        post self.err_dy as event (ErrorDataEvent) for any object
        which wants to reconstruct the initial data.
        
        :param evt: Menu event
        
        """
        if not self.graph.selected_plottable == None:
            ## store existing dy
            name =self.plots[self.graph.selected_plottable].name
            dy = self.plots[self.graph.selected_plottable].dy
            self.err_dy[name] = dy
            ## Create a new dy for a new plottable
            #import numpy
            dy = numpy.zeros(len(self.plots[self.graph.selected_plottable].y))
            selected_plot = self.plots[self.graph.selected_plottable]
            
            if selected_plot.__class__.__name__ == "Data1D":
                # Make sure that we can pass a basic Data1D
                dxl = None
                dxw = None
                if hasattr(selected_plot, "dxl"):
                    dxl = selected_plot.dxl
                if hasattr(selected_plot, "dxw"):
                    dxw = selected_plot.dxw
                new_plot = Data1D(x=selected_plot.x, y=selected_plot.y,
                               dx=selected_plot.dx, dy=dy)
                new_plot.dxl = dxl
                new_plot.dxw = dxw            
            else:
                 new_plot = Theory1D(x=selected_plot.x, 
                                     y=selected_plot.y, dy=dy)
            new_plot.interactive = True
            self.errors_hide = True
            new_plot.name = self.plots[self.graph.selected_plottable].name 
            if hasattr(self.plots[self.graph.selected_plottable], "group_id"):
                new_plot.group_id = self.plots[self.graph.selected_plottable].group_id
                if hasattr(self.plots[self.graph.selected_plottable], "id"):
                    new_plot.id = self.plots[self.graph.selected_plottable].id
                else:
                    new_plot.id = str(time.time())
            else:
                new_plot.group_id = str(time.time())
                new_plot.id = str(time.time())
            label, unit = self.plots[self.graph.selected_plottable].get_xaxis()
            new_plot.xaxis(label, unit)
            label, unit = self.plots[self.graph.selected_plottable].get_yaxis()
            new_plot.yaxis(label, unit)
            ## save the color of the selected plottable before it is deleted
            color = self.graph.plottables[self.plots[self.graph.selected_plottable]]
            self.graph.delete(self.plots[self.graph.selected_plottable])
            ## add newly created plottable to the graph with the save color
            self.graph.color += color
            self.graph.add(new_plot, color)
            ## transforming the view of the new data into the same of 
            #the previous data
            self._onEVT_FUNC_PROPERTY()
            ## save the plot 
            self.plots[self.graph.selected_plottable] = new_plot
            ## Render the graph
            self.graph.render(self)
            self.subplot.figure.canvas.draw_idle() 
            event = ErrorDataEvent(err_dy=self.err_dy)
            wx.PostEvent(self.parent, event)

    def _on_add_errors(self, evt):
        """
        create a new data1D witht the errors saved in self.err_dy
        to show errors of the plot.
        Compute reasonable errors for a data set without 
        errors and transorm the plottable to a Data1D
        
        :param evt: Menu event
        
        """
        if not self.graph.selected_plottable == None \
            and self.graph.selected_plottable in self.plots.keys():
            ##Reset the flag to display the hide option on the context menu
            self.errors_hide = False
            ## restore dy 
            length = len(self.plots[self.graph.selected_plottable].x)
            dy = numpy.zeros(length)
            selected_plot = self.plots[self.graph.selected_plottable]
            try:
                dy = self.err_dy[selected_plot.name]
            except:
                if hasattr(selected_plot, "dy"):
                    dy = selected_plot.dy
                else:
                    dy = numpy.zeros(selected_plot.dy)
            ## Create a new plottable data1D
            if selected_plot.__class__.__name__ == "Data1D":
                # Make sure that we can pass a basic Data1D
                dxl = None
                dxw = None
                if hasattr(selected_plot, "dxl"):
                    dxl = selected_plot.dxl
                if hasattr(selected_plot, "dxw"):
                    dxw = selected_plot.dxw
                new_plot = Data1D(x=selected_plot.x,
                                               y=selected_plot.y,
                                               dx=selected_plot.dx,
                                               dy=dy)
                new_plot.dxl = dxl
                new_plot.dxw = dxw                       
            else:
                ## Create a new plottable Theory1D
                new_plot = Theory1D(x=selected_plot.x, y=selected_plot.y, dy=dy)
            new_plot.interactive = True
            new_plot.name = self.plots[self.graph.selected_plottable].name 
            if hasattr(self.plots[self.graph.selected_plottable], "group_id"):
                new_plot.group_id = self.plots[self.graph.selected_plottable].group_id
                if hasattr(self.plots[self.graph.selected_plottable],"id"):
                    new_plot.id = self.plots[self.graph.selected_plottable].id
                else:
                    new_plot.id = str(time.time())
            else:
                new_plot.group_id = str(time.time())
                new_plot.id = str(time.time())
            
            label, unit = self.plots[self.graph.selected_plottable].get_xaxis()
            new_plot.xaxis(label, unit)
            label, unit = self.plots[self.graph.selected_plottable].get_yaxis()
            new_plot.yaxis(label, unit)
            ## save the color of the selected plottable before it is deleted
            color=self.graph.plottables[self.plots[self.graph.selected_plottable]]
            self.graph.delete(self.plots[self.graph.selected_plottable])
            self.graph.color += color
            ## add newly created plottable to the graph with the save color
            self.graph.add(new_plot, color)
            ## transforming the view of the new data into the same of
            # the previous data
            self._onEVT_FUNC_PROPERTY()
            ## save the plot 
            self.plots[self.graph.selected_plottable]=new_plot
            ## render the graph with its new content
            self.graph.render(self)
            self.subplot.figure.canvas.draw_idle() 
               
               
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
                out.write("<X>   <Y>   <dY>\n")
            else:
                out.write("<X>   <Y>\n")
                
            for i in range(len(data.x)):
                if has_errors:
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
        id = str(evt.GetId())
        if id in self.action_ids:         
            
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
