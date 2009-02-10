"""
This software was developed by the University of Tennessee as part of the
Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
project funded by the US National Science Foundation. 

See the license text in license.txt

copyright 2008, University of Tennessee
"""


import wx
import sys
import pylab

import danse.common.plottools
from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.plottables import Graph,Data1D
from sans.guicomm.events import EVT_NEW_PLOT,EVT_SLICER_PARS_UPDATE
from sans.guicomm.events import EVT_SLICER_PARS
from sans.guicomm.events import StatusEvent ,NewPlotEvent,SlicerEvent
from sans.guiframe.utils import PanelMenu
from binder import BindArtist
from Plotter1D import ModelPanel1D
(InternalEvent, EVT_INTERNAL)   = wx.lib.newevent.NewEvent()



DEFAULT_QMAX = 0.05
DEFAULT_QSTEP = 0.001
DEFAULT_BEAM = 0.005
BIN_WIDTH = 1.0




class ModelPanel2D( ModelPanel1D):
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
        ModelPanel1D.__init__(self, parent, id = id, style = style, **kwargs)
        
        ## Reference to the parent window
        self.parent = parent
        ## Plottables
        self.plots = {}
        self.data2D= data2d
        self.data =data2d.data
        ## Unique ID (from gui_manager)
        self.uid = None
        
        ## Action IDs for internal call-backs
        self.action_ids = {}
        self.connect = BindArtist(self.subplot.figure)
        
        # Beam stop
        self.beamstop_radius = DEFAULT_BEAM
       
        self.slicer_z = 5
        self.slicer = None
        #self.parent.Bind(EVT_INTERNAL, self._onEVT_INTERNAL)
        self.Bind(EVT_INTERNAL, self._onEVT_INTERNAL)
        self.axes_frozen = False
        
        self.panel_slicer=None
        #self.parent.Bind(EVT_SLICER_PARS, self.onParamChange)
        ## Graph        
        self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ","cm^{-1}")
        self.graph.render(self)
        #self.Bind(boxSum.EVT_SLICER_PARS_UPDATE, self._onEVT_SLICER_PARS)
        self.Bind(EVT_SLICER_PARS, self._onEVT_SLICER_PARS)
        self.Bind(EVT_SLICER_PARS_UPDATE, self._onEVT_SLICER_PANEL)
        
        
    def _onEVT_SLICER_PARS(self, event):
        #print "paramaters entered on slicer panel", event.type, event.params
        self.slicer.set_params(event.params)
        from sans.guicomm.events import SlicerPanelEvent
        wx.PostEvent(self.parent, SlicerPanelEvent (panel= self.panel_slicer))
        
        
    def _onEVT_SLICER_PANEL(self, event):
        #print "box move plotter2D", event.type, event.params
        self.panel_slicer.set_slicer(event.type, event.params)
        from sans.guicomm.events import SlicerPanelEvent
        wx.PostEvent(self.parent, SlicerPanelEvent (panel= self.panel_slicer)) 
        
    def _onEVT_1DREPLOT(self, event):
        """
            Data is ready to be displayed
            
            #TODO: this name should be changed to something more appropriate
            # Don't forget that changing this name will mean changing code
            # in plotting.py
             
            @param event: data event
        """
              
        self.data2D= event.plot
        self.data =event.plot.data
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
                if hasattr(event.plot,"id"):
                    if event.plot.id==plottable.id :
                        self.graph.delete(plottable)
            
            self.plots[event.plot.name] = event.plot
            self.graph.add(self.plots[event.plot.name])
        else:
            # Update the plottable with the new data
            
            #TODO: we should have a method to do this, 
            #      something along the lines of:
            #      plottable1.update_data_from_plottable(plottable2)
            
            self.plots[event.plot.name].xmin = event.plot.xmin
            self.plots[event.plot.name].xmax = event.plot.xmax
            self.plots[event.plot.name].ymin = event.plot.ymin
            self.plots[event.plot.name].ymax = event.plot.ymax
            self.plots[event.plot.name].data = event.plot.data
            self.plots[event.plot.name].err_data = event.plot.err_data
            # update qmax with the new xmax of data plotted
            self.qmax= event.plot.xmax
            
        self.slicer= None
       
        # Check axis labels
        #TODO: Should re-factor this
        #if event.plot._xunit != self.graph.prop["xunit"]:
        self.graph.xaxis(event.plot._xaxis, event.plot._xunit)
            
        #if event.plot._yunit != self.graph.prop["yunit"]:
        self.graph.yaxis(event.plot._yaxis, event.plot._yunit)
        self.graph.title(self.data2D.name)
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
    
        item_list = self.parent.get_context_menu(self.graph)
        if (not item_list==None) and (not len(item_list)==0):
                
                for item in item_list:
                    try:
                        id = wx.NewId()
                        slicerpop.Append(id, item[0], item[1])
                        wx.EVT_MENU(self, id, item[2])
                    except:
                        pass
                        #print sys.exc_value
                        #print RuntimeError, "View1DPanel2D.onContextMenu: bad menu item"
        
        slicerpop.AppendSeparator()
        
        id = wx.NewId()
        slicerpop.Append(id, '&Perform circular average')
        wx.EVT_MENU(self, id, self.onCircular) 
        
        id = wx.NewId()
        slicerpop.Append(id, '&Sector [Q view]')
        wx.EVT_MENU(self, id, self.onSectorQ) 
        
        id = wx.NewId()
        slicerpop.Append(id, '&Annulus [Phi view ]')
        wx.EVT_MENU(self, id, self.onSectorPhi) 
       
        id = wx.NewId()
        slicerpop.Append(id, '&Box Sum')
        wx.EVT_MENU(self, id, self.onBoxSum) 
        
        id = wx.NewId()
        slicerpop.Append(id, '&Box averaging in Qx')
        wx.EVT_MENU(self, id, self.onBoxavgX) 
        
        id = wx.NewId()
        slicerpop.Append(id, '&Box averaging in Qy')
        wx.EVT_MENU(self, id, self.onBoxavgY) 
        if self.slicer !=None:
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
        
        # Option to save the data displayed
        id = wx.NewId()
        slicerpop.Append(id,'&Printer setup', 'Set image size')
        wx.EVT_MENU(self, id, self.onPrinterSetup)
        
        id = wx.NewId()
        slicerpop.Append(id,'&Printer Preview', 'Set image size')
        wx.EVT_MENU(self, id, self.onPrinterPreview)
    
        id = wx.NewId()
        slicerpop.Append(id,'&Print image', 'Print image ')
        wx.EVT_MENU(self, id, self.onPrint)
        slicerpop.AppendSeparator()
        id = wx.NewId()
        slicerpop.Append(id, '&Toggle Linear/Log scale')
        wx.EVT_MENU(self, id, self._onToggleScale) 
                 
      
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
        
    
        
        
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
        #print "come here"
        self.subplot.set_ylim(self.data2D.ymin, self.data2D.ymax)
        self.subplot.set_xlim(self.data2D.xmin, self.data2D.xmax)
       
        self.update()
        self.slicer.update()
        
        # Post slicer event
        event = self._getEmptySlicerEvent()
        event.type = self.slicer.__class__.__name__
        
        event.obj_class = self.slicer.__class__
        event.params = self.slicer.get_params()
        #print "Plotter2D: event.type",event.type,event.params, self.parent
        
        #wx.PostEvent(self.parent, event)
        wx.PostEvent(self, event)

    def onCircular(self, event):
        """
            perform circular averaging on Data2D
        """
        
        from DataLoader.manipulations import CircularAverage
        import math
        self.qmax= max(math.fabs(self.data2D.xmax),math.fabs(self.data2D.xmin))
        self.ymax=max(math.fabs(self.data2D.ymax),math.fabs(self.data2D.ymin))
        self.radius= math.sqrt( math.pow(self.qmax,2)+math.pow(self.ymax,2)) 
        #print "radius?",self.radius
        # bin_width = self.qmax -self.qmin/nbins 
        #nbins= 30
        bin_width = (self.qmax +self.qmax)/100
        
        Circle = CircularAverage( r_min=0, r_max=self.radius, bin_width=bin_width)
       
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
        #new_plot.info=self.data2D.info
        new_plot.interactive = True
        #print "loader output.detector",output.source
        new_plot.detector =self.data2D.detector
        
        # If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}","A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ","cm^{-1}")
        new_plot.group_id = "Circ avg "+ self.data2D.name
        new_plot.id = "Circ avg "+ self.data2D.name
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
        #print "onsector self.data2Dxmax",self.data2D.xmax, self.parent
        from SectorSlicer import SectorInteractor
        self.onClearSlicer(event)
        #wx.PostEvent(self.parent, InternalEvent(slicer= SectorInteractor))
        wx.PostEvent(self, InternalEvent(slicer= SectorInteractor))
        
    def onSectorPhi(self, event):
        """
            Perform sector averaging on Phi
        """
        from AnnulusSlicer import AnnulusInteractor
        self.onClearSlicer(event)
        #wx.PostEvent(self.parent, InternalEvent(slicer= AnnulusInteractor))
        wx.PostEvent(self, InternalEvent(slicer= AnnulusInteractor))
        
    def onBoxSum(self,event):
        from boxSum import BoxSum
        self.onClearSlicer(event)
        #wx.PostEvent(self.parent, InternalEvent(slicer= BoxSum))
        if not self.slicer == None:  
            self.slicer.clear()             
        self.slicer_z += 1
        self.slicer =  BoxSum(self, self.subplot, zorder=self.slicer_z)
        #print "come here"
        self.subplot.set_ylim(self.data2D.ymin, self.data2D.ymax)
        self.subplot.set_xlim(self.data2D.xmin, self.data2D.xmax)
       
        self.update()
        self.slicer.update()
        
        # Post slicer event
        event = self._getEmptySlicerEvent()
        event.type = self.slicer.__class__.__name__
        
        
        event.obj_class = self.slicer.__class__
        event.params = self.slicer.get_params()
        #print "Plotter2D: event.type",event.type,event.params, self.parent
        
        from slicerpanel import SlicerPanel
        new_panel = SlicerPanel(parent= self.parent,id= -1,base= self,type=event.type,
                                 params=event.params, style=wx.RAISED_BORDER)
        #new_panel.set_slicer(self.slicer.__class__.__name__,
        new_panel.window_caption=self.slicer.__class__.__name__+" "+ str(self.data2D.name)
       
        self.panel_slicer= new_panel
        
        wx.PostEvent(self.panel_slicer, event)
        from sans.guicomm.events import SlicerPanelEvent
        wx.PostEvent(self.parent, SlicerPanelEvent (panel= self.panel_slicer))
        #print "finish box sum"
        
    def onBoxavgX(self,event):
        from boxSlicer import BoxInteractorX
        self.onClearSlicer(event)
        #wx.PostEvent(self.parent, InternalEvent(slicer= BoxInteractorX))
        wx.PostEvent(self, InternalEvent(slicer= BoxInteractorX))
       
       
    def onBoxavgY(self,event):
        from boxSlicer import BoxInteractorY
        self.onClearSlicer(event)
        wx.PostEvent(self, InternalEvent(slicer= BoxInteractorY))
        #wx.PostEvent(self.parent, InternalEvent(slicer= BoxInteractorY))
        
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
            #wx.PostEvent(self.parent, event)
            wx.PostEvent(self, event)
          
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
        
        """     
            #TODO: this name should be changed to something more appropriate
            # Don't forget that changing this name will mean changing code
            # in plotting.py
             
            # Update the plottable with the new data
            
            #TODO: we should have a method to do this, 
            #      something along the lines of:
            #      plottable1.update_data_from_plottable(plottable2)
            
            self.plots[event.plot.name].xmin = event.plot.xmin
            self.plots[event.plot.name].xmax = event.plot.xmax
            self.plots[event.plot.name].ymin = event.plot.ymin
            self.plots[event.plot.name].ymax = event.plot.ymax
            self.plots[event.plot.name].data = event.plot.data
            self.plots[event.plot.name].err_data = event.plot.err_data
        """