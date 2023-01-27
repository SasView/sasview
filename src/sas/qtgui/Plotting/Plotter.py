from PyQt5 import QtGui
from PyQt5 import QtWidgets

import functools
import copy
import sys
import matplotlib as mpl
import numpy as np
from matplotlib.font_manager import FontProperties
from packaging import version

from sas.qtgui.Plotting.PlotterData import Data1D
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Plotting.AddText import AddText
from sas.qtgui.Plotting.Binder import BindArtist
from sas.qtgui.Plotting.SetGraphRange import SetGraphRange
from sas.qtgui.Plotting.LinearFit import LinearFit
from sas.qtgui.Plotting.QRangeSlider import QRangeSlider
from sas.qtgui.Plotting.PlotProperties import PlotProperties
from sas.qtgui.Plotting.ScaleProperties import ScaleProperties

import sas.qtgui.Utilities.GuiUtils as GuiUtils
import sas.qtgui.Plotting.PlotUtilities as PlotUtilities

def _legendResize(width, parent):
    """
    resize factor for the legend, based on total canvas width
    """
    # The factor 4.0 was chosen to look similar in size/ratio to what we had in 4.x
    if not hasattr(parent.parent, "manager"):
        return None
    if parent is None or parent.parent is None or parent.parent.manager is None \
        or parent.parent.manager.parent is None or parent.parent.manager.parent._parent is None:
        return None

    screen_width = parent.parent.manager.parent._parent.screen_width
    screen_height = parent.parent.manager.parent._parent.screen_height
    screen_factor = screen_width * screen_height

    if sys.platform == 'win32':
        factor = 4
        denomintor = 100
        scale_factor = width/denomintor + factor
    else:
        #Function inferred based on tests for several resolutions
        scale_factor = (3e-6*screen_factor + 1)*width/640
    return scale_factor

class PlotterWidget(PlotterBase):
    """
    1D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False):
        super(PlotterWidget, self).__init__(parent, manager=manager, quickplot=quickplot)

        self.parent = parent

        # Dictionary of {plot_id:Data1d}
        self.plot_dict = {}
        # Dictionaty of {plot_id:line}
        self.plot_lines = {}
        # Dictionary of slider interactors {plot_id:interactor}
        self.sliders = {}

        # Window for text add
        self.addText = AddText(self)

        # Log-ness of the axes
        self.xLogLabel = "log10(x)"
        self.yLogLabel = "log10(y)"

        # Data container for the linear fit
        self.fit_result = Data1D(x=[], y=[], dy=None)
        self.fit_result.symbol = 17
        self.fit_result.name = "Fit"

        # Range setter - used to store active SetGraphRange instance
        # Initialize to None so graph range is only stored once data is present.
        self.setRange = None

        # Connections used to prevent conflict between built in mpl toolbar actions and SasView context menu actions.
        # Toolbar actions only needed in 1D plots. 2D plots have no such conflicts.
        self.toolbar._actions['home'].triggered.connect(self._home)
        self.toolbar._actions['back'].triggered.connect(self._back)
        self.toolbar._actions['forward'].triggered.connect(self._forward)
        self.toolbar._actions['pan'].triggered.connect(self._pan)
        self.toolbar._actions['zoom'].triggered.connect(self._zoom)

        self.legendVisible = True

        parent.geometry()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        """ data setter """
        #self._data = value
        self._data.append(value)
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

    def plot(self, data=None, color=None, marker=None, hide_error=False, transform=True):
        """
        Add a new plot of self._data to the chart.
        """
        if data is None:
            # just refresh
            self.canvas.draw_idle()
            return

        # Data1D
        if isinstance(data, Data1D):
            self.data.append(data)

        is_fit = (data.id=="fit")

        if not is_fit:
            # make sure we have some function to operate on
            if data.xtransform is None:
                if data.isSesans:
                    data.xtransform='x'
                else:
                    data.xtransform = 'log10(x)'
            if data.ytransform is None:
                if data.isSesans:
                    data.ytransform='y'
                else:
                    data.ytransform = 'log10(y)'
            #Added condition to Dmax explorer from P(r) perspective
            if data._xaxis == 'D_{max}':
                self.xscale = 'linear'
            # Transform data if required.
            if transform and (data.xtransform is not None or data.ytransform is not None):
                self.xLabel, self.yLabel, xscale, yscale = \
                    GuiUtils.xyTransform(data, data.xtransform, data.ytransform)
                if xscale != 'log' and xscale != self.xscale:
                    self.xscale = xscale
                if yscale != 'log' and yscale != self.yscale:
                    self.yscale = yscale

                # Redefine the Scale properties dialog
                self.properties = ScaleProperties(self,
                                        init_scale_x=data.xtransform,
                                        init_scale_y=data.ytransform)

        # Shortcuts
        ax = self.ax
        x = data.view.x
        y = data.view.y
        label = data.name # was self._title

        # Marker symbol. Passed marker is one of matplotlib.markers characters
        # Alternatively, picked up from Data1D as an int index of PlotUtilities.SHAPES dict
        if marker is None:
            marker = data.symbol
            # Try name first
            try:
                marker = dict(PlotUtilities.SHAPES)[marker]
            except KeyError:
                marker = list(PlotUtilities.SHAPES.values())[marker]

        assert marker is not None
        # Plot name
        if data.title:
            self.title(title=data.title)
        else:
            self.title(title=data.name)

        # Error marker toggle
        if hide_error is None:
            hide_error = data.hide_error

        # Plot color
        if color is None:
            color = data.custom_color

        color = PlotUtilities.getValidColor(color)
        data.custom_color = color

        markersize = data.markersize

        # Include scaling (log vs. linear)
        if version.parse(mpl.__version__) < version.parse("3.3"):
            ax.set_xscale(self.xscale, nonposx='clip') if self.xscale != 'linear' else self.ax.set_xscale(self.xscale)
            ax.set_yscale(self.yscale, nonposy='clip') if self.yscale != 'linear' else self.ax.set_yscale(self.yscale)
        else:
            ax.set_xscale(self.xscale, nonpositive='clip') if self.xscale != 'linear' else self.ax.set_xscale(self.xscale)
            ax.set_yscale(self.yscale, nonpositive='clip') if self.yscale != 'linear' else self.ax.set_yscale(self.yscale)

        # Draw non-standard markers
        l_width = markersize * 0.4
        if marker == '-' or marker == '--':
            line = self.ax.plot(x, y, color=color, lw=l_width, marker='',
                             linestyle=marker, label=label, zorder=10)[0]

        elif marker == 'vline':
            y_min = min(y)*9.0/10.0 if min(y) < 0 else 0.0
            line = self.ax.vlines(x=x, ymin=y_min, ymax=y, color=color,
                            linestyle='-', label=label, lw=l_width, zorder=1)

        elif marker == 'step':
            line = self.ax.step(x, y, color=color, marker='', linestyle='-',
                                label=label, lw=l_width, zorder=1)[0]

        else:
            # plot data with/without errorbars
            if hide_error:
                line = ax.plot(x, y, marker=marker, color=color, markersize=markersize,
                        linestyle='', label=label, picker=True)
            else:
                dy = data.view.dy
                # Convert tuple (lo,hi) to array [(x-lo),(hi-x)]
                if dy is not None and type(dy) == type(()):
                    dy = np.vstack((y - dy[0], dy[1] - y)).transpose()

                line = ax.errorbar(x, y,
                            yerr=dy,
                            xerr=None,
                            capsize=2, linestyle='',
                            barsabove=False,
                            color=color,
                            marker=marker,
                            markersize=markersize,
                            lolims=False, uplims=False,
                            xlolims=False, xuplims=False,
                            label=label,
                            zorder=1,
                            picker=True)

        # Display horizontal axis if requested
        if data.show_yzero:
            ax.axhline(color='black', linewidth=1)

        # Update the list of data sets (plots) in chart
        self.plot_dict[data.name] = data

        self.plot_lines[data.name] = line

        # Now add the legend with some customizations.
        if self.showLegend:
            width=_legendResize(self.canvas.size().width(), self.parent)
            if width is not None:
                self.legend = ax.legend(loc='upper right', shadow=True, prop={'size':width})
            else:
                self.legend = ax.legend(loc='upper right', shadow=True)
            if self.legend:
                self.legend.set_picker(True)
            self.legend.set_visible(self.legendVisible)
        # Current labels for axes
        if self.yLabel and not is_fit:
            ax.set_ylabel(self.yLabel)
        if self.xLabel and not is_fit:
            ax.set_xlabel(self.xLabel)

        # define the ranges
        if isinstance(self.setRange, SetGraphRange) and self.setRange.rangeModified:
            # Assume the range has changed and retain the current and default ranges for future use
            modified = self.setRange.rangeModified
            default_x_range = self.setRange.defaultXRange
            default_y_range = self.setRange.defaultYRange
            x_range = self.setRange.xrange()
            y_range = self.setRange.yrange()
        else:
            # Use default ranges given by matplotlib
            x_range = default_x_range = self.ax.get_xlim()
            y_range = default_y_range = self.ax.get_ylim()
            modified = False
        self.setRange = SetGraphRange(parent=self, x_range=x_range, y_range=y_range)
        self.setRange.rangeModified = modified
        self.setRange.defaultXRange = default_x_range
        self.setRange.defaultYRange = default_y_range
        # Go to expected range
        self.ax.set_xbound(x_range[0], x_range[1])
        self.ax.set_ybound(y_range[0], y_range[1])

        # Add q-range sliders
        if data.show_q_range_sliders:
            # Grab existing slider if it exists
            existing_slider = self.sliders.pop(data.name, None)
            sliders = QRangeSlider(self, self.ax, data=data)
            # New sliders should be visible but existing sliders that were turned off should remain off
            if existing_slider is not None and not existing_slider.is_visible:
                sliders.toggle()
            self.sliders[data.name] = sliders

        # refresh canvas
        self.canvas.draw_idle()

    def onResize(self, event):
        """
        Resize the legend window/font on canvas resize
        """
        if not self.showLegend or not self.legendVisible:
            return
        width = _legendResize(event.width, self.parent)
        # resize the legend to follow the canvas width.
        if width is not None:
            self.legend.prop.set_size(width)

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
        if self.show_legend:
            self.actionToggleLegend = self.contextMenu.addAction("Toggle Legend")
            self.contextMenu.addSeparator()
        self.actionChangeScale = self.contextMenu.addAction("Change Scale")
        self.contextMenu.addSeparator()
        self.actionSetGraphRange = self.contextMenu.addAction("Set Graph Range")
        self.actionResetGraphRange =\
            self.contextMenu.addAction("Reset Graph Range")

        # Add the title change for dialogs
        self.contextMenu.addSeparator()
        self.actionWindowTitle = self.contextMenu.addAction("Window Title")
        self.contextMenu.addSeparator()
        self.actionToggleMenu = self.contextMenu.addAction("Toggle Navigation Menu")

        # Define the callbacks
        self.actionAddText.triggered.connect(self.onAddText)
        self.actionRemoveText.triggered.connect(self.onRemoveText)
        self.actionChangeScale.triggered.connect(self.onScaleChange)
        self.actionSetGraphRange.triggered.connect(self.onSetGraphRange)
        self.actionResetGraphRange.triggered.connect(self.onResetGraphRange)
        self.actionWindowTitle.triggered.connect(self.onWindowsTitle)
        self.actionToggleMenu.triggered.connect(self.onToggleMenu)
        if self.show_legend:
            self.actionToggleLegend.triggered.connect(self.onToggleLegend)

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

            if plot.show_q_range_sliders:
                self.actionToggleSlider = plot_menu.addAction("Toggle Q-Range Slider Visibility")
                self.actionToggleSlider.triggered.connect(
                                    functools.partial(self.toggleSlider, id))

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

        if self.show_legend:
            self.actionToggleLegend = self.contextMenu.addAction("Toggle Legend")
            self.actionToggleLegend.triggered.connect(self.onToggleLegend)

    def onScaleChange(self):
        """
        Show a dialog allowing axes rescaling
        """
        if self.properties.exec_() == QtWidgets.QDialog.Accepted:
            self.xLogLabel, self.yLogLabel = self.properties.getValues()
            for d in self.data:
                d.xtransform = self.xLogLabel
                d.ytransform = self.yLogLabel
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
            self.canvas.draw_idle()

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

    def _zoom_pan_handler(self, event):
        if not self.setRange:
            self.setRange = SetGraphRange(parent=self)
        x_range = self.ax.get_xlim()
        y_range = self.ax.get_ylim()
        self.setRange.txtXmin.setText(str(x_range[0]))
        self.setRange.txtXmax.setText(str(x_range[1]))
        self.setRange.txtYmin.setText(str(y_range[0]))
        self.setRange.txtYmax.setText(str(y_range[1]))
        self._setGraphRange()

    def _zoom_handler(self, event):
        """
        Explicitly call toolbar method to ensure range is changed. In MPL 2.2, local events take precedence over the
        toolbar events, so the range isn't zoomed until after _zoom_pan_handler is run.
        """
        self.toolbar.release_zoom(event)
        self._zoom_pan_handler(event)

    def _pan_handler(self, event):
        """
        Explicitly call toolbar method to ensure range is changed. In MPL 2.2, local events take precedence over the
        toolbar events, so the range isn't panned until after _zoom_pan_handler is run.
        """
        self.toolbar.release_pan(event)
        self._zoom_pan_handler(event)

    def _home(self, event):
        """
        Catch home button click events
        """
        self.onResetGraphRange()

    def _back(self, event):
        """
        Catch back button click events
        """
        self.toolbar.back()
        self._zoom_pan_handler(event)

    def _forward(self, event):
        """
        Catch forward button click events
        """
        self.toolbar.forward()
        self._zoom_pan_handler(event)

    def _pan(self, event):
        """
        Catch pan button click events
        """
        self.canvas.mpl_connect('button_release_event', self._pan_handler)

    def _zoom(self, event):
        """
        Catch zoom button click events
        """
        self.canvas.mpl_connect('button_release_event', self._zoom_handler)

    def onSetGraphRange(self):
        """
        Show a dialog allowing setting the chart ranges
        """
        # min and max of data
        if self.setRange.exec_() == QtWidgets.QDialog.Accepted:
            self._setGraphRange()

    def _setGraphRange(self):
        x_range = self.setRange.xrange()
        y_range = self.setRange.yrange()
        if x_range is not None and y_range is not None:
            self.setRange.rangeModified = (self.setRange.defaultXRange != x_range
                                           or self.setRange.defaultYRange != y_range)
            self.ax.set_xlim(x_range)
            self.ax.set_ylim(y_range)
            self.canvas.draw_idle()

    def onResetGraphRange(self):
        """
        Resets the chart X and Y ranges to their original values
        """
        # Clear graph and plot everything again
        self.ax.cla()
        self.setRange = None
        for ids in self.plot_dict:
            # Color, marker, etc. are stored in each data set and will be used to restore visual changes on replot
            self.plot(data=self.plot_dict[ids], hide_error=self.plot_dict[ids].hide_error)

        # Redraw
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

    def replacePlot(self, id, new_plot, retain_dimensions=True):
        """
        Remove plot 'id' and add 'new_plot' to the chart.
        This effectlvely refreshes the chart with changes to one of its plots
        """

        # Pull the current transform settings from the old plot
        selected_plot = self.plot_dict[id]
        new_plot.xtransform = selected_plot.xtransform
        new_plot.ytransform = selected_plot.ytransform
        #Adding few properties ftom ModifyPlot to preserve them in future changes
        new_plot.title = selected_plot.title
        new_plot.custom_color = selected_plot.custom_color
        new_plot.markersize = selected_plot.markersize
        new_plot.symbol = selected_plot.symbol
        self.removePlot(id)
        self.plot(data=new_plot)
        # Apply user-defined plot range
        if retain_dimensions or self.setRange.rangeModified:
            x_bounds = self.setRange.xrange()
            y_bounds = self.setRange.yrange()
            self.ax.set_xbound(x_bounds[0], x_bounds[1])
            self.ax.set_ybound(y_bounds[0], y_bounds[1])

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

        # Remove the plot from the list of plots
        self.plot_dict.pop(id)

        # Labels might have been changed
        xl = self.ax.xaxis.label.get_text()
        yl = self.ax.yaxis.label.get_text()

        self.ax.cla()

        # Recreate Artist bindings after plot clear
        self.connect = BindArtist(self.figure)

        for ids in self.plot_dict:
            if ids != id:
                self.plot(data=self.plot_dict[ids], hide_error=self.plot_dict[ids].hide_error)

        # Reset the labels
        self.ax.set_xlabel(xl)
        self.ax.set_ylabel(yl)
        self.canvas.draw_idle()

    def toggleSlider(self, id):
        if id in self.sliders.keys():
            slider = self.sliders.get(id)
            slider.toggle()

    def onFreeze(self, id):
        """
        Freezes the selected plot to a separate chart
        """
        plot = self.plot_dict[id]
        plot = copy.deepcopy(plot)
        self.manager.add_data(data_list={id:plot})
        self.manager.freezeDataToItem(plot)

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
        legend = selected_plot.name
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
            selected_plot.name = plotPropertiesWidget.legend()
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

            self.plot(data=current_plot, transform=False)

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

        self.fit_result.reset_view()
        #self.offset_graph()

        # Set plot properties
        self.fit_result.id = 'fit'
        self.fit_result.title = 'Fit'
        self.fit_result.name = 'Fit'

        if self.fit_result.name in self.plot_dict.keys():
            # Replace an existing Fit and ensure the plot range is not reset
            self.replacePlot("Fit", new_plot=self.fit_result)
        else:
            # Otherwise, Plot a new line
            self.plot(data=self.fit_result, marker='-', hide_error=True)

    def onToggleLegend(self):
        """
        Toggle legend visibility in the chart
        """
        if not self.showLegend:
            return

        #visible = self.legend.get_visible()
        self.legendVisible = not self.legendVisible
        self.legend.set_visible(self.legendVisible)
        self.canvas.draw_idle()

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

        x_str = GuiUtils.formatNumber(self.x_click)
        y_str = GuiUtils.formatNumber(self.y_click)
        coord_str = "x: {}, y: {}".format(x_str, y_str)
        self.manager.communicator.statusBarUpdateSignal.emit(coord_str)

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
