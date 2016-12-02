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
from sas.qtgui.PlotterBase import PlotterBase

class Plotter2D(PlotterBase):
    def __init__(self, parent=None, quickplot=False):
        super(Plotter2D, self).__init__(parent, quickplot=quickplot)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data=None):
        """ data setter """
        self._data = data
        self.qx_data=data.qx_data
        self.qy_data=data.qy_data
        self.xmin=data.xmin
        self.xmax=data.xmax
        self.ymin=data.ymin
        self.ymax=data.ymax
        self.zmin=data.zmin
        self.zmax=data.zmax
        self.label=data.name
        self.xLabel(xlabel="%s(%s)"%(data._xaxis, data._xunit))
        self.yLabel(ylabel="%s(%s)"%(data._yaxis, data._yunit))
        self.title(title=data.title)

    def plot(self, marker=None, linestyle=None):
        """
        Plot 2D self._data
        """
        # create an axis object
        ax = self.ax

        # graph properties
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        # Title only for regular charts
        if not self.quickplot:
            ax.set_title(label=self.title)

        # Re-adjust colorbar
        self.figure.subplots_adjust(left=0.2, right=.8, bottom=.2)

        output = PlotUtilities.build_matrix(self._data.data, self.qx_data, self.qy_data)

        im = ax.imshow(output,
                       interpolation='nearest',
                       origin='lower',
                       vmin=self.zmin, vmax=self.zmax,
                       cmap=self.cmap,
                       extent=(self.xmin, self.xmax,
                               self.ymin, self.ymax))

        cbax = self.figure.add_axes([0.84, 0.2, 0.02, 0.7])
        cb = self.figure.colorbar(im, cax=cbax)
        cb.update_bruteforce(im)
        cb.set_label('$' + self._scale + '$')

        # Schedule the draw for the next time the event loop is idle.
        self.canvas.draw_idle()
