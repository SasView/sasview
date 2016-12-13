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
from sas.qtgui.WindowTitle import WindowTitle
import sas.qtgui.PlotHelper as PlotHelper

class PlotterBase(QtGui.QWidget):
    def __init__(self, parent=None, manager=None, quickplot=False):
        super(PlotterBase, self).__init__(parent)

        # Required for the communicator
        self.manager = manager
        self.quickplot = quickplot

        # a figure instance to plot on
        self.figure = plt.figure()

        # Define canvas for the figure to be placed on
        self.canvas = FigureCanvas(self.figure)

        # ... and the toolbar with all the default MPL buttons
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Set the layout and place the canvas widget in it.
        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.canvas)

        # 1D plotter defaults
        self.current_plot = 111
        self._data = [] # Original 1D/2D object
        self._xscale = 'log'
        self._yscale = 'log'
        self.qx_data = []
        self.qy_data = []
        self.color = 0
        self.symbol = 0
        self.grid_on = False
        self.scale = 'linear'
        self.x_label = "log10(x)"
        self.y_label = "log10(y)"

        # Pre-define the Scale properties dialog
        self.properties = ScaleProperties(self,
                                          init_scale_x=self.x_label,
                                          init_scale_y=self.y_label)

        # default color map
        self.cmap = DEFAULT_CMAP

        # Add the axes object -> subplot
        # TODO: self.ax will have to be tracked and exposed
        # to enable subplot specific operations
        self.ax = self.figure.add_subplot(self.current_plot)

        # Set the background color to white
        self.canvas.figure.set_facecolor('#FFFFFF')

        if not quickplot:
            # set the layout
            layout.addWidget(self.toolbar)
            # Add the context menu
            self.contextMenu()
            # Notify PlotHelper about the new plot
            self.upatePlotHelper()
        else:
            self.contextMenuQuickPlot()

        self.setLayout(layout)

    @property
    def data(self):
        """ data getter """
        return self._data

    @data.setter
    def data(self, data=None):
        """ Pure virtual data setter """
        raise NotImplementedError("Data setter must be implemented in derived class.")

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

    def upatePlotHelper(self):
        """
        Notify the plot helper about the new plot
        """
        # Notify the helper
        PlotHelper.addPlot(self)
        # Notify the listeners about a new graph
        self.manager.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())

    def defaultContextMenu(self):
        """
        Content of the dialog-universal context menu:
        Save, Print and Copy
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

    def contextMenu(self):
        """
        Define common context menu and associated actions for the MPL widget
        TODO: move to plotter1d/plotter2d
        """
        raise NotImplementedError("Context menu method must be implemented in derived class.")

    def contextMenuQuickPlot(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        raise NotImplementedError("Context menu method must be implemented in derived class.")

    def contextMenuEvent(self, event):
        """
        Display the context menu
        """
        self.contextMenu.exec_(self.canvas.mapToGlobal(event.pos()))

    def clean(self):
        """
        Redraw the graph
        """
        self.figure.delaxes(self.ax)
        self.ax = self.figure.add_subplot(self.current_plot)

    def plot(self, marker=None, linestyle=None):
        """
        PURE VIRTUAL
        Plot the content of self._data
        """
        raise NotImplementedError("Plot method must be implemented in derived class.")

    def closeEvent(self, event):
        """
        Overwrite the close event adding helper notification
        """
        # Please remove me from your database.
        PlotHelper.deletePlot(PlotHelper.idOfPlot(self))
        # Notify the listeners
        self.manager.communicator.activeGraphsSignal.emit(PlotHelper.currentPlots())
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
        if dialog.exec_() != QtGui.QDialog.Accepted:
            return

        painter = QtGui.QPainter(printer)
        # Grab the widget screenshot
        pmap = QtGui.QPixmap.grabWidget(self)
        # Create a label with pixmap drawn
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

    def onWindowsTitle(self):
        """
        Show a dialog allowing chart title customisation
        """
        current_title = self.windowTitle()
        titleWidget = WindowTitle(self, new_title=current_title)
        result = titleWidget.exec_()
        if result != QtGui.QDialog.Accepted:
            return

        title = titleWidget.title()
        self.setWindowTitle(title)
        # Notify the listeners about a new graph title
        self.manager.communicator.activeGraphName.emit((current_title, title))
