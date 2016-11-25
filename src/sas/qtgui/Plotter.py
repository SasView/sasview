import logging

from PyQt4 import QtGui

# TODO: Replace the qt4agg calls below with qt5 equivalent.
# Requires some code modifications.
# https://www.boxcontrol.net/embedding-matplotlib-plot-on-pyqt5-gui.html
#
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

import sas.qtgui.PlotHelper as PlotHelper

class Plotter(QtGui.QDialog):
    def __init__(self, parent=None):
        super(Plotter, self).__init__(parent)

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
        self._title = "Plot"
        self._id = ""
        self._xlabel = "X"
        self._ylabel = "Y"
        self._ax = self.figure.add_subplot(self._current_plot)

        # Notify the helper
        PlotHelper.addPlot(self)
        # Notify the listeners
        self.parent.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())

    @property
    def data(self):
        """ data getter """
        return self._data

    @data.setter
    def data(self, value):
        """ data setter """
        self._data = value

    def title(self, title=""):
        """ title setter """
        self._title = title

    def id(self, id=""):
        """ id setter """
        self._id = id

    def x_label(self, xlabel=""):
        """ x-label setter """
        self._xlabel = xlabel

    def y_label(self, ylabel=""):
        """ y-label setter """
        self._ylabel = ylabel

    def clean(self):
        """
        Redraw the graph
        """
        self.figure.delaxes(self._ax)
        self._ax = self.figure.add_subplot(self._current_plot)

    def plot(self, marker=None, linestyle=None):
        """
        Plot self._data
        """
        # create an axis
        ax = self._ax

        if marker == None:
            marker = '*'

        if linestyle == None:
            linestyle = '-'

        # plot data with legend
        ax.plot(self._data.x, self._data.y, marker=marker, linestyle=linestyle, label=self._title)

        # Now add the legend with some customizations.
        legend = ax.legend(loc='lower left', shadow=True)

        ax.set_ylabel(self._ylabel)
        ax.set_xlabel(self._xlabel)

        ax.set_yscale('log')
        ax.set_xscale('log')

        # refresh canvas
        self.canvas.draw()

    def closeEvent(self, event):
        """
        Overwrite the close event adding helper notification
        """
        # Please remove me from your database.
        PlotHelper.deletePlot(PlotHelper.idOfPlot(self))
        # Notify the listeners
        self.parent.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())
        event.accept()

