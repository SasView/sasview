import copy
import functools
import math
import textwrap

import matplotlib.ticker as ticker
import numpy as np
from matplotlib.font_manager import FontProperties
from PySide6 import QtGui, QtWidgets

import sas.qtgui.Plotting.PlotUtilities as PlotUtilities
import sas.qtgui.Utilities.GuiUtils as GuiUtils
from sas import config
from sas.qtgui.Plotting.AddText import AddText
from sas.qtgui.Plotting.Binder import BindArtist
from sas.qtgui.Plotting.LinearFit import LinearFit
from sas.qtgui.Plotting.PlotLabelProperties import PlotLabelProperties, PlotLabelPropertyHolder
from sas.qtgui.Plotting.PlotProperties import PlotProperties
from sas.qtgui.Plotting.PlotterBase import PlotterBase
from sas.qtgui.Plotting.PlotterData import Data1D, DataRole
from sas.qtgui.Plotting.QRangeSlider import QRangeSlider
from sas.qtgui.Plotting.ScaleProperties import ScaleProperties
from sas.qtgui.Plotting.SetGraphRange import SetGraphRange


class PlotterWidget(PlotterBase):
    """
    1D Plot widget for use with a QDialog
    """
    def __init__(self, parent=None, manager=None, quickplot=False):
        super().__init__(parent, manager=manager, quickplot=quickplot)

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

        if parent is not None:
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
            # Added condition to volume distribution plot in size distribution perspective
            if data._yaxis == '\\rm{VolumeDistribution}':
                 self.yscale = 'linear'
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

        # grid on/off, stored on self
        ax.grid(self.grid_on)

        color = PlotUtilities.getValidColor(color)
        data.custom_color = color

        markersize = data.markersize

        # Include scaling (log vs. linear)
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
                if dy is not None and isinstance(dy, tuple):
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

        # Display +/- 3 sigma and +/- 1 sigma lines for residual plots
        if data.plot_role in [DataRole.ROLE_RESIDUAL, DataRole.ROLE_RESIDUAL_SESANS]:
            ax.axhline(y=3, color='red', linestyle='-')
            ax.axhline(y=-3, color='red', linestyle='-')
            ax.axhline(y=1, color='gray', linestyle='--')
            ax.axhline(y=-1, color='gray', linestyle='--')
        # Update the list of data sets (plots) in chart
        self.plot_dict[data.name] = data

        self.plot_lines[data.name] = line

        # Now add the legend with some customizations.
        if self.showLegend:
            max_legend_width = config.FITTING_PLOT_LEGEND_MAX_LINE_LENGTH
            handles, labels = ax.get_legend_handles_labels()
            newhandles = []
            newlabels = []
            for h,l in zip(handles,labels):
                    if config.FITTING_PLOT_LEGEND_TRUNCATE:
                        if len(l)> config.FITTING_PLOT_LEGEND_MAX_LINE_LENGTH:
                            half_legend_width = math.floor(max_legend_width/2)
                            newlabels.append(f'{l[0:half_legend_width-3]} .. {l[-half_legend_width+3:]}')
                        else:
                            newlabels.append(l)
                    else:
                        newlabels.append(textwrap.fill(l,max_legend_width))
                    newhandles.append(h)

            if config.FITTING_PLOT_FULL_WIDTH_LEGENDS:
                self.legend = ax.legend(newhandles,newlabels,loc='best', mode='expand')
            else:
                self.legend = ax.legend(newhandles,newlabels,loc='best', shadow=True)
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

        elif isinstance(data, Data1D):
            # Get default ranges from data

            if self.has_nonempty_plots():
                x_range, y_range = self._plot_bounds()

            else:

                x_range = self.ax.get_xlim()
                y_range = self.ax.get_ylim()

            default_x_range, default_y_range = x_range, y_range

            modified = False
        else:
            # Use default ranges given by matplotlib
            default_x_range = self.ax.get_xlim()
            default_y_range = self.ax.get_ylim()
            x_range = default_x_range
            y_range = default_y_range
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

    def has_nonempty_plots(self) -> bool:

        for key in self.plot_dict:
            if len(self.plot_dict[key].x) > 0:
                return True

        return False

    def _plot_bounds(self, offset=0.05) -> tuple[tuple[float, float], tuple[float, float]]:
        """
        Get the appropriate bounds for the plots. This is a workaround for an
        edge case bug in matplotlib's autoscale. Basically, data whose range is
        tiny on a log scale (e.g. 0.9 to 1.1 on a log scale).

        This should be removed if and when matplotlib fixes the bug. In the
        meantime this private method ensures that all plots are scaled such
        that there is a small "white space" between the data extremes and the
        plot edges.

        In order to achieve this, the min and max of all the data on the plot
        are computed, taking into account that will include the top, or bottom,
        of any error bars present with the data. For log axes data that first
        requires removing any negative values from the min max computation.

        The min and max values for each scale are then converted from data
        coordinates to axes coordinates before computing the range of the data
        (max-min). A fraction of that range (default is 5%) is then added and
        subtracted from the smallest (min) and largest (max) values of x and y,
        still in axes space. This ensures that regardless of the plot scaling
        10% of the plot space (5% on either end) will be empty.

        Finally, those adjusted min and max values are converted back to data
        coordinates to be used in setting the plot bounds in the usual fashion

        :param offset: The fraction of the absolute value of the full
         data range to add to each end of the data range
        :returns: lower right (xmin,ymin) and upper left (xmax,ymax) corners of
         where the plot (figure) bounds should be set.
        """

        x_min, x_max = np.inf, -np.inf
        y_min, y_max = np.inf, -np.inf

        # First let's find the smallest xmin and ymin and largest xmax and ymax
        # in all the data sets. if the data have error bars then we need to
        # keep track of the data poing + (or -) the error bar height to make
        # sure the error bars stay within the plot.
        for key in self.plot_dict:

            plot_data = self.plot_dict[key].view

            # First find the x axes bounds
            if len(plot_data.x) > 0:
                x_min = min(np.min(plot_data.x), x_min)
                x_max = max(np.max(plot_data.x), x_max)

            # and now the y axss. Note: here we need to ensure not only are the
            # y value is in bounds we also need to make sure that the top (or
            # bottom) of the error bars on the points are also within the plot
            # bounds.
            if len(plot_data.y) > 0:
                dy = plot_data.dy
                if dy is None:
                    y_min = min(np.min(plot_data.y), y_min)
                    y_max = max(np.max(plot_data.y), y_max)
                else:
                    try:
                        # For log scales we need to worry about whether y-dy
                        # will be negative. Note that only postive y and x
                        # are available when ax.axis is in log scale
                        if self.ax.yaxis.get_scale() == "log":
                            y_min = min(np.min([i for i in (np.array(plot_data.y) - np.array(dy)) if i > 0]), y_min)
                            y_max = max(np.max([i for i in (np.array(plot_data.y) + np.array(dy))if i > 0]), y_max)
                        else:
                            y_min = min(np.min(np.array(plot_data.y) - np.array(dy)), y_min)
                            y_max = max(np.max(np.array(plot_data.y) + np.array(dy)), y_max)
                    except ValueError:
                        # Ignore error term if it doesn't match y scale and causes an error
                        y_min = min(np.min(plot_data.y), y_min)
                        y_max = max(np.max(plot_data.y), y_max)

        # Now we move from data coordinates to axes coordinates.
        # This allows us to provide even padding between all the data limits
        # and their respective plot bounds in "image" space, regardless of the
        # scale of the plot (e.g log vs. linear).
        data_to_axis = self.ax.transData + self.ax.transAxes.inverted()

        ax_xmin, ax_ymin = data_to_axis.transform((x_min,y_min))
        ax_xmax, ax_ymax = data_to_axis.transform((x_max,y_max))

        x_pad = offset*(ax_xmax - ax_xmin)
        y_pad = offset*(ax_ymax - ax_ymin)

        # Return the bounds in data coordinates now
        re_xmin,re_ymin = data_to_axis.inverted().transform((ax_xmin-x_pad,ax_ymin-y_pad))
        re_xmax,re_ymax = data_to_axis.inverted().transform((ax_xmax+x_pad,ax_ymax+y_pad))

        return ((float(re_xmin),
                 float(re_xmax)),
                (float(re_ymin),
                 float(re_ymax)))


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
        self.actionToggleGrid = self.contextMenu.addAction("Toggle Grid On/Off")
        if self.show_legend:
            self.actionToggleLegend = self.contextMenu.addAction("Toggle Legend")
            self.contextMenu.addSeparator()
        # Additional actions
        self.actionCustomizeLabel = self.contextMenu.addAction("Customize Labels")
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
        self.actionToggleGrid.triggered.connect(self.onGridToggle)
        self.actionResetGraphRange.triggered.connect(self.onResetGraphRange)
        self.actionWindowTitle.triggered.connect(self.onWindowsTitle)
        self.actionToggleMenu.triggered.connect(self.onToggleMenu)
        if self.show_legend:
            self.actionToggleLegend.triggered.connect(self.onToggleLegend)
        self.actionCustomizeLabel.triggered.connect(self.onCusotmizeLabel)

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
                if plot.dy is not None and len(plot.dy)>0:
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
        # Get an index of the font style which we can then lookup in the styles list.
        font_index = extra_font.style().value
        mpl_font.set_style(styles[font_index])

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
        This effectively refreshes the chart with changes to one of its plots
        """

        # Pull the current transform settings from the old plot
        selected_plot = self.plot_dict[id]
        new_plot.plot_role = selected_plot.plot_role
        # Adding few properties from ModifyPlot to preserve them in future changes
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

    def onFitDisplay(self, temp_x, temp_y):
        """
        Add a linear fitting line to the chart
        """
        # Create new data structure with fitting result
        self.fit_result.x = []
        self.fit_result.y = []
        self.fit_result.x = temp_x
        self.fit_result.y = temp_y
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

    def onCusotmizeLabel(self):
        """
        Show label customization widget
        """
        xl = self.ax.xaxis.label
        yl = self.ax.yaxis.label
        font_x = PlotLabelPropertyHolder(
            size=xl.get_fontsize(),
            font=xl.get_family()[0],
            color=xl.get_color(),
            weight=xl.get_weight(),
            text=xl.get_text())

        font_y = PlotLabelPropertyHolder(
            size=yl.get_fontsize(),
            font=yl.get_family()[0],
            color=yl.get_color(),
            weight=yl.get_weight(),
            text=yl.get_text())

        labelWidget = PlotLabelProperties(self, x_props=font_x, y_props=font_y)

        if labelWidget.exec_() != QtWidgets.QDialog.Accepted:
            return

        fx = labelWidget.fx()
        fy = labelWidget.fy()
        label_x = labelWidget.text_x()
        label_y = labelWidget.text_y()
        apply_x = labelWidget.apply_to_ticks_x()
        apply_y = labelWidget.apply_to_ticks_y()

        self.ax.set_xlabel(label_x, fontdict=fx)
        self.ax.set_ylabel(label_y, fontdict=fy)
        if apply_x:
            # self.ax.tick_params(axis='x', labelsize=fx.size, labelcolor=fx.color)
            from matplotlib.pyplot import gca
            a = gca()
            a.set_xticklabels(a.get_xticks(), **fx)
        if apply_y:
            # self.ay.tick_params(axis='y', labelsize=fy.size, labelcolor=fy.color)
            from matplotlib.pyplot import gca
            a = gca()
            a.set_yticklabels(a.get_yticks(), **fy)
        if self.ax.xaxis.get_scale() == "log":
            self.ax.xaxis.set_major_formatter(ticker.LogFormatterSciNotation(labelOnlyBase=True))
        else:
            self.ax.xaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))
        if self.ax.yaxis.get_scale() == "log":
            self.ax.yaxis.set_major_formatter(ticker.LogFormatterSciNotation(labelOnlyBase=True))
        else:
            self.ax.yaxis.set_major_formatter(ticker.ScalarFormatter(useMathText=True))

        self.canvas.draw_idle()

    def onMplMouseDown(self, event):
        """
        Left button down and ready to drag
        """
        # Before checking if this mouse click is a left click, we need to update the position of the mouse regardless as
        # this may be needed by other events (e.g. adding text)
        try:
            self.x_click = float(event.xdata)  # / size_x
            self.y_click = float(event.ydata)  # / size_y
        except:
            self.position = None
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

        x_str = GuiUtils.formatNumber(self.x_click)
        y_str = GuiUtils.formatNumber(self.y_click)
        coord_str = f"x: {x_str}, y: {y_str}"
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

        PlotterWidget.__init__(self, parent=None, manager=parent, quickplot=quickplot)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/res/ball.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
