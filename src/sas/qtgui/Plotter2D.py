import copy
import numpy
import pylab

from PyQt4 import QtGui

DEFAULT_CMAP = pylab.cm.jet
from mpl_toolkits.mplot3d import Axes3D

import sas.qtgui.PlotUtilities as PlotUtilities
from sas.qtgui.PlotterBase import PlotterBase
from sas.sasgui.guiframe.dataFitting import Data2D

# Minimum value of Z for which we will present data.
MIN_Z=-32

class Plotter2DWidget(PlotterBase):
    """
    2D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False, dimension=2):
        self.dimension = dimension
        super(Plotter2DWidget, self).__init__(parent, manager=manager, quickplot=quickplot)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data=None):
        """ data setter """
        self._data = data
        self.qx_data = data.qx_data
        self.qy_data = data.qy_data
        self.xmin = data.xmin
        self.xmax = data.xmax
        self.ymin = data.ymin
        self.ymax = data.ymax
        self.zmin = data.zmin
        self.zmax = data.zmax
        self.label = data.name
        self.xLabel = "%s(%s)"%(data._xaxis, data._xunit)
        self.yLabel = "%s(%s)"%(data._yaxis, data._yunit)
        self.title(title=data.title)

    def plot(self, data=None, marker=None, linestyle=None):
        """
        Plot 2D self._data
        """
        # Assing data
        if isinstance(data, Data2D):
            self.data = data

        assert(self._data)

        # Toggle the scale
        zmin_2D_temp = self.zmin
        zmax_2D_temp = self.zmax
        # self.scale predefined in the baseclass
        if self.scale == 'log_{10}':
            self.scale = 'linear'
            if not self.zmin is None:
                zmin_2D_temp = numpy.power(10, self.zmin)
            if not self.zmax is None:
                zmax_2D_temp = numpy.power(10, self.zmax)
        else:
            self.scale = 'log_{10}'
            if not self.zmin is None:
                # min log value: no log(negative)
                if self.zmin <= 0:
                    zmin_2D_temp = MIN_Z
                else:
                    zmin_2D_temp = numpy.log10(self.zmin)
            if not self.zmax is None:
                zmax_2D_temp = numpy.log10(self.zmax)

        # Prepare and show the plot
        self.showPlot(data=self.data.data,
                      qx_data=self.qx_data,
                      qy_data=self.qy_data,
                      xmin=self.xmin,
                      xmax=self.xmax,
                      ymin=self.ymin, ymax=self.ymax,
                      cmap=self.cmap, zmin=zmin_2D_temp,
                      zmax=zmax_2D_temp)

    def contextMenu(self):
        """
        Define common context menu and associated actions for the MPL widget
        """
        self.defaultContextMenu()

    def contextMenuQuickPlot(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        self.defaultContextMenu()

        if self.dimension == 2:
            self.actionToggleGrid = self.contextMenu.addAction("Toggle Grid On/Off")
            self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Toggle Linear/Log Scale")

        # Define the callbacks
        self.actionChangeScale.triggered.connect(self.onToggleScale)
        if self.dimension == 2:
            self.actionToggleGrid.triggered.connect(self.onGridToggle)

    def onToggleScale(self, event):
        """
        Toggle axis and replot image
        """
        self.plot()

    def showPlot(self, data, qx_data, qy_data, xmin, xmax, ymin, ymax,
                 zmin, zmax, color=0, symbol=0, markersize=0,
                 label='data2D', cmap=DEFAULT_CMAP):
        """
        Render and show the current data
        """
        self.qx_data = qx_data
        self.qy_data = qy_data
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax
        self.zmin = zmin
        self.zmax = zmax
        # If we don't have any data, skip.
        if data is None:
            return
        if data.ndim == 1:
            output = PlotUtilities.build_matrix(data, self.qx_data, self.qy_data)
        else:
            output = copy.deepcopy(data)

        zmin_temp = self.zmin
        # check scale
        if self.scale == 'log_{10}':
            try:
                if  self.zmin <= 0  and len(output[output > 0]) > 0:
                    zmin_temp = self.zmin_2D
                    output[output > 0] = numpy.log10(output[output > 0])
                elif self.zmin <= 0:
                    zmin_temp = self.zmin
                    output[output > 0] = numpy.zeros(len(output))
                    output[output <= 0] = MIN_Z
                else:
                    zmin_temp = self.zmin
                    output[output > 0] = numpy.log10(output[output > 0])
            except:
                #Too many problems in 2D plot with scale
                output[output > 0] = numpy.log10(output[output > 0])
                pass

        self.cmap = cmap
        if self.dimension != 3:
            #Re-adjust colorbar
            self.figure.subplots_adjust(left=0.2, right=.8, bottom=.2)

            im = self.ax.imshow(output, interpolation='nearest',
                                origin='lower',
                                vmin=zmin_temp, vmax=self.zmax,
                                cmap=self.cmap,
                                extent=(self.xmin, self.xmax,
                                        self.ymin, self.ymax))

            cbax = self.figure.add_axes([0.84, 0.2, 0.02, 0.7])

            # Current labels for axes
            self.ax.set_ylabel(self.y_label)
            self.ax.set_xlabel(self.x_label)

            # Title only for regular charts
            if not self.quickplot:
                self.ax.set_title(label=self._title)

            if cbax is None:
                ax.set_frame_on(False)
                cb = self.figure.colorbar(im, shrink=0.8, aspect=20)
            else:
                cb = self.figure.colorbar(im, cax=cbax)

            cb.update_bruteforce(im)
            cb.set_label('$' + self.scale + '$')

        else:
            # clear the previous 2D from memory
            self.figure.clear()

            self.figure.subplots_adjust(left=0.1, right=.8, bottom=.1)

            X = self._data.x_bins[0:-1]
            Y = self._data.y_bins[0:-1]
            X, Y = numpy.meshgrid(X, Y)

            ax = Axes3D(self.figure)
            #cbax = self.figure.add_axes([0.84, 0.1, 0.02, 0.8])

            # Disable rotation for large sets.
            # TODO: Define "large" for a dataset
            SET_TOO_LARGE = 500
            if len(X) > SET_TOO_LARGE:
                ax.disable_mouse_rotation()

            self.figure.canvas.resizing = False
            im = ax.plot_surface(X, Y, output, rstride=1, cstride=1, cmap=cmap,
                                 linewidth=0, antialiased=False)
            self.ax.set_axis_off()

        if self.dimension != 3:
            self.figure.canvas.draw_idle()
        else:
            self.figure.canvas.draw()

class Plotter2D(QtGui.QDialog, Plotter2DWidget):
    def __init__(self, parent=None, quickplot=False, dimension=2):

        QtGui.QDialog.__init__(self)
        Plotter2DWidget.__init__(self, manager=parent, quickplot=quickplot, dimension=dimension)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/ball.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
