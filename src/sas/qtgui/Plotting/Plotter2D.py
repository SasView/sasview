import copy
import numpy
import functools

from PyQt5 import QtGui
from PyQt5 import QtWidgets

from mpl_toolkits.mplot3d import Axes3D

from sas.sascalc.dataloader.manipulations import CircularAverage

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterData import Data2D

import sas.qtgui.Plotting.PlotUtilities as PlotUtilities
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Plotting.ColorMap import ColorMap
from sas.qtgui.Plotting.BoxSum import BoxSum
from sas.qtgui.Plotting.SlicerParameters import SlicerParameters

# TODO: move to sas.qtgui namespace
from sas.qtgui.Plotting.Slicers.BoxSlicer import BoxInteractorX
from sas.qtgui.Plotting.Slicers.BoxSlicer import BoxInteractorY
from sas.qtgui.Plotting.Slicers.AnnulusSlicer import AnnulusInteractor
from sas.qtgui.Plotting.Slicers.SectorSlicer import SectorInteractor
from sas.qtgui.Plotting.Slicers.BoxSum import BoxSumCalculator

import matplotlib as mpl
DEFAULT_CMAP = mpl.cm.jet

# Minimum value of Z for which we will present data.
MIN_Z = -32


class Plotter2DWidget(PlotterBase):
    """
    2D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False, dimension=2):
        self.dimension = dimension
        super(Plotter2DWidget, self).__init__(parent, manager=manager, quickplot=quickplot)

        self.cmap = DEFAULT_CMAP.name
        # Default scale
        self.scale = 'log_{10}'
        # to set the order of lines drawn first.
        self.slicer_z = 5
        # Reference to the current slicer
        self.slicer = None
        self.slicer_widget = None
        self.vmin = None
        self.vmax = None
        self.im = None

        self.manager = manager

    @property
    def data(self):
        return self._data

    @property
    def data0(self):
        return self._data[0]

    @data.setter
    def data(self, data=None):
        """ data setter """
        if self._data:
            self._data[0] = data
        else:
            self._data.append(data)
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

    def plot(self, data=None, marker=None, show_colorbar=True, update=False):
        """
        Plot 2D self._data
        marker - unused
        """
        # Assing data
        if isinstance(data, Data2D):
            # no append, since there can only be one data in Data2D plot
            self.data = data

        if not self._data:
            return

        # Toggle the scale
        zmin_2D_temp, zmax_2D_temp = self.calculateDepth()

        # Prepare and show the plot
        self.showPlot(data=self.data0.data,
                      qx_data=self.qx_data,
                      qy_data=self.qy_data,
                      xmin=self.xmin,
                      xmax=self.xmax,
                      ymin=self.ymin, ymax=self.ymax,
                      cmap=self.cmap, zmin=zmin_2D_temp,
                      zmax=zmax_2D_temp, show_colorbar=show_colorbar,
                      update=update)

        self.updateCircularAverage()

    def calculateDepth(self):
        """
        Re-calculate the plot depth parameters depending on the scale
        """
        # Toggle the scale
        zmin_temp = self.zmin
        zmax_temp = self.zmax
        # self.scale predefined in the baseclass
        # in numpy > 1.12 power(int, -int) raises ValueException
        # "Integers to negative integer powers are not allowed."
        if self.scale == 'log_{10}':
            if self.zmin is not None:
                zmin_temp = numpy.power(10.0, self.zmin)
            if self.zmax is not None:
                zmax_temp = numpy.power(10.0, self.zmax)
        else:
            if self.zmin is not None:
                # min log value: no log(negative)
                zmin_temp = MIN_Z if self.zmin <= 0 else numpy.log10(self.zmin)
            if self.zmax is not None:
                zmax_temp = numpy.log10(self.zmax)

        return (zmin_temp, zmax_temp)

    def createContextMenu(self):
        """
        Define common context menu and associated actions for the MPL widget
        """
        self.defaultContextMenu()

        self.contextMenu.addSeparator()
        self.actionDataInfo = self.contextMenu.addAction("&DataInfo")
        self.actionDataInfo.triggered.connect(
             functools.partial(self.onDataInfo, self.data0))

        self.actionSavePointsAsFile = self.contextMenu.addAction("&Save Points as a File")
        self.actionSavePointsAsFile.triggered.connect(
             functools.partial(self.onSavePoints, self.data0))
        self.contextMenu.addSeparator()

        self.actionCircularAverage = self.contextMenu.addAction("&Perform Circular Average")
        self.actionCircularAverage.triggered.connect(self.onCircularAverage)

        self.actionSectorView = self.contextMenu.addAction("&Sector [Q View]")
        self.actionSectorView.triggered.connect(self.onSectorView)
        self.actionAnnulusView = self.contextMenu.addAction("&Annulus [Phi View]")
        self.actionAnnulusView.triggered.connect(self.onAnnulusView)
        self.actionBoxSum = self.contextMenu.addAction("&Box Sum")
        self.actionBoxSum.triggered.connect(self.onBoxSum)
        self.actionBoxAveragingX = self.contextMenu.addAction("&Box Averaging in Qx")
        self.actionBoxAveragingX.triggered.connect(self.onBoxAveragingX)
        self.actionBoxAveragingY = self.contextMenu.addAction("&Box Averaging in Qy")
        self.actionBoxAveragingY.triggered.connect(self.onBoxAveragingY)
        # Additional items for slicer interaction
        if self.slicer:
            self.actionClearSlicer = self.contextMenu.addAction("&Clear Slicer")
            self.actionClearSlicer.triggered.connect(self.onClearSlicer)
        self.actionEditSlicer = self.contextMenu.addAction("&Edit Slicer Parameters")
        self.actionEditSlicer.triggered.connect(self.onEditSlicer)
        self.contextMenu.addSeparator()
        self.actionColorMap = self.contextMenu.addAction("&2D Color Map")
        self.actionColorMap.triggered.connect(self.onColorMap)
        self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Toggle Linear/Log Scale")
        self.actionChangeScale.triggered.connect(self.onToggleScale)
        self.contextMenu.addSeparator()
        self.actionToggleMenu = self.contextMenu.addAction("Toggle Navigation Menu")
        self.actionToggleMenu.triggered.connect(self.onToggleMenu)

    def createContextMenuQuick(self):
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
        # self.scale predefined in the baseclass
        if self.scale == 'log_{10}':
            self.scale = 'linear'
        else:
            self.scale = 'log_{10}'

        self.plot()

    def onClearSlicer(self):
        """
        Remove all sclicers from the chart
        """
        if self.slicer is None:
            return

        self.slicer.clear()
        self.canvas.draw()
        self.slicer = None
        if self.slicer_widget:
            self.slicer_widget.setModel(None)

    def getActivePlots(self):
        ''' utility method for manager query of active plots '''
        return self.manager.active_plots

    def onEditSlicer(self):
        """
        Present a dialog for manipulating the current slicer
        """
        # Only show the dialog if not currently shown
        if self.slicer_widget:
            return

        def slicer_closed():
            # Need to disconnect the signal!!
            self.slicer_widget.closeWidgetSignal.disconnect()
            self.manager.parent.workspace().removeSubWindow(self.slicer_subwindow)
            # reset slicer_widget on "Edit Slicer Parameters" window close
            self.slicer_widget = None

        self.param_model = None
        validator = None
        if self.slicer is not None and not isinstance(self.slicer, BoxSumCalculator):
            self.param_model = self.slicer.model()
            validator = self.slicer.validate
        # Pass the model to the Slicer Parameters widget
        self.slicer_widget = SlicerParameters(self, model=self.param_model,
                                              active_plots=self.getActivePlots(),
                                              validate_method=validator,
                                              communicator=self.manager.communicator)
        self.slicer_widget.closeWidgetSignal.connect(slicer_closed)
        # Add the plot to the workspace
        self.slicer_subwindow = self.manager.parent.workspace().addSubWindow(self.slicer_widget)

        self.slicer_widget.show()

    def circularAverage(self):
        """
        Calculate the circular average and create the Data object for it
        """
        # Find the best number of bins
        npt = numpy.sqrt(len(self.data0.data[numpy.isfinite(self.data0.data)]))
        npt = numpy.floor(npt)
        # compute the maximum radius of data2D
        self.qmax = max(numpy.fabs(self.data0.xmax),
                        numpy.fabs(self.data0.xmin))
        self.ymax = max(numpy.fabs(self.data0.ymax),
                        numpy.fabs(self.data0.ymin))
        self.radius = numpy.sqrt(numpy.power(self.qmax, 2) + numpy.power(self.ymax, 2))
        #Compute beam width
        bin_width = (self.qmax + self.qmax) / npt
        # Create data1D circular average of data2D
        circle = CircularAverage(r_min=0, r_max=self.radius, bin_width=bin_width)
        circ = circle(self.data0)
        dxl = circ.dxl if hasattr(circ, "dxl") else None
        dxw = circ.dxw if hasattr(circ, "dxw") else None

        new_plot = Data1D(x=circ.x, y=circ.y, dy=circ.dy, dx=circ.dx)
        new_plot.dxl = dxl
        new_plot.dxw = dxw
        new_plot.name = new_plot.title = "Circ avg " + self.data0.name
        new_plot.source = self.data0.source
        new_plot.interactive = True
        new_plot.detector = self.data0.detector

        # Define axes if not done yet.
        new_plot.xaxis("\\rm{Q}", "A^{-1}")
        if hasattr(self.data0, "scale") and \
                    self.data0.scale == 'linear':
            new_plot.ytransform = 'y'
            new_plot.yaxis("\\rm{Residuals} ", "normalized")
        else:
            new_plot.yaxis("\\rm{Intensity} ", "cm^{-1}")

        new_plot.group_id = "2daverage" + self.data0.name
        new_plot.id = "Circ avg " + self.data0.name
        new_plot.is_data = True

        return new_plot

    def onCircularAverage(self):
        """
        Perform circular averaging on Data2D
        """
        new_plot = self.circularAverage()

        item = self._item
        if self._item.parent() is not None:
            item = self._item.parent()

        GuiUtils.updateModelItemWithPlot(item, new_plot, new_plot.id)

        self.manager.communicator.plotUpdateSignal.emit([new_plot])
        self.manager.communicator.forcePlotDisplaySignal.emit([item, new_plot])

    def updateCircularAverage(self):
        """
        Update circular averaging plot on Data2D change
        """
        if not hasattr(self, '_item'): return
        item = self._item
        if self._item.parent() is not None:
            item = self._item.parent()

        # Get all plots for current item
        plots = GuiUtils.plotsFromModel("", item)
        if plots is None: return
        ca_caption = '2daverage' + self.data0.name
        # See if current item plots contain 2D average plot
        has_plot = False
        for plot in plots:
            if plot.group_id is None: continue
            if ca_caption in plot.group_id: has_plot = True
        # return prematurely if no circular average plot found
        if not has_plot: return

        # Create a new plot
        new_plot = self.circularAverage()

        # Overwrite existing plot
        GuiUtils.updateModelItemWithPlot(item, new_plot, new_plot.id)
        # Show the new plot, if already visible
        self.manager.communicator.plotUpdateSignal.emit([new_plot])

    def setSlicer(self, slicer, reset=True):
        """
        Clear the previous slicer and create a new one.
        slicer: slicer class to create
        """
        # Clear current slicer
        if self.slicer is not None:
            self.slicer.clear()
        # Create a new slicer
        self.slicer_z += 1
        self.slicer = slicer(self, self.ax, item=self._item, zorder=self.slicer_z)
        self.ax.set_ylim(self.data0.ymin, self.data0.ymax)
        self.ax.set_xlim(self.data0.xmin, self.data0.xmax)
        # Draw slicer
        self.figure.canvas.draw()
        self.slicer.update()

        # Reset the model on the Edit slicer parameters widget
        self.param_model = self.slicer.model()
        if self.slicer_widget and reset:
            self.slicer_widget.setModel(self.param_model)

    def onSectorView(self):
        """
        Perform sector averaging on Q and draw sector slicer
        """
        self.setSlicer(slicer=SectorInteractor)

    def onAnnulusView(self):
        """
        Perform sector averaging on Phi and draw annulus slicer
        """
        self.setSlicer(slicer=AnnulusInteractor)

    def onBoxSum(self):
        """
        Perform 2D Data averaging Qx and Qy.
        Display box slicer details.
        """
        self.onClearSlicer()
        self.slicer_z += 1
        self.slicer = BoxSumCalculator(self, self.ax, zorder=self.slicer_z)

        self.ax.set_ylim(self.data0.ymin, self.data0.ymax)
        self.ax.set_xlim(self.data0.xmin, self.data0.xmax)
        self.figure.canvas.draw()
        self.slicer.update()

        def boxWidgetClosed():
            # Need to disconnect the signal!!
            self.boxwidget.closeWidgetSignal.disconnect()
            # reset box on "Edit Slicer Parameters" window close
            self.manager.parent.workspace().removeSubWindow(self.boxwidget_subwindow)
            self.boxwidget = None

        # Get the BoxSumCalculator model.
        self.box_sum_model = self.slicer.model()
        # Pass the BoxSumCalculator model to the BoxSum widget
        self.boxwidget = BoxSum(self, model=self.box_sum_model)
        # Add the plot to the workspace
        self.boxwidget_subwindow = self.manager.parent.workspace().addSubWindow(self.boxwidget)
        self.boxwidget.closeWidgetSignal.connect(boxWidgetClosed)

        self.boxwidget.show()

    def onBoxAveragingX(self):
        """
        Perform 2D data averaging on Qx
        Create a new slicer.
        """
        self.setSlicer(slicer=BoxInteractorX)

    def onBoxAveragingY(self):
        """
        Perform 2D data averaging on Qy
        Create a new slicer .
        """
        self.setSlicer(slicer=BoxInteractorY)

    def onColorMap(self):
        """
        Display the color map dialog and modify the plot's map accordingly
        """
        color_map_dialog = ColorMap(self, cmap=self.cmap,
                                    vmin=self.vmin,
                                    vmax=self.vmax,
                                    data=self.data0)

        color_map_dialog.apply_signal.connect(self.onApplyMap)

        if color_map_dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.onApplyMap(color_map_dialog.norm(), color_map_dialog.cmap())

    def onApplyMap(self, v_values, cmap):
        """
        Update the chart color map based on data passed from the widget
        """
        self.cmap = str(cmap)
        self.vmin, self.vmax = v_values
        # Redraw the chart with new cmap
        self.plot()

    def showPlot(self, data, qx_data, qy_data, xmin, xmax, ymin, ymax,
                 zmin, zmax, label='data2D', cmap=DEFAULT_CMAP, show_colorbar=True,
                 update=False):
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
        if data.ndim == 0:
            return
        elif data.ndim == 1:
            output = PlotUtilities.build_matrix(data, self.qx_data, self.qy_data)
        else:
            output = copy.deepcopy(data)

        # get the x and y_bin arrays.
        x_bins, y_bins = PlotUtilities.get_bins(self.qx_data, self.qy_data)
        self.data0.x_bins = x_bins
        self.data0.y_bins = y_bins

        zmin_temp = self.zmin
        # check scale
        if self.scale == 'log_{10}':
            #with numpy.errstate(all='ignore'):
            #    output = numpy.log10(output)
            #index = numpy.isfinite(output)
            #if not index.all():
            #    cutoff = (numpy.quantile(output[index], 0.05) - numpy.log10(2) if index.any() else 0.)
            #    output[output < cutoff] = cutoff
            #    output[~index] = cutoff
            try:
                if  self.zmin <= 0  and len(output[output > 0]) > 0:
                    zmin_temp = self.zmin
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

        vmin, vmax = None, None

        self.cmap = cmap
        if self.dimension != 3:
            #Re-adjust colorbar
            self.figure.subplots_adjust(left=0.2, right=.8, bottom=.2)

            zmax_temp = self.zmax
            if self.vmin is not None:
                zmin_temp = self.vmin
                zmax_temp = self.vmax
            if self.im is not None and update:
                self.im.set_data(output)
            else:
                self.im = self.ax.imshow(output, interpolation='nearest',
                                origin='lower',
                                vmin=zmin_temp, vmax=zmax_temp,
                                cmap=self.cmap,
                                extent=(self.xmin, self.xmax,
                                        self.ymin, self.ymax))

            cbax = self.figure.add_axes([0.88, 0.2, 0.02, 0.7])

            # Current labels for axes
            self.ax.set_ylabel(self.y_label)
            self.ax.set_xlabel(self.x_label)

            # Title only for regular charts
            if not self.quickplot:
                self.ax.set_title(label=self._title)

            if cbax is None:
                self.ax.set_frame_on(False)
                cb = self.figure.colorbar(self.im, shrink=0.8, aspect=20)
            else:
                cb = self.figure.colorbar(self.im, cax=cbax)

            cb.update_bruteforce(self.im)
            cb.set_label('$' + self.scale + '$')

            self.vmin = cb.vmin
            self.vmax = cb.vmax

            if show_colorbar is False:
                cb.remove()

        else:
            # clear the previous 2D from memory
            self.figure.clear()

            self.figure.subplots_adjust(left=0.1, right=.8, bottom=.1)

            data_x, data_y = numpy.meshgrid(self.data0.x_bins[0:-1],
                                            self.data0.y_bins[0:-1])

            ax = Axes3D(self.figure)

            # Disable rotation for large sets.
            # TODO: Define "large" for a dataset
            SET_TOO_LARGE = 500
            if len(data_x) > SET_TOO_LARGE:
                ax.disable_mouse_rotation()

            self.figure.canvas.resizing = False
            im = ax.plot_surface(data_x, data_y, output, rstride=1,
                                 cstride=1, cmap=cmap,
                                 linewidth=0, antialiased=False)
            self.ax.set_axis_off()

        if self.dimension != 3:
            self.figure.canvas.draw_idle()
        else:
            self.figure.canvas.draw()

    def imageShow(self, img, origin=None):
        """
        Show background image
        :Param img: [imread(path) from matplotlib.pyplot]
        """
        if origin is not None:
            im = self.ax.imshow(img, origin=origin)
        else:
            im = self.ax.imshow(img)

    def replacePlot(self, id, new_plot):
        """
        Replace data in current chart.
        This effectively refreshes the chart with changes to one of its plots
        """
        self.plot(data=new_plot)

    def onMplMouseDown(self, event):
        """
        Display x/y/intensity on click
        """
        # Check that the LEFT button was pressed
        if event.button != 1:
            return

        if event.inaxes is None:
            return
        x_click = 0.0
        y_click = 0.0
        try:
            x_click = float(event.xdata)  # / size_x
            y_click = float(event.ydata)  # / size_y
        except:
            self.position = None
        x_str = GuiUtils.formatNumber(x_click)
        y_str = GuiUtils.formatNumber(y_click)
        coord_str = "x: {}, y: {}".format(x_str, y_str)
        self.manager.communicate.statusBarUpdateSignal.emit(coord_str)

class Plotter2D(QtWidgets.QDialog, Plotter2DWidget):
    """
    Plotter widget implementation
    """
    def __init__(self, parent=None, quickplot=False, dimension=2):
        QtWidgets.QDialog.__init__(self)
        Plotter2DWidget.__init__(self, manager=parent, quickplot=quickplot, dimension=dimension)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/ball.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
