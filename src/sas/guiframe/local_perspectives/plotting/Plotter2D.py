
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
import numpy
import logging
from sas.plottools.PlotPanel import PlotPanel
from sas.plottools.plottables import Graph
from sas.plottools.TextDialog import TextDialog
from sas.guiframe.events import StatusEvent
from sas.guiframe.events import NewPlotEvent
from sas.guiframe.events import PanelOnFocusEvent
from sas.guiframe.events import SlicerEvent
from sas.guiframe.utils import PanelMenu
from  sas.guiframe.local_perspectives.plotting.binder import BindArtist
from Plotter1D import ModelPanel1D
from sas.plottools.toolbar import NavigationToolBar
from matplotlib.font_manager import FontProperties
from graphAppearance import graphAppearance
(InternalEvent, EVT_INTERNAL) = wx.lib.newevent.NewEvent()

DEFAULT_QMAX = 0.05
DEFAULT_QSTEP = 0.001
DEFAULT_BEAM = 0.005
BIN_WIDTH = 1.0


def find_key(dic, val):
    """return the key of dictionary dic given the value"""
    return [k for k, v in dic.iteritems() if v == val][0]


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
        #add button
        id_context = wx.NewId()
        context_tip = 'Graph Menu'
        context = wx.ArtProvider.GetBitmap(wx.ART_LIST_VIEW, wx.ART_TOOLBAR)
        self.InsertSimpleTool(0, id_context, context, context_tip, context_tip)
        wx.EVT_TOOL(self, id_context, self.parent.onToolContextMenu)
        self.InsertSeparator(1)
        #add print button
        id_print = wx.NewId()
        print_bmp = wx.ArtProvider.GetBitmap(wx.ART_PRINT, wx.ART_TOOLBAR)
        self.AddSimpleTool(id_print, print_bmp, 'Print', 'Activate printing')
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


    def __init__(self, parent, id=-1, data2d=None, color=None,
                 dpi=None, style=wx.NO_FULL_REPAINT_ON_RESIZE, **kwargs):
        """
        Initialize the panel
        """
        ModelPanel1D.__init__(self, parent, id=id, style=style, **kwargs)
        self.parent = parent
        ## Reference to the parent window
        if hasattr(parent, "parent"):
            self.parent = self.parent.parent
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

    def on_plot_qrange(self, event=None):
        """
        On Qmin Qmax vertical line event
        """
        # Not implemented
        if event == None:
            return
        event.Skip()

    def onLeftDown(self, event):
        """
        left button down and ready to drag

        """
        # Check that the LEFT button was pressed
        PlotPanel.onLeftDown(self, event)
        ax = event.inaxes
        if ax != None:
            # data coordinate position
            pos_x = "%8.3g" % event.xdata
            pos_y = "%8.3g" % event.ydata
            position = "x: %s    y: %s" % (pos_x, pos_y)
            wx.PostEvent(self.parent, StatusEvent(status=position))
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
        _, th = self.toolbar.GetSizeTuple()
        fw, _ = self.canvas.GetSizeTuple()
        self.toolbar.SetSize(wx.Size(fw, th))
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
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
        if data.__class__.__name__ == 'Data1D':
            return
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
        if self._is_changed_legend_label:
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
        if not self.is_zoomed:
            return
        # Recover the x,y limits
        if xlo and xhi and ylo and yhi:
            if xlo > data.xmin and xhi < data.xmax and \
                        ylo > data.ymin and yhi < data.ymax:
                self.subplot.set_xlim((xlo, xhi))
                self.subplot.set_ylim((ylo, yhi))
            else:
                self.toolbar.update()
                self.is_zoomed = False

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
        self.xaxis(xname, xunits, self.xaxis_font,
                   self.xaxis_color, self.xaxis_tick)
        self.yaxis(yname, yunits, self.yaxis_font,
                   self.yaxis_color, self.yaxis_tick)

    def onContextMenu(self, event):
        """
        2D plot context menu

        :param event: wx context event

        """
        ids = iter(self._menu_ids)
        slicerpop = PanelMenu()
        slicerpop.set_plots(self.plots)
        slicerpop.set_graph(self.graph)

        wx_id = ids.next()
        slicerpop.Append(wx_id, '&Save Image')
        wx.EVT_MENU(self, wx_id, self.onSaveImage)

        wx_id = ids.next()
        slicerpop.Append(wx_id, '&Print Image', 'Print image')
        wx.EVT_MENU(self, wx_id, self.onPrint)

        wx_id = ids.next()
        slicerpop.Append(wx_id, '&Copy to Clipboard', 'Copy to the clipboard')
        wx.EVT_MENU(self, wx_id, self.OnCopyFigureMenu)
        slicerpop.AppendSeparator()
        # saving data
        plot = self.data2D
        wx_id = ids.next()
        slicerpop.Append(wx_id, "&Data Info")
        wx.EVT_MENU(self, wx_id, self._onDataShow)

        wx_id = ids.next()
        slicerpop.Append(wx_id, "&Save as a File (DAT)")
        self.action_ids[str(wx_id)] = plot
        wx.EVT_MENU(self, wx_id, self._onSave)

        slicerpop.AppendSeparator()
        if len(self.data2D.detector) == 1:
            item_list = self.parent.get_current_context_menu(self)
            if (not item_list == None) and (not len(item_list) == 0) and\
                self.data2D.name.split(" ")[0] != 'Residuals':
                # The line above; Not for trunk
                # Note: reusing menu ids for the sub-menus.  See Plotter1D.
                for item, wx_id in zip(item_list, self._menu_ids):
                    try:
                        slicerpop.Append(wx_id, item[0], item[1])
                        wx.EVT_MENU(self, wx_id, item[2])
                    except:
                        msg = "ModelPanel1D.onContextMenu: "
                        msg += "bad menu item  %s" % sys.exc_value
                        wx.PostEvent(self.parent, StatusEvent(status=msg))
                slicerpop.AppendSeparator()

            wx_id = ids.next()
            slicerpop.Append(wx_id, '&Perform Circular Average')
            wx.EVT_MENU(self, wx_id, self.onCircular) \
            # For Masked Data
            if not plot.mask.all():
                wx_id = ids.next()
                slicerpop.Append(wx_id, '&Masked Circular Average')
                wx.EVT_MENU(self, wx_id, self.onMaskedCircular)
            wx_id = ids.next()
            slicerpop.Append(wx_id, '&Sector [Q View]')
            wx.EVT_MENU(self, wx_id, self.onSectorQ)
            wx_id = ids.next()
            slicerpop.Append(wx_id, '&Annulus [Phi View ]')
            wx.EVT_MENU(self, wx_id, self.onSectorPhi)
            wx_id = ids.next()
            slicerpop.Append(wx_id, '&Box Sum')
            wx.EVT_MENU(self, wx_id, self.onBoxSum)
            wx_id = ids.next()
            slicerpop.Append(wx_id, '&Box Averaging in Qx')
            wx.EVT_MENU(self, wx_id, self.onBoxavgX)
            wx_id = ids.next()
            slicerpop.Append(wx_id, '&Box Averaging in Qy')
            wx.EVT_MENU(self, wx_id, self.onBoxavgY)
            if self.slicer != None:
                wx_id = ids.next()
                slicerpop.Append(wx_id, '&Clear Slicer')
                wx.EVT_MENU(self, wx_id, self.onClearSlicer)
                if self.slicer.__class__.__name__ != "BoxSum":
                    wx_id = ids.next()
                    slicerpop.Append(wx_id, '&Edit Slicer Parameters')
                    wx.EVT_MENU(self, wx_id, self._onEditSlicer)
            slicerpop.AppendSeparator()

        wx_id = ids.next()
        slicerpop.Append(wx_id, '&Edit Graph Label', 'Edit Graph Label')
        wx.EVT_MENU(self, wx_id, self.onEditLabels)
        slicerpop.AppendSeparator()

        # ILL mod here

        wx_id = ids.next()
        slicerpop.Append(wx_id, '&Modify graph appearance', 'Modify graph appearance')
        wx.EVT_MENU(self, wx_id, self.modifyGraphAppearance)
        slicerpop.AppendSeparator()

        wx_id = ids.next()
        slicerpop.Append(wx_id, '&2D Color Map')
        wx.EVT_MENU(self, wx_id, self._onEditDetector)
        slicerpop.AppendSeparator()

        wx_id = ids.next()
        slicerpop.Append(wx_id, '&Toggle Linear/Log Scale')
        wx.EVT_MENU(self, wx_id, self._onToggleScale)

        slicerpop.AppendSeparator()
        wx_id = ids.next()
        slicerpop.Append(wx_id, '&Window Title')
        wx.EVT_MENU(self, wx_id, self.onChangeCaption)

        try:
            pos_evt = event.GetPosition()
            pos = self.ScreenToClient(pos_evt)
        except:
            pos_x, pos_y = self.toolbar.GetPositionTuple()
            pos = (pos_x, pos_y + 5)
        self.PopupMenu(slicerpop, pos)

    def onEditLabels(self, event):
        """
        Edit legend label
        """
        try:
            selected_plot = self.plots[self.graph.selected_plottable]
        except:
            selected_plot = self.plots[self.data2D.id]
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
                    # update Label
                    selected_plot.label = newlabel
                    self.graph.title(newlabel)
                    self.title_label = selected_plot.label
                    self.title_font = font
                    self.title_color = colour
                    ## render the graph
                    self.subplot.set_title(label=self.title_label,
                                           fontproperties=self.title_font,
                                           color=self.title_color)
                    self._is_changed_legend_label = True
                    self.subplot.figure.canvas.draw_idle()
            except:
                msg = "Add Text: Error. Check your property values..."
                logging.error(msg)
                if self.parent != None:
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
        dial.Destroy()

    def _onEditDetector(self, event):
        """
        Allow to view and edits  detector parameters

        :param event: wx.menu event

        """
        import detector_dialog
        dialog = detector_dialog.DetectorDialog(self, -1, base=self.parent,
                                                reset_zmin_ctl=self.default_zmin_ctl,
                                                reset_zmax_ctl=self.default_zmax_ctl, cmap=self.cmap)
        ## info of current detector and data2D
        xnpts = len(self.data2D.x_bins)
        ynpts = len(self.data2D.y_bins)
        xmax = max(self.data2D.xmin, self.data2D.xmax)
        ymax = max(self.data2D.ymin, self.data2D.ymax)
        qmax = math.sqrt(math.pow(xmax, 2) + math.pow(ymax, 2))
        ## set dialog window content
        dialog.setContent(xnpts=xnpts, ynpts=ynpts, qmax=qmax,
                          beam=self.data2D.xmin,
                          zmin=self.zmin_2D,
                          zmax=self.zmax_2D)
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
                   xmin=self.data2D.xmin,
                   xmax=self.data2D.xmax,
                   ymin=self.data2D.ymin,
                   ymax=self.data2D.ymax,
                   zmin=self.zmin_2D,
                   zmax=self.zmax_2D,
                   cmap=self.cmap,
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

    def onMouseMotion(self, event):
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
        msg = "Plotter2D._setSlicer  %s" % self.slicer.__class__.__name__
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
        from sas.dataloader.manipulations import CircularAverage
        ## compute the maximum radius of data2D
        self.qmax = max(math.fabs(self.data2D.xmax),
                        math.fabs(self.data2D.xmin))
        self.ymax = max(math.fabs(self.data2D.ymax),
                        math.fabs(self.data2D.ymin))
        self.radius = math.sqrt(math.pow(self.qmax, 2) + math.pow(self.ymax, 2))
        ##Compute beam width
        bin_width = (self.qmax + self.qmax) / npt
        ## Create data1D circular average of data2D
        Circle = CircularAverage(r_min=0, r_max=self.radius,
                                 bin_width=bin_width)
        circ = Circle(self.data2D, ismask=ismask)
        from sas.guiframe.dataFitting import Data1D
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

        new_plot.group_id = "2daverage" + self.data2D.name
        new_plot.id = "Circ avg " + self.data2D.name
        new_plot.is_data = True
        self.parent.update_theory(data_id=self.data2D.id, \
                                       theory=new_plot)
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
        from sas.guiframe.gui_manager import MDIFrame
        from boxSum import BoxSum
        self.onClearSlicer(event)
        self.slicer_z += 1
        self.slicer = BoxSum(self, self.subplot, zorder=self.slicer_z)
        self.subplot.set_ylim(self.data2D.ymin, self.data2D.ymax)
        self.subplot.set_xlim(self.data2D.xmin, self.data2D.xmax)
        self.update()
        self.slicer.update()
        ## Value used to initially set the slicer panel
        params = self.slicer.get_params()
        ## Create a new panel to display results of summation of Data2D
        from slicerpanel import SlicerPanel
        win = MDIFrame(self.parent, None, 'None', (100, 200))
        new_panel = SlicerPanel(parent=win, id=-1,
                                base=self, type=self.slicer.__class__.__name__,
                                params=params, style=wx.RAISED_BORDER)

        new_panel.window_caption = self.slicer.__class__.__name__ + " " + \
                                    str(self.data2D.name)
        new_panel.window_name = self.slicer.__class__.__name__ + " " + \
                                    str(self.data2D.name)
        ## Store a reference of the new created panel

        ## save the window_caption of the new panel in the current slicer
        self.slicer.set_panel_name(name=new_panel.window_caption)
        ## post slicer panel to guiframe to display it
        from sas.guiframe.events import SlicerPanelEvent

        win.set_panel(new_panel)
        new_panel.frame = win
        wx.PostEvent(self.parent, SlicerPanelEvent(panel=new_panel,
                                                   main_panel=self))
        wx.CallAfter(new_panel.frame.Show)
        self.panel_slicer = new_panel

    def onBoxavgX(self, event):
        """
        Perform 2D data averaging on Qx
        Create a new slicer .

        :param event: wx.menu event
        """
        from boxSlicer import BoxInteractorX
        self.onClearSlicer(event)
        wx.PostEvent(self, InternalEvent(slicer=BoxInteractorX))

    def onBoxavgY(self, event):
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
        event_id = str(evt.GetId())
        if self.parent != None:
            self._default_save_location = self.parent._default_save_location
        default_name = self.plots[self.graph.selected_plottable].label
        if default_name.count('.') > 0:
            default_name = default_name.split('.')[0]
        default_name += "_out"
        if event_id in self.action_ids:
            self.parent.save_data2d(self.data2D, default_name)

    def _onDataShow(self, evt):
        """
        Show the data set in text

        :param evt: Menu event

        """
        menu = evt.GetEventObject()
        event_id = evt.GetId()
        self.set_selected_from_menu(menu, event_id)
        data = self.plots[self.graph.selected_plottable]
        default_name = data.label
        if default_name.count('.') > 0:
            default_name = default_name.split('.')[0]
        #default_name += "_out"
        if self.parent != None:
            self.parent.show_data2d(data, default_name)

    def modifyGraphAppearance(self, e):
        self.graphApp = graphAppearance(self, 'Modify graph appearance', legend=False)
        self.graphApp.setDefaults(self.grid_on, self.legend_on,
                                  self.xaxis_label, self.yaxis_label,
                                  self.xaxis_unit, self.yaxis_unit,
                                  self.xaxis_font, self.yaxis_font,
                                  find_key(self.get_loc_label(), self.legendLoc),
                                  self.xcolor, self.ycolor,
                                  self.is_xtick, self.is_ytick)
        self.graphApp.Bind(wx.EVT_CLOSE, self.on_graphApp_close)

    def on_graphApp_close(self, e):
        """
            Gets values from graph appearance dialog and sends them off
            to modify the plot
        """
        self.onGridOnOff(self.graphApp.get_togglegrid())
        self.xaxis_label = self.graphApp.get_xlab()
        self.yaxis_label = self.graphApp.get_ylab()
        self.xaxis_unit = self.graphApp.get_xunit()
        self.yaxis_unit = self.graphApp.get_yunit()
        self.xaxis_font = self.graphApp.get_xfont()
        self.yaxis_font = self.graphApp.get_yfont()
        self.is_xtick = self.graphApp.get_xtick_check()
        self.is_ytick = self.graphApp.get_ytick_check()
        if self.is_xtick:
            self.xaxis_tick = self.xaxis_font
        if self.is_ytick:
            self.yaxis_tick = self.yaxis_font

        self.xaxis(self.xaxis_label, self.xaxis_unit,
                   self.graphApp.get_xfont(), self.graphApp.get_xcolor(),
                   self.xaxis_tick)
        self.yaxis(self.yaxis_label, self.yaxis_unit,
                   self.graphApp.get_yfont(), self.graphApp.get_ycolor(),
                   self.yaxis_tick)

        self.graphApp.Destroy()
