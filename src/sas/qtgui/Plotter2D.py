import logging
import copy
import numpy
import pylab

from PyQt4 import QtGui

# TODO: Replace the qt4agg calls below with qt5 equivalent.
# Requires some code modifications.
# https://www.boxcontrol.net/embedding-matplotlib-plot-on-pyqt5-gui.html
#
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

DEFAULT_CMAP = pylab.cm.jet

import sas.qtgui.PlotUtilities as PlotUtilities
import sas.qtgui.PlotHelper as PlotHelper

class Plotter2D(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Plotter2D, self).__init__(parent)

        # Required for the communicator
        self.parent = parent

        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # set the layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)
        self.setLayout(layout)

        # defaults
        self._current_plot = 111
        self._data = []
        self._qx_data = []
        self._qy_data = []
        self._color=0
        self._symbol=0
        self._scale = 'linear'

        # default color map
        self._cmap = DEFAULT_CMAP

        self._ax = self.figure.add_subplot(self._current_plot)

        # Notify the helper
        PlotHelper.addPlot(self)
        # Notify the listeners
        self.parent.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data=None):
        """ data setter """
        self._data = data
        self._qx_data=data.qx_data
        self._qy_data=data.qy_data
        self._xmin=data.xmin
        self._xmax=data.xmax
        self._ymin=data.ymin
        self._ymax=data.ymax
        self._zmin=data.zmin
        self._zmax=data.zmax
        self._label=data.name
        self.x_label(xlabel=data._xaxis + data._xunit)
        self.y_label(ylabel=data._yaxis + data._yunit)
        self.title(title=data.title)

    def title(self, title=""):
        """ title setter """
        self._title = title

    def id(self, id=""):
        """ id setter """
        self._id = id

    def x_label(self, xlabel=""):
        """ x-label setter """
        self._xlabel = r'$%s$'% xlabel

    def y_label(self, ylabel=""):
        """ y-label setter """
        self._ylabel = r'$%s$'% ylabel

    def clean(self):
        """
        Redraw the graph
        """
        self.figure.delaxes(self._ax)
        self._ax = self.figure.add_subplot(self._current_plot)

    def plot(self, marker=None, linestyle=None):
        """
        Plot 2D self._data
        """
        # create an axis
        ax = self._ax

        # graph properties
        ax.set_xlabel(self._xlabel)
        ax.set_ylabel(self._ylabel)
        ax.set_title(label=self._title)

        # Re-adjust colorbar
        # self.figure.subplots_adjust(left=0.2, right=.8, bottom=.2)

        output = PlotUtilities.build_matrix(self._data.data, self._qx_data, self._qy_data)

        im = ax.imshow(output,
                       interpolation='nearest',
                       origin='lower',
                       vmin=self._zmin, vmax=self._zmax,
                       cmap=self._cmap,
                       extent=(self._xmin, self._xmax,
                               self._ymin, self._ymax))

        cbax = self.figure.add_axes([0.84, 0.2, 0.02, 0.7])
        cb = self.figure.colorbar(im, cax=cbax)
        cb.update_bruteforce(im)
        cb.set_label('$' + self._scale + '$')

        # Schedule the draw for the next time the event loop is idle.
        self.canvas.draw_idle()

    def closeEvent(self, event):
        """
        Overwrite the close event adding helper notification
        """
        # Please remove me from your database.
        PlotHelper.deletePlot(PlotHelper.idOfPlot(self))
        # Notify the listeners
        self.parent.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())
        event.accept()

