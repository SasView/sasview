import copy
import functools
import logging

import matplotlib as mpl
import numpy
from PySide6 import QtGui, QtWidgets

from sasdata.data_util.manipulations import CircularAverage

import sas.qtgui.Plotting.PlotUtilities as PlotUtilities
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas.qtgui.Plotting.BoxSum import BoxSum
from sas.qtgui.Plotting.ColorMap import ColorMap
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Plotting.PlotterData import Data1D, Data2D, DataRole
from sas.qtgui.Plotting.SlicerParameters import SlicerParameters
from sas.qtgui.Plotting.Slicers.AnnulusSlicer import AnnulusInteractor
from sas.qtgui.Plotting.Slicers.BoxSlicer import BoxInteractorX, BoxInteractorY
from sas.qtgui.Plotting.Slicers.BoxSum import BoxSumCalculator
from sas.qtgui.Plotting.Slicers.SectorSlicer import SectorInteractor
from sas.qtgui.Plotting.Slicers.WedgeSlicer import WedgeInteractorPhi, WedgeInteractorQ
from sas.system import config

logger = logging.getLogger(__name__)

DEFAULT_CMAP = mpl.cm.jet

# Minimum value of Z for which we will present data.
MIN_Z = -32

# Color cycle for slicers (colorblind-friendly palette)
SLICER_COLORS = [
    '#E69F00',  # orange
    '#56B4E9',  # sky blue
    '#009E73',  # bluish green
    '#F0E442',  # yellow
    '#0072B2',  # blue
    '#D55E00',  # vermillion
    '#CC79A7',  # reddish purple
    '#000000',  # black
    '#E31A1C',  # red
    '#1F78B4',  # light blue
    '#33A02C',  # green
    '#FF7F00',  # orange
    '#6A3D9A',  # purple
    '#B15928',  # brown
    '#FDBF6F'   # light orange
]


class Plotter2DWidget(PlotterBase):
    """
    2D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False, dimension=2):
        self.dimension = dimension
        super(Plotter2DWidget, self).__init__(manager=manager, quickplot=quickplot)

        self.cmap = DEFAULT_CMAP.name
        # Default scale
        self.scale = 'log_{10}'
        # to set the order of lines drawn first.
        self.slicer_z = 5
        # Reference to the current slicer
        self.slicer = None
        self.slicers = {}
        self.slicer_widget = None
        self.stackplots = config.STACK_PLOTS  # whether to stack multiple slicer plots
        self.slicer_plots_dict = {}  # keep track of slicer plots
        self.vmin = None
        self.vmax = None
        self.im = None
        self.cb = None
        # Masking properties
        self._show_masked_data = False  # TODO: Tie into configuration system
        self._masked_data = []

        self.manager = manager

        # Track color index for slicer color cycling
        self._slicer_color_index = 0

    @property
    def data(self):
        return self._data

    @property
    def data0(self):
        return self._data[0] if not self._show_masked_data else self._masked_data[0]

    @data.setter
    def data(self, data=None):
        """ data setter """
        if hasattr(data, 'mask') and not data.mask.all():
            # Create a copy of the data set to only be used in this context
            # Remove all masked points from the copy
            masked_data = copy.deepcopy(data)
            masked_data.data = masked_data.data[masked_data.mask == 1]
            masked_data.qx_data = masked_data.qx_data[masked_data.mask == 1]
            masked_data.qy_data = masked_data.qy_data[masked_data.mask == 1]
            if masked_data.err_data is not None:
                masked_data.err_data = masked_data.err_data[masked_data.mask == 1]
            if masked_data.dqx_data is not None:
                masked_data.dqx_data = masked_data.dqx_data[masked_data.mask == 1]
            if masked_data.dqy_data is not None:
                masked_data.dqy_data = masked_data.dqy_data[masked_data.mask == 1]
            if masked_data.q_data is not None:
                masked_data.q_data = masked_data.q_data[masked_data.mask == 1]
            masked_data.mask = masked_data.mask[masked_data.mask == 1]
        else:
            masked_data = data
        if self._data:
            self._data[0] = data
            self._masked_data[0] = masked_data
        else:
            self._data.append(data)
            self._masked_data.append(masked_data)
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
                      qx_data=self.data0.qx_data,
                      qy_data=self.data0.qy_data,
                      xmin=self.xmin,
                      xmax=self.xmax,
                      ymin=self.ymin, ymax=self.ymax,
                      cmap=self.cmap, zmin=zmin_2D_temp,
                      zmax=zmax_2D_temp, show_colorbar=show_colorbar,
                      update=update)

        self.updateCircularAverage()
        self.updateSlicer()

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

        plot_slicer_menu=self.contextMenu.addMenu('Slicers')
        self.actionCircularAverage = plot_slicer_menu.addAction("&Perform Circular Average")
        self.actionCircularAverage.triggered.connect(self.onCircularAverage)
        self.actionSectorView = plot_slicer_menu.addAction("&Sector [Q View]")
        self.actionSectorView.triggered.connect(self.onSectorView)
        self.actionAnnulusView = plot_slicer_menu.addAction("&Annulus [Phi View]")
        self.actionAnnulusView.triggered.connect(self.onAnnulusView)
        self.actionBoxSum = plot_slicer_menu.addAction("&Box Sum")
        self.actionBoxSum.triggered.connect(self.onBoxSum)
        self.actionBoxAveragingX = plot_slicer_menu.addAction("&Box Averaging in Qx")
        self.actionBoxAveragingX.triggered.connect(self.onBoxAveragingX)
        self.actionBoxAveragingY = plot_slicer_menu.addAction("&Box Averaging in Qy")
        self.actionBoxAveragingY.triggered.connect(self.onBoxAveragingY)
        self.actionWedgeAveragingQ = plot_slicer_menu.addAction("&Wedge Averaging in Q")
        self.actionWedgeAveragingQ.triggered.connect(self.onWedgeAveragingQ)
        self.actionWedgeAveragingPhi = plot_slicer_menu.addAction("&Wedge Averaging in Phi")
        self.actionWedgeAveragingPhi.triggered.connect(self.onWedgeAveragingPhi)

        plot_slicer_menu.addSeparator()

        # Additional items for slicer interaction
        if (self.slicer is not None) or (hasattr(self.slicer, 'slicers') and len(self.slicers) > 0):
            plot_slicer_menu.actionClearSlicer = plot_slicer_menu.addAction("&Clear Slicers")
            plot_slicer_menu.actionClearSlicer.triggered.connect(self.onClearSlicer)
        plot_slicer_menu.actionEditSlicer = plot_slicer_menu.addAction("&Edit Slicer Parameters")
        plot_slicer_menu.actionEditSlicer.triggered.connect(self.onEditSlicer)

        self.contextMenu.addSeparator()
        self.actionDataInfo = self.contextMenu.addAction("&DataInfo")
        self.actionDataInfo.triggered.connect(
             functools.partial(self.onDataInfo, self.data0))

        self.actionSavePointsAsFile = self.contextMenu.addAction("&Save Points as a File")
        self.actionSavePointsAsFile.triggered.connect(
             functools.partial(self.onSavePoints, self.data0))
        self.contextMenu.addSeparator()

        # Additional items for slicer interaction
        self.contextMenu.addSeparator()
        self.actionColorMap = self.contextMenu.addAction("&2D Color Map")
        self.actionColorMap.triggered.connect(self.onColorMap)
        self.contextMenu.addSeparator()
        self.actionToggleMaskedData = self.contextMenu.addAction("&Toggle Masked Data")
        self.actionToggleMaskedData.triggered.connect(self.onToggleMaskedData)
        self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Toggle Linear/Log Scale")
        self.actionChangeScale.triggered.connect(self.onToggleScale)
        self.contextMenu.addSeparator()
        self.actionToggleMenu = self.contextMenu.addAction("Toggle Navigation Menu")
        self.actionToggleMenu.triggered.connect(self.onToggleMenu)

        self.addHelpToContextMenu()

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

        self.addHelpToContextMenu()

    def onToggleMaskedData(self, event):
        """ Toggle the visibility of masked data points."""
        self._show_masked_data = not self._show_masked_data
        self.plot()

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
        Remove all slicers from the chart
        """
        # Clear all existing slicers
        for slicer in self.slicers.values():
            slicer.clear()
        self.slicers = {}

        # Clear box sum which is not stored in the dict
        if self.slicer is not None:
            self.slicer.clear()
            if self.slicer is BoxSumCalculator:
                self.boxwidget.close()
                self.boxwidget_subwindow.close()
                self.boxwidget = None
                self.boxwidget_subwindow = None

        self.slicer = None
        # Reset color index when all slicers are cleared
        self._slicer_color_index = 0
        self._removeSlicerPlots()

        self.canvas.draw()

        if self.slicer_widget:
            self.slicer_widget.close()
            self.slicer_widget = None

        # Close the box sum widget if it exists
        if hasattr(self, 'boxwidget') and self.boxwidget is not None:
            self.boxwidget.close()
            self.boxwidget = None

    def getActivePlots(self):
        ''' utility method for manager query of active plots '''
        return self.manager.active_plots

    def getActiveSlicerPlots(self):
        """
        Utility method for manager query of active slicer plots.
        Returns a dictionary of plot_id: plot_window for all 1D plots
        that were created by slicers from this 2D plot.
        """
        slicer_plots = {}

        if not hasattr(self, 'manager') or not hasattr(self.manager, 'active_plots'):
            return slicer_plots

        # Search through all active plots
        for plot_id, plot_window in self.manager.active_plots.items():
            if not hasattr(plot_window, 'data') and plot_window.data is not None:
                # No data loaded (catches the cases where data == None and data == [])
                continue
            # Get the data (could be a list or single item)
            data_list = plot_window.data if isinstance(plot_window.data, list) else [plot_window.data]

            # Check if any data in this plot is from a slicer
            for data in data_list:
                if ((type_id := getattr(data, 'type_id', None)) and  # Primary method: Check if this data has a type_id
                    self.data0.name in type_id):  # Check if the type_id contains this 2D plot's name
                    slicer_plots[plot_id] = plot_window
                    break  # Found a slicer plot, no need to check other data

                # Fallback: Check if data has plot_role attribute (older method)
                elif ((plot_role := getattr(data, 'plot_role', None)) and
                      plot_role == DataRole.ROLE_ANGULAR_SLICE and  # Only use the roles that actually exist
                      self.data0.name in data.name):  # Check if the data name contains this 2D plot's name
                    slicer_plots[plot_id] = plot_window
                    break
        return slicer_plots

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
                                              communicator=GuiUtils.communicate)
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

        new_plot.id = "2daverage" + self.data0.name
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

        GuiUtils.communicate.plotUpdateSignal.emit([new_plot])
        GuiUtils.communicate.forcePlotDisplaySignal.emit([item, new_plot])

    def updateCircularAverage(self):
        """
        Update circular averaging plot on Data2D change
        """
        if not hasattr(self, '_item'):
            return
        item = self._item
        if self._item.parent() is not None:
            item = self._item.parent()

        # Get all plots for current item
        plots = GuiUtils.plotsFromModel("", item)
        if plots is None:
            return
        ca_caption = '2daverage' + self.data0.name
        # See if current item plots contain 2D average plot
        has_plot = False
        for plot in plots:
            if plot.id is None:
                continue
            if ca_caption in plot.id:
                has_plot = True
        # return prematurely if no circular average plot found
        if not has_plot:
            return

        # Create a new plot
        new_plot = self.circularAverage()

        # Overwrite existing plot
        GuiUtils.updateModelItemWithPlot(item, new_plot, new_plot.id)
        # Show the new plot, if already visible
        GuiUtils.communicate.plotUpdateSignal.emit([new_plot])

    def updateSlicer(self):
        """
        Update slicer plot on Data2D change
        """
        if not hasattr(self, '_item'):
            return
        item = self._item
        if self._item.parent() is not None:
            item = self._item.parent()

        # Get all plots for current item
        plots = GuiUtils.plotsFromModel("", item)
        if plots is None:
            return
        slicer_caption = 'Slicer' + self.data0.name
        # See if current item plots contain slicer plot
        has_plot = False
        for plot in plots:
            if not hasattr(plot, 'type_id') or plot.type_id is None:
                continue
            if slicer_caption in plot.type_id:
                has_plot = True
        # return prematurely if no slicer plot found
        if not has_plot:
            return

        # Now that we've identified the right plot, update the 2D data the slicers uses
        for slicer in self.slicers.values():
            slicer.data = self.data0
            # Replot now that the 2D data is updated
            slicer._post_data()

    def _get_next_slicer_color(self):
        """
        Get the next color for a new slicer and increment the index
        """
        color = SLICER_COLORS[self._slicer_color_index % len(SLICER_COLORS)] # so colours don't overflow
        self._slicer_color_index += 1
        return color

    def _recurse_plots_to_remove(self, item):
        temp_plots_to_remove = []
        slicer_type_id = 'Slicer' + self.data0.name
        for item_index in range(item.rowCount()):
            child = item.child(item_index)
            if child.hasChildren():
                self._recurse_plots_to_remove(child)
            if (isinstance(child.data(), (Data1D, Data2D))
                    and hasattr(child.data(), 'type_id')
                    and slicer_type_id in child.data().type_id
                    and child.rowCount() > 0
                    and child.child(0).text()):
                        temp_plots_to_remove.append(item.child(item_index))

        for plot in temp_plots_to_remove:
            item.removeRow(plot.row())

    def _removeSlicerPlots(self):
        """  
        Clear the previous slicer plots  
        """
        # Clear the old slicer plots so they don't reappear later
        if not hasattr(self, '_item'):
            return
        item = self._item
        if self._item.parent() is not None:
            item = self._item.parent()
        self._recurse_plots_to_remove(item)

    def setSlicer(self, slicer, stack: bool=None):
        """ Create a new slicer without removing the old one """
        # Clear the previous slicers if BoxSumCalculator is used or clear BoxSum if other slicer is used
        if isinstance(self.slicer, BoxSumCalculator):
            self.onClearSlicer()
        elif self.slicer is not None and slicer == BoxSumCalculator:
            # If we're creating a BoxSum but there are other slicers, clear them
            self.onClearSlicer()

        self.slicer_z += 1

        # Get next color for this slicer
        slicer_color = self._get_next_slicer_color()

        self.slicer = slicer(self, self.ax, item=self._item, color=slicer_color, zorder=self.slicer_z)

        if stack is not None:
            self.stackplots = stack

        # Generate a unique name for this slicer
        slicer_name = f"{slicer.__name__}_{self.data0.name}_{len(self.slicers)}"

        # Store in dictionary with unique name as key
        self.slicers[slicer_name] = self.slicer

        self.ax.set_ylim(self.data0.ymin, self.data0.ymax)
        self.ax.set_xlim(self.data0.xmin, self.data0.xmax)
        # Draw slicer
        self.figure.canvas.draw()
        self.slicer.update()

        # Reset the model on the Edit slicer parameters widget
        self.param_model = self.slicer.model()
        if self.slicer_widget:
            # Update the slicers list and auto-check the newly created slicer
            self.slicer_widget.updateSlicersList()
            self.slicer_widget.checkSlicerByName(slicer_name)
            self.setParamOnModel()

    def notifySlicerModified(self, slicer_obj):
        """Notify the parameters dialog that a slicer was interacted with."""
        try:
            # Find the slicer name from the mapping
            for name, obj in self.slicers.items():
                if obj is slicer_obj:
                    if self.slicer_widget:
                        self.slicer_widget.checkSlicerByName(name)
                    break
        except Exception as e:
            logger.error("Error in notifySlicerModified: %s", str(e))

    def onSectorView(self):
        """
        Perform sector averaging on Q and draw sector slicer
        """
        self.setSlicer(slicer=SectorInteractor)

    def setParamOnModel(self):
        """ Set the model on the slicer widget """
        if self.slicer_widget:
            self.slicer_widget.setModel(self.param_model)

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
        if self.slicer is not None or len(self.slicers) > 0:
            # Pop up a confirmation dialog
            reply = QtWidgets.QMessageBox.question(self, 'Delete Slicer',
                                                'Are you sure you want to delete this slicer?',
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                                QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                return

        self.onClearSlicer()
        self.slicer_z += 1

        # Get next color for this slicer
        slicer_color = self._get_next_slicer_color()

        self.slicer = BoxSumCalculator(self, self.ax, color=slicer_color, zorder=self.slicer_z)

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
            # Clear the reference in the slicer
            if self.slicer is not None:
                self.slicer.widget = None

        # Get the BoxSumCalculator model.
        self.box_sum_model = self.slicer.model()
        # Pass the BoxSumCalculator model to the BoxSum widget
        self.boxwidget = BoxSum(self, model=self.box_sum_model)
        # Add the plot to the workspace
        self.boxwidget_subwindow = self.manager.parent.workspace().addSubWindow(self.boxwidget)
        self.boxwidget.closeWidgetSignal.connect(boxWidgetClosed)

        # Store widget reference in the slicer so it can close it when cleared
        self.slicer.widget = self.boxwidget

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

    def onWedgeAveragingQ(self):
        """
        Perform 2D data averaging on Q
        Create a new slicer .
        """
        self.setSlicer(slicer=WedgeInteractorQ)

    def onWedgeAveragingPhi(self):
        """
        Perform 2D data averaging on Phi
        Create a new slicer .
        """
        self.setSlicer(slicer=WedgeInteractorPhi)

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

            # color bar for the plot
            cbax = self.figure.add_axes([0.88, 0.2, 0.02, 0.7])

            # Current labels for axes
            self.ax.set_ylabel(self.y_label)
            self.ax.set_xlabel(self.x_label)

            # Title only for regular charts
            if not self.quickplot:
                self.ax.set_title(label=self._title)

            # remove color bar in case we have it on screen
            if self.cb is not None:
                self.cb.remove()
            if cbax is None:
                self.ax.set_frame_on(False)
                self.cb = self.figure.colorbar(self.im, shrink=0.8, aspect=20)
            else:
                self.cb = self.figure.colorbar(self.im, cax=cbax)

            self.cb.update_normal(self.im)
            self.cb.set_label('$' + self.scale + '$')

            self.vmin = self.cb.vmin
            self.vmax = self.cb.vmax

            if show_colorbar is False:
                self.cb.remove()

        else:
            # clear the previous 2D from memory
            self.figure.clear()

            self.figure.subplots_adjust(left=0.1, right=.8, bottom=.1)

            data_x, data_y = numpy.meshgrid(self.data0.x_bins[0:-1],
                                            self.data0.y_bins[0:-1])

            self.ax = self.figure.add_subplot(111, projection='3d')

            # Disable rotation for large sets.
            # TODO: Define "large" for a dataset
            SET_TOO_LARGE = 500
            if len(data_x) > SET_TOO_LARGE:
                self.ax.disable_mouse_rotation()

            self.figure.canvas.resizing = False
            im = self.ax.plot_surface(data_x, data_y, output, rstride=1,
                                     cstride=1, cmap=cmap,
                                     linewidth=0, antialiased=False)

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
            self.ax.imshow(img, origin=origin)
        else:
            self.ax.imshow(img)

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
        coord_str = f"x: {x_str}, y: {y_str}"
        GuiUtils.communicate.statusBarUpdateSignal.emit(coord_str)

class Plotter2D(QtWidgets.QDialog, Plotter2DWidget):
    """
    Plotter widget implementation
    """
    def __init__(self, parent=None, quickplot=False, dimension=2):
        Plotter2DWidget.__init__(self, manager=parent, quickplot=quickplot, dimension=dimension)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/ball.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
