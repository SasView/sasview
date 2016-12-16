import pylab
import numpy

from PyQt4 import QtGui

# TODO: Replace the qt4agg calls below with qt5 equivalent.
# Requires some code modifications.
# https://www.boxcontrol.net/embedding-matplotlib-plot-on-pyqt5-gui.html
#
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar

import matplotlib.pyplot as plt

DEFAULT_CMAP = pylab.cm.jet
from sas.sasgui.plottools.binder import BindArtist

from sas.qtgui.ScaleProperties import ScaleProperties
from sas.qtgui.WindowTitle import WindowTitle
import sas.qtgui.PlotHelper as PlotHelper
import sas.qtgui.PlotUtilities as PlotUtilities

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

        # Mouse click related
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
        event_pos = event.pos()
        self.contextMenu.exec_(self.canvas.mapToGlobal(event_pos))

    def onMplMouseDown(self, event):
        """
        Left button down and ready to drag
        """
        # Check that the LEFT button was pressed
        if event.button == 1:
            self.leftdown = True
            ax = event.inaxes
            for text in self.textList:
                if text.contains(event)[0]: # If user has clicked on text
                    self.selectedText = text
                    return

            if ax != None:
                self.xInit, self.yInit = event.xdata, event.ydata
                try:
                    self.x_click = float(event.xdata)  # / size_x
                    self.y_click = float(event.ydata)  # / size_y
                except:
                    self.position = None

    def onMplMouseUp(self, event):
        """
        Set the data coordinates of the click
        """
        self.x_click = event.xdata
        self.y_click = event.ydata

        # Check that the LEFT button was released
        if event.button == 1:
            self.leftdown = False
            #self.leftup = True
            self.selectedText = None

        #release the legend
        if self.gotLegend == 1:
            self.gotLegend = 0

    def onMplMouseMotion(self, event):
        """
        Check if the left button is press and the mouse in moving.
        Compute delta for x and y coordinates and then perform the drag
        """
        if self.gotLegend == 1 and self.leftdown:
            self.onLegendMotion(event)
            return

        if self.leftdown and self.selectedText is not None:
            # User has clicked on text and is dragging
            ax = event.inaxes
            if ax != None:
                # Only move text if mouse is within axes
                self.selectedText.set_position((event.xdata, event.ydata))
                self.canvas.draw_idle()
            else:
                # User has dragged outside of axes
                self.selectedText = None
            return

    def onMplPick(self, event):
        """
        On pick legend
        """
        legend = self.legend
        if event.artist == legend:
            # Get the box of the legend.
            bbox = self.legend.get_window_extent()
            # Get mouse coordinates at time of pick.
            self.mouse_x = event.mouseevent.x
            self.mouse_y = event.mouseevent.y
            # Get legend coordinates at time of pick.
            self.legend_x = bbox.xmin
            self.legend_y = bbox.ymin
            # Indicate we picked up the legend.
            self.gotLegend = 1

            #self.legend.legendPatch.set_alpha(0.5)

    def onLegendMotion(self, event):
        """
        On legend in motion
        """
        ax = event.inaxes
        if ax == None:
            return
        # Event occurred inside a plotting area
        lo_x, hi_x = ax.get_xlim()
        lo_y, hi_y = ax.get_ylim()
        # How much the mouse moved.
        x = mouse_diff_x = self.mouse_x - event.x
        y = mouse_diff_y = self.mouse_y - event.y
        # Put back inside
        if x < lo_x:
            x = lo_x
        if x > hi_x:
            x = hi_x
        if y < lo_y:
            y = lo_y
        if y > hi_y:
            y = hi_y
        # Move the legend from its previous location by that same amount
        loc_in_canvas = self.legend_x - mouse_diff_x, \
                        self.legend_y - mouse_diff_y
        # Transform into legend coordinate system
        trans_axes = self.legend.parent.transAxes.inverted()
        loc_in_norm_axes = trans_axes.transform_point(loc_in_canvas)
        self.legend_pos_loc = tuple(loc_in_norm_axes)
        self.legend._loc = self.legend_pos_loc
        # self.canvas.draw()
        self.canvas.draw_idle()

    def onMplWheel(self, event):
        """
        Process mouse wheel as zoom events
        """
        ax = event.inaxes
        step = event.step

        if ax != None:
            # Event occurred inside a plotting area
            lo, hi = ax.get_xlim()
            lo, hi = PlotUtilities.rescale(lo, hi, step,
                              pt=event.xdata, scale=ax.get_xscale())
            if not self.xscale == 'log' or lo > 0:
                self._scale_xlo = lo
                self._scale_xhi = hi
                ax.set_xlim((lo, hi))

            lo, hi = ax.get_ylim()
            lo, hi = PlotUtilities.rescale(lo, hi, step, pt=event.ydata,
                              scale=ax.get_yscale())
            if not self.yscale == 'log' or lo > 0:
                self._scale_ylo = lo
                self._scale_yhi = hi
                ax.set_ylim((lo, hi))
        else:
            # Check if zoom happens in the axes
            xdata, ydata = None, None
            x, y = event.x, event.y

            for ax in self.axes:
                insidex, _ = ax.xaxis.contains(event)
                if insidex:
                    xdata, _ = ax.transAxes.inverted().transform_point((x, y))
                insidey, _ = ax.yaxis.contains(event)
                if insidey:
                    _, ydata = ax.transAxes.inverted().transform_point((x, y))
            if xdata is not None:
                lo, hi = ax.get_xlim()
                lo, hi = PlotUtilities.rescale(lo, hi, step,
                                  bal=xdata, scale=ax.get_xscale())
                if not self.xscale == 'log' or lo > 0:
                    self._scale_xlo = lo
                    self._scale_xhi = hi
                    ax.set_xlim((lo, hi))
            if ydata is not None:
                lo, hi = ax.get_ylim()
                lo, hi = PlotUtilities.rescale(lo, hi, step, bal=ydata,
                                  scale=ax.get_yscale())
                if not self.yscale == 'log' or lo > 0:
                    self._scale_ylo = lo
                    self._scale_yhi = hi
                    ax.set_ylim((lo, hi))
        self.canvas.draw_idle()

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
