"""
    Mask editor
"""
################################################################################
# This software was developed by the University of Tennessee as part of the
# Distributed Data Analysis of Neutron Scattering Experiments (DANSE)
# project funded by the US National Science Foundation.
#
# If you use DANSE applications to do scientific research that leads to
# publication, we ask that you acknowledge the use of the software with the
# following sentence:
#
# This work benefited from DANSE software developed under NSF award DMR-0520547.
#
# copyright 2008, University of Tennessee
################################################################################


# #Todo: cleaning up, improving the maskplotpanel initialization, and testing.
import wx
import sys
import time
import matplotlib.cm as cm
import math
import copy
import numpy as np
from sas.sasgui.plottools.PlotPanel import PlotPanel
from sas.sasgui.plottools.plottables import Graph
from binder import BindArtist
from sas.sasgui.guiframe.dataFitting import Data1D, Data2D
from boxMask import BoxMask
from sector_mask import SectorMask
from AnnulusSlicer import CircularMask

from sas.sasgui.guiframe.events import SlicerEvent
from sas.sasgui.guiframe.events import StatusEvent
from functools import partial

(InternalEvent, EVT_INTERNAL) = wx.lib.newevent.NewEvent()

DEFAULT_CMAP = cm.get_cmap('jet')
_BOX_WIDTH = 76
_SCALE = 1e-6
_STATICBOX_WIDTH = 380

# SLD panel size
if sys.platform.count("win32") > 0:
    PANEL_SIZE = 350
    FONT_VARIANT = 0
else:
    PANEL_SIZE = 300
    FONT_VARIANT = 1

from sas.sascalc.data_util.calcthread import CalcThread

class CalcPlot(CalcThread):
    """
    Compute Resolution
    """
    def __init__(self,
                 id=-1,
                 panel=None,
                 image=None,
                 completefn=None,
                 updatefn=None,
                 elapsed=0,
                 yieldtime=0.01,
                 worktime=0.01):
        """
        """
        CalcThread.__init__(self, completefn, updatefn, yieldtime, worktime)
        self.starttime = 0
        self.id = id
        self.panel = panel
        self.image = image

    def compute(self):
        """
        excuting computation
        """
        elapsed = time.time() - self.starttime

        self.complete(panel=self.panel, image=self.image, elapsed=elapsed)


class MaskPanel(wx.Dialog):
    """
    Provides the Mask Editor GUI.
    """
    # # Internal nickname for the window, used by the AUI manager
    window_name = "Mask Editor"
    # # Name to appear on the window title bar
    window_caption = "Mask Editor"
    # # Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = True
    def __init__(self, parent=None, base=None,
                 data=None, id=-1, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        kwds["size"] = wx.Size(_STATICBOX_WIDTH * 0.8, PANEL_SIZE)
        wx.Dialog.__init__(self, parent, id=id, *args, **kwds)

        if data != None:
            # Font size
            kwds = []
            self.SetWindowVariant(variant=FONT_VARIANT)
            self.SetTitle("Mask Editor for " + data.name)
            self.parent = base
            self.data = data
            self.str = self.data.__str__()
            # # mask for 2D
            self.mask = data.mask
            self.default_mask = copy.deepcopy(data.mask)
            # # masked data from GUI
            self.slicer_mask = None
            self.slicer = None
            self.slicer_z = 5
            self.data.interactive = True
            # # when 2 data have the same id override the 1 st plotted
            self.name = self.data.name
            # Panel for 2D plot
            self.plotpanel = Maskplotpanel(self, -1,
                                           style=wx.TRANSPARENT_WINDOW)
            self.cmap = DEFAULT_CMAP
            # # Create Artist and bind it
            self.subplot = self.plotpanel.subplot
            self.connect = BindArtist(self.subplot.figure)
            self._setup_layout()
            self.newplot = Data2D(image=self.data.data)
            self.newplot.setValues(self.data)
            self.plotpanel.add_image(self.newplot)
            self._update_mask(self.mask)
            self.Centre()
            self.Layout()
            # bind evt_close to _draw in fitpage
            self.Bind(wx.EVT_CLOSE, self.OnClose)

    def ShowMessage(self, msg=''):
        """
        Show error message when mask covers whole data area
        """
        mssg = 'Erase, redraw or clear the mask. \n\r'
        mssg += 'The data range can not be completely masked... \n\r'
        mssg += msg
        wx.MessageBox(mssg, 'Error', wx.OK | wx.ICON_ERROR)

    def _setup_layout(self):
        """
        Set up the layout
        """
        note = "Note: This masking applies\n     only to %s." % self.data.name
        note_txt = wx.StaticText(self, -1, note)
        note_txt.SetForegroundColour(wx.RED)
        shape = "Select a Shape for Masking:"
        #  panel
        sizer = wx.GridBagSizer(10, 10)
        #---------inputs----------------
        shape_txt = wx.StaticText(self, -1, shape)
        sizer.Add(shape_txt, (1, 1), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
        self.innersector_rb = wx.RadioButton(self, -1, "Double Wings")
        self.Bind(wx.EVT_RADIOBUTTON, partial(self._on_mask, slicer=SectorMask, inside=True),
                  id=self.innersector_rb.GetId())
        sizer.Add(self.innersector_rb, (2, 1),
                  flag=wx.RIGHT | wx.BOTTOM, border=5)
        self.innercircle_rb = wx.RadioButton(self, -1, "Circular Disk")
        self.Bind(wx.EVT_RADIOBUTTON, partial(self._on_mask, slicer=CircularMask, inside=True),
                  id=self.innercircle_rb.GetId())
        sizer.Add(self.innercircle_rb, (3, 1),
                  flag=wx.RIGHT | wx.BOTTOM, border=5)
        self.innerbox_rb = wx.RadioButton(self, -1, "Rectangular Disk")
        self.Bind(wx.EVT_RADIOBUTTON, partial(self._on_mask, slicer=BoxMask, inside=True),
                  id=self.innerbox_rb.GetId())
        sizer.Add(self.innerbox_rb, (4, 1), flag=wx.RIGHT | wx.BOTTOM, border=5)
        self.outersector_rb = wx.RadioButton(self, -1, "Double Wing Window")
        self.Bind(wx.EVT_RADIOBUTTON, partial(self._on_mask, slicer=SectorMask, inside=False),
                  id=self.outersector_rb.GetId())
        sizer.Add(self.outersector_rb, (5, 1),
                  flag=wx.RIGHT | wx.BOTTOM, border=5)
        self.outercircle_rb = wx.RadioButton(self, -1, "Circular Window")
        self.Bind(wx.EVT_RADIOBUTTON, partial(self._on_mask, slicer=CircularMask, inside=False),
                  id=self.outercircle_rb.GetId())
        sizer.Add(self.outercircle_rb, (6, 1),
                  flag=wx.RIGHT | wx.BOTTOM, border=5)
        self.outerbox_rb = wx.RadioButton(self, -1, "Rectangular Window")
        self.Bind(wx.EVT_RADIOBUTTON, partial(self._on_mask, slicer=BoxMask, inside=False),
                  id=self.outerbox_rb.GetId())
        sizer.Add(self.outerbox_rb, (7, 1), flag=wx.RIGHT | wx.BOTTOM, border=5)
        sizer.Add(note_txt, (8, 1), flag=wx.RIGHT | wx.BOTTOM, border=5)
        self.innercircle_rb.SetValue(False)
        self.outercircle_rb.SetValue(False)
        self.innerbox_rb.SetValue(False)
        self.outerbox_rb.SetValue(False)
        self.innersector_rb.SetValue(False)
        self.outersector_rb.SetValue(False)
        sizer.Add(self.plotpanel, (0, 2), (13, 13),
                  wx.EXPAND | wx.LEFT | wx.RIGHT, 15)

        #-----Buttons------------1
        id_button = wx.NewId()
        button_add = wx.Button(self, id_button, "Add")
        button_add.SetToolTipString("Add the mask drawn.")
        button_add.Bind(wx.EVT_BUTTON, self._on_add_mask, id=button_add.GetId())
        sizer.Add(button_add, (13, 7))
        id_button = wx.NewId()
        button_erase = wx.Button(self, id_button, "Erase")
        button_erase.SetToolTipString("Erase the mask drawn.")
        button_erase.Bind(wx.EVT_BUTTON, self._on_erase_mask,
                          id=button_erase.GetId())
        sizer.Add(button_erase, (13, 8))
        id_button = wx.NewId()
        button_reset = wx.Button(self, id_button, "Reset")
        button_reset.SetToolTipString("Reset the mask.")
        button_reset.Bind(wx.EVT_BUTTON, self._on_reset_mask,
                          id=button_reset.GetId())
        sizer.Add(button_reset, (13, 9), flag=wx.RIGHT | wx.BOTTOM, border=15)
        id_button = wx.NewId()
        button_reset = wx.Button(self, id_button, "Clear")
        button_reset.SetToolTipString("Clear all mask.")
        button_reset.Bind(wx.EVT_BUTTON, self._on_clear_mask,
                          id=button_reset.GetId())
        sizer.Add(button_reset, (13, 10), flag=wx.RIGHT | wx.BOTTOM, border=15)
        sizer.AddGrowableCol(3)
        sizer.AddGrowableRow(2)
        self.SetSizerAndFit(sizer)
        self.Centre()
        self.Show(True)

    def _on_mask(self, event=None, slicer=BoxMask, inside=True):
        """
            Draw a slicer and use it as mask
            :param event: wx event
            :param slicer: Slicer class to use
            :param inside: whether we mask what's inside or outside the slicer
        """
        # get ready for next evt
        event.Skip()
        # from boxMask import BoxMask
        if event != None:
            self._on_clear_slicer(event)
        self.slicer_z += 1
        self.slicer = slicer(self, self.subplot,
                             zorder=self.slicer_z, side=inside)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)
        self.update()
        self.slicer_mask = self.slicer.update()

    def _on_add_mask(self, event):
        """
        Add new mask to old mask
        """
        if not self.slicer is None:
            data = Data2D()
            data = self.data
            self.slicer_mask = self.slicer.update()
            data.mask = self.data.mask & self.slicer_mask
            self._check_display_mask(data.mask, event)

    def _check_display_mask(self, mask, event):
        """
        check if the mask valid and update the plot

        :param mask: mask data
        """
        # # Redraw the current image
        self._update_mask(mask)

    def _on_erase_mask(self, event):
        """
        Erase new mask from old mask
        """
        if not self.slicer is None:
            self.slicer_mask = self.slicer.update()
            mask = self.data.mask
            mask[self.slicer_mask == False] = True
            self._check_display_mask(mask, event)

    def _on_reset_mask(self, event):
        """
        Reset mask to the original mask
        """
        self.slicer_z += 1
        self.slicer = BoxMask(self, self.subplot,
                              zorder=self.slicer_z, side=True)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)
        mask = copy.deepcopy(self.default_mask)
        self.data.mask = mask
        # update mask plot
        self._check_display_mask(mask, event)

    def _on_clear_mask(self, event):
        """
        Clear mask
        """
        self.slicer_z += 1
        self.slicer = BoxMask(self, self.subplot,
                              zorder=self.slicer_z, side=True)
        self.subplot.set_ylim(self.data.ymin, self.data.ymax)
        self.subplot.set_xlim(self.data.xmin, self.data.xmax)
        mask = np.ones(len(self.data.mask), dtype=bool)
        self.data.mask = mask
        # update mask plot
        self._check_display_mask(mask, event)

    def _on_clear_slicer(self, event):
        """
        Clear the slicer on the plot
        """
        if not self.slicer is None:
            self.slicer.clear()
            self.subplot.figure.canvas.draw()
            self.slicer = None

    def update(self, draw=True):
        """
        Respond to changes in the model by recalculating the
        profiles and resetting the widgets.
        """
        self.plotpanel.draw()

    def _set_mask(self, mask):
        """
        Set mask
        """
        self.data.mask = mask

    def set_plot_unfocus(self):
        """
        Not implemented
        """
        pass

    def _update_mask(self, mask):
        """
        Respond to changes in masking
        """
        # the case of liitle numbers of True points
        if len(mask[mask]) < 10 and self.data != None:
            self.ShowMessage()
            mask = copy.deepcopy(self.mask)
            self.data.mask = mask
        else:
            self.mask = mask
        # make temperary data to plot
        temp_mask = np.zeros(len(mask))
        temp_data = copy.deepcopy(self.data)
        # temp_data default is None
        # This method is to distinguish between masked point and data point = 0.
        temp_mask = temp_mask / temp_mask
        temp_mask[mask] = temp_data.data[mask]
        # set temp_data value for self.mask==True, else still None
        # temp_mask[mask] = temp_data[mask]

        # TODO: refactor this horrible logic
        temp_data.data[mask == False] = temp_mask[mask == False]
        self.plotpanel.clear()
        if self.slicer != None:
            self.slicer.clear()
            self.slicer = None
        # Post slicer None event
        event = self._getEmptySlicerEvent()
        wx.PostEvent(self, event)

        # #use this method
        # set zmax and zmin to plot: Fix it w/ data.
        if self.plotpanel.scale == 'log_{10}':
            zmax = math.log10(max(self.data.data[self.data.data > 0]))
            zmin = math.log10(min(self.data.data[self.data.data > 0]))
        else:
            zmax = max(self.data.data[self.data.data > 0])
            zmin = min(self.data.data[self.data.data > 0])
        # plot
        self.plotpanel.image(data=temp_mask,
                             qx_data=self.data.qx_data,
                             qy_data=self.data.qy_data,
                             xmin=self.data.xmin,
                             xmax=self.data.xmax,
                             ymin=self.data.ymin,
                             ymax=self.data.ymax,
                             zmin=zmin,
                             zmax=zmax,
                             cmap=self.cmap,
                             color=0, symbol=0, label=self.data.name)
        # axis labels
        self.plotpanel.axes[0].set_xlabel('$\\rm{Q}_{x}(A^{-1})$')
        self.plotpanel.axes[0].set_ylabel('$\\rm{Q}_{y}(A^{-1})$')
        self.plotpanel.render()
        self.plotpanel.subplot.figure.canvas.draw_idle()

    def _getEmptySlicerEvent(self):
        """
        create an empty slicervent
        """
        self.innerbox_rb.SetValue(False)
        self.outerbox_rb.SetValue(False)
        self.innersector_rb.SetValue(False)
        self.outersector_rb.SetValue(False)
        self.innercircle_rb.SetValue(False)
        self.outercircle_rb.SetValue(False)
        return SlicerEvent(type=None,
                           params=None,
                           obj_class=None)

    def _draw_model(self, event):
        """
         on_close, update the model2d plot
        """
        pass

    def freeze_axes(self):
        """
        freeze axes
        """
        self.plotpanel.axes_frozen = True

    def thaw_axes(self):
        """
        thaw axes
        """
        self.plotpanel.axes_frozen = False

    def onMouseMotion(self, event):
        """
        onMotion event
        """
        pass

    def onWheel(self, event):
        """
        on wheel event
        """
        pass

    def OnClose(self, event):
        """
            Processing close event
        """
        try:
            self.parent._draw_masked_model(event)
        except:
            # when called by data panel
            event.Skip()
            pass

class FloatPanel(wx.Dialog):
    """
    Provides the Mask Editor GUI.
    """
    # # Internal nickname for the window, used by the AUI manager
    window_name = "Plot"
    # # Name to appear on the window title bar
    window_caption = "Plot"
    # # Flag to tell the AUI manager to put this panel in the center pane
    CENTER_PANE = False
    ID = wx.NewId()
    def __init__(self, parent=None, base=None,
                 data=None, dimension=1, id=ID, *args, **kwds):
        kwds["style"] = wx.DEFAULT_DIALOG_STYLE
        kwds["size"] = wx.Size(PANEL_SIZE * 1.5, PANEL_SIZE * 1.5)
        wx.Dialog.__init__(self, parent, id=id, *args, **kwds)

        if data != None:
            # Font size
            kwds = []
            self.SetWindowVariant(variant=FONT_VARIANT)
            self.SetTitle("Plot " + data.name)
            self.parent = base
            self.data = data
            self.str = self.data.__str__()
            # # when 2 data have the same id override the 1 st plotted
            self.name = self.data.name
            self.dimension = dimension
            # Panel for 2D plot
            self.plotpanel = Maskplotpanel(self, -1, dimension,
                                           style=wx.TRANSPARENT_WINDOW)
            self.plotpanel._SetInitialSize()
            self.plotpanel.prevXtrans = "x"
            self.plotpanel.prevYtrans = "y"

            self.cmap = DEFAULT_CMAP
            # # Create Artist and bind it
            self.subplot = self.plotpanel.subplot
            self._setup_layout()
            if self.dimension == 1:
                self.newplot = Data1D(x=data.x, y=data.y,
                                      dx=data.dx, dy=data.dy)
                self.newplot.name = data.name
            else:
                self.newplot = Data2D(image=self.data.data)
                self.newplot.setValues(self.data)
                    # Compute and get the image plot
            self.get_plot()
            # self.plotpanel.add_image(self.newplot)
            self.Centre()
            self.Layout()

    def get_plot(self):
        """
        Get Plot panel
        """
        cal_plot = CalcPlot(panel=self.plotpanel,
                            image=self.newplot,
                            completefn=self.complete)
        cal_plot.queue()

    def complete(self, panel, image, elapsed=None):
        """
        Plot image

        :param image: newplot [plotpanel]
        """
        wx.CallAfter(panel.add_image, image)

    def _setup_layout(self):
        """
        Set up the layout
        """
        #  panel
        sizer = wx.GridBagSizer(10, 10)
        if self.dimension == 3:
            note = "Note: I am very SLOW.     Please be PATIENT...\n"
            if len(self.data.data) > 3600:
                note += "Rotation disabled for pixels > 60x60."
            note_txt = wx.StaticText(self, -1, note)
            note_txt.SetForegroundColour(wx.RED)
            sizer.Add(note_txt, (0, 2), flag=wx.RIGHT | wx.TOP, border=5)

        sizer.Add(self.plotpanel, (1, 0), (9, 9),
                  wx.EXPAND | wx.ALL, 15)

        sizer.AddGrowableCol(3)
        sizer.AddGrowableRow(2)

        self.SetSizerAndFit(sizer)
        self.Centre()
        self.Show(True)

    def set_plot_unfocus(self):
        """
        Not implemented
        """
        pass

    def _draw_model(self, event):
        """
         on_close, update the model2d plot
        """
        pass

    def freeze_axes(self):
        """
        freeze axes
        """
        self.plotpanel.axes_frozen = True

    def thaw_axes(self):
        """
        thaw axes
        """
        self.plotpanel.axes_frozen = False

    def OnClose(self, event):
        """
        """
        try:
            self.plotpanel.subplot.figure.clf()
            self.plotpanel.Close()
        except:
            # when called by data panel
            event.Skip()
            pass

class Maskplotpanel(PlotPanel):
    """
    PlotPanel for Quick plot and masking plot
    """
    def __init__(self, parent, id=-1, dimension=2, color=None, dpi=None, **kwargs):
        """
        """
        PlotPanel.__init__(self, parent, id=id, color=color, dpi=dpi, **kwargs)

        # Keep track of the parent Frame
        self.parent = parent
        # Internal list of plottable names (because graph
        # doesn't have a dictionary of handles for the plottables)
        self.dimension = dimension
        self.plots = {}
        self.graph = Graph()
        # add axis labels
        self.graph.xaxis('\\rm{x} ', '')
        self.graph.yaxis('\\rm{y} ', '')

    def add_toolbar(self):
        """
        Add toolbar
        """
        # Not implemented
        pass

    def on_set_focus(self, event):
        """
        send to the parenet the current panel on focus
        """
        if self.dimension == 3:
            pass
        else:
            self.draw()

    def add_image(self, plot):
        """
        Add Image
        """
        self.plots[plot.name] = plot
        # init graph
        self.graph = Graph()
        # add plot
        self.graph.add(plot)
        # add axes
        if self.dimension == 1:
            self.xaxis_label = '\\rm{x} '
            self.xaxis_unit = ''
            self.yaxis_label = '\\rm{y} '
            self.yaxis_unit = ''
        # draw
        # message
        status_type = 'progress'
        msg = 'Plotting...'
        self._status_info(msg, status_type)
        status_type = 'stop'
        self.graph.render(self)
        self.subplot.figure.canvas.resizing = False
        if self.dimension < 3:
            self.graph.render(self)
            self.subplot.figure.canvas.draw()
        elif FONT_VARIANT:
            self.subplot.figure.canvas.draw()
        msg = 'Plotting Completed.'
        self._status_info(msg, status_type)

    def onMouseMotion(self, event):
        """
        Disable dragging 2D image
        """
        pass

    def onWheel(self, event):
        """
        """
        pass

    def onLeftDown(self, event):
        """
        Disables LeftDown
        """
        pass

    def onPick(self, event):
        """
        Disables OnPick
        """
        pass

    def draw(self):
        """
        Draw
        """
        # message
        status_type = 'progress'
        msg = 'Plotting...'
        self._status_info(msg, status_type)
        status_type = 'stop'

        if not self.dimension == 3:
            self.subplot.figure.canvas.draw_idle()

        msg = 'Plotting Completed.'
        self._status_info(msg, status_type)

    def onContextMenu(self, event):
        """
        Default context menu for a plot panel
        """
        # Selective Slicer plot popup menu
        slicerpop = wx.Menu()

        id = wx.NewId()
        slicerpop.Append(id, '&Print Image', 'Print image')
        wx.EVT_MENU(self, id, self.onPrint)

        id = wx.NewId()
        slicerpop.Append(id, '&Copy to Clipboard', 'Copy to the clipboard')
        wx.EVT_MENU(self, id, self.OnCopyFigureMenu)

        if self.dimension == 1:
            id = wx.NewId()
            slicerpop.Append(id, '&Change Scale')
            wx.EVT_MENU(self, id, self._onProperties)
        else:
            slicerpop.AppendSeparator()
            id_cm = wx.NewId()
            slicerpop.Append(id_cm, '&Toggle Linear/Log scale')
            wx.EVT_MENU(self, id_cm, self._onToggleScale)

        pos = event.GetPosition()
        pos = self.ScreenToClient(pos)
        self.PopupMenu(slicerpop, pos)

    def _status_info(self, msg='', type="update"):
        """
        Status msg
        """
        if self.parent.parent.parent != None:
            wx.PostEvent(self.parent.parent.parent,
                         StatusEvent(status=msg, type=type))

class ViewerFrame(wx.Frame):
    """
    Add comment
    """
    def __init__(self, parent, id, title):
        """
        comment
        :param parent: parent panel/container
        """
        # Initialize the Frame object
        wx.Frame.__init__(self, parent, id, title,
                          wx.DefaultPosition, wx.Size(950, 850))
        # Panel for 1D plot
        self.plotpanel = Maskplotpanel(self, -1, style=wx.RAISED_BORDER)

class ViewApp(wx.App):
    def OnInit(self):
        frame = ViewerFrame(None, -1, 'testView')
        frame.Show(True)
        # self.SetTopWindow(frame)

        return True

if __name__ == "__main__":
    app = ViewApp(0)
    app.MainLoop()
