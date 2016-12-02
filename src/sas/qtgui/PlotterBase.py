import logging
import copy
import numpy
import pylab

from PyQt4 import QtGui
from PyQt4 import QtCore

# TODO: Replace the qt4agg calls below with qt5 equivalent.
# Requires some code modifications.
# https://www.boxcontrol.net/embedding-matplotlib-plot-on-pyqt5-gui.html
#
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.backend_bases import NavigationToolbar2

import matplotlib.pyplot as plt

DEFAULT_CMAP = pylab.cm.jet
from sas.qtgui.ScaleProperties import ScaleProperties
import sas.qtgui.PlotUtilities as PlotUtilities
import sas.qtgui.PlotHelper as PlotHelper

class PlotterBase(QtGui.QDialog):
    def __init__(self, parent=None, quickplot=False):
        super(PlotterBase, self).__init__(parent)

        # Required for the communicator
        self.parent = parent
        self.quickplot = quickplot

        # a figure instance to plot on
        self.figure = plt.figure()

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.properties = ScaleProperties(self)

        # set the layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)

        # defaults
        self.current_plot = 111
        self._data = []
        self.qx_data = []
        self.qy_data = []
        self.color=0
        self.symbol=0
        self.grid_on = False
        self.scale = 'linear'

        # default color map
        self.cmap = DEFAULT_CMAP

        self.ax = self.figure.add_subplot(self.current_plot)
        self.canvas.figure.set_facecolor('#FFFFFF')

        if not quickplot:
            layout.addWidget(self.toolbar)
            # Notify the helper
            PlotHelper.addPlot(self)
            # Notify the listeners
            self.parent.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())
        else:
            self.contextMenuQuickPlot()

        self.setLayout(layout)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data=None):
        """ data setter """
        pass

    def title(self, title=""):
        """ title setter """
        self.title = title

    def id(self, id=""):
        """ id setter """
        self.id = id

    def xLabel(self, xlabel=""):
        """ x-label setter """
        self.x_label = r'$%s$'% xlabel

    def yLabel(self, ylabel=""):
        """ y-label setter """
        self.y_label = r'$%s$'% ylabel

    @property
    def yscale(self):
        """ Y-axis scale getter """
        return self.yscale

    @yscale.setter
    def yscale(self, scale='linear'):
        """ Y-axis scale setter """
        self.subplot.set_yscale(scale, nonposy='clip')
        self.yscale = scale

    @property
    def xscale(self):
        """ X-axis scale getter """
        return self.xscale

    @xscale.setter
    def xscale(self, scale='linear'):
        """ X-axis scale setter """
        self.subplot.set_xscale(scale)
        self.xscale = scale

    def contextMenuQuickPlot(self):
        """
        Define context menu and associated actions for the MPL widget
        """
        # Actions
        self.contextMenu = QtGui.QMenu(self)
        self.actionSaveImage = self.contextMenu.addAction("Save Image")
        self.actionPrintImage = self.contextMenu.addAction("Print Image")
        self.actionCopyToClipboard = self.contextMenu.addAction("Copy to Clipboard")
        self.contextMenu.addSeparator()
        self.actionToggleGrid = self.contextMenu.addAction("Toggle Grid On/Off")
        self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Change Scale")

        # Define the callbacks
        self.actionSaveImage.triggered.connect(self.onImageSave)
        self.actionPrintImage.triggered.connect(self.onImagePrint)
        self.actionCopyToClipboard.triggered.connect(self.onClipboardCopy)
        self.actionToggleGrid.triggered.connect(self.onGridToggle)
        self.actionChangeScale.triggered.connect(self.onScaleChange)

    def contextMenuEvent(self, event):
        """
        Display the context menu
        """
        self.contextMenu.exec_( self.canvas.mapToGlobal(event.pos()) )

    def clean(self):
        """
        Redraw the graph
        """
        self.figure.delaxes(self.ax)
        self.ax = self.figure.add_subplot(self.current_plot)

    def plot(self, marker=None, linestyle=None):
        """
        VIRTUAL
        Plot the content of self._data
        """
        raise ImportError("Plot method must be implemented in derived class.")

    def closeEvent(self, event):
        """
        Overwrite the close event adding helper notification
        """
        # Please remove me from your database.
        PlotHelper.deletePlot(PlotHelper.idOfPlot(self))
        # Notify the listeners
        self.parent.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())
        event.accept()

    def onImageSave(self):
        """
        Use the internal MPL method for saving to file
        """
        self.toolbar.save_figure()

    def onImagePrint(self):
        """
        Display printer dialog and print the MPL widget area
        """
        # Define the printer
        printer = QtGui.QPrinter()

        # Display the print dialog
        dialog = QtGui.QPrintDialog(printer)
        dialog.setModal(True)
        dialog.setWindowTitle("Print")
        if(dialog.exec_() != QtGui.QDialog.Accepted):
            return

        painter = QtGui.QPainter(printer)
        # Create a label with pixmap drawn
        pmap = QtGui.QPixmap.grabWidget(self)
        printLabel = QtGui.QLabel()
        printLabel.setPixmap(pmap)

        # Print the label
        printLabel.render(painter)
        painter.end()

    def onClipboardCopy(self):
        """
        Copy MPL widget area to buffer
        """
        bmp = QtGui.QApplication.clipboard()
        pixmap = QtGui.QPixmap.grabWidget(self.canvas)
        bmp.setPixmap(pixmap)

    def onGridToggle(self):
        """
        Add/remove grid lines from MPL plot
        """
        self.grid_on = (not self.grid_on)
        self.ax.grid(self.grid_on)
        self.canvas.draw_idle()

    def onScaleChange(self):
        """
        Show a dialog allowing axes rescaling
        """
        if self.properties.exec_() == QtGui.QDialog.Accepted:
            xLabel, yLabel = self.properties.getValues()
            #self.xyTransform(xLabel, yLabel)

    def xyTransform(self, xLabel="", yLabel=""):
        """
        Transforms x and y in View and set the scale
        """
        # The logic should be in the right order
        self.ly = None
        self.q_ctrl = None
        # Changing the scale might be incompatible with
        # currently displayed data (for instance, going
        # from ln to log when all plotted values have
        # negative natural logs).
        # Go linear and only change the scale at the end.
        self.set_xscale("linear")
        self.set_yscale("linear")
        _xscale = 'linear'
        _yscale = 'linear'
        # Local data is either 1D or 2D
        #for item in list:
        #if item.id == 'fit':
        #    continue
        item.setLabel(self.xLabel, self.yLabel)
        # control axis labels from the panel itself
        yname, yunits = item.get_yaxis()
        if self.yaxis_label != None:
            yname = self.yaxis_label
            yunits = self.yaxis_unit
        else:
            self.yaxis_label = yname
            self.yaxis_unit = yunits
        xname, xunits = item.get_xaxis()
        if self.xaxis_label != None:
            xname = self.xaxis_label
            xunits = self.xaxis_unit
        else:
            self.xaxis_label = xname
            self.xaxis_unit = xunits
        # Goes through all possible scales
        if self.xLabel == "x":
            item.transformX(transform.toX, transform.errToX)
            self.graph._xaxis_transformed("%s" % xname, "%s" % xunits)
        if self.xLabel == "x^(2)":
            item.transformX(transform.toX2, transform.errToX2)
            xunits = convert_unit(2, xunits)
            self.graph._xaxis_transformed("%s^{2}" % xname, "%s" % xunits)
        if self.xLabel == "x^(4)":
            item.transformX(transform.toX4, transform.errToX4)
            xunits = convert_unit(4, xunits)
            self.graph._xaxis_transformed("%s^{4}" % xname, "%s" % xunits)
        if self.xLabel == "ln(x)":
            item.transformX(transform.toLogX, transform.errToLogX)
            self.graph._xaxis_transformed("\ln{(%s)}" % xname, "%s" % xunits)
        if self.xLabel == "log10(x)":
            item.transformX(transform.toX_pos, transform.errToX_pos)
            _xscale = 'log'
            self.graph._xaxis_transformed("%s" % xname, "%s" % xunits)
        if self.xLabel == "log10(x^(4))":
            item.transformX(transform.toX4, transform.errToX4)
            xunits = convert_unit(4, xunits)
            self.graph._xaxis_transformed("%s^{4}" % xname, "%s" % xunits)
            _xscale = 'log'
        if self.yLabel == "ln(y)":
            item.transformY(transform.toLogX, transform.errToLogX)
            self.graph._yaxis_transformed("\ln{(%s)}" % yname, "%s" % yunits)
        if self.yLabel == "y":
            item.transformY(transform.toX, transform.errToX)
            self.graph._yaxis_transformed("%s" % yname, "%s" % yunits)
        if self.yLabel == "log10(y)":
            item.transformY(transform.toX_pos, transform.errToX_pos)
            _yscale = 'log'
            self.graph._yaxis_transformed("%s" % yname, "%s" % yunits)
        if self.yLabel == "y^(2)":
            item.transformY(transform.toX2, transform.errToX2)
            yunits = convert_unit(2, yunits)
            self.graph._yaxis_transformed("%s^{2}" % yname, "%s" % yunits)
        if self.yLabel == "1/y":
            item.transformY(transform.toOneOverX, transform.errOneOverX)
            yunits = convert_unit(-1, yunits)
            self.graph._yaxis_transformed("1/%s" % yname, "%s" % yunits)
        if self.yLabel == "y*x^(2)":
            item.transformY(transform.toYX2, transform.errToYX2)
            xunits = convert_unit(2, self.xaxis_unit)
            self.graph._yaxis_transformed("%s \ \ %s^{2}" % (yname, xname),
                                            "%s%s" % (yunits, xunits))
        if self.yLabel == "y*x^(4)":
            item.transformY(transform.toYX4, transform.errToYX4)
            xunits = convert_unit(4, self.xaxis_unit)
            self.graph._yaxis_transformed("%s \ \ %s^{4}" % (yname, xname),
                                            "%s%s" % (yunits, xunits))
        if self.yLabel == "1/sqrt(y)":
            item.transformY(transform.toOneOverSqrtX,
                            transform.errOneOverSqrtX)
            yunits = convert_unit(-0.5, yunits)
            self.graph._yaxis_transformed("1/\sqrt{%s}" % yname,
                                            "%s" % yunits)
        if self.yLabel == "ln(y*x)":
            item.transformY(transform.toLogXY, transform.errToLogXY)
            self.graph._yaxis_transformed("\ln{(%s \ \ %s)}" % (yname, xname),
                                            "%s%s" % (yunits, self.xaxis_unit))
        if self.yLabel == "ln(y*x^(2))":
            item.transformY(transform.toLogYX2, transform.errToLogYX2)
            xunits = convert_unit(2, self.xaxis_unit)
            self.graph._yaxis_transformed("\ln (%s \ \ %s^{2})" % (yname, xname),
                                            "%s%s" % (yunits, xunits))
        if self.yLabel == "ln(y*x^(4))":
            item.transformY(transform.toLogYX4, transform.errToLogYX4)
            xunits = convert_unit(4, self.xaxis_unit)
            self.graph._yaxis_transformed("\ln (%s \ \ %s^{4})" % (yname, xname),
                                            "%s%s" % (yunits, xunits))
        if self.yLabel == "log10(y*x^(4))":
            item.transformY(transform.toYX4, transform.errToYX4)
            xunits = convert_unit(4, self.xaxis_unit)
            _yscale = 'log'
            self.graph._yaxis_transformed("%s \ \ %s^{4}" % (yname, xname),
                                            "%s%s" % (yunits, xunits))
            item.transformView()

        # set new label and units
        yname = self.graph.prop["ylabel"]
        yunits = ''
        xname = self.graph.prop["xlabel"]
        xunits = ''

        self.resetFitView()
        self.prevXtrans = self.xLabel
        self.prevYtrans = self.yLabel
        self.graph.render(self)
        self.set_xscale(_xscale)
        self.set_yscale(_yscale)

        self.xaxis(xname, xunits, self.xaxis_font,
                   self.xaxis_color, self.xaxis_tick)
        self.yaxis(yname, yunits, self.yaxis_font,
                   self.yaxis_color, self.yaxis_tick)
        self.subplot.texts = self.textList

        self.canvas.draw_idle()
