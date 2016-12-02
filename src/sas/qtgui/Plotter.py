import logging

from PyQt4 import QtGui

# TODO: Replace the qt4agg calls below with qt5 equivalent.
# Requires some code modifications.
# https://www.boxcontrol.net/embedding-matplotlib-plot-on-pyqt5-gui.html
#
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib as mpl

import sas.qtgui.PlotHelper as PlotHelper
from sas.qtgui.PlotterBase import PlotterBase

class Plotter(PlotterBase):
    def __init__(self, parent=None, quickplot=False):
        super(Plotter, self).__init__(parent, quickplot=quickplot)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """ data setter """
        self._data = value
        self.label=value.name
        self.xLabel(xlabel="%s(%s)"%(value._xaxis, value._xunit))
        self.yLabel(ylabel="%s(%s)"%(value._yaxis, value._yunit))
        self.title(title=value.title)

    def plot(self, marker=None, linestyle=None):
        """
        Plot self._data
        """
        # create an axis
        ax = self.ax

        if marker == None:
            marker = '*'

        if linestyle == None:
            linestyle = '-'

        # plot data with legend
        ax.plot(self._data.x, self._data.y, marker=marker, linestyle=linestyle, label=self.title)

        # Now add the legend with some customizations.
        legend = ax.legend(loc='upper right', shadow=True)

        ax.set_ylabel(self.y_label)
        ax.set_xlabel(self.x_label)
        # Title only for regular charts
        if not self.quickplot:
            ax.set_title(label=self.title)

        ax.set_yscale('log')
        ax.set_xscale('log')

        # refresh canvas
        self.canvas.draw()

