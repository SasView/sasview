import copy
import numpy
import pylab

from PyQt4 import QtGui

DEFAULT_CMAP = pylab.cm.jet

import sas.qtgui.PlotUtilities as PlotUtilities
from sas.qtgui.PlotterBase import PlotterBase

class Plotter2D(PlotterBase):
    def __init__(self, parent=None, quickplot=False, dimension=2):
        self.dimension = dimension
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
        self.xLabel="%s(%s)"%(data._xaxis, data._xunit)
        self.yLabel="%s(%s)"%(data._yaxis, data._yunit)
        self.title(title=data.title)

    def plot(self, marker=None, linestyle=None):
        """
        Plot 2D self._data
        """
        # create an axis object
        zmin_2D_temp = self.zmin
        zmax_2D_temp = self.zmax
        if self.scale == 'log_{10}':
            self.scale = 'linear'
            if not self.zmin is None:
                zmin_2D_temp = numpy.pow(10, self.zmin)
            if not self.zmax is None:
                zmax_2D_temp = numpy.pow(10, self.zmax)
        else:
            self.scale = 'log_{10}'
            if not self.zmin is None:
                # min log value: no log(negative)
                if self.zmin <= 0:
                    zmin_2D_temp = -32
                else:
                    zmin_2D_temp = numpy.log10(self.zmin)
            if not self.zmax is None:
                zmax_2D_temp = numpy.log10(self.zmax)

        self.image(data=self.data.data, qx_data=self.qx_data,
                   qy_data=self.qy_data, xmin=self.xmin,
                   xmax=self.xmax,
                   ymin=self.ymin, ymax=self.ymax,
                   cmap=self.cmap, zmin=zmin_2D_temp,
                   zmax=zmax_2D_temp)

    def contextMenuQuickPlot(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        # Actions
        self.contextMenu = QtGui.QMenu(self)
        self.actionSaveImage = self.contextMenu.addAction("Save Image")
        self.actionPrintImage = self.contextMenu.addAction("Print Image")
        self.actionCopyToClipboard = self.contextMenu.addAction("Copy to Clipboard")
        self.contextMenu.addSeparator()
        if self.dimension == 2:
            self.actionToggleGrid = self.contextMenu.addAction("Toggle Grid On/Off")
            self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Toggle Linear/Log Scale")

        # Define the callbacks
        self.actionSaveImage.triggered.connect(self.onImageSave)
        self.actionPrintImage.triggered.connect(self.onImagePrint)
        self.actionCopyToClipboard.triggered.connect(self.onClipboardCopy)
        if self.dimension == 2:
            self.actionToggleGrid.triggered.connect(self.onGridToggle)
        self.actionChangeScale.triggered.connect(self.onToggleScale)

    def onToggleScale(self, event):
        """
        Toggle axis and replot image
        """
        self.plot()

    def image(self, data, qx_data, qy_data, xmin, xmax, ymin, ymax,
              zmin, zmax, color=0, symbol=0, markersize=0,
              label='data2D', cmap=DEFAULT_CMAP):
        """
        Render the current data
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
        if data == None:
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
                    output[output <= 0] = -32
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
        else:
            # clear the previous 2D from memory
            # mpl is not clf, so we do
            self.figure.clear()

            self.figure.subplots_adjust(left=0.1, right=.8, bottom=.1)

            X = self._data.x_bins[0:-1]
            Y = self._data.y_bins[0:-1]
            X, Y = numpy.meshgrid(X, Y)

            try:
                # mpl >= 1.0.0
                ax = self.figure.gca(projection='3d')
                cbax = self.figure.add_axes([0.84, 0.1, 0.02, 0.8])
                if len(X) > 60:
                    ax.disable_mouse_rotation()
            except:
                # mpl < 1.0.0
                try:
                    from mpl_toolkits.mplot3d import Axes3D
                except:
                    logging.error("PlotPanel could not import Axes3D")
                self.figure.clear()
                ax = Axes3D(self.figure)
                if len(X) > 60:
                    ax.cla()
                cbax = None
            self.figure.canvas.resizing = False
            im = ax.plot_surface(X, Y, output, rstride=1, cstride=1, cmap=cmap,
                                 linewidth=0, antialiased=False)
            self.ax.set_axis_off()

        if cbax == None:
            ax.set_frame_on(False)
            cb = self.figure.colorbar(im, shrink=0.8, aspect=20)
        else:
            cb = self.figure.colorbar(im, cax=cbax)
        cb.update_bruteforce(im)
        cb.set_label('$' + self.scale + '$')
        if self.dimension != 3:
            self.figure.canvas.draw_idle()
        else:
            self.figure.canvas.draw()
