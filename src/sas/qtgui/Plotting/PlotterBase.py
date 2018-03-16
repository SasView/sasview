import pylab
import numpy

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets, QtPrintSupport

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import matplotlib.pyplot as plt

DEFAULT_CMAP = pylab.cm.jet
from sas.qtgui.Plotting.Binder import BindArtist
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

from sas.qtgui.Plotting.ScaleProperties import ScaleProperties
from sas.qtgui.Plotting.WindowTitle import WindowTitle
import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Plotting.PlotHelper as PlotHelper
import sas.qtgui.Plotting.PlotUtilities as PlotUtilities

class PlotterBase(QtWidgets.QWidget):
    def __init__(self, parent=None, manager=None, quickplot=False):
        super(PlotterBase, self).__init__(parent)

        # Required for the communicator
        self.manager = manager
        self.quickplot = quickplot

        #plt.style.use('ggplot')
        #plt.style.use('seaborn-darkgrid')

        # a figure instance to plot on
        self.figure = plt.figure()

        # Define canvas for the figure to be placed on
        self.canvas = FigureCanvas(self.figure)

        # ... and the toolbar with all the default MPL buttons
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Simple window for data display
        self.txt_widget = QtWidgets.QTextEdit(None)

        # Set the layout and place the canvas widget in it.
        layout = QtWidgets.QVBoxLayout()
        # FIXME setMargin -> setContentsMargins in qt5 with 4 args
        #layout.setContentsMargins(0)
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

        # Mouse click related
        self._scale_xlo = None
        self._scale_xhi = None
        self._scale_ylo = None
        self._scale_yhi = None
        self.x_click = None
        self.y_click = None
        self.event_pos = None
        self.leftdown = False
        self.gotLegend = 0

        # Annotations
        self.selectedText = None
        self.textList = []

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

        # Remove this, DAMMIT
        self.axes = [self.ax]

        # Set the background color to white
        self.canvas.figure.set_facecolor('#FFFFFF')

        # Canvas event handlers
        self.canvas.mpl_connect('button_release_event', self.onMplMouseUp)
        self.canvas.mpl_connect('button_press_event', self.onMplMouseDown)
        self.canvas.mpl_connect('motion_notify_event', self.onMplMouseMotion)
        self.canvas.mpl_connect('pick_event', self.onMplPick)
        self.canvas.mpl_connect('scroll_event', self.onMplWheel)

        self.contextMenu = QtWidgets.QMenu(self)

        if not quickplot:
            # Add the toolbar
            layout.addWidget(self.toolbar)
            # Notify PlotHelper about the new plot
            self.upatePlotHelper()

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
        # Set the object name to satisfy the Squish object picker
        self.canvas.setObjectName(title)

    @property
    def xLabel(self, xlabel=""):
        """ x-label setter """
        return self.x_label

    @xLabel.setter
    def xLabel(self, xlabel=""):
        """ x-label setter """
        self.x_label = r'$%s$'% xlabel if xlabel else ""

    @property
    def yLabel(self, ylabel=""):
        """ y-label setter """
        return self.y_label

    @yLabel.setter
    def yLabel(self, ylabel=""):
        """ y-label setter """
        self.y_label = r'$%s$'% ylabel if ylabel else ""

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
        self.ax.cla()
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
        self.contextMenu.clear()
        self.actionSaveImage = self.contextMenu.addAction("Save Image")
        self.actionPrintImage = self.contextMenu.addAction("Print Image")
        self.actionCopyToClipboard = self.contextMenu.addAction("Copy to Clipboard")
        self.contextMenu.addSeparator()

        # Define the callbacks
        self.actionSaveImage.triggered.connect(self.onImageSave)
        self.actionPrintImage.triggered.connect(self.onImagePrint)
        self.actionCopyToClipboard.triggered.connect(self.onClipboardCopy)

    def createContextMenu(self):
        """
        Define common context menu and associated actions for the MPL widget
        """
        raise NotImplementedError("Context menu method must be implemented in derived class.")

    def createContextMenuQuick(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        raise NotImplementedError("Context menu method must be implemented in derived class.")

    def contextMenuEvent(self, event):
        """
        Display the context menu
        """
        if not self.quickplot:
            self.createContextMenu()
        else:
            self.createContextMenuQuick()

        event_pos = event.pos()
        self.contextMenu.exec_(self.canvas.mapToGlobal(event_pos))

    def onMplMouseUp(self, event):
        """
        Mouse button up callback
        """
        pass

    def onMplMouseDown(self, event):
        """
        Mouse button down callback
        """
        pass

    def onMplMouseMotion(self, event):
        """
        Mouse motion callback
        """
        pass

    def onMplPick(self, event):
        """
        Mouse pick callback
        """
        pass

    def onMplWheel(self, event):
        """
        Mouse wheel scroll callback
        """
        pass

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
        printer = QtPrintSupport.QPrinter()

        # Display the print dialog
        dialog = QtPrintSupport.QPrintDialog(printer)
        dialog.setModal(True)
        dialog.setWindowTitle("Print")
        if dialog.exec_() != QtWidgets.QDialog.Accepted:
            return

        painter = QtGui.QPainter(printer)
        # Grab the widget screenshot
        pmap = QtGui.QPixmap(self.size())
        self.render(pmap)
        # Create a label with pixmap drawn
        printLabel = QtWidgets.QLabel()
        printLabel.setPixmap(pmap)

        # Print the label
        printLabel.render(painter)
        painter.end()

    def onClipboardCopy(self):
        """
        Copy MPL widget area to buffer
        """
        bmp = QtWidgets.QApplication.clipboard()
        pixmap = QtGui.QPixmap(self.canvas.size())
        self.canvas.render(pixmap)
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
        if result != QtWidgets.QDialog.Accepted:
            return

        title = titleWidget.title()
        self.setWindowTitle(title)
        # Notify the listeners about a new graph title
        self.manager.communicator.activeGraphName.emit((current_title, title))

    def offset_graph(self):
        """
        Zoom and offset the graph to the last known settings
        """
        for ax in self.axes:
            if self._scale_xhi is not None and self._scale_xlo is not None:
                ax.set_xlim(self._scale_xlo, self._scale_xhi)
            if self._scale_yhi is not None and self._scale_ylo is not None:
                ax.set_ylim(self._scale_ylo, self._scale_yhi)

    def onDataInfo(self, plot_data):
        """
        Displays data info text window for the selected plot
        """
        if isinstance(plot_data, Data1D):
            text_to_show = GuiUtils.retrieveData1d(plot_data)
        else:
            text_to_show = GuiUtils.retrieveData2d(plot_data)
        # Hardcoded sizes to enable full width rendering with default font
        self.txt_widget.resize(420,600)

        self.txt_widget.setReadOnly(True)
        self.txt_widget.setWindowFlags(QtCore.Qt.Window)
        self.txt_widget.setWindowIcon(QtGui.QIcon(":/res/ball.ico"))
        self.txt_widget.setWindowTitle("Data Info: %s" % plot_data.filename)
        self.txt_widget.insertPlainText(text_to_show)

        self.txt_widget.show()
        # Move the slider all the way up, if present
        vertical_scroll_bar = self.txt_widget.verticalScrollBar()
        vertical_scroll_bar.triggerAction(QtWidgets.QScrollBar.SliderToMinimum)

    def onSavePoints(self, plot_data):
        """
        Saves plot data to a file
        """
        if isinstance(plot_data, Data1D):
            GuiUtils.saveData1D(plot_data)
        else:
            GuiUtils.saveData2D(plot_data)
