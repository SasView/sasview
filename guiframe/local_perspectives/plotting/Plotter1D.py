"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""


import wx
import sys
import danse.common.plottools
from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.plottables import Graph,Data1D
from sans.guicomm.events import EVT_NEW_PLOT
from sans.guicomm.events import StatusEvent ,NewPlotEvent


from SlicerParameters import SlicerEvent
from binder import BindArtist
(InternalEvent, EVT_INTERNAL)   = wx.lib.newevent.NewEvent()
#from SlicerParameters import SlicerEvent
#(InternalEvent, EVT_INTERNAL)   = wx.lib.newevent.NewEvent()
DEFAULT_QMAX = 0.05

DEFAULT_QSTEP = 0.001
DEFAULT_BEAM = 0.005
BIN_WIDTH =1
import pylab

class PanelMenu(wx.Menu):
    plots = None
    graph = None
    
    def set_plots(self, plots):
        self.plots = plots
    
    def set_graph(self, graph):
        self.graph = graph
class ModelPanel1D(PlotPanel):
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
            @param event: data event
        """
        #TODO: Check for existence of plot attribute

        # Check whether this is a replot. If we ask for a replot
        # and the plottable no longer exists, ignore the event.
        if hasattr(event, "update") and event.update==True \
            and event.plot.name not in self.plots.keys():
            return
        
        if hasattr(event, "reset"):
            self._reset()
        
        is_new = True
        if event.plot.name in self.plots.keys():
            # Check whether the class of plottable changed
            if not event.plot.__class__==self.plots[event.plot.name].__class__:
                #overwrite a plottable using the same name
                self.graph.delete(self.plots[event.plot.name])
            else:
                # plottable is already draw on the panel
                is_new = False

           
        if is_new:
            # a new plottable overwrites a plotted one  using the same id
            for plottable in self.plots.itervalues():
                if event.plot.id==plottable.id :
                    self.graph.delete(plottable)
            
            self.plots[event.plot.name] = event.plot
            self.graph.add(self.plots[event.plot.name])
        else:
            #replot the graph
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
      
        # Set the view scale for all plots
       
        self._onEVT_FUNC_PROPERTY()
    
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()

    def onLeftDown(self,event): 
        """ left button down and ready to drag"""
           
        PlotPanel.onLeftDown(self, event)
        ax = event.inaxes
        if ax != None:
            position = "x: %8.3g    y: %8.3g" % (event.xdata, event.ydata)
            wx.PostEvent(self.parent, StatusEvent(status=position))

    def _onRemove(self, event):
        """
        """
        if not self.graph.selected_plottable == None:
            print self.graph.selected_plottable
            
            
            self.graph.delete(self.plots[self.graph.selected_plottable])
            del self.plots[self.graph.selected_plottable]
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
                
            # Option to delete plottable
            id = wx.NewId()
            slicerpop.Append(id, "Remove %s curve" % name)
            self.action_ids[str(id)] = plot
            wx.EVT_MENU(self, id, self._onRemove)
            
            # Option to hide
            #TODO: implement functionality to hide a plottable (legend click)
            slicerpop.AppendSeparator()
                
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
        
        if self.graph.selected_plottable in self.plots:
            if self.plots[self.graph.selected_plottable].__class__.__name__=="Theory1D":
                id = wx.NewId()
                slicerpop.Append(id, '&Add errors to data')
                wx.EVT_MENU(self, id, self._on_add_errors)
            else:
                id = wx.NewId()
                slicerpop.Append(id, '&Linear fit')
                wx.EVT_MENU(self, id, self.onFitting)
                
        

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
        import time
        
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
            if hasattr(self.plots[self.graph.selected_plottable], "group_id"):
                new_plot.group_id = self.plots[self.graph.selected_plottable].group_id
            else:
                new_plot.group_id = str(time.time())
            
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
       