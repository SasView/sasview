from __future__ import with_statement, print_function

# The Figure object is used to create backend-independent plot representations.
from matplotlib.figure import Figure
GUI_TOOLKIT = "qt5"
from matplotlib.backends.qt_compat import QtCore, QtWidgets

class EmbeddedPylab(object):
    """
    Define a 'with' context manager that lets you use pylab commands to
    plot on an embedded canvas.  This is useful for wrapping existing
    scripts in a GUI, and benefits from being more familiar than the
    underlying object oriented interface.

    As a convenience, the pylab module is returned on entry.

    Example
    -------

    The following example shows how to use the WxAgg backend in a wx panel::

        from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
        from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as Toolbar
        from matplotlib.figure import Figure

        class PlotPanel(wx.Panel):
            def __init__(self, *args, **kw):
                wx.Panel.__init__(self, *args, **kw)

                figure = Figure(figsize=(1,1), dpi=72)
                canvas = FigureCanvas(self, wx.ID_ANY, figure)
                self.pylab_interface = EmbeddedPylab(canvas)

                # Instantiate the matplotlib navigation toolbar and explicitly show it.
                mpl_toolbar = Toolbar(canvas)
                mpl_toolbar.Realize()

                # Create a vertical box sizer to manage the widgets in the main panel.
                sizer = wx.BoxSizer(wx.VERTICAL)
                sizer.Add(canvas, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, border=0)
                sizer.Add(mpl_toolbar, 0, wx.EXPAND|wx.ALL, border=0)

                # Associate the sizer with its container.
                self.SetSizer(sizer)
                sizer.Fit(self)

            def plot(self, *args, **kw):
                with self.pylab_interface as pylab:
                    pylab.clf()
                    pylab.plot(*args, **kw)

    Similar patterns should work for the other backends.  Check the source code
    in matplotlib.backend_bases.* for examples showing how to use matplotlib
    with other GUI toolkits.
    """
    def __init__(self, canvas):
        # delay loading pylab until matplotlib.use() is called
        from matplotlib.backend_bases import FigureManagerBase
        self.fm = FigureManagerBase(canvas, -1)
    def __enter__(self):
        # delay loading pylab until matplotlib.use() is called
        import pylab
        from matplotlib._pylab_helpers import Gcf
        Gcf.set_active(self.fm)
        return pylab
    def __exit__(self, *args, **kw):
        # delay loading pylab until matplotlib.use() is called
        from matplotlib._pylab_helpers import Gcf
        Gcf._activeQue = [f for f in Gcf._activeQue if f is not self.fm]
        try:
            del Gcf.figs[-1]
        except KeyError:
            pass


class _PlotViewShared(object):
    title = 'Plot'
    default_size = (600, 400)
    pylab_interface = None  # type: EmbeddedPylab
    plot_state = None
    model = None
    _calculating = False
    _need_plot =  False
    _need_newmodel = False

    def set_model(self, model):
        self.model = model
        if not self._is_shown():
            self._need_newmodel = True
        else:
            self._redraw(newmodel=True)

    def update_model(self, model):
        #print "profile update model"
        if self.model != model:  # ignore updates to different models
            return

        if not self._is_shown():
            self._need_newmodel = True
        else:
            self._redraw(newmodel=True)

    def update_parameters(self, model):
        #print "profile update parameters"
        if self.model != model:
            return

        if not self._is_shown():
            self._need_plot = True
        else:
            self._redraw(newmodel=self._need_newmodel)

    def _show(self):
        #print "showing theory"
        if self._need_newmodel:
            self._redraw(newmodel=True)
        elif self._need_plot:
            self._redraw(newmodel=False)

    def _redraw(self, newmodel=False):
        self._need_newmodel = newmodel
        if self._calculating:
            # That means that I've entered the thread through a
            # wx.Yield for the currently executing redraw.  I need
            # to cancel the running thread and force it to start
            # the calculation over.
            self.cancel_calculation = True
            #print "canceling calculation"
            return

        with self.pylab_interface as pylab:
            self._calculating = True

            #print "calling again"
            while True:
                #print "restarting"
                # We are restarting the calculation, so clear the reset flag
                self.cancel_calculation = False

                if self._need_newmodel:
                    self.newmodel()
                    if self.cancel_calculation:
                        continue
                    self._need_newmodel = False
                self.plot()
                if self.cancel_calculation:
                    continue
                pylab.draw()
                break
        self._need_plot = False
        self._calculating = False

    def get_state(self):
        #print "returning state",self.model,self.plot_state
        return self.model, self.plot_state

    def set_state(self, state):
        self.model, self.plot_state = state
        #print "setting state",self.model,self.plot_state
        self.plot()

    def menu(self):
        """
        Return a model specific menu
        """
        return None

    def newmodel(self, model=None):
        """
        New or updated model structure.  Do any sort or precalculation you
        need.  plot will be called separately when you are done.

        For long calculations, periodically perform wx.YieldIfNeeded()
        and then if self.cancel_calculation is True, return from the plot.
        """
        pass

    def plot(self):
        """
        Plot to the current figure.  If model has a plot method,
        just use that.

        For long calculations, periodically perform wx.YieldIfNeeded()
        and then if self.cancel_calculation is True, return from the plot.
        """
        if hasattr(self.model, 'plot'):
            self.model.plot()
        else:
            raise NotImplementedError("PlotPanel needs a plot method")

class PlotView(QtWidgets.QWidget, _PlotViewShared):
    def __init__(self, *args, **kw):
        QtWidgets.QWidget.__init__(self, *args, **kw)
        #import matplotlib.backends.backend_qt4agg
        #matplotlib.backends.backend_qt4agg.DEBUG = True
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
        from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as Toolbar

        #QtWidgets.QWidget.__init__(self, *args, **kw)

        # Can specify name on
        if 'title' in kw:
            self.title = kw['title']

        # Instantiate a figure object that will contain our plots.
        figure = Figure(figsize=(1,1), dpi=72)

        # Initialize the figure canvas, mapping the figure object to the plot
        # engine backend.
        canvas = FigureCanvas(figure)

        # Wx-Pylab magic ...
        # Make our canvas an active figure manager for pylab so that when
        # pylab plotting statements are executed they will operate on our
        # canvas and not create a new frame and canvas for display purposes.
        # This technique allows this application to execute code that uses
        # pylab stataments to generate plots and embed these plots in our
        # application window(s).  Use _activate_figure() to set.
        self.pylab_interface = EmbeddedPylab(canvas)

        # Instantiate the matplotlib navigation toolbar and explicitly show it.
        mpl_toolbar = Toolbar(canvas, self, False)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(canvas)
        layout.addWidget(mpl_toolbar)
        self.setLayout(layout)

    def _is_shown(self):
        return IS_MAC or self.IsShown()
