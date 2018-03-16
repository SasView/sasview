from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

import functools
import copy
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Plotting.AddText import AddText
from sas.qtgui.Plotting.SetGraphRange import SetGraphRange
from sas.qtgui.Plotting.LinearFit import LinearFit
from sas.qtgui.Plotting.PlotProperties import PlotProperties

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Plotting.PlotUtilities as PlotUtilities

class PlotterWidget(PlotterBase):
    """
    1D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False):
        super(PlotterWidget, self).__init__(parent, manager=manager, quickplot=quickplot)

        self.parent = parent

        # Dictionary of {plot_id:Data1d}
        self.plot_dict = {}

        # Window for text add
        self.addText = AddText(self)

        # Log-ness of the axes
        self.xLogLabel = "log10(x)"
        self.yLogLabel = "log10(y)"

        # Data container for the linear fit
        self.fit_result = Data1D(x=[], y=[], dy=None)
        self.fit_result.symbol = 13
        self.fit_result.name = "Fit"

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """ data setter """
        self._data = value
        if value._xunit:
            self.xLabel = "%s(%s)"%(value._xaxis, value._xunit)
        else:
            self.xLabel = "%s"%(value._xaxis)
        if value._yunit:
            self.yLabel = "%s(%s)"%(value._yaxis, value._yunit)
        else:
            self.yLabel = "%s"%(value._yaxis)

        if value.scale == 'linear' or value.isSesans:
            self.xscale = 'linear'
            self.yscale = 'linear'
        self.title(title=value.name)

    def plot(self, data=None, color=None, marker=None, hide_error=False):
        """
        Add a new plot of self._data to the chart.
        """
        # Data1D
        if isinstance(data, Data1D):
            self.data = data
        assert(self._data)

        is_fit = (self.data.id=="fit")

        # Transform data if required.
        # TODO: it properly!
        #if data.xtransform is not None or data.ytransform is not None:
        #    a, b, c, d = GuiUtils.xyTransform(self.data, self.data.xtransform, self.data.ytransform)

        # Shortcuts
        ax = self.ax
        x = self._data.view.x
        y = self._data.view.y

        # Marker symbol. Passed marker is one of matplotlib.markers characters
        # Alternatively, picked up from Data1D as an int index of PlotUtilities.SHAPES dict
        if marker is None:
            marker = self.data.symbol
            # Try name first
            try:
                marker = dict(PlotUtilities.SHAPES)[marker]
            except KeyError:
                marker = list(PlotUtilities.SHAPES.values())[marker]

        assert marker is not None
        # Plot name
        if self.data.title:
            self.title(title=self.data.title)
        else:
            self.title(title=self.data.name)

        # Error marker toggle
        if hide_error is None:
            hide_error = self.data.hide_error

        # Plot color
        if color is None:
            color = self.data.custom_color

        color = PlotUtilities.getValidColor(color)

        markersize = self._data.markersize

        # Draw non-standard markers
        l_width = markersize * 0.4
        if marker == '-' or marker == '--':
            line = self.ax.plot(x, y, color=color, lw=l_width, marker='',
                             linestyle=marker, label=self._title, zorder=10)[0]

        elif marker == 'vline':
            y_min = min(y)*9.0/10.0 if min(y) < 0 else 0.0
            line = self.ax.vlines(x=x, ymin=y_min, ymax=y, color=color,
                            linestyle='-', label=self._title, lw=l_width, zorder=1)

        elif marker == 'step':
            line = self.ax.step(x, y, color=color, marker='', linestyle='-',
                                label=self._title, lw=l_width, zorder=1)[0]

        else:
            # plot data with/without errorbars
            if hide_error:
                line = ax.plot(x, y, marker=marker, color=color, markersize=markersize,
                        linestyle='', label=self._title, picker=True)
            else:
                line = ax.errorbar(x, y,
                            yerr=self._data.view.dy, xerr=None,
                            capsize=2, linestyle='',
                            barsabove=False,
                            color=color,
                            marker=marker,
                            markersize=markersize,
                            lolims=False, uplims=False,
                            xlolims=False, xuplims=False,
                            label=self._title,
                            picker=True)

        # Update the list of data sets (plots) in chart
        self.plot_dict[self._data.id] = self.data

        # Now add the legend with some customizations.

        self.legend = ax.legend(loc='upper right', shadow=True)
        if self.legend:
            self.legend.set_picker(True)

        # Current labels for axes
        if self.y_label and not is_fit:
            ax.set_ylabel(self.y_label)
        if self.x_label and not is_fit:
            ax.set_xlabel(self.x_label)

        # Include scaling (log vs. linear)
        ax.set_xscale(self.xscale)
        ax.set_yscale(self.yscale)

        # define the ranges
        self.setRange = SetGraphRange(parent=self,
            x_range=self.ax.get_xlim(), y_range=self.ax.get_ylim())

        # refresh canvas
        self.canvas.draw_idle()

    def createContextMenu(self):
        """
        Define common context menu and associated actions for the MPL widget
        """
        self.defaultContextMenu()

        # Separate plots
        self.addPlotsToContextMenu()

        # Additional menu items
        self.contextMenu.addSeparator()
        self.actionAddText = self.contextMenu.addAction("Add Text")
        self.actionRemoveText = self.contextMenu.addAction("Remove Text")
        self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Change Scale")
        self.contextMenu.addSeparator()
        self.actionSetGraphRange = self.contextMenu.addAction("Set Graph Range")
        self.actionResetGraphRange =\
            self.contextMenu.addAction("Reset Graph Range")
        # Add the title change for dialogs
        #if self.parent:
        self.contextMenu.addSeparator()
        self.actionWindowTitle = self.contextMenu.addAction("Window Title")

        # Define the callbacks
        self.actionAddText.triggered.connect(self.onAddText)
        self.actionRemoveText.triggered.connect(self.onRemoveText)
        self.actionChangeScale.triggered.connect(self.onScaleChange)
        self.actionSetGraphRange.triggered.connect(self.onSetGraphRange)
        self.actionResetGraphRange.triggered.connect(self.onResetGraphRange)
        self.actionWindowTitle.triggered.connect(self.onWindowsTitle)

    def addPlotsToContextMenu(self):
        """
        Adds operations on all plotted sets of data to the context menu
        """
        for id in list(self.plot_dict.keys()):
            plot = self.plot_dict[id]

            name = plot.name if plot.name else plot.title
            plot_menu = self.contextMenu.addMenu('&%s' % name)

            self.actionDataInfo = plot_menu.addAction("&DataInfo")
            self.actionDataInfo.triggered.connect(
                                functools.partial(self.onDataInfo, plot))

            self.actionSavePointsAsFile = plot_menu.addAction("&Save Points as a File")
            self.actionSavePointsAsFile.triggered.connect(
                                functools.partial(self.onSavePoints, plot))
            plot_menu.addSeparator()

            if plot.id != 'fit':
                self.actionLinearFit = plot_menu.addAction('&Linear Fit')
                self.actionLinearFit.triggered.connect(
                                functools.partial(self.onLinearFit, id))
                plot_menu.addSeparator()

            self.actionRemovePlot = plot_menu.addAction("Remove")
            self.actionRemovePlot.triggered.connect(
                                functools.partial(self.onRemovePlot, id))

            if not plot.is_data:
                self.actionFreeze = plot_menu.addAction('&Freeze')
                self.actionFreeze.triggered.connect(
                                functools.partial(self.onFreeze, id))
            plot_menu.addSeparator()

            if plot.is_data:
                self.actionHideError = plot_menu.addAction("Hide Error Bar")
                if plot.dy is not None and plot.dy != []:
                    if plot.hide_error:
                        self.actionHideError.setText('Show Error Bar')
                else:
                    self.actionHideError.setEnabled(False)
                self.actionHideError.triggered.connect(
                                functools.partial(self.onToggleHideError, id))
                plot_menu.addSeparator()

            self.actionModifyPlot = plot_menu.addAction('&Modify Plot Property')
            self.actionModifyPlot.triggered.connect(
                                functools.partial(self.onModifyPlot, id))

    def createContextMenuQuick(self):
        """
        Define context menu and associated actions for the quickplot MPL widget
        """
        # Default actions
        self.defaultContextMenu()

        # Additional actions
        self.actionToggleGrid = self.contextMenu.addAction("Toggle Grid On/Off")
        self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Change Scale")

        # Define the callbacks
        self.actionToggleGrid.triggered.connect(self.onGridToggle)
        self.actionChangeScale.triggered.connect(self.onScaleChange)

    def onScaleChange(self):
        """
        Show a dialog allowing axes rescaling
        """
        if self.properties.exec_() == QtWidgets.QDialog.Accepted:
            self.xLogLabel, self.yLogLabel = self.properties.getValues()
            self.xyTransform(self.xLogLabel, self.yLogLabel)

    def onAddText(self):
        """
        Show a dialog allowing adding custom text to the chart
        """
        if self.addText.exec_() != QtWidgets.QDialog.Accepted:
            return

        # Retrieve the new text, its font and color
        extra_text = self.addText.text()
        extra_font = self.addText.font()
        extra_color = self.addText.color()

        # Place the text on the screen at the click location
        pos_x = self.x_click
        pos_y = self.y_click

        # Map QFont onto MPL font
        mpl_font = FontProperties()
        mpl_font.set_size(int(extra_font.pointSize()))
        mpl_font.set_family(str(extra_font.family()))
        mpl_font.set_weight(int(extra_font.weight()))
        # MPL style names
        styles = ['normal', 'italic', 'oblique']
        # QFont::Style maps directly onto the above
        try:
            mpl_font.set_style(styles[extra_font.style()])
        except:
            pass

        if len(extra_text) > 0:
            new_text = self.ax.text(pos_x,
                                    pos_y,
                                    extra_text,
                                    color=extra_color,
                                    fontproperties=mpl_font)

            # Update the list of annotations
            self.textList.append(new_text)
            self.canvas.draw()

    def onRemoveText(self):
        """
        Remove the most recently added text
        """
        num_text = len(self.textList)
        if num_text < 1:
            return
        txt = self.textList[num_text - 1]
        text_remove = txt.get_text()
        try:
            txt.remove()
        except ValueError:
            # Text got already deleted somehow
            pass
        self.textList.remove(txt)

        self.canvas.draw_idle()

    def onSetGraphRange(self):
        """
        Show a dialog allowing setting the chart ranges
        """
        # min and max of data
        if self.setRange.exec_() == QtWidgets.QDialog.Accepted:
            x_range = self.setRange.xrange()
            y_range = self.setRange.yrange()
            if x_range is not None and y_range is not None:
                self.ax.set_xlim(x_range)
                self.ax.set_ylim(y_range)
                self.canvas.draw_idle()

    def onResetGraphRange(self):
        """
        Resets the chart X and Y ranges to their original values
        """
        x_range = (self.data.x.min(), self.data.x.max())
        y_range = (self.data.y.min(), self.data.y.max())
        if x_range is not None and y_range is not None:
            self.ax.set_xlim(x_range)
            self.ax.set_ylim(y_range)
            self.canvas.draw_idle()

    def onLinearFit(self, id):
        """
        Creates and displays a simple linear fit for the selected plot
        """
        selected_plot = self.plot_dict[id]

        maxrange = (min(selected_plot.x), max(selected_plot.x))
        fitrange = self.ax.get_xlim()

        fit_dialog = LinearFit(parent=self,
                    data=selected_plot,
                    max_range=maxrange,
                    fit_range=fitrange,
                    xlabel=self.xLogLabel,
                    ylabel=self.yLogLabel)
        fit_dialog.updatePlot.connect(self.onFitDisplay)
        if fit_dialog.exec_() == QtWidgets.QDialog.Accepted:
            return

    def replacePlot(self, id, new_plot):
        """
        Remove plot 'id' and add 'new_plot' to the chart.
        This effectlvely refreshes the chart with changes to one of its plots
        """
        self.removePlot(id)
        self.plot(data=new_plot)

    def onRemovePlot(self, id):
        """
        Responds to the plot delete action
        """
        self.removePlot(id)

        if len(self.plot_dict) == 0:
            # last plot: graph is empty must be the panel must be destroyed
                self.parent.close()

    def removePlot(self, id):
        """
        Deletes the selected plot from the chart
        """
        if id not in list(self.plot_dict.keys()):
            return

        selected_plot = self.plot_dict[id]

        plot_dict = copy.deepcopy(self.plot_dict)

        # Labels might have been changed
        xl = self.ax.xaxis.label.get_text()
        yl = self.ax.yaxis.label.get_text()

        self.plot_dict = {}

        plt.cla()
        self.ax.cla()

        for ids in plot_dict:
            if ids != id:
                self.plot(data=plot_dict[ids], hide_error=plot_dict[ids].hide_error)

        # Reset the labels
        self.ax.set_xlabel(xl)
        self.ax.set_ylabel(yl)
        self.canvas.draw()

    def onFreeze(self, id):
        """
        Freezes the selected plot to a separate chart
        """
        plot = self.plot_dict[id]
        self.manager.add_data(data_list=[plot])

    def onModifyPlot(self, id):
        """
        Allows for MPL modifications to the selected plot
        """
        selected_plot = self.plot_dict[id]

        # Old style color - single integer for enum color
        # New style color - #hhhhhh
        color = selected_plot.custom_color
        # marker symbol and size
        marker = selected_plot.symbol
        marker_size = selected_plot.markersize
        # plot name
        legend = selected_plot.title

        plotPropertiesWidget = PlotProperties(self,
                                color=color,
                                marker=marker,
                                marker_size=marker_size,
                                legend=legend)
        if plotPropertiesWidget.exec_() == QtWidgets.QDialog.Accepted:
            # Update Data1d
            selected_plot.markersize = plotPropertiesWidget.markersize()
            selected_plot.custom_color = plotPropertiesWidget.color()
            selected_plot.symbol = plotPropertiesWidget.marker()
            selected_plot.title = plotPropertiesWidget.legend()

            # Redraw the plot
            self.replacePlot(id, selected_plot)

    def onToggleHideError(self, id):
        """
        Toggles hide error/show error menu item
        """
        selected_plot = self.plot_dict[id]
        current = selected_plot.hide_error

        # Flip the flag
        selected_plot.hide_error = not current

        plot_dict = copy.deepcopy(self.plot_dict)
        self.plot_dict = {}

        # Clean the canvas
        plt.cla()
        self.ax.cla()

        # Recreate the plots but reverse the error flag for the current
        for ids in plot_dict:
            if ids == id:
                self.plot(data=plot_dict[ids], hide_error=(not current))
            else:
                self.plot(data=plot_dict[ids], hide_error=plot_dict[ids].hide_error)                

    def xyTransform(self, xLabel="", yLabel=""):
        """
        Transforms x and y in View and set the scale
        """
        # Transform all the plots on the chart
        for id in list(self.plot_dict.keys()):
            current_plot = self.plot_dict[id]
            if current_plot.id == "fit":
                self.removePlot(id)
                continue

            new_xlabel, new_ylabel, xscale, yscale =\
                GuiUtils.xyTransform(current_plot, xLabel, yLabel)
            self.xscale = xscale
            self.yscale = yscale

            # Plot the updated chart
            self.removePlot(id)

            # This assignment will wrap the label in Latex "$"
            self.xLabel = new_xlabel
            self.yLabel = new_ylabel
            # Directly overwrite the data to avoid label reassignment
            self._data = current_plot
            self.plot()

        pass # debug hook

    def onFitDisplay(self, fit_data):
        """
        Add a linear fitting line to the chart
        """
        # Create new data structure with fitting result
        tempx = fit_data[0]
        tempy = fit_data[1]
        self.fit_result.x = []
        self.fit_result.y = []
        self.fit_result.x = tempx
        self.fit_result.y = tempy
        self.fit_result.dx = None
        self.fit_result.dy = None

        #Remove another Fit, if exists
        self.removePlot("fit")

        self.fit_result.reset_view()
        #self.offset_graph()

        # Set plot properties
        self.fit_result.id = 'fit'
        self.fit_result.title = 'Fit'
        self.fit_result.name = 'Fit'

        # Plot the line
        self.plot(data=self.fit_result, marker='-', hide_error=True)

    def onMplMouseDown(self, event):
        """
        Left button down and ready to drag
        """
        # Check that the LEFT button was pressed
        if event.button != 1:
            return

        self.leftdown = True
        for text in self.textList:
            if text.contains(event)[0]: # If user has clicked on text
                self.selectedText = text
                return
        if event.inaxes is None:
            return
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

        #if self.leftdown and self.selectedText is not None:
        if not self.leftdown or self.selectedText is None:
            return
        # User has clicked on text and is dragging
        if event.inaxes is None:
            # User has dragged outside of axes
            self.selectedText = None
        else:
            # Only move text if mouse is within axes
            self.selectedText.set_position((event.xdata, event.ydata))
            self.canvas.draw_idle()
        return

    def onMplPick(self, event):
        """
        On pick legend
        """
        legend = self.legend
        if event.artist != legend:
            return
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
        if ax is None:
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

        if ax is not None:
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


class Plotter(QtWidgets.QDialog, PlotterWidget):
    def __init__(self, parent=None, quickplot=False):

        QtWidgets.QDialog.__init__(self)
        PlotterWidget.__init__(self, parent=self, manager=parent, quickplot=quickplot)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/ball.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)


