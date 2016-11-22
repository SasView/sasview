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

import PlotHelper

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

        # default color map
        self._cmap = DEFAULT_CMAP

        self._ax = self.figure.add_subplot(self._current_plot)

        # Notify the helper
        PlotHelper.addPlot(self)
        # Notify the listeners
        self.parent.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())

    def data(self, data=None):
        """ data setter """
        self._data = data.data
        self._qx_data=data.qx_data
        self._qy_data=data.qy_data
        self._xmin=data.xmin
        self._xmax=data.xmax
        self._ymin=data.ymin
        self._ymax=data.ymax
        self._zmin=data.zmin
        self._zmax=data.zmax
        self._color=0
        self._symbol=0
        self._label=data.name
        self._scale = 'linear'

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

        output = self._build_matrix()

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

    def _build_matrix(self):
        """
        Build a matrix for 2d plot from a vector
        Returns a matrix (image) with ~ square binning
        Requirement: need 1d array formats of
        self.data, self._qx_data, and self._qy_data
        where each one corresponds to z, x, or y axis values

        """
        # No qx or qy given in a vector format
        if self._qx_data == None or self._qy_data == None \
                or self._qx_data.ndim != 1 or self._qy_data.ndim != 1:
            # do we need deepcopy here?
            return self._data

        # maximum # of loops to fillup_pixels
        # otherwise, loop could never stop depending on data
        max_loop = 1
        # get the x and y_bin arrays.
        self._get_bins()
        # set zero to None

        #Note: Can not use scipy.interpolate.Rbf:
        # 'cause too many data points (>10000)<=JHC.
        # 1d array to use for weighting the data point averaging
        #when they fall into a same bin.
        weights_data = numpy.ones([self._data.size])
        # get histogram of ones w/len(data); this will provide
        #the weights of data on each bins
        weights, xedges, yedges = numpy.histogram2d(x=self._qy_data,
                                                    y=self._qx_data,
                                                    bins=[self.y_bins, self.x_bins],
                                                    weights=weights_data)
        # get histogram of data, all points into a bin in a way of summing
        image, xedges, yedges = numpy.histogram2d(x=self._qy_data,
                                                  y=self._qx_data,
                                                  bins=[self.y_bins, self.x_bins],
                                                  weights=self._data)
        # Now, normalize the image by weights only for weights>1:
        # If weight == 1, there is only one data point in the bin so
        # that no normalization is required.
        image[weights > 1] = image[weights > 1] / weights[weights > 1]
        # Set image bins w/o a data point (weight==0) as None (was set to zero
        # by histogram2d.)
        image[weights == 0] = None

        # Fill empty bins with 8 nearest neighbors only when at least
        #one None point exists
        loop = 0

        # do while loop until all vacant bins are filled up up
        #to loop = max_loop
        while not(numpy.isfinite(image[weights == 0])).all():
            if loop >= max_loop:  # this protects never-ending loop
                break
            image = self._fillup_pixels(image=image, weights=weights)
            loop += 1

        return image

    def _get_bins(self):
        """
        get bins
        set x_bins and y_bins into self, 1d arrays of the index with
        ~ square binning
        Requirement: need 1d array formats of
        self._qx_data, and self._qy_data
        where each one corresponds to  x, or y axis values
        """
        # No qx or qy given in a vector format
        if self._qx_data == None or self._qy_data == None \
                or self._qx_data.ndim != 1 or self._qy_data.ndim != 1:
            return self._data

        # find max and min values of qx and qy
        xmax = self._qx_data.max()
        xmin = self._qx_data.min()
        ymax = self._qy_data.max()
        ymin = self._qy_data.min()

        # calculate the range of qx and qy: this way, it is a little
        # more independent
        x_size = xmax - xmin
        y_size = ymax - ymin

        # estimate the # of pixels on each axes
        npix_y = int(numpy.floor(numpy.sqrt(len(self._qy_data))))
        npix_x = int(numpy.floor(len(self._qy_data) / npix_y))

        # bin size: x- & y-directions
        xstep = x_size / (npix_x - 1)
        ystep = y_size / (npix_y - 1)

        # max and min taking account of the bin sizes
        xmax = xmax + xstep / 2.0
        xmin = xmin - xstep / 2.0
        ymax = ymax + ystep / 2.0
        ymin = ymin - ystep / 2.0

        # store x and y bin centers in q space
        x_bins = numpy.linspace(xmin, xmax, npix_x)
        y_bins = numpy.linspace(ymin, ymax, npix_y)

        #set x_bins and y_bins
        self.x_bins = x_bins
        self.y_bins = y_bins

    def _fillup_pixels(self, image=None, weights=None):
        """
        Fill z values of the empty cells of 2d image matrix
        with the average over up-to next nearest neighbor points

        :param image: (2d matrix with some zi = None)

        :return: image (2d array )

        :TODO: Find better way to do for-loop below

        """
        # No image matrix given
        if image == None or numpy.ndim(image) != 2 \
                or numpy.isfinite(image).all() \
                or weights == None:
            return image
        # Get bin size in y and x directions
        len_y = len(image)
        len_x = len(image[1])
        temp_image = numpy.zeros([len_y, len_x])
        weit = numpy.zeros([len_y, len_x])
        # do for-loop for all pixels
        for n_y in range(len(image)):
            for n_x in range(len(image[1])):
                # find only null pixels
                if weights[n_y][n_x] > 0 or numpy.isfinite(image[n_y][n_x]):
                    continue
                else:
                    # find 4 nearest neighbors
                    # check where or not it is at the corner
                    if n_y != 0 and numpy.isfinite(image[n_y - 1][n_x]):
                        temp_image[n_y][n_x] += image[n_y - 1][n_x]
                        weit[n_y][n_x] += 1
                    if n_x != 0 and numpy.isfinite(image[n_y][n_x - 1]):
                        temp_image[n_y][n_x] += image[n_y][n_x - 1]
                        weit[n_y][n_x] += 1
                    if n_y != len_y - 1 and numpy.isfinite(image[n_y + 1][n_x]):
                        temp_image[n_y][n_x] += image[n_y + 1][n_x]
                        weit[n_y][n_x] += 1
                    if n_x != len_x - 1 and numpy.isfinite(image[n_y][n_x + 1]):
                        temp_image[n_y][n_x] += image[n_y][n_x + 1]
                        weit[n_y][n_x] += 1
                    # go 4 next nearest neighbors when no non-zero
                    # neighbor exists
                    if n_y != 0 and n_x != 0 and\
                         numpy.isfinite(image[n_y - 1][n_x - 1]):
                        temp_image[n_y][n_x] += image[n_y - 1][n_x - 1]
                        weit[n_y][n_x] += 1
                    if n_y != len_y - 1 and n_x != 0 and \
                        numpy.isfinite(image[n_y + 1][n_x - 1]):
                        temp_image[n_y][n_x] += image[n_y + 1][n_x - 1]
                        weit[n_y][n_x] += 1
                    if n_y != len_y and n_x != len_x - 1 and \
                        numpy.isfinite(image[n_y - 1][n_x + 1]):
                        temp_image[n_y][n_x] += image[n_y - 1][n_x + 1]
                        weit[n_y][n_x] += 1
                    if n_y != len_y - 1 and n_x != len_x - 1 and \
                        numpy.isfinite(image[n_y + 1][n_x + 1]):
                        temp_image[n_y][n_x] += image[n_y + 1][n_x + 1]
                        weit[n_y][n_x] += 1

        # get it normalized
        ind = (weit > 0)
        image[ind] = temp_image[ind] / weit[ind]

        return image
