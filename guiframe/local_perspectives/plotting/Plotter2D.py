
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
import math
import pylab
import danse.common.plottools
from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.plottables import Graph
from sans.guicomm.events import EVT_NEW_PLOT
from sans.guicomm.events import EVT_SLICER_PARS
from sans.guicomm.events import StatusEvent 
from sans.guicomm.events import NewPlotEvent
from sans.guicomm.events import SlicerEvent
from sans.guiframe.utils import PanelMenu
from binder import BindArtist
from Plotter1D import ModelPanel1D
from danse.common.plottools.toolbar import NavigationToolBar 
from sans.guiframe.dataFitting import Data1D
(InternalEvent, EVT_INTERNAL) = wx.lib.newevent.NewEvent()

DEFAULT_QMAX = 0.05
DEFAULT_QSTEP = 0.001
DEFAULT_BEAM = 0.005
BIN_WIDTH = 1.0


class NavigationToolBar2D(NavigationToolBar):
    """
    """
    def __init__(self, canvas, parent=None):
        NavigationToolBar.__init__(self, canvas=canvas, parent=parent)
        
    def delete_option(self):
        """
        remove default toolbar item
        """
        #delete reset button
        self.DeleteToolByPos(0) 
        #delete dragging
        self.DeleteToolByPos(2) 
        #delete unwanted button that configures subplot parameters
        self.DeleteToolByPos(4)
        
    def add_option(self):
        """
        add item to the toolbar
        """
        #add print button
        id_print = wx.NewId()
        print_bmp =  wx.ArtProvider.GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR)
        self.AddSimpleTool(id_print, print_bmp,
                           'Print', 'Activate printing')
        wx.EVT_TOOL(self, id_print, self.on_print)
        
        
class ModelPanel2D(ModelPanel1D):
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
    
    
    def __init__(self, parent, id=-1, data2d=None, color = None,
                 dpi=None, style=wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        """
        Initialize the panel
        """
        ModelPanel1D.__init__(self, parent, id=id, style=style, **kwargs)
        
        ## Reference to the parent window
        self.parent = parent
        ## Dictionary containing Plottables
        self.plots = {}
        ## Save reference of the current plotted 
        self.data2D = data2d
        ## Unique ID (from gui_manager)
        self.uid = None
        ## Action IDs for internal call-backs
        self.action_ids = {}
        ## Create Artist and bind it
        self.connect = BindArtist(self.subplot.figure)
        ## Beam stop
        self.beamstop_radius = DEFAULT_BEAM
        ## to set the order of lines drawn first.
        self.slicer_z = 5
        ## Reference to the current slicer
        self.slicer = None
        ## event to send slicer info 
        self.Bind(EVT_INTERNAL, self._onEVT_INTERNAL)
        
        self.axes_frozen = False
        ## panel that contains result from slicer motion (ex: Boxsum info)
        self.panel_slicer = None
        ## Graph        
        self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ", "cm^{-1}")
        self.graph.render(self)
        ## store default value of zmin and zmax 
        self.default_zmin_ctl = self.zmin_2D
        self.default_zmax_ctl = self.zmax_2D
       
    def add_toolbar(self):
        """
        add toolbar
        """
        self.enable_toolbar = True
        self.toolbar = NavigationToolBar2D(parent=self, canvas=self.canvas)
        self.toolbar.Realize()
        # On Windows platform, default window size is incorrect, so set
        # toolbar width to figure width.
        tw, th = self.toolbar.GetSizeTuple()
        fw, fh = self.canvas.GetSizeTuple()
        self.toolbar.SetSize(wx.Size(fw, th))
        self.sizer.Add(self.toolbar, 0, wx.LEFT|wx.EXPAND)
        # update the axes menu on the toolbar
        self.toolbar.update()
         
    def _onEVT_1DREPLOT(self, event):
        """
        Data is ready to be displayed
        
        :TODO: this name should be changed to something more appropriate
             Don't forget that changing this name will mean changing code
             in plotting.py
         
        :param event: data event
        """
        ## Update self.data2d with the current plot
        self.data2D = event.plot
        
        #TODO: Check for existence of plot attribute
        
        # Check whether this is a replot. If we ask for a replot
        # and the plottable no longer exists, ignore the event.
        if hasattr(event, "update") and event.update == True \
            and event.plot.name not in self.plots.keys():
            return
        if hasattr(event, "reset"):
            self._reset()
        is_new = True
        if event.plot.name in self.plots.keys():
            # Check whether the class of plottable changed
            if not event.plot.__class__ == self.plots[event.plot.name].__class__:
                #overwrite a plottable using the same name
                self.graph.delete(self.plots[event.plot.name])
            else:
                # plottable is already draw on the panel
                is_new = False
           
        if is_new:
            # a new plottable overwrites a plotted one  using the same id
            for plottable in self.plots.itervalues():
                if hasattr(event.plot,"id"):
                    if event.plot.id == plottable.id:
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
            self.plots[event.plot.name].qx_data = event.plot.qx_data
            self.plots[event.plot.name].qy_data = event.plot.qy_data
            self.plots[event.plot.name].err_data = event.plot.err_data
            # update qmax with the new xmax of data plotted
            self.qmax = event.plot.xmax
            
        self.slicer = None
        # Check axis labels
        #TODO: Should re-factor this
        ## render the graph with its new content
                
        #data2D: put 'Pixel (Number)' for axis title and unit in case of having no detector info and none in _units
        if len(self.data2D.detector) < 1: 
            if len(event.plot._xunit) < 1 and len(event.plot._yunit) < 1:
                event.plot._xaxis = '\\rm{x}'
                event.plot._yaxis = '\\rm{y}'
                event.plot._xunit = 'pixel'
                event.plot._yunit = 'pixel'
        self.graph.xaxis(event.plot._xaxis, event.plot._xunit)
        self.graph.yaxis(event.plot._yaxis, event.plot._yunit)
        self.graph.title(self.data2D.name)
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()
        ## store default value of zmin and zmax 
        self.default_zmin_ctl = self.zmin_2D
        self.default_zmax_ctl = self.zmax_2D

    def onContextMenu(self, event):
        """
        2D plot context menu
        
        :param event: wx context event
        
        """
        slicerpop = PanelMenu()
        slicerpop.set_plots(self.plots)
        slicerpop.set_graph(self.graph)
             
        id = wx.NewId()
        slicerpop.Append(id, '&Save image')
        wx.EVT_MENU(self, id, self.onSaveImage)
        
        id = wx.NewId()
        slicerpop.Append(id,'&Print image', 'Print image')
        wx.EVT_MENU(self, id, self.onPrint)
        
        id = wx.NewId()
        slicerpop.Append(id,'&Print Preview', 'image preview for print')
        wx.EVT_MENU(self, id, self.onPrinterPreview)
        
        slicerpop.AppendSeparator()
        if len(self.data2D.detector) == 1:        
            
            item_list = self.parent.get_context_menu(self.graph)
            if (not item_list == None) and (not len(item_list) == 0):
                for item in item_list:
                    try:
                        id = wx.NewId()
                        slicerpop.Append(id, item[0], item[1])
                        wx.EVT_MENU(self, id, item[2])
                    except:
                        msg = "ModelPanel1D.onContextMenu: "
                        msg += "bad menu item  %s"%sys.exc_value
                        wx.PostEvent(self.parent, StatusEvent(status=msg))
                        pass
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
            if self.slicer != None:
                id = wx.NewId()
                slicerpop.Append(id, '&Clear slicer')
                wx.EVT_MENU(self, id,  self.onClearSlicer) 
                if self.slicer.__class__.__name__  != "BoxSum":
                    id = wx.NewId()
                    slicerpop.Append(id, '&Edit Slicer Parameters')
                    wx.EVT_MENU(self, id, self._onEditSlicer) 
            slicerpop.AppendSeparator() 
        id = wx.NewId()
        slicerpop.Append(id, '&Detector Parameters')
        wx.EVT_MENU(self, id, self._onEditDetector)
        id = wx.NewId()
        slicerpop.Append(id, '&Toggle Linear/Log scale')
        wx.EVT_MENU(self, id, self._onToggleScale) 
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
   
    def _onEditDetector(self, event):
        """
        Allow to view and edits  detector parameters
        
        :param event: wx.menu event
        
        """
        import detector_dialog
        dialog = detector_dialog.DetectorDialog(self, -1,base=self.parent,
                       reset_zmin_ctl =self.default_zmin_ctl,
                       reset_zmax_ctl = self.default_zmax_ctl,cmap=self.cmap)
        ## info of current detector and data2D
        xnpts = len(self.data2D.x_bins)
        ynpts = len(self.data2D.y_bins)
        xmax = max(self.data2D.xmin, self.data2D.xmax)
        ymax = max(self.data2D.ymin, self.data2D.ymax)
        qmax = math.sqrt(math.pow(xmax, 2) + math.pow(ymax, 2))
        beam = self.data2D.xmin
        ## set dialog window content
        dialog.setContent(xnpts=xnpts,ynpts=ynpts,qmax=qmax,
                           beam=self.data2D.xmin,
                           zmin = self.zmin_2D,
                          zmax = self.zmax_2D)
        if dialog.ShowModal() == wx.ID_OK:
            evt = dialog.getContent()
            self.zmin_2D = evt.zmin
            self.zmax_2D = evt.zmax
            self.cmap = evt.cmap
        dialog.Destroy()
        ## Redraw the current image
        self.image(data=self.data2D.data,
                   qx_data=self.data2D.qx_data,
                   qy_data=self.data2D.qy_data,
                   xmin= self.data2D.xmin,
                   xmax= self.data2D.xmax,
                   ymin= self.data2D.ymin,
                   ymax= self.data2D.ymax,
                   zmin= self.zmin_2D,
                   zmax= self.zmax_2D,
                   cmap= self.cmap,
                   color=0, symbol=0, label=self.data2D.name)
        self.subplot.figure.canvas.draw_idle()
        
    def freeze_axes(self):
        """
        """
        self.axes_frozen = True
        
    def thaw_axes(self):
        """
        """
        self.axes_frozen = False
        
    def onMouseMotion(self,event):
        """
        """
        pass
    
    def onWheel(self, event):
        """
        """
        pass  
      
    def update(self, draw=True):
        """
        Respond to changes in the model by recalculating the 
        profiles and resetting the widgets.
        """
        self.draw()
        
    def _getEmptySlicerEvent(self):
        """
        create an empty slicervent 
        """
        return SlicerEvent(type=None, params=None, obj_class=None)
        
    def _onEVT_INTERNAL(self, event):
        """
        Draw the slicer
        
        :param event: wx.lib.newevent (SlicerEvent) containing slicer
            parameter
            
        """
        self._setSlicer(event.slicer)
            
    def _setSlicer(self, slicer):
        """
        Clear the previous slicer and create a new one.Post an internal
        event.
        
        :param slicer: slicer class to create
        
        """
        ## Clear current slicer
        if not self.slicer == None:  
            self.slicer.clear()            
        ## Create a new slicer    
        self.slicer_z += 1
        self.slicer = slicer(self, self.subplot, zorder=self.slicer_z)
        self.subplot.set_ylim(self.data2D.ymin, self.data2D.ymax)
        self.subplot.set_xlim(self.data2D.xmin, self.data2D.xmax)
        ## Draw slicer
        self.update()
        self.slicer.update()
        msg = "Plotter2D._setSlicer  %s"%self.slicer.__class__.__name__
        wx.PostEvent(self.parent, StatusEvent(status=msg))
        # Post slicer event
        event = self._getEmptySlicerEvent()
        event.type = self.slicer.__class__.__name__
        event.obj_class = self.slicer.__class__
        event.params = self.slicer.get_params()
        wx.PostEvent(self, event)

    def onCircular(self, event):
        """
        perform circular averaging on Data2D
        
        :param event: wx.menu event
        
        """
        from DataLoader.manipulations import CircularAverage
        ## compute the maximum radius of data2D
        self.qmax = max(math.fabs(self.data2D.xmax), 
                        math.fabs(self.data2D.xmin))
        self.ymax = max(math.fabs(self.data2D.ymax),
                        math.fabs(self.data2D.ymin))
        self.radius = math.sqrt(math.pow(self.qmax, 2)+ math.pow(self.ymax, 2)) 
        ##Compute beam width
        bin_width = (self.qmax + self.qmax)/100
        ## Create data1D circular average of data2D
        Circle = CircularAverage(r_min=0, r_max=self.radius, 
                                 bin_width=bin_width)
        circ = Circle(self.data2D)
        from sans.guiframe.dataFitting import Data1D
        if hasattr(circ, "dxl"):
            dxl = circ.dxl
        else:
            dxl = None
        if hasattr(circ, "dxw"):
            dxw = circ.dxw
        else:
            dxw = None
        new_plot = Data1D(x=circ.x, y=circ.y, dy=circ.dy)
        new_plot.dxl = dxl
        new_plot.dxw = dxw
        new_plot.name = "Circ avg " + self.data2D.name
        new_plot.source = self.data2D.source
        #new_plot.info = self.data2D.info
        new_plot.interactive = True
        new_plot.detector = self.data2D.detector
        ## If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")
        new_plot.group_id = "Circ avg " + self.data2D.name
        new_plot.id = "Circ avg " + self.data2D.name
        new_plot.is_data = True
        wx.PostEvent(self.parent, 
                     NewPlotEvent(plot=new_plot, title=new_plot.name))
       
    def _onEditSlicer(self, event):
        """
        Is available only when a slicer is drawn.Create a dialog 
        window where the user can enter value to reset slicer
        parameters.
        
        :param event: wx.menu event
        
        """
        if self.slicer != None:
            from SlicerParameters import SlicerParameterPanel
            dialog = SlicerParameterPanel(self, -1, "Slicer Parameters")
            dialog.set_slicer(self.slicer.__class__.__name__,
                            self.slicer.get_params())
            if dialog.ShowModal() == wx.ID_OK:
                dialog.Destroy() 
        
    def onSectorQ(self, event):
        """
        Perform sector averaging on Q and draw sector slicer
        """
        from SectorSlicer import SectorInteractor
        self.onClearSlicer(event)
        wx.PostEvent(self, InternalEvent(slicer=SectorInteractor))
        
    def onSectorPhi(self, event):
        """
        Perform sector averaging on Phi and draw annulus slicer
        """
        from AnnulusSlicer import AnnulusInteractor
        self.onClearSlicer(event)
        wx.PostEvent(self, InternalEvent(slicer=AnnulusInteractor))
        
    def onBoxSum(self, event):
        """
        """
        from boxSum import BoxSum
        self.onClearSlicer(event)
        self.slicer_z += 1
        self.slicer =  BoxSum(self, self.subplot, zorder=self.slicer_z)
        self.subplot.set_ylim(self.data2D.ymin, self.data2D.ymax)
        self.subplot.set_xlim(self.data2D.xmin, self.data2D.xmax)
        self.update()
        self.slicer.update()
        ## Value used to initially set the slicer panel
        type = self.slicer.__class__.__name__
        params = self.slicer.get_params()
        ## Create a new panel to display results of summation of Data2D
        from slicerpanel import SlicerPanel
        new_panel = SlicerPanel(parent=self.parent, id=-1,
                                    base=self, type=type,
                                    params=params, style=wx.RAISED_BORDER)
        
        new_panel.window_caption = self.slicer.__class__.__name__ + " " + \
                                    str(self.data2D.name)
        new_panel.window_name = self.slicer.__class__.__name__+ " " + \
                                    str(self.data2D.name)
        ## Store a reference of the new created panel
        self.panel_slicer = new_panel
        ## save the window_caption of the new panel in the current slicer
        self.slicer.set_panel_name(name=new_panel.window_caption)
        ## post slicer panel to guiframe to display it 
        from sans.guicomm.events import SlicerPanelEvent
        wx.PostEvent(self.parent, SlicerPanelEvent(panel=self.panel_slicer,
                                                    main_panel=self))

    def onBoxavgX(self,event):
        """
        Perform 2D data averaging on Qx
        Create a new slicer .
        
        :param event: wx.menu event
        """
        from boxSlicer import BoxInteractorX
        self.onClearSlicer(event)
        wx.PostEvent(self, InternalEvent(slicer=BoxInteractorX))
       
    def onBoxavgY(self,event):
        """
        Perform 2D data averaging on Qy
        Create a new slicer .
        
        :param event: wx.menu event
        
        """
        from boxSlicer import BoxInteractorY
        self.onClearSlicer(event)
        wx.PostEvent(self, InternalEvent(slicer=BoxInteractorY))
        
    def onClearSlicer(self, event):
        """
        Clear the slicer on the plot
        """
        if not self.slicer == None:
            self.slicer.clear()
            self.subplot.figure.canvas.draw()
            self.slicer = None
            # Post slicer None event
            event = self._getEmptySlicerEvent()
            wx.PostEvent(self, event)
   