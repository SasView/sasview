"""
    Plot panel.
"""


import logging
import traceback
import wx
# Try a normal import first
# If it fails, try specifying a version
import matplotlib
matplotlib.interactive(False)
#Use the WxAgg back end. The Wx one takes too long to render
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import os
from . import transform
#TODO: make the plottables interactive
from .binder import BindArtist
from matplotlib.font_manager import FontProperties
DEBUG = False

from .plottables import Graph
from .TextDialog import TextDialog
from .LabelDialog import LabelDialog
import operator

import math
import pylab
DEFAULT_CMAP = pylab.cm.jet
import copy
import numpy as np

from sas.sasgui.guiframe.events import StatusEvent
from .toolbar import NavigationToolBar, PlotPrintout, bind

logger = logging.getLogger(__name__)

def show_tree(obj, d=0):
    """Handy function for displaying a tree of graph objects"""
    print("%s%s" % ("-"*d, obj.__class__.__name__))
    if 'get_children' in dir(obj):
        for a in obj.get_children(): show_tree(a, d + 1)

from .convert_units import convert_unit


def _rescale(lo, hi, step, pt=None, bal=None, scale='linear'):
    """
        Rescale (lo,hi) by step, returning the new (lo,hi)
        The scaling is centered on pt, with positive values of step
        driving lo/hi away from pt and negative values pulling them in.
        If bal is given instead of point, it is already in [0,1] coordinates.

        This is a helper function for step-based zooming.

    """
    # Convert values into the correct scale for a linear transformation
    # TODO: use proper scale transformers
    loprev = lo
    hiprev = hi
    if scale == 'log':
        assert lo > 0
        if lo > 0:
            lo = math.log10(lo)
        if hi > 0:
            hi = math.log10(hi)
        if pt is not None:
            pt = math.log10(pt)

    # Compute delta from axis range * %, or 1-% if persent is negative
    if step > 0:
        delta = float(hi - lo) * step / 100
    else:
        delta = float(hi - lo) * step / (100 - step)

    # Add scale factor proportionally to the lo and hi values,
    # preserving the
    # point under the mouse
    if bal is None:
        bal = float(pt - lo) / (hi - lo)
    lo = lo - (bal * delta)
    hi = hi + (1 - bal) * delta

    # Convert transformed values back to the original scale
    if scale == 'log':
        if (lo <= -250) or (hi >= 250):
            lo = loprev
            hi = hiprev
        else:
            lo, hi = math.pow(10., lo), math.pow(10., hi)
    return (lo, hi)


class PlotPanel(wx.Panel):
    """
    The PlotPanel has a Figure and a Canvas. OnSize events simply set a
    flag, and the actually redrawing of the
    figure is triggered by an Idle event.
    """
    def __init__(self, parent, id=-1, xtransform=None,
                 ytransform=None, scale='log_{10}',
                 color=None, dpi=None, **kwargs):
        """
        """
        wx.Panel.__init__(self, parent, id=id, **kwargs)
        self.parent = parent
        if hasattr(parent, "parent"):
            self.parent = self.parent.parent
        self.dimension = 1
        self.gotLegend = 0  # to begin, legend is not picked.
        self.legend_pos_loc = None
        self.legend = None
        self.line_collections_list = []
        self.figure = Figure(None, dpi, linewidth=2.0)
        self.color = '#b3b3b3'
        from .canvas import FigureCanvas
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.SetColor(color)
        self._resizeflag = True
        self._SetSize()
        self.subplot = self.figure.add_subplot(111)
        self.figure.subplots_adjust(left=0.2, bottom=.2)
        self.yscale = 'linear'
        self.xscale = 'linear'
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        #add toolbar
        self.enable_toolbar = True
        self.toolbar = None
        self.add_toolbar()
        self.SetSizer(self.sizer)

        # Graph object to manage the plottables
        self.graph = Graph()

        #Boolean value to keep track of whether current legend is
        #visible or not
        self.legend_on = True
        self.grid_on = False
        #Location of legend, default is 0 or 'best'
        self.legendLoc = 0
        self.position = None
        self._loc_labels = self.get_loc_label()

        self.Bind(wx.EVT_CONTEXT_MENU, self.onContextMenu)

        # Define some constants
        self.colorlist = ['b', 'g', 'r', 'c', 'm', 'y', 'k']
        self.symbollist = ['o', 'x', '^', 'v', '<', '>', '+',
                           's', 'd', 'D', 'h', 'H', 'p', '-']

        #List of texts currently on the plot
        self.textList = []
        self.selectedText = None
        #User scale
        if xtransform is not None:
            self.xLabel = xtransform
        else:
            self.xLabel = "log10(x)"
        if ytransform is not None:
            self.yLabel = ytransform
        else:
            self.yLabel = "log10(y)"
        self.viewModel = "--"
        # keep track if the previous transformation of x
        # and y in Property dialog
        self.prevXtrans = "log10(x)"
        self.prevYtrans = "log10(y)"
        self.scroll_id = self.canvas.mpl_connect('scroll_event', self.onWheel)
        #taking care of dragging
        self.motion_id = self.canvas.mpl_connect('motion_notify_event',
                                                 self.onMouseMotion)
        self.press_id = self.canvas.mpl_connect('button_press_event',
                                                self.onLeftDown)
        self.pick_id = self.canvas.mpl_connect('pick_event', self.onPick)
        self.release_id = self.canvas.mpl_connect('button_release_event',
                                                  self.onLeftUp)

        wx.EVT_RIGHT_DOWN(self, self.onLeftDown)
        # to turn axis off whenn resizing the panel
        self.resizing = False

        self.leftdown = False
        self.leftup = False
        self.mousemotion = False
        self.axes = [self.subplot]
        ## Fit dialog
        self._fit_dialog = None
        # Interactor
        self.connect = BindArtist(self.subplot.figure)
        #self.selected_plottable = None

        # new data for the fit
        from sas.sasgui.guiframe.dataFitting import Data1D
        self.fit_result = Data1D(x=[], y=[], dy=None)
        self.fit_result.symbol = 13
        #self.fit_result = Data1D(x=[], y=[],dx=None, dy=None)
        self.fit_result.name = "Fit"
        # For fit Dialog initial display
        self.xmin = 0.0
        self.xmax = 0.0
        self.xminView = 0.0
        self.xmaxView = 0.0
        self._scale_xlo = None
        self._scale_xhi = None
        self._scale_ylo = None
        self._scale_yhi = None
        self.Avalue = None
        self.Bvalue = None
        self.ErrAvalue = None
        self.ErrBvalue = None
        self.Chivalue = None

        # for 2D scale
        if scale != 'linear':
            scale = 'log_{10}'
        self.scale = scale
        self.data = None
        self.qx_data = None
        self.qy_data = None
        self.xmin_2D = None
        self.xmax_2D = None
        self.ymin_2D = None
        self.ymax_2D = None
        ## store reference to the current plotted vmin and vmax of plotted image
        ##z range in linear scale
        self.zmin_2D = None
        self.zmax_2D = None

        #index array
        self.index_x = None
        self.index_y = None

        #number of bins
        self.x_bins = None
        self.y_bins = None

        ## default color map
        self.cmap = DEFAULT_CMAP

        # Dragging info
        self.begDrag = False
        self.xInit = None
        self.yInit = None
        self.xFinal = None
        self.yFinal = None

        #axes properties
        self.xaxis_font = None
        self.xaxis_label = None
        self.xaxis_unit = None
        self.xaxis_color = 'black'
        self.xaxis_tick = None
        self.yaxis_font = None
        self.yaxis_label = None
        self.yaxis_unit = None
        self.yaxis_color = 'black'
        self.yaxis_tick = None

        # check if zoomed.
        self.is_zoomed = False
        # Plottables
        self.plots = {}

        # Default locations
        self._default_save_location = os.getcwd()
        # let canvas know about axes
        self.canvas.set_panel(self)
        self.ly = None
        self.q_ctrl = None
        #Bind focus to change the border color
        self.canvas.Bind(wx.EVT_SET_FOCUS, self.on_set_focus)
        self.canvas.Bind(wx.EVT_KILL_FOCUS, self.on_kill_focus)

    def _SetInitialSize(self,):
        """
        """
        pixels = self.parent.GetClientSize()
        self.canvas.SetSize(pixels)
        self.figure.set_size_inches(pixels[0] / self.figure.get_dpi(),
                                    pixels[1] / self.figure.get_dpi(), forward=True)

    def On_Paint(self, event):
        """
        """
        self.canvas.SetBackgroundColour(self.color)

    def on_set_focus(self, event):
        """
        Send to the parenet the current panel on focus
        """
        # light blue
        self.color = '#0099f7'
        self.figure.set_edgecolor(self.color)
        if self.parent and self.window_caption:
            self.parent.send_focus_to_datapanel(self.window_caption)
        self.draw()

    def on_kill_focus(self, event):
        """
        Reset the panel color
        """
        # light grey
        self.color = '#b3b3b3'
        self.figure.set_edgecolor(self.color)
        self.draw()

    def set_resizing(self, resizing=False):
        """
        Set the resizing (True/False)
        """
        pass  # Not implemented

    def schedule_full_draw(self, func='append'):
        """
        Put self in schedule to full redraw list
        """
        pass  # Not implemented

    def add_toolbar(self):
        """
        add toolbar
        """
        self.enable_toolbar = True
        self.toolbar = NavigationToolBar(parent=self, canvas=self.canvas)
        bind(self.toolbar, wx.EVT_TOOL, self.onResetGraph, id=self.toolbar._NTB2_RESET)
        bind(self.toolbar, wx.EVT_TOOL, self.onContextMenu, id=self.toolbar._NTB2_HOME)
        self.toolbar.Realize()
        ## The 'SetToolBar()' is not working on MAC: JHC
        #if IS_MAC:
        # Mac platform (OSX 10.3, MacPython) does not seem to cope with
        # having a toolbar in a sizer. This work-around gets the buttons
        # back, but at the expense of having the toolbar at the top
        #self.SetToolBar(self.toolbar)
        #else:
        # On Windows platform, default window size is incorrect, so set
        # toolbar width to figure width.
        tw, th = self.toolbar.GetSizeTuple()
        fw, fh = self.canvas.GetSizeTuple()
        # By adding toolbar in sizer, we are able to put it at the bottom
        # of the frame - so appearance is closer to GTK version.
        # As noted above, doesn't work for Mac.
        self.toolbar.SetSize(wx.Size(fw, th))
        self.sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)

        # update the axes menu on the toolbar
        self.toolbar.update()

    def onLeftDown(self, event):
        """
        left button down and ready to drag
        """
        # Check that the LEFT button was pressed
        if event.button == 1:
            self.leftdown = True
            ax = event.inaxes
            for text in self.textList:
                if text.contains(event)[0]: # If user has clicked on text
                    self.selectedText = text
                    return

            if ax is not None:
                self.xInit, self.yInit = event.xdata, event.ydata
                try:
                    pos_x = float(event.xdata)  # / size_x
                    pos_y = float(event.ydata)  # / size_y
                    pos_x = "%8.3g" % pos_x
                    pos_y = "%8.3g" % pos_y
                    self.position = str(pos_x), str(pos_y)
                    wx.PostEvent(self.parent, StatusEvent(status=self.position))
                except:
                    self.position = None

    def onLeftUp(self, event):
        """
        Dragging is done
        """
        # Check that the LEFT button was released
        if event.button == 1:
            self.leftdown = False
            self.mousemotion = False
            self.leftup = True
            self.selectedText = None

        #release the legend
        if self.gotLegend == 1:
            self.gotLegend = 0
            self.set_legend_alpha(1)

    def set_legend_alpha(self, alpha=1):
        """
        Set legend alpha
        """
        if self.legend is not None:
            self.legend.legendPatch.set_alpha(alpha)

    def onPick(self, event):
        """
        On pick legend
        """
        legend = self.legend
        if event.artist == legend:
            #gets the box of the legend.
            bbox = self.legend.get_window_extent()
            #get mouse coordinates at time of pick.
            self.mouse_x = event.mouseevent.x
            self.mouse_y = event.mouseevent.y
            #get legend coordinates at time of pick.
            self.legend_x = bbox.xmin
            self.legend_y = bbox.ymin
            #indicates we picked up the legend.
            self.gotLegend = 1
            self.set_legend_alpha(0.5)

    def _on_legend_motion(self, event):
        """
        On legend in motion
        """
        ax = event.inaxes
        if ax is None:
            return
        # Event occurred inside a plotting area
        lo_x, hi_x = ax.get_xlim()
        lo_y, hi_y = ax.get_ylim()
        # How much the mouse moved.
        x = mouse_diff_x = self.mouse_x - event.x
        y = mouse_diff_y = self.mouse_y - event.y
        # Put back inside
        if x < lo_x:
            x = lo_x
        if x > hi_x:
            x = hi_x
        if y < lo_y:
            y = lo_y
        if y > hi_y:
            y = hi_y
        # Move the legend from its previous location by that same amount
        loc_in_canvas = self.legend_x - mouse_diff_x, \
                        self.legend_y - mouse_diff_y
        # Transform into legend coordinate system
        trans_axes = self.legend.parent.transAxes.inverted()
        loc_in_norm_axes = trans_axes.transform_point(loc_in_canvas)
        self.legend_pos_loc = tuple(loc_in_norm_axes)
        self.legend._loc = self.legend_pos_loc
        self.resizing = True
        self.canvas.set_resizing(self.resizing)
        self.canvas.draw()

    def onMouseMotion(self, event):
        """
        check if the left button is press and the mouse in moving.
        computer delta for x and y coordinates and then calls draghelper
        to perform the drag
        """
        self.cusor_line(event)
        if self.gotLegend == 1 and self.leftdown:
            self._on_legend_motion(event)
            return

        if self.leftdown and self.selectedText is not None:
            # User has clicked on text and is dragging
            ax = event.inaxes
            if ax is not None:
                # Only move text if mouse is within axes
                self.selectedText.set_position((event.xdata, event.ydata))
                self._dragHelper(0, 0)
            else:
                # User has dragged outside of axes
                self.selectedText = None
            return

        if self.enable_toolbar:
            #Disable dragging without the toolbar to allow zooming with toolbar
            return
        self.mousemotion = True
        if self.leftdown == True and self.mousemotion == True:
            ax = event.inaxes
            if ax is not None:  # the dragging is perform inside the figure
                self.xFinal, self.yFinal = event.xdata, event.ydata
                # Check whether this is the first point
                if self.xInit is None:
                    self.xInit = self.xFinal
                    self.yInit = self.yFinal

                xdelta = self.xFinal - self.xInit
                ydelta = self.yFinal - self.yInit

                if self.xscale == 'log':
                    xdelta = math.log10(self.xFinal) - math.log10(self.xInit)
                if self.yscale == 'log':
                    ydelta = math.log10(self.yFinal) - math.log10(self.yInit)
                self._dragHelper(xdelta, ydelta)
            else:  # no dragging is perform elsewhere
                self._dragHelper(0, 0)

    def cusor_line(self, event):
        """
        """
        pass

    def _offset_graph(self):
        """
        Zoom and offset the graph to the last known settings
        """
        for ax in self.axes:
            if self._scale_xhi is not None and self._scale_xlo is not None:
                ax.set_xlim(self._scale_xlo, self._scale_xhi)
            if self._scale_yhi is not None and self._scale_ylo is not None:
                ax.set_ylim(self._scale_ylo, self._scale_yhi)

    def _dragHelper(self, xdelta, ydelta):
        """
        dragging occurs here
        """
        # Event occurred inside a plotting area
        for ax in self.axes:
            lo, hi = ax.get_xlim()
            newlo, newhi = lo - xdelta, hi - xdelta
            if self.xscale == 'log':
                if lo > 0:
                    newlo = math.log10(lo) - xdelta
                if hi > 0:
                    newhi = math.log10(hi) - xdelta
            if self.xscale == 'log':
                self._scale_xlo = math.pow(10, newlo)
                self._scale_xhi = math.pow(10, newhi)
                ax.set_xlim(math.pow(10, newlo), math.pow(10, newhi))
            else:
                self._scale_xlo = newlo
                self._scale_xhi = newhi
                ax.set_xlim(newlo, newhi)

            lo, hi = ax.get_ylim()
            newlo, newhi = lo - ydelta, hi - ydelta
            if self.yscale == 'log':
                if lo > 0:
                    newlo = math.log10(lo) - ydelta
                if hi > 0:
                    newhi = math.log10(hi) - ydelta
            if  self.yscale == 'log':
                self._scale_ylo = math.pow(10, newlo)
                self._scale_yhi = math.pow(10, newhi)
                ax.set_ylim(math.pow(10, newlo), math.pow(10, newhi))
            else:
                self._scale_ylo = newlo
                self._scale_yhi = newhi
                ax.set_ylim(newlo, newhi)
        self.canvas.draw_idle()

    def resetFitView(self):
        """
        For fit Dialog initial display
        """
        self.xmin = 0.0
        self.xmax = 0.0
        self.xminView = 0.0
        self.xmaxView = 0.0
        self._scale_xlo = None
        self._scale_xhi = None
        self._scale_ylo = None
        self._scale_yhi = None
        self.Avalue = None
        self.Bvalue = None
        self.ErrAvalue = None
        self.ErrBvalue = None
        self.Chivalue = None

    def onWheel(self, event):
        """
        Process mouse wheel as zoom events

        :param event: Wheel event

        """
        ax = event.inaxes
        step = event.step

        if ax is not None:
            # Event occurred inside a plotting area
            lo, hi = ax.get_xlim()
            lo, hi = _rescale(lo, hi, step,
                              pt=event.xdata, scale=ax.get_xscale())
            if not self.xscale == 'log' or lo > 0:
                self._scale_xlo = lo
                self._scale_xhi = hi
                ax.set_xlim((lo, hi))

            lo, hi = ax.get_ylim()
            lo, hi = _rescale(lo, hi, step, pt=event.ydata,
                              scale=ax.get_yscale())
            if not self.yscale == 'log' or lo > 0:
                self._scale_ylo = lo
                self._scale_yhi = hi
                ax.set_ylim((lo, hi))
        else:
            # Check if zoom happens in the axes
            xdata, ydata = None, None
            x, y = event.x, event.y

            for ax in self.axes:
                insidex, _ = ax.xaxis.contains(event)
                if insidex:
                    xdata, _ = ax.transAxes.inverted().transform_point((x, y))
                insidey, _ = ax.yaxis.contains(event)
                if insidey:
                    _, ydata = ax.transAxes.inverted().transform_point((x, y))
            if xdata is not None:
                lo, hi = ax.get_xlim()
                lo, hi = _rescale(lo, hi, step,
                                  bal=xdata, scale=ax.get_xscale())
                if not self.xscale == 'log' or lo > 0:
                    self._scale_xlo = lo
                    self._scale_xhi = hi
                    ax.set_xlim((lo, hi))
            if ydata is not None:
                lo, hi = ax.get_ylim()
                lo, hi = _rescale(lo, hi, step, bal=ydata,
                                  scale=ax.get_yscale())
                if not self.yscale == 'log' or lo > 0:
                    self._scale_ylo = lo
                    self._scale_yhi = hi
                    ax.set_ylim((lo, hi))
        self.canvas.draw_idle()

    def returnTrans(self):
        """
        Return values and labels used by Fit Dialog
        """
        return self.xLabel, self.yLabel, self.Avalue, self.Bvalue, \
                self.ErrAvalue, self.ErrBvalue, self.Chivalue

    def setTrans(self, xtrans, ytrans):
        """

        :param xtrans: set x transformation on Property dialog
        :param ytrans: set y transformation on Property dialog

        """
        self.prevXtrans = xtrans
        self.prevYtrans = ytrans

    def onFitting(self, event):
        """
        when clicking on linear Fit on context menu , display Fitting Dialog
        """
        plot_dict = {}
        menu = event.GetEventObject()
        event_id = event.GetId()
        self.set_selected_from_menu(menu, event_id)
        plotlist = self.graph.returnPlottable()
        if self.graph.selected_plottable is not None:
            for item in plotlist:
                if item.id == self.graph.selected_plottable:
                    plot_dict[item] = plotlist[item]
        else:
            plot_dict = plotlist
        from .fitDialog import LinearFit

        if len(list(plot_dict.keys())) > 0:
            first_item = list(plot_dict.keys())[0]
            dlg = LinearFit(parent=None, plottable=first_item,
                            push_data=self.onFitDisplay,
                            transform=self.returnTrans,
                            title='Linear Fit')

            if (self.xmin != 0.0)and (self.xmax != 0.0)\
                and(self.xminView != 0.0)and (self.xmaxView != 0.0):
                dlg.setFitRange(self.xminView, self.xmaxView,
                                self.xmin, self.xmax)
            else:
                xlim = self.subplot.get_xlim()
                ylim = self.subplot.get_ylim()
                dlg.setFitRange(xlim[0], xlim[1], ylim[0], ylim[1])
            # It would be nice for this to NOT be modal (i.e. Show).
            # Not sure about other ramifications - for example
            # if a second linear fit is started before the first is closed.
            # consider for future - being able to work on the plot while
            # seing the fit values would be very nice  -- PDB 7/10/16
            dlg.ShowModal()

    def set_selected_from_menu(self, menu, id):
        """
        Set selected_plottable from context menu selection

        :param menu: context menu item
        :param id: menu item id
        """
        if len(self.plots) < 1:
            return
        name = menu.GetHelpString(id)
        for plot in list(self.plots.values()):
            if plot.name == name:
                self.graph.selected_plottable = plot.id
                break

    def linear_plottable_fit(self, plot):
        """
            when clicking on linear Fit on context menu, display Fitting Dialog

            :param plot: PlotPanel owning the graph

        """
        from .fitDialog import LinearFit
        if self._fit_dialog is not None:
            return
        self._fit_dialog = LinearFit(None, plot, self.onFitDisplay,
                                     self.returnTrans, -1, 'Linear Fit')
        # Set the zoom area
        if self._scale_xhi is not None and self._scale_xlo is not None:
            self._fit_dialog.set_fit_region(self._scale_xlo, self._scale_xhi)
        # Register the close event
        self._fit_dialog.register_close(self._linear_fit_close)
        # Show a non-model dialog
        self._fit_dialog.Show()

    def _linear_fit_close(self):
        """
        A fit dialog was closed
        """
        self._fit_dialog = None

    def _onProperties(self, event):
        """
        when clicking on Properties on context menu ,
        The Property dialog is displayed
        The user selects a transformation for x or y value and
        a new plot is displayed
        """
        if self._fit_dialog is not None:
            self._fit_dialog.Destroy()
            self._fit_dialog = None
        plot_list = self.graph.returnPlottable()
        if len(list(plot_list.keys())) > 0:
            first_item = list(plot_list.keys())[0]
            if first_item.x != []:
                from .PropertyDialog import Properties
                dial = Properties(self, -1, 'Properties')
                dial.setValues(self.prevXtrans, self.prevYtrans, self.viewModel)
                if dial.ShowModal() == wx.ID_OK:
                    self.xLabel, self.yLabel, self.viewModel = dial.getValues()
                    self._onEVT_FUNC_PROPERTY()
                dial.Destroy()

    def set_yscale(self, scale='linear'):
        """
        Set the scale on Y-axis

        :param scale: the scale of y-axis

        """
        self.subplot.set_yscale(scale, nonposy='clip')
        self.yscale = scale

    def get_yscale(self):
        """

        :return: Y-axis scale

        """
        return self.yscale

    def set_xscale(self, scale='linear'):
        """
        Set the scale on x-axis

        :param scale: the scale of x-axis

        """
        self.subplot.set_xscale(scale)
        self.xscale = scale

    def get_xscale(self):
        """

        :return: x-axis scale

        """
        return self.xscale

    def SetColor(self, rgbtuple):
        """
        Set figure and canvas colours to be the same

        """
        if not rgbtuple:
            rgbtuple = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE).Get()
        col = [c / 255.0 for c in rgbtuple]
        self.figure.set_facecolor(col)
        self.figure.set_edgecolor(self.color)
        self.canvas.SetBackgroundColour(wx.Colour(*rgbtuple))

    def _onSize(self, event):
        """
        """
        self._resizeflag = True

    def _onIdle(self, evt):
        """
        """
        if self._resizeflag:
            self._resizeflag = False
            self._SetSize()
            self.draw()

    def _SetSize(self, pixels=None):
        """
        This method can be called to force the Plot to be a desired size,
         which defaults to the ClientSize of the panel

        """
        if not pixels:
            pixels = tuple(self.GetClientSize())
        self.canvas.SetSize(pixels)
        self.figure.set_size_inches(float(pixels[0]) / self.figure.get_dpi(),
                                    float(pixels[1]) / self.figure.get_dpi())

    def draw(self):
        """
        Where the actual drawing happens

        """
        self.figure.canvas.draw_idle()

    def legend_picker(self, legend, event):
        """
            Pick up the legend patch
        """
        return self.legend.legendPatch.contains(event)

    def get_loc_label(self):
        """
        Associates label to a specific legend location
        """
        _labels = {}
        i = 0
        _labels['best'] = i
        i += 1
        _labels['upper right'] = i
        i += 1
        _labels['upper left'] = i
        i += 1
        _labels['lower left'] = i
        i += 1
        _labels['lower right'] = i
        i += 1
        _labels['right'] = i
        i += 1
        _labels['center left'] = i
        i += 1
        _labels['center right'] = i
        i += 1
        _labels['lower center'] = i
        i += 1
        _labels['upper center'] = i
        i += 1
        _labels['center'] = i
        return _labels

    def onSaveImage(self, evt):
        """
        Implement save image
        """
        self.toolbar.save_figure(evt)

    def onContextMenu(self, event):
        """
        Default context menu for a plot panel

        """
        # Slicer plot popup menu
        wx_id = wx.NewId()
        slicerpop = wx.Menu()
        slicerpop.Append(wx_id, '&Save image', 'Save image as PNG')
        wx.EVT_MENU(self, wx_id, self.onSaveImage)

        wx_id = wx.NewId()
        slicerpop.Append(wx_id, '&Printer setup', 'Set image size')
        wx.EVT_MENU(self, wx_id, self.onPrinterSetup)

        wx_id = wx.NewId()
        slicerpop.Append(wx_id, '&Print image', 'Print image ')
        wx.EVT_MENU(self, wx_id, self.onPrint)

        wx_id = wx.NewId()
        slicerpop.Append(wx_id, '&Copy', 'Copy to the clipboard')
        wx.EVT_MENU(self, wx_id, self.OnCopyFigureMenu)

        wx_id = wx.NewId()
        slicerpop.AppendSeparator()
        slicerpop.Append(wx_id, '&Properties')
        wx.EVT_MENU(self, wx_id, self._onProperties)

        wx_id = wx.NewId()
        slicerpop.AppendSeparator()
        slicerpop.Append(wx_id, '&Linear Fit')
        wx.EVT_MENU(self, wx_id, self.onFitting)

        wx_id = wx.NewId()
        slicerpop.AppendSeparator()
        slicerpop.Append(wx_id, '&Toggle Legend On/Off', 'Toggle Legend On/Off')
        wx.EVT_MENU(self, wx_id, self.onLegend)

        loc_menu = wx.Menu()
        for label in self._loc_labels:
            wx_id = wx.NewId()
            loc_menu.Append(wx_id, str(label), str(label))
            wx.EVT_MENU(self, wx_id, self.onChangeLegendLoc)
        wx_id = wx.NewId()
        slicerpop.AppendMenu(wx_id, '&Modify Legend Location', loc_menu)

        wx_id = wx.NewId()
        slicerpop.Append(wx_id, '&Modify Y Axis Label')
        wx.EVT_MENU(self, wx_id, self._on_yaxis_label)
        wx_id = wx.NewId()
        slicerpop.Append(wx_id, '&Modify X Axis Label')
        wx.EVT_MENU(self, wx_id, self._on_xaxis_label)

        try:
            # mouse event
            pos_evt = event.GetPosition()
            pos = self.ScreenToClient(pos_evt)
        except:
            # toolbar event
            pos_x, pos_y = self.toolbar.GetPositionTuple()
            pos = (pos_x, pos_y + 5)

        self.PopupMenu(slicerpop, pos)

    def onToolContextMenu(self, event):
        """
        ContextMenu from toolbar

        :param event: toolbar event
        """
        # reset postion
        self.position = None
        if self.graph.selected_plottable is not None:
            self.graph.selected_plottable = None

        self.onContextMenu(event)

# modified kieranrcampbell ILL june2012
    def onLegend(self, legOnOff):
        """
        Toggles whether legend is visible/not visible
        """
        self.legend_on = legOnOff
        if not self.legend_on:
            for ax in self.axes:
                self.remove_legend(ax)
        else:
            # sort them by labels
            handles, labels = self.subplot.get_legend_handles_labels()
            hl = sorted(zip(handles, labels),
                        key=operator.itemgetter(1))
            handles2, labels2 = list(zip(*hl))
            self.line_collections_list = handles2
            self.legend = self.subplot.legend(handles2, labels2,
                                              prop=FontProperties(size=10),
                                              loc=self.legendLoc)
            if self.legend is not None:
                self.legend.set_picker(self.legend_picker)
                self.legend.set_axes(self.subplot)
                self.legend.set_zorder(20)

        self.subplot.figure.canvas.draw_idle()

    def onChangeLegendLoc(self, event):
        """
        Changes legend loc based on user input
        """
        menu = event.GetEventObject()
        label = menu.GetLabel(event.GetId())
        self.ChangeLegendLoc(label)

    def ChangeLegendLoc(self, label):
        """
        Changes legend loc based on user input
        """
        self.legendLoc = label
        self.legend_pos_loc = None
        # sort them by labels
        handles, labels = self.subplot.get_legend_handles_labels()
        hl = sorted(zip(handles, labels),
                    key=operator.itemgetter(1))
        handles2, labels2 = list(zip(*hl))
        self.line_collections_list = handles2
        self.legend = self.subplot.legend(handles2, labels2,
                                          prop=FontProperties(size=10),
                                          loc=self.legendLoc)
        if self.legend is not None:
            self.legend.set_picker(self.legend_picker)
            self.legend.set_axes(self.subplot)
            self.legend.set_zorder(20)
        self.subplot.figure.canvas.draw_idle()

    def remove_legend(self, ax=None):
        """
        Remove legend for ax or the current axes.
        """
        from pylab import gca
        if ax is None:
            ax = gca()
        ax.legend_ = None

    def _on_addtext(self, event):
        """
        Allows you to add text to the plot
        """
        pos_x = 0
        pos_y = 0
        if self.position is not None:
            pos_x, pos_y = self.position
        else:
            pos_x, pos_y = 0.01, 1.00

        textdial = TextDialog(None, -1, 'Add Custom Text')
        if textdial.ShowModal() == wx.ID_OK:
            try:
                FONT = FontProperties()
                label = textdial.getText()
                xpos = pos_x
                ypos = pos_y
                font = FONT.copy()
                font.set_size(textdial.getSize())
                font.set_family(textdial.getFamily())
                font.set_style(textdial.getStyle())
                font.set_weight(textdial.getWeight())
                colour = textdial.getColor()
                if len(label) > 0 and xpos > 0 and ypos > 0:
                    new_text = self.subplot.text(str(xpos), str(ypos), label,
                                                 fontproperties=font,
                                                 color=colour)
                    self.textList.append(new_text)
                    self.subplot.figure.canvas.draw_idle()
            except:
                if self.parent is not None:
                    msg = "Add Text: Error. Check your property values..."
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
                else:
                    raise
        textdial.Destroy()
        #Have a pop up box come up for user to type in the
        #text that they want to add...then create text Plottable
        #based on this and plot it at user designated coordinates

    def onGridOnOff(self, gridon_off):
        """
        Allows ON/OFF Grid
        """
        self.grid_on = gridon_off

        self.subplot.figure.canvas.draw_idle()

    def _on_xaxis_label(self, event):
        """
        Allows you to add text to the plot
        """
        xaxis_label, xaxis_unit, xaxis_font, xaxis_color, \
                     is_ok, is_tick = self._on_axis_label(axis='x')
        if not is_ok:
            return

        self.xaxis_label = xaxis_label
        self.xaxis_unit = xaxis_unit
        self.xaxis_font = xaxis_font
        self.xaxis_color = xaxis_color
        if is_tick:
            self.xaxis_tick = xaxis_font

        if self.data is not None:
            # 2D
            self.xaxis(self.xaxis_label, self.xaxis_unit, \
                        self.xaxis_font, self.xaxis_color, self.xaxis_tick)
            self.subplot.figure.canvas.draw_idle()
        else:
            # 1D
            self._check_zoom_plot()

    def _check_zoom_plot(self):
        """
        Check the zoom range and plot (1D only)
        """
        xlo, xhi = self.subplot.get_xlim()
        ylo, yhi = self.subplot.get_ylim()
        ## Set the view scale for all plots
        self._onEVT_FUNC_PROPERTY(False)
        if self.is_zoomed:
            # Recover the x,y limits
            self.subplot.set_xlim((xlo, xhi))
            self.subplot.set_ylim((ylo, yhi))

    @property
    def is_zoomed(self):
        toolbar_zoomed = self.toolbar.GetToolEnabled(self.toolbar.wx_ids['Back'])
        return self._is_zoomed or toolbar_zoomed

    @is_zoomed.setter
    def is_zoomed(self, value):
        self._is_zoomed = value

    def _on_yaxis_label(self, event):
        """
        Allows you to add text to the plot
        """
        yaxis_label, yaxis_unit, yaxis_font, yaxis_color, \
                        is_ok, is_tick = self._on_axis_label(axis='y')
        if not is_ok:
            return

        self.yaxis_label = yaxis_label
        self.yaxis_unit = yaxis_unit
        self.yaxis_font = yaxis_font
        self.yaxis_color = yaxis_color
        if is_tick:
            self.yaxis_tick = yaxis_font

        if self.data is not None:
            # 2D
            self.yaxis(self.yaxis_label, self.yaxis_unit, \
                        self.yaxis_font, self.yaxis_color, self.yaxis_tick)
            self.subplot.figure.canvas.draw_idle()
        else:
            # 1D
            self._check_zoom_plot()

    def _on_axis_label(self, axis='x'):
        """
        Modify axes labels

        :param axis: x or y axis [string]
        """
        is_ok = True
        title = 'Modify %s axis label' % axis
        font = 'serif'
        colour = 'black'
        if axis == 'x':
            label = self.xaxis_label
            unit = self.xaxis_unit
        else:
            label = self.yaxis_label
            unit = self.yaxis_unit
        textdial = TextDialog(None, -1, title, label, unit)
        if textdial.ShowModal() == wx.ID_OK:
            try:
                FONT = FontProperties()
                font = FONT.copy()
                font.set_size(textdial.getSize())
                font.set_family(textdial.getFamily())
                font.set_style(textdial.getStyle())
                font.set_weight(textdial.getWeight())
                unit = textdial.getUnit()
                colour = textdial.getColor()
                is_tick = textdial.getTickLabel()
                label_temp = textdial.getText()
                if label_temp.count("\%s" % "\\") > 0:
                    if self.parent is not None:
                        msg = "Add Label: Error. Can not use double '\\' "
                        msg += "characters..."
                        wx.PostEvent(self.parent, StatusEvent(status=msg))
                else:
                    label = label_temp
            except:
                if self.parent is not None:
                    msg = "Add Label: Error. Check your property values..."
                    wx.PostEvent(self.parent, StatusEvent(status=msg))
                else:
                    pass
        else:
            is_ok = False
            is_tick = True
        textdial.Destroy()
        return label, unit, font, colour, is_ok, is_tick

    def _on_removetext(self, event):
        """
        Removes all text from the plot.
        Eventually, add option to remove specific text boxes
        """
        num_text = len(self.textList)
        if num_text < 1:
            if self.parent is not None:
                msg = "Remove Text: Nothing to remove.  "
                wx.PostEvent(self.parent, StatusEvent(status=msg))
            else:
                raise
            return
        txt = self.textList[num_text - 1]
        try:
            text_remove = txt.get_text()
            txt.remove()
            if self.parent is not None:
                msg = "Removed Text: '%s'. " % text_remove
                wx.PostEvent(self.parent, StatusEvent(status=msg))
        except:
            if self.parent is not None:
                msg = "Remove Text: Error occurred. "
                wx.PostEvent(self.parent, StatusEvent(status=msg))
            else:
                raise
        self.textList.remove(txt)

        self.subplot.figure.canvas.draw_idle()

    def properties(self, prop):
        """
        Set some properties of the graph.
        The set of properties is not yet determined.

        """
        # The particulars of how they are stored and manipulated (e.g., do
        # we want an inventory internally) is not settled.  I've used a
        # property dictionary for now.
        #
        # How these properties interact with a user defined style file is
        # even less clear.

        # Properties defined by plot

        # Ricardo:
        # A empty label "$$" will prevent the panel from displaying!
        if prop["xlabel"]:
            self.subplot.set_xlabel(r"$%s$"%prop["xlabel"])
        if prop["ylabel"]:
            self.subplot.set_ylabel(r"$%s$"%prop["ylabel"])
        self.subplot.set_title(prop["title"])


    def clear(self):
        """Reset the plot"""
        # TODO: Redraw is brutal.  Render to a backing store and swap in
        # TODO: rather than redrawing on the fly.
        self.subplot.clear()
        self.subplot.hold(True)

    def render(self):
        """Commit the plot after all objects are drawn"""
        # TODO: this is when the backing store should be swapped in.
        if self.legend_on:
            ax = self.subplot
            ax.texts = self.textList
            try:
                handles, labels = ax.get_legend_handles_labels()
                # sort them by labels
                hl = sorted(zip(handles, labels),
                            key=operator.itemgetter(1))
                handles2, labels2 = list(zip(*hl))
                self.line_collections_list = handles2
                self.legend = ax.legend(handles2, labels2,
                                        prop=FontProperties(size=10),
                                        loc=self.legendLoc)
                if self.legend is not None:
                    self.legend.set_picker(self.legend_picker)
                    self.legend.set_axes(self.subplot)
                    self.legend.set_zorder(20)

            except:
                self.legend = ax.legend(prop=FontProperties(size=10),
                                        loc=self.legendLoc)

    def xaxis(self, label, units, font=None, color='black', t_font=None):
        """xaxis label and units.

        Axis labels know about units.

        We need to do this so that we can detect when axes are not
        commesurate.  Currently this is ignored other than for formatting
        purposes.

        """

        self.xcolor = color
        if units.count("{") > 0 and units.count("$") < 2:
            units = '$' + units + '$'
        if label.count("{") > 0 and label.count("$") < 2:
            label = '$' + label + '$'
        if units != "":
            label = label + " (" + units + ")"
        if font:
            self.subplot.set_xlabel(label, fontproperties=font, color=color)
            if t_font is not None:
                for tick in self.subplot.xaxis.get_major_ticks():
                    tick.label.set_fontproperties(t_font)
                for line in self.subplot.xaxis.get_ticklines():
                    size = t_font.get_size()
                    line.set_markersize(size / 3)
        else:
            self.subplot.set_xlabel(label, color=color)
        pass

    def yaxis(self, label, units, font=None, color='black', t_font=None):
        """yaxis label and units."""
        self.ycolor = color
        if units.count("{") > 0 and units.count("$") < 2:
            units = '$' + units + '$'
        if label.count("{") > 0 and label.count("$") < 2:
            label = '$' + label + '$'
        if units != "":
            label = label + " (" + units + ")"
        if font:
            self.subplot.set_ylabel(label, fontproperties=font, color=color)
            if t_font is not None:
                for tick_label in self.subplot.get_yticklabels():
                    tick_label.set_fontproperties(t_font)
                for line in self.subplot.yaxis.get_ticklines():
                    size = t_font.get_size()
                    line.set_markersize(size / 3)
        else:
            self.subplot.set_ylabel(label, color=color)
        pass

    def _connect_to_xlim(self, callback):
        """Bind the xlim change notification to the callback"""
        def process_xlim(axes):
            lo, hi = subplot.get_xlim()
            callback(lo, hi)
        self.subplot.callbacks.connect('xlim_changed', process_xlim)

    def interactive_points(self, x, y, dx=None, dy=None, name='', color=0,
                           symbol=0, markersize=5, zorder=1, id=None,
                           label=None, hide_error=False):
        """Draw markers with error bars"""
        self.subplot.set_yscale('linear')
        self.subplot.set_xscale('linear')
        if id is None:
            id = name
        from .plottable_interactor import PointInteractor
        p = PointInteractor(self, self.subplot, zorder=zorder, id=id)
        if p.markersize is not None:
            markersize = p.markersize
        p.points(x, y, dx=dx, dy=dy, color=color, symbol=symbol, zorder=zorder,
                 markersize=markersize, label=label, hide_error=hide_error)

        self.subplot.set_yscale(self.yscale, nonposy='clip')
        self.subplot.set_xscale(self.xscale)

    def interactive_curve(self, x, y, dy=None, name='', color=0,
                          symbol=0, zorder=1, id=None, label=None):
        """Draw markers with error bars"""
        self.subplot.set_yscale('linear')
        self.subplot.set_xscale('linear')
        if id is None:
            id = name
        from .plottable_interactor import PointInteractor
        p = PointInteractor(self, self.subplot, zorder=zorder, id=id)
        p.curve(x, y, dy=dy, color=color, symbol=symbol, zorder=zorder,
                label=label)

        self.subplot.set_yscale(self.yscale, nonposy='clip')
        self.subplot.set_xscale(self.xscale)

    def plottable_selected(self, id):
        """
        Called to register a plottable as selected
        """
        #TODO: check that it really is in the list of plottables
        self.graph.selected_plottable = id

    def points(self, x, y, dx=None, dy=None,
               color=0, symbol=0, marker_size=5, label=None,
               id=None, hide_error=False):
        """Draw markers with error bars"""

        # Convert tuple (lo,hi) to array [(x-lo),(hi-x)]
        if dx is not None and type(dx) == type(()):
            dx = nx.vstack((x - dx[0], dx[1] - x)).transpose()
        if dy is not None and type(dy) == type(()):
            dy = nx.vstack((y - dy[0], dy[1] - y)).transpose()
        if dx is None and dy is None:
            self.subplot.plot(x, y, color=self._color(color),
                              marker=self._symbol(symbol),
                              markersize=marker_size,
                              linestyle='',
                              label=label)
        else:
            col = self._color(color)
            if hide_error:
                self.subplot.plot(x, y, color=col,
                                  marker=self._symbol(symbol),
                                  markersize=marker_size,
                                  linestyle='',
                                  label=label)
            else:
                self.subplot.errorbar(x, y, yerr=dy, xerr=None,
                                      ecolor=col, capsize=2, linestyle='',
                                      barsabove=False,
                                      mec=col, mfc=col,
                                      marker=self._symbol(symbol),
                                      markersize=marker_size,
                                      lolims=False, uplims=False,
                                      xlolims=False, xuplims=False, label=label)

        self.subplot.set_yscale(self.yscale, nonposy='clip')
        self.subplot.set_xscale(self.xscale)

    def _onToggleScale(self, event):
        """
        toggle axis and replot image

        """
        zmin_2D_temp = self.zmin_2D
        zmax_2D_temp = self.zmax_2D
        if self.scale == 'log_{10}':
            self.scale = 'linear'
            if self.zmin_2D is not None:
                zmin_2D_temp = math.pow(10, self.zmin_2D)
            if self.zmax_2D is not None:
                zmax_2D_temp = math.pow(10, self.zmax_2D)
        else:
            self.scale = 'log_{10}'
            if self.zmin_2D is not None:
                # min log value: no log(negative)
                if self.zmin_2D <= 0:
                    zmin_2D_temp = -32
                else:
                    zmin_2D_temp = math.log10(self.zmin_2D)
            if self.zmax_2D is not None:
                zmax_2D_temp = math.log10(self.zmax_2D)

        self.image(data=self.data, qx_data=self.qx_data,
                   qy_data=self.qy_data, xmin=self.xmin_2D,
                   xmax=self.xmax_2D,
                   ymin=self.ymin_2D, ymax=self.ymax_2D,
                   cmap=self.cmap, zmin=zmin_2D_temp,
                   zmax=zmax_2D_temp)

    def image(self, data, qx_data, qy_data, xmin, xmax, ymin, ymax,
              zmin, zmax, color=0, symbol=0, markersize=0,
              label='data2D', cmap=DEFAULT_CMAP):
        """
        Render the current data

        """
        self.data = data
        self.qx_data = qx_data
        self.qy_data = qy_data
        self.xmin_2D = xmin
        self.xmax_2D = xmax
        self.ymin_2D = ymin
        self.ymax_2D = ymax
        self.zmin_2D = zmin
        self.zmax_2D = zmax
        c = self._color(color)
        # If we don't have any data, skip.
        if self.data is None:
            return
        if self.data.ndim == 1:
            output = self._build_matrix()
        else:
            output = copy.deepcopy(self.data)
        # check scale
        if self.scale == 'log_{10}':
            try:
                if  self.zmin_2D <= 0  and len(output[output > 0]) > 0:
                    zmin_temp = self.zmin_2D
                    output[output > 0] = np.log10(output[output > 0])
                    #In log scale Negative values are not correct in general
                    #output[output<=0] = math.log(np.min(output[output>0]))
                elif self.zmin_2D <= 0:
                    zmin_temp = self.zmin_2D
                    output[output > 0] = np.zeros(len(output))
                    output[output <= 0] = -32
                else:
                    zmin_temp = self.zmin_2D
                    output[output > 0] = np.log10(output[output > 0])
                    #In log scale Negative values are not correct in general
                    #output[output<=0] = math.log(np.min(output[output>0]))
            except:
                #Too many problems in 2D plot with scale
                pass

        else:
            zmin_temp = self.zmin_2D
        self.cmap = cmap
        if self.dimension != 3:
            #Re-adjust colorbar
            self.subplot.figure.subplots_adjust(left=0.2, right=.8, bottom=.2)

            im = self.subplot.imshow(output, interpolation='nearest',
                                     origin='lower',
                                     vmin=zmin_temp, vmax=self.zmax_2D,
                                     cmap=self.cmap,
                                     extent=(self.xmin_2D, self.xmax_2D,
                                             self.ymin_2D, self.ymax_2D))

            cbax = self.subplot.figure.add_axes([0.84, 0.2, 0.02, 0.7])
        else:
            # clear the previous 2D from memory
            # mpl is not clf, so we do
            self.subplot.figure.clear()

            self.subplot.figure.subplots_adjust(left=0.1, right=.8, bottom=.1)

            X = self.x_bins[0:-1]
            Y = self.y_bins[0:-1]
            X, Y = np.meshgrid(X, Y)

            try:
                # mpl >= 1.0.0
                ax = self.subplot.figure.gca(projection='3d')
                #ax.disable_mouse_rotation()
                cbax = self.subplot.figure.add_axes([0.84, 0.1, 0.02, 0.8])
                if len(X) > 60:
                    ax.disable_mouse_rotation()
            except:
                # mpl < 1.0.0
                try:
                    from mpl_toolkits.mplot3d import Axes3D
                except:
                    logger.error("PlotPanel could not import Axes3D")
                self.subplot.figure.clear()
                ax = Axes3D(self.subplot.figure)
                if len(X) > 60:
                    ax.cla()
                cbax = None
            self.subplot.figure.canvas.resizing = False
            im = ax.plot_surface(X, Y, output, rstride=1, cstride=1, cmap=cmap,
                                 linewidth=0, antialiased=False)
            self.subplot.set_axis_off()

        if cbax is None:
            ax.set_frame_on(False)
            cb = self.subplot.figure.colorbar(im, shrink=0.8, aspect=20)
        else:
            cb = self.subplot.figure.colorbar(im, cax=cbax)
        cb.update_bruteforce(im)
        cb.set_label('$' + self.scale + '$')
        if self.dimension != 3:
            self.figure.canvas.draw_idle()
        else:
            self.figure.canvas.draw()

    def _build_matrix(self):
        """
        Build a matrix for 2d plot from a vector
        Returns a matrix (image) with ~ square binning
        Requirement: need 1d array formats of
        self.data, self.qx_data, and self.qy_data
        where each one corresponds to z, x, or y axis values

        """
        # No qx or qy given in a vector format
        if self.qx_data is None or self.qy_data is None \
                or self.qx_data.ndim != 1 or self.qy_data.ndim != 1:
            # do we need deepcopy here?
            return copy.deepcopy(self.data)

        # maximum # of loops to fillup_pixels
        # otherwise, loop could never stop depending on data
        max_loop = 1
        # get the x and y_bin arrays.
        self._get_bins()
        # set zero to None

        #Note: Can not use scipy.interpolate.Rbf:
        # 'cause too many data points (>10000)<=JHC.
        # 1d array to use for weighting the data point averaging
        #when they fall into a same bin.
        weights_data = np.ones([self.data.size])
        # get histogram of ones w/len(data); this will provide
        #the weights of data on each bins
        weights, xedges, yedges = np.histogram2d(x=self.qy_data,
                                                    y=self.qx_data,
                                                    bins=[self.y_bins, self.x_bins],
                                                    weights=weights_data)
        # get histogram of data, all points into a bin in a way of summing
        image, xedges, yedges = np.histogram2d(x=self.qy_data,
                                                  y=self.qx_data,
                                                  bins=[self.y_bins, self.x_bins],
                                                  weights=self.data)
        # Now, normalize the image by weights only for weights>1:
        # If weight == 1, there is only one data point in the bin so
        # that no normalization is required.
        image[weights > 1] = image[weights > 1] / weights[weights > 1]
        # Set image bins w/o a data point (weight==0) as None (was set to zero
        # by histogram2d.)
        image[weights == 0] = None

        # Fill empty bins with 8 nearest neighbors only when at least
        #one None point exists
        loop = 0

        # do while loop until all vacant bins are filled up up
        #to loop = max_loop
        while not(np.isfinite(image[weights == 0])).all():
            if loop >= max_loop:  # this protects never-ending loop
                break
            image = self._fillup_pixels(image=image, weights=weights)
            loop += 1

        return image

    def _get_bins(self):
        """
        get bins
        set x_bins and y_bins into self, 1d arrays of the index with
        ~ square binning
        Requirement: need 1d array formats of
        self.qx_data, and self.qy_data
        where each one corresponds to  x, or y axis values
        """
        # No qx or qy given in a vector format
        if self.qx_data is None or self.qy_data is None \
                or self.qx_data.ndim != 1 or self.qy_data.ndim != 1:
            # do we need deepcopy here?
            return copy.deepcopy(self.data)

        # find max and min values of qx and qy
        xmax = self.qx_data.max()
        xmin = self.qx_data.min()
        ymax = self.qy_data.max()
        ymin = self.qy_data.min()

        # calculate the range of qx and qy: this way, it is a little
        # more independent
        x_size = xmax - xmin
        y_size = ymax - ymin

        # estimate the # of pixels on each axes
        npix_y = int(math.floor(math.sqrt(len(self.qy_data))))
        npix_x = int(math.floor(len(self.qy_data) / npix_y))

        # bin size: x- & y-directions
        xstep = x_size / (npix_x - 1)
        ystep = y_size / (npix_y - 1)

        # max and min taking account of the bin sizes
        xmax = xmax + xstep / 2.0
        xmin = xmin - xstep / 2.0
        ymax = ymax + ystep / 2.0
        ymin = ymin - ystep / 2.0

        # store x and y bin centers in q space
        x_bins = np.linspace(xmin, xmax, npix_x)
        y_bins = np.linspace(ymin, ymax, npix_y)

        #set x_bins and y_bins
        self.x_bins = x_bins
        self.y_bins = y_bins

    def _fillup_pixels(self, image=None, weights=None):
        """
        Fill z values of the empty cells of 2d image matrix
        with the average over up-to next nearest neighbor points

        :param image: (2d matrix with some zi = None)

        :return: image (2d array )

        :TODO: Find better way to do for-loop below

        """
        # No image matrix given
        if image is None or np.ndim(image) != 2 \
                or np.isfinite(image).all() \
                or weights is None:
            return image
        # Get bin size in y and x directions
        len_y = len(image)
        len_x = len(image[1])
        temp_image = np.zeros([len_y, len_x])
        weit = np.zeros([len_y, len_x])
        # do for-loop for all pixels
        for n_y in range(len(image)):
            for n_x in range(len(image[1])):
                # find only null pixels
                if weights[n_y][n_x] > 0 or np.isfinite(image[n_y][n_x]):
                    continue
                else:
                    # find 4 nearest neighbors
                    # check where or not it is at the corner
                    if n_y != 0 and np.isfinite(image[n_y - 1][n_x]):
                        temp_image[n_y][n_x] += image[n_y - 1][n_x]
                        weit[n_y][n_x] += 1
                    if n_x != 0 and np.isfinite(image[n_y][n_x - 1]):
                        temp_image[n_y][n_x] += image[n_y][n_x - 1]
                        weit[n_y][n_x] += 1
                    if n_y != len_y - 1 and np.isfinite(image[n_y + 1][n_x]):
                        temp_image[n_y][n_x] += image[n_y + 1][n_x]
                        weit[n_y][n_x] += 1
                    if n_x != len_x - 1 and np.isfinite(image[n_y][n_x + 1]):
                        temp_image[n_y][n_x] += image[n_y][n_x + 1]
                        weit[n_y][n_x] += 1
                    # go 4 next nearest neighbors when no non-zero
                    # neighbor exists
                    if n_y != 0 and n_x != 0 and \
                            np.isfinite(image[n_y - 1][n_x - 1]):
                        temp_image[n_y][n_x] += image[n_y - 1][n_x - 1]
                        weit[n_y][n_x] += 1
                    if n_y != len_y - 1 and n_x != 0 and \
                            np.isfinite(image[n_y + 1][n_x - 1]):
                        temp_image[n_y][n_x] += image[n_y + 1][n_x - 1]
                        weit[n_y][n_x] += 1
                    if n_y != len_y and n_x != len_x - 1 and \
                            np.isfinite(image[n_y - 1][n_x + 1]):
                        temp_image[n_y][n_x] += image[n_y - 1][n_x + 1]
                        weit[n_y][n_x] += 1
                    if n_y != len_y - 1 and n_x != len_x - 1 and \
                            np.isfinite(image[n_y + 1][n_x + 1]):
                        temp_image[n_y][n_x] += image[n_y + 1][n_x + 1]
                        weit[n_y][n_x] += 1

        # get it normalized
        ind = (weit > 0)
        image[ind] = temp_image[ind] / weit[ind]

        return image

    def curve(self, x, y, dy=None, color=0, symbol=0, label=None):
        """Draw a line on a graph, possibly with confidence intervals."""
        c = self._color(color)
        self.subplot.set_yscale('linear')
        self.subplot.set_xscale('linear')

        self.subplot.plot(x, y, color=c, marker='',
                          linestyle='-', label=label)
        self.subplot.set_yscale(self.yscale)
        self.subplot.set_xscale(self.xscale)

    def _color(self, c):
        """Return a particular colour"""
        return self.colorlist[c % len(self.colorlist)]

    def _symbol(self, s):
        """Return a particular symbol"""
        return self.symbollist[s % len(self.symbollist)]

    def _replot(self, remove_fit=False):
        """
        Rescale the plottables according to the latest
        user selection and update the plot

        :param remove_fit: Fit line will be removed if True

        """
        self.graph.reset_scale()
        self._onEVT_FUNC_PROPERTY(remove_fit=remove_fit)
        #TODO: Why do we have to have the following line?
        self.fit_result.reset_view()
        self.graph.render(self)
        self.subplot.figure.canvas.draw_idle()

    def _onEVT_FUNC_PROPERTY(self, remove_fit=True, show=True):
        """
        Receive the x and y transformation from myDialog,
        Transforms x and y in View
        and set the scale
        """
        # The logic should be in the right order
        # Delete first, and then get the whole list...
        if remove_fit:
            self.graph.delete(self.fit_result)
            if hasattr(self, 'plots'):
                if 'fit' in list(self.plots.keys()):
                    del self.plots['fit']
        self.ly = None
        self.q_ctrl = None
        list = self.graph.returnPlottable()
        # Changing the scale might be incompatible with
        # currently displayed data (for instance, going
        # from ln to log when all plotted values have
        # negative natural logs).
        # Go linear and only change the scale at the end.
        self.set_xscale("linear")
        self.set_yscale("linear")
        _xscale = 'linear'
        _yscale = 'linear'
        for item in list:
            if item.id == 'fit':
                continue
            item.setLabel(self.xLabel, self.yLabel)
            # control axis labels from the panel itself
            yname, yunits = item.get_yaxis()
            if self.yaxis_label is not None:
                yname = self.yaxis_label
                yunits = self.yaxis_unit
            else:
                self.yaxis_label = yname
                self.yaxis_unit = yunits
            xname, xunits = item.get_xaxis()
            if self.xaxis_label is not None:
                xname = self.xaxis_label
                xunits = self.xaxis_unit
            else:
                self.xaxis_label = xname
                self.xaxis_unit = xunits
            # Goes through all possible scales
            if self.xLabel == "x":
                item.transformX(transform.toX, transform.errToX)
                self.graph._xaxis_transformed("%s" % xname, "%s" % xunits)
            if self.xLabel == "x^(2)":
                item.transformX(transform.toX2, transform.errToX2)
                xunits = convert_unit(2, xunits)
                self.graph._xaxis_transformed("%s^{2}" % xname, "%s" % xunits)
            if self.xLabel == "x^(4)":
                item.transformX(transform.toX4, transform.errToX4)
                xunits = convert_unit(4, xunits)
                self.graph._xaxis_transformed("%s^{4}" % xname, "%s" % xunits)
            if self.xLabel == "ln(x)":
                item.transformX(transform.toLogX, transform.errToLogX)
                self.graph._xaxis_transformed("\ln{(%s)}" % xname, "%s" % xunits)
            if self.xLabel == "log10(x)":
                item.transformX(transform.toX_pos, transform.errToX_pos)
                _xscale = 'log'
                self.graph._xaxis_transformed("%s" % xname, "%s" % xunits)
            if self.xLabel == "log10(x^(4))":
                item.transformX(transform.toX4, transform.errToX4)
                xunits = convert_unit(4, xunits)
                self.graph._xaxis_transformed("%s^{4}" % xname, "%s" % xunits)
                _xscale = 'log'
            if self.yLabel == "ln(y)":
                item.transformY(transform.toLogX, transform.errToLogX)
                self.graph._yaxis_transformed("\ln{(%s)}" % yname, "%s" % yunits)
            if self.yLabel == "y":
                item.transformY(transform.toX, transform.errToX)
                self.graph._yaxis_transformed("%s" % yname, "%s" % yunits)
            if self.yLabel == "log10(y)":
                item.transformY(transform.toX_pos, transform.errToX_pos)
                _yscale = 'log'
                self.graph._yaxis_transformed("%s" % yname, "%s" % yunits)
            if self.yLabel == "y^(2)":
                item.transformY(transform.toX2, transform.errToX2)
                yunits = convert_unit(2, yunits)
                self.graph._yaxis_transformed("%s^{2}" % yname, "%s" % yunits)
            if self.yLabel == "1/y":
                item.transformY(transform.toOneOverX, transform.errOneOverX)
                yunits = convert_unit(-1, yunits)
                self.graph._yaxis_transformed("1/%s" % yname, "%s" % yunits)
            if self.yLabel == "y*x^(2)":
                item.transformY(transform.toYX2, transform.errToYX2)
                xunits = convert_unit(2, self.xaxis_unit)
                self.graph._yaxis_transformed("%s \ \ %s^{2}" % (yname, xname),
                                              "%s%s" % (yunits, xunits))
            if self.yLabel == "y*x^(4)":
                item.transformY(transform.toYX4, transform.errToYX4)
                xunits = convert_unit(4, self.xaxis_unit)
                self.graph._yaxis_transformed("%s \ \ %s^{4}" % (yname, xname),
                                              "%s%s" % (yunits, xunits))
            if self.yLabel == "1/sqrt(y)":
                item.transformY(transform.toOneOverSqrtX,
                                transform.errOneOverSqrtX)
                yunits = convert_unit(-0.5, yunits)
                self.graph._yaxis_transformed("1/\sqrt{%s}" % yname,
                                              "%s" % yunits)
            if self.yLabel == "ln(y*x)":
                item.transformY(transform.toLogXY, transform.errToLogXY)
                self.graph._yaxis_transformed("\ln{(%s \ \ %s)}" % (yname, xname),
                                              "%s%s" % (yunits, self.xaxis_unit))
            if self.yLabel == "ln(y*x^(2))":
                item.transformY(transform.toLogYX2, transform.errToLogYX2)
                xunits = convert_unit(2, self.xaxis_unit)
                self.graph._yaxis_transformed("\ln (%s \ \ %s^{2})" % (yname, xname),
                                              "%s%s" % (yunits, xunits))
            if self.yLabel == "ln(y*x^(4))":
                item.transformY(transform.toLogYX4, transform.errToLogYX4)
                xunits = convert_unit(4, self.xaxis_unit)
                self.graph._yaxis_transformed("\ln (%s \ \ %s^{4})" % (yname, xname),
                                              "%s%s" % (yunits, xunits))
            if self.yLabel == "log10(y*x^(4))":
                item.transformY(transform.toYX4, transform.errToYX4)
                xunits = convert_unit(4, self.xaxis_unit)
                _yscale = 'log'
                self.graph._yaxis_transformed("%s \ \ %s^{4}" % (yname, xname),
                                              "%s%s" % (yunits, xunits))
            item.transformView()

        # set new label and units
        yname = self.graph.prop["ylabel"]
        yunits = ''
        xname = self.graph.prop["xlabel"]
        xunits = ''

        self.resetFitView()
        self.prevXtrans = self.xLabel
        self.prevYtrans = self.yLabel
        self.graph.render(self)
        self.set_xscale(_xscale)
        self.set_yscale(_yscale)

        self.xaxis(xname, xunits, self.xaxis_font,
                   self.xaxis_color, self.xaxis_tick)
        self.yaxis(yname, yunits, self.yaxis_font,
                   self.yaxis_color, self.yaxis_tick)
        self.subplot.texts = self.textList
        if show:
            self.subplot.figure.canvas.draw_idle()

    def onFitDisplay(self, tempx, tempy, xminView,
                     xmaxView, xmin, xmax, func):
        """
        Add a new plottable into the graph .In this case this plottable
        will be used to fit some data

        :param tempx: The x data of fit line
        :param tempy: The y data of fit line
        :param xminView: the lower bound of fitting range
        :param xminView: the upper bound of  fitting range
        :param xmin: the lowest value of data to fit to the line
        :param xmax: the highest value of data to fit to the line

        """
        xlim = self.subplot.get_xlim()
        ylim = self.subplot.get_ylim()

        # Saving value to redisplay in Fit Dialog when it is opened again
        self.Avalue, self.Bvalue, self.ErrAvalue, \
                      self.ErrBvalue, self.Chivalue = func
        self.xminView = xminView
        self.xmaxView = xmaxView
        self.xmin = xmin
        self.xmax = xmax
        #In case need to change the range of data plotted
        for item in self.graph.returnPlottable():
            item.onFitRange(None, None)
        # Create new data plottable with result
        self.fit_result.x = []
        self.fit_result.y = []
        self.fit_result.x = tempx
        self.fit_result.y = tempy
        self.fit_result.dx = None
        self.fit_result.dy = None
        #Load the view with the new values
        self.fit_result.reset_view()
        # Add the new plottable to the graph
        self.graph.add(self.fit_result)
        self.graph.render(self)
        self._offset_graph()
        if hasattr(self, 'plots'):
            # Used by Plotter1D
            fit_id = 'fit'
            self.fit_result.id = fit_id
            self.fit_result.title = 'Fit'
            self.fit_result.name = 'Fit'
            self.plots[fit_id] = self.fit_result
        self.subplot.set_xlim(xlim)
        self.subplot.set_ylim(ylim)
        self.subplot.figure.canvas.draw_idle()

    def onChangeCaption(self, event):
        """
        """
        if self.parent is None:
            return
        # get current caption
        old_caption = self.window_caption
        # Get new caption dialog
        dial = LabelDialog(None, -1, 'Modify Window Title', old_caption)
        if dial.ShowModal() == wx.ID_OK:
            new_caption = dial.getText()

            # send to guiframe to change the panel caption
            caption = self.parent.on_change_caption(self.window_name,
                                                    old_caption, new_caption)

            # also set new caption in plot_panels list
            self.parent.plot_panels[self.uid].window_caption = caption
            # set new caption
            self.window_caption = caption

        dial.Destroy()

    def onResetGraph(self, event):
        """
        Reset the graph by plotting the full range of data
        """
        for item in self.graph.returnPlottable():
            item.onReset()
        self.graph.render(self)
        self._onEVT_FUNC_PROPERTY(False)
        self.is_zoomed = False
        self.toolbar.update()

    def onPrint(self, event=None):
        self.toolbar.print_figure(event)

    def onPrinterSetup(self, event=None):
        """
        """
        self.canvas.Printer_Setup(event=event)
        self.Update()

    def onPrinterPreview(self, event=None):
        """
        Matplotlib camvas can no longer print itself.  Thus need to do
        everything ourselves: need to create a printpreview frame to to
        see the preview but needs a parent frame object.  Also needs a
        printout object (just as any printing task).
        """
        try:
            #check if parent is a frame.  If not keep getting the higher
            #parent till we find a frame
            _plot = self
            while not isinstance(_plot, wx.Frame):
                _plot = _plot.GetParent()
                assert _plot is not None

            #now create the printpeview object
            _preview = wx.PrintPreview(PlotPrintout(self.canvas),
                                       PlotPrintout(self.canvas))
            #and tie it to a printpreview frame then show it
            _frame = wx.PreviewFrame(_preview, _plot, "Print Preview", wx.Point(100, 100), wx.Size(600, 650))
            _frame.Centre(wx.BOTH)
            _frame.Initialize()
            _frame.Show(True)
        except:
            traceback.print_exc()
            pass

    def OnCopyFigureMenu(self, evt):
        """
        Copy the current figure to clipboard
        """
        try:
            self.toolbar.copy_figure(self.canvas)
        except:
            print("Error in copy Image")


#---------------------------------------------------------------
class NoRepaintCanvas(FigureCanvasWxAgg):
    """
    We subclass FigureCanvasWxAgg, overriding the _onPaint method, so that
    the draw method is only called for the first two paint events. After that,
    the canvas will only be redrawn when it is resized.

    """
    def __init__(self, *args, **kwargs):
        """
        """
        FigureCanvasWxAgg.__init__(self, *args, **kwargs)
        self._drawn = 0

    def _onPaint(self, evt):
        """
        Called when wxPaintEvt is generated

        """
        if not self._isRealized:
            self.realize()
        if self._drawn < 2:
            self.draw(repaint=False)
            self._drawn += 1
        self.gui_repaint(drawDC=wx.PaintDC(self))
