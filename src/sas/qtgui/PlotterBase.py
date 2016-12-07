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
        layout.setMargin(0)
        layout.addWidget(self.canvas)

        # defaults
        self.current_plot = 111
        self._data = [] # Original 1D/2D object
        self._xscale = 'log'
        self._yscale = 'log'
        self.qx_data = []
        self.qy_data = []
        self.color=0
        self.symbol=0
        self.grid_on = False
        self.scale = 'linear'
        self.x_label = "log10(x)"
        self.y_label = "log10(y)"

        # default color map
        self.cmap = DEFAULT_CMAP

        self.ax = self.figure.add_subplot(self.current_plot)
        self.canvas.figure.set_facecolor('#FFFFFF')

        if not quickplot:
            # set the layout
            layout.addWidget(self.toolbar)
            # Notify the helper
            PlotHelper.addPlot(self)
            # Add the context menu
            self.contextMenu()
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
        """ virtual data setter """
        raise ImportError("Data setter must be implemented in derived class.")

    def title(self, title=""):
        """ title setter """
        self._title = title

    @property
    def xLabel(self, xlabel=""):
        """ x-label setter """
        return self.x_label

    @xLabel.setter
    def xLabel(self, xlabel=""):
        """ x-label setter """
        self.x_label = r'$%s$'% xlabel

    @property
    def yLabel(self, ylabel=""):
        """ y-label setter """
        return self.y_label

    @yLabel.setter
    def yLabel(self, ylabel=""):
        """ y-label setter """
        self.y_label = r'$%s$'% ylabel

    @property
    def yscale(self):
        """ Y-axis scale getter """
        return self._yscale

    @yscale.setter
    def yscale(self, scale='linear'):
        """ Y-axis scale setter """
        self.ax.set_yscale(scale, nonposy='clip')
        self._yscale = scale

    @property
    def xscale(self):
        """ X-axis scale getter """
        return self._xscale

    @xscale.setter
    def xscale(self, scale='linear'):
        """ X-axis scale setter """
        self.ax.set_xscale(scale)
        self._xscale = scale

    def contextMenu(self):
        """
        Define context menu and associated actions for the MPL widget
        """
        # Actions
        self.contextMenu = QtGui.QMenu(self)
        self.actionSaveImage = self.contextMenu.addAction("Save Image")
        self.actionPrintImage = self.contextMenu.addAction("Print Image")
        self.actionCopyToClipboard = self.contextMenu.addAction("Copy to Clipboard")
        self.contextMenu.addSeparator()

        # Define the callbacks
        self.actionSaveImage.triggered.connect(self.onImageSave)
        self.actionPrintImage.triggered.connect(self.onImagePrint)
        self.actionCopyToClipboard.triggered.connect(self.onClipboardCopy)

    def contextMenuQuickPlot(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        raise ImportError("Context menu method must be implemented in derived class.")

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
