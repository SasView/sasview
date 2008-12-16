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
class View1DPanel1D(PlotPanel):
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
        #print "model panel name",event.plot.name
        if event.plot.name in self.plots.keys():
            # Check whether the class of plottable changed
            #print "model panel",event.plot.name,event.plot.__class__
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
        
class View1DPanel2D( View1DPanel1D):
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
    
    
    def __init__(self, parent, id = -1,data2d=None, color = None,\
        dpi = None, style = wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        """
            Initialize the panel
        """
        View1DPanel1D.__init__(self, parent, id = id, style = style, **kwargs)
        
        ## Reference to the parent window
        self.parent = parent
        ## Plottables
        self.plots = {}
        self.data2D= data2d
        self.data = data2d.data
        ## Unique ID (from gui_manager)
        self.uid = None
        
        ## Action IDs for internal call-backs
        self.action_ids = {}
        self.connect = BindArtist(self.subplot.figure)
        
        # Beam stop
        self.beamstop_radius = DEFAULT_BEAM
        # Slicer
        if data2d.xmax==None:
            data2d.xmax=DEFAULT_QMAX
        
        self.qmax = data2d.xmax
        if data2d.ymax==None:
            data2d.ymax=DEFAULT_QMAX
        self.imax = data2d.ymax
      
        self.qstep = DEFAULT_QSTEP
        print "panel2D qmax",self.qmax,
        self.x = pylab.arange(-1*self.qmax, self.qmax+self.qstep*0.01, self.qstep)
        self.y = pylab.arange(-1*self.imax, self.imax+self.qstep*0.01, self.qstep)

        self.slicer_z = 5
        self.slicer = None
        self.parent.Bind(EVT_INTERNAL, self._onEVT_INTERNAL)
        self.axes_frozen = False
        
       
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
                self.graph.delete(self.plots[event.plot.name])
            else:
                is_new = False
        self.plots[event.plot.name] = event.plot
        #if is_new:
        self.graph.add(self.plots[event.plot.name])
        

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
            2D plot context menu
            @param event: wx context event
        """
        
        #slicerpop = wx.Menu()
        slicerpop = PanelMenu()
        slicerpop.set_plots(self.plots)
        slicerpop.set_graph(self.graph)
                
        # Option to save the data displayed
    
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
                        print RuntimeError, "View1DPanel2D.onContextMenu: bad menu item"
        
        slicerpop.AppendSeparator()
        
        id = wx.NewId()
        slicerpop.Append(id, '&Perform circular average')
        wx.EVT_MENU(self, id, self.onCircular) 
        
        id = wx.NewId()
        slicerpop.Append(id, '&Sector Q')
        wx.EVT_MENU(self, id, self.onSectorQ) 
        
        id = wx.NewId()
        slicerpop.Append(id, '&Sector Phi')
        wx.EVT_MENU(self, id, self.onSectorPhi) 
      
        
        id = wx.NewId()
        slicerpop.Append(id, '&Clear slicer')
        wx.EVT_MENU(self, id,  self.onClearSlicer) 
        
        id = wx.NewId()
        slicerpop.Append(id, '&Edit Slicer Parameters')
        wx.EVT_MENU(self, id, self._onEditSlicer) 
        
        slicerpop.AppendSeparator()
        
        id = wx.NewId()
        slicerpop.Append(id, '&Save image')
        wx.EVT_MENU(self, id, self.onSaveImage) 
     
        id = wx.NewId()
        slicerpop.Append(id, '&Toggle Linear/Log scale')
        wx.EVT_MENU(self, id, self._onToggleScale) 
         
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
   
    def _setSlicer(self, slicer):
        # Clear current slicer
        #printEVT("Plotter2D._setSlicer %s" % slicer)
        
        if not self.slicer == None:  
            self.slicer.clear()            
            
        self.slicer_z += 1
        self.slicer = slicer(self, self.subplot, zorder=self.slicer_z)
        self.subplot.set_ylim(-self.qmax, self.qmax)
        self.subplot.set_xlim(-self.qmax, self.qmax)
        self.update()
        self.slicer.update()
        
        
    def get_corrected_data(self):
        # Protect against empty data set
        if self.data == None:
            return None
        import copy
        output = copy.deepcopy(self.data)
        return output
    def freeze_axes(self):
        self.axes_frozen = True
        
    def thaw_axes(self):
        self.axes_frozen = False
        
    def onMouseMotion(self,event):
        pass
    def onWheel(self, event):
        pass    
    def update(self, draw=True):
        """
            Respond to changes in the model by recalculating the 
            profiles and resetting the widgets.
        """
        #self.slicer.update()
        self.draw()
        
        
    def _getEmptySlicerEvent(self):
        return SlicerEvent(type=None,
                           params=None,
                           obj_class=None)
    def _onEVT_INTERNAL(self, event):
        """
            I don't understand why Unbind followed by a Bind
            using a modified self.slicer doesn't work.
            For now, I post a clear event followed by
            a new slicer event...
        """
        self._setSlicer(event.slicer)
            
    def _setSlicer(self, slicer):
        # Clear current slicer
        #printEVT("Plotter2D._setSlicer %s" % slicer)
        
        if not self.slicer == None:  
            self.slicer.clear()            
            
        self.slicer_z += 1
        self.slicer = slicer(self, self.subplot, zorder=self.slicer_z)
        self.subplot.set_ylim(-self.qmax, self.qmax)
        self.subplot.set_xlim(-self.qmax, self.qmax)
        self.update()
        self.slicer.update()
        
        # Post slicer event
        event = self._getEmptySlicerEvent()
        event.type = self.slicer.__class__.__name__
        event.obj_class = self.slicer.__class__
        event.params = self.slicer.get_params()
        wx.PostEvent(self.parent, event)

    def onCircular(self, event):
        """
            perform circular averaging on Data2D
        """
        
        from DataLoader.manipulations import CircularAverage
        #Circle = CircularAverage( r_min= -self.qmax, r_max= self.qmax, bin_width=BIN_WIDTH )
        Circle = CircularAverage( r_min= -1, r_max= 1, bin_width=0.001 )
        circ = Circle(self.data2D)
        from sans.guiframe.dataFitting import Data1D
        if hasattr(circ,"dxl"):
            dxl= circ.dxl
        else:
            dxl= None
        if hasattr(circ,"dxw"):
            dxw= circ.dxw
        else:
            dxw= None
            
        new_plot = Data1D(x=circ.x,y=circ.y,dy=circ.dy,dxl=dxl,dxw=dxw)
        new_plot.name = "Circ avg "+ self.data2D.name
        new_plot.source=self.data2D.source
        new_plot.info=self.data2D.info
        new_plot.interactive = True
        #print "loader output.detector",output.source
        new_plot.detector =self.data2D.detector
        
        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{q}","A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        new_plot.group_id = "Circ avg "+ self.data2D.name
        self.scale = 'log'
        wx.PostEvent(self.parent, NewPlotEvent(plot=new_plot, title=new_plot.name))
        
        
    def _onEditSlicer(self, event):
        if self.slicer !=None:
            from SlicerParameters import SlicerParameterPanel
            dialog = SlicerParameterPanel(self.parent, -1, "Slicer Parameters")
            dialog.set_slicer(self.slicer.__class__.__name__,
                            self.slicer.get_params())
            if dialog.ShowModal() == wx.ID_OK:
                dialog.Destroy() 
        
    def onSectorQ(self, event):
        """
            Perform sector averaging on Q
        """
        
        from SectorSlicer import SectorInteractorQ
        self.onClearSlicer(event)
        wx.PostEvent(self.parent, InternalEvent(slicer= SectorInteractorQ))
        
    def onSectorPhi(self, event):
        """
            Perform sector averaging on Phi
        """
        from SectorSlicer import SectorInteractorPhi
        self.onClearSlicer(event)
        wx.PostEvent(self.parent, InternalEvent(slicer= SectorInteractorPhi))
        
       
    def onClearSlicer(self, event):
        """
            Clear the slicer on the plot
        """
        if not self.slicer==None:
            self.slicer.clear()
            self.subplot.figure.canvas.draw()
            self.slicer = None
        
            # Post slicer None event
            event = self._getEmptySlicerEvent()
            wx.PostEvent(self.parent, event)
          
    def _onEditDetector(self, event):
        print "on parameter"
        
        
    def _onToggleScale(self, event):
        """
            toggle pixel scale and replot image
        """
        if self.scale == 'log':
            self.scale = 'linear'
        else:
            self.scale = 'log'
        self.image(self.data,self.xmin_2D,self.xmax_2D,self.ymin_2D,
                   self.ymax_2D,self.zmin_2D ,self.zmax_2D )
        wx.PostEvent(self.parent, StatusEvent(status="Image is in %s scale"%self.scale))
        
        
        
        
        
        
class View1DModelPanel2D( View1DPanel2D):
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
    
    def __init__(self, parent, id = -1,color = None,\
        dpi = None, style = wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        """
            Initialize the panel
        """
        View1DPanel2D.__init__(self, parent, id = id, style = style, **kwargs)
        ## Reference to the parent window
        self.parent = parent
        ## Plottables
        self.plots = {}
        print "Model 2d panel"
        
        ## Unique ID (from gui_manager)
        self.uid = None
        
        ## Action IDs for internal call-backs
        self.action_ids = {}
        
        ## Graph        
        self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        self.graph.render(self)
        
        
    def onContextMenu(self, event):
        # Slicer plot popup menu
         #slicerpop = wx.Menu()
        slicerpop = PanelMenu()
        slicerpop.set_plots(self.plots)
        slicerpop.set_graph(self.graph)
                
        # Option to save the data displayed
    
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
                        print RuntimeError, "View1DPanel2D.onContextMenu: bad menu item"
        
        slicerpop.AppendSeparator()
      
        id = wx.NewId()
        slicerpop.Append(id, '&sector averaging')
        wx.EVT_MENU(self, id, self.onSectorSlicer) 
        
    
        
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
   

        
        