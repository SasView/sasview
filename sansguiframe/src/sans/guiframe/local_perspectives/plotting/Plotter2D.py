
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
import math
import numpy
import pylab
import danse.common.plottools
from danse.common.plottools.PlotPanel import PlotPanel
from danse.common.plottools.plottables import Graph
from danse.common.plottools.TextDialog import TextDialog
from sans.guiframe.events import EVT_NEW_PLOT
from sans.guiframe.events import EVT_SLICER_PARS
from sans.guiframe.events import StatusEvent 
from sans.guiframe.events import NewPlotEvent
from sans.guiframe.events import PanelOnFocusEvent
from sans.guiframe.events import SlicerEvent
from sans.guiframe.utils import PanelMenu
from binder import BindArtist
from Plotter1D import ModelPanel1D
from danse.common.plottools.toolbar import NavigationToolBar 
from sans.guiframe.dataFitting import Data1D
from matplotlib.font_manager import FontProperties
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
        self.title_label = None
        self.title_font = None
        self.title_color = 'black'
        ## Graph        
        self.graph = Graph()
        self.graph.xaxis("\\rm{Q}", 'A^{-1}')
        self.graph.yaxis("\\rm{Intensity} ", "cm^{-1}")
        self.graph.render(self)
        ## store default value of zmin and zmax 
        self.default_zmin_ctl = self.zmin_2D
        self.default_zmax_ctl = self.zmax_2D
       
    def onLeftDown(self, event): 
        """
        left button down and ready to drag
        
        """
        # Check that the LEFT button was pressed
        if event.button == 1:
            self.leftdown = True
            ax = event.inaxes
            if ax != None:
                self.xInit, self.yInit = event.xdata, event.ydata
        self.plottable_selected(self.data2D.id)
       
        self._manager.set_panel_on_focus(self)
        wx.PostEvent(self.parent, PanelOnFocusEvent(panel=self))
        
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
         
    def plot_data(self, data):
        """
        Data is ready to be displayed
        
        :TODO: this name should be changed to something more appropriate
             Don't forget that changing this name will mean changing code
             in plotting.py
         
        :param event: data event
        """
        xlo = None
        xhi = None
        ylo = None 
        yhi = None
        ## Update self.data2d with the current plot
        self.data2D = data
        if data.id in self.plots.keys():
            #replace
            xlo, xhi = self.subplot.get_xlim()
            ylo, yhi = self.subplot.get_ylim()
            self.graph.replace(data)
            self.plots[data.id] = data
        else:
            self.plots[data.id] = data
            self.graph.add(self.plots[data.id]) 
            # update qmax with the new xmax of data plotted
            self.qmax = data.xmax
            
        self.slicer = None
        # Check axis labels
        #TODO: Should re-factor this
        ## render the graph with its new content
                
        #data2D: put 'Pixel (Number)' for axis title and unit in case of having no detector info and none in _units
        if len(data.detector) < 1: 
            if len(data._xunit) < 1 and len(data._yunit) < 1:
                data._xaxis = '\\rm{x}'
                data._yaxis = '\\rm{y}'
                data._xunit = 'pixel'
                data._yunit = 'pixel'
        
        # graph properties
        self.graph.xaxis(data._xaxis, data._xunit)
        self.graph.yaxis(data._yaxis, data._yunit)
            
        data.label = self.title_label
        
        if data.label == None:
            data.label = data.name
            
        if not self.title_font:
            self.graph.title(data.label)
            self.graph.render(self)
            # Set the axis labels on subplot
            self._set_axis_labels()
            self.draw_plot()
        else:
            self.graph.render(self)
            self.draw_plot()
            self.subplot.set_title(label=data.label,
                                   fontproperties=self.title_font,
                                   color=self.title_color)
            self.subplot.figure.canvas.draw_idle() 
        
        
        ## store default value of zmin and zmax 
        self.default_zmin_ctl = self.zmin_2D
        self.default_zmax_ctl = self.zmax_2D
        # Recover the x,y limits
        if (xlo and xhi and ylo and yhi) != None:
            if (xlo > data.xmin and xhi < data.xmax and\
                        ylo > data.ymin and yhi < data.ymax):
                self.subplot.set_xlim((xlo, xhi))     
                self.subplot.set_ylim((ylo, yhi)) 
            else: 
                self.toolbar.update()
    def _set_axis_labels(self):
        """
        Set axis labels
        """
        data = self.data2D
        # control axis labels from the panel itself
        yname, yunits = data.get_yaxis()
        if self.yaxis_label != None:
            yname = self.yaxis_label
            yunits = self.yaxis_unit
        else:
            self.yaxis_label = yname
            self.yaxis_unit = yunits
        xname, xunits = data.get_xaxis()
        if self.xaxis_label != None:
            xname = self.xaxis_label
            xunits = self.xaxis_unit
        else:
            self.xaxis_label = xname
            self.xaxis_unit = xunits
        self.xaxis(xname, xunits, self.xaxis_font, self.xaxis_color)
        self.yaxis(yname, yunits, self.yaxis_font, self.yaxis_color)
        
    def onContextMenu(self, event):
        """
        2D plot context menu
        
        :param event: wx context event
        
        """
        slicerpop = PanelMenu()
        slicerpop.set_plots(self.plots)
        slicerpop.set_graph(self.graph)
             
        id = wx.NewId()
        slicerpop.Append(id, '&Save Image')
        wx.EVT_MENU(self, id, self.onSaveImage)
        
        id = wx.NewId()
        slicerpop.Append(id,'&Print Image', 'Print image')
        wx.EVT_MENU(self, id, self.onPrint)
        
        id = wx.NewId()
        slicerpop.Append(id,'&Print Preview', 'Print preview')
        wx.EVT_MENU(self, id, self.onPrinterPreview)

        id = wx.NewId()
        slicerpop.Append(id, '&Copy to Clipboard', 'Copy to the clipboard')
        wx.EVT_MENU(self, id, self.OnCopyFigureMenu)
        slicerpop.AppendSeparator()
        # saving data
        plot = self.data2D
        id = wx.NewId()
        name = plot.name
        slicerpop.Append(id, "&Save as a File (DAT)" )
        self.action_ids[str(id)] = plot
        wx.EVT_MENU(self, id, self._onSave)

        slicerpop.AppendSeparator()
        if len(self.data2D.detector) == 1:        
            
            item_list = self.parent.get_context_menu(self)
            if (not item_list == None) and (not len(item_list) == 0) and\
                self.data2D.name.split(" ")[0] != 'Residuals':  
                # The line above; Not for trunk
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
            slicerpop.Append(id, '&Perform Circular Average')
            wx.EVT_MENU(self, id, self.onCircular) \
            # For Masked Data
            if not plot.mask.all():
                id = wx.NewId()
                slicerpop.Append(id, '&Masked Circular Average')
                wx.EVT_MENU(self, id, self.onMaskedCircular) 
            id = wx.NewId()
            slicerpop.Append(id, '&Sector [Q View]')
            wx.EVT_MENU(self, id, self.onSectorQ) 
            id = wx.NewId()
            slicerpop.Append(id, '&Annulus [Phi View ]')
            wx.EVT_MENU(self, id, self.onSectorPhi) 
            id = wx.NewId()
            slicerpop.Append(id, '&Box Sum')
            wx.EVT_MENU(self, id, self.onBoxSum) 
            id = wx.NewId()
            slicerpop.Append(id, '&Box Averaging in Qx')
            wx.EVT_MENU(self, id, self.onBoxavgX) 
            id = wx.NewId()
            slicerpop.Append(id, '&Box Averaging in Qy')
            wx.EVT_MENU(self, id, self.onBoxavgY) 
            if self.slicer != None:
                id = wx.NewId()
                slicerpop.Append(id, '&Clear Slicer')
                wx.EVT_MENU(self, id,  self.onClearSlicer) 
                if self.slicer.__class__.__name__  != "BoxSum":
                    id = wx.NewId()
                    slicerpop.Append(id, '&Edit Slicer Parameters')
                    wx.EVT_MENU(self, id, self._onEditSlicer) 
            slicerpop.AppendSeparator() 
            
        id = wx.NewId()
        slicerpop.Append(id, '&Edit Label', 'Edit Label')
        wx.EVT_MENU(self, id, self.onEditLabels)
        slicerpop.AppendSeparator()
        
        id = wx.NewId()
        slicerpop.Append(id, '&Modify Y Axis Label')
        wx.EVT_MENU(self, id, self._on_yaxis_label)     
        id = wx.NewId()
        slicerpop.Append(id, '&Modify X Axis Label')
        wx.EVT_MENU(self, id, self._on_xaxis_label)
        slicerpop.AppendSeparator()
        
        id = wx.NewId()
        slicerpop.Append(id, '&2D Color Map')
        wx.EVT_MENU(self, id, self._onEditDetector)
        slicerpop.AppendSeparator()
        
        id = wx.NewId()
        slicerpop.Append(id, '&Toggle Linear/Log Scale')
        wx.EVT_MENU(self, id, self._onToggleScale) 
        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)
            
    def onEditLabels(self, event):
        """
        Edit legend label
        """
        selected_plot = self.plots[self.graph.selected_plottable]
        label = selected_plot.label
        dial = TextDialog(None, -1, 'Change Label', label)
        if dial.ShowModal() == wx.ID_OK:
            try:
                FONT = FontProperties()
                newlabel = dial.getText()
                font = FONT.copy()
                font.set_size(dial.getSize())
                font.set_family(dial.getFamily())
                font.set_style(dial.getStyle())
                font.set_weight(dial.getWeight())
                colour = dial.getColor()
                if len(newlabel) > 0:
                    selected_plot.label = newlabel
                    self.title_label = selected_plot.label
                    self.title_font = font
                    self.title_color = colour
                    ## render the graph
                    self.subplot.set_title(label=self.title_label,
                                           fontproperties=self.title_font,
                                           color=self.title_color)
                    self.subplot.figure.canvas.draw_idle()  
            except:
                if self.parent != None:
                    from sans.guiframe.events import StatusEvent 
                    msg= "Add Text: Error. Check your property values..."
                    wx.PostEvent(self.parent, StatusEvent(status = msg ))
                else:
                    raise
        dial.Destroy()

        
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
        self.draw_plot()
        
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
        
    def onMaskedCircular(self, event):
        """
        perform circular averaging on Data2D with mask if it exists
        
        :param event: wx.menu event
        
        """
        self.onCircular(event, True)
        
    def onCircular(self, event, ismask=False):
        """
        perform circular averaging on Data2D
        
        :param event: wx.menu event
        
        """
        # Find the best number of bins
        npt = math.sqrt(len(self.data2D.data[numpy.isfinite(self.data2D.data)]))
        npt = math.floor(npt)
        from sans.dataloader.manipulations import CircularAverage
        ## compute the maximum radius of data2D
        self.qmax = max(math.fabs(self.data2D.xmax), 
                        math.fabs(self.data2D.xmin))
        self.ymax = max(math.fabs(self.data2D.ymax),
                        math.fabs(self.data2D.ymin))
        self.radius = math.sqrt(math.pow(self.qmax, 2)+ math.pow(self.ymax, 2)) 
        ##Compute beam width
        bin_width = (self.qmax + self.qmax)/npt
        ## Create data1D circular average of data2D
        Circle = CircularAverage(r_min=0, r_max=self.radius, 
                                 bin_width=bin_width)
        circ = Circle(self.data2D, ismask=ismask)
        from sans.guiframe.dataFitting import Data1D
        if hasattr(circ, "dxl"):
            dxl = circ.dxl
        else:
            dxl = None
        if hasattr(circ, "dxw"):
            dxw = circ.dxw
        else:
            dxw = None

        new_plot = Data1D(x=circ.x, y=circ.y, dy=circ.dy, dx=circ.dx)
        new_plot.dxl = dxl
        new_plot.dxw = dxw
        new_plot.name = "Circ avg " + self.data2D.name
        new_plot.source = self.data2D.source
        #new_plot.info = self.data2D.info
        new_plot.interactive = True
        new_plot.detector = self.data2D.detector
        
        ## If the data file does not tell us what the axes are, just assume...
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        if hasattr(self.data2D, "scale") and \
                    self.data2D.scale == 'linear':
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "normalized")
        else:
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
        from sans.guiframe.events import SlicerPanelEvent
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
            
    def _onSave(self, evt):
        """
        Save a data set to a dat(text) file
        
        :param evt: Menu event
        
        """
        id = str(evt.GetId())
        if id in self.action_ids:         
            
            path = None
            wildcard = "IGOR/DAT 2D file in Q_map (*.dat)|*.DAT"
            dlg = wx.FileDialog(self, "Choose a file",
                                self._default_save_location,
                                 "", wildcard , wx.SAVE)
           
            if dlg.ShowModal() == wx.ID_OK:
                path = dlg.GetPath()
                # ext_num = 0 for .txt, ext_num = 1 for .xml
                # This is MAC Fix
                ext_num = dlg.GetFilterIndex()
                if ext_num == 0:
                    format = '.dat'
                else:
                    format = ''
                path = os.path.splitext(path)[0] + format
                mypath = os.path.basename(path)
                
                #TODO: This is bad design. The DataLoader is designed 
                #to recognize extensions.
                # It should be a simple matter of calling the .
                #save(file, data, '.xml') method
                # of the DataLoader.loader.Loader class.
                from sans.dataloader.loader import  Loader
                #Instantiate a loader 
                loader = Loader() 
                data = self.data2D

                format = ".dat"
                if os.path.splitext(mypath)[1].lower() == format:
                    # Make sure the ext included in the file name
                    # especially on MAC
                    fName = os.path.splitext(path)[0] + format
                    loader.save(fName, data, format)
                try:
                    self._default_save_location = os.path.dirname(path)
                except:
                    pass    
            dlg.Destroy()