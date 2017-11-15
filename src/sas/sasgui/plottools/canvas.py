"""
This module implements a faster canvas for plotting.
it ovewrites some matplolib methods to allow printing on sys.platform=='win32'
"""
import wx
import sys
import logging
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backend_bases import MouseEvent, RendererBase
from matplotlib.backends.backend_wx import GraphicsContextWx, PrintoutWx
from matplotlib.backends.backend_wx import RendererWx

logger = logging.getLogger(__name__)


def draw_image(self, x, y, im, bbox, clippath=None, clippath_trans=None):
    """
    Draw the image instance into the current axes;

    :param x: is the distance in pixels from the left hand side of the canvas.
    :param y: the distance from the origin.  That is, if origin is
        upper, y is the distance from top.  If origin is lower, y
        is the distance from bottom
    :param im: the class`matplotlib._image.Image` instance
    :param bbox: a class `matplotlib.transforms.Bbox` instance for clipping, or
        None

    """
    pass


def select(self):
    """
    """
    pass


def unselect(self):
    """
    """
    pass


def OnPrintPage(self, page):
    """
    override printPage of matplotlib
    """
    self.canvas.draw()
    dc = self.GetDC()
    try:
        (ppw, pph) = self.GetPPIPrinter()  # printer's pixels per in
    except:
        ppw = 1
        pph = 1
    (pgw, _) = self.GetPageSizePixels()  # page size in pixels
    (dcw, _) = dc.GetSize()
    (grw, _) = self.canvas.GetSizeTuple()

    # save current figure dpi resolution and bg color,
    # so that we can temporarily set them to the dpi of
    # the printer, and the bg color to white
    bgcolor = self.canvas.figure.get_facecolor()
    fig_dpi = self.canvas.figure.dpi

    # draw the bitmap, scaled appropriately
    vscale = float(ppw) / fig_dpi

    # set figure resolution,bg color for printer
    self.canvas.figure.dpi = ppw
    self.canvas.figure.set_facecolor('#FFFFFF')

    renderer = RendererWx(self.canvas.bitmap, self.canvas.figure.dpi)
    self.canvas.figure.draw(renderer)
    self.canvas.bitmap.SetWidth(int(self.canvas.bitmap.GetWidth() * vscale))
    self.canvas.bitmap.SetHeight(int(self.canvas.bitmap.GetHeight() * vscale))
    self.canvas.draw()

    # page may need additional scaling on preview
    page_scale = 1.0
    if self.IsPreview():
        page_scale = float(dcw) / pgw

    # get margin in pixels = (margin in in) * (pixels/in)
    top_margin = int(self.margin * pph * page_scale)
    left_margin = int(self.margin * ppw * page_scale)

    # set scale so that width of output is self.width inches
    # (assuming grw is size of graph in inches....)
    user_scale = (self.width * fig_dpi * page_scale) / float(grw)
    dc.SetDeviceOrigin(left_margin, top_margin)
    dc.SetUserScale(user_scale, user_scale)

    # this cute little number avoid API inconsistencies in wx
    try:
        dc.DrawBitmap(self.canvas.bitmap, 0, 0)
    except:
        try:
            dc.DrawBitmap(self.canvas.bitmap, (0, 0))
        except:
            logger.error(sys.exc_info()[1])

    # restore original figure  resolution
    self.canvas.figure.set_facecolor(bgcolor)
    # # used to be self.canvas.figure.dpi.set( fig_dpi)
    self.canvas.figure.dpi = fig_dpi
    self.canvas.draw()
    return True

GraphicsContextWx.select = select
GraphicsContextWx.unselect = unselect
PrintoutWx.OnPrintPage = OnPrintPage
RendererBase.draw_image = draw_image


class FigureCanvas(FigureCanvasWxAgg):
    """
    Add features to the wx agg canvas for better support of AUI and
    faster plotting.
    """

    def __init__(self, *args, **kw):
        super(FigureCanvas, self).__init__(*args, **kw)
        self._isRendered = False

        # Create an timer for handling draw_idle requests
        # If there are events pending when the timer is
        # complete, reset the timer and continue.  The
        # alternative approach, binding to wx.EVT_IDLE,
        # doesn't behave as nicely.
        self.idletimer = wx.CallLater(1, self._onDrawIdle)
        # panel information
        self.panel = None
        self.resizing = False
        self.xaxis = None
        self.yaxis = None
        self.ndraw = 0
        # Support for mouse wheel
        self.Bind(wx.EVT_MOUSEWHEEL, self._onMouseWheel)

    def set_panel(self, panel):
        """
        Set axes
        """
        # set panel
        self.panel = panel
        # set axes
        self.xaxis = panel.subplot.xaxis
        self.yaxis = panel.subplot.yaxis

    def draw_idle(self, *args, **kwargs):
        """
        Render after a delay if no other render requests have been made.
        """
        self.panel.subplot.grid(self.panel.grid_on)
        if self.panel.legend is not None and self.panel.legend_pos_loc:
            self.panel.legend._loc = self.panel.legend_pos_loc
        self.idletimer.Restart(5, *args, **kwargs)  # Delay by 5 ms

    def _onDrawIdle(self, *args, **kwargs):
        """
        """
        if False and wx.GetApp().Pending():
            self.idletimer.Restart(5, *args, **kwargs)
        else:
            # Draw plot, changes resizing too
            self.draw(*args, **kwargs)
            self.resizing = False

    def _get_axes_switch(self):
        """
        """
        # Check resize whether or not True
        if self.panel.dimension == 3:
            return

        # This is for fast response when plot is being resized
        if not self.resizing:
            self.xaxis.set_visible(True)
            self.yaxis.set_visible(True)
            self.panel.schedule_full_draw('del')
        else:
            self.xaxis.set_visible(False)
            self.yaxis.set_visible(False)
            self.panel.schedule_full_draw('append')
        # set the resizing back to default= False
        self.set_resizing(False)

    def set_resizing(self, resizing=False):
        """
        Setting the resizing
        """
        self.resizing = resizing
        self.panel.set_resizing(False)

    def draw(self, drawDC=None):
        """
        Render the figure using agg.
        """
        # Only draw if window is shown, otherwise graph will bleed through
        # on the notebook style AUI widgets.
        #    raise
        fig = FigureCanvasWxAgg
        if self.IsShownOnScreen() and self.ndraw != 1:
            self._isRendered = True
            self._get_axes_switch()
            # import time
            # st = time.time()
            try:
                fig.draw(self)
            except ValueError:
                logger.error(sys.exc_info()[1])
        else:
            self._isRendered = False
        if self.ndraw <= 1:
            self.ndraw += 1

    def _onMouseWheel(self, evt):
        """Translate mouse wheel events into matplotlib events"""
        # Determine mouse location
        _, h = self.figure.canvas.get_width_height()
        x = evt.GetX()
        y = h - evt.GetY()

        # Convert delta/rotation/rate into a floating point step size
        delta = evt.GetWheelDelta()
        rotation = evt.GetWheelRotation()
        rate = evt.GetLinesPerAction()
        # print "delta,rotation,rate",delta,rotation,rate
        step = rate * float(rotation) / delta

        # Convert to mpl event
        evt.Skip()
        self.scroll_event(x, y, step, guiEvent=evt)

    def scroll_event(self, x, y, step=1, guiEvent=None):
        """
        Backend derived classes should call this function on any
        scroll wheel event.  x,y are the canvas coords: 0,0 is lower,
        left.  button and key are as defined in MouseEvent
        """
        button = 'up' if step >= 0 else 'down'
        self._button = button
        s = 'scroll_event'
        event = MouseEvent(s, self, x, y, button, self._key, guiEvent=guiEvent)
        setattr(event, 'step', step)
        self.callbacks.process(s, event)
        if step != 0:
            self.panel.is_zoomed = True

    def _onRightButtonDown(self, evt):
        """
        Overload the right button down call back to avoid a problem
        with the context menu over matplotlib plots on linux.

        :TODO: Investigate what the root cause of the problem is.

        """
        if sys.platform == 'linux2' or self.panel.dimension == 3:
            evt.Skip()
        else:
            FigureCanvasWxAgg._onRightButtonDown(self, evt)
            # This solves the focusing on rightclick.
            # Todo: better design
            self.panel.parent.set_plot_unfocus()
            self.panel.on_set_focus(None)
        return

    # CRUFT: wx 3.0.0.0 on OS X doesn't release the mouse on leaving window
    def _onLeave(self, evt):
        if self.HasCapture(): self.ReleaseMouse()
        super(FigureCanvas, self)._onLeave(evt)
