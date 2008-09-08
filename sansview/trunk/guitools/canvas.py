import wx
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg, _convert_agg_to_wx_bitmap
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backend_bases import MouseEvent

class FigureCanvas(FigureCanvasWxAgg):
    """
    Add features to the wx agg canvas for better support of AUI and
    faster plotting.
    """

    def __init__(self, *args, **kw):
        super(FigureCanvas,self).__init__(*args, **kw)
        self._isRendered = False
        
        # Create an timer for handling draw_idle requests
        # If there are events pending when the timer is
        # complete, reset the timer and continue.  The
        # alternative approach, binding to wx.EVT_IDLE,
        # doesn't behave as nicely.
        self.idletimer = wx.CallLater(1,self._onDrawIdle)
        # Support for mouse wheel
        self.Bind(wx.EVT_MOUSEWHEEL, self._onMouseWheel)


    def draw_idle(self, *args, **kwargs):
        """
        Render after a delay if no other render requests have been made.
        """
        self.idletimer.Restart(5, *args, **kwargs)  # Delay by 5 ms

    def _onDrawIdle(self, *args, **kwargs):
        if False and wx.GetApp().Pending():
            self.idletimer.Restart(5, *args, **kwargs)
        else:
            self.draw(*args, **kwargs)

    def draw(self, drawDC=None):
        """
        Render the figure using agg.
        """

        # Only draw if window is shown, otherwise graph will bleed through
        # on the notebook style AUI widgets.
        if self.IsShownOnScreen():
            self._isRendered = True
            FigureCanvasWxAgg.draw(self)
            self.bitmap = _convert_agg_to_wx_bitmap(self.get_renderer(), None)
            self.gui_repaint(drawDC=drawDC)
        else:
            self._isRendered = False
    def _onMouseWheel(self, evt):
        """Translate mouse wheel events into matplotlib events"""
        # Determine mouse location
        w,h = self.figure.canvas.get_width_height()
        x = evt.GetX()
        y = h - evt.GetY()

        # Convert delta/rotation/rate into a floating point step size
        delta = evt.GetWheelDelta()
        rotation = evt.GetWheelRotation()
        rate = evt.GetLinesPerAction()
        #print "delta,rotation,rate",delta,rotation,rate
        step = rate*float(rotation)/delta

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
        setattr(event,'step',step)
        self.callbacks.process(s, event)


    def _onPaint(self, evt):
        """
        Called when wxPaintEvt is generated
        """

        if not self._isRealized:
            self.realize()

        # Need to draw the graph the first time it is shown otherwise
        # it is a black canvas.  After that we can use the rendered 
        # bitmap for updates.
        if self._isRendered:
            self.gui_repaint(drawDC=wx.PaintDC(self))
        else:
            self.draw(drawDC=wx.PaintDC(self))

        evt.Skip()
   